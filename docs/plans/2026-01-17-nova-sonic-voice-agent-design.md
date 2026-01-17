# Nova 2 Sonic Voice Agent Design

**Date:** 2026-01-17
**Status:** Approved
**Goal:** Replace ElevenLabs with Amazon Nova 2 Sonic for voice agent

---

## Executive Summary

Build a mobile-first PWA voice interface using Amazon Nova 2 Sonic (speech-to-speech model) to replace the current ElevenLabs-based `/av` endpoint. Nova orchestrates conversations and has access to all MCP tools directly, plus an explicit `ask_claude` tool for complex reasoning tasks.

**Key decisions:**
- Nova 2 Sonic as voice layer + orchestrator
- Claude via `ask_claude` tool for complex tasks (full MCP access)
- All MCP skills exposed as Nova tools
- Single user, single stream (no auth complexity)
- Soft summarization with generous limits (500K verbatim, 750K trigger)
- Neo-brutal UI style (cyan/magenta/yellow/black)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    BROWSER (Neo-Brutal PWA)                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Cyan/Magenta/Yellow  │  Black borders  │  Bold sans-serif│  │
│  │  Waveform bar  │  Scrolling transcript  │  Mic button     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              ↕ WebSocket                        │
└─────────────────────────────────────────────────────────────────┘
                               ↕
┌─────────────────────────────────────────────────────────────────┐
│                      NOVA SONIC SERVICE                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    NovaBridge                            │   │
│  │  • Single global instance (one stream at a time)        │   │
│  │  • Browser WebSocket ↔ Nova audio proxy                 │   │
│  │  • Tool execution on toolUse events                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ↕                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              NovaConversationManager                     │   │
│  │  • 1M token context (Nova's limit)                      │   │
│  │  • 500K verbatim, summarize at 750K                     │   │
│  │  • Claude-based intelligent summarization               │   │
│  │  • Persists to conversation.json                        │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                               ↕
              AWS Bedrock (Nova 2 Sonic) ←→ MCP Server (32 tools)
                               ↕
                    Claude API (via ask_claude tool)
```

---

## Technical Requirements

### Python Environment

**Version:** 3.12+ (required for experimental AWS SDK)

**Installation:**
```bash
# Experimental SDK (not on PyPI - must install from GitHub)
pip install git+https://github.com/awslabs/aws-sdk-python.git#subdirectory=clients/aws-sdk-bedrock-runtime

# Dependencies
pip install pyaudio smithy-aws-core flask flask-sock tiktoken anthropic
```

### Audio Formats

| Direction | Sample Rate | Format | Channels | Encoding |
|-----------|-------------|--------|----------|----------|
| Input (mic → Nova) | 16kHz | 16-bit PCM | Mono | base64 |
| Output (Nova → speakers) | 24kHz | 16-bit PCM | Mono | base64 |

**Note:** Different sample rates - don't mix them.

### AWS Configuration

- **Region:** us-west-2 (Oregon) or us-east-1
- **Model ID:** `amazon.nova-2-sonic-v1:0`
- **Credentials:** Environment variables or `~/.aws/credentials`

---

## Event Flow

Complete bidirectional stream protocol:

```
1.  sessionStart           → Configure inference + turn detection
2.  promptStart            → System prompt + tool definitions
3.  textContentStart       → System message begins
4.  textContentDelta       → System message chunks
5.  textContentEnd         → System message complete
6.  audioInputStart        → Signal start of user speech (REQUIRED)
7.  audioInput             → Stream user audio chunks
8.  audioInputEnd          → Signal end of user speech (REQUIRED)
9.  turnDetected           → Nova detected natural pause
10. textOutput             → Transcription / response text
11. toolUse                → Nova requests tool execution
12. toolResult             → Tool response
13. audioOutput            → Nova's speech response
14. contentEnd             → Turn complete
15. sessionEnd             → Close session (REQUIRED for graceful shutdown)
```

---

## Tool Configuration

### Tool Registration (promptStart event)

```json
{
  "event": {
    "promptStart": {
      "promptName": "voice-agent-session",
      "audioOutputConfiguration": {
        "mediaType": "audio/lpcm",
        "sampleRateHertz": 24000,
        "sampleSizeBits": 16,
        "channelCount": 1,
        "voiceId": "matthew",
        "encoding": "base64",
        "audioType": "SPEECH"
      },
      "toolConfiguration": {
        "tools": [
          {
            "toolSpec": {
              "name": "keno_analytics",
              "description": "Fetch Keno Empire revenue, DAU, and retention metrics",
              "inputSchema": {
                "json": {
                  "type": "object",
                  "properties": {
                    "metric": {
                      "type": "string",
                      "enum": ["revenue", "dau", "retention"]
                    },
                    "date": {"type": "string"}
                  },
                  "required": ["metric"]
                }
              }
            }
          },
          {
            "toolSpec": {
              "name": "ask_claude",
              "description": "For complex analysis, documents, code, multi-step reasoning tasks. Use when you need Claude's deep thinking.",
              "inputSchema": {
                "json": {
                  "type": "object",
                  "properties": {
                    "query": {
                      "type": "string",
                      "description": "The question or task for Claude"
                    }
                  },
                  "required": ["query"]
                }
              }
            }
          }
        ],
        "toolChoice": {"auto": {}}
      }
    }
  }
}
```

### Turn Detection

```json
{
  "sessionStart": {
    "inferenceConfiguration": {
      "maxTokens": 1024,
      "topP": 0.9,
      "temperature": 0.7
    },
    "turnDetectionConfiguration": {
      "endpointingSensitivity": "MEDIUM"
    }
  }
}
```

**Sensitivity levels:**
- `LOW`: Waits longer (technical discussions)
- `MEDIUM`: Balanced (default)
- `HIGH`: Quick response (rapid back-and-forth)

---

## Tool Execution

### MCP Tools (Direct)

```python
async def execute_tool(tool_name: str, params: dict) -> dict:
    if tool_name == "keno_analytics":
        return await mcp_client.call("keno_analytics", params)
    elif tool_name == "shortcuts_list":
        return await mcp_client.call("shortcuts_list", {})
    elif tool_name == "shortcuts_execute":
        return await mcp_client.call("shortcuts_execute", params)
    elif tool_name == "ask_claude":
        return await ask_claude(params["query"])
    # ... other MCP tools
```

### ask_claude Implementation

```python
from anthropic import Anthropic

CLAUDE_MODEL = "claude-sonnet-4-5-20250514"

async def ask_claude(query: str) -> str:
    """
    Route complex queries to Claude with full MCP access.
    Claude Agent SDK handles conversation state + tool use.
    """
    client = Anthropic()

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        system="You are called via voice. Provide concise responses optimized for speech. Avoid code blocks and markdown.",
        messages=[{"role": "user", "content": query}],
        tools=get_mcp_tool_definitions(),  # All 32 MCP tools
    )

    # Handle tool use loop if Claude needs tools
    while response.stop_reason == "tool_use":
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = await mcp_client.call(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result)
                })

        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": query},
                {"role": "assistant", "content": response.content},
                {"role": "user", "content": tool_results}
            ],
            tools=get_mcp_tool_definitions(),
        )

    # Extract text response
    return "".join(
        block.text for block in response.content
        if hasattr(block, "text")
    )
