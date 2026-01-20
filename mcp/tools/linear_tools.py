"""
Linear Tools - Full Linear API integration.

Provides comprehensive Linear integration including:
- Issues: list, create, get, update, delete, search
- Projects: list, get, create
- Teams: list, get
- Cycles: list, get active, create
- Comments: add
- Labels: list, create
- Users: list, get viewer
- Workflow states: list
- Organization: get
"""

import sys
import asyncio
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


def _run_async(coro):
    """Run async coroutine from sync context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already in async context, create task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def linear_list_issues(
    team: str = None,
    status: str = None,
    assignee: str = None,
    limit: int = 20
) -> str:
    """List Linear issues with optional filters."""
    client = _get_linear()
    if not client:
        return "Error: Linear not configured"

    try:
        issues = _run_async(client.get_issues(
            team_id=team,
            state=status,
            assignee_id=assignee,
            limit=limit
        ))

        if not issues:
            return "No issues found"

        lines = [f"Linear Issues ({len(issues)}):"]
        for issue in issues[:limit]:
            state = issue.get('state', {}).get('name', 'Unknown')
            title = issue.get('title', 'No title')
            identifier = issue.get('identifier', '')
            assignee_name = issue.get('assignee', {}).get('name', 'Unassigned') if issue.get('assignee') else 'Unassigned'
            lines.append(f"  [{identifier}] {title} - {state} ({assignee_name})")

        return "\n".join(lines)
    except Exception as e:
        return f"Error listing issues: {str(e)}"


def linear_create_issue(
    title: str,
    team_id: str,
    description: str = "",
    priority: int = 3,
    assignee_id: str = None,
    label_ids: str = None,
    project_id: str = None,
    cycle_id: str = None,
    due_date: str = None,
    estimate: int = None,
    parent_id: str = None
) -> str:
    """Create a Linear issue with full options."""
    client = _get_linear()
    if not client:
        return "Error: Linear not configured"

    try:
        # Parse label_ids if provided as comma-separated string
        labels = label_ids.split(",") if label_ids else None

        issue = _run_async(client.create_issue(
            team_id=team_id,
            title=title,
            description=description or None,
            priority=priority,
            assignee_id=assignee_id,
            label_ids=labels,
            project_id=project_id,
            cycle_id=cycle_id,
            due_date=due_date,
            estimate=estimate,
            parent_id=parent_id
        ))

        if issue:
            identifier = issue.get('identifier', 'unknown')
            url = issue.get('url', '')
            return f"Created issue: {identifier} - {title}\nURL: {url}"
        return "Failed to create issue"
    except Exception as e:
        return f"Error creating issue: {str(e)}"


def linear_get_issue(identifier: str) -> str:
    """Get full details of a Linear issue including comments and sub-issues."""
    client = _get_linear()
    if not client:
        return "Error: Linear not configured"

    try:
        issue = _run_async(client.get_issue(identifier))

        if not issue:
            return f"Issue {identifier} not found"

        # Build comprehensive output
        lines = [
            f"# {issue.get('identifier')} - {issue.get('title')}",
            f"",
            f"**Status:** {issue.get('state', {}).get('name', 'Unknown')}",
            f"**Priority:** {issue.get('priorityLabel', 'None')}",
            f"**Team:** {issue.get('team', {}).get('name', 'Unknown')}",
        ]

        if issue.get('assignee'):
            lines.append(f"**Assignee:** {issue['assignee'].get('name', 'Unknown')}")
        else:
            lines.append("**Assignee:** Unassigned")

        if issue.get('project'):
            lines.append(f"**Project:** {issue['project'].get('name', '')}")

        if issue.get('cycle'):
            lines.append(f"**Cycle:** {issue['cycle'].get('name', '')} (#{issue['cycle'].get('number', '')})")

        if issue.get('dueDate'):
            lines.append(f"**Due Date:** {issue['dueDate']}")

        if issue.get('estimate'):
            lines.append(f"**Estimate:** {issue['estimate']} points")

        # Labels
        labels = issue.get('labels', {}).get('nodes', [])
        if labels:
            label_names = [l.get('name', '') for l in labels]
            lines.append(f"**Labels:** {', '.join(label_names)}")

        lines.append(f"**URL:** {issue.get('url', '')}")

        # Description
        lines.append(f"\n## Description\n{issue.get('description', 'No description')}")

        # Sub-issues
        children = issue.get('children', {}).get('nodes', [])
        if children:
            lines.append("\n## Sub-issues")
            for child in children:
                child_state = child.get('state', {}).get('name', '')
                lines.append(f"  - [{child.get('identifier')}] {child.get('title')} ({child_state})")

        # Parent issue
        if issue.get('parent'):
            parent = issue['parent']
            lines.append(f"\n**Parent:** [{parent.get('identifier')}] {parent.get('title')}")

        # Comments
        comments = issue.get('comments', {}).get('nodes', [])
        if comments:
            lines.append(f"\n## Comments ({len(comments)})")
            for comment in comments[:5]:  # Show last 5 comments
                user = comment.get('user', {}).get('name', 'Unknown')
                body = comment.get('body', '')[:200]
                lines.append(f"  **{user}:** {body}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error getting issue: {str(e)}"


def linear_update_issue(
    identifier: str,
    title: str = None,
    description: str = None,
    state_id: str = None,
    priority: int = None,
    assignee_id: str = None,
    label_ids: str = None,
    due_date: str = None,
    estimate: int = None,
    cycle_id: str = None
) -> str:
    """Update a Linear issue with full options."""
    client = _get_linear()
    if not client:
        return "Error: Linear not configured"

    try:
        # Parse label_ids if provided
        labels = label_ids.split(",") if label_ids else None

        result = _run_async(client.update_issue(
            issue_id=identifier,
            title=title,
            description=description,
            state_id=state_id,
            priority=priority,
            assignee_id=assignee_id,
            label_ids=labels,
            due_date=due_date,
            estimate=estimate,
            cycle_id=cycle_id
        ))

        if result:
            return f"Updated issue {identifier}\nURL: {result.get('url', '')}"
        return f"Failed to update issue {identifier}"
    except Exception as e:
        return f"Error updating issue: {str(e)}"


# =============================================================================
# Issue Operations (Additional)
# =============================================================================

def linear_delete_issue(identifier: str) -> str:
    """Delete (archive) a Linear issue."""
    client = _get_linear()
    if not client:
        return "Error: Linear not configured"

    try:
        result = _run_async(client.delete_issue(identifier))
        if result:
            return f"Deleted issue {identifier}"
        return f"Failed to delete issue {identifier}"
    except Exception as e:
        return f"Error deleting issue: {str(e)}"


def linear_search_issues(query: str, limit: int = 20) -> str:
    """Search Linear issues by text."""
    client = _get_linear()
    if not client:
        return "Error: Linear not configured"

    try:
        issues = _run_async(client.search_issues(query, limit=limit))

        if not issues:
            return f"No issues found matching '{query}'"

        lines = [f"Search Results for '{query}' ({len(issues)} found):"]
        for issue in issues:
            state = issue.get('state', {}).get('name', 'Unknown')
            team = issue.get('team', {}).get('key', '')
            lines.append(f"  [{issue.get('identifier')}] {issue.get('title')} - {state} ({team})")

        return "\n".join(lines)
    except Exception as e:
        return f"Error searching issues: {str(e)}"


# =============================================================================
# Comment Operations
# =============================================================================

def linear_add_comment(issue_id: str, body: str) -> str:
    """Add a comment to a Linear issue."""
    client = _get_linear()
    if not client:
        return "Error: Linear not configured"

    try:
        comment = _run_async(client.add_comment(issue_id, body))
        if comment:
            return f"Added comment to {issue_id}"
        return f"Failed to add comment to {issue_id}"
    except Exception as e:
        return f"Error adding comment: {str(e)}"


# =============================================================================
# Team Operations
# =============================================================================

def linear_list_teams() -> str:
    """List all Linear teams."""
    client = _get_linear()
    if not client:
        return "Error: Linear not configured"

    try:
        teams = _run_async(client.get_teams())

        if not teams:
            return "No teams found"

        lines = ["Linear Teams:"]
        for team in teams:
            key = team.get('key', '')
            name = team.get('name', '')
            issue_count = team.get('issueCount', 0)
            lines.append(f"  [{key}] {name} ({issue_count} issues)")

        return "\n".join(lines)
    except Exception as e:
        return f"Error listing teams: {str(e)}"


def linear_get_team(team_id: str) -> str:
    """Get details of a Linear team including workflow states and labels."""
    client = _get_linear()
    if not client:
        return "Error: Linear not configured"

    try:
        team = _run_async(client.get_team(team_id))

        if not team:
            return f"Team {team_id} not found"

        lines = [
            f"# Team: {team.get('name')} [{team.get('key')}]",
            f"**Issues:** {team.get('issueCount', 0)}",
        ]

        if team.get('description'):
            lines.append(f"**Description:** {team['description']}")

        # Workflow states
        states = team.get('states', {}).get('nodes', [])
        if states:
            lines.append("\n## Workflow States")
            for state in states:
                lines.append(f"  - {state.get('name')} ({state.get('type')}) - ID: {state.get('id')}")

        # Labels
        labels = team.get('labels', {}).get('nodes', [])
        if labels:
            lines.append("\n## Labels")
            for label in labels:
                lines.append(f"  - {label.get('name')} - ID: {label.get('id')}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error getting team: {str(e)}"


# =============================================================================
# Project Operations
# =============================================================================

def linear_list_projects(team_id: str = None, limit: int = 50) -> str:
    """List Linear projects, optionally filtered by team."""
    client = _get_linear()
    if not client:
        return "Error: Linear not configured"

    try:
        projects = _run_async(client.get_projects(team_id=team_id, limit=limit))

        if not projects:
            return "No projects found"

        lines = ["Linear Projects:"]
        for project in projects:
            name = project.get('name', '')
            state = project.get('state', '')
            progress = project.get('progress', 0)
            progress_pct = int(progress * 100) if progress else 0
            lines.append(f"  [{project.get('id')[:8]}] {name} - {state} ({progress_pct}%)")

        return "\n".join(lines)
    except Exception as e:
        return f"Error listing projects: {str(e)}"


def linear_get_project(project_id: str) -> str:
    """Get details of a Linear project including its issues."""
    client = _get_linear()
    if not client:
        return "Error: Linear not configured"

    try:
        project = _run_async(client.get_project(project_id))

        if not project:
            return f"Project {project_id} not found"

        lines = [
            f"# Project: {project.get('name')}",
            f"**State:** {project.get('state', 'Unknown')}",
            f"**Progress:** {int(project.get('progress', 0) * 100)}%",
        ]

        if project.get('description'):
            lines.append(f"**Description:** {project['description']}")

        if project.get('lead'):
            lines.append(f"**Lead:** {project['lead'].get('name', 'Unknown')}")

        if project.get('startDate'):
            lines.append(f"**Start Date:** {project['startDate']}")

        if project.get('targetDate'):
            lines.append(f"**Target Date:** {project['targetDate']}")

        lines.append(f"**URL:** {project.get('url', '')}")

        # Teams
        teams = project.get('teams', {}).get('nodes', [])
        if teams:
            team_names = [t.get('name', '') for t in teams]
            lines.append(f"**Teams:** {', '.join(team_names)}")

        # Issues
        issues = project.get('issues', {}).get('nodes', [])
        if issues:
            lines.append(f"\n## Issues ({len(issues)})")
            for issue in issues[:10]:  # Show first 10
                state = issue.get('state', {}).get('name', '')
                lines.append(f"  - [{issue.get('identifier')}] {issue.get('title')} ({state})")

        return "\n".join(lines)
    except Exception as e:
        return f"Error getting project: {str(e)}"


def linear_create_project(
    name: str,
    team_ids: str = None,
    description: str = None,
    lead_id: str = None,
    start_date: str = None,
    target_date: str = None
) -> str:
    """Create a new Linear project."""
    client = _get_linear()
    if not client:
        return "Error: Linear not configured"

    try:
        # Parse team_ids if provided as comma-separated
        teams = team_ids.split(",") if team_ids else None

        project = _run_async(client.create_project(
            name=name,
            description=description,
            team_ids=teams,
            lead_id=lead_id,
            start_date=start_date,
            target_date=target_date
        ))

        if project:
            return f"Created project: {project.get('name')}\nID: {project.get('id')}\nURL: {project.get('url', '')}"
        return "Failed to create project"
    except Exception as e:
        return f"Error creating project: {str(e)}"


# =============================================================================
# Cycle Operations
# =============================================================================

def linear_list_cycles(team_id: str, limit: int = 10) -> str:
    """List cycles for a Linear team."""
    client = _get_linear()
    if not client:
        return "Error: Linear not configured"

    try:
        cycles = _run_async(client.get_cycles(team_id, limit=limit))

        if not cycles:
            return f"No cycles found for team {team_id}"

        lines = [f"Cycles for team {team_id}:"]
        for cycle in cycles:
            name = cycle.get('name', f"Cycle {cycle.get('number', '')}")
            progress = int(cycle.get('progress', 0) * 100)
            start = cycle.get('startsAt', '')[:10] if cycle.get('startsAt') else ''
            end = cycle.get('endsAt', '')[:10] if cycle.get('endsAt') else ''
            lines.append(f"  [{cycle.get('id')[:8]}] {name} ({progress}%) - {start} to {end}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error listing cycles: {str(e)}"


def linear_get_active_cycle(team_id: str) -> str:
    """Get the current active cycle for a team."""
    client = _get_linear()
    if not client:
        return "Error: Linear not configured"

    try:
        cycle = _run_async(client.get_active_cycle(team_id))

        if not cycle:
            return f"No active cycle for team {team_id}"

        cycle_name = cycle.get('name') or f"Cycle {cycle.get('number', '')}"
        lines = [
            f"# Active Cycle: {cycle_name}",
            f"**Progress:** {int(cycle.get('progress', 0) * 100)}%",
            f"**Starts:** {cycle.get('startsAt', '')[:10] if cycle.get('startsAt') else 'N/A'}",
            f"**Ends:** {cycle.get('endsAt', '')[:10] if cycle.get('endsAt') else 'N/A'}",
        ]

        # Issues in cycle
        issues = cycle.get('issues', {}).get('nodes', [])
        if issues:
            lines.append(f"\n## Issues ({len(issues)})")
            for issue in issues:
                state = issue.get('state', {}).get('name', '')
                assignee = issue.get('assignee', {}).get('name', 'Unassigned') if issue.get('assignee') else 'Unassigned'
                lines.append(f"  - [{issue.get('identifier')}] {issue.get('title')} ({state}) - {assignee}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error getting active cycle: {str(e)}"


def linear_create_cycle(
    team_id: str,
    name: str,
    starts_at: str,
    ends_at: str
) -> str:
    """Create a new cycle for a team."""
    client = _get_linear()
    if not client:
        return "Error: Linear not configured"

    try:
        cycle = _run_async(client.create_cycle(team_id, name, starts_at, ends_at))

        if cycle:
            return f"Created cycle: {cycle.get('name')}\nID: {cycle.get('id')}"
        return "Failed to create cycle"
    except Exception as e:
        return f"Error creating cycle: {str(e)}"


# =============================================================================
# Label Operations
# =============================================================================

def linear_list_labels(team_id: str = None) -> str:
    """List Linear labels, optionally filtered by team."""
    client = _get_linear()
    if not client:
        return "Error: Linear not configured"

    try:
        labels = _run_async(client.get_labels(team_id=team_id))

        if not labels:
            return "No labels found"

        lines = ["Linear Labels:"]
        for label in labels:
            name = label.get('name', '')
            team_name = label.get('team', {}).get('name', 'Workspace') if label.get('team') else 'Workspace'
            lines.append(f"  [{label.get('id')[:8]}] {name} ({team_name})")

        return "\n".join(lines)
    except Exception as e:
        return f"Error listing labels: {str(e)}"


def linear_create_label(
    team_id: str,
    name: str,
    color: str = None,
    description: str = None
) -> str:
    """Create a new label for a team."""
    client = _get_linear()
    if not client:
        return "Error: Linear not configured"

    try:
        label = _run_async(client.create_label(team_id, name, color=color, description=description))

        if label:
            return f"Created label: {label.get('name')}\nID: {label.get('id')}"
        return "Failed to create label"
    except Exception as e:
        return f"Error creating label: {str(e)}"


# =============================================================================
# User Operations
# =============================================================================

def linear_list_users() -> str:
    """List all users in the Linear organization."""
    client = _get_linear()
    if not client:
        return "Error: Linear not configured"

    try:
        users = _run_async(client.get_users())

        if not users:
            return "No users found"

        lines = ["Linear Users:"]
        for user in users:
            name = user.get('name', '')
            email = user.get('email', '')
            active = "Active" if user.get('active', False) else "Inactive"
            admin = " (Admin)" if user.get('admin', False) else ""
            lines.append(f"  [{user.get('id')[:8]}] {name} <{email}> - {active}{admin}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error listing users: {str(e)}"


def linear_get_viewer() -> str:
    """Get the authenticated user's information and assigned issues."""
    client = _get_linear()
    if not client:
        return "Error: Linear not configured"

    try:
        viewer = _run_async(client.get_viewer())

        if not viewer:
            return "Could not get viewer information"

        lines = [
            f"# Current User: {viewer.get('name')}",
            f"**Email:** {viewer.get('email', '')}",
            f"**Display Name:** {viewer.get('displayName', '')}",
            f"**Admin:** {'Yes' if viewer.get('admin', False) else 'No'}",
        ]

        # Assigned issues
        issues = viewer.get('assignedIssues', {}).get('nodes', [])
        if issues:
            lines.append(f"\n## Assigned Issues ({len(issues)})")
            for issue in issues:
                state = issue.get('state', {}).get('name', '')
                lines.append(f"  - [{issue.get('identifier')}] {issue.get('title')} ({state})")

        return "\n".join(lines)
    except Exception as e:
        return f"Error getting viewer: {str(e)}"


