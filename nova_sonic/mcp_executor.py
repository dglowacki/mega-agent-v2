"""
MCP Tool Executor

Executes tools by calling the MCP server.
"""

import logging
import httpx
from typing import Any

from . import config
from .claude_bridge import ask_claude

logger = logging.getLogger(__name__)

MCP_BASE_URL = config.MCP_SERVER_URL


async def execute_tool(tool_name: str, params: dict) -> Any:
    """
    Execute a tool via the MCP server.

    Args:
        tool_name: Name of the tool to execute
        params: Tool parameters

    Returns:
        Tool execution result
    """
    logger.info(f"Executing tool: {tool_name}")

    # Handle local tools
    if tool_name == "ask_claude":
        query = params.get("query", "")
        return await ask_claude(query)

    if tool_name == "get_time":
        from datetime import datetime
        try:
            import pytz
            tz_name = params.get("timezone", "America/Los_Angeles")
            tz = pytz.timezone(tz_name)
            now = datetime.now(tz)
            return f"It's {now.strftime('%I:%M %p')} on {now.strftime('%A, %B %d, %Y')} ({tz_name})"
        except Exception as e:
            return f"Error getting time: {e}"

    # Call MCP server for everything else
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            message = {
                "jsonrpc": "2.0",
                "id": f"tool-{tool_name}",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": params
                }
            }

            response = await client.post(f"{MCP_BASE_URL}/messages", json=message)

            if response.status_code in [200, 202]:
                result = response.json()

                # Extract content from MCP response
                if "result" in result:
                    content = result["result"].get("content", [])
                    if content and isinstance(content, list):
                        texts = [b.get("text", "") for b in content if b.get("type") == "text"]
                        return "\n".join(texts) if texts else result["result"]
                    return result["result"]
                elif "error" in result:
                    return f"Error: {result['error'].get('message', result['error'])}"
                return result
            else:
                return f"MCP error: {response.status_code}"

    except httpx.TimeoutException:
        return f"Tool {tool_name} timed out"
    except Exception as e:
        return f"Tool error: {e}"
