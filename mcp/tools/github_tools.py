"""
GitHub Tools - PR, issue, and repository operations.

Uses the GitHub CLI (gh) for operations.
"""

import subprocess
import json
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


def _run_gh(args: list, repo: str = None) -> str:
    """
    Run a GitHub CLI command.

    Args:
        args: gh command arguments
        repo: Repository in owner/repo format

    Returns:
        Command output or error
    """
    cmd = ["gh"] + args

    if repo and "-R" not in args:
        cmd.extend(["-R", repo])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0 and result.stderr:
            return f"Error: {result.stderr.strip()}"

        return result.stdout.strip() if result.stdout.strip() else "[No output]"

    except subprocess.TimeoutExpired:
        return "Error: GitHub command timed out"
    except FileNotFoundError:
        return "Error: GitHub CLI (gh) not installed"
    except Exception as e:
        return f"Error running gh: {str(e)}"


def github_pr_list(
    repo: str = None,
    state: str = "open",
    limit: int = 10
) -> str:
    """
    List pull requests.

    Args:
        repo: Repository (owner/repo format)
        state: PR state (open, closed, merged, all)
        limit: Maximum PRs to return

    Returns:
        List of PRs
    """
    args = ["pr", "list", "--state", state, "--limit", str(limit)]
    return _run_gh(args, repo)


def github_pr_view(
    pr_number: int,
    repo: str = None
) -> str:
    """
    View pull request details.

    Args:
        pr_number: PR number
        repo: Repository (owner/repo format)

    Returns:
        PR details
    """
    args = ["pr", "view", str(pr_number)]
    return _run_gh(args, repo)


def github_pr_create(
    title: str,
    body: str,
    base: str = "main",
    head: str = None,
    draft: bool = False,
    repo: str = None
) -> str:
    """
    Create a pull request.

    Args:
        title: PR title
        body: PR description
        base: Base branch
        head: Head branch (current branch if not specified)
        draft: Create as draft PR
        repo: Repository (owner/repo format)

    Returns:
        Created PR URL
    """
    args = ["pr", "create", "--title", title, "--body", body, "--base", base]

    if head:
        args.extend(["--head", head])
    if draft:
        args.append("--draft")

    return _run_gh(args, repo)


def github_pr_merge(
    pr_number: int,
    method: str = "squash",
    delete_branch: bool = True,
    repo: str = None
) -> str:
    """
    Merge a pull request.

    Args:
        pr_number: PR number
        method: Merge method (merge, squash, rebase)
        delete_branch: Delete branch after merge
        repo: Repository (owner/repo format)

    Returns:
        Merge result
    """
    args = ["pr", "merge", str(pr_number), f"--{method}"]

    if delete_branch:
        args.append("--delete-branch")

    return _run_gh(args, repo)


def github_pr_checkout(
    pr_number: int,
    repo: str = None
) -> str:
    """
    Checkout a pull request locally.

    Args:
        pr_number: PR number
        repo: Repository (owner/repo format)

    Returns:
        Checkout result
    """
    args = ["pr", "checkout", str(pr_number)]
    return _run_gh(args, repo)


def github_pr_review(
    pr_number: int,
    action: str = "comment",
    body: str = None,
    repo: str = None
) -> str:
    """
    Review a pull request.

    Args:
        pr_number: PR number
        action: Review action (approve, request-changes, comment)
        body: Review comment
        repo: Repository (owner/repo format)

    Returns:
        Review result
    """
    args = ["pr", "review", str(pr_number), f"--{action}"]

    if body:
        args.extend(["--body", body])

    return _run_gh(args, repo)


def github_issue_list(
    repo: str = None,
    state: str = "open",
    limit: int = 10,
    labels: str = None
) -> str:
    """
    List issues.

    Args:
        repo: Repository (owner/repo format)
        state: Issue state (open, closed, all)
        limit: Maximum issues to return
        labels: Filter by labels (comma-separated)

    Returns:
        List of issues
    """
    args = ["issue", "list", "--state", state, "--limit", str(limit)]

    if labels:
        args.extend(["--label", labels])

    return _run_gh(args, repo)


