"""
Linear Tools - Issue and project management.

Provides Linear integration for the voice assistant.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "integrations"))

logger = logging.getLogger(__name__)

_linear_client = None


def _get_linear():
    """Get Linear client."""
    global _linear_client
    if _linear_client is None:
        try:
            from linear_client import LinearClient
            _linear_client = LinearClient()
        except Exception as e:
            logger.error(f"Failed to init Linear: {e}")
            return None
    return _linear_client


def linear_list_issues(
    team: str = None,
    status: str = None,
    limit: int = 20
) -> str:
    """List Linear issues."""
    client = _get_linear()
    if not client:
        return "Error: Linear not configured"

    try:
        issues = client.get_issues(team_key=team, limit=limit)

        lines = [f"Linear Issues ({len(issues)}):"]
        for issue in issues[:limit]:
            state = issue.get('state', {}).get('name', 'Unknown')
            title = issue.get('title', 'No title')
            identifier = issue.get('identifier', '')
            lines.append(f"  [{identifier}] {title} - {state}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error listing issues: {str(e)}"


def linear_create_issue(
    title: str,
    description: str = "",
    team: str = None,
    priority: int = 3
) -> str:
    """Create a Linear issue."""
    client = _get_linear()
    if not client:
        return "Error: Linear not configured"

    try:
        issue = client.create_issue(
            title=title,
            description=description,
            team_key=team,
            priority=priority
        )

        if issue:
            return f"Created issue: {issue.get('identifier', 'unknown')} - {title}"
        return "Failed to create issue"
    except Exception as e:
        return f"Error creating issue: {str(e)}"


def linear_get_issue(identifier: str) -> str:
    """Get details of a Linear issue."""
    client = _get_linear()
    if not client:
        return "Error: Linear not configured"

    try:
        issue = client.get_issue(identifier)

        if not issue:
            return f"Issue {identifier} not found"

        lines = [
            f"Issue: {issue.get('identifier')} - {issue.get('title')}",
            f"Status: {issue.get('state', {}).get('name', 'Unknown')}",
            f"Priority: {issue.get('priority', 'None')}",
            f"Assignee: {issue.get('assignee', {}).get('name', 'Unassigned')}",
            f"Description: {issue.get('description', 'No description')[:200]}"
        ]

        return "\n".join(lines)
    except Exception as e:
        return f"Error getting issue: {str(e)}"


def linear_update_issue(
    identifier: str,
    title: str = None,
    status: str = None,
    priority: int = None
) -> str:
    """Update a Linear issue."""
    client = _get_linear()
    if not client:
        return "Error: Linear not configured"

    try:
        updates = {}
        if title:
            updates['title'] = title
        if status:
            updates['state'] = status
        if priority:
            updates['priority'] = priority

        result = client.update_issue(identifier, **updates)

        if result:
            return f"Updated issue {identifier}"
        return f"Failed to update issue {identifier}"
    except Exception as e:
        return f"Error updating issue: {str(e)}"


def register_linear_tools(server) -> int:
    """Register Linear tools."""

    server.register_tool(
        name="linear_list_issues",
        description="List Linear issues, optionally filtered by team or status.",
        input_schema={
            "type": "object",
            "properties": {
                "team": {"type": "string", "description": "Team key to filter by"},
                "status": {"type": "string", "description": "Status to filter by"},
                "limit": {"type": "integer", "description": "Max issues", "default": 20}
            }
        },
        handler=linear_list_issues,
        requires_approval=False,
        category="linear"
    )

    server.register_tool(
        name="linear_create_issue",
        description="Create a new Linear issue.",
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Issue title"},
                "description": {"type": "string", "description": "Issue description"},
                "team": {"type": "string", "description": "Team key"},
                "priority": {"type": "integer", "description": "Priority 1-4", "default": 3}
            },
            "required": ["title"]
        },
        handler=linear_create_issue,
        requires_approval=True,
        category="linear"
    )

    server.register_tool(
        name="linear_get_issue",
        description="Get details of a Linear issue by identifier.",
        input_schema={
            "type": "object",
            "properties": {
                "identifier": {"type": "string", "description": "Issue identifier (e.g., PROJ-123)"}
            },
            "required": ["identifier"]
        },
        handler=linear_get_issue,
        requires_approval=False,
        category="linear"
    )

    server.register_tool(
        name="linear_update_issue",
        description="Update a Linear issue.",
        input_schema={
            "type": "object",
            "properties": {
                "identifier": {"type": "string", "description": "Issue identifier"},
                "title": {"type": "string", "description": "New title"},
                "status": {"type": "string", "description": "New status"},
                "priority": {"type": "integer", "description": "New priority 1-4"}
            },
            "required": ["identifier"]
        },
        handler=linear_update_issue,
        requires_approval=True,
        category="linear"
    )

    return 4
