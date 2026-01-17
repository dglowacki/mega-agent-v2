#!/usr/bin/env python3
"""
End-to-end tests for Nova Sonic Voice Agent.

Tests:
1. AWS credentials and Bedrock access
2. Nova Sonic client connection
3. Session start/end flow
4. Audio round-trip (simulated)
5. Tool execution
6. WebSocket endpoint
"""

import asyncio
import json
import os
import sys
import base64
import struct

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment
from dotenv import load_dotenv
load_dotenv()


def test_aws_credentials():
    """Test AWS credentials are configured."""
    print("Test 1: AWS Credentials")

    import boto3
    sts = boto3.client('sts', region_name='us-east-1')
    identity = sts.get_caller_identity()

    assert 'Account' in identity
    assert 'Arn' in identity
    print(f"  Account: {identity['Account']}")
    print(f"  ARN: {identity['Arn']}")
    print("  PASSED\n")


def test_bedrock_model_access():
    """Test Bedrock has Nova Sonic model."""
    print("Test 2: Bedrock Model Access")

    import boto3
    bedrock = boto3.client('bedrock', region_name='us-east-1')
    models = bedrock.list_foundation_models()

    nova_sonic = None
    for m in models['modelSummaries']:
        if 'nova-2-sonic' in m['modelId'].lower():
            nova_sonic = m
            break

    assert nova_sonic is not None, "Nova 2 Sonic model not found"
    print(f"  Model ID: {nova_sonic['modelId']}")
    print(f"  Status: {nova_sonic.get('modelLifecycle', {}).get('status', 'N/A')}")
    print("  PASSED\n")


async def test_nova_client_connection():
    """Test Nova Sonic client can connect."""
    print("Test 3: Nova Sonic Client Connection")

    from nova_sonic.client import NovaSonicClient

    client = NovaSonicClient()
    result = await client.connect()

    assert result == True
    assert client.is_active == True
    print("  Client connected successfully")

    await client.close()
    assert client.is_active == False
    print("  Client closed successfully")
    print("  PASSED\n")


async def test_session_flow():
    """Test full session start/end flow."""
    print("Test 4: Session Flow")

    from nova_sonic.client import NovaSonicClient
    from nova_sonic.tool_registry import get_tool_definitions

    client = NovaSonicClient()
    await client.connect()

    # Send session start with tools
    tools = get_tool_definitions()
    await client.send_session_start(tools=tools)
    print(f"  Session start sent with {len(tools)} tools")

    # Send prompt start (tools are in sessionStart)
    await client.send_prompt_start()
    print("  Prompt start sent")

    # Send system message
    await client.send_system_message("You are a helpful voice assistant.")
    print("  System message sent")

    # Start audio input
    await client.send_audio_start()
    print("  Audio input started")

    # Send a short silence (to trigger something)
    silence = generate_silence(0.5)  # 0.5 seconds
    await client.send_audio_chunk(silence)
    print("  Audio chunk sent (silence)")

    # End audio
    await client.send_audio_end()
    print("  Audio input ended")

    # Try to receive a few events (with timeout)
    events_received = []
    try:
        async def collect_events():
            async for event in receive_n_events(client, 3):
                events_received.append(event)
        await asyncio.wait_for(collect_events(), timeout=5.0)
    except asyncio.TimeoutError:
        pass

    print(f"  Received {len(events_received)} events")

    # Close session
    await client.close()
    print("  Session closed")
    print("  PASSED\n")


async def receive_n_events(client, n):
    """Receive up to n events from client."""
    count = 0
    async for event in client.receive_events():
        yield event
        count += 1
        if count >= n:
            break


def generate_silence(duration_seconds: float) -> bytes:
    """Generate silent PCM audio (16kHz, 16-bit mono)."""
    sample_rate = 16000
    num_samples = int(sample_rate * duration_seconds)
    # Silent samples (all zeros)
    return struct.pack(f'<{num_samples}h', *([0] * num_samples))


def generate_tone(frequency: float, duration_seconds: float, amplitude: float = 0.5) -> bytes:
    """Generate a tone as PCM audio (16kHz, 16-bit mono)."""
    import math
    sample_rate = 16000
    num_samples = int(sample_rate * duration_seconds)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        sample = int(amplitude * 32767 * math.sin(2 * math.pi * frequency * t))
        samples.append(sample)
    return struct.pack(f'<{num_samples}h', *samples)


def test_mcp_executor():
    """Test MCP executor can call tools."""
    print("Test 5: MCP Executor")

    from nova_sonic.mcp_executor import execute_tool, list_available_tools

    async def run_test():
        # List available tools
        tools = await list_available_tools()
        print(f"  Available tools: {len(tools)}")

        # Test get_time tool (should work without external deps)
        result = await execute_tool("get_time", {"timezone": "America/Los_Angeles"})
        return result

    result = asyncio.run(run_test())

    assert result is not None
    print(f"  get_time result: {result}")
    print("  PASSED\n")


