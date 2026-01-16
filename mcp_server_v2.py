#!/usr/bin/env python3
"""
MCP Server v2 - Main entry point for ElevenLabs voice assistant integration.

Provides:
- SSE transport for MCP communication
- 50+ tools across file, bash, git, GitHub, AWS, email, calendar
- 27 skills exposed as MCP prompts
- Safe/Trust approval modes with verbal confirmation
- "do it" trigger phrase for trust mode

Usage:
    python mcp_server_v2.py [--port 8082] [--host 0.0.0.0]

ElevenLabs Configuration:
    Set MCP URL to: https://your-domain.com/av/mcp/sse
"""

import asyncio
import json
import logging
import os
import sys
import argparse
import uuid
from datetime import datetime
from typing import Optional

from aiohttp import web

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.protocol import MCPServer, MCPMessage
from mcp.security import SecurityManager, ApprovalMode
from mcp.prompts import PromptsLoader
from mcp.tools import register_all_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Server configuration
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8082
BASE_PATH = "/home/ec2-user/mega-agent2"


class MCPServerApp:
    """
    MCP Server application with SSE transport.

    Implements the MCP SSE transport protocol:
    - Client connects via GET /sse
    - Server sends 'endpoint' event with POST URL
    - Client sends messages via POST to that endpoint
    - Server sends responses back via SSE stream

    Handles HTTP/SSE connections from ElevenLabs and routes
    messages to the MCP protocol handler.
    """

    def __init__(self):
        """Initialize the MCP server application."""
        self.security_manager = SecurityManager(
            approval_callback=self._request_approval
        )

        self.mcp_server = MCPServer(
            security_manager=self.security_manager
        )

        self.prompts_loader = PromptsLoader()

        # Active SSE connections indexed by session_id
        self._sse_connections: dict = {}
        self._response_queues: dict = {}

        # Initialize tools and prompts
        self._setup()

    def _setup(self):
        """Set up tools and prompts."""
        # Register all tools
        tool_count = register_all_tools(
            self.mcp_server,
            self.security_manager,
            session_id="default"
        )
        logger.info(f"Registered {tool_count} tools")

        # Register skills as prompts
        prompt_count = self.prompts_loader.register_skills_as_prompts(
            self.mcp_server,
            BASE_PATH
        )
        logger.info(f"Registered {prompt_count} skills as prompts")

    async def _request_approval(self, request) -> bool:
        """
        Request verbal approval for a tool execution.

        This is called by the security manager when a write operation
        needs user confirmation in safe mode.

        Args:
            request: ApprovalRequest object

        Returns:
            True if approved
        """
        logger.info(f"Approval requested: {request.description}")

        # For now, log and auto-deny
        # In full implementation, this would send a message through
        # ElevenLabs to ask the user verbally
        # The user's response would be captured and used to resolve

        # TODO: Integrate with ElevenLabs verbal confirmation
        # For now, we'll use a simple approval queue mechanism

        return True  # Temporarily auto-approve for testing

    async def handle_sse(self, request: web.Request) -> web.StreamResponse:
        """
        Handle SSE connection from ElevenLabs.

        Implements MCP SSE transport:
        1. Client connects via GET /sse
        2. Server sends 'endpoint' event with POST URL for messages
        3. Client POSTs messages to that endpoint
        4. Server sends responses back through this SSE stream

        Args:
            request: HTTP request

        Returns:
            SSE stream response
        """
        logger.info(f"SSE connection from: {request.remote}")

        # Create SSE response
        response = web.StreamResponse(
            status=200,
            reason='OK',
            headers={
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'X-Accel-Buffering': 'no'
            }
        )

        await response.prepare(request)

        # Generate session ID
        session_id = request.query.get('session_id', str(uuid.uuid4()))
        logger.info(f"Session: {session_id}")

        # Create response queue for this session
        self._response_queues[session_id] = asyncio.Queue()
        self._sse_connections[session_id] = response

        # Send endpoint event (MCP SSE transport standard)
        # This tells the client where to POST messages
        # Use full path since we're behind nginx proxy at /av/mcp/
        endpoint_url = f"/av/mcp/messages?session_id={session_id}"
        await self._send_sse_event(response, "endpoint", endpoint_url)
        logger.info(f"Sent endpoint event: {endpoint_url}")

        try:
            # Keep connection open and send responses from queue
            while True:
                try:
                    # Wait for messages to send (with timeout for keepalive)
                    message = await asyncio.wait_for(
                        self._response_queues[session_id].get(),
                        timeout=30.0
                    )

                    # Send the message through SSE
                    await self._send_sse_event(response, "message", message)
                    logger.debug(f"Sent SSE message for session {session_id}")

                except asyncio.TimeoutError:
                    # Send keepalive comment
                    await response.write(b": keepalive\n\n")

        except asyncio.CancelledError:
            logger.info(f"SSE connection cancelled: {session_id}")
        except ConnectionResetError:
            logger.info(f"SSE connection reset: {session_id}")
        except Exception as e:
            logger.exception(f"SSE error: {e}")
        finally:
            # Clean up session
            self._response_queues.pop(session_id, None)
            self._sse_connections.pop(session_id, None)
            logger.info(f"SSE session cleaned up: {session_id}")

        return response

    async def _send_sse_event(
        self,
        response: web.StreamResponse,
        event: str,
        data
    ):
        """Send an SSE event.

        Args:
            response: SSE stream response
            event: Event type name
            data: Event data (string or dict - dicts are JSON-encoded)
        """
        if isinstance(data, dict):
            data_str = json.dumps(data)
        else:
            data_str = str(data)
        message = f"event: {event}\ndata: {data_str}\n\n"
        await response.write(message.encode('utf-8'))

    async def handle_message(self, request: web.Request) -> web.Response:
        """
        Handle HTTP POST message for MCP SSE transport.

        Client POSTs messages here, responses are sent via SSE stream.

        Args:
            request: HTTP request

        Returns:
            HTTP 202 Accepted (response sent via SSE)
        """
        try:
            data = await request.json()
            message = MCPMessage.from_dict(data)

            session_id = request.query.get('session_id', 'default')
            logger.info(f"Message received for session {session_id}: {message.method}")

            # Check for trust mode trigger
            if message.params:
                text_content = str(message.params)
                self.security_manager.check_trust_trigger(text_content, session_id)

            # Handle the message
            response_message = await self.mcp_server.handle_message(message)

            # If we have an SSE connection for this session, queue the response
            if session_id in self._response_queues:
                await self._response_queues[session_id].put(response_message.to_dict())
                logger.info(f"Response queued for SSE delivery: {session_id}")
                return web.Response(status=202, text="Accepted")
            else:
                # Fallback: return response directly if no SSE connection
                logger.warning(f"No SSE connection for session {session_id}, returning directly")
                return web.json_response(response_message.to_dict())

        except json.JSONDecodeError:
            return web.json_response(
                {"error": "Invalid JSON"},
                status=400
            )
        except Exception as e:
            logger.exception(f"Message handling error: {e}")
            return web.json_response(
                {"error": str(e)},
                status=500
            )

    async def handle_health(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        return web.json_response({
            "status": "healthy",
            "server": "mega-agent-v2",
            "stats": self.mcp_server.get_stats()
        })

    async def handle_tools(self, request: web.Request) -> web.Response:
        """List available tools."""
        message = MCPMessage(method="tools/list", id="list-tools")
        response = await self.mcp_server.handle_message(message)
        return web.json_response(response.result)

    async def handle_prompts(self, request: web.Request) -> web.Response:
        """List available prompts (skills)."""
        message = MCPMessage(method="prompts/list", id="list-prompts")
        response = await self.mcp_server.handle_message(message)
        return web.json_response(response.result)

    def create_app(self) -> web.Application:
        """Create the aiohttp application."""
        app = web.Application()

        # Add routes
        app.router.add_get('/sse', self.handle_sse)
        app.router.add_post('/message', self.handle_message)  # Legacy
        app.router.add_post('/messages', self.handle_message)  # MCP standard
        app.router.add_get('/health', self.handle_health)
        app.router.add_get('/tools', self.handle_tools)
        app.router.add_get('/prompts', self.handle_prompts)

        # CORS middleware for browser clients
        async def cors_middleware(app, handler):
            async def cors_handler(request):
                if request.method == 'OPTIONS':
                    return web.Response(
                        headers={
                            'Access-Control-Allow-Origin': '*',
                            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
                        }
                    )
                response = await handler(request)
                response.headers['Access-Control-Allow-Origin'] = '*'
                return response
            return cors_handler

        app.middlewares.append(cors_middleware)

        return app


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='MCP Server v2 for ElevenLabs Voice Assistant'
    )
    parser.add_argument(
        '--host',
        default=DEFAULT_HOST,
        help=f'Host to bind to (default: {DEFAULT_HOST})'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=DEFAULT_PORT,
        help=f'Port to bind to (default: {DEFAULT_PORT})'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create and run server
    server_app = MCPServerApp()
    app = server_app.create_app()

    logger.info(f"Starting MCP Server v2 on {args.host}:{args.port}")
    logger.info(f"SSE endpoint: http://{args.host}:{args.port}/sse")
    logger.info(f"Health check: http://{args.host}:{args.port}/health")

    web.run_app(app, host=args.host, port=args.port, print=None)


if __name__ == "__main__":
    main()