```

---

## Conversation Management

### Thresholds

| Parameter | Value | Notes |
|-----------|-------|-------|
| max_tokens | 1,000,000 | Nova's context limit |
| verbatim_keep | 500,000 | Always keep recent 500K verbatim |
| summarize_threshold | 750,000 | Trigger summarization at 75% |
| summary_max_tokens | 4,000 | Max size of compressed summary |

### Summarization Strategy

1. Keep recent 500K tokens verbatim (no loss)
2. At 750K total, summarize oldest messages
3. Use Claude Haiku for fast, cheap summarization
4. Chain summaries if conversation continues very long
5. Manual reset: say "start fresh" or "new conversation"

### Claude-Based Summarization

```python
async def create_indexed_summary(
    messages: List[Message],
    existing_summary: Optional[str]
) -> str:
    """Use Claude Haiku to create intelligent summary."""

    transcript = "\n".join(
        f"{'User' if m.role == 'user' else 'Nova'}: {m.content}"
        for m in messages
    )

    prompt = f"""Summarize this conversation for context continuity.

EXISTING CONTEXT:
{existing_summary or "None"}

NEW MESSAGES:
{transcript}

Preserve:
- Key facts and decisions
- User preferences mentioned
- Ongoing tasks/commitments
- Important names, dates, numbers

Format as concise bullet points. Max 2000 tokens."""

    response = await claude_client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text
