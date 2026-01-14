# Grok Voice Agent + Claude Agent SDK Integration Plan

## Goal
Enable voice conversations with the existing Claude Agent SDK multi-agent system by integrating xAI's Grok Voice Agent API as the voice interface layer.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User's Device                                │
│  ┌─────────────┐                              ┌─────────────────┐   │
│  │ Microphone  │ ──audio──►                   │    Speaker      │   │
│  └─────────────┘           │                  └─────────────────┘   │
└────────────────────────────│──────────────────────────▲─────────────┘
                             │                          │
                             ▼                          │
┌─────────────────────────────────────────────────────────────────────┐
│                      Voice Gateway Server                            │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                  WebSocket Handler                              │ │
│  │  • Accept audio from client                                     │ │
│  │  • Forward to Grok Voice API                                    │ │
│  │  • Relay responses back to client                               │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                             │                          ▲             │
│                             ▼                          │             │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              Grok Voice WebSocket Client                        │ │
│  │  • wss://api.x.ai/v1/realtime                                  │ │
│  │  • STT: Audio → Text transcription                              │ │
│  │  • TTS: Text → Audio synthesis                                  │ │
│  │  • Voice: Ara/Rex/Sal/Eve/Leo                                   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                             │                          ▲             │
│                             ▼                          │             │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              Claude Agent SDK Bridge                            │ │
│  │  • Receives transcribed text from Grok                          │ │
│  │  • Calls query() with text prompt                               │ │
│  │  • Streams responses back to Grok for TTS                       │ │
│  │  • Handles tool calls via existing MCP servers                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Two Integration Approaches

### Option A: Direct WebSocket Integration (Recommended)
Build a custom voice gateway that:
1. Connects to xAI Grok Voice API via WebSocket
2. Uses Grok for STT (speech-to-text) and TTS (text-to-speech)
3. Pipes transcribed text to Claude Agent SDK's `query()` function
4. Streams Claude responses back through Grok for voice synthesis

**Pros:**
- Full control over the integration
- Direct use of existing Claude Agent SDK patterns
- Claude handles all the intelligence/reasoning
- Grok just handles voice I/O

**Cons:**
- More code to write
- Need to manage two WebSocket connections

### Option B: LiveKit Integration
Use xAI's official LiveKit plugin with their agent framework.

**Pros:**
- Pre-built infrastructure for voice agents
- WebRTC support for better audio quality
- Room-based multi-party conversations

**Cons:**
- Requires learning LiveKit framework
- May need to adapt existing agent architecture
- Less direct integration with Claude Agent SDK

---

## Recommended Approach: Option A (Direct Integration)

### Implementation Components

#### 1. Voice Gateway Server (`voice_gateway.py`)
A Python WebSocket server that:
- Accepts audio streams from clients (browser/app)
- Maintains connection to xAI Grok Voice API
- Bridges voice I/O with Claude Agent SDK

#### 2. Grok Voice Client (`integrations/grok_voice_client.py`)
WebSocket client for xAI's realtime API:
- Session management and configuration
- Audio buffer handling (base64 PCM)
- Response streaming
- Tool call forwarding

#### 3. Voice Agent Definition (`agents.py` addition)
New agent type optimized for voice interactions:
- Concise responses suitable for speech
- Voice-appropriate system prompts
- Optional: route to specialized agents via Task tool

#### 4. Client Interface Options
- **Web Browser**: HTML5 + WebSocket + Web Audio API
- **CLI**: PyAudio-based terminal interface
- **Mobile**: React Native or Flutter app

---

## Detailed Implementation Steps

### Step 1: Create Grok Voice Client

```python
# integrations/grok_voice_client.py
import asyncio
import websockets
import json
import base64
import os

class GrokVoiceClient:
    """WebSocket client for xAI Grok Voice Agent API."""

    def __init__(self):
        self.ws = None
        self.api_key = os.getenv("XAI_API_KEY")
        self.uri = "wss://api.x.ai/v1/realtime"

    async def connect(self, voice="Ara", instructions=""):
        """Connect to Grok Voice API."""
        self.ws = await websockets.connect(
            self.uri,
            additional_headers={"Authorization": f"Bearer {self.api_key}"}
        )

        # Configure session
        await self.ws.send(json.dumps({
            "type": "session.update",
            "session": {
                "voice": voice,
                "instructions": instructions,
                "turn_detection": {"type": "server_vad"},
                "audio": {
                    "input": {"format": {"type": "audio/pcm", "rate": 24000}},
                    "output": {"format": {"type": "audio/pcm", "rate": 24000}}
                }
            }
        }))

    async def send_audio(self, audio_bytes: bytes):
        """Send audio chunk to Grok."""
        encoded = base64.b64encode(audio_bytes).decode('utf-8')
        await self.ws.send(json.dumps({
            "type": "input_audio_buffer.append",
            "audio": encoded
        }))

    async def receive_messages(self):
        """Async generator for incoming messages."""
        async for message in self.ws:
            yield json.loads(message)

    async def close(self):
        if self.ws:
            await self.ws.close()
```