def github_issue_view(
    issue_number: int,
    repo: str = None
) -> str:
    """
    View issue details.

    Args:
        issue_number: Issue number
        repo: Repository (owner/repo format)

    Returns:
        Issue details
    """
    args = ["issue", "view", str(issue_number)]
    return _run_gh(args, repo)


def github_issue_create(
    title: str,
    body: str,
    labels: str = None,
    assignees: str = None,
    repo: str = None
) -> str:
    """
    Create an issue.

    Args:
        title: Issue title
        body: Issue body
        labels: Labels (comma-separated)
        assignees: Assignees (comma-separated)
        repo: Repository (owner/repo format)

    Returns:
        Created issue URL
    """
    args = ["issue", "create", "--title", title, "--body", body]

    if labels:
        args.extend(["--label", labels])
    if assignees:
        args.extend(["--assignee", assignees])

    return _run_gh(args, repo)


def github_issue_comment(
    issue_number: int,
    body: str,
    repo: str = None
) -> str:
    """
    Add a comment to an issue.

    Args:
        issue_number: Issue number
        body: Comment body
        repo: Repository (owner/repo format)

    Returns:
        Comment result
    """
    args = ["issue", "comment", str(issue_number), "--body", body]
    return _run_gh(args, repo)


def github_repo_view(repo: str = None) -> str:
    """
    View repository details.

    Args:
        repo: Repository (owner/repo format)

    Returns:
        Repository details
    """
    args = ["repo", "view"]
    return _run_gh(args, repo)


def github_workflow_list(
    repo: str = None,
    limit: int = 10
) -> str:
    """
    List workflow runs.

    Args:
        repo: Repository (owner/repo format)
        limit: Maximum runs to return

    Returns:
        List of workflow runs
    """
    args = ["run", "list", "--limit", str(limit)]
    return _run_gh(args, repo)


def github_workflow_view(
    run_id: int,
    repo: str = None
) -> str:
    """
    View workflow run details.

    Args:
        run_id: Workflow run ID
        repo: Repository (owner/repo format)

    Returns:
        Run details
    """
    args = ["run", "view", str(run_id)]
    return _run_gh(args, repo)