# =============================================================================
# Workflow State Operations
# =============================================================================

def linear_get_workflow_states(team_id: str) -> str:
    """Get workflow states for a team (useful for setting issue status)."""
    client = _get_linear()
    if not client:
        return "Error: Linear not configured"

    try:
        states = _run_async(client.get_workflow_states(team_id))

        if not states:
            return f"No workflow states found for team {team_id}"

        lines = [f"Workflow States for team {team_id}:"]
        for state in states:
            state_type = state.get('type', 'unknown')
            lines.append(f"  [{state.get('id')}] {state.get('name')} ({state_type})")

        return "\n".join(lines)
    except Exception as e:
        return f"Error getting workflow states: {str(e)}"


# =============================================================================
# Organization Operations
# =============================================================================

def linear_get_organization() -> str:
    """Get Linear organization information."""
    client = _get_linear()
    if not client:
        return "Error: Linear not configured"

    try:
        org = _run_async(client.get_organization())

        if not org:
            return "Could not get organization information"

        lines = [
            f"# Organization: {org.get('name')}",
            f"**URL Key:** {org.get('urlKey', '')}",
            f"**Created:** {org.get('createdAt', '')[:10] if org.get('createdAt') else 'N/A'}",
        ]

        return "\n".join(lines)
    except Exception as e:
        return f"Error getting organization: {str(e)}"


