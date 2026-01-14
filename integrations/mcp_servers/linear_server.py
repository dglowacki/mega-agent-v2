"""
Linear MCP Server for Claude Agent SDK

Exposes Linear GraphQL API operations as MCP tools that agents can use directly.
"""

import os
import sys
from pathlib import Path

# Add integrations to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_agent_sdk import create_sdk_mcp_server, tool
from linear_client import LinearClient


@tool(
    name="linear_get_teams",
    description="Get all teams in Linear organization",
    input_schema={
        "type": "object",
        "properties": {}
    }
)
async def linear_get_teams(args):
    """Get Linear teams."""
    try:
        client = LinearClient()
        teams = await client.get_teams()

        team_lines = [f"Found {len(teams)} teams:\n"]
        for team in teams:
            name = team.get("name", "Unnamed")
            key = team.get("key", "")
            issue_count = team.get("issueCount", 0)
            team_lines.append(f"- {name} ({key}) - {issue_count} issues")

        return {
            "content": [{
                "type": "text",
                "text": "\n".join(team_lines)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to get teams: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="linear_get_issues",
    description="Get issues from Linear with optional filters",
    input_schema={
        "type": "object",
        "properties": {
            "team_id": {
                "type": "string",
                "description": "Filter by team ID"
            },
            "state": {
                "type": "string",
                "description": "Filter by state name (e.g., 'In Progress', 'Done')"
            },
            "assignee_id": {
                "type": "string",
                "description": "Filter by assignee user ID"
            },
            "limit": {
                "type": "number",
                "description": "Maximum number of issues",
                "default": 50
            }
        }
    }
)
async def linear_get_issues(args):
    """Get Linear issues."""
    try:
        client = LinearClient()

        issues = await client.get_issues(
            team_id=args.get("team_id"),
            state=args.get("state"),
            assignee_id=args.get("assignee_id"),
            limit=args.get("limit", 50)
        )

        issue_lines = [f"Found {len(issues)} issues:\n"]
        for issue in issues[:50]:  # Limit display
            identifier = issue.get("identifier", "???")
            title = issue.get("title", "Untitled")
            state = issue.get("state", {}).get("name", "Unknown")
            issue_lines.append(f"- [{identifier}] {title} ({state})")

        return {
            "content": [{
                "type": "text",
                "text": "\n".join(issue_lines)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to get issues: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="linear_create_issue",
    description="Create a new issue in Linear",
    input_schema={
        "type": "object",
        "properties": {
            "team_id": {
                "type": "string",
                "description": "Team ID"
            },
            "title": {
                "type": "string",
                "description": "Issue title"
            },
            "description": {
                "type": "string",
                "description": "Issue description (markdown supported)"
            },
            "priority": {
                "type": "number",
                "description": "Priority (0=none, 1=urgent, 2=high, 3=normal, 4=low)"
            },
            "assignee_id": {
                "type": "string",
                "description": "User ID to assign"
            }
        },
        "required": ["team_id", "title"]
    }
)
async def linear_create_issue(args):
    """Create a Linear issue."""
    try:
        client = LinearClient()

        issue = await client.create_issue(
            team_id=args["team_id"],
            title=args["title"],
            description=args.get("description"),
            priority=args.get("priority"),
            assignee_id=args.get("assignee_id")
        )

        return {
            "content": [{
                "type": "text",
                "text": f"✓ Issue created: [{issue.get('identifier')}] {issue.get('title')}\n"
                       f"URL: {issue.get('url', 'N/A')}"
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to create issue: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="linear_update_issue",
    description="Update an existing Linear issue",
    input_schema={
        "type": "object",
        "properties": {
            "issue_id": {
                "type": "string",
                "description": "Issue ID or identifier (e.g., 'ABC-123')"
            },
            "title": {
                "type": "string",
                "description": "New title"
            },
            "description": {
                "type": "string",
                "description": "New description"
            },
            "state_id": {
                "type": "string",
                "description": "New state ID"
            },
            "priority": {
                "type": "number",
                "description": "New priority"
            }
        },
        "required": ["issue_id"]
    }
)
async def linear_update_issue(args):
    """Update a Linear issue."""
    try:
        client = LinearClient()

        issue = await client.update_issue(
            issue_id=args["issue_id"],
            title=args.get("title"),
            description=args.get("description"),
            state_id=args.get("state_id"),
            priority=args.get("priority")
        )

        return {
            "content": [{
                "type": "text",
                "text": f"✓ Issue updated: [{issue.get('identifier')}] {issue.get('title')}"
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to update issue: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="linear_search_issues",
    description="Search Linear issues by text",
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query"
            },
            "limit": {
                "type": "number",
                "description": "Maximum results",
                "default": 20
            }
        },
        "required": ["query"]
    }
)
async def linear_search_issues(args):
    """Search Linear issues."""
    try:
        client = LinearClient()

        issues = await client.search_issues(
            query_text=args["query"],
            limit=args.get("limit", 20)
        )

        issue_lines = [f"Found {len(issues)} matching issues:\n"]
        for issue in issues:
            identifier = issue.get("identifier", "???")
            title = issue.get("title", "Untitled")
            state = issue.get("state", {}).get("name", "Unknown")
            issue_lines.append(f"- [{identifier}] {title} ({state})")

        return {
            "content": [{
                "type": "text",
                "text": "\n".join(issue_lines)
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
linear_mcp_server = create_sdk_mcp_server(
    name="linear",
    version="1.0.0",
    tools=[
        linear_get_teams,
        linear_get_issues,
        linear_create_issue,
        linear_update_issue,
        linear_search_issues
    ]
)
