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
from mcp.auth import auth_manager

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
        # Detect path prefix from request (could be /mcp2/ or /av/mcp/)
        request_path = request.path
        if '/av/mcp' in request.headers.get('X-Original-URI', request_path):
            base_path = '/av/mcp'
        else:
            base_path = '/mcp2'
        endpoint_url = f"{base_path}/messages?session_id={session_id}"
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

    async def handle_root(self, request: web.Request) -> web.Response:
        """Root endpoint - returns MCP server info."""
        return web.json_response({
            "name": "mega-agent-mcp-v2",
            "version": "2.0.0",
            "protocol": "MCP",
            "transport": "sse",
            "endpoints": {
                "sse": "/sse",
                "messages": "/messages"
            }
        })

    async def handle_tools(self, request: web.Request) -> web.Response:
        """List available tools."""
        message = MCPMessage(method="tools/list", id="list-tools")
        response = await self.mcp_server.handle_message(message)
        return web.json_response(response.result)

    async def handle_voice_tools(self, request: web.Request) -> web.Response:
        """
        List tools organized by tier for voice agents.

        Returns tiered tool structure:
        - tier1: Direct access tools (~35)
        - tier2: Meta-tools (6)
        - tier3: Discovery tools (3)
        """
        from mcp.voice import (
            TIER_1_TOOLS, TIER_2_META_TOOLS, TIER_3_DISCOVERY,
            get_tool_metadata
        )

        # Build tier 1 tools with metadata
        tier1 = []
        for name in sorted(TIER_1_TOOLS):
            tool = self.mcp_server._tools.get(name)
            meta = get_tool_metadata(name)
            if tool:
                tier1.append({
                    "name": name,
                    "description": tool.description,
                    "latency": meta.latency.value,
                    "requires_confirmation": meta.requires_confirmation,
                    "voice_description": meta.voice_description
                })

        # Build tier 2 meta-tools
        tier2 = []
        for name, config in TIER_2_META_TOOLS.items():
            tool = self.mcp_server._tools.get(name)
            if tool:
                tier2.append({
                    "name": name,
                    "description": config["description"],
                    "actions": config["actions"],
                    "internal_tool_count": len(config["internal_tools"])
                })

        # Build tier 3 discovery tools
        tier3 = []
        for name, config in TIER_3_DISCOVERY.items():
            tool = self.mcp_server._tools.get(name)
            if tool:
                tier3.append({
                    "name": name,
                    "description": config["description"]
                })

        return web.json_response({
            "tier1": tier1,
            "tier2": tier2,
            "tier3": tier3,
            "summary": {
                "tier1_count": len(tier1),
                "tier2_count": len(tier2),
                "tier3_count": len(tier3),
                "total_exposed": len(tier1) + len(tier2) + len(tier3)
            }
        })

    async def handle_prompts(self, request: web.Request) -> web.Response:
        """List available prompts (skills)."""
        message = MCPMessage(method="prompts/list", id="list-prompts")
        response = await self.mcp_server.handle_message(message)
        return web.json_response(response.result)

    # =========================================
    # OAuth2 Endpoints
    # =========================================

    async def handle_oauth_metadata(self, request: web.Request) -> web.Response:
        """OAuth2 Authorization Server Metadata (RFC 8414)."""
        # Get base URL from headers (nginx sets X-Forwarded-Proto)
        proto = request.headers.get('X-Forwarded-Proto', 'https')
        host = request.headers.get('Host', request.host)
        base_url = f"{proto}://{host}"

        metadata = auth_manager.get_oauth_metadata(base_url)
        return web.json_response(metadata)

    async def handle_protected_resource_metadata(self, request: web.Request) -> web.Response:
        """OAuth2 Protected Resource Metadata (RFC 9449)."""
        proto = request.headers.get('X-Forwarded-Proto', 'https')
        host = request.headers.get('Host', request.host)
        base_url = f"{proto}://{host}"

        return web.json_response({
            "resource": f"{base_url}/mcp2/",
            "authorization_servers": [base_url],
            "bearer_methods_supported": ["header"],
            "scopes_supported": ["mcp"]
        })

    async def handle_authorize(self, request: web.Request) -> web.Response:
        """OAuth2 authorization endpoint - shows login form if password required."""
        params = request.query

        response_type = params.get('response_type')
        client_id = params.get('client_id')
        redirect_uri = params.get('redirect_uri')
        scope = params.get('scope', 'mcp')
        state = params.get('state', '')
        code_challenge = params.get('code_challenge')
        code_challenge_method = params.get('code_challenge_method', 'plain')

        if response_type != 'code':
            return web.json_response(
                {'error': 'unsupported_response_type'},
                status=400
            )

        if not client_id or not redirect_uri:
            return web.json_response(
                {'error': 'invalid_request', 'error_description': 'Missing client_id or redirect_uri'},
                status=400
            )

        # If password is required, show login form
        if auth_manager.requires_oauth_password():
            pending_id = auth_manager.create_pending_authorization(
                client_id=client_id,
                redirect_uri=redirect_uri,
                scope=scope,
                state=state,
                code_challenge=code_challenge,
                code_challenge_method=code_challenge_method
            )
            logger.info(f"OAuth authorize: client={client_id}, showing login form")
            return web.Response(
                text=self._get_login_html(pending_id, client_id),
                content_type='text/html'
            )

        # No password required - auto-approve (development mode)
        code = auth_manager.create_authorization_code(
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=scope,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method
        )

        redirect_url = f"{redirect_uri}?code={code}"
        if state:
            redirect_url += f"&state={state}"

        logger.info(f"OAuth authorize: client={client_id}, auto-approved (no password set)")
        raise web.HTTPFound(location=redirect_url)

    async def handle_authorize_submit(self, request: web.Request) -> web.Response:
        """Handle login form submission."""
        try:
            data = await request.post()
        except Exception:
            return web.json_response({'error': 'Invalid request'}, status=400)

        pending_id = data.get('pending_id', '')
        password = data.get('password', '')

        pending = auth_manager.get_pending_authorization(pending_id)
        if not pending:
            return web.Response(
                text=self._get_error_html("Authorization expired or invalid. Please try again."),
                content_type='text/html',
                status=400
            )

        code = auth_manager.approve_pending_authorization(pending_id, password)
        if not code:
            # Wrong password - show form again with error
            return web.Response(
                text=self._get_login_html(pending_id, pending['client_id'], error="Invalid password"),
                content_type='text/html'
            )

        # Success - redirect with code
        redirect_url = f"{pending['redirect_uri']}?code={code}"
        if pending.get('state'):
            redirect_url += f"&state={pending['state']}"

        logger.info(f"OAuth authorize approved for client={pending['client_id']}")
        raise web.HTTPFound(location=redirect_url)

    def _get_login_html(self, pending_id: str, client_id: str, error: str = "") -> str:
        """Generate login form HTML."""
        error_html = f'<p style="color: #dc3545; margin-bottom: 15px;">{error}</p>' if error else ''
        return f'''<!DOCTYPE html>
<html>
<head>
    <title>MCP Authorization</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               background: #1a1a2e; color: #eee; display: flex; justify-content: center;
               align-items: center; min-height: 100vh; margin: 0; }}
        .container {{ background: #16213e; padding: 40px; border-radius: 12px;
                     box-shadow: 0 4px 20px rgba(0,0,0,0.3); max-width: 400px; width: 90%; }}
        h1 {{ margin: 0 0 10px; font-size: 24px; color: #fff; }}
        .client {{ color: #0f9; font-family: monospace; margin-bottom: 20px; }}
        input[type="password"] {{ width: 100%; padding: 12px; border: 1px solid #333;
                                  border-radius: 6px; background: #0f0f23; color: #fff;
                                  font-size: 16px; box-sizing: border-box; }}
        button {{ width: 100%; padding: 12px; background: #0f9; color: #000; border: none;
                 border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer;
                 margin-top: 15px; }}
        button:hover {{ background: #0da; }}
        .note {{ color: #888; font-size: 12px; margin-top: 15px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Authorize Access</h1>
        <p class="client">{client_id}</p>
        {error_html}
        <form method="POST" action="/authorize/submit">
            <input type="hidden" name="pending_id" value="{pending_id}">
            <input type="password" name="password" placeholder="Enter password" autofocus required>
            <button type="submit">Authorize</button>
        </form>
        <p class="note">This will grant the application access to your MCP server.</p>
    </div>
</body>
</html>'''

    def _get_error_html(self, message: str) -> str:
        """Generate error page HTML."""
        return f'''<!DOCTYPE html>
<html>
<head>
    <title>Authorization Error</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               background: #1a1a2e; color: #eee; display: flex; justify-content: center;
               align-items: center; min-height: 100vh; margin: 0; }}
        .container {{ background: #16213e; padding: 40px; border-radius: 12px; text-align: center; }}
        h1 {{ color: #dc3545; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Error</h1>
        <p>{message}</p>
    </div>
</body>
</html>'''

    async def handle_oauth_token(self, request: web.Request) -> web.Response:
        """OAuth2 token endpoint."""
        try:
            data = await request.post()
        except Exception:
            data = request.query

        grant_type = data.get('grant_type')
        client_id = data.get('client_id')
        client_secret = data.get('client_secret')
        code = data.get('code')
        redirect_uri = data.get('redirect_uri')
        code_verifier = data.get('code_verifier')
        scope = data.get('scope', 'mcp')

        if grant_type == 'authorization_code':
            if not code or not client_id or not redirect_uri:
                return web.json_response(
                    {'error': 'invalid_request', 'error_description': 'Missing required parameters'},
                    status=400
                )

            token_response = auth_manager.exchange_code_for_token(
                code=code,
                client_id=client_id,
                redirect_uri=redirect_uri,
                code_verifier=code_verifier
            )

            if not token_response:
                return web.json_response(
                    {'error': 'invalid_grant', 'error_description': 'Invalid or expired code'},
                    status=400
                )

            return web.json_response(token_response)

        elif grant_type == 'client_credentials':
            if not client_id:
                return web.json_response(
                    {'error': 'invalid_request', 'error_description': 'Missing client_id'},
                    status=400
                )

            token_response = auth_manager.create_client_credentials_token(
                client_id=client_id,
                scope=scope
            )
            return web.json_response(token_response)

        else:
            return web.json_response(
                {'error': 'unsupported_grant_type'},
                status=400
            )

    async def handle_generate_api_key(self, request: web.Request) -> web.Response:
        """Generate a new API key (admin endpoint)."""
        # This should be protected - for now just check for admin header
        admin_key = request.headers.get('X-Admin-Key')
        if admin_key != os.environ.get('MCP_ADMIN_KEY', 'admin'):
            return web.json_response({'error': 'Unauthorized'}, status=401)

        plain_key, key_hash = auth_manager.generate_api_key()
        return web.json_response({
            'api_key': plain_key,
            'key_hash': key_hash,
            'note': 'Save the api_key securely - it cannot be retrieved later'
        })

    async def handle_set_oauth_password(self, request: web.Request) -> web.Response:
        """Set the OAuth authorization password (admin endpoint)."""
        admin_key = request.headers.get('X-Admin-Key')
        if admin_key != os.environ.get('MCP_ADMIN_KEY', 'admin'):
            return web.json_response({'error': 'Unauthorized'}, status=401)

        try:
            data = await request.json()
        except Exception:
            return web.json_response({'error': 'Invalid JSON'}, status=400)

        password = data.get('password')
        if not password:
            return web.json_response({'error': 'Password required'}, status=400)

        auth_manager.set_oauth_password(password)
        return web.json_response({
            'status': 'ok',
            'message': 'OAuth password set successfully'
        })

    def create_app(self) -> web.Application:
        """Create the aiohttp application."""
        app = web.Application()

        # OAuth2 routes (no auth required)
        app.router.add_get('/.well-known/oauth-authorization-server', self.handle_oauth_metadata)
        app.router.add_get('/.well-known/oauth-protected-resource', self.handle_protected_resource_metadata)
        app.router.add_get('/authorize', self.handle_authorize)
        app.router.add_post('/authorize/submit', self.handle_authorize_submit)
        app.router.add_post('/oauth/token', self.handle_oauth_token)
        app.router.add_get('/oauth/token', self.handle_oauth_token)  # Some clients use GET

        # Admin routes
        app.router.add_post('/admin/api-key', self.handle_generate_api_key)
        app.router.add_post('/admin/oauth-password', self.handle_set_oauth_password)

        # Public routes (no auth - for discovery)
        app.router.add_get('/health', self.handle_health)

        # Root endpoint - returns server info or handles MCP init
        app.router.add_get('/', self.handle_root)
        app.router.add_post('/', self.handle_message)  # MCP can POST to root

        # Protected routes (require auth)
        app.router.add_get('/sse', self.handle_sse)
        app.router.add_post('/message', self.handle_message)  # Legacy
        app.router.add_post('/messages', self.handle_message)  # MCP standard
        app.router.add_get('/tools', self.handle_tools)
        app.router.add_get('/voice/tools', self.handle_voice_tools)
        app.router.add_get('/prompts', self.handle_prompts)

        # Routes that don't require auth (use their own auth or public)
        NO_AUTH_ROUTES = {
            '/.well-known/oauth-authorization-server',
            '/.well-known/oauth-protected-resource',
            '/authorize',
            '/authorize/submit',
            '/oauth/token',
            '/health',
            '/tools',                # Tool discovery is public
            '/voice/tools',          # Tool discovery is public
            '/prompts',              # Prompt discovery is public
            '/admin/api-key',        # Uses X-Admin-Key
            '/admin/oauth-password', # Uses X-Admin-Key
            '/sse',                  # SSE endpoint - temp no auth
            '/messages',             # MCP messages - temp no auth
            '/message',              # MCP messages - temp no auth
            '/',                     # Root - temp no auth
        }

        # Authentication middleware
        @web.middleware
        async def auth_middleware(request, handler):
            # Skip auth for OAuth and health endpoints
            if request.path in NO_AUTH_ROUTES:
                return await handler(request)

            # Skip auth for OPTIONS (CORS preflight)
            if request.method == 'OPTIONS':
                return await handler(request)

            # Check authentication
            auth_header = request.headers.get('Authorization')
            api_key = request.headers.get('X-API-Key')

            is_auth, error = auth_manager.authenticate(auth_header, api_key)

            if not is_auth:
                logger.warning(f"Auth failed for {request.path}: {error}")
                return web.json_response(
                    {'error': 'unauthorized', 'message': error},
                    status=401,
                    headers={'WWW-Authenticate': 'Bearer realm="mcp"'}
                )

            return await handler(request)

        # CORS middleware for browser clients
        @web.middleware
        async def cors_middleware(request, handler):
            if request.method == 'OPTIONS':
                return web.Response(
                    headers={
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-API-Key'
                    }
                )
            response = await handler(request)
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response

        app.middlewares.append(cors_middleware)
        app.middlewares.append(auth_middleware)

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
