"""
ClickUp Tools - Task and project management.

Provides ClickUp integration for the voice assistant.
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "integrations"))

logger = logging.getLogger(__name__)

_clickup_client = None


def _get_clickup():
    """Get ClickUp client."""
    global _clickup_client
    if _clickup_client is None:
        try:
            from clickup_client import ClickUpClient
            _clickup_client = ClickUpClient()
        except Exception as e:
            logger.error(f"Failed to init ClickUp: {e}")
            return None
    return _clickup_client


def clickup_list_tasks(
    list_id: str = None,
    status: str = None,
    limit: int = 20
) -> str:
    """List ClickUp tasks."""
    client = _get_clickup()
    if not client:
        return "Error: ClickUp not configured"

    try:
        tasks = client.get_tasks(list_id=list_id, limit=limit)

        lines = [f"ClickUp Tasks ({len(tasks)}):"]
        for task in tasks[:limit]:
            status_name = task.get('status', {}).get('status', 'Unknown')
            name = task.get('name', 'No name')
            task_id = task.get('id', '')
            lines.append(f"  [{task_id}] {name} - {status_name}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error listing tasks: {str(e)}"


def clickup_create_task(
    name: str,
    list_id: str,
    description: str = "",
    priority: int = 3
) -> str:
    """Create a ClickUp task."""
    client = _get_clickup()
    if not client:
        return "Error: ClickUp not configured"

    try:
        task = client.create_task(
            list_id=list_id,
            name=name,
            description=description,
            priority=priority
        )

        if task:
            return f"Created task: {task.get('id', 'unknown')} - {name}"
        return "Failed to create task"
    except Exception as e:
        return f"Error creating task: {str(e)}"


def clickup_get_task(task_id: str) -> str:
    """Get details of a ClickUp task."""
    client = _get_clickup()
    if not client:
        return "Error: ClickUp not configured"

    try:
        task = client.get_task(task_id)

        if not task:
            return f"Task {task_id} not found"

        lines = [
            f"Task: {task.get('name')}",
            f"Status: {task.get('status', {}).get('status', 'Unknown')}",
            f"Priority: {task.get('priority', {}).get('priority', 'None')}",
            f"Assignees: {', '.join([a.get('username', '') for a in task.get('assignees', [])])}",
            f"Description: {task.get('description', 'No description')[:200]}"
        ]

        return "\n".join(lines)
    except Exception as e:
        return f"Error getting task: {str(e)}"


def clickup_list_spaces() -> str:
    """List ClickUp spaces."""
    client = _get_clickup()
    if not client:
        return "Error: ClickUp not configured"

    try:
        spaces = client.get_spaces()

        lines = ["ClickUp Spaces:"]
        for space in spaces:
            lines.append(f"  - {space.get('name')} (ID: {space.get('id')})")

        return "\n".join(lines)
    except Exception as e:
        return f"Error listing spaces: {str(e)}"


def register_clickup_tools(server) -> int:
    """Register ClickUp tools."""

    server.register_tool(
        name="clickup_list_tasks",
        description="List ClickUp tasks, optionally filtered by list or status.",
        input_schema={
            "type": "object",
            "properties": {
                "list_id": {"type": "string", "description": "List ID to filter by"},
                "status": {"type": "string", "description": "Status to filter by"},
                "limit": {"type": "integer", "description": "Max tasks", "default": 20}
            }
        },
        handler=clickup_list_tasks,
        requires_approval=False,
        category="clickup"
    )

    server.register_tool(
        name="clickup_create_task",
        description="Create a new ClickUp task.",
        input_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Task name"},
                "list_id": {"type": "string", "description": "List ID to create in"},
                "description": {"type": "string", "description": "Task description"},
                "priority": {"type": "integer", "description": "Priority 1-4", "default": 3}
            },
            "required": ["name", "list_id"]
        },
        handler=clickup_create_task,
        requires_approval=True,
        category="clickup"
    )

    server.register_tool(
        name="clickup_get_task",
        description="Get details of a ClickUp task.",
        input_schema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID"}
            },
            "required": ["task_id"]
        },
        handler=clickup_get_task,
        requires_approval=False,
        category="clickup"
    )

    server.register_tool(
        name="clickup_list_spaces",
        description="List all ClickUp spaces.",
        input_schema={
            "type": "object",
            "properties": {}
        },
        handler=clickup_list_spaces,
        requires_approval=False,
        category="clickup"
    )

    return 4
