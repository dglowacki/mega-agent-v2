"""
MCP Tool Executor

Executes MCP tools by calling the MCP server.
"""

import asyncio
import json
import logging
import httpx
from typing import Any, Optional

from . import config
from .claude_bridge import ask_claude

logger = logging.getLogger(__name__)

# MCP Server base URL
MCP_BASE_URL = config.MCP_SERVER_URL


async def execute_tool(tool_name: str, params: dict) -> Any:
    """
    Execute an MCP tool.

    Args:
        tool_name: Name of the tool to execute
        params: Tool parameters

    Returns:
        Tool execution result
    """
    logger.info(f"Executing tool: {tool_name} with params: {params}")

    # Special handling for ask_claude
    if tool_name == "ask_claude":
        query = params.get("query", "")
        return await ask_claude(query)

    # Call MCP server for other tools
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{MCP_BASE_URL}/tools/call",
                json={
                    "name": tool_name,
                    "arguments": params
                }
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"Tool {tool_name} executed successfully")
                return result.get("result", result)
            else:
                error = f"MCP server returned {response.status_code}: {response.text}"
                logger.error(error)
                return {"error": error}

    except httpx.TimeoutException:
        error = f"Tool {tool_name} timed out"
        logger.error(error)
        return {"error": error}

    except Exception as e:
        error = f"Tool execution failed: {str(e)}"
        logger.error(error)
        return {"error": error}


async def list_available_tools() -> list[dict]:
    """
    Get list of available tools from MCP server.

    Returns:
        List of tool definitions
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{MCP_BASE_URL}/tools/list")

            if response.status_code == 200:
                result = response.json()
                return result.get("tools", [])
            else:
                logger.error(f"Failed to list tools: {response.status_code}")
                return []

    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        return []


# Voice-relevant tools to expose directly to Nova
# These are the tools that make sense for voice interactions
VOICE_TOOLS = [
    # Quick lookups
    "get_weather",
    "get_time",
    "web_search",

    # Calendar/scheduling
    "list_calendar_events",
    "create_calendar_event",

    # Communication
    "send_email",
    "list_emails",
    "send_slack_message",

    # Tasks
    "list_tasks",
    "create_task",

    # Analytics (for your apps)
    "keno_analytics",
    "appstore_sales",

    # Shortcuts
    "list_shortcuts",
    "run_shortcut",

    # Files (basic)
    "read_file",
    "list_files",

    # ask_claude for complex tasks
    "ask_claude"
]


def is_voice_relevant(tool_name: str) -> bool:
    """Check if a tool is voice-relevant."""
    return tool_name in VOICE_TOOLS or tool_name == "ask_claude"
