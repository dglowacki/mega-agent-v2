"""
Slack Tools - Slack messaging and workspace operations.

Provides Slack integration for the voice assistant.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

# Add integrations to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "integrations"))

logger = logging.getLogger(__name__)

# Lazy load SlackMessageReader to avoid import errors if not configured
_slack_clients = {}


def _get_slack_client(workspace: str = "flycow"):
    """Get or create Slack client for workspace."""
    if workspace not in _slack_clients:
        try:
            from slack_client import SlackMessageReader
            _slack_clients[workspace] = SlackMessageReader(workspace=workspace)
        except Exception as e:
            logger.error(f"Failed to initialize Slack client for {workspace}: {e}")
            return None
    return _slack_clients[workspace]


def slack_send_dm(
    recipient: str,
    message: str,
    workspace: str = "flycow"
) -> str:
    """
    Send a Slack direct message.

    Args:
        recipient: @username, email address, user ID, or 'self'
        message: Message text to send
        workspace: 'flycow' or 'trailmix'

    Returns:
        Success or error message
    """
    slack = _get_slack_client(workspace)
    if not slack:
        return f"Error: Could not connect to Slack workspace '{workspace}'"

    try:
        if recipient.lower() == 'self':
            result = slack.send_message_to_self(message)
        else:
            result = slack.send_dm(recipient, message)

        if result:
            return f"Message sent to {recipient} in {workspace} workspace"
        else:
            return f"Failed to send message to {recipient}"

    except Exception as e:
        return f"Error sending Slack DM: {str(e)}"


def slack_send_channel(
    channel: str,
    message: str,
    workspace: str = "flycow"
) -> str:
    """
    Send a message to a Slack channel.

    Args:
        channel: Channel ID or #channel-name
        message: Message text to send
        workspace: 'flycow' or 'trailmix'

    Returns:
        Success or error message
    """
    slack = _get_slack_client(workspace)
    if not slack:
        return f"Error: Could not connect to Slack workspace '{workspace}'"

    try:
        # If channel starts with #, look up the channel ID
        if channel.startswith('#'):
            channel_name = channel[1:]
            channels = slack.get_all_channels()
            channel_id = None
            for ch in channels:
                if ch['name'] == channel_name:
                    channel_id = ch['id']
                    break
            if not channel_id:
                return f"Channel {channel} not found"
        else:
            channel_id = channel

        result = slack.send_message(channel_id, message)
        if result:
            return f"Message sent to channel {channel} in {workspace}"
        else:
            return f"Failed to send message to channel {channel}"

    except Exception as e:
        return f"Error sending channel message: {str(e)}"


def slack_list_channels(workspace: str = "flycow") -> str:
    """
    List all Slack channels in a workspace.

    Args:
        workspace: 'flycow' or 'trailmix'

    Returns:
        List of channels
    """
    slack = _get_slack_client(workspace)
    if not slack:
        return f"Error: Could not connect to Slack workspace '{workspace}'"

    try:
        channels = slack.get_all_channels()

        lines = [f"Channels in {workspace} workspace:"]
        for ch in channels[:30]:
            privacy = "🔒" if ch.get('is_private') else "#"
            members = ch.get('num_members', 0)
            lines.append(f"  {privacy} {ch['name']} ({members} members) - {ch['id']}")

        if len(channels) > 30:
            lines.append(f"  ... and {len(channels) - 30} more")

        return "\n".join(lines)

    except Exception as e:
        return f"Error listing channels: {str(e)}"


def slack_list_users(workspace: str = "flycow") -> str:
    """
    List all users in a Slack workspace.

    Args:
        workspace: 'flycow' or 'trailmix'

    Returns:
        List of users
    """
    slack = _get_slack_client(workspace)
    if not slack:
        return f"Error: Could not connect to Slack workspace '{workspace}'"

    try:
        users = slack.list_all_users()

        lines = [f"Users in {workspace} workspace:"]
        for user in users[:50]:
            name = user.get('real_name', 'Unknown')
            username = user.get('name', 'unknown')
            lines.append(f"  - {name} (@{username})")

        if len(users) > 50:
            lines.append(f"  ... and {len(users) - 50} more")

        return "\n".join(lines)

    except Exception as e:
        return f"Error listing users: {str(e)}"


def slack_get_messages(
    channel: str,
    limit: int = 10,
    workspace: str = "flycow"
) -> str:
    """
    Get recent messages from a Slack channel.

    Args:
        channel: Channel ID or #channel-name
        limit: Number of messages to retrieve
        workspace: 'flycow' or 'trailmix'

    Returns:
        Recent messages with content
    """
    slack = _get_slack_client(workspace)
    if not slack:
        return f"Error: Could not connect to Slack workspace '{workspace}'"

    try:
        # If channel starts with #, look up the channel ID
        if channel.startswith('#'):
            channel_name = channel[1:]
            channels = slack.get_all_channels()
            channel_id = None
            for ch in channels:
                if ch['name'] == channel_name:
                    channel_id = ch['id']
                    break
            if not channel_id:
                return f"Channel {channel} not found"
        else:
            channel_id = channel

        messages = slack.get_channel_messages(channel_id, limit=limit)

        if not messages:
            return f"No messages found in {channel}"

        # Format messages with content
        lines = [f"Retrieved {len(messages)} messages from {channel}:\n"]
        
        for msg in reversed(messages):
            if msg.get('type') == 'message':
                user = msg.get('user', 'Unknown')
                text = msg.get('text', '')
                ts = float(msg['ts'])
                from datetime import datetime
                timestamp = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                
                # Get user name if possible
                try:
                    user_info = slack.client.users_info(user=user)
                    user_name = user_info['user']['real_name']
                except:
                    user_name = user
                
                lines.append(f"[{timestamp}] {user_name}: {text}")

        return "\n".join(lines)

    except Exception as e:
        return f"Error getting messages: {str(e)}"


def slack_search(
    query: str,
    limit: int = 10,
    workspace: str = "flycow"
) -> str:
    """
    Search for messages in Slack.

    Args:
        query: Search query
        limit: Maximum results
        workspace: 'flycow' or 'trailmix'

    Returns:
        Search results
    """
    slack = _get_slack_client(workspace)
    if not slack:
        return f"Error: Could not connect to Slack workspace '{workspace}'"

    try:
        results = slack.search_messages(query, limit=limit)

        if not results:
            return f"No messages found matching '{query}'"

        lines = [f"Search results for '{query}' in {workspace}:"]
        for r in results:
            lines.append(f"\n[{r['timestamp']}] #{r['channel_name']}")
            lines.append(f"  {r['text'][:100]}...")

        return "\n".join(lines)

    except Exception as e:
        return f"Error searching: {str(e)}"


def slack_get_mentions(
    limit: int = 10,
    workspace: str = "flycow"
) -> str:
    """
    Get recent mentions of the authenticated user.

    Args:
        limit: Maximum mentions to retrieve
        workspace: 'flycow' or 'trailmix'

    Returns:
        Recent mentions
    """
    slack = _get_slack_client(workspace)
    if not slack:
        return f"Error: Could not connect to Slack workspace '{workspace}'"

    try:
        mentions = slack.get_mentions(limit=limit)

        if not mentions:
            return "No recent mentions found"

        return f"Found {len(mentions)} mentions"

    except Exception as e:
        return f"Error getting mentions: {str(e)}"


def slack_get_unread(workspace: str = "flycow") -> str:
    """
    Get channels with unread messages.

    Args:
        workspace: 'flycow' or 'trailmix'

    Returns:
        List of channels with unread message counts
    """
    slack = _get_slack_client(workspace)
    if not slack:
        return f"Error: Could not connect to Slack workspace '{workspace}'"

    try:
        unread_channels = slack.get_unread_messages()

        if not unread_channels:
            return f"No unread messages in {workspace}"

        total = sum(ch['count'] for ch in unread_channels)
        lines = [f"Unread messages in {workspace}: {total} total\n"]
        
        for ch in unread_channels:
            lines.append(f"  - {ch['name']}: {ch['count']} unread (ID: {ch['id']})")

        return "\n".join(lines)

    except Exception as e:
        return f"Error getting unread messages: {str(e)}"


def register_slack_tools(server) -> int:
    """Register all Slack tools with the MCP server."""

    server.register_tool(
        name="slack_send_dm",
        description="Send a Slack direct message to a user. Recipient can be @username, email, or 'self'.",
        input_schema={
            "type": "object",
            "properties": {
                "recipient": {"type": "string", "description": "Recipient: @username, email, or 'self'"},
                "message": {"type": "string", "description": "Message text"},
                "workspace": {"type": "string", "description": "Workspace: flycow or trailmix", "default": "flycow"}
            },
            "required": ["recipient", "message"]
        },
        handler=slack_send_dm,
        requires_approval=True,
        category="slack"
    )

    server.register_tool(
        name="slack_send_channel",
        description="Send a message to a Slack channel.",
        input_schema={
            "type": "object",
            "properties": {
                "channel": {"type": "string", "description": "Channel ID or #channel-name"},
                "message": {"type": "string", "description": "Message text"},
                "workspace": {"type": "string", "description": "Workspace: flycow or trailmix", "default": "flycow"}
            },
            "required": ["channel", "message"]
        },
        handler=slack_send_channel,
        requires_approval=True,
        category="slack"
    )

    server.register_tool(
        name="slack_list_channels",
        description="List all Slack channels in a workspace.",
        input_schema={
            "type": "object",
            "properties": {
                "workspace": {"type": "string", "description": "Workspace: flycow or trailmix", "default": "flycow"}
            }
        },
        handler=slack_list_channels,
        requires_approval=False,
        category="slack"
    )

    server.register_tool(
        name="slack_list_users",
        description="List all users in a Slack workspace.",
        input_schema={
            "type": "object",
            "properties": {
                "workspace": {"type": "string", "description": "Workspace: flycow or trailmix", "default": "flycow"}
            }
        },
        handler=slack_list_users,
        requires_approval=False,
        category="slack"
    )

    server.register_tool(
        name="slack_get_messages",
        description="Get recent messages from a Slack channel.",
        input_schema={
            "type": "object",
            "properties": {
                "channel": {"type": "string", "description": "Channel ID or #channel-name"},
                "limit": {"type": "integer", "description": "Number of messages", "default": 10},
                "workspace": {"type": "string", "description": "Workspace: flycow or trailmix", "default": "flycow"}
            },
            "required": ["channel"]
        },
        handler=slack_get_messages,
        requires_approval=False,
        category="slack"
    )

    server.register_tool(
        name="slack_search",
        description="Search for messages in Slack.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results", "default": 10},
                "workspace": {"type": "string", "description": "Workspace: flycow or trailmix", "default": "flycow"}
            },
            "required": ["query"]
        },
        handler=slack_search,
        requires_approval=False,
        category="slack"
    )

    server.register_tool(
        name="slack_get_mentions",
        description="Get recent @mentions of yourself in Slack.",
        input_schema={
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max mentions", "default": 10},
                "workspace": {"type": "string", "description": "Workspace: flycow or trailmix", "default": "flycow"}
            }
        },
        handler=slack_get_mentions,
        requires_approval=False,
        category="slack"
    )

    server.register_tool(
        name="slack_get_unread",
        description="Get channels with unread messages and their counts.",
        input_schema={
            "type": "object",
            "properties": {
                "workspace": {"type": "string", "description": "Workspace: flycow or trailmix", "default": "flycow"}
            }
        },
        handler=slack_get_unread,
        requires_approval=False,
        category="slack"
    )

    server.register_tool(
        name="slack_send_image",
        description="Generate an AI image and send it to Slack. Creates the image first, then uploads it.",
        input_schema={
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Description of the image to generate"},
                "recipient": {"type": "string", "description": "Slack recipient: @username, email, channel name, or 'self'"},
                "message": {"type": "string", "description": "Optional message to include with the image"},
                "workspace": {"type": "string", "description": "Workspace: flycow or trailmix", "default": "flycow"}
            },
            "required": ["prompt", "recipient"]
        },
        handler=slack_send_image,
        requires_approval=True,
        category="slack"
    )

    return 9  # Number of tools registered


def slack_send_image(
    prompt: str,
    recipient: str,
    message: str = None,
    workspace: str = "flycow"
) -> str:
    """
    Generate an AI image and send it to Slack.

    Args:
        prompt: Description of the image to generate
        recipient: @username, email, #channel, or 'self'
        message: Optional message to include with the image
        workspace: 'flycow' or 'trailmix'

    Returns:
        Success or error message
    """
    import os
    import tempfile
    from datetime import datetime

    # First, generate the image
    try:
        from mcp.tools.image_tools import image_generate
        result = image_generate(prompt=prompt, size="1024x1024", quality="standard")

        if "error" in result.lower():
            return f"Failed to generate image: {result}"

        # Extract file path from result
        # The image_generate function returns a path like "/home/.../generated_images/..."
        if "saved to" in result.lower():
            # Parse the path from the result message
            import re
            match = re.search(r'saved to[:\s]+([^\s]+\.png)', result, re.IGNORECASE)
            if match:
                image_path = match.group(1)
            else:
                return f"Could not find image path in result: {result}"
        else:
            return f"Unexpected image generation result: {result}"

        if not os.path.exists(image_path):
            return f"Generated image not found at: {image_path}"

    except Exception as e:
        return f"Error generating image: {str(e)}"

    # Now upload to Slack
    slack = _get_slack_client(workspace)
    if not slack:
        return f"Error: Could not connect to Slack workspace '{workspace}'"

    try:
        title = f"AI Generated: {prompt[:50]}..." if len(prompt) > 50 else f"AI Generated: {prompt}"

        if recipient.startswith('#'):
            # Channel
            channel_name = recipient[1:]
            channels = slack.get_all_channels()
            channel_id = None
            for ch in channels:
                if ch['name'] == channel_name:
                    channel_id = ch['id']
                    break
            if not channel_id:
                return f"Channel {recipient} not found"

            result = slack.upload_file(channel_id, image_path, title=title, initial_comment=message)
        else:
            # DM to user
            result = slack.upload_file_to_user(recipient, image_path, title=title, initial_comment=message)

        if result:
            return f"Image generated and sent to {recipient} in {workspace} workspace"
        else:
            return f"Failed to upload image to {recipient}"

    except Exception as e:
        return f"Error sending image to Slack: {str(e)}"
