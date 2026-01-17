#!/usr/bin/env python3
"""
Nova Sonic Voice Service

Flask app for Nova 2 Sonic voice agent.
Single user, single stream, minimal complexity.

Usage:
    python nova_sonic_service.py [--port PORT]
"""

import argparse
import asyncio
import json
import logging
import os
import sys

from flask import Flask, render_template, send_from_directory, jsonify
from flask_sock import Sock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nova_sonic.audio_bridge import nova_bridge
from nova_sonic.conversation_manager import conversation_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__, static_folder='static')
sock = Sock(app)


@app.route('/nova')
def nova_ui():
    """Serve the Nova voice agent UI."""
    return send_from_directory('static/nova', 'index.html')


@app.route('/nova/<path:filename>')
def nova_static(filename):
    """Serve static files for Nova UI."""
    return send_from_directory('static/nova', filename)


@sock.route('/nova/stream')
def nova_stream(ws):
    """
    WebSocket endpoint for Nova audio streaming.

    Single stream at a time - rejects if already active.
    """
    if nova_bridge.is_active():
        ws.send(json.dumps({
            "type": "error",
            "message": "Session already active. Close the other session first."
        }))
        ws.close()
        return

    # Run the async bridge in an event loop
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(nova_bridge.handle_websocket(ws))
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        loop.close()


@app.route('/nova/status')
def nova_status():
    """Get Nova service status."""
    stats = conversation_manager.get_stats()
    return jsonify({
        "active": nova_bridge.is_active(),
        "conversation": stats
    })


@app.route('/nova/clear', methods=['POST'])
def nova_clear():
    """Clear conversation history."""
    conversation_manager.clear()
    return jsonify({"status": "cleared"})


@app.route('/nova/transcript')
def nova_transcript():
    """Get current transcript."""
    return jsonify({
        "transcript": nova_bridge.get_transcript()
    })


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "service": "nova-sonic"})


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Nova Sonic Voice Service")
    parser.add_argument('--port', type=int, default=5001, help='Port to run on')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    logger.info(f"Starting Nova Sonic service on {args.host}:{args.port}")
    logger.info("UI available at: http://localhost:{}/nova".format(args.port))

    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug
    )


if __name__ == '__main__':
    main()
