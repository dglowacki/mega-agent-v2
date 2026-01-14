"""
Slack MCP Server for Claude Agent SDK

Exposes Slack operations as MCP tools that agents can use directly.
"""

import os
import sys
from pathlib import Path

# Add integrations to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_agent_sdk import create_sdk_mcp_server, tool
from slack_client import SlackMessageReader


@tool(
    name="send_slack_dm",
    description="Send a Slack direct message to a user",
    input_schema={
        "type": "object",
        "properties": {
            "recipient": {
                "type": "string",
                "description": "Recipient: @username, email, user_id, or 'self'"
            },
            "message": {
                "type": "string",
                "description": "Message text to send"
            },
            "workspace": {
                "type": "string",
                "description": "Workspace: 'flycow' or 'trailmix'",
                "enum": ["flycow", "trailmix"],
                "default": "flycow"
            }
        },
        "required": ["recipient", "message"]
    }
)
def send_slack_dm(args):
    """Send Slack direct message."""
    try:
        workspace = args.get("workspace", "flycow")
        slack = SlackMessageReader(workspace=workspace)

        result = slack.send_dm(
            recipient=args["recipient"],
            text=args["message"]
        )

        return {
            "content": [{
                "type": "text",
                "text": f"✓ Slack DM sent successfully to {args['recipient']} in {workspace} workspace"
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to send Slack DM: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="send_slack_channel_message",
    description="Send a message to a Slack channel",
    input_schema={
        "type": "object",
        "properties": {
            "channel_id": {
                "type": "string",
                "description": "Channel ID (e.g., C12345678)"
            },
            "message": {
                "type": "string",
                "description": "Message text to send"
            },
            "workspace": {
                "type": "string",
                "description": "Workspace: 'flycow' or 'trailmix'",
                "enum": ["flycow", "trailmix"],
                "default": "flycow"
            }
        },
        "required": ["channel_id", "message"]
    }
)
def send_slack_channel_message(args):
    """Send message to Slack channel."""
    try:
        workspace = args.get("workspace", "flycow")
        slack = SlackMessageReader(workspace=workspace)

        result = slack.send_message(
            channel_id=args["channel_id"],
            text=args["message"]
        )

        return {
            "content": [{
                "type": "text",
                "text": f"✓ Message sent to channel {args['channel_id']} in {workspace} workspace"
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to send channel message: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="list_slack_users",
    description="List all users in a Slack workspace",
    input_schema={
        "type": "object",
        "properties": {
            "workspace": {
                "type": "string",
                "description": "Workspace: 'flycow' or 'trailmix'",
                "enum": ["flycow", "trailmix"],
                "default": "flycow"
            }
        }
    }
)
def list_slack_users(args):
    """List Slack users."""
    try:
        workspace = args.get("workspace", "flycow")
        slack = SlackMessageReader(workspace=workspace)

        users = slack.list_all_users()

        # Format user list
        user_lines = []
        for user in users[:50]:  # Limit to first 50
            user_lines.append(
                f"- {user.get('real_name', 'Unknown')} "
                f"(@{user.get('name', 'unknown')}) "
                f"[{user.get('id', '')}]"
            )

        return {
            "content": [{
                "type": "text",
                "text": f"Slack users in {workspace} workspace:\n" + "\n".join(user_lines)
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to list users: {str(e)}"
            }],
            "isError": True
        }


# Create and export the MCP server
slack_mcp_server = create_sdk_mcp_server(
    name="slack",
    version="1.0.0",
    tools=[send_slack_dm, send_slack_channel_message, list_slack_users]
)
