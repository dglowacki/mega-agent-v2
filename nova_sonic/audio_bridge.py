"""
Nova Sonic Audio Bridge

Bridges browser WebSocket audio to Nova 2 Sonic bidirectional stream.
Single user, single stream at a time.
"""

import asyncio
import base64
import json
import logging
import os
from datetime import datetime
from typing import Optional, Callable, Awaitable

from .client import NovaSonicClient
from .event_handler import EventHandler, EventType, ParsedEvent
from .tool_registry import get_tool_definitions
from .mcp_executor import execute_tool
from . import config

logger = logging.getLogger(__name__)

# Transcript log directory
TRANSCRIPT_DIR = "/home/ec2-user/mega-agent2/logs/transcripts"
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)


class NovaBridge:
    """
    Single-stream bridge between browser WebSocket and Nova 2 Sonic.

    Handles:
    - Browser audio → Nova
    - Nova audio → Browser
    - Tool execution
    - Transcript logging
    """

    def __init__(self):
        self.client: Optional[NovaSonicClient] = None
        self.event_handler = EventHandler()
        self.active = False
        self._transcript: list[dict] = []
        self._ws = None
        self._on_transcript: Optional[Callable[[str, str], Awaitable[None]]] = None
        self._session_id: Optional[str] = None
        self._transcript_file: Optional[str] = None

    def is_active(self) -> bool:
        """Check if a session is currently active."""
        return self.active

    async def handle_websocket(self, ws) -> None:
        """
        Handle a WebSocket connection from browser.

        Args:
            ws: Flask-Sock WebSocket connection
        """
        # If a session is "active" but stale, force cleanup
        if self.active:
            logger.warning("Forcing cleanup of stale session")
            await self._cleanup()

        self._ws = ws
        self.active = True
        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._transcript_file = os.path.join(TRANSCRIPT_DIR, f"nova_{self._session_id}.log")
        self._log_transcript("SESSION", "Nova voice session started")
        logger.info(f"Starting Nova bridge session: {self._session_id}")

        try:
            # Initialize Nova client
            self.client = NovaSonicClient()
            await self.client.connect()

            # Get tool definitions and send session start with tools
            tools = get_tool_definitions()
            await self.client.send_session_start(tools=tools)

            # Send prompt start (tools are in sessionStart)
            await self.client.send_prompt_start()

            # Send system message
            system_prompt = self._get_system_prompt()
            await self.client.send_system_message(system_prompt)

            # Register event handlers
            self._setup_event_handlers()

            # Send ready signal to browser
            await self._send_ws(ws, {"type": "ready"})

            # Run concurrent tasks
            await asyncio.gather(
                self._browser_to_nova(ws),
                self._nova_to_browser(ws),
                return_exceptions=True
            )

        except Exception as e:
            logger.error(f"Bridge error: {e}")
            await self._send_ws(ws, {"type": "error", "message": str(e)})

        finally:
            await self._cleanup()

    def _setup_event_handlers(self) -> None:
        """Set up event handlers for Nova events."""

        async def on_audio(event: ParsedEvent):
            if event.audio_bytes and self._ws:
                # Send audio to browser (24kHz)
                audio_b64 = base64.b64encode(event.audio_bytes).decode('utf-8')
                await self._send_ws(self._ws, {
                    "type": "audio",
                    "data": audio_b64
                })

        async def on_text(event: ParsedEvent):
            if event.content and self._ws:
                content = event.content.strip()

                # Skip JSON-like content (turn detection noise, metadata)
                if content.startswith('{') and content.endswith('}'):
                    return

                # Skip empty or whitespace-only content
                if not content:
                    return

                role = "assistant" if event.role != "USER" else "user"
                await self._send_ws(self._ws, {
                    "type": "transcript",
                    "role": role,
                    "content": content
                })
                # Log transcript to memory and file
                self._transcript.append({
                    "role": role,
                    "content": content
                })
                self._log_transcript(role, content)
                if self._on_transcript:
                    await self._on_transcript(role, content)

        async def on_tool_use(event: ParsedEvent):
            if event.tool_name and event.tool_use_id:
                logger.info(f"Tool use: {event.tool_name}")
                self._log_transcript("TOOL_CALL", f"{event.tool_name}({json.dumps(event.tool_input or {})})")

                # Notify browser
                await self._send_ws(self._ws, {
                    "type": "tool_use",
                    "tool": event.tool_name,
                    "input": event.tool_input
                })

                # Execute tool
                try:
                    result = await execute_tool(event.tool_name, event.tool_input or {})
                    result_str = str(result)[:500]  # Truncate for logging
                    self._log_transcript("TOOL_RESULT", f"{event.tool_name} -> {result_str}")
                    await self.client.send_tool_result(event.tool_use_id, result)

                    await self._send_ws(self._ws, {
                        "type": "tool_result",
                        "tool": event.tool_name,
                        "success": True
                    })

                except Exception as e:
                    logger.error(f"Tool execution error: {e}")
                    self._log_transcript("TOOL_ERROR", f"{event.tool_name} -> {str(e)}")
                    await self.client.send_tool_result(
                        event.tool_use_id,
                        {"error": str(e)}
                    )
                    await self._send_ws(self._ws, {
                        "type": "tool_result",
                        "tool": event.tool_name,
                        "success": False,
                        "error": str(e)
                    })

        async def on_error(event: ParsedEvent):
            logger.error(f"Nova error: {event.error_code} - {event.error_message}")
            if self._ws:
                await self._send_ws(self._ws, {
                    "type": "error",
                    "code": event.error_code,
                    "message": event.error_message
                })

        async def on_turn_detected(event: ParsedEvent):
            if self._ws:
                await self._send_ws(self._ws, {
                    "type": "turn_detected",
                    "interrupted": event.interrupted
                })

        self.event_handler.on(EventType.AUDIO_OUTPUT, on_audio)
        self.event_handler.on(EventType.TEXT_OUTPUT, on_text)
        self.event_handler.on(EventType.TOOL_USE, on_tool_use)
        self.event_handler.on(EventType.ERROR, on_error)
        self.event_handler.on(EventType.TURN_DETECTED, on_turn_detected)

    async def _browser_to_nova(self, ws) -> None:
        """Forward browser audio to Nova."""
        audio_started = False

        try:
            while self.active:
                try:
                    message = ws.receive(timeout=0.1)
                    if message is None:
                        continue

                    data = json.loads(message) if isinstance(message, str) else message

                    if data.get("type") == "audio_start":
                        if not audio_started:
                            await self.client.send_audio_start()
                            audio_started = True

                    elif data.get("type") == "audio":
                        # Decode base64 audio from browser
                        audio_bytes = base64.b64decode(data["data"])
                        await self.client.send_audio_chunk(audio_bytes)

                    elif data.get("type") == "audio_end":
                        if audio_started:
                            await self.client.send_audio_end()
                            audio_started = False

                    elif data.get("type") == "reset":
                        # User requested conversation reset
                        self._transcript = []
                        await self._send_ws(ws, {"type": "reset_confirmed"})

                    elif data.get("type") == "close":
                        break

                except TimeoutError:
                    continue
                except Exception as e:
                    if "closed" in str(e).lower():
                        break
                    logger.error(f"Browser to Nova error: {e}")

        except Exception as e:
            logger.error(f"Browser to Nova loop error: {e}")

        finally:
            if audio_started:
                try:
                    await self.client.send_audio_end()
                except Exception:
                    pass

    async def _nova_to_browser(self, ws) -> None:
        """Forward Nova events to browser."""
        try:
            async for event in self.client.receive_events():
                if not self.active:
                    break
                await self.event_handler.handle(event)

        except Exception as e:
            if self.active:
                logger.error(f"Nova to browser error: {e}")

    async def _send_ws(self, ws, data: dict) -> None:
        """Send JSON data to WebSocket."""
        try:
            ws.send(json.dumps(data))
        except Exception as e:
            logger.error(f"WebSocket send error: {e}")

    async def _cleanup(self) -> None:
        """Clean up resources."""
        if self._transcript_file:
            self._log_transcript("SESSION", "Nova voice session ended")
        self.active = False
        if self.client:
            try:
                await self.client.close()
            except Exception as e:
                logger.warning(f"Client cleanup error: {e}")
        self.client = None
        self._ws = None
        self._transcript_file = None
        logger.info("Nova bridge session ended")

    def _get_system_prompt(self) -> str:
        """Get system prompt for Nova."""
        return """You are Jesse's AI voice assistant with access to 110+ tools via the MCP server. You can help with a wide range of tasks.

YOUR CAPABILITIES:

1. INFORMATION & SEARCH
   - Web search for current information, news, weather
   - Get current time in any timezone
   - Weather forecasts for any location

2. CALENDAR & SCHEDULING
   - View upcoming Google Calendar events
   - Create new calendar events
   - Check availability and schedule meetings

3. COMMUNICATION
   - Send and read Gmail emails
   - Send Slack messages to channels or users
   - List recent Slack conversations

4. TASK MANAGEMENT
   - View and create Linear issues
   - Manage ClickUp tasks
   - Track project progress

5. DEVELOPER TOOLS
   - Read and search files
   - Run bash commands
   - Git operations (status, diff, commit, push)
   - GitHub PR and issue management

6. APP ANALYTICS
   - App Store Connect sales and downloads
   - Keno Empire app metrics

7. IMAGE GENERATION
   - Generate AI images from text descriptions
   - Send generated images to Slack users or channels
   - Create icons, banners, and artwork

8. COMPLEX REASONING
   - Use ask_claude for complex analysis, code review, document processing, or multi-step reasoning

VOICE OUTPUT GUIDELINES:
- Keep responses concise and conversational (2-3 sentences for simple questions)
- Avoid code blocks, markdown, or long lists in speech
- Use natural spoken language
- For multi-part answers, say "First", "Second", etc.
- When listing items, limit to top 3-5 and offer to share more

USER CONTEXT:
- Name: Jesse
- Timezone: Pacific Time (PT)
- Location: Parksville, BC, Canada
- Wife: Jess (jessglow@gmail.com personal, jess@ehnow.ca work)
- Friend: Allen (allen@alistsearch.com)
- Work email: dave@ehnow.ca (TrailMix Technologies)

When asked about your capabilities, briefly describe the categories above without going into excessive detail."""

    def _log_transcript(self, role: str, content: str) -> None:
        """Log transcript entry to file."""
        if self._transcript_file:
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(self._transcript_file, "a") as f:
                    f.write(f"[{timestamp}] {role.upper()}: {content}\n")
            except Exception as e:
                logger.error(f"Failed to log transcript: {e}")

    def get_transcript(self) -> list[dict]:
        """Get the current transcript."""
        return self._transcript.copy()

    def set_transcript_callback(
        self,
        callback: Callable[[str, str], Awaitable[None]]
    ) -> None:
        """Set callback for transcript updates."""
        self._on_transcript = callback


# Global singleton instance
nova_bridge = NovaBridge()