### Step 2: Create Voice Bridge

```python
# voice_bridge.py
import asyncio
from claude_agent_sdk import query
from agents import get_agent_options
from integrations.grok_voice_client import GrokVoiceClient

class VoiceBridge:
    """Bridges Grok Voice with Claude Agent SDK."""

    def __init__(self):
        self.grok = GrokVoiceClient()
        self.options = get_agent_options()

    async def start(self):
        await self.grok.connect(
            voice="Ara",
            instructions="You handle voice transcription. Forward all queries."
        )

    async def handle_transcription(self, text: str):
        """Process transcribed text through Claude."""
        response_text = ""

        async for message in query(
            prompt=text,
            options=self.options,
            agent=None  # Let orchestrator decide
        ):
            if hasattr(message, "content"):
                for content in message.content:
                    if hasattr(content, "text"):
                        response_text += content.text

        return response_text

    async def send_response_as_speech(self, text: str):
        """Send text to Grok for TTS synthesis."""
        await self.grok.ws.send(json.dumps({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "input_text", "text": text}]
            }
        }))
        await self.grok.ws.send(json.dumps({"type": "response.create"}))
```

### Step 3: Create Voice Gateway Server

```python
# voice_gateway.py
import asyncio
import websockets
import json
from voice_bridge import VoiceBridge

class VoiceGateway:
    """WebSocket server for voice clients."""

    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.bridge = VoiceBridge()

    async def handle_client(self, websocket):
        """Handle a connected voice client."""
        await self.bridge.start()

        # Listen for Grok events and forward to client
        async def forward_grok_events():
            async for msg in self.bridge.grok.receive_messages():
                if msg["type"] == "input_audio_buffer.speech_stopped":
                    # Transcription coming...
                    pass
                elif msg["type"] == "conversation.item.input_audio_transcription.completed":
                    # Got transcription, send to Claude
                    text = msg["transcript"]
                    response = await self.bridge.handle_transcription(text)
                    await self.bridge.send_response_as_speech(response)
                elif msg["type"] == "response.output_audio.delta":
                    # Forward audio to client
                    await websocket.send(json.dumps({
                        "type": "audio",
                        "data": msg["delta"]
                    }))

        # Listen for client audio
        async def receive_client_audio():
            async for message in websocket:
                data = json.loads(message)
                if data["type"] == "audio":
                    await self.bridge.grok.send_audio(
                        base64.b64decode(data["data"])
                    )

        await asyncio.gather(forward_grok_events(), receive_client_audio())

    async def start(self):
        async with websockets.serve(self.handle_client, self.host, self.port):
            print(f"Voice Gateway running on ws://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever

if __name__ == "__main__":
    gateway = VoiceGateway()
    asyncio.run(gateway.start())
```

### Step 4: Add Voice-Optimized Agent

Add to `agents.py`:

```python
"voice-agent": AgentDefinition(
    description="Voice-optimized agent for spoken conversations",
    prompt="""You are a voice assistant powered by Claude.

IMPORTANT: Your responses will be spoken aloud, so:
- Keep responses concise (1-3 sentences when possible)
- Avoid bullet points, markdown, or formatting
- Use natural conversational language
- Spell out numbers and abbreviations
- Don't include URLs or code blocks in responses

You can delegate to specialized agents using the Task tool:
- "Send a Slack message" → communication-agent
- "Check my calendar" → scheduling-agent
- "What's in my email" → communication-agent
- "GitHub status" → code-agent

For complex tasks, briefly explain what you're doing, then delegate.""",
    tools=["Read", "Bash", "Task", "Skill"],
    model="sonnet"
),
```

### Step 5: Web Client (Optional)

