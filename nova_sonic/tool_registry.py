"""
Nova Tool Registry

Fetches tools from MCP server and converts to Nova 2 Sonic format.
"""

import logging
import httpx
from typing import Optional
from . import config

logger = logging.getLogger(__name__)

# Cache for tools
_cached_tools: Optional[list[dict]] = None


def _fetch_mcp_tools() -> list[dict]:
    """Fetch tools from MCP server."""
    try:
        response = httpx.get(f"{config.MCP_SERVER_URL}/tools", timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            return data.get("tools", [])
    except Exception as e:
        logger.error(f"Failed to fetch MCP tools: {e}")
    return []


def _convert_to_nova_format(mcp_tool: dict) -> dict:
    """Convert MCP tool schema to Nova format."""
    return {
        "toolSpec": {
            "name": mcp_tool["name"],
            "description": mcp_tool.get("description", ""),
            "inputSchema": {
                "json": mcp_tool.get("inputSchema", {"type": "object", "properties": {}})
            }
        }
    }


# Tools most useful for voice interactions
VOICE_RELEVANT_TOOLS = {
    # Information
    "web_search", "web_fetch",

    # Calendar
    "google_calendar_list", "google_calendar_create",

    # Email
    "gmail_list", "gmail_send", "gmail_read",

    # Slack
    "slack_send_dm", "slack_send_channel", "slack_send_image",
    "slack_get_messages", "slack_get_unread",

    # Tasks
    "linear_list_issues", "linear_create_issue",
    "clickup_list_tasks", "clickup_create_task",

    # Images
    "image_generate", "image_generate_icon",

    # Files (basic)
    "file_read", "file_glob",

    # App analytics
    "appstore_sales_summary", "appstore_get_app",

    # GitHub
    "github_list_prs", "github_get_pr", "github_list_issues",
}


def get_tool_definitions() -> list[dict]:
    """
    Get tool definitions in Nova format.

    Fetches from MCP server and filters to voice-relevant tools.
    Always includes ask_claude for complex reasoning.
    """
    global _cached_tools

    tools = []

    # Always add ask_claude (handled locally, not via MCP)
    tools.append({
        "toolSpec": {
            "name": "ask_claude",
            "description": "Ask Claude for help with complex reasoning, analysis, code review, or multi-step tasks. Use for anything requiring deep thinking.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The question or task for Claude"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    })

    # Add built-in get_time (doesn't need MCP)
    tools.append({
        "toolSpec": {
            "name": "get_time",
            "description": "Get current time in a timezone",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "description": "Timezone name (default: America/Los_Angeles)"
                        }
                    },
                    "required": []
                }
            }
        }
    })

    # Fetch MCP tools
    mcp_tools = _fetch_mcp_tools()

    if mcp_tools:
        _cached_tools = mcp_tools
        logger.info(f"Fetched {len(mcp_tools)} tools from MCP server")
    elif _cached_tools:
        mcp_tools = _cached_tools
        logger.info(f"Using {len(mcp_tools)} cached MCP tools")
    else:
        logger.warning("No MCP tools available")

    # Filter to voice-relevant tools and convert format
    for mcp_tool in mcp_tools:
        name = mcp_tool.get("name", "")
        if name in VOICE_RELEVANT_TOOLS:
            tools.append(_convert_to_nova_format(mcp_tool))

    logger.info(f"Registered {len(tools)} tools for Nova")
    return tools


def get_tool_count() -> int:
    """Get the number of registered tools."""
    return len(get_tool_definitions())
