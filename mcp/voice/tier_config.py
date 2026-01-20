"""
Voice Tool Tier Configuration

Defines the 3-tier tool exposure system:
- Tier 1: Direct access (~35 high-frequency tools)
- Tier 2: Meta-tools (category gateways)
- Tier 3: Discovery (search/schema/execute anything)
"""

from typing import Optional

# Tier 1: Direct access tools (always exposed to voice agent)
TIER_1_TOOLS = {
    # Basics
    "get_time",
    "get_weather",
    "list_capabilities",

    # App Store
    "appstore_list_apps",
    "appstore_sales",
    "appstore_downloads",
    "appstore_ratings",

    # TestFlight (high-frequency)
    "testflight_list_builds",
    "testflight_check_build_status",
    "testflight_get_review_status",

    # Files
    "file_read",
    "file_write",
    "file_edit",
    "file_list",
    "file_grep",

    # Git/GitHub (combined)
    "git_status",
    "git_diff",
    "git_log",
    "git_commit",
    "git_push",
    "github_pr_list",
    "github_pr_view",
    "github_issue_list",

    # Bash
    "bash_execute",
    "bash_background",

    # Skills
    "skill_list",
    "skill_create",
    "skill_edit",
    "skill_activate",
    "skill_validate",

    # Slack
    "slack_get_unread",
    "slack_get_mentions",
    "slack_send_dm",
    "slack_send_channel",

    # Gmail
    "gmail_list",
    "gmail_search",
    "gmail_send",

    # Calendar
    "gcal_list_events",
    "gcal_create_event",

    # ClickUp
    "clickup_list_tasks",
    "clickup_create_task",
    "clickup_get_task",

    # Google Tasks
    "tasks_list",
    "tasks_create",
    "tasks_complete",

    # Web
    "web_search",
}

# Tier 2: Meta-tools (gateways to related tools)
TIER_2_META_TOOLS = {
    "aws_ops": {
        "description": "AWS operations: Lambda, S3, DynamoDB, Cost reports",
        "actions": ["lambda_list", "lambda_invoke", "lambda_logs", "s3_list", "s3_get", "s3_put", "dynamodb_list", "dynamodb_scan", "cost_usage", "cost_forecast"],
        "internal_tools": [
            "aws_lambda_invoke", "aws_lambda_list", "aws_lambda_logs",
            "aws_s3_list", "aws_s3_get", "aws_s3_put",
            "aws_dynamodb_list_tables", "aws_dynamodb_scan", "aws_dynamodb_query",
            "aws_cost_get_usage", "aws_cost_get_forecast",
        ]
    },
    "github_ops": {
        "description": "Advanced GitHub operations: PR management, releases, workflows",
        "actions": ["pr_create", "pr_merge", "pr_review", "issue_create", "issue_comment", "workflow_run"],
        "internal_tools": [
            "github_pr_create", "github_pr_merge", "github_pr_checkout", "github_pr_review",
            "github_issue_create", "github_issue_comment", "github_issue_close",
            "github_workflow_list", "github_workflow_view", "github_workflow_run",
            "github_repo_view", "github_release_list",
        ]
    },
    "content_ops": {
        "description": "Content operations: WordPress, SEO, writing",
        "actions": ["wp_post", "wp_update", "seo_analyze", "seo_keywords"],
        "internal_tools": [
            "wordpress_create_post", "wordpress_update_post", "wordpress_list_posts",
            "wordpress_seo_analyze", "wordpress_seo_keywords",
        ]
    },
    "image_ops": {
        "description": "Image operations: generate, edit, icons, upload",
        "actions": ["generate", "generate_icon", "edit", "upload_slack"],
        "internal_tools": [
            "image_generate", "image_generate_icon", "image_edit",
            "slack_send_image",
        ]
    },
    "email_ops": {
        "description": "Advanced email: threads, labels, drafts, attachments",
        "actions": ["get_thread", "label", "draft", "attach"],
        "internal_tools": [
            "gmail_get_thread", "gmail_label", "gmail_draft",
            "gmail_get_attachment", "gmail_send_with_attachment",
        ]
    },
    "skill_ops": {
        "description": "Advanced skill operations: marketplace, scripts, references",
        "actions": ["marketplace_search", "marketplace_install", "add_script", "add_reference"],
        "internal_tools": [
            "skill_marketplace_search", "skill_marketplace_install", "skill_marketplace_info",
            "skill_add_script", "skill_add_reference", "skill_view", "skill_delete",
        ]
    },
    "linear_ops": {
        "description": "Linear operations: issues, projects, teams, cycles, labels, comments, users",
        "actions": [
            "list_issues", "create_issue", "get_issue", "update_issue", "delete_issue", "search_issues",
            "list_teams", "get_team", "list_projects", "get_project", "create_project",
            "list_cycles", "get_active_cycle", "create_cycle",
            "list_labels", "create_label", "add_comment",
            "list_users", "get_viewer", "get_workflow_states", "get_organization"
        ],
        "internal_tools": [
            "linear_list_issues", "linear_create_issue", "linear_get_issue",
            "linear_update_issue", "linear_delete_issue", "linear_search_issues",
            "linear_list_teams", "linear_get_team",
            "linear_list_projects", "linear_get_project", "linear_create_project",
            "linear_list_cycles", "linear_get_active_cycle", "linear_create_cycle",
            "linear_list_labels", "linear_create_label",
            "linear_add_comment",
            "linear_list_users", "linear_get_viewer",
            "linear_get_workflow_states", "linear_get_organization",
        ]
    },
    "testflight_ops": {
        "description": "TestFlight operations: builds, beta testers, beta groups, review submissions",
        "actions": [
            "get_build", "submit_for_review", "list_testers", "add_tester", "remove_tester",
            "list_groups", "create_group", "delete_group", "add_build_to_group",
            "add_testers_to_group", "remove_testers_from_group"
        ],
        "internal_tools": [
            "testflight_get_build", "testflight_submit_for_review",
            "testflight_list_testers", "testflight_add_tester", "testflight_remove_tester",
            "testflight_list_groups", "testflight_create_group", "testflight_delete_group",
            "testflight_add_build_to_group", "testflight_add_testers_to_group",
            "testflight_remove_testers_from_group",
        ]
    },
    "browser_ops": {
        "description": "Browser automation: navigation, interactions, screenshots, testing",
        "actions": [
            "open", "back", "forward", "reload", "close",
            "snapshot", "click", "fill", "type", "press", "hover", "scroll",
            "get_text", "get_html", "get_value", "get_attribute", "get_title", "get_url",
            "screenshot", "pdf", "wait",
            "is_visible", "is_enabled", "is_checked",
            "eval", "cookies", "set_viewport", "set_device",
            "tab_list", "tab_new", "tab_switch", "tab_close"
        ],
        "internal_tools": [
            "browser_open", "browser_back", "browser_forward", "browser_reload", "browser_close",
            "browser_snapshot", "browser_click", "browser_fill", "browser_type", "browser_press",
            "browser_hover", "browser_check", "browser_uncheck", "browser_select",
            "browser_scroll", "browser_scroll_into_view",
            "browser_get_text", "browser_get_html", "browser_get_value", "browser_get_attribute",
            "browser_get_title", "browser_get_url",
            "browser_screenshot", "browser_pdf", "browser_wait",
            "browser_is_visible", "browser_is_enabled", "browser_is_checked",
            "browser_eval", "browser_cookies_get", "browser_cookies_set", "browser_cookies_clear",
            "browser_set_viewport", "browser_set_device",
            "browser_tab_list", "browser_tab_new", "browser_tab_switch", "browser_tab_close",
        ]
    },
}

