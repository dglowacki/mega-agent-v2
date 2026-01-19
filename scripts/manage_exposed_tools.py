#!/usr/bin/env python3
"""
Manage exposed MCP tools.

Usage:
    ./manage_exposed_tools.py list              # List currently exposed tools
    ./manage_exposed_tools.py all               # List ALL registered tools
    ./manage_exposed_tools.py add <tool>        # Add a tool to exposed list
    ./manage_exposed_tools.py remove <tool>     # Remove a tool from exposed list
    ./manage_exposed_tools.py expose-all        # Expose all tools (delete config)
    ./manage_exposed_tools.py search <query>    # Search registered tools

Config file: data/exposed_tools.json
- If file exists with tools array: only those tools are exposed
- If file missing or tools=null: all tools are exposed
"""

import json
import sys
from pathlib import Path

CONFIG_FILE = Path(__file__).parent.parent / "data" / "exposed_tools.json"

# All registered tools (update when adding new tools)
ALL_TOOLS = [
    # Voice basics
    "get_time", "get_weather", "list_capabilities",

    # App Store
    "appstore_list_apps", "appstore_get_sales", "appstore_get_downloads", "appstore_get_ratings",

    # Files
    "file_read", "file_write", "file_edit", "file_list", "file_grep", "file_glob", "file_delete",

    # Bash
    "bash_execute", "bash_background", "bash_check_process", "bash_kill_process", "bash_list_processes",

    # Git
    "git_status", "git_diff", "git_log", "git_commit", "git_push", "git_pull",
    "git_branch", "git_checkout", "git_add", "git_stash", "git_reset",

    # GitHub
    "github_pr_list", "github_pr_view", "github_pr_create", "github_pr_merge", "github_pr_checkout", "github_pr_review",
    "github_issue_list", "github_issue_view", "github_issue_create", "github_issue_comment",
    "github_repo_view", "github_workflow_list", "github_workflow_view",

    # Web
    "web_search", "web_fetch", "web_api_call",

    # AWS
    "aws_lambda_list", "aws_lambda_invoke", "aws_lambda_logs",
    "aws_s3_list", "aws_s3_get", "aws_s3_put",
    "aws_dynamodb_list_tables", "aws_dynamodb_scan", "aws_dynamodb_query",
    "aws_cost_get_usage", "aws_cost_get_forecast",

    # Slack
    "slack_get_unread", "slack_get_mentions", "slack_get_messages",
    "slack_send_dm", "slack_send_channel", "slack_send_image",
    "slack_list_channels", "slack_list_users", "slack_search",

    # Gmail
    "gmail_list_messages", "gmail_search", "gmail_send",

    # Calendar
    "gcal_list_events", "gcal_create_event", "gcal_search_events",
    "calendar_list", "calendar_add", "calendar_search", "calendar_delete",

    # Google Tasks
    "gtasks_list_tasks", "gtasks_create_task", "gtasks_complete_task",

    # Linear
    "linear_list_issues", "linear_create_issue", "linear_get_issue", "linear_update_issue",

    # ClickUp
    "clickup_list_tasks", "clickup_create_task", "clickup_get_task", "clickup_list_spaces",

    # Email/Comms
    "email_send", "email_draft",

    # WordPress
    "wp_list_posts", "wp_get_post", "wp_create_post", "wp_update_post",

    # Images
    "image_generate", "image_generate_icon", "image_generate_banner",

    # Skills
    "skill_list", "skill_create_start", "skill_edit_instructions", "skill_activate", "skill_validate",
    "skill_view", "skill_delete", "skill_add_script", "skill_add_reference",
    "skill_marketplace_search", "skill_marketplace_install", "skill_marketplace_info",

    # Session/Security
    "session_get_mode", "session_enable_safe", "session_enable_trust",
    "session_get_stats", "session_list_approved", "session_clear_approvals",

    # Meta-tools (Tier 2)
    "aws_ops", "github_ops", "content_ops", "image_ops", "email_ops", "skill_ops",

    # Discovery tools (Tier 3)
    "tools_search", "tools_schema", "tools_execute",
]


def load_config():
    """Load exposed tools config."""
    if not CONFIG_FILE.exists():
        return None
    with open(CONFIG_FILE) as f:
        data = json.load(f)
    return data.get("tools")


def save_config(tools):
    """Save exposed tools config."""
    data = {
        "description": "Tools to expose via MCP. Set tools to null or remove file to expose all tools.",
        "tools": sorted(tools) if tools else None
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved {len(tools) if tools else 'all'} tools to {CONFIG_FILE}")
    print("Restart mcp-server-v2 to apply: sudo systemctl restart mcp-server-v2")


def list_exposed():
    """List currently exposed tools."""
    tools = load_config()
    if tools is None:
        print("All tools exposed (no filter)")
        return
    print(f"Exposed tools ({len(tools)}):")
    for t in sorted(tools):
        print(f"  {t}")


def list_all():
    """List all registered tools."""
    print(f"All registered tools ({len(ALL_TOOLS)}):")
    for t in sorted(ALL_TOOLS):
        print(f"  {t}")


def add_tool(name):
    """Add a tool to exposed list."""
    if name not in ALL_TOOLS:
        print(f"Warning: '{name}' not in known tools list")

    tools = load_config()
    if tools is None:
        print("Currently exposing all tools. Creating filtered list.")
        tools = list(ALL_TOOLS)

    if name in tools:
        print(f"'{name}' already in exposed list")
        return

    tools.append(name)
    save_config(tools)


def remove_tool(name):
    """Remove a tool from exposed list."""
    tools = load_config()
    if tools is None:
        print("Currently exposing all tools. Nothing to remove.")
        return

    if name not in tools:
        print(f"'{name}' not in exposed list")
        return

    tools.remove(name)
    save_config(tools)


def expose_all():
    """Expose all tools by removing config."""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
        print("Removed config file. All tools now exposed.")
        print("Restart mcp-server-v2 to apply: sudo systemctl restart mcp-server-v2")
    else:
        print("Config file doesn't exist. All tools already exposed.")


def search_tools(query):
    """Search for tools by name."""
    query = query.lower()
    matches = [t for t in ALL_TOOLS if query in t.lower()]
    if not matches:
        print(f"No tools matching '{query}'")
        return
    print(f"Tools matching '{query}':")
    for t in sorted(matches):
        exposed = load_config()
        status = "exposed" if exposed is None or t in exposed else "hidden"
        print(f"  {t} [{status}]")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "list":
        list_exposed()
    elif cmd == "all":
        list_all()
    elif cmd == "add" and len(sys.argv) > 2:
        add_tool(sys.argv[2])
    elif cmd == "remove" and len(sys.argv) > 2:
        remove_tool(sys.argv[2])
    elif cmd == "expose-all":
        expose_all()
    elif cmd == "search" and len(sys.argv) > 2:
        search_tools(sys.argv[2])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
