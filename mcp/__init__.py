"""
MCP Server v2 - Model Context Protocol implementation for ElevenLabs integration.

Provides:
- SSE transport for real-time communication
- 50+ tools across file, bash, git, GitHub, AWS, email, calendar
- 27 skills exposed as MCP prompts
- Security layer with safe/trust approval modes
"""

from .protocol import MCPServer, MCPMessage
from .security import SecurityManager, ApprovalMode

__version__ = "2.0.0"
__all__ = ["MCPServer", "MCPMessage", "SecurityManager", "ApprovalMode"]
