"""
MCP Security Layer - Authentication and approval handling.

Provides:
- API key authentication
- Safe mode (confirm writes) vs Trust mode (auto-approve)
- Verbal confirmation interface for ElevenLabs
- Session-based approval tracking
"""

import hashlib
import hmac
import logging
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class ApprovalMode(Enum):
    """Approval mode for tool execution."""
    SAFE = "safe"      # Auto-approve reads, confirm writes
    TRUST = "trust"    # Auto-approve all operations


@dataclass
class ApprovalRequest:
    """Pending approval request."""
    id: str
    tool_name: str
    arguments: Dict[str, Any]
    description: str
    created_at: datetime
    resolved: bool = False
    approved: bool = False


@dataclass
class Session:
    """User session with approval state."""
    session_id: str
    created_at: datetime
    mode: ApprovalMode = ApprovalMode.SAFE
    approved_tools: Set[str] = field(default_factory=set)
    pending_approvals: Dict[str, ApprovalRequest] = field(default_factory=dict)
    trust_enabled_at: Optional[datetime] = None


class SecurityManager:
    """
    Security and approval manager for MCP tools.

    Features:
    - API key validation
    - Session management
    - Safe/Trust mode switching
    - Verbal confirmation for write operations
    - Approval request tracking
    """

    # Tools that always require approval in safe mode
    WRITE_TOOLS = {
        "file_write", "file_edit", "file_delete",
        "bash_execute", "bash_background",
        "git_commit", "git_push", "git_reset",
        "github_create_pr", "github_merge_pr", "github_create_issue",
        "email_send", "calendar_create", "calendar_delete",
        "aws_lambda_deploy", "aws_s3_upload", "aws_dynamodb_write"
    }

    # Tools that are always safe (read-only)
    READ_TOOLS = {
        "file_read", "file_glob", "file_grep",
        "git_status", "git_diff", "git_log",
        "github_get_pr", "github_list_prs", "github_get_issue",
        "web_search", "web_fetch",
        "aws_lambda_list", "aws_s3_list", "aws_costs_get",
        "calendar_list", "email_list"
    }

    # Trust mode trigger phrase
    TRUST_TRIGGER = "do it"

    def __init__(
        self,
        api_keys: List[str] = None,
        approval_callback: Callable = None,
        approval_timeout: int = 30
    ):
        """
        Initialize SecurityManager.

        Args:
            api_keys: List of valid API keys (hashed)
            approval_callback: Async callback for verbal approval requests
            approval_timeout: Seconds to wait for approval response
        """
        self.api_keys = set(api_keys or [])
        self.approval_callback = approval_callback
        self.approval_timeout = approval_timeout

        self._sessions: Dict[str, Session] = {}
        self._approval_counter = 0

    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate an API key.

        Args:
            api_key: API key to validate

        Returns:
            True if valid
        """
        if not self.api_keys:
            # No keys configured = open access (for development)
            return True

        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        return key_hash in self.api_keys

    def get_or_create_session(self, session_id: str) -> Session:
        """
        Get existing session or create new one.

        Args:
            session_id: Session identifier

        Returns:
            Session object
        """
        if session_id not in self._sessions:
            self._sessions[session_id] = Session(
                session_id=session_id,
                created_at=datetime.now()
            )
            logger.info(f"Created new session: {session_id}")
        return self._sessions[session_id]

    def set_mode(self, session_id: str, mode: ApprovalMode) -> None:
        """
        Set approval mode for a session.

        Args:
            session_id: Session identifier
            mode: New approval mode
        """
        session = self.get_or_create_session(session_id)
        old_mode = session.mode
        session.mode = mode

        if mode == ApprovalMode.TRUST:
            session.trust_enabled_at = datetime.now()

        logger.info(f"Session {session_id} mode changed: {old_mode.value} -> {mode.value}")

    def check_trust_trigger(self, text: str, session_id: str) -> bool:
        """
        Check if text contains trust mode trigger phrase.

        Args:
            text: User input text
            session_id: Session identifier

        Returns:
            True if trust mode was triggered
        """
        if self.TRUST_TRIGGER.lower() in text.lower():
            self.set_mode(session_id, ApprovalMode.TRUST)
            return True
        return False

    def requires_approval(
        self,
        tool_name: str,
        session_id: str
    ) -> bool:
        """
        Check if a tool requires approval.

        Args:
            tool_name: Name of the tool
            session_id: Session identifier

        Returns:
            True if approval is required
        """
        session = self.get_or_create_session(session_id)

        # Trust mode = no approval needed
        if session.mode == ApprovalMode.TRUST:
            return False

        # Read tools never need approval
        if tool_name in self.READ_TOOLS:
            return False

        # Previously approved tools don't need re-approval
        if tool_name in session.approved_tools:
            return False

        # Write tools need approval in safe mode
        if tool_name in self.WRITE_TOOLS:
            return True

        # Unknown tools default to requiring approval
        return True

    async def request_approval(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        session_id: str = "default"
    ) -> bool:
        """
        Request approval for a tool execution.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            session_id: Session identifier

        Returns:
            True if approved
        """
        session = self.get_or_create_session(session_id)

        # Check if approval is actually required
        if not self.requires_approval(tool_name, session_id):
            return True

        # Create approval request
        self._approval_counter += 1
        request_id = f"approval_{self._approval_counter}"

        description = self._format_approval_description(tool_name, arguments)

        request = ApprovalRequest(
            id=request_id,
            tool_name=tool_name,
            arguments=arguments,
            description=description,
            created_at=datetime.now()
        )

        session.pending_approvals[request_id] = request
        logger.info(f"Created approval request: {request_id} for {tool_name}")

        # If no callback, auto-deny
        if not self.approval_callback:
            logger.warning("No approval callback configured, denying request")
            return False

        # Request verbal approval
        try:
            approved = await asyncio.wait_for(
                self.approval_callback(request),
                timeout=self.approval_timeout
            )

            request.resolved = True
            request.approved = approved

            if approved:
                # Remember approval for this tool
                session.approved_tools.add(tool_name)
                logger.info(f"Approval granted for {tool_name}")
            else:
                logger.info(f"Approval denied for {tool_name}")

            return approved

        except asyncio.TimeoutError:
            logger.warning(f"Approval timeout for {tool_name}")
            request.resolved = True
            request.approved = False
            return False

    def _format_approval_description(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> str:
        """
        Format a human-readable description of the operation.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            Human-readable description
        """
        descriptions = {
            "file_write": lambda a: f"Write to file: {a.get('path', 'unknown')}",
            "file_edit": lambda a: f"Edit file: {a.get('path', 'unknown')}",
            "file_delete": lambda a: f"Delete file: {a.get('path', 'unknown')}",
            "bash_execute": lambda a: f"Run command: {a.get('command', 'unknown')[:50]}...",
            "git_commit": lambda a: f"Commit changes: {a.get('message', 'unknown')[:50]}...",
            "git_push": lambda a: f"Push to remote: {a.get('remote', 'origin')}",
            "email_send": lambda a: f"Send email to: {a.get('to', 'unknown')}",
            "github_create_pr": lambda a: f"Create PR: {a.get('title', 'unknown')}",
            "aws_lambda_deploy": lambda a: f"Deploy Lambda: {a.get('function_name', 'unknown')}",
        }

        formatter = descriptions.get(tool_name)
        if formatter:
            try:
                return formatter(arguments)
            except Exception:
                pass

        return f"Execute {tool_name}"

    def get_pending_approvals(self, session_id: str) -> List[ApprovalRequest]:
        """Get pending approval requests for a session."""
        session = self.get_or_create_session(session_id)
        return [
            req for req in session.pending_approvals.values()
            if not req.resolved
        ]

    def resolve_approval(
        self,
        request_id: str,
        approved: bool,
        session_id: str
    ) -> bool:
        """
        Resolve a pending approval request.

        Args:
            request_id: Approval request ID
            approved: Whether to approve
            session_id: Session identifier

        Returns:
            True if request was found and resolved
        """
        session = self.get_or_create_session(session_id)
        request = session.pending_approvals.get(request_id)

        if not request or request.resolved:
            return False

        request.resolved = True
        request.approved = approved

        if approved:
            session.approved_tools.add(request.tool_name)

        return True

    def cleanup_sessions(self, max_age_hours: int = 24) -> int:
        """
        Clean up old sessions.

        Args:
            max_age_hours: Maximum session age in hours

        Returns:
            Number of sessions removed
        """
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        old_sessions = [
            sid for sid, session in self._sessions.items()
            if session.created_at < cutoff
        ]

        for sid in old_sessions:
            del self._sessions[sid]

        if old_sessions:
            logger.info(f"Cleaned up {len(old_sessions)} old sessions")

        return len(old_sessions)

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session."""
        session = self.get_or_create_session(session_id)
        return {
            "session_id": session_id,
            "mode": session.mode.value,
            "created_at": session.created_at.isoformat(),
            "approved_tools": list(session.approved_tools),
            "pending_approvals": len(self.get_pending_approvals(session_id)),
            "trust_enabled_at": session.trust_enabled_at.isoformat() if session.trust_enabled_at else None
        }
