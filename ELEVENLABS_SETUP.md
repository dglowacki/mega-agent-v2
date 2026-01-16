# ElevenLabs Voice Assistant Setup

This guide explains how to configure ElevenLabs Conversational AI with your Claude Agent SDK.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        YOUR SERVER                               │
│                                                                  │
│  ┌──────────────┐     ┌─────────────────────────────────────┐  │
│  │ voice_service│     │ elevenlabs_llm.py                   │  │
│  │ .py          │     │ (Custom LLM Endpoint)               │  │
│  │              │     │                                     │  │
│  │ /av/eleven   │     │ POST /v1/chat/completions           │  │
│  │ /av/signed-  │     │  - Receives messages from ElevenLabs │  │
│  │   url        │     │  - Runs Claude Agent SDK             │  │
│  └──────────────┘     │  - Returns streaming response        │  │
│         │             └─────────────────────────────────────┘  │
│         │                              ▲                        │
│         │ Signed URL                   │ OpenAI-format API      │
│         ▼                              │                        │
└─────────┼──────────────────────────────┼────────────────────────┘
          │                              │
          ▼                              │
┌─────────────────────────────────────────────────────────────────┐
│                    ELEVENLABS CLOUD                              │
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────────────┐  │
│  │ STT      │───▶│ Your     │───▶│ Custom LLM               │  │
│  │ (Whisper)│    │ Agent    │    │ (calls your endpoint)    │  │
│  └──────────┘    └──────────┘    └──────────────────────────┘  │
│       ▲                                         │               │
│       │                                         ▼               │
│  ┌──────────┐                          ┌──────────┐            │
│  │ Mic      │                          │ TTS      │            │
│  │ Input    │                          │ (Voice)  │            │
│  └──────────┘                          └──────────┘            │
│                                                                 │
│              User's Browser (Widget)                            │
└─────────────────────────────────────────────────────────────────┘
```

## Step 1: Get ElevenLabs API Key

1. Go to https://elevenlabs.io and sign up or log in
2. Click on your profile icon (top right)
3. Select "Profile + API key"
4. Copy your API key

## Step 2: Create an Agent in ElevenLabs

1. Go to https://elevenlabs.io/app/conversational-ai
2. Click "Create Agent" or "New Agent"
3. Configure basic settings:
   - **Name**: "Claude Voice Assistant" (or your preference)
   - **First Message**: "Hello! I'm your voice assistant. How can I help you today?"

### Configure LLM Settings

1. In your agent settings, go to **Model** or **LLM** section
2. Select **Custom LLM**
3. Configure:
   - **URL**: `https://YOUR_DOMAIN/av/llm/chat/completions`
     - Replace `YOUR_DOMAIN` with your server's public URL
     - Example: `https://a.fcow.ca/av/llm/chat/completions`
   - **Model Name**: `claude-agent-sdk`
   - **Enable "Custom LLM extra body"**: Yes (allows passing session info)

### Configure Authentication

1. Go to **Security** tab in agent settings
2. Enable **Agent Authentication**
3. Add your domain to the **Allowlist**:
   - `a.fcow.ca` (or your domain)
   - Add `localhost:5050` for local testing if needed

### Configure Voice

1. Go to **Voice** section
2. Select a voice (e.g., "Rachel", "Adam", or any voice you prefer)
3. Adjust settings as needed

### Get Your Agent ID

1. After saving, find your Agent ID in the URL or settings
2. It looks like: `agent_2601kf1fmbnseaxvp5kvc4zc21bz`

## Step 3: Configure Your Server

### Set Environment Variables

Add to your `.bashrc` or environment:

```bash
export ELEVENLABS_API_KEY="your-api-key-here"
export ELEVENLABS_AGENT_ID="agent_2601kf1fmbnseaxvp5kvc4zc21bz"
```

Or create a `.env` file:

```
ELEVENLABS_API_KEY=your-api-key-here
ELEVENLABS_AGENT_ID=agent_2601kf1fmbnseaxvp5kvc4zc21bz
```

### Start the Services

```bash
# Start the Custom LLM endpoint (port 8080)
python elevenlabs_llm.py --port 8080 &

# Start the voice service (port 5050)
python voice_service.py --port 5050 &
```

### Configure nginx (for public access)

Add to your nginx config:

```nginx
# ElevenLabs Custom LLM endpoint
location /av/llm/ {
    proxy_pass http://127.0.0.1:8080/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # For streaming responses
    proxy_buffering off;
    proxy_cache off;
    chunked_transfer_encoding on;
}

# Voice service (existing)
location /av/ {
    proxy_pass http://127.0.0.1:5050/av/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
}
```

Reload nginx:
```bash
sudo nginx -t && sudo systemctl reload nginx
```

## Step 4: Test the Integration

1. Open your browser and go to: `https://your-domain/av/eleven`
2. Log in with your password
3. The page should show "Ready" status
4. Click the ElevenLabs widget to start talking

### Debug Endpoints

- Health check: `https://your-domain/av/health`
- Status: `https://your-domain/av/status`
- Signed URL test: `https://your-domain/av/signed-url` (requires auth)
- LLM health: `https://your-domain/av/llm/health`

## Security Model

### How Signed URLs Work

1. User authenticates on your page (password login)
2. Your server generates a signed URL using your ElevenLabs API key
3. Signed URL is valid for 15 minutes
4. Client uses signed URL to connect to ElevenLabs
5. No API keys are ever exposed to the client

### Domain Allowlist

ElevenLabs only accepts connections from domains you've whitelisted. This prevents:
- Other websites embedding your agent
- Unauthorized access to your agent

### Custom LLM Authentication (Optional)

For additional security, you can validate requests to your Custom LLM endpoint:

1. Enable "Custom LLM extra body" in ElevenLabs
2. Pass session tokens in the extra body from your widget
3. Validate tokens in your `elevenlabs_llm.py` endpoint

## Troubleshooting

### "ElevenLabs API key not configured"

Set the `ELEVENLABS_API_KEY` environment variable.

### "Failed to get signed URL"

1. Check your API key is valid
2. Check your Agent ID is correct
3. Ensure the agent has authentication enabled

### "Custom LLM not responding"

1. Verify `elevenlabs_llm.py` is running
2. Check nginx is proxying `/av/llm/` correctly
3. Test the endpoint directly: `curl -X POST https://your-domain/av/llm/v1/chat/completions`

### Widget not appearing

1. Check browser console for errors
2. Verify signed URL is being returned
3. Check ElevenLabs widget script is loading

## Files Reference

| File | Purpose |
|------|---------|
| `voice_service.py` | Main Flask app with `/av/eleven` and `/av/signed-url` |
| `elevenlabs_llm.py` | OpenAI-compatible endpoint wrapping Claude Agent SDK |
| `voice_orchestration/` | Context management (skills, history, user context) |

## API Reference

### GET /av/signed-url

Returns a signed URL for ElevenLabs connection.

**Requires**: Authentication (session cookie)

**Response**:
```json
{
  "signed_url": "wss://api.elevenlabs.io/..."
}
```

### POST /av/llm/v1/chat/completions

OpenAI-compatible chat completion endpoint called by ElevenLabs.

**Request**:
```json
{
  "messages": [
    {"role": "user", "content": "Hello"}
  ],
  "stream": true
}
```

**Response**: Server-Sent Events (SSE) stream in OpenAI format.
