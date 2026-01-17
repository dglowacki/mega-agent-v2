"""
Nova Conversation Manager

Manages conversation state with generous limits for Nova's 1M context window.
Single user, single conversation.
"""

import asyncio
import json
import logging
import tiktoken
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from . import config
from .claude_bridge import summarize_for_context

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """A single message in the conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    token_count: int = 0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "token_count": self.token_count,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            token_count=data.get("token_count", 0),
            metadata=data.get("metadata", {})
        )


@dataclass
class Conversation:
    """Single conversation with message history."""
    id: str = "main"
    messages: List[Message] = field(default_factory=list)
    total_tokens: int = 0
    summary: Optional[str] = None
    summary_tokens: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "messages": [m.to_dict() for m in self.messages],
            "total_tokens": self.total_tokens,
            "summary": self.summary,
            "summary_tokens": self.summary_tokens,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Conversation":
        return cls(
            id=data.get("id", "main"),
            messages=[Message.from_dict(m) for m in data.get("messages", [])],
            total_tokens=data.get("total_tokens", 0),
            summary=data.get("summary"),
            summary_tokens=data.get("summary_tokens", 0),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            last_activity=datetime.fromisoformat(data["last_activity"]) if "last_activity" in data else datetime.now()
        )


class NovaConversationManager:
    """
    Conversation manager optimized for Nova's 1M token context.

    Features:
    - Generous verbatim threshold (500K tokens)
    - Claude-based intelligent summarization
    - Single file persistence
    """

    def __init__(self, persistence_file: str = None):
        self.max_tokens = config.CONTEXT_MAX_TOKENS
        self.verbatim_keep = config.VERBATIM_KEEP_TOKENS
        self.summarize_threshold = config.SUMMARIZE_THRESHOLD
        self.summary_max_tokens = config.SUMMARY_MAX_TOKENS

        self.persistence_file = Path(persistence_file or config.CONVERSATION_FILE)

        # Initialize tokenizer
        try:
            self._tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self._tokenizer = None
            logger.warning("tiktoken not available, using rough estimates")

        # Load or create conversation
        self._conversation: Optional[Conversation] = None

    @property
    def conversation(self) -> Conversation:
        """Get the current conversation, loading from disk if needed."""
        if self._conversation is None:
            self._conversation = self._load() or Conversation()
        return self._conversation

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self._tokenizer:
            return len(self._tokenizer.encode(text))
        # Rough estimate: 4 chars per token
        return len(text) // 4

    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[dict] = None
    ) -> Message:
        """
        Add a message to the conversation.

        Args:
            role: "user" or "assistant"
            content: Message content
            metadata: Optional metadata

        Returns:
            The created Message
        """
        conv = self.conversation

        token_count = self.count_tokens(content)
        message = Message(
            role=role,
            content=content,
            token_count=token_count,
            metadata=metadata or {}
        )

        conv.messages.append(message)
        conv.total_tokens += token_count
        conv.last_activity = datetime.now()

        # Check if we need to summarize
        if conv.total_tokens > self.summarize_threshold:
            asyncio.create_task(self._manage_context_window())

        # Save
        self._save()

        return message

    async def _manage_context_window(self) -> None:
        """
        Manage context window by summarizing old messages.

        Strategy:
        - Keep most recent 500K tokens verbatim
        - Summarize older messages using Claude Haiku
        """
        conv = self.conversation

        if conv.total_tokens <= self.summarize_threshold:
            return

        logger.info(f"Managing context: {conv.total_tokens} tokens, threshold: {self.summarize_threshold}")

        # Find split point to keep verbatim_keep tokens
        keep_tokens = 0
        split_idx = len(conv.messages)

        for i, msg in enumerate(reversed(conv.messages)):
            if keep_tokens + msg.token_count > self.verbatim_keep:
                split_idx = len(conv.messages) - i
                break
            keep_tokens += msg.token_count

        if split_idx == 0:
            logger.info("No messages to summarize")
            return

        # Split messages
        old_messages = conv.messages[:split_idx]
        recent_messages = conv.messages[split_idx:]

        logger.info(f"Summarizing {len(old_messages)} old messages, keeping {len(recent_messages)} recent")

        # Format old messages for summarization
        old_text_parts = []
        if conv.summary:
            old_text_parts.append(f"[Previous context]\n{conv.summary}\n")

        for msg in old_messages:
            prefix = "User" if msg.role == "user" else "Nova"
            old_text_parts.append(f"{prefix}: {msg.content}")

        old_text = "\n".join(old_text_parts)

        # Summarize using Claude Haiku
        try:
            new_summary = await summarize_for_context(old_text, self.summary_max_tokens)
            conv.summary = new_summary
            conv.summary_tokens = self.count_tokens(new_summary)
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            # Fallback: truncate
            conv.summary = old_text[:self.summary_max_tokens * 4]
            conv.summary_tokens = self.count_tokens(conv.summary)

        # Update conversation
        conv.messages = recent_messages
        conv.total_tokens = conv.summary_tokens + keep_tokens

        logger.info(f"Context compressed to {conv.total_tokens} tokens")

        # Save
        self._save()

    def get_context_for_nova(self) -> str:
        """
        Get conversation context formatted for Nova's system prompt.

        Returns:
            Formatted context string
        """
        conv = self.conversation
        parts = []

        if conv.summary:
            parts.append("[Conversation Summary]")
            parts.append(conv.summary)
            parts.append("")

        if conv.messages:
            parts.append("[Recent Conversation]")
            for msg in conv.messages[-50:]:  # Last 50 messages
                prefix = "User" if msg.role == "user" else "Assistant"
                parts.append(f"{prefix}: {msg.content}")

        return "\n".join(parts)

    def clear(self) -> None:
        """Clear the conversation (start fresh)."""
        self._conversation = Conversation()
        self._save()
        logger.info("Conversation cleared")

    def get_stats(self) -> dict:
        """Get conversation statistics."""
        conv = self.conversation
        return {
            "message_count": len(conv.messages),
            "total_tokens": conv.total_tokens,
            "has_summary": conv.summary is not None,
            "summary_tokens": conv.summary_tokens,
            "created_at": conv.created_at.isoformat(),
            "last_activity": conv.last_activity.isoformat()
        }

    def _save(self) -> None:
        """Save conversation to disk."""
        try:
            self.persistence_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.persistence_file, "w") as f:
                json.dump(self.conversation.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")

    def _load(self) -> Optional[Conversation]:
        """Load conversation from disk."""
        if not self.persistence_file.exists():
            return None

        try:
            with open(self.persistence_file) as f:
                data = json.load(f)
            return Conversation.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load conversation: {e}")
            return None


# Global instance
conversation_manager = NovaConversationManager()
