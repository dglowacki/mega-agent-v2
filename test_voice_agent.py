#!/usr/bin/env python3.11
"""
End-to-end test for Voice Agent.

Tests the complete pipeline:
1. WebSocket connection (local and public)
2. Grok Voice API connection
3. Text query processing via Claude
4. Response generation

Usage:
    python test_voice_agent.py [--query "your question"] [--public]
"""

import asyncio
import json
import ssl
import sys
import websockets

LOCAL_WS_URL = "ws://127.0.0.1:8765"
PUBLIC_WS_URL = "wss://a.fcow.ca/av/ws"
DEFAULT_QUERY = "What is the current time?"
TIMEOUT = 60  # seconds


async def test_voice_agent(query: str = DEFAULT_QUERY, public: bool = False) -> bool:
    """
    Test the voice agent end-to-end.

    Returns True if successful, False otherwise.
    """
    ws_url = PUBLIC_WS_URL if public else LOCAL_WS_URL

    print("=" * 60)
    print("VOICE AGENT END-TO-END TEST")
    print("=" * 60)
    print(f"Mode: {'PUBLIC' if public else 'LOCAL'}")
    print(f"URL: {ws_url}")
    print(f"Query: {query}")
    print()

    success = False
    response_text = None

    # SSL context for public URL
    ssl_context = ssl.create_default_context() if public else None

    try:
        # Step 1: Connect to WebSocket
        print("[1/4] Connecting to WebSocket...")
        async with websockets.connect(ws_url, ssl=ssl_context, close_timeout=5) as ws:
            print("      Connected!")

            # Step 2: Wait for grok_ready
            print("[2/4] Waiting for Grok Voice API to initialize...")
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=35)
                data = json.loads(msg)
                if data.get("type") == "grok_ready":
                    print("      Grok Voice API ready!")
                else:
                    print(f"      ERROR: Expected grok_ready, got: {data}")
                    return False
            except asyncio.TimeoutError:
                print("      ERROR: Timeout waiting for grok_ready")
                return False

            # Step 3: Send text query
            print(f"[3/4] Sending query: '{query}'")
            await ws.send(json.dumps({
                "type": "text",
                "text": query
            }))
            print("      Query sent!")

            # Step 4: Wait for response
            print("[4/4] Waiting for response...")
            start_time = asyncio.get_event_loop().time()
            got_transcription = False
            got_response = False

            while True:
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > TIMEOUT:
                    print(f"      ERROR: Timeout after {TIMEOUT}s")
                    break

                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=5)
                    data = json.loads(msg)
                    msg_type = data.get("type")

                    if msg_type == "transcription":
                        print(f"      [Transcription] {data.get('text', '')[:50]}...")
                        got_transcription = True

                    elif msg_type == "thinking":
                        if data.get("active"):
                            print("      [Thinking] Processing...")
                        else:
                            print("      [Thinking] Done")

                    elif msg_type == "response":
                        response_text = data.get("text", "")
                        print(f"      [Response] {response_text[:100]}...")
                        got_response = True
                        success = True
                        break

                    elif msg_type == "pong":
                        pass  # Ignore keepalive

                    elif msg_type == "error":
                        print(f"      [ERROR] {data.get('message', 'Unknown error')}")
                        break

                    else:
                        print(f"      [Unknown] {msg_type}: {str(data)[:50]}")

                except asyncio.TimeoutError:
                    # Keep waiting
                    print(f"      (waiting... {int(elapsed)}s elapsed)")
                    continue

    except websockets.exceptions.ConnectionClosed as e:
        print(f"ERROR: Connection closed: {e}")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")

    # Summary
    print()
    print("=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    if success:
        print("STATUS: SUCCESS")
        print(f"RESPONSE: {response_text}")
    else:
        print("STATUS: FAILED")
        print("Check /tmp/voice_gateway.log for details")
    print("=" * 60)

    return success


async def main():
    query = DEFAULT_QUERY
    public = False
    run_both = False

    args = sys.argv[1:]

    if "--public" in args:
        public = True
        args.remove("--public")

    if "--both" in args:
        run_both = True
        args.remove("--both")

    if "--query" in args:
        idx = args.index("--query")
        if idx + 1 < len(args):
            query = args[idx + 1]
    elif args:
        query = " ".join(args)

    if run_both:
        print("\n" + "=" * 60)
        print("RUNNING BOTH LOCAL AND PUBLIC TESTS")
        print("=" * 60 + "\n")

        local_success = await test_voice_agent(query, public=False)
        print("\n")
        public_success = await test_voice_agent(query, public=True)

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Local test:  {'PASS' if local_success else 'FAIL'}")
        print(f"Public test: {'PASS' if public_success else 'FAIL'}")
        print("=" * 60)

        sys.exit(0 if local_success and public_success else 1)
    else:
        success = await test_voice_agent(query, public=public)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
