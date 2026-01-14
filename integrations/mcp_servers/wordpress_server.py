"""
WordPress MCP Server for Claude Agent SDK

Exposes WordPress REST API operations as MCP tools that agents can use directly.
"""

import os
import sys
from pathlib import Path

# Add integrations to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_agent_sdk import create_sdk_mcp_server, tool
from wordpress_client import WordPressClient


# Helper to get WordPress client from config
def get_wordpress_client(site: str = "listorati"):
    """Get WordPress client for a site."""
    # Default to Listorati
    if site == "listorati" or not site:
        site_url = os.getenv("WORDPRESS_LISTORATI_URL", "https://listorati.com")
        username = os.getenv("WORDPRESS_LISTORATI_USERNAME")
        app_password = os.getenv("WORDPRESS_LISTORATI_APP_PASSWORD")
    else:
        # Generic fallback
        site_url = os.getenv(f"WORDPRESS_{site.upper()}_URL")
        username = os.getenv(f"WORDPRESS_{site.upper()}_USERNAME")
        app_password = os.getenv(f"WORDPRESS_{site.upper()}_APP_PASSWORD")

    if not all([site_url, username, app_password]):
        raise ValueError(f"WordPress credentials not configured for site: {site}")

    return WordPressClient(site_url, username, app_password)


@tool(
    name="wordpress_get_posts",
    description="Get posts from WordPress site",
    input_schema={
        "type": "object",
        "properties": {
            "site": {
                "type": "string",
                "description": "Site identifier (default: 'listorati')",
                "default": "listorati"
            },
            "per_page": {
                "type": "number",
                "description": "Posts per page (default: 10)",
                "default": 10
            },
            "page": {
                "type": "number",
                "description": "Page number (default: 1)",
                "default": 1
            },
            "status": {
                "type": "string",
                "description": "Post status filter (publish, draft, pending, etc.)"
            }
        }
    }
)
async def wordpress_get_posts(args):
    """Get WordPress posts."""
    try:
        site = args.get("site", "listorati")
        per_page = args.get("per_page", 10)
        page = args.get("page", 1)
        status = args.get("status")

        client = get_wordpress_client(site)

        kwargs = {}
        if status:
            kwargs["status"] = status

        posts = await client.get_posts(per_page=per_page, page=page, **kwargs)

        post_lines = [f"Found {len(posts)} posts on {site}:\n"]
        for post in posts[:20]:  # Limit display to first 20
            title = post.get("title", {}).get("rendered", "Untitled")
            post_id = post.get("id")
            post_status = post.get("status", "unknown")
            post_lines.append(f"- [{post_id}] {title} ({post_status})")

        return {
            "content": [{
                "type": "text",
                "text": "\n".join(post_lines)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to get posts: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="wordpress_get_post",
    description="Get a specific WordPress post by ID",
    input_schema={
        "type": "object",
        "properties": {
            "post_id": {
                "type": "number",
                "description": "Post ID"
            },
            "site": {
                "type": "string",
                "description": "Site identifier",
                "default": "listorati"
            }
        },
        "required": ["post_id"]
    }
)
async def wordpress_get_post(args):
    """Get a specific WordPress post."""
    try:
        site = args.get("site", "listorati")
        post_id = args["post_id"]

        client = get_wordpress_client(site)
        post = await client.get_post(post_id)

        title = post.get("title", {}).get("rendered", "Untitled")
        content_len = len(post.get("content", {}).get("rendered", ""))
        status = post.get("status", "unknown")

        return {
            "content": [{
                "type": "text",
                "text": f"✓ Post {post_id}: {title}\n"
                       f"Status: {status}\n"
                       f"Content length: {content_len} characters"
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to get post: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="wordpress_update_post",
    description="Update a WordPress post",
    input_schema={
        "type": "object",
        "properties": {
            "post_id": {
                "type": "number",
                "description": "Post ID"
            },
            "title": {
                "type": "string",
                "description": "New title"
            },
            "content": {
                "type": "string",
                "description": "New content (HTML)"
            },
            "status": {
                "type": "string",
                "description": "Post status (publish, draft, pending, etc.)"
            },
            "site": {
                "type": "string",
                "description": "Site identifier",
                "default": "listorati"
            }
        },
        "required": ["post_id"]
    }
)
async def wordpress_update_post(args):
    """Update a WordPress post."""
    try:
        site = args.get("site", "listorati")
        post_id = args["post_id"]

        client = get_wordpress_client(site)

        # Build update data
        update_data = {}
        if "title" in args:
            update_data["title"] = args["title"]
        if "content" in args:
            update_data["content"] = args["content"]
        if "status" in args:
            update_data["status"] = args["status"]

        post = await client.update_post(post_id, **update_data)

        title = post.get("title", {}).get("rendered", "Untitled")

        return {
            "content": [{
                "type": "text",
                "text": f"✓ Post {post_id} updated successfully: {title}"
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to update post: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="wordpress_search",
    description="Search WordPress content",
    input_schema={
        "type": "object",
        "properties": {
            "search_term": {
                "type": "string",
                "description": "Search query"
            },
            "type": {
                "type": "string",
                "description": "Content type (post, page, etc.)",
                "default": "post"
            },
            "site": {
                "type": "string",
                "description": "Site identifier",
                "default": "listorati"
            },
            "per_page": {
                "type": "number",
                "description": "Results per page",
                "default": 10
            }
        },
        "required": ["search_term"]
    }
)
async def wordpress_search(args):
    """Search WordPress content."""
    try:
        site = args.get("site", "listorati")
        search_term = args["search_term"]
        content_type = args.get("type", "post")
        per_page = args.get("per_page", 10)

        client = get_wordpress_client(site)
        results = await client.search(
            search_term=search_term,
            type=content_type,
            per_page=per_page
        )

        result_lines = [f"Found {len(results)} results for '{search_term}':\n"]
        for result in results[:20]:
            title = result.get("title", "Untitled")
            result_id = result.get("id")
            result_lines.append(f"- [{result_id}] {title}")

        return {
            "content": [{
                "type": "text",
                "text": "\n".join(result_lines)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Search failed: {str(e)}"
            }],
            "isError": True
        }


# Create and export the MCP server
wordpress_mcp_server = create_sdk_mcp_server(
    name="wordpress",
    version="1.0.0",
    tools=[
        wordpress_get_posts,
        wordpress_get_post,
        wordpress_update_post,
        wordpress_search
    ]
)
