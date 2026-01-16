"""
Session Tools - Approval mode and session management.

Provides tools for managing safe/trust mode and session state.
"""

import logging
from typing import Optional

from ..security import SecurityManager, ApprovalMode

logger = logging.getLogger(__name__)

# Module-level references (set during registration)
_security_manager: Optional[SecurityManager] = None
_session_id: str = "default"


def session_get_mode() -> str:
    """
    Get the current approval mode.

    Returns:
        Current mode description
    """
    if not _security_manager:
        return "Error: Security manager not configured"

    stats = _security_manager.get_session_stats(_session_id)
    mode = stats["mode"]

    if mode == "safe":
        return """Current mode: SAFE
- Read operations auto-approved
- Write operations require verbal confirmation
- Say "do it" to enable trust mode"""
    else:
        return """Current mode: TRUST
- All operations auto-approved
- No confirmation required
- Trust mode enabled at: """ + (stats.get("trust_enabled_at") or "unknown")


def session_enable_trust() -> str:
    """
    Enable trust mode (auto-approve all operations).

    Returns:
        Confirmation message
    """
    if not _security_manager:
        return "Error: Security manager not configured"

    _security_manager.set_mode(_session_id, ApprovalMode.TRUST)
    return "Trust mode enabled. All operations will be auto-approved."


def session_enable_safe() -> str:
    """
    Enable safe mode (confirm write operations).

    Returns:
        Confirmation message
    """
    if not _security_manager:
        return "Error: Security manager not configured"

    _security_manager.set_mode(_session_id, ApprovalMode.SAFE)
    return "Safe mode enabled. Write operations will require confirmation."


def session_get_stats() -> str:
    """
    Get session statistics.

    Returns:
        Session statistics
    """
    if not _security_manager:
        return "Error: Security manager not configured"

    stats = _security_manager.get_session_stats(_session_id)

    return f"""Session Statistics
-----------------
Session ID: {stats['session_id']}
Mode: {stats['mode']}
Created: {stats['created_at']}
Approved tools: {', '.join(stats['approved_tools']) or 'none'}
Pending approvals: {stats['pending_approvals']}
Trust enabled: {stats.get('trust_enabled_at') or 'never'}"""


def session_list_approved() -> str:
    """
    List tools that have been approved this session.

    Returns:
        List of approved tools
    """
    if not _security_manager:
        return "Error: Security manager not configured"

    stats = _security_manager.get_session_stats(_session_id)
    approved = stats.get('approved_tools', [])

    if not approved:
        return "No tools have been explicitly approved yet."

    return "Approved tools:\n" + "\n".join(f"  - {tool}" for tool in approved)


def session_clear_approvals() -> str:
    """
    Clear all tool approvals (reset to requiring confirmation).

    Returns:
        Confirmation message
    """
    if not _security_manager:
        return "Error: Security manager not configured"

    session = _security_manager.get_or_create_session(_session_id)
    count = len(session.approved_tools)
    session.approved_tools.clear()

    return f"Cleared {count} tool approvals. All write operations will require confirmation again."


def register_session_tools(
    server,
    security_manager: SecurityManager = None,
    session_id: str = "default"
) -> int:
    """Register all session tools with the MCP server."""
    global _security_manager, _session_id

    _security_manager = security_manager
    _session_id = session_id

    server.register_tool(
        name="session_get_mode",
        description="Get the current approval mode (safe or trust).",
        input_schema={
            "type": "object",
            "properties": {}
        },
        handler=session_get_mode,
        requires_approval=False,
        category="session"
    )

    server.register_tool(
        name="session_enable_trust",
        description="Enable trust mode - all operations auto-approved without confirmation.",
        input_schema={
            "type": "object",
            "properties": {}
        },
        handler=session_enable_trust,
        requires_approval=False,
        category="session"
    )

    server.register_tool(
        name="session_enable_safe",
        description="Enable safe mode - write operations require verbal confirmation.",
        input_schema={
            "type": "object",
            "properties": {}
        },
        handler=session_enable_safe,
        requires_approval=False,
        category="session"
    )

    server.register_tool(
        name="session_get_stats",
        description="Get statistics about the current session.",
        input_schema={
            "type": "object",
            "properties": {}
        },
        handler=session_get_stats,
        requires_approval=False,
        category="session"
    )

    server.register_tool(
        name="session_list_approved",
        description="List tools that have been approved this session.",
        input_schema={
            "type": "object",
            "properties": {}
        },
        handler=session_list_approved,
        requires_approval=False,
        category="session"
    )

    server.register_tool(
        name="session_clear_approvals",
        description="Clear all tool approvals and reset to requiring confirmation.",
        input_schema={
            "type": "object",
            "properties": {}
        },
        handler=session_clear_approvals,
        requires_approval=False,
        category="session"
    )

    return 6  # Number of tools registered
