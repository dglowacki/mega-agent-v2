#!/usr/bin/env python3
"""
ElevenLabs Conversational AI Agent Management API

Usage:
    python eleven_api.py get-config
    python eleven_api.py update-prompt "New prompt text"
    python eleven_api.py update-voice --speed 1.2 --stability 0.5
    python eleven_api.py list-mcp
    python eleven_api.py conversations [--limit 10]
    python eleven_api.py transcript <conversation_id>
"""

import argparse
import json
import os
import sys
import requests

API_KEY = os.getenv("ELEVENLABS_API_KEY", "sk_2cdc94ae356746a5f92093400fd79d45cc7fa196ff01a229")
AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID", "agent_2601kf1fmbnseaxvp5kvc4zc21bz")
BASE_URL = "https://api.elevenlabs.io/v1/convai"


def get_headers():
    return {
        "xi-api-key": API_KEY,
        "Content-Type": "application/json"
    }


def get_config():
    """Get current agent configuration."""
    url = f"{BASE_URL}/agents/{AGENT_ID}"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()
    return response.json()


def update_prompt(prompt: str):
    """Update agent system prompt."""
    url = f"{BASE_URL}/agents/{AGENT_ID}"
    payload = {
        "conversation_config": {
            "agent": {
                "prompt": {
                    "prompt": prompt
                }
            }
        }
    }
    response = requests.patch(url, headers=get_headers(), json=payload)
    response.raise_for_status()
    return {"status": "success", "message": "Prompt updated"}


def update_voice(voice_id: str = None, speed: float = None,
                 stability: float = None, similarity_boost: float = None):
    """Update voice settings."""
    url = f"{BASE_URL}/agents/{AGENT_ID}"

    tts_config = {}
    if voice_id:
        tts_config["voice_id"] = voice_id
    if speed:
        tts_config["speed"] = speed
    if stability:
        tts_config["stability"] = stability
    if similarity_boost:
        tts_config["similarity_boost"] = similarity_boost

    if not tts_config:
        return {"error": "No voice settings provided"}

    payload = {
        "conversation_config": {
            "tts": tts_config
        }
    }
    response = requests.patch(url, headers=get_headers(), json=payload)
    response.raise_for_status()
    return {"status": "success", "message": "Voice settings updated", "settings": tts_config}


def list_mcp_servers():
    """List linked MCP servers."""
    config = get_config()
    prompt_config = config.get("conversation_config", {}).get("agent", {}).get("prompt", {})
    mcp_server_ids = prompt_config.get("mcp_server_ids", [])

    servers = []
    for server_id in mcp_server_ids:
        url = f"{BASE_URL}/mcp-servers/{server_id}"
        response = requests.get(url, headers=get_headers())
        if response.status_code == 200:
            servers.append(response.json())

    return {"mcp_servers": servers}


def get_conversations(limit: int = 10):
    """Get recent conversations."""
    url = f"{BASE_URL}/conversations?agent_id={AGENT_ID}"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()
    data = response.json()

    conversations = data.get("conversations", [])[:limit]
    return {
        "count": len(conversations),
        "conversations": [
            {
                "id": c.get("conversation_id"),
                "title": c.get("call_summary_title"),
                "duration": c.get("call_duration_secs"),
                "status": c.get("status"),
                "messages": c.get("message_count")
            }
            for c in conversations
        ]
    }


def get_transcript(conversation_id: str):
    """Get conversation transcript."""
    url = f"{BASE_URL}/conversations/{conversation_id}"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()
    data = response.json()

    transcript = []
    for entry in data.get("transcript", []):
        transcript.append({
            "role": entry.get("role"),
            "message": entry.get("message", "")[:500]
        })

    return {
        "conversation_id": conversation_id,
        "status": data.get("status"),
        "transcript": transcript
    }


def main():
    parser = argparse.ArgumentParser(description="ElevenLabs Agent Management")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # get-config
    subparsers.add_parser("get-config", help="Get agent configuration")

    # update-prompt
    prompt_parser = subparsers.add_parser("update-prompt", help="Update agent prompt")
    prompt_parser.add_argument("prompt", help="New prompt text")

    # update-voice
    voice_parser = subparsers.add_parser("update-voice", help="Update voice settings")
    voice_parser.add_argument("--voice-id", help="Voice ID")
    voice_parser.add_argument("--speed", type=float, help="Speech speed")
    voice_parser.add_argument("--stability", type=float, help="Voice stability (0-1)")
    voice_parser.add_argument("--similarity-boost", type=float, help="Similarity boost (0-1)")

    # list-mcp
    subparsers.add_parser("list-mcp", help="List MCP servers")

    # conversations
    conv_parser = subparsers.add_parser("conversations", help="Get recent conversations")
    conv_parser.add_argument("--limit", type=int, default=10, help="Number of conversations")

    # transcript
    trans_parser = subparsers.add_parser("transcript", help="Get conversation transcript")
    trans_parser.add_argument("conversation_id", help="Conversation ID")

    args = parser.parse_args()

    try:
        if args.command == "get-config":
            result = get_config()
            # Print summary
            config = result.get("conversation_config", {})
            agent = config.get("agent", {})
            tts = config.get("tts", {})
            print(f"Agent: {result.get('name')}")
            print(f"Voice ID: {tts.get('voice_id')}")
            print(f"Speed: {tts.get('speed')}")
            print(f"LLM: {agent.get('prompt', {}).get('llm')}")
            print(f"MCP Servers: {agent.get('prompt', {}).get('mcp_server_ids', [])}")

        elif args.command == "update-prompt":
            result = update_prompt(args.prompt)
            print(json.dumps(result, indent=2))

        elif args.command == "update-voice":
            result = update_voice(
                voice_id=args.voice_id,
                speed=args.speed,
                stability=args.stability,
                similarity_boost=args.similarity_boost
            )
            print(json.dumps(result, indent=2))

        elif args.command == "list-mcp":
            result = list_mcp_servers()
            for server in result.get("mcp_servers", []):
                config = server.get("config", {})
                print(f"ID: {server.get('id')}")
                print(f"  Name: {config.get('name')}")
                print(f"  URL: {config.get('url')}")
                print(f"  Policy: {config.get('approval_policy')}")
                print()

        elif args.command == "conversations":
            result = get_conversations(args.limit)
            print(f"Recent {result['count']} conversations:")
            for c in result["conversations"]:
                print(f"  [{c['id']}] {c['title']} ({c['duration']}s, {c['messages']} msgs)")

        elif args.command == "transcript":
            result = get_transcript(args.conversation_id)
            print(f"Conversation: {result['conversation_id']}")
            print(f"Status: {result['status']}")
            print("\nTranscript:")
            for entry in result["transcript"]:
                print(f"  [{entry['role']}]: {entry['message'][:200]}")

        else:
            parser.print_help()

    except requests.exceptions.HTTPError as e:
        print(f"API Error: {e}")
        print(e.response.text[:500] if e.response else "")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
