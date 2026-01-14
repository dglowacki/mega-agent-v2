"""
Voice Bridge - Connects Grok Voice API with Claude Agent SDK.

This module bridges voice I/O (via Grok) with the Claude agent system,
enabling spoken conversations with all available agents.

Architecture:
    Audio Input → Grok STT → Claude Agents → Grok TTS → Audio Output
"""

import asyncio
import json
import subprocess
import sys
from typing import Optional, Callable, Awaitable
from integrations.grok_voice_client import GrokVoiceClient


class VoiceBridge:
    """
    Bridges Grok Voice with Claude Agent SDK.

    Handles:
    - Voice-to-text via Grok
    - Text processing via Claude agents
    - Text-to-voice via Grok
    - Streaming responses
    """

    def __init__(
        self,
        voice: str = "Ara",
        sample_rate: int = 24000
    ):
        """
        Initialize Voice Bridge.

        Args:
            voice: Grok voice to use (Ara, Rex, Sal, Eve, Leo)
            sample_rate: Audio sample rate
        """
        self.voice = voice
        self.sample_rate = sample_rate

        self.grok = GrokVoiceClient()
        # Query runner script for isolated subprocess execution
        self.query_runner = "/home/ec2-user/mega-agent2/voice_query_runner.py"

        # State
        self.is_connected = False
        self.is_processing = False

        # Callbacks for external handling
        self.on_user_speech: Optional[Callable[[str], None]] = None
        self.on_claude_response: Optional[Callable[[str], None]] = None
        self.on_audio_output: Optional[Callable[[bytes], None]] = None
        self.on_thinking: Optional[Callable[[bool], None]] = None

    async def connect(self) -> None:
        """Connect to Grok Voice API."""
        print("Connecting to Grok Voice API...", flush=True)
        # Grok handles voice personality, Claude handles text responses
        instructions = """Transcribe audio accurately. Facts must be represented EXACTLY. Add commentary or color as needed, have a clever personality.

VOCABULARY CONTEXT (for accurate transcription):
- Names: Dave, Jess, Allen
- Projects: EH! (pronounced like letter "A", a social media app), TrailMix, Fieldy, Mega Agent
- Companies: FlyCow Games, Trail Mix Technologies
- Technical: Claude, Grok, MCP, WebSocket, API, GitHub, AWS
"""

        try:
            await asyncio.wait_for(
                self.grok.connect(
                    voice=self.voice,
                    instructions=instructions,
                    sample_rate=self.sample_rate,
                    use_vad=True  # Server-side voice activity detection
                ),
                timeout=30
            )
            self.is_connected = True
            print("Connected to Grok Voice API", flush=True)
        except asyncio.TimeoutError:
            print("Timeout connecting to Grok Voice API", flush=True)
            raise
        except Exception as e:
            print(f"Error connecting to Grok: {e}", flush=True)
            raise

    async def process_transcription(self, text: str) -> str:
        """
        Process transcribed text through Claude agents.

        Args:
            text: Transcribed user speech

        Returns:
            Claude's response text
        """
        if self.on_user_speech:
            self.on_user_speech(text)

        if self.on_thinking:
            self.on_thinking(True)

        self.is_processing = True
        response_text = ""

        try:
            # Run query in isolated subprocess to avoid async context issues
            process = await asyncio.create_subprocess_exec(
                sys.executable, self.query_runner, text,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=60  # 60 second timeout
            )

            if stderr:
                print(f"Query stderr: {stderr.decode()}", flush=True)

            if stdout:
                try:
                    result = json.loads(stdout.decode().strip())
                    if result.get("success"):
                        response_text = result.get("response", "")
                    else:
                        response_text = result.get("response", "I had trouble processing that.")
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}, output: {stdout.decode()[:200]}", flush=True)
                    response_text = "I had trouble processing that request."

        except asyncio.TimeoutError:
            print("Query timeout", flush=True)
            response_text = "I'm taking too long to think. Please try again."

        except Exception as e:
            print(f"Query error: {e}", flush=True)
            response_text = f"I encountered an error: {str(e)}"

        finally:
            self.is_processing = False
            if self.on_thinking:
                self.on_thinking(False)

        if self.on_claude_response:
            self.on_claude_response(response_text)

        return response_text

    async def speak_response(self, text: str) -> None:
        """
        Send text to Grok for TTS synthesis.

        Args:
            text: Text for Grok to speak
        """
        # Clean text for speech (remove markdown, code blocks, etc.)
        clean_text = self._clean_for_speech(text)

        await self.grok.send_assistant_text(clean_text)

    def _clean_for_speech(self, text: str) -> str:
        """
        Clean text for spoken output.

        Removes markdown formatting, code blocks, URLs, etc.
        """
        import re

        # Remove code blocks
        text = re.sub(r'```[\s\S]*?```', ' (code block omitted) ', text)
        text = re.sub(r'`[^`]+`', '', text)

        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)

        # Remove markdown formatting
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*([^*]+)\*', r'\1', text)      # Italic
        text = re.sub(r'#{1,6}\s+', '', text)           # Headers
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)  # Lists
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)  # Numbered lists

        # Remove extra whitespace
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    async def send_audio(self, audio_data: bytes) -> None:
        """
        Send audio chunk to Grok for processing.

        Args:
            audio_data: Raw PCM audio bytes
        """
        await self.grok.send_audio(audio_data)

    async def run_voice_loop(self) -> None:
        """
        Main voice conversation loop.

        Listens for transcriptions, processes through Claude,
        and sends responses back as speech.
        """
        if not self.is_connected:
            await self.connect()

        audio_buffer = bytearray()

        async for msg in self.grok.receive_messages():
            msg_type = msg.get("type", "")

            # User finished speaking - transcription incoming
            if msg_type == "conversation.item.input_audio_transcription.completed":
                transcript = msg.get("transcript", "").strip()

                if transcript:
                    # Process through Claude
                    response = await self.process_transcription(transcript)

                    # Inject Claude's response into Grok's conversation history
                    # so Grok has context for future turns (prevents hallucination)
                    if response:
                        await self.grok.add_assistant_context(response)

            # Audio response chunk from TTS
            elif msg_type == "response.output_audio.delta":
                audio_b64 = msg.get("delta", "")
                if audio_b64:
                    import base64
                    audio_bytes = base64.b64decode(audio_b64)
                    audio_buffer.extend(audio_bytes)

            # Audio response complete
            elif msg_type == "response.output_audio.done":
                if audio_buffer and self.on_audio_output:
                    self.on_audio_output(bytes(audio_buffer))
                audio_buffer.clear()

            # Handle errors
            elif msg_type == "error":
                error = msg.get("error", {}).get("message", "Unknown error")
                print(f"Grok error: {error}", flush=True)

    async def close(self) -> None:
        """Close connections."""
        await self.grok.close()
        self.is_connected = False


