"""
Google Tasks MCP Server for Claude Agent SDK

Exposes Google Tasks operations as MCP tools that agents can use directly.
"""

import os
import sys
from pathlib import Path

# Add integrations to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_agent_sdk import create_sdk_mcp_server, tool
from google_tasks_client import GoogleTasksClient


@tool(
    name="tasks_list_tasks",
    description="List tasks from Google Tasks",
    input_schema={
        "type": "object",
        "properties": {
            "task_list_id": {
                "type": "string",
                "description": "Task list ID (leave empty for default/Inbox)"
            },
            "show_completed": {
                "type": "boolean",
                "description": "Show completed tasks",
                "default": False
            },
            "max_results": {
                "type": "number",
                "description": "Maximum number of tasks",
                "default": 100
            },
            "user_email": {
                "type": "string",
                "description": "Email to impersonate"
            }
        }
    }
)
async def tasks_list_tasks(args):
    """List Google Tasks."""
    try:
        user_email = args.get("user_email")
        client = GoogleTasksClient(user_email=user_email)

        task_list_id = args.get("task_list_id")
        show_completed = args.get("show_completed", False)
        max_results = args.get("max_results", 100)

        tasks = await client.list_tasks(
            task_list_id=task_list_id,
            show_completed=show_completed,
            max_results=max_results
        )

        task_lines = [f"Found {len(tasks)} tasks:\n"]
        for task in tasks[:50]:  # Limit display to 50
            title = task.get("title", "Untitled")
            status = task.get("status", "needsAction")
            status_icon = "✓" if status == "completed" else "○"
            task_lines.append(f"{status_icon} {title}")

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
                "text": f"✗ Failed to list tasks: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="tasks_create_task",
    description="Create a new task in Google Tasks",
    input_schema={
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Task title"
            },
            "notes": {
                "type": "string",
                "description": "Task notes/description"
            },
            "due": {
                "type": "string",
                "description": "Due date (RFC 3339 format, e.g., '2024-12-31T23:59:59Z')"
            },
            "task_list_id": {
                "type": "string",
                "description": "Task list ID (leave empty for default)"
            },
            "user_email": {
                "type": "string",
                "description": "Email to impersonate"
            }
        },
        "required": ["title"]
    }
)
async def tasks_create_task(args):
    """Create a Google Task."""
    try:
        user_email = args.get("user_email")
        client = GoogleTasksClient(user_email=user_email)

        task = await client.create_task(
            title=args["title"],
            task_list_id=args.get("task_list_id"),
            notes=args.get("notes"),
            due=args.get("due")
        )

        return {
            "content": [{
                "type": "text",
                "text": f"✓ Task created: {task.get('title', 'Untitled')}\n"
                       f"Task ID: {task.get('id')}"
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


@tool(
    name="tasks_complete_task",
    description="Mark a task as completed in Google Tasks",
    input_schema={
        "type": "object",
        "properties": {
            "task_list_id": {
                "type": "string",
                "description": "Task list ID"
            },
            "task_id": {
                "type": "string",
                "description": "Task ID"
            },
            "user_email": {
                "type": "string",
                "description": "Email to impersonate"
            }
        },
        "required": ["task_list_id", "task_id"]
    }
)
async def tasks_complete_task(args):
    """Complete a Google Task."""
    try:
        user_email = args.get("user_email")
        client = GoogleTasksClient(user_email=user_email)

        task = await client.complete_task(
            task_list_id=args["task_list_id"],
            task_id=args["task_id"]
        )

        return {
            "content": [{
                "type": "text",
                "text": f"✓ Task completed: {task.get('title', 'Untitled')}"
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to complete task: {str(e)}"
            }],
            "isError": True
        }


# Create and export the MCP server
google_tasks_mcp_server = create_sdk_mcp_server(
    name="google_tasks",
    version="1.0.0",
    tools=[
        tasks_list_tasks,
        tasks_create_task,
        tasks_complete_task
    ]
)