def register_github_tools(server) -> int:
    """Register all GitHub tools with the MCP server."""

    server.register_tool(
        name="github_pr_list",
        description="List pull requests in a repository.",
        input_schema={
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository (owner/repo)"},
                "state": {"type": "string", "description": "PR state", "default": "open"},
                "limit": {"type": "integer", "description": "Max PRs to show", "default": 10}
            }
        },
        handler=github_pr_list,
        requires_approval=False,
        category="github"
    )

    server.register_tool(
        name="github_pr_view",
        description="View details of a specific pull request.",
        input_schema={
            "type": "object",
            "properties": {
                "pr_number": {"type": "integer", "description": "PR number"},
                "repo": {"type": "string", "description": "Repository (owner/repo)"}
            },
            "required": ["pr_number"]
        },
        handler=github_pr_view,
        requires_approval=False,
        category="github"
    )

    server.register_tool(
        name="github_pr_create",
        description="Create a new pull request.",
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "PR title"},
                "body": {"type": "string", "description": "PR description"},
                "base": {"type": "string", "description": "Base branch", "default": "main"},
                "head": {"type": "string", "description": "Head branch"},
                "draft": {"type": "boolean", "description": "Create as draft", "default": False},
                "repo": {"type": "string", "description": "Repository (owner/repo)"}
            },
            "required": ["title", "body"]
        },
        handler=github_pr_create,
        requires_approval=True,
        category="github"
    )

    server.register_tool(
        name="github_pr_merge",
        description="Merge a pull request.",
        input_schema={
            "type": "object",
            "properties": {
                "pr_number": {"type": "integer", "description": "PR number"},
                "method": {"type": "string", "description": "Merge method", "default": "squash"},
                "delete_branch": {"type": "boolean", "description": "Delete branch after", "default": True},
                "repo": {"type": "string", "description": "Repository (owner/repo)"}
            },
            "required": ["pr_number"]
        },
        handler=github_pr_merge,
        requires_approval=True,
        category="github"
    )

    server.register_tool(
        name="github_pr_checkout",
        description="Checkout a pull request locally for testing.",
        input_schema={
            "type": "object",
            "properties": {
                "pr_number": {"type": "integer", "description": "PR number"},
                "repo": {"type": "string", "description": "Repository (owner/repo)"}
            },
            "required": ["pr_number"]
        },
        handler=github_pr_checkout,
        requires_approval=True,
        category="github"
    )

    server.register_tool(
        name="github_pr_review",
        description="Add a review to a pull request (approve, request changes, or comment).",
        input_schema={
            "type": "object",
            "properties": {
                "pr_number": {"type": "integer", "description": "PR number"},
                "action": {"type": "string", "description": "Review action", "default": "comment"},
                "body": {"type": "string", "description": "Review comment"},
                "repo": {"type": "string", "description": "Repository (owner/repo)"}
            },
            "required": ["pr_number"]
        },
        handler=github_pr_review,
        requires_approval=True,
        category="github"
    )

    server.register_tool(
        name="github_issue_list",
        description="List issues in a repository.",
        input_schema={
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository (owner/repo)"},
                "state": {"type": "string", "description": "Issue state", "default": "open"},
                "limit": {"type": "integer", "description": "Max issues", "default": 10},
                "labels": {"type": "string", "description": "Filter by labels"}
            }
        },
        handler=github_issue_list,
        requires_approval=False,
        category="github"
    )

    server.register_tool(
        name="github_issue_view",
        description="View details of a specific issue.",
        input_schema={
            "type": "object",
            "properties": {
                "issue_number": {"type": "integer", "description": "Issue number"},
                "repo": {"type": "string", "description": "Repository (owner/repo)"}
            },
            "required": ["issue_number"]
        },
        handler=github_issue_view,
        requires_approval=False,
        category="github"
    )

    server.register_tool(
        name="github_issue_create",
        description="Create a new issue.",
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Issue title"},
                "body": {"type": "string", "description": "Issue body"},
                "labels": {"type": "string", "description": "Labels (comma-separated)"},
                "assignees": {"type": "string", "description": "Assignees (comma-separated)"},
                "repo": {"type": "string", "description": "Repository (owner/repo)"}
            },
            "required": ["title", "body"]
        },
        handler=github_issue_create,
        requires_approval=True,
        category="github"
    )

    server.register_tool(
        name="github_issue_comment",
        description="Add a comment to an issue.",
        input_schema={
            "type": "object",
            "properties": {
                "issue_number": {"type": "integer", "description": "Issue number"},
                "body": {"type": "string", "description": "Comment body"},
                "repo": {"type": "string", "description": "Repository (owner/repo)"}
            },
            "required": ["issue_number", "body"]
        },
        handler=github_issue_comment,
        requires_approval=True,
        category="github"
    )

    server.register_tool(
        name="github_repo_view",
        description="View repository information.",
        input_schema={
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository (owner/repo)"}
            }
        },
        handler=github_repo_view,
        requires_approval=False,
        category="github"
    )

    server.register_tool(
        name="github_workflow_list",
        description="List recent workflow runs.",
        input_schema={
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository (owner/repo)"},
                "limit": {"type": "integer", "description": "Max runs", "default": 10}
            }
        },
        handler=github_workflow_list,
        requires_approval=False,
        category="github"
    )

    server.register_tool(
        name="github_workflow_view",
        description="View details of a workflow run.",
        input_schema={
            "type": "object",
            "properties": {
                "run_id": {"type": "integer", "description": "Workflow run ID"},
                "repo": {"type": "string", "description": "Repository (owner/repo)"}
            },
            "required": ["run_id"]
        },
        handler=github_workflow_view,
        requires_approval=False,
        category="github"
    )

    return 14  # Number of tools registered