```

---

## PWA Interface

### Layout

```
┌────────────────────────────────────────┐
│  ██ VOICE AGENT ██          [status]  │  ← Header (cyan bg, black border)
├────────────────────────────────────────┤
│  ┌──────────────────────────────────┐  │
│  │ ∿∿∿ waveform / listening ∿∿∿    │  │  ← Small feedback bar (40-60px)
│  └──────────────────────────────────┘  │
├────────────────────────────────────────┤
│                                        │
│  You: What's on my calendar today?     │  ← Scrolling transcript
│                                        │     (main area, auto-scroll)
│  Agent: You have 3 meetings...         │
│  [📅 calendar tool]                    │     Tool calls shown inline
│                                        │
│  You: Send Allen an email about...     │
│                                        │
│  Agent: I've drafted an email...       │
│  [✉️ email tool]                       │
│                                        │
├────────────────────────────────────────┤
│     ┌────────────────────────────────┐ │
│     │      🎤 TAP TO SPEAK           │ │  ← Mic button (magenta, fixed)
│     └────────────────────────────────┘ │
└────────────────────────────────────────┘
```

### Visual Design

- **Colors:** Cyan (#00FFFF), Magenta (#FF3366), Yellow (#FFFF00), Black, White
- **Borders:** 4-6px solid black
- **Typography:** Bold sans-serif (Arial Black / system-ui)
- **Shadows:** Hard offset (4px 4px 0px #000)

### States

| State | Mic Button | Waveform | Transcript |
|-------|------------|----------|------------|
| Idle | Solid magenta, "Tap to speak" | Flat line | Shows history |
| Listening | Pulsing, cyan glow | Animating input | "Listening..." |
| Processing | Spinner | Flat | "Thinking..." |
| Speaking | Dimmed | Animating output | Response appears |
| Tool use | Yellow flash | Brief pause | Tool badge shown |

---

## File Structure

```
mega-agent2/
├── nova_sonic_service.py          # Flask app (~50 lines)
├── nova_sonic/
│   ├── __init__.py
│   ├── config.py                  # Constants (~30 lines)
│   ├── client.py                  # BedrockRuntimeClient wrapper (~100 lines)
│   ├── event_handler.py           # Parse/route events (~80 lines)
│   ├── audio_bridge.py            # WebSocket ↔ Nova (~120 lines)
│   ├── tool_registry.py           # MCP → Nova schemas (~60 lines)
│   ├── mcp_executor.py            # Execute MCP tools (~40 lines)
│   ├── claude_bridge.py           # ask_claude impl (~80 lines)
│   └── conversation_manager.py    # Adapted for Nova (~200 lines)
├── static/nova/
│   ├── index.html                 # Neo-brutal UI (~80 lines)
│   ├── app.js                     # Mic/WebSocket/audio (~150 lines)
│   └── style.css                  # Neo-brutal styles (~50 lines)
└── conversation.json              # Persistent transcript
```

**Total:** ~800 lines of code

---

## Implementation Order

```
1. nova_sonic/config.py
   Define constants (model ID, audio rates, thresholds)
   Test: Import works

2. nova_sonic/client.py
   Get bidirectional stream working
   Test: Connect to Nova, receive events

3. nova_sonic/event_handler.py
   Parse events, log everything
   Test: See all event types in console

4. nova_sonic/audio_bridge.py
   Wire WebSocket ↔ Nova
   Test: Talk to Nova, hear response

5. nova_sonic/mcp_executor.py
   Execute tools directly
   Test: "What's revenue?" → tool runs → Nova speaks

6. nova_sonic/tool_registry.py
   Register all MCP tools with Nova
   Test: Nova sees all tools

7. nova_sonic/claude_bridge.py
   Route complex queries to Claude
   Test: "Analyze this..." → Claude handles

8. nova_sonic/conversation_manager.py
   Adapt for Nova's 1M context
   Test: Long conversation persists correctly

9. nova_sonic_service.py
   Flask wrapper
   Test: Browser → Flask → Nova → Browser

10. static/nova/
    Neo-brutal PWA interface
    Test: Works in Chrome
```

---

## Browser Compatibility

- **Required:** Google Chrome (16kHz mic streaming)
- **May not work:** Firefox, Safari (audio sample rate limitations)

---

## References

- [AWS Nova 2 Sonic Docs](https://docs.aws.amazon.com/nova/latest/nova2-userguide/sonic-tool-configuration.html)
- [AWS Nova Samples](https://github.com/aws-samples/amazon-nova-samples/tree/main/speech-to-speech/amazon-nova-2-sonic)
- [Experimental Python SDK](https://github.com/awslabs/aws-sdk-python)
