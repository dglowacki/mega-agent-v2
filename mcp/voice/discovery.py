"""
Tier 3 Discovery Tools

Universal access to all tools:
- tools_search: Find tools by keyword or intent
- tools_schema: Get full schema for any tool
- tools_execute: Execute any tool dynamically
"""

import logging
from typing import Any, Optional
import json

logger = logging.getLogger(__name__)

# Reference to the MCP server (set during registration)
_mcp_server = None


def tools_search(
    query: str,
    category: Optional[str] = None,
    format: str = "voice"
) -> dict:
    """
    Search for tools by keyword or intent.

    Args:
        query: Search query (e.g., "send message", "create file", "deploy")
        category: Optional category filter
        format: "voice" or "standard"

    Returns:
        Matching tools with descriptions
    """
    if not _mcp_server:
        return {"error": "Server not initialized"}

    query_lower = query.lower()
    matches = []

    for name, tool in _mcp_server._tools.items():
        # Score based on name and description match
        score = 0
        name_lower = name.lower()
        desc_lower = tool.description.lower() if tool.description else ""

        # Exact name match
        if query_lower in name_lower:
            score += 10

        # Word matches in name
        for word in query_lower.split():
            if word in name_lower:
                score += 5
            if word in desc_lower:
                score += 2

        # Category filter
        tool_category = getattr(tool, 'category', 'general')
        if category and category.lower() != tool_category.lower():
            continue

        if score > 0:
            matches.append({
                "name": name,
                "description": tool.description[:100] if tool.description else "",
                "category": tool_category,
                "score": score
            })

    # Sort by score
    matches.sort(key=lambda x: x["score"], reverse=True)
    matches = matches[:10]  # Top 10

    if format == "voice":
        if not matches:
            return {"spoken": f"No tools found matching '{query}'"}

        top_names = [m["name"] for m in matches[:5]]
        return {
            "matches": matches,
            "spoken": f"Found {len(matches)} tools. Top matches: {', '.join(top_names)}"
        }

    return {"matches": matches, "total": len(matches)}


def tools_schema(
    tool_name: str,
    format: str = "voice"
) -> dict:
    """
    Get full schema for any tool.

    Args:
        tool_name: Name of the tool
        format: "voice" or "standard"

    Returns:
        Tool schema with description and parameters
    """
    if not _mcp_server:
        return {"error": "Server not initialized"}

    tool = _mcp_server._tools.get(tool_name)
    if not tool:
        # Try with underscores/dots
        tool = _mcp_server._tools.get(tool_name.replace(".", "_"))
        if not tool:
            tool = _mcp_server._tools.get(tool_name.replace("_", "."))

    if not tool:
        return {"error": f"Tool '{tool_name}' not found"}

    schema = {
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.input_schema,
        "requires_approval": tool.requires_approval,
        "category": getattr(tool, 'category', 'general')
    }

    if format == "voice":
        # Summarize for voice
        params = tool.input_schema.get("properties", {})
        required = tool.input_schema.get("required", [])

        param_summary = []
        for name, spec in list(params.items())[:5]:
            req = "(required)" if name in required else ""
            param_summary.append(f"{name} {req}".strip())

        return {
            **schema,
            "spoken": f"{tool.name}: {tool.description[:100]}. Parameters: {', '.join(param_summary) or 'none'}"
        }

    return schema


def tools_execute(
    tool_name: str,
    arguments: dict,
    format: str = "voice"
) -> dict:
    """
    Execute any tool by name with arguments.

    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments
        format: "voice" or "standard"

    Returns:
        Tool execution result
    """
    if not _mcp_server:
        return {"error": "Server not initialized"}

    tool = _mcp_server._tools.get(tool_name)
    if not tool:
        tool = _mcp_server._tools.get(tool_name.replace(".", "_"))
        if not tool:
            tool = _mcp_server._tools.get(tool_name.replace("_", "."))

    if not tool:
        return {"error": f"Tool '{tool_name}' not found"}

    try:
        # Execute the tool
        result = tool.handler(**arguments)

        if format == "voice":
            from .formatter import format_response, VoiceFormat
            return format_response(result, VoiceFormat.VOICE, tool_name)

        return {"result": result}

    except TypeError as e:
        return {"error": f"Invalid arguments: {str(e)}"}
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        return {"error": str(e)}


def register_discovery_tools(server) -> int:
    """Register Tier 3 discovery tools with the MCP server."""
    global _mcp_server
    _mcp_server = server

    server.register_tool(
        name="tools_search",
        description="Search for tools by keyword or intent. Use when you need to find a tool you don't know the name of.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (e.g., 'send message', 'create file', 'deploy')"
                },
                "category": {
                    "type": "string",
                    "description": "Optional category filter (e.g., 'slack', 'git', 'aws')"
                },
                "format": {
                    "type": "string",
                    "enum": ["voice", "standard"],
                    "default": "voice"
                }
            },
            "required": ["query"]
        },
        handler=tools_search,
        requires_approval=False,
        category="discovery"
    )

    server.register_tool(
        name="tools_schema",
        description="Get full schema and parameters for any tool. Use to understand how to call a tool.",
        input_schema={
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "description": "Name of the tool"
                },
                "format": {
                    "type": "string",
                    "enum": ["voice", "standard"],
                    "default": "voice"
                }
            },
            "required": ["tool_name"]
        },
        handler=tools_schema,
        requires_approval=False,
        category="discovery"
    )

    server.register_tool(
        name="tools_execute",
        description="Execute any tool by name with arguments. Use when you found a tool via search and want to run it.",
        input_schema={
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "description": "Name of the tool to execute"
                },
                "arguments": {
                    "type": "object",
                    "description": "Tool arguments as key-value pairs"
                },
                "format": {
                    "type": "string",
                    "enum": ["voice", "standard"],
                    "default": "voice"
                }
            },
            "required": ["tool_name", "arguments"]
        },
        handler=tools_execute,
        requires_approval=True,  # Require approval since it can call any tool
        category="discovery"
    )

    return 3