# Tier 3: Discovery tools (access everything)
TIER_3_DISCOVERY = {
    "tools_search": {
        "description": "Search for tools by keyword or intent",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query or intent"},
                "category": {"type": "string", "description": "Optional category filter"},
            },
            "required": ["query"]
        }
    },
    "tools_schema": {
        "description": "Get full schema for any tool",
        "input_schema": {
            "type": "object",
            "properties": {
                "tool_name": {"type": "string", "description": "Name of the tool"},
            },
            "required": ["tool_name"]
        }
    },
    "tools_execute": {
        "description": "Execute any tool by name with arguments",
        "input_schema": {
            "type": "object",
            "properties": {
                "tool_name": {"type": "string", "description": "Name of the tool"},
                "arguments": {"type": "object", "description": "Tool arguments"},
            },
            "required": ["tool_name", "arguments"]
        }
    },
}


def get_tier_for_tool(tool_name: str) -> int:
    """Get the tier for a tool (1, 2, or 3)."""
    normalized = tool_name.replace(".", "_")

    if normalized in TIER_1_TOOLS:
        return 1

    if normalized in TIER_2_META_TOOLS:
        return 2

    for meta_tool, config in TIER_2_META_TOOLS.items():
        if normalized in config["internal_tools"]:
            return 2

    if normalized in TIER_3_DISCOVERY:
        return 3

    # Everything else is accessible via Tier 3 discovery
    return 3


def get_meta_tool_for_internal(tool_name: str) -> Optional[str]:
    """Get the meta-tool that wraps an internal tool."""
    normalized = tool_name.replace(".", "_")

    for meta_tool, config in TIER_2_META_TOOLS.items():
        if normalized in config["internal_tools"]:
            return meta_tool

    return None


def get_all_exposed_tools() -> list[str]:
    """Get all tools directly exposed to voice agent (Tier 1 + meta-tools + discovery)."""
    tools = list(TIER_1_TOOLS)
    tools.extend(TIER_2_META_TOOLS.keys())
    tools.extend(TIER_3_DISCOVERY.keys())
    return sorted(tools)
