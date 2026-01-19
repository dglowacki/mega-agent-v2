"""
Voice Bridge - Connects Grok Voice API with Claude Agent SDK.

This module bridges voice I/O (via Grok) with the Claude agent system,
enabling spoken conversations with all available agents.

Architecture:
    Audio Input → Grok STT → Voice Orchestration → Claude Agents → Grok TTS → Audio Output

Components:
    - ConversationManager: Maintains conversation history across turns
    - SkillsRegistry: Discovers available capabilities
    - UserContext: User preferences and session info
    - ContextBuilder: Assembles complete context for queries
"""

import asyncio
import json
import subprocess
import sys
import uuid
from typing import Optional, Callable, Awaitable
from integrations.grok_voice_client import GrokVoiceClient
from voice_orchestration import (
    ConversationManager,
    SkillsRegistry,
    UserContext,
    ContextBuilder
)
from voice_orchestration.user_context import create_default_user_context


class VoiceBridge:
    """
    Bridges Grok Voice with Claude Agent SDK.

    Handles:
    - Voice-to-text via Grok
    - Context management via Voice Orchestration
    - Text processing via Claude agents
    - Text-to-voice via Grok
    - Streaming responses
    """

    def __init__(
        self,
        voice: str = "Ara",
        sample_rate: int = 24000,
        conversation_id: Optional[str] = None,
        persistence_dir: Optional[str] = None
    ):
        """
        Initialize Voice Bridge.

        Args:
            voice: Grok voice to use (Ara, Rex, Sal, Eve, Leo)
            sample_rate: Audio sample rate
            conversation_id: Optional ID for conversation persistence
            persistence_dir: Directory for session persistence
        """
        self.voice = voice
        self.sample_rate = sample_rate

        # Generate conversation ID if not provided
        self.conversation_id = conversation_id or str(uuid.uuid4())[:8]

        # Initialize Grok client
        self.grok = GrokVoiceClient()

        # Query runner script for isolated subprocess execution
        self.query_runner = "/home/ec2-user/mega-agent2/voice_query_runner.py"

        # Initialize Voice Orchestration components
        self.conversation_manager = ConversationManager(
            max_tokens=8000,
            summarize_threshold=6000,
            keep_recent_messages=10,
            persistence_dir=persistence_dir
        )

        self.skills_registry = SkillsRegistry(
            skills_path=".claude/skills",
            refresh_interval=300
        )
        # Discover skills on init
        self.skills_registry.discover(base_path="/home/ec2-user/mega-agent2")

        self.user_context = create_default_user_context()

        self.context_builder = ContextBuilder(
            conversation_manager=self.conversation_manager,
            skills_registry=self.skills_registry,
            user_context=self.user_context,
            max_total_tokens=8000
        )

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

        # Build vocabulary from user context
        vocab_items = []

        # Add contacts
        for contact in self.user_context.contacts.values():
            vocab_items.append(contact.name)

        # Add projects with pronunciations
        for project in self.user_context.projects.values():
            if project.pronunciation:
                vocab_items.append(f'{project.name} (pronounced {project.pronunciation})')
            else:
                vocab_items.append(project.name)

        # Grok instructions - factual only, no interpretation
        instructions = f"""You are a voice interface. Your ONLY job is to:
1. Transcribe user speech accurately
2. Read back responses exactly as provided - NO additions, NO commentary, NO interpretation

CRITICAL RULES:
- DO NOT add opinions or personality
- DO NOT paraphrase or summarize - read responses VERBATIM
- DO NOT make up facts or add information not in the response
- If you receive a response, speak it exactly as written

VOCABULARY (for accurate transcription):
- Names: {', '.join(c.name for c in self.user_context.contacts.values()) or 'Dave, Jess, Allen'}
- Projects: {', '.join(vocab_items) or 'EH! (pronounced like letter "A"), TrailMix, Fieldy, Mega Agent'}
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

            # Log skills discovered
            stats = self.skills_registry.get_stats()
            print(f"Skills registry: {stats['total_skills']} skills in {len(stats['categories'])} categories", flush=True)

        except asyncio.TimeoutError:
            print("Timeout connecting to Grok Voice API", flush=True)
            raise
        except Exception as e:
            print(f"Error connecting to Grok: {e}", flush=True)
            raise

    async def process_transcription(self, text: str) -> str:
        """
        Process transcribed text through Claude agents with full context.

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
            # Add user message to conversation history
            self.conversation_manager.add_message(
                self.conversation_id,
                role="user",
                content=text,
                metadata={"source": "voice"}
            )

            # Increment interaction count
            self.user_context.increment_interaction()

            # Build full context
            full_prompt = self.context_builder.build_full_prompt(
                self.conversation_id,
                text,
                include_skills=True,
                include_user_context=True,
                voice_mode=True
            )

            # Get system prompt for the query
            system_prompt = self.context_builder.get_system_prompt(
                include_skills=True,
                include_user_context=True,
                voice_mode=True
            )

            # Run query in isolated subprocess
            process = await asyncio.create_subprocess_exec(
                sys.executable, self.query_runner,
                "--prompt", text,
                "--system", system_prompt,
                "--history", self.conversation_manager.format_history_for_prompt(
                    self.conversation_id, max_tokens=4000
                ),
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

            # Add assistant response to conversation history
            if response_text:
                self.conversation_manager.add_message(
                    self.conversation_id,
                    role="assistant",
                    content=response_text,
                    metadata={"source": "claude"}
                )

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
                    # Process through Claude with full context
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

    def get_conversation_stats(self) -> dict:
        """Get statistics about the current conversation."""
        conv_stats = self.conversation_manager.get_conversation_stats(self.conversation_id)
        skills_stats = self.skills_registry.get_stats()

        return {
            "conversation": conv_stats,
            "skills": skills_stats,
            "user_context": {
                "timezone": self.user_context.timezone,
                "location": self.user_context.location,
                "contacts": len(self.user_context.contacts),
                "projects": len(self.user_context.projects),
                "interaction_count": self.user_context.interaction_count,
                "session_duration": self.user_context.get_session_duration()
            }
        }

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
        conversation_id: Optional[str] = None
    ):
        self.bridge = VoiceBridge(voice=voice, conversation_id=conversation_id)
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
    print(f"Stats: {bridge.get_conversation_stats()}")

    await bridge.run_voice_loop()


if __name__ == "__main__":
    asyncio.run(_test())
