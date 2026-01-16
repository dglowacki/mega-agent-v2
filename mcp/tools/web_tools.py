"""
Web Tools - Search and fetch web content.

Provides web search and content fetching capabilities.
"""

import subprocess
import logging
import json
import re
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Maximum content length to return
MAX_CONTENT = 20000


def web_search(
    query: str,
    limit: int = 5
) -> str:
    """
    Search the web using DuckDuckGo.

    Args:
        query: Search query
        limit: Maximum results to return

    Returns:
        Search results
    """
    try:
        # Use curl to fetch DuckDuckGo HTML search
        cmd = [
            "curl", "-s", "-L",
            "-A", "Mozilla/5.0 (compatible; VoiceAssistant/1.0)",
            f"https://html.duckduckgo.com/html/?q={query}"
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode != 0:
            return f"Search failed: {result.stderr}"

        html = result.stdout

        # Parse results from HTML
        results = []
        # Find result blocks
        pattern = r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>'
        matches = re.findall(pattern, html)

        for url, title in matches[:limit]:
            results.append(f"- {title.strip()}\n  {url}")

        if not results:
            return f"No results found for: {query}"

        return f"Search results for '{query}':\n\n" + "\n\n".join(results)

    except subprocess.TimeoutExpired:
        return "Search timed out"
    except Exception as e:
        return f"Search error: {str(e)}"


def web_fetch(
    url: str,
    extract_text: bool = True
) -> str:
    """
    Fetch content from a URL.

    Args:
        url: URL to fetch
        extract_text: Extract text only (strip HTML)

    Returns:
        Page content
    """
    # Validate URL
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ["http", "https"]:
            return f"Invalid URL scheme: {parsed.scheme}"
    except Exception as e:
        return f"Invalid URL: {str(e)}"

    try:
        cmd = [
            "curl", "-s", "-L",
            "-A", "Mozilla/5.0 (compatible; VoiceAssistant/1.0)",
            "--max-time", "30",
            url
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=35
        )

        if result.returncode != 0:
            return f"Fetch failed: {result.stderr}"

        content = result.stdout

        if extract_text:
            # Simple HTML to text conversion
            # Remove script and style
            content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
            content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)

            # Remove HTML tags
            content = re.sub(r'<[^>]+>', ' ', content)

            # Decode entities
            content = content.replace('&nbsp;', ' ')
            content = content.replace('&amp;', '&')
            content = content.replace('&lt;', '<')
            content = content.replace('&gt;', '>')
            content = content.replace('&quot;', '"')

            # Clean whitespace
            content = re.sub(r'\s+', ' ', content)
            content = content.strip()

        # Truncate if too long
        if len(content) > MAX_CONTENT:
            content = content[:MAX_CONTENT] + "\n\n... (content truncated)"

        return content

    except subprocess.TimeoutExpired:
        return "Fetch timed out"
    except Exception as e:
        return f"Fetch error: {str(e)}"


def web_api_call(
    url: str,
    method: str = "GET",
    headers: str = None,
    body: str = None
) -> str:
    """
    Make an HTTP API call.

    Args:
        url: API URL
        method: HTTP method (GET, POST, PUT, DELETE)
        headers: Headers as JSON string
        body: Request body

    Returns:
        API response
    """
    # Validate URL
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ["http", "https"]:
            return f"Invalid URL scheme: {parsed.scheme}"
    except Exception as e:
        return f"Invalid URL: {str(e)}"

    # Validate method
    method = method.upper()
    if method not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
        return f"Invalid method: {method}"

    cmd = ["curl", "-s", "-X", method, "--max-time", "30"]

    # Add headers
    if headers:
        try:
            header_dict = json.loads(headers)
            for key, value in header_dict.items():
                cmd.extend(["-H", f"{key}: {value}"])
        except json.JSONDecodeError:
            return "Invalid headers JSON"

    # Add body
    if body:
        cmd.extend(["-d", body])

    cmd.append(url)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=35
        )

        if result.returncode != 0:
            return f"API call failed: {result.stderr}"

        # Try to pretty-print JSON
        content = result.stdout
        try:
            parsed_json = json.loads(content)
            content = json.dumps(parsed_json, indent=2)
        except json.JSONDecodeError:
            pass

        # Truncate if too long
        if len(content) > MAX_CONTENT:
            content = content[:MAX_CONTENT] + "\n\n... (response truncated)"

        return content

    except subprocess.TimeoutExpired:
        return "API call timed out"
    except Exception as e:
        return f"API call error: {str(e)}"


def register_web_tools(server) -> int:
    """Register all web tools with the MCP server."""

    server.register_tool(
        name="web_search",
        description="Search the web using DuckDuckGo. Returns titles and URLs.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results", "default": 5}
            },
            "required": ["query"]
        },
        handler=web_search,
        requires_approval=False,
        category="web"
    )

    server.register_tool(
        name="web_fetch",
        description="Fetch content from a URL. Optionally extracts text only.",
        input_schema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch"},
                "extract_text": {"type": "boolean", "description": "Extract text only", "default": True}
            },
            "required": ["url"]
        },
        handler=web_fetch,
        requires_approval=False,
        category="web"
    )

    server.register_tool(
        name="web_api_call",
        description="Make an HTTP API call (GET, POST, PUT, DELETE).",
        input_schema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "API URL"},
                "method": {"type": "string", "description": "HTTP method", "default": "GET"},
                "headers": {"type": "string", "description": "Headers as JSON"},
                "body": {"type": "string", "description": "Request body"}
            },
            "required": ["url"]
        },
        handler=web_api_call,
        requires_approval=False,
        category="web"
    )

    return 3  # Number of tools registered