```html
<!-- voice_client.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Claude Voice Assistant</title>
</head>
<body>
    <button id="start">Start Conversation</button>
    <div id="status">Ready</div>

    <script>
    const ws = new WebSocket('ws://localhost:8765');
    let audioContext, mediaRecorder;

    document.getElementById('start').onclick = async () => {
        audioContext = new AudioContext({ sampleRate: 24000 });
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        // Send audio to server
        const processor = audioContext.createScriptProcessor(4096, 1, 1);
        const source = audioContext.createMediaStreamSource(stream);
        source.connect(processor);
        processor.connect(audioContext.destination);

        processor.onaudioprocess = (e) => {
            const pcm = e.inputBuffer.getChannelData(0);
            const int16 = new Int16Array(pcm.length);
            for (let i = 0; i < pcm.length; i++) {
                int16[i] = Math.max(-32768, Math.min(32767, pcm[i] * 32768));
            }
            ws.send(JSON.stringify({
                type: 'audio',
                data: btoa(String.fromCharCode(...new Uint8Array(int16.buffer)))
            }));
        };
    };

    // Play received audio
    ws.onmessage = async (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === 'audio') {
            const bytes = atob(msg.data);
            const buffer = new Int16Array(bytes.length / 2);
            for (let i = 0; i < buffer.length; i++) {
                buffer[i] = bytes.charCodeAt(i*2) | (bytes.charCodeAt(i*2+1) << 8);
            }
            // Play audio...
        }
    };
    </script>
</body>
</html>
```

---

## File Structure After Implementation

```
/home/ec2-user/mega-agent2/
├── main.py                         # Existing CLI entry
├── voice_gateway.py                # NEW: Voice WebSocket server
├── voice_bridge.py                 # NEW: Grok↔Claude bridge
├── agents.py                       # MODIFY: Add voice-agent
├── integrations/
│   ├── grok_voice_client.py       # NEW: xAI Voice API client
│   ├── slack_client.py
│   ├── gmail_client.py
│   └── ...
├── static/
│   └── voice_client.html          # NEW: Web interface
└── requirements.txt               # MODIFY: Add websockets
```

## Dependencies to Add

```
# requirements.txt additions
websockets>=12.0
numpy>=1.24.0  # For audio processing
```

## Environment Variables

Already configured in `.env`:
```
XAI_API_KEY=[REDACTED - stored in .env]
```

---

## Implementation Phases

### Phase 1: Core Voice Bridge
1. Create `grok_voice_client.py` with WebSocket connection
2. Create `voice_bridge.py` to connect Grok↔Claude
3. Test transcription and basic responses

### Phase 2: Gateway Server
1. Create `voice_gateway.py` WebSocket server
2. Handle audio streaming from clients
3. Forward responses back to clients

### Phase 3: Voice Agent
1. Add `voice-agent` to `agents.py`
2. Tune prompts for spoken responses
3. Test delegation to other agents

### Phase 4: Client Interface
1. Create web client with Web Audio API
2. Optionally: CLI client with PyAudio
3. Optionally: Mobile app

---

## Alternative: Simpler CLI-Only Voice

For a quick terminal-based voice interface:

```python
# voice_cli.py
import asyncio
import sounddevice as sd
import numpy as np
from integrations.grok_voice_client import GrokVoiceClient
from claude_agent_sdk import query
from agents import get_agent_options

async def main():
    grok = GrokVoiceClient()
    options = get_agent_options()

    await grok.connect(voice="Ara")

    # Record audio
    print("Listening... (speak now)")
    audio = sd.rec(int(5 * 24000), samplerate=24000, channels=1, dtype='int16')
    sd.wait()

    # Send to Grok for transcription
    await grok.send_audio(audio.tobytes())

    # Get transcription
    async for msg in grok.receive_messages():
        if msg["type"] == "conversation.item.input_audio_transcription.completed":
            text = msg["transcript"]
            print(f"You said: {text}")

            # Send to Claude
            response = ""
            async for message in query(prompt=text, options=options):
                if hasattr(message, "content"):
                    for c in message.content:
                        if hasattr(c, "text"):
                            response += c.text

            print(f"Claude: {response}")
            # Could send response back to Grok for TTS here
            break

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Questions to Resolve

1. **Audio capture method**: Web browser, CLI with PyAudio, or mobile app?
2. **Deployment**: Local only, or accessible remotely (requires HTTPS/WSS)?
3. **Voice preference**: Which Grok voice (Ara, Rex, Sal, Eve, Leo)?
4. **Wake word**: Always listening, or push-to-talk?
5. **Agent routing**: Use orchestrator, or direct to voice-agent?

---

## Sources

- [xAI Grok Voice Agent API](https://docs.x.ai/docs/guides/voice/agent)
- [xAI LiveKit Plugin](https://docs.livekit.io/agents/models/realtime/plugins/xai/)
- [LiveKit xAI Partnership](https://blog.livekit.io/xai-livekit-partnership-grok-voice-agent-api/)
