"""
Grok Voice Client - WebSocket client for xAI Grok Voice Agent API.

Provides real-time voice I/O capabilities using xAI's Grok Voice API.
Handles WebSocket connection, audio streaming, and response handling.

API Documentation: https://docs.x.ai/docs/guides/voice/agent
"""

import asyncio
import base64
import json
import os
from typing import AsyncGenerator, Callable, Optional
import websockets
from websockets.client import WebSocketClientProtocol


class GrokVoiceClient:
    """
    WebSocket client for xAI Grok Voice Agent API.

    Provides:
    - Real-time audio streaming (send/receive)
    - Speech-to-text transcription
    - Text-to-speech synthesis
    - Server-side VAD (Voice Activity Detection)
    - Tool call handling
    """

    ENDPOINT = "wss://api.x.ai/v1/realtime"

    # Available voices
    VOICES = {
        "ara": "Ara (Female, warm/friendly)",
        "rex": "Rex (Male, confident/clear)",
        "sal": "Sal (Neutral, smooth/balanced)",
        "eve": "Eve (Female, energetic/upbeat)",
        "leo": "Leo (Male, authoritative/strong)"
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Grok Voice Client.

        Args:
            api_key: xAI API key. Defaults to XAI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("XAI_API_KEY")
        if not self.api_key:
            raise ValueError("XAI_API_KEY not set in environment or provided")

        self.ws: Optional[WebSocketClientProtocol] = None
        self.session_configured = False

        # Callbacks
        self.on_transcription: Optional[Callable[[str], None]] = None
        self.on_audio_response: Optional[Callable[[bytes], None]] = None
        self.on_text_response: Optional[Callable[[str], None]] = None
        self.on_speech_started: Optional[Callable[[], None]] = None
        self.on_speech_stopped: Optional[Callable[[], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None

    async def connect(
        self,
        voice: str = "Ara",
        instructions: str = "",
        sample_rate: int = 24000,
        use_vad: bool = True
    ) -> None:
        """
        Connect to Grok Voice API and configure session.

        Args:
            voice: Voice to use (Ara, Rex, Sal, Eve, Leo)
            instructions: System instructions for the voice agent
            sample_rate: Audio sample rate (8000-48000)
            use_vad: Enable server-side voice activity detection
        """
        self.ws = await websockets.connect(
            self.ENDPOINT,
            additional_headers={"Authorization": f"Bearer {self.api_key}"},
            ping_interval=30,
            ping_timeout=10
        )

        # Configure session
        session_config = {
            "type": "session.update",
            "session": {
                "voice": voice,
                "instructions": instructions,
                "turn_detection": {"type": "server_vad"} if use_vad else None,
                "audio": {
                    "input": {
                        "format": {
                            "type": "audio/pcm",
                            "rate": sample_rate
                        }
                    },
                    "output": {
                        "format": {
                            "type": "audio/pcm",
                            "rate": sample_rate
                        }
                    }
                }
            }
        }

        await self.ws.send(json.dumps(session_config))

        # Wait for session.updated confirmation
        async for msg in self.ws:
            data = json.loads(msg)
            if data.get("type") == "session.updated":
                self.session_configured = True
                break
            elif data.get("type") == "error":
                raise ConnectionError(f"Session config failed: {data}")

    async def send_audio(self, audio_data: bytes) -> None:
        """
        Send audio chunk to Grok for processing.

        Args:
            audio_data: Raw PCM audio bytes (16-bit, mono)
        """
        if not self.ws or not self.session_configured:
            raise RuntimeError("Not connected. Call connect() first.")

        encoded = base64.b64encode(audio_data).decode('utf-8')
        await self.ws.send(json.dumps({
            "type": "input_audio_buffer.append",
            "audio": encoded
        }))

    async def commit_audio(self) -> None:
        """
        Commit audio buffer (for manual VAD mode only).
        With server_vad, this is handled automatically.
        """
        if self.ws:
            await self.ws.send(json.dumps({
                "type": "input_audio_buffer.commit"
            }))

    async def clear_audio_buffer(self) -> None:
        """Clear the audio input buffer."""
        if self.ws:
            await self.ws.send(json.dumps({
                "type": "input_audio_buffer.clear"
            }))

    async def send_text(self, text: str) -> None:
        """
        Send text message (instead of audio).

        Args:
            text: Text to send to Grok
        """
        if not self.ws:
            raise RuntimeError("Not connected")

        await self.ws.send(json.dumps({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": text}]
            }
        }))

        # Trigger response
        await self.ws.send(json.dumps({"type": "response.create"}))

    async def add_assistant_context(self, text: str) -> None:
        """
        Add assistant response to conversation history WITHOUT generating audio.

        This injects context so Grok knows what was said, but doesn't trigger TTS.

        Args:
            text: Assistant's response text to add to history
        """
        if not self.ws:
            raise RuntimeError("Not connected")

        await self.ws.send(json.dumps({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": text}]
            }
        }))
        # Note: NOT calling response.create - just adding to history

    async def send_assistant_text(self, text: str) -> None:
        """
        Send assistant response text for TTS synthesis.

        Note: This adds the text as an assistant message and generates audio.
        The response.create with modalities=["audio"] ensures we only get
        audio synthesis, not additional AI-generated content.

        Args:
            text: Text for Grok to speak
        """
        if not self.ws:
            raise RuntimeError("Not connected")

        await self.ws.send(json.dumps({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": text}]
            }
        }))

        # Generate audio only - no additional AI text generation
        await self.ws.send(json.dumps({
            "type": "response.create",
            "response": {
                "modalities": ["audio"]
            }
        }))

    async def send_function_result(self, call_id: str, result: str) -> None:
        """
        Send function call result back to Grok.

        Args:
            call_id: The function call ID from the request
            result: JSON string result of the function
        """
        if not self.ws:
            raise RuntimeError("Not connected")

        await self.ws.send(json.dumps({
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "call_id": call_id,
                "output": result
            }
        }))

        # Continue conversation
        await self.ws.send(json.dumps({"type": "response.create"}))

    async def receive_messages(self) -> AsyncGenerator[dict, None]:
        """
        Async generator yielding incoming messages from Grok.

        Yields:
            dict: Parsed JSON message from the WebSocket
        """
        if not self.ws:
            raise RuntimeError("Not connected")

        async for message in self.ws:
            data = json.loads(message)
            yield data

    async def listen(self) -> None:
        """
        Main event loop - process incoming messages and trigger callbacks.

        This handles:
        - Speech detection events
        - Transcription results
        - Audio responses
        - Text responses
        - Errors
        """
        if not self.ws:
            raise RuntimeError("Not connected")

        audio_buffer = bytearray()
        transcript_buffer = ""

        async for msg in self.receive_messages():
            msg_type = msg.get("type", "")

            # Speech detection
            if msg_type == "input_audio_buffer.speech_started":
                if self.on_speech_started:
                    self.on_speech_started()

            elif msg_type == "input_audio_buffer.speech_stopped":
                if self.on_speech_stopped:
                    self.on_speech_stopped()

            # Transcription
            elif msg_type == "conversation.item.input_audio_transcription.completed":
                transcript = msg.get("transcript", "")
                if transcript and self.on_transcription:
                    self.on_transcription(transcript)

            # Audio response chunks
            elif msg_type == "response.output_audio.delta":
                audio_b64 = msg.get("delta", "")
                if audio_b64:
                    audio_bytes = base64.b64decode(audio_b64)
                    audio_buffer.extend(audio_bytes)

            elif msg_type == "response.output_audio.done":
                if audio_buffer and self.on_audio_response:
                    self.on_audio_response(bytes(audio_buffer))
                audio_buffer.clear()

            # Text response chunks
            elif msg_type == "response.output_audio_transcript.delta":
                text = msg.get("delta", "")
                transcript_buffer += text

            elif msg_type == "response.output_audio_transcript.done":
                if transcript_buffer and self.on_text_response:
                    self.on_text_response(transcript_buffer)
                transcript_buffer = ""

            # Function calls (tool use)
            elif msg_type == "response.function_call_arguments.done":
                # This would need external handling
                pass

            # Errors
            elif msg_type == "error":
                error_msg = msg.get("error", {}).get("message", "Unknown error")
                if self.on_error:
                    self.on_error(error_msg)

    async def close(self) -> None:
        """Close the WebSocket connection."""
        if self.ws:
            await self.ws.close()
            self.ws = None
            self.session_configured = False


# Convenience function for quick usage
async def transcribe_audio(audio_data: bytes, api_key: Optional[str] = None) -> str:
    """
    Quick transcription of audio data.

    Args:
        audio_data: Raw PCM audio bytes
        api_key: Optional API key

    Returns:
        Transcribed text
    """
    client = GrokVoiceClient(api_key)
    result = ""

    def on_transcript(text: str):
        nonlocal result
        result = text

    client.on_transcription = on_transcript

    await client.connect(use_vad=False)
    await client.send_audio(audio_data)
    await client.commit_audio()

    # Wait for transcription
    async for msg in client.receive_messages():
        if msg.get("type") == "conversation.item.input_audio_transcription.completed":
            result = msg.get("transcript", "")
            break

    await client.close()
    return result
