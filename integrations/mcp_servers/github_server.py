"""
GitHub MCP Server for Claude Agent SDK

Exposes GitHub operations as MCP tools that agents can use directly.
"""

import os
import json
from datetime import datetime, timedelta

from claude_agent_sdk import create_sdk_mcp_server, tool

try:
    from github import Github, GithubException
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False


def get_github_client():
    """Get authenticated GitHub client."""
    if not GITHUB_AVAILABLE:
        raise Exception("PyGithub not installed. Run: pip install PyGithub")

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise Exception("GITHUB_TOKEN environment variable not set")

    return Github(token)


@tool(
    name="get_commits",
    description="Get recent commits from a GitHub repository",
    input_schema={
        "type": "object",
        "properties": {
            "repo": {
                "type": "string",
                "description": "Repository in format 'owner/repo' (e.g., 'anthropics/claude-code')"
            },
            "days": {
                "type": "number",
                "description": "Number of days to look back",
                "default": 1
            },
            "branch": {
                "type": "string",
                "description": "Branch name (default: main/master)",
                "default": "main"
            }
        },
        "required": ["repo"]
    }
)
def get_commits(args):
    """Get recent commits from repository."""
    try:
        gh = get_github_client()
        repo = gh.get_repo(args["repo"])
        days = args.get("days", 1)
        branch = args.get("branch", "main")

        # Calculate cutoff date
        since = datetime.now() - timedelta(days=days)

        # Get commits
        try:
            commits = repo.get_commits(sha=branch, since=since)
        except:
            # Try 'master' if 'main' fails
            commits = repo.get_commits(sha="master", since=since)

        # Format commit data
        commit_list = []
        for commit in commits:
            commit_data = {
                "sha": commit.sha,
                "author": commit.commit.author.name,
                "email": commit.commit.author.email,
                "date": commit.commit.author.date.isoformat(),
                "message": commit.commit.message,
                "additions": commit.stats.additions,
                "deletions": commit.stats.deletions,
                "files_count": len(commit.files),
                "files_changed": [f.filename for f in commit.files[:10]]  # Limit to 10
            }
            commit_list.append(commit_data)

        return {
            "content": [{
                "type": "text",
                "text": f"✓ Retrieved {len(commit_list)} commits from {args['repo']}\n"
                       f"Branch: {branch}\n"
                       f"Period: Last {days} day(s)\n\n"
                       f"Commit data:\n{json.dumps(commit_list, indent=2)}"
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to get commits: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="list_repositories",
    description="List GitHub repositories for the authenticated user",
    input_schema={
        "type": "object",
        "properties": {
            "limit": {
                "type": "number",
                "description": "Maximum number of repos to return",
                "default": 50
            }
        }
    }
)
def list_repositories(args):
    """List user's repositories."""
    try:
        gh = get_github_client()
        user = gh.get_user()

        repos = []
        for repo in user.get_repos()[:args.get("limit", 50)]:
            repos.append({
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "private": repo.private,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None
            })

        return {
            "content": [{
                "type": "text",
                "text": f"✓ Found {len(repos)} repositories:\n\n" +
                       "\n".join([f"- {r['full_name']}: {r['description'] or 'No description'}"
                                 for r in repos[:20]])
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to list repositories: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="create_issue",
    description="Create a GitHub issue",
    input_schema={
        "type": "object",
        "properties": {
            "repo": {
                "type": "string",
                "description": "Repository in format 'owner/repo'"
            },
            "title": {
                "type": "string",
                "description": "Issue title"
            },
            "body": {
                "type": "string",
                "description": "Issue body/description"
            },
            "labels": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of label names"
            }
        },
        "required": ["repo", "title", "body"]
    }
)
def create_issue(args):
    """Create GitHub issue."""
    try:
        gh = get_github_client()
        repo = gh.get_repo(args["repo"])

        issue = repo.create_issue(
            title=args["title"],
            body=args["body"],
            labels=args.get("labels", [])
        )

        return {
            "content": [{
                "type": "text",
                "text": f"✓ Created issue #{issue.number} in {args['repo']}\n"
                       f"Title: {args['title']}\n"
                       f"URL: {issue.html_url}"
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


# Create and export the MCP server
github_mcp_server = create_sdk_mcp_server(
    name="github",
    version="1.0.0",
    tools=[get_commits, list_repositories, create_issue]
)