class VoiceConversation:
    """
    High-level interface for voice conversations.

    Provides a simple API for starting and managing voice sessions.
    """

    def __init__(
        self,
        voice: str = "Ara",
        agent: Optional[str] = "voice-agent"
    ):
        self.bridge = VoiceBridge(voice=voice, agent=agent)
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the voice conversation."""
        await self.bridge.connect()
        self._task = asyncio.create_task(self.bridge.run_voice_loop())

    async def send_audio(self, audio_data: bytes) -> None:
        """Send audio to the conversation."""
        await self.bridge.send_audio(audio_data)

    async def stop(self) -> None:
        """Stop the voice conversation."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self.bridge.close()

    def on_response(self, callback: Callable[[str], None]) -> None:
        """Set callback for Claude's text responses."""
        self.bridge.on_claude_response = callback

    def on_audio(self, callback: Callable[[bytes], None]) -> None:
        """Set callback for audio output."""
        self.bridge.on_audio_output = callback

    def on_user_speech(self, callback: Callable[[str], None]) -> None:
        """Set callback for user's transcribed speech."""
        self.bridge.on_user_speech = callback


# Simple test
async def _test():
    """Test the voice bridge."""
    bridge = VoiceBridge()

    bridge.on_user_speech = lambda t: print(f"You said: {t}")
    bridge.on_claude_response = lambda t: print(f"Claude: {t}")

    await bridge.connect()
    print("Voice bridge connected. Listening...")

    await bridge.run_voice_loop()


if __name__ == "__main__":
    asyncio.run(_test())
