"""
Claude Bridge

Handles ask_claude tool - routes complex queries to Claude with full MCP access.
"""

import json
import logging
import httpx
from typing import Any, Optional

from anthropic import Anthropic

from . import config

logger = logging.getLogger(__name__)

# Claude client
_client: Optional[Anthropic] = None


def get_client() -> Anthropic:
    """Get or create Anthropic client."""
    global _client
    if _client is None:
        _client = Anthropic()
    return _client


async def ask_claude(query: str) -> str:
    """
    Route a query to Claude with full MCP tool access.

    Args:
        query: The question or task for Claude

    Returns:
        Claude's response text
    """
    logger.info(f"ask_claude: {query[:100]}...")

    client = get_client()

    # Get MCP tool definitions for Claude
    tools = await get_mcp_tools_for_claude()

    try:
        # Initial request
        response = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=4096,
            system="""You are called via a voice assistant. Provide concise responses optimized for speech.

GUIDELINES:
- Keep responses brief and conversational
- Avoid code blocks, markdown, or long lists
- Use natural spoken language
- Maximum 2-3 paragraphs for complex topics
- If showing code or data, summarize verbally

You have access to MCP tools for file operations, web search, email, calendar, and more.
Use them when needed to answer the user's question.""",
            messages=[{"role": "user", "content": query}],
            tools=tools if tools else None
        )

        # Handle tool use loop
        messages = [{"role": "user", "content": query}]

        while response.stop_reason == "tool_use":
            # Collect tool results
            tool_results = []
            assistant_content = []

            for block in response.content:
                if block.type == "tool_use":
                    logger.info(f"Claude calling tool: {block.name}")
                    result = await execute_mcp_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result) if not isinstance(result, str) else result
                    })
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })
                elif block.type == "text":
                    assistant_content.append({
                        "type": "text",
                        "text": block.text
                    })

            # Add assistant message and tool results
            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})

            # Continue conversation
            response = client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=4096,
                system="""You are called via a voice assistant. Provide concise responses optimized for speech.""",
                messages=messages,
                tools=tools if tools else None
            )

        # Extract final text response
        result_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                result_text += block.text

        logger.info(f"ask_claude response: {result_text[:100]}...")
        return result_text

    except Exception as e:
        logger.error(f"ask_claude error: {e}")
        return f"I encountered an error: {str(e)}"


async def get_mcp_tools_for_claude() -> list[dict]:
    """
    Get MCP tool definitions in Claude format.

    Returns:
        List of tool definitions for Claude API
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{config.MCP_SERVER_URL}/tools/list")

            if response.status_code == 200:
                result = response.json()
                mcp_tools = result.get("tools", [])

                # Convert to Claude format
                claude_tools = []
                for tool in mcp_tools:
                    claude_tools.append({
                        "name": tool.get("name"),
                        "description": tool.get("description", ""),
                        "input_schema": tool.get("inputSchema", {
                            "type": "object",
                            "properties": {},
                            "required": []
                        })
                    })

                return claude_tools

    except Exception as e:
        logger.error(f"Failed to get MCP tools: {e}")

    # Fallback: return basic tools
    return [
        {
            "name": "web_search",
            "description": "Search the web",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        },
        {
            "name": "read_file",
            "description": "Read a file",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"}
                },
                "required": ["path"]
            }
        }
    ]


async def execute_mcp_tool(tool_name: str, params: dict) -> Any:
    """
    Execute an MCP tool via the MCP server.

    Args:
        tool_name: Name of the tool
        params: Tool parameters

    Returns:
        Tool execution result
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{config.MCP_SERVER_URL}/tools/call",
                json={
                    "name": tool_name,
                    "arguments": params
                }
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("result", result)
            else:
                return {"error": f"Tool failed: {response.status_code}"}

    except Exception as e:
        logger.error(f"MCP tool execution failed: {e}")
        return {"error": str(e)}


async def summarize_for_context(text: str, max_tokens: int = 2000) -> str:
    """
    Use Claude Haiku to summarize text for context compression.

    Args:
        text: Text to summarize
        max_tokens: Maximum tokens for summary

    Returns:
        Summarized text
    """
    client = get_client()

    try:
        response = client.messages.create(
            model=config.CLAUDE_HAIKU_MODEL,
            max_tokens=max_tokens,
            messages=[{
                "role": "user",
                "content": f"""Summarize this conversation for context continuity.

Preserve:
- Key facts and decisions
- User preferences mentioned
- Ongoing tasks/commitments
- Important names, dates, numbers

Format as concise bullet points.

TEXT TO SUMMARIZE:
{text}"""
            }]
        )

        return response.content[0].text

    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        # Fallback: truncate
        return text[:max_tokens * 4] + "..."
