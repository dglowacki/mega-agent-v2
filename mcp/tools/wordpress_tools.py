"""
WordPress Tools - Content management.

Provides WordPress integration for the voice assistant.
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "integrations"))

logger = logging.getLogger(__name__)

_wordpress_client = None


def _get_wordpress():
    """Get WordPress client."""
    global _wordpress_client
    if _wordpress_client is None:
        try:
            from wordpress_client import WordPressClient
            _wordpress_client = WordPressClient()
        except Exception as e:
            logger.error(f"Failed to init WordPress: {e}")
            return None
    return _wordpress_client


def wp_list_posts(status: str = "publish", limit: int = 10) -> str:
    """List WordPress posts."""
    client = _get_wordpress()
    if not client:
        return "Error: WordPress not configured"

    try:
        posts = client.get_posts(status=status, per_page=limit)

        if not posts:
            return "No posts found"

        lines = [f"WordPress Posts ({status}):"]
        for post in posts:
            title = post.get('title', {}).get('rendered', 'No title')
            post_id = post.get('id', '')
            lines.append(f"  [{post_id}] {title[:50]}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error listing posts: {str(e)}"


def wp_get_post(post_id: int) -> str:
    """Get a WordPress post."""
    client = _get_wordpress()
    if not client:
        return "Error: WordPress not configured"

    try:
        post = client.get_post(post_id)

        if not post:
            return f"Post {post_id} not found"

        title = post.get('title', {}).get('rendered', 'No title')
        status = post.get('status', 'Unknown')
        content = post.get('content', {}).get('rendered', '')[:500]

        return f"Post: {title}\nStatus: {status}\nContent: {content}..."
    except Exception as e:
        return f"Error getting post: {str(e)}"


def wp_create_post(
    title: str,
    content: str,
    status: str = "draft"
) -> str:
    """Create a WordPress post."""
    client = _get_wordpress()
    if not client:
        return "Error: WordPress not configured"

    try:
        post = client.create_post(title=title, content=content, status=status)

        if post:
            return f"Created post: {post.get('id')} - {title}"
        return "Failed to create post"
    except Exception as e:
        return f"Error creating post: {str(e)}"


def wp_update_post(
    post_id: int,
    title: str = None,
    content: str = None,
    status: str = None
) -> str:
    """Update a WordPress post."""
    client = _get_wordpress()
    if not client:
        return "Error: WordPress not configured"

    try:
        updates = {}
        if title:
            updates['title'] = title
        if content:
            updates['content'] = content
        if status:
            updates['status'] = status

        result = client.update_post(post_id, **updates)

        if result:
            return f"Updated post {post_id}"
        return f"Failed to update post {post_id}"
    except Exception as e:
        return f"Error updating post: {str(e)}"


def register_wordpress_tools(server) -> int:
    """Register WordPress tools."""

    server.register_tool(
        name="wp_list_posts",
        description="List WordPress posts.",
        input_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Post status", "default": "publish"},
                "limit": {"type": "integer", "description": "Max posts", "default": 10}
            }
        },
        handler=wp_list_posts,
        requires_approval=False,
        category="wordpress"
    )

    server.register_tool(
        name="wp_get_post",
        description="Get a WordPress post by ID.",
        input_schema={
            "type": "object",
            "properties": {
                "post_id": {"type": "integer", "description": "Post ID"}
            },
            "required": ["post_id"]
        },
        handler=wp_get_post,
        requires_approval=False,
        category="wordpress"
    )

    server.register_tool(
        name="wp_create_post",
        description="Create a WordPress post.",
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Post title"},
                "content": {"type": "string", "description": "Post content"},
                "status": {"type": "string", "description": "Post status", "default": "draft"}
            },
            "required": ["title", "content"]
        },
        handler=wp_create_post,
        requires_approval=True,
        category="wordpress"
    )

    server.register_tool(
        name="wp_update_post",
        description="Update a WordPress post.",
        input_schema={
            "type": "object",
            "properties": {
                "post_id": {"type": "integer", "description": "Post ID"},
                "title": {"type": "string", "description": "New title"},
                "content": {"type": "string", "description": "New content"},
                "status": {"type": "string", "description": "New status"}
            },
            "required": ["post_id"]
        },
        handler=wp_update_post,
        requires_approval=True,
        category="wordpress"
    )

    return 4
