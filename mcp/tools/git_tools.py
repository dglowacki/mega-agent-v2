"""
Git Tools - Version control operations.

Provides git operations for the voice assistant.
"""

import subprocess
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default repository path
DEFAULT_REPO = Path("/home/ec2-user/mega-agent2")


def _run_git(args: list, repo_path: Path = None) -> str:
    """
    Run a git command.

    Args:
        args: Git command arguments
        repo_path: Repository path

    Returns:
        Command output or error
    """
    cwd = repo_path or DEFAULT_REPO

    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=60
        )

        output = result.stdout
        if result.stderr and result.returncode != 0:
            output += f"\n[stderr] {result.stderr}"

        return output.strip() if output.strip() else "[No output]"

    except subprocess.TimeoutExpired:
        return "Error: Git command timed out"
    except Exception as e:
        return f"Error running git: {str(e)}"


def git_status(repo_path: str = None) -> str:
    """
    Get git status of the repository.

    Args:
        repo_path: Path to git repository

    Returns:
        Git status output
    """
    path = Path(repo_path) if repo_path else DEFAULT_REPO
    return _run_git(["status"], path)


def git_diff(
    staged: bool = False,
    file_path: str = None,
    repo_path: str = None
) -> str:
    """
    Show git diff.

    Args:
        staged: Show staged changes only
        file_path: Specific file to diff
        repo_path: Path to git repository

    Returns:
        Diff output
    """
    path = Path(repo_path) if repo_path else DEFAULT_REPO

    args = ["diff"]
    if staged:
        args.append("--staged")
    if file_path:
        args.extend(["--", file_path])

    output = _run_git(args, path)

    # Truncate very long diffs
    if len(output) > 10000:
        output = output[:10000] + "\n\n... (diff truncated)"

    return output


def git_log(
    count: int = 10,
    oneline: bool = True,
    file_path: str = None,
    repo_path: str = None
) -> str:
    """
    Show git log.

    Args:
        count: Number of commits to show
        oneline: Use oneline format
        file_path: Show log for specific file
        repo_path: Path to git repository

    Returns:
        Git log output
    """
    path = Path(repo_path) if repo_path else DEFAULT_REPO

    args = ["log", f"-{min(count, 50)}"]
    if oneline:
        args.append("--oneline")
    if file_path:
        args.extend(["--", file_path])

    return _run_git(args, path)


def git_branch(
    list_all: bool = False,
    repo_path: str = None
) -> str:
    """
    List git branches.

    Args:
        list_all: Include remote branches
        repo_path: Path to git repository

    Returns:
        Branch list
    """
    path = Path(repo_path) if repo_path else DEFAULT_REPO

    args = ["branch"]
    if list_all:
        args.append("-a")

    return _run_git(args, path)


def git_checkout(
    branch: str,
    create: bool = False,
    repo_path: str = None
) -> str:
    """
    Checkout a branch.

    Args:
        branch: Branch name
        create: Create new branch
        repo_path: Path to git repository

    Returns:
        Checkout result
    """
    path = Path(repo_path) if repo_path else DEFAULT_REPO

    args = ["checkout"]
    if create:
        args.append("-b")
    args.append(branch)

    return _run_git(args, path)


def git_add(
    files: str = ".",
    repo_path: str = None
) -> str:
    """
    Stage files for commit.

    Args:
        files: Files to add (default: all)
        repo_path: Path to git repository

    Returns:
        Add result
    """
    path = Path(repo_path) if repo_path else DEFAULT_REPO
    return _run_git(["add", files], path)


def git_commit(
    message: str,
    repo_path: str = None
) -> str:
    """
    Create a git commit.

    Args:
        message: Commit message
        repo_path: Path to git repository

    Returns:
        Commit result
    """
    path = Path(repo_path) if repo_path else DEFAULT_REPO

    # Add co-author
    full_message = f"{message}\n\nCo-Authored-By: Voice Assistant <voice@assistant.local>"

    return _run_git(["commit", "-m", full_message], path)


def git_push(
    remote: str = "origin",
    branch: str = None,
    set_upstream: bool = False,
    repo_path: str = None
) -> str:
    """
    Push to remote repository.

    Args:
        remote: Remote name
        branch: Branch to push
        set_upstream: Set upstream tracking
        repo_path: Path to git repository

    Returns:
        Push result
    """
    path = Path(repo_path) if repo_path else DEFAULT_REPO

    args = ["push"]
    if set_upstream:
        args.append("-u")
    args.append(remote)
    if branch:
        args.append(branch)

    return _run_git(args, path)


def git_pull(
    remote: str = "origin",
    branch: str = None,
    repo_path: str = None
) -> str:
    """
    Pull from remote repository.

    Args:
        remote: Remote name
        branch: Branch to pull
        repo_path: Path to git repository

    Returns:
        Pull result
    """
    path = Path(repo_path) if repo_path else DEFAULT_REPO

    args = ["pull", remote]
    if branch:
        args.append(branch)

    return _run_git(args, path)


def git_stash(
    action: str = "push",
    message: str = None,
    repo_path: str = None
) -> str:
    """
    Git stash operations.

    Args:
        action: push, pop, list, drop
        message: Stash message (for push)
        repo_path: Path to git repository

    Returns:
        Stash result
    """
    path = Path(repo_path) if repo_path else DEFAULT_REPO

    args = ["stash", action]
    if action == "push" and message:
        args.extend(["-m", message])

    return _run_git(args, path)


