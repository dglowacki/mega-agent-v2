"""
ClickUp MCP Server for Claude Agent SDK

Exposes ClickUp operations as MCP tools that agents can use directly.
"""

import os
import sys
from pathlib import Path

# Add integrations to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_agent_sdk import create_sdk_mcp_server, tool
from clickup_client import ClickUpClient


@tool(
    name="clickup_get_workspaces",
    description="Get all ClickUp workspaces/teams",
    input_schema={
        "type": "object",
        "properties": {}
    }
)
async def clickup_get_workspaces(args):
    """Get ClickUp workspaces."""
    try:
        client = ClickUpClient()
        workspaces = await client.get_workspaces()

        workspace_lines = [f"Found {len(workspaces)} workspaces:\n"]
        for workspace in workspaces:
            name = workspace.get("name", "Unnamed")
            workspace_id = workspace.get("id")
            workspace_lines.append(f"- {name} (ID: {workspace_id})")

        return {
            "content": [{
                "type": "text",
                "text": "\n".join(workspace_lines)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to get workspaces: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="clickup_get_lists",
    description="Get lists from a ClickUp space or folder",
    input_schema={
        "type": "object",
        "properties": {
            "space_id": {
                "type": "string",
                "description": "Space ID"
            },
            "folder_id": {
                "type": "string",
                "description": "Folder ID (alternative to space_id)"
            }
        }
    }
)
async def clickup_get_lists(args):
    """Get ClickUp lists."""
    try:
        client = ClickUpClient()

        space_id = args.get("space_id")
        folder_id = args.get("folder_id")

        lists = await client.get_lists(space_id=space_id, folder_id=folder_id)

        list_lines = [f"Found {len(lists)} lists:\n"]
        for lst in lists:
            name = lst.get("name", "Unnamed")
            list_id = lst.get("id")
            list_lines.append(f"- {name} (ID: {list_id})")

        return {
            "content": [{
                "type": "text",
                "text": "\n".join(list_lines)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to get lists: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="clickup_get_tasks",
    description="Get tasks from a ClickUp list",
    input_schema={
        "type": "object",
        "properties": {
            "list_id": {
                "type": "string",
                "description": "List ID"
            },
            "archived": {
                "type": "boolean",
                "description": "Include archived tasks",
                "default": False
            }
        },
        "required": ["list_id"]
    }
)
async def clickup_get_tasks(args):
    """Get ClickUp tasks."""
    try:
        client = ClickUpClient()

        list_id = args["list_id"]
        archived = args.get("archived", False)

        tasks = await client.get_tasks(list_id=list_id, archived=archived)

        task_lines = [f"Found {len(tasks)} tasks:\n"]
        for task in tasks[:50]:  # Limit to 50
            name = task.get("name", "Unnamed")
            task_id = task.get("id")
            status = task.get("status", {}).get("status", "unknown")
            task_lines.append(f"- [{status}] {name} (ID: {task_id})")

        return {
            "content": [{
                "type": "text",
                "text": "\n".join(task_lines)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to get tasks: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="clickup_create_task",
    description="Create a new task in ClickUp",
    input_schema={
        "type": "object",
        "properties": {
            "list_id": {
                "type": "string",
                "description": "List ID"
            },
            "name": {
                "type": "string",
                "description": "Task name"
            },
            "description": {
                "type": "string",
                "description": "Task description"
            },
            "priority": {
                "type": "number",
                "description": "Priority (1=urgent, 2=high, 3=normal, 4=low)"
            }
        },
        "required": ["list_id", "name"]
    }
)
async def clickup_create_task(args):
    """Create a ClickUp task."""
    try:
        client = ClickUpClient()

        task = await client.create_task(
            list_id=args["list_id"],
            name=args["name"],
            description=args.get("description"),
            priority=args.get("priority")
        )

        return {
            "content": [{
                "type": "text",
                "text": f"✓ Task created: {task.get('name', 'Unnamed')}\n"
                       f"Task ID: {task.get('id')}\n"
                       f"URL: {task.get('url', 'N/A')}"
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to create task: {str(e)}"
            }],
            "isError": True
        }


# Create and export the MCP server
clickup_mcp_server = create_sdk_mcp_server(
    name="clickup",
    version="1.0.0",
    tools=[
        clickup_get_workspaces,
        clickup_get_lists,
        clickup_get_tasks,
        clickup_create_task
    ]
)
