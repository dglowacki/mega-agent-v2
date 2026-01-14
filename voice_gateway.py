#!/usr/bin/env python3.11
"""
Voice Gateway - WebSocket server for voice clients.

Provides a WebSocket interface for web browsers and other clients
to connect and have voice conversations with Claude agents.

Usage:
    python voice_gateway.py [--host HOST] [--port PORT] [--voice VOICE]

Architecture:
    Browser (Web Audio API)
           ↓ WebSocket
    Voice Gateway Server
           ↓
    Grok Voice API (STT/TTS)
           ↓
    Claude Agent SDK
"""

import argparse
import asyncio
import base64
import json
import os
import signal
import sys
from typing import Set

import websockets
from websockets.server import WebSocketServerProtocol

from voice_bridge import VoiceBridge


class VoiceGateway:
    """
    WebSocket server for voice clients.

    Handles:
    - Client connections (browser, mobile, etc.)
    - Audio streaming from clients
    - Audio responses back to clients
    - Multiple concurrent connections
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8765,
        voice: str = "Ara"
    ):
        """
        Initialize Voice Gateway.

        Args:
            host: Host to bind to
            port: Port to listen on
            voice: Grok voice to use
        """
        self.host = host
        self.port = port
        self.voice = voice

        self.clients: Set[WebSocketServerProtocol] = set()
        self._server = None
        self._shutdown_event = asyncio.Event()

    async def handle_client(self, websocket: WebSocketServerProtocol) -> None:
        """
        Handle a connected voice client.

        Args:
            websocket: Client WebSocket connection
        """
        client_id = id(websocket)
        self.clients.add(websocket)
        print(f"Client {client_id} connected. Total clients: {len(self.clients)}", flush=True)

        # Create a dedicated bridge for this client
        bridge = VoiceBridge(voice=self.voice)

        try:
            await bridge.connect()

            # Notify client that Grok is ready
            await websocket.send(json.dumps({"type": "grok_ready"}))
            print(f"Sent grok_ready to client {client_id}", flush=True)

            # Set up callbacks to forward to client
            async def send_to_client(msg_type: str, data: dict) -> None:
                try:
                    await websocket.send(json.dumps({"type": msg_type, **data}))
                except websockets.ConnectionClosed:
                    pass

            bridge.on_user_speech = lambda t: asyncio.create_task(
                send_to_client("transcription", {"text": t})
            )
            bridge.on_claude_response = lambda t: asyncio.create_task(
                send_to_client("response", {"text": t})
            )
            bridge.on_audio_output = lambda a: asyncio.create_task(
                send_to_client("audio", {"data": base64.b64encode(a).decode('utf-8')})
            )
            bridge.on_thinking = lambda t: asyncio.create_task(
                send_to_client("thinking", {"active": t})
            )

            # Run two tasks concurrently:
            # 1. Listen for messages from client
            # 2. Run the voice bridge loop

            async def receive_from_client():
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        msg_type = data.get("type", "")

                        if msg_type == "audio":
                            # Client sending audio
                            audio_b64 = data.get("data", "")
                            if audio_b64:
                                audio_bytes = base64.b64decode(audio_b64)
                                await bridge.send_audio(audio_bytes)

                        elif msg_type == "text":
                            # Client sending text directly
                            text = data.get("text", "")
                            if text:
                                response = await bridge.process_transcription(text)
                                await bridge.speak_response(response)

                        elif msg_type == "config":
                            # Configuration update
                            # Could switch voice, agent, etc.
                            pass

                        elif msg_type == "ping":
                            await websocket.send(json.dumps({"type": "pong"}))

                    except json.JSONDecodeError:
                        print(f"Invalid JSON from client {client_id}", flush=True)
                    except Exception as e:
                        print(f"Error processing client message: {e}", flush=True)

            async def run_bridge_loop():
                try:
                    await asyncio.wait_for(bridge.run_voice_loop(), timeout=300)
                except asyncio.TimeoutError:
                    print(f"Bridge loop timeout for client {client_id}", flush=True)
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    print(f"Bridge loop error for client {client_id}: {e}", flush=True)

            # Run both tasks
            receive_task = asyncio.create_task(receive_from_client())
            bridge_task = asyncio.create_task(run_bridge_loop())

            done, pending = await asyncio.wait(
                [receive_task, bridge_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel remaining tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        except websockets.ConnectionClosed:
            print(f"Client {client_id} disconnected", flush=True)
        except Exception as e:
            print(f"Error handling client {client_id}: {e}", flush=True)
        finally:
            await bridge.close()
            self.clients.discard(websocket)
            print(f"Client {client_id} cleaned up. Remaining: {len(self.clients)}", flush=True)

    async def start(self) -> None:
        """Start the voice gateway server."""
        print(f"Starting Voice Gateway on ws://{self.host}:{self.port}", flush=True)
        print(f"Voice: {self.voice}", flush=True)

        self._server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=10
        )

        print(f"Voice Gateway running at ws://{self.host}:{self.port}", flush=True)
        print("Press Ctrl+C to stop", flush=True)

        # Wait for shutdown
        await self._shutdown_event.wait()

    async def stop(self) -> None:
        """Stop the voice gateway server."""
        print("\nShutting down Voice Gateway...")

        # Close all client connections
        for client in list(self.clients):
            try:
                await client.close()
            except Exception:
                pass

        # Close server
        if self._server:
            self._server.close()
            await self._server.wait_closed()

        self._shutdown_event.set()
        print("Voice Gateway stopped.")

    def shutdown(self) -> None:
        """Signal shutdown (for signal handlers)."""
        asyncio.create_task(self.stop())


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Voice Gateway Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to listen on")
    parser.add_argument("--voice", default="Ara", choices=["Ara", "Rex", "Sal", "Eve", "Leo"],
                       help="Grok voice to use")
    args = parser.parse_args()

    gateway = VoiceGateway(
        host=args.host,
        port=args.port,
        voice=args.voice
    )

    # Handle Ctrl+C
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, gateway.shutdown)

    try:
        await gateway.start()
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    asyncio.run(main())
