"""
MCP Servers for mega-agent2 integrations.

Exposes integrations as proper SDK tools that agents can use.
"""

# Core communication servers
from .slack_server import slack_mcp_server
from .gmail_server import gmail_mcp_server
from .github_server import github_mcp_server

# Integration servers
from .appstore_server import appstore_mcp_server
from .wordpress_server import wordpress_mcp_server
from .google_calendar_server import google_calendar_mcp_server
from .google_tasks_server import google_tasks_mcp_server
from .clickup_server import clickup_mcp_server
from .linear_server import linear_mcp_server
from .supabase_server import supabase_mcp_server
from .firebase_server import firebase_mcp_server
from .google_ads_server import google_ads_mcp_server

__all__ = [
    # Core
    'slack_mcp_server',
    'gmail_mcp_server',
    'github_mcp_server',
    # Integrations
    'appstore_mcp_server',
    'wordpress_mcp_server',
    'google_calendar_mcp_server',
    'google_tasks_mcp_server',
    'clickup_mcp_server',
    'linear_mcp_server',
    'supabase_mcp_server',
    'firebase_mcp_server',
    'google_ads_mcp_server'
]