def test_tool_registry():
    """Test tool registry has expected tools."""
    print("Test 6: Tool Registry")

    from nova_sonic.tool_registry import get_tool_definitions, get_tool_count

    tools = get_tool_definitions()
    count = get_tool_count()

    assert count > 0
    assert len(tools) == count

    # Check for key tools
    tool_names = [t['toolSpec']['name'] for t in tools]

    assert 'ask_claude' in tool_names, "ask_claude tool missing"
    assert 'get_weather' in tool_names, "get_weather tool missing"
    assert 'get_time' in tool_names, "get_time tool missing"

    print(f"  {count} tools registered")
    print(f"  Tools: {', '.join(tool_names[:5])}...")
    print("  PASSED\n")


def test_conversation_manager():
    """Test conversation manager."""
    print("Test 7: Conversation Manager")

    from nova_sonic.conversation_manager import conversation_manager

    # Clear any existing state
    conversation_manager.clear()

    # Add some messages
    conversation_manager.add_message("user", "Hello")
    conversation_manager.add_message("assistant", "Hi there!")
    conversation_manager.add_message("user", "How are you?")
    conversation_manager.add_message("assistant", "I'm doing well, thanks!")

    stats = conversation_manager.get_stats()
    assert stats['message_count'] == 4

    context = conversation_manager.get_context_for_nova()
    assert len(context) > 0

    print(f"  Messages: {stats['message_count']}")
    print(f"  Tokens: {stats['total_tokens']}")
    print("  PASSED\n")


def test_flask_service():
    """Test Flask service endpoints."""
    print("Test 8: Flask Service Endpoints")

    import requests

    base_url = "http://127.0.0.1:5051"

    # Health check
    r = requests.get(f"{base_url}/health")
    assert r.status_code == 200
    data = r.json()
    assert data['status'] == 'ok'
    print(f"  /health: OK")

    # Status endpoint
    r = requests.get(f"{base_url}/nova/status")
    assert r.status_code == 200
    data = r.json()
    assert 'active' in data
    assert 'conversation' in data
    print(f"  /nova/status: OK")

    # UI endpoint
    r = requests.get(f"{base_url}/nova")
    assert r.status_code == 200
    assert 'VOICE AGENT' in r.text
    print(f"  /nova: OK")

    # Static files
    r = requests.get(f"{base_url}/nova/style.css")
    assert r.status_code == 200
    assert 'neo-brutal' in r.text.lower() or '--cyan' in r.text
    print(f"  /nova/style.css: OK")

    print("  PASSED\n")


async def test_websocket_connection():
    """Test WebSocket can connect (basic test)."""
    print("Test 9: WebSocket Connection")

    import websockets

    uri = "ws://127.0.0.1:5051/nova/stream"

    try:
        async with websockets.connect(uri, close_timeout=2) as ws:
            # Send audio_start
            await ws.send(json.dumps({"type": "audio_start"}))
            print("  Sent audio_start")

            # Wait briefly for response
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=3.0)
                data = json.loads(msg)
                print(f"  Received: {data.get('type', 'unknown')}")
            except asyncio.TimeoutError:
                print("  No immediate response (expected for audio mode)")

            # Send audio_end to close cleanly
            await ws.send(json.dumps({"type": "audio_end"}))
            print("  Sent audio_end")

    except Exception as e:
        print(f"  WebSocket error: {e}")
        raise

    print("  PASSED\n")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Nova Sonic Voice Agent - End-to-End Tests")
    print("=" * 60 + "\n")

    tests = [
        ("AWS Credentials", test_aws_credentials),
        ("Bedrock Model Access", test_bedrock_model_access),
        ("Nova Client Connection", lambda: asyncio.run(test_nova_client_connection())),
        ("Session Flow", lambda: asyncio.run(test_session_flow())),
        ("MCP Executor", test_mcp_executor),
        ("Tool Registry", test_tool_registry),
        ("Conversation Manager", test_conversation_manager),
        ("Flask Service", test_flask_service),
        ("WebSocket Connection", lambda: asyncio.run(test_websocket_connection())),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"  FAILED: {e}\n")
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    # Install test dependencies if needed
    try:
        import websockets
    except ImportError:
        print("Installing websockets for testing...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "websockets", "python-dotenv", "-q"])
        import websockets

    try:
        from dotenv import load_dotenv
    except ImportError:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "python-dotenv", "-q"])
        from dotenv import load_dotenv

    success = run_all_tests()
    sys.exit(0 if success else 1)
