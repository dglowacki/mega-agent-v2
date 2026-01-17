"""
Nova Sonic Event Handler

Parses and routes events from Nova 2 Sonic.
"""

import base64
import json
import logging
from dataclasses import dataclass
from typing import Optional, Callable, Awaitable, Any
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Nova Sonic event types."""
    # Session events
    SESSION_START = "sessionStart"
    SESSION_END = "sessionEnd"

    # Content events
    CONTENT_START = "contentStart"
    CONTENT_END = "contentEnd"
    COMPLETION_END = "completionEnd"

    # Text events
    TEXT_OUTPUT = "textOutput"

    # Audio events
    AUDIO_OUTPUT = "audioOutput"

    # Tool events
    TOOL_USE = "toolUse"

    # Turn detection
    TURN_DETECTED = "turnDetected"

    # Error
    ERROR = "error"

    # Unknown
    UNKNOWN = "unknown"


@dataclass
class ParsedEvent:
    """A parsed Nova event."""
    type: EventType
    role: Optional[str] = None
    content: Optional[str] = None
    audio_bytes: Optional[bytes] = None
    tool_name: Optional[str] = None
    tool_use_id: Optional[str] = None
    tool_input: Optional[dict] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    interrupted: bool = False
    raw: Optional[dict] = None


class EventHandler:
    """
    Handles Nova 2 Sonic events.

    Parses events and dispatches to registered callbacks.
    """

    def __init__(self):
        self._handlers: dict[EventType, list[Callable]] = {}

    def on(self, event_type: EventType, handler: Callable[[ParsedEvent], Awaitable[None]]) -> None:
        """
        Register an event handler.

        Args:
            event_type: Type of event to handle
            handler: Async callback function
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def parse(self, raw_event: dict) -> ParsedEvent:
        """
        Parse a raw Nova event into a ParsedEvent.

        Args:
            raw_event: Raw event dictionary from Nova

        Returns:
            ParsedEvent with extracted data
        """
        event_data = raw_event.get("event", {})

        # Check for error
        if "error" in raw_event:
            return ParsedEvent(
                type=EventType.ERROR,
                error_code=raw_event["error"].get("code"),
                error_message=raw_event["error"].get("message"),
                raw=raw_event
            )

        # Determine event type
        event_type = EventType.UNKNOWN
        for key in event_data:
            try:
                event_type = EventType(key)
                break
            except ValueError:
                continue

        parsed = ParsedEvent(type=event_type, raw=raw_event)

        # Extract type-specific data
        inner = event_data.get(event_type.value, {})

        if event_type == EventType.TEXT_OUTPUT:
            parsed.content = inner.get("content", "")
            parsed.role = inner.get("role")

        elif event_type == EventType.AUDIO_OUTPUT:
            audio_b64 = inner.get("content", "")
            if audio_b64:
                parsed.audio_bytes = base64.b64decode(audio_b64)

        elif event_type == EventType.TOOL_USE:
            parsed.tool_name = inner.get("toolName")
            parsed.tool_use_id = inner.get("toolUseId")
            parsed.role = inner.get("role")
            # Parse tool input
            content = inner.get("content", "{}")
            try:
                parsed.tool_input = json.loads(content) if isinstance(content, str) else content
            except json.JSONDecodeError:
                parsed.tool_input = {"raw": content}

        elif event_type == EventType.CONTENT_START:
            parsed.role = inner.get("role")

        elif event_type == EventType.TURN_DETECTED:
            # Check for interruption
            parsed.interrupted = inner.get("interrupted", False)

        return parsed

    async def dispatch(self, parsed: ParsedEvent) -> None:
        """
        Dispatch a parsed event to registered handlers.

        Args:
            parsed: Parsed event to dispatch
        """
        handlers = self._handlers.get(parsed.type, [])
        for handler in handlers:
            try:
                await handler(parsed)
            except Exception as e:
                logger.error(f"Error in handler for {parsed.type}: {e}")

    async def handle(self, raw_event: dict) -> ParsedEvent:
        """
        Parse and dispatch an event.

        Args:
            raw_event: Raw event from Nova

        Returns:
            Parsed event
        """
        parsed = self.parse(raw_event)
        await self.dispatch(parsed)
        return parsed


# Default event handler instance
default_handler = EventHandler()


def log_all_events(parsed: ParsedEvent) -> None:
    """Debug handler that logs all events."""
    if parsed.type == EventType.AUDIO_OUTPUT:
        size = len(parsed.audio_bytes) if parsed.audio_bytes else 0
        logger.debug(f"Event: {parsed.type.value} (audio: {size} bytes)")
    elif parsed.type == EventType.TEXT_OUTPUT:
        logger.debug(f"Event: {parsed.type.value} - {parsed.content[:100] if parsed.content else ''}")
    elif parsed.type == EventType.TOOL_USE:
        logger.info(f"Event: {parsed.type.value} - {parsed.tool_name}({parsed.tool_input})")
    elif parsed.type == EventType.ERROR:
        logger.error(f"Event: ERROR - {parsed.error_code}: {parsed.error_message}")
    else:
        logger.debug(f"Event: {parsed.type.value}")