def git_reset(
    mode: str = "mixed",
    ref: str = "HEAD",
    repo_path: str = None
) -> str:
    """
    Reset git state.

    Args:
        mode: soft, mixed, or hard
        ref: Reference to reset to
        repo_path: Path to git repository

    Returns:
        Reset result
    """
    path = Path(repo_path) if repo_path else DEFAULT_REPO

    if mode not in ["soft", "mixed", "hard"]:
        return f"Error: Invalid mode '{mode}'. Use soft, mixed, or hard."

    return _run_git(["reset", f"--{mode}", ref], path)


def register_git_tools(server) -> int:
    """Register all git tools with the MCP server."""

    server.register_tool(
        name="git_status",
        description="Show the working tree status - modified, staged, and untracked files.",
        input_schema={
            "type": "object",
            "properties": {
                "repo_path": {"type": "string", "description": "Path to git repository"}
            }
        },
        handler=git_status,
        requires_approval=False,
        category="git"
    )

    server.register_tool(
        name="git_diff",
        description="Show changes between commits, commit and working tree, etc.",
        input_schema={
            "type": "object",
            "properties": {
                "staged": {"type": "boolean", "description": "Show only staged changes", "default": False},
                "file_path": {"type": "string", "description": "Specific file to diff"},
                "repo_path": {"type": "string", "description": "Path to git repository"}
            }
        },
        handler=git_diff,
        requires_approval=False,
        category="git"
    )

    server.register_tool(
        name="git_log",
        description="Show commit history.",
        input_schema={
            "type": "object",
            "properties": {
                "count": {"type": "integer", "description": "Number of commits", "default": 10},
                "oneline": {"type": "boolean", "description": "Compact format", "default": True},
                "file_path": {"type": "string", "description": "Filter by file"},
                "repo_path": {"type": "string", "description": "Path to git repository"}
            }
        },
        handler=git_log,
        requires_approval=False,
        category="git"
    )

    server.register_tool(
        name="git_branch",
        description="List, create, or delete branches.",
        input_schema={
            "type": "object",
            "properties": {
                "list_all": {"type": "boolean", "description": "Include remote branches", "default": False},
                "repo_path": {"type": "string", "description": "Path to git repository"}
            }
        },
        handler=git_branch,
        requires_approval=False,
        category="git"
    )

    server.register_tool(
        name="git_checkout",
        description="Switch branches or create new branches.",
        input_schema={
            "type": "object",
            "properties": {
                "branch": {"type": "string", "description": "Branch name"},
                "create": {"type": "boolean", "description": "Create new branch", "default": False},
                "repo_path": {"type": "string", "description": "Path to git repository"}
            },
            "required": ["branch"]
        },
        handler=git_checkout,
        requires_approval=True,
        category="git"
    )

    server.register_tool(
        name="git_add",
        description="Stage files for commit.",
        input_schema={
            "type": "object",
            "properties": {
                "files": {"type": "string", "description": "Files to stage (default: all)", "default": "."},
                "repo_path": {"type": "string", "description": "Path to git repository"}
            }
        },
        handler=git_add,
        requires_approval=True,
        category="git"
    )

    server.register_tool(
        name="git_commit",
        description="Create a new commit with staged changes.",
        input_schema={
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Commit message"},
                "repo_path": {"type": "string", "description": "Path to git repository"}
            },
            "required": ["message"]
        },
        handler=git_commit,
        requires_approval=True,
        category="git"
    )

    server.register_tool(
        name="git_push",
        description="Push commits to remote repository.",
        input_schema={
            "type": "object",
            "properties": {
                "remote": {"type": "string", "description": "Remote name", "default": "origin"},
                "branch": {"type": "string", "description": "Branch to push"},
                "set_upstream": {"type": "boolean", "description": "Set upstream tracking", "default": False},
                "repo_path": {"type": "string", "description": "Path to git repository"}
            }
        },
        handler=git_push,
        requires_approval=True,
        category="git"
    )

    server.register_tool(
        name="git_pull",
        description="Pull changes from remote repository.",
        input_schema={
            "type": "object",
            "properties": {
                "remote": {"type": "string", "description": "Remote name", "default": "origin"},
                "branch": {"type": "string", "description": "Branch to pull"},
                "repo_path": {"type": "string", "description": "Path to git repository"}
            }
        },
        handler=git_pull,
        requires_approval=True,
        category="git"
    )

    server.register_tool(
        name="git_stash",
        description="Stash changes for later. Actions: push, pop, list, drop.",
        input_schema={
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "Stash action", "default": "push"},
                "message": {"type": "string", "description": "Stash message"},
                "repo_path": {"type": "string", "description": "Path to git repository"}
            }
        },
        handler=git_stash,
        requires_approval=True,
        category="git"
    )

    server.register_tool(
        name="git_reset",
        description="Reset current HEAD to specified state. Modes: soft, mixed, hard.",
        input_schema={
            "type": "object",
            "properties": {
                "mode": {"type": "string", "description": "Reset mode (soft/mixed/hard)", "default": "mixed"},
                "ref": {"type": "string", "description": "Reference to reset to", "default": "HEAD"},
                "repo_path": {"type": "string", "description": "Path to git repository"}
            }
        },
        handler=git_reset,
        requires_approval=True,
        category="git"
    )

    return 11  # Number of tools registered
