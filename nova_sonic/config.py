"""
Nova Sonic Configuration

Constants for Amazon Nova 2 Sonic speech-to-speech integration.
"""

# AWS Configuration
AWS_REGION = "us-east-1"
NOVA_MODEL_ID = "amazon.nova-2-sonic-v1:0"
BEDROCK_ENDPOINT = f"https://bedrock-runtime.{AWS_REGION}.amazonaws.com"

# Audio Configuration
AUDIO_INPUT_SAMPLE_RATE = 16000  # 16kHz for input (mic -> Nova)
AUDIO_OUTPUT_SAMPLE_RATE = 24000  # 24kHz for output (Nova -> speakers)
AUDIO_SAMPLE_SIZE_BITS = 16
AUDIO_CHANNELS = 1  # Mono
AUDIO_ENCODING = "base64"

# Inference Configuration
MAX_TOKENS = 1024
TOP_P = 0.9
TEMPERATURE = 0.7

# Turn Detection
ENDPOINTING_SENSITIVITY = "MEDIUM"  # LOW, MEDIUM, HIGH

# Voice Configuration
VOICE_ID = "matthew"  # Default voice
AUDIO_TYPE = "SPEECH"

# Conversation Manager Thresholds
CONTEXT_MAX_TOKENS = 1_000_000  # Nova's full context window
VERBATIM_KEEP_TOKENS = 500_000  # Keep recent 500K verbatim
SUMMARIZE_THRESHOLD = 750_000  # Trigger summarization at 75%
SUMMARY_MAX_TOKENS = 4000  # Max size of compressed summary

# Claude Configuration (for ask_claude tool)
CLAUDE_MODEL = "claude-sonnet-4-5-20250514"
CLAUDE_HAIKU_MODEL = "claude-3-5-haiku-20241022"  # For summarization

# WebSocket Configuration
WS_PING_INTERVAL = 30  # seconds
WS_PING_TIMEOUT = 10  # seconds

# MCP Server
MCP_SERVER_URL = "http://localhost:8082"

# Persistence
CONVERSATION_FILE = "conversation.json"