def register_linear_tools(server) -> int:
    """Register all Linear tools (21 total)."""

    # ==========================================================================
    # Issue Operations (6 tools)
    # ==========================================================================

    server.register_tool(
        name="linear_list_issues",
        description="List Linear issues with filters for team, status, assignee.",
        input_schema={
            "type": "object",
            "properties": {
                "team": {"type": "string", "description": "Team ID to filter by"},
                "status": {"type": "string", "description": "Status name to filter by"},
                "assignee": {"type": "string", "description": "Assignee ID to filter by"},
                "limit": {"type": "integer", "description": "Max issues (default 20)", "default": 20}
            }
        },
        handler=linear_list_issues,
        requires_approval=False,
        category="linear"
    )

    server.register_tool(
        name="linear_create_issue",
        description="Create a Linear issue with full options (labels, project, cycle, due date, etc).",
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Issue title"},
                "team_id": {"type": "string", "description": "Team ID (required)"},
                "description": {"type": "string", "description": "Issue description (markdown)"},
                "priority": {"type": "integer", "description": "Priority: 1=Urgent, 2=High, 3=Normal, 4=Low", "default": 3},
                "assignee_id": {"type": "string", "description": "Assignee user ID"},
                "label_ids": {"type": "string", "description": "Comma-separated label IDs"},
                "project_id": {"type": "string", "description": "Project ID"},
                "cycle_id": {"type": "string", "description": "Cycle ID"},
                "due_date": {"type": "string", "description": "Due date (ISO format)"},
                "estimate": {"type": "integer", "description": "Point estimate"},
                "parent_id": {"type": "string", "description": "Parent issue ID for sub-issues"}
            },
            "required": ["title", "team_id"]
        },
        handler=linear_create_issue,
        requires_approval=True,
        category="linear"
    )

    server.register_tool(
        name="linear_get_issue",
        description="Get full details of a Linear issue including comments, sub-issues, and metadata.",
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
        description="Update a Linear issue (title, status, priority, assignee, labels, etc).",
        input_schema={
            "type": "object",
            "properties": {
                "identifier": {"type": "string", "description": "Issue identifier"},
                "title": {"type": "string", "description": "New title"},
                "description": {"type": "string", "description": "New description"},
                "state_id": {"type": "string", "description": "New state ID (use linear_get_workflow_states to find)"},
                "priority": {"type": "integer", "description": "New priority 1-4"},
                "assignee_id": {"type": "string", "description": "New assignee ID"},
                "label_ids": {"type": "string", "description": "Comma-separated label IDs (replaces existing)"},
                "due_date": {"type": "string", "description": "New due date (ISO format)"},
                "estimate": {"type": "integer", "description": "New estimate"},
                "cycle_id": {"type": "string", "description": "New cycle ID"}
            },
            "required": ["identifier"]
        },
        handler=linear_update_issue,
        requires_approval=True,
        category="linear"
    )

    server.register_tool(
        name="linear_delete_issue",
        description="Delete (archive) a Linear issue.",
        input_schema={
            "type": "object",
            "properties": {
                "identifier": {"type": "string", "description": "Issue identifier to delete"}
            },
            "required": ["identifier"]
        },
        handler=linear_delete_issue,
        requires_approval=True,
        category="linear"
    )

    server.register_tool(
        name="linear_search_issues",
        description="Search Linear issues by text query.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query text"},
                "limit": {"type": "integer", "description": "Max results (default 20)", "default": 20}
            },
            "required": ["query"]
        },
        handler=linear_search_issues,
        requires_approval=False,
        category="linear"
    )

    # ==========================================================================
    # Comment Operations (1 tool)
    # ==========================================================================

    server.register_tool(
        name="linear_add_comment",
        description="Add a comment to a Linear issue.",
        input_schema={
            "type": "object",
            "properties": {
                "issue_id": {"type": "string", "description": "Issue identifier"},
                "body": {"type": "string", "description": "Comment body (markdown supported)"}
            },
            "required": ["issue_id", "body"]
        },
        handler=linear_add_comment,
        requires_approval=True,
        category="linear"
    )

    # ==========================================================================
    # Team Operations (2 tools)
    # ==========================================================================

    server.register_tool(
        name="linear_list_teams",
        description="List all Linear teams in the organization.",
        input_schema={
            "type": "object",
            "properties": {}
        },
        handler=linear_list_teams,
        requires_approval=False,
        category="linear"
    )

    server.register_tool(
        name="linear_get_team",
        description="Get team details including workflow states and labels.",
        input_schema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Team ID"}
            },
            "required": ["team_id"]
        },
        handler=linear_get_team,
        requires_approval=False,
        category="linear"
    )

    # ==========================================================================
    # Project Operations (3 tools)
    # ==========================================================================

    server.register_tool(
        name="linear_list_projects",
        description="List Linear projects, optionally filtered by team.",
        input_schema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Team ID to filter by"},
                "limit": {"type": "integer", "description": "Max projects (default 50)", "default": 50}
            }
        },
        handler=linear_list_projects,
        requires_approval=False,
        category="linear"
    )

    server.register_tool(
        name="linear_get_project",
        description="Get project details including issues.",
        input_schema={
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID"}
            },
            "required": ["project_id"]
        },
        handler=linear_get_project,
        requires_approval=False,
        category="linear"
    )

    server.register_tool(
        name="linear_create_project",
        description="Create a new Linear project.",
        input_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Project name"},
                "team_ids": {"type": "string", "description": "Comma-separated team IDs"},
                "description": {"type": "string", "description": "Project description"},
                "lead_id": {"type": "string", "description": "Project lead user ID"},
                "start_date": {"type": "string", "description": "Start date (ISO format)"},
                "target_date": {"type": "string", "description": "Target date (ISO format)"}
            },
            "required": ["name"]
        },
        handler=linear_create_project,
        requires_approval=True,
        category="linear"
    )

    # ==========================================================================
    # Cycle Operations (3 tools)
    # ==========================================================================

    server.register_tool(
        name="linear_list_cycles",
        description="List cycles for a Linear team.",
        input_schema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Team ID"},
                "limit": {"type": "integer", "description": "Max cycles (default 10)", "default": 10}
            },
            "required": ["team_id"]
        },
        handler=linear_list_cycles,
        requires_approval=False,
        category="linear"
    )

    server.register_tool(
        name="linear_get_active_cycle",
        description="Get the current active cycle for a team with its issues.",
        input_schema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Team ID"}
            },
            "required": ["team_id"]
        },
        handler=linear_get_active_cycle,
        requires_approval=False,
        category="linear"
    )

    server.register_tool(
        name="linear_create_cycle",
        description="Create a new cycle for a team.",
        input_schema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Team ID"},
                "name": {"type": "string", "description": "Cycle name"},
                "starts_at": {"type": "string", "description": "Start datetime (ISO 8601 UTC)"},
                "ends_at": {"type": "string", "description": "End datetime (ISO 8601 UTC)"}
            },
            "required": ["team_id", "name", "starts_at", "ends_at"]
        },
        handler=linear_create_cycle,
        requires_approval=True,
        category="linear"
    )

    # ==========================================================================
    # Label Operations (2 tools)
    # ==========================================================================

    server.register_tool(
        name="linear_list_labels",
        description="List Linear labels, optionally filtered by team.",
        input_schema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Team ID to filter by (optional)"}
            }
        },
        handler=linear_list_labels,
        requires_approval=False,
        category="linear"
    )

    server.register_tool(
        name="linear_create_label",
        description="Create a new label for a team.",
        input_schema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Team ID"},
                "name": {"type": "string", "description": "Label name"},
                "color": {"type": "string", "description": "Hex color (e.g., #ff0000)"},
                "description": {"type": "string", "description": "Label description"}
            },
            "required": ["team_id", "name"]
        },
        handler=linear_create_label,
        requires_approval=True,
        category="linear"
    )

    # ==========================================================================
    # User Operations (2 tools)
    # ==========================================================================

    server.register_tool(
        name="linear_list_users",
        description="List all users in the Linear organization.",
        input_schema={
            "type": "object",
            "properties": {}
        },
        handler=linear_list_users,
        requires_approval=False,
        category="linear"
    )

    server.register_tool(
        name="linear_get_viewer",
        description="Get the authenticated user's info and assigned issues.",
        input_schema={
            "type": "object",
            "properties": {}
        },
        handler=linear_get_viewer,
        requires_approval=False,
        category="linear"
    )

    # ==========================================================================
    # Workflow & Organization Operations (2 tools)
    # ==========================================================================

    server.register_tool(
        name="linear_get_workflow_states",
        description="Get workflow states for a team (needed to update issue status).",
        input_schema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "Team ID"}
            },
            "required": ["team_id"]
        },
        handler=linear_get_workflow_states,
        requires_approval=False,
        category="linear"
    )

    server.register_tool(
        name="linear_get_organization",
        description="Get Linear organization information.",
        input_schema={
            "type": "object",
            "properties": {}
        },
        handler=linear_get_organization,
        requires_approval=False,
        category="linear"
    )

    return 21
