"""
Tier 2 Meta-Tools

Category gateway tools that wrap multiple internal tools:
- aws_ops: CDK, CloudFormation, Lambda, S3
- github_ops: Advanced PR/issue operations
- content_ops: WordPress, SEO
- image_ops: Generate, edit, icons
- email_ops: Advanced Gmail operations
- skill_ops: Advanced skill operations
- linear_ops: Issues, projects, teams, cycles, labels
- browser_ops: Navigation, interactions, screenshots, automation
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def aws_ops(
    action: str,
    format: str = "voice",
    **kwargs
) -> dict:
    """
    AWS operations gateway.

    Actions:
    - lambda_list: List Lambda functions
    - lambda_invoke: Invoke Lambda function
    - lambda_logs: Get Lambda logs
    - s3_list: List S3 buckets/objects
    - s3_get: Get S3 object
    - s3_put: Put S3 object
    - dynamodb_list: List DynamoDB tables
    - dynamodb_scan: Scan DynamoDB table
    - cost_usage: Get cost and usage report
    - cost_forecast: Get cost forecast

    Args:
        action: Action to perform
        format: "voice" or "standard"
        **kwargs: Action-specific arguments
    """
    from mcp.tools.aws_tools import (
        aws_lambda_invoke, aws_lambda_list, aws_lambda_logs,
        aws_s3_list, aws_s3_get, aws_s3_put,
        aws_dynamodb_list_tables, aws_dynamodb_scan,
        aws_cost_get_usage, aws_cost_get_forecast
    )

    action_map = {
        "lambda_list": aws_lambda_list,
        "lambda_invoke": aws_lambda_invoke,
        "lambda_logs": aws_lambda_logs,
        "s3_list": aws_s3_list,
        "s3_get": aws_s3_get,
        "s3_put": aws_s3_put,
        "dynamodb_list": aws_dynamodb_list_tables,
        "dynamodb_scan": aws_dynamodb_scan,
        "cost_usage": aws_cost_get_usage,
        "cost_forecast": aws_cost_get_forecast,
    }

    if action not in action_map:
        return {
            "error": f"Unknown action '{action}'",
            "available_actions": list(action_map.keys())
        }

    try:
        result = action_map[action](**kwargs)
        return _format_result(result, format, f"aws_{action}")
    except TypeError as e:
        return {"error": f"Invalid arguments for {action}: {str(e)}"}
    except Exception as e:
        logger.error(f"AWS ops error: {e}")
        return {"error": str(e)}


def github_ops(
    action: str,
    format: str = "voice",
    **kwargs
) -> dict:
    """
    Advanced GitHub operations gateway.

    Actions:
    - pr_create: Create pull request
    - pr_merge: Merge pull request
    - pr_review: Add PR review
    - pr_checkout: Checkout PR locally
    - issue_create: Create issue
    - issue_comment: Comment on issue
    - issue_close: Close issue
    - workflow_list: List workflows
    - workflow_run: Trigger workflow
    - release_list: List releases

    Args:
        action: Action to perform
        format: "voice" or "standard"
        **kwargs: Action-specific arguments
    """
    from mcp.tools.github_tools import (
        github_pr_create, github_pr_merge, github_pr_review, github_pr_checkout,
        github_issue_create, github_issue_comment,
        github_workflow_list, github_workflow_view
    )

    action_map = {
        "pr_create": github_pr_create,
        "pr_merge": github_pr_merge,
        "pr_review": github_pr_review,
        "pr_checkout": github_pr_checkout,
        "issue_create": github_issue_create,
        "issue_comment": github_issue_comment,
        "workflow_list": github_workflow_list,
        "workflow_view": github_workflow_view,
    }

    if action not in action_map:
        return {
            "error": f"Unknown action '{action}'",
            "available_actions": list(action_map.keys())
        }

    try:
        result = action_map[action](**kwargs)
        return _format_result(result, format, f"github_{action}")
    except TypeError as e:
        return {"error": f"Invalid arguments for {action}: {str(e)}"}
    except Exception as e:
        logger.error(f"GitHub ops error: {e}")
        return {"error": str(e)}


def content_ops(
    action: str,
    format: str = "voice",
    **kwargs
) -> dict:
    """
    Content operations gateway (WordPress, SEO).

    Actions:
    - wp_create_post: Create WordPress post
    - wp_update_post: Update WordPress post
    - wp_list_posts: List posts
    - seo_analyze: Analyze content for SEO
    - seo_keywords: Generate keywords

    Args:
        action: Action to perform
        format: "voice" or "standard"
        **kwargs: Action-specific arguments
    """
    from mcp.tools.wordpress_tools import (
        wordpress_create_post, wordpress_update_post, wordpress_list_posts
    )

    action_map = {
        "wp_create_post": wordpress_create_post,
        "wp_update_post": wordpress_update_post,
        "wp_list_posts": wordpress_list_posts,
    }

    if action not in action_map:
        return {
            "error": f"Unknown action '{action}'",
            "available_actions": list(action_map.keys())
        }

    try:
        result = action_map[action](**kwargs)
        return _format_result(result, format, f"content_{action}")
    except TypeError as e:
        return {"error": f"Invalid arguments for {action}: {str(e)}"}
    except Exception as e:
        logger.error(f"Content ops error: {e}")
        return {"error": str(e)}


def image_ops(
    action: str,
    format: str = "voice",
    **kwargs
) -> dict:
    """
    Image operations gateway.

    Actions:
    - generate: Generate image from prompt
    - generate_icon: Generate app icon
    - send_slack: Generate and send to Slack

    Args:
        action: Action to perform
        format: "voice" or "standard"
        **kwargs: Action-specific arguments
    """
    from mcp.tools.image_tools import image_generate, image_generate_icon
    from mcp.tools.slack_tools import slack_send_image

    action_map = {
        "generate": image_generate,
        "generate_icon": image_generate_icon,
        "send_slack": slack_send_image,
    }

    if action not in action_map:
        return {
            "error": f"Unknown action '{action}'",
            "available_actions": list(action_map.keys())
        }

    try:
        result = action_map[action](**kwargs)
        return _format_result(result, format, f"image_{action}")
    except TypeError as e:
        return {"error": f"Invalid arguments for {action}: {str(e)}"}
    except Exception as e:
        logger.error(f"Image ops error: {e}")
        return {"error": str(e)}


def email_ops(
    action: str,
    format: str = "voice",
    **kwargs
) -> dict:
    """
    Advanced email operations gateway.

    Actions:
    - get_thread: Get email thread
    - label: Apply label to message
    - draft: Create draft
    - send_attachment: Send with attachment

    Args:
        action: Action to perform
        format: "voice" or "standard"
        **kwargs: Action-specific arguments
    """
    from mcp.tools.google_tools import gmail_list, gmail_send, gmail_read

    # Map available actions - some may need to be implemented
    action_map = {
        "list": gmail_list,
        "send": gmail_send,
        "read": gmail_read,
    }

    if action not in action_map:
        return {
            "error": f"Unknown action '{action}'",
            "available_actions": list(action_map.keys())
        }

    try:
        result = action_map[action](**kwargs)
        return _format_result(result, format, f"email_{action}")
    except TypeError as e:
        return {"error": f"Invalid arguments for {action}: {str(e)}"}
    except Exception as e:
        logger.error(f"Email ops error: {e}")
        return {"error": str(e)}


def skill_ops(
    action: str,
    format: str = "voice",
    **kwargs
) -> dict:
    """
    Advanced skill operations gateway.

    Actions:
    - marketplace_search: Search skill marketplace
    - marketplace_install: Install from marketplace
    - marketplace_info: Get skill info
    - add_script: Add script to skill
    - add_reference: Add reference doc
    - view: View skill details
    - delete: Delete skill

    Args:
        action: Action to perform
        format: "voice" or "standard"
        **kwargs: Action-specific arguments
    """
    from mcp.tools.skill_tools import (
        skill_marketplace_search, skill_marketplace_install, skill_marketplace_info,
        skill_add_script, skill_add_reference, skill_view, skill_delete
    )

    action_map = {
        "marketplace_search": skill_marketplace_search,
        "marketplace_install": skill_marketplace_install,
        "marketplace_info": skill_marketplace_info,
        "add_script": skill_add_script,
        "add_reference": skill_add_reference,
        "view": skill_view,
        "delete": skill_delete,
    }

    if action not in action_map:
        return {
            "error": f"Unknown action '{action}'",
            "available_actions": list(action_map.keys())
        }

    try:
        result = action_map[action](**kwargs)
        return _format_result(result, format, f"skill_{action}")
    except TypeError as e:
        return {"error": f"Invalid arguments for {action}: {str(e)}"}
    except Exception as e:
        logger.error(f"Skill ops error: {e}")
        return {"error": str(e)}


def linear_ops(
    action: str,
    format: str = "voice",
    **kwargs
) -> dict:
    """
    Linear operations gateway.

    Actions:
    - list_issues: List issues with filters
    - create_issue: Create new issue
    - get_issue: Get issue details
    - update_issue: Update issue
    - delete_issue: Delete/archive issue
    - search_issues: Search issues by text
    - list_teams: List all teams
    - get_team: Get team with states/labels
    - list_projects: List projects
    - get_project: Get project details
    - create_project: Create project
    - list_cycles: List cycles
    - get_active_cycle: Get current cycle
    - create_cycle: Create cycle
    - list_labels: List labels
    - create_label: Create label
    - add_comment: Add comment to issue
    - list_users: List users
    - get_viewer: Get authenticated user
    - get_workflow_states: Get workflow states
    - get_organization: Get org info

    Args:
        action: Action to perform
        format: "voice" or "standard"
        **kwargs: Action-specific arguments
    """
    from mcp.tools.linear_tools import (
        linear_list_issues, linear_create_issue, linear_get_issue,
        linear_update_issue, linear_delete_issue, linear_search_issues,
        linear_list_teams, linear_get_team,
        linear_list_projects, linear_get_project, linear_create_project,
        linear_list_cycles, linear_get_active_cycle, linear_create_cycle,
        linear_list_labels, linear_create_label,
        linear_add_comment,
        linear_list_users, linear_get_viewer,
        linear_get_workflow_states, linear_get_organization,
    )

    action_map = {
        "list_issues": linear_list_issues,
        "create_issue": linear_create_issue,
        "get_issue": linear_get_issue,
        "update_issue": linear_update_issue,
        "delete_issue": linear_delete_issue,
        "search_issues": linear_search_issues,
        "list_teams": linear_list_teams,
        "get_team": linear_get_team,
        "list_projects": linear_list_projects,
        "get_project": linear_get_project,
        "create_project": linear_create_project,
        "list_cycles": linear_list_cycles,
        "get_active_cycle": linear_get_active_cycle,
        "create_cycle": linear_create_cycle,
        "list_labels": linear_list_labels,
        "create_label": linear_create_label,
        "add_comment": linear_add_comment,
        "list_users": linear_list_users,
        "get_viewer": linear_get_viewer,
        "get_workflow_states": linear_get_workflow_states,
        "get_organization": linear_get_organization,
    }

    if action not in action_map:
        return {
            "error": f"Unknown action '{action}'",
            "available_actions": list(action_map.keys())
        }

    try:
        result = action_map[action](**kwargs)
        return _format_result(result, format, f"linear_{action}")
    except TypeError as e:
        return {"error": f"Invalid arguments for {action}: {str(e)}"}
    except Exception as e:
        logger.error(f"Linear ops error: {e}")
        return {"error": str(e)}


def browser_ops(
    action: str,
    format: str = "voice",
    **kwargs
) -> dict:
    """
    Browser automation gateway.

    Actions:
    - open: Navigate to URL
    - back: Go back in history
    - forward: Go forward in history
    - reload: Reload page
    - close: Close browser
    - snapshot: Get page elements with refs
    - click: Click element by ref
    - fill: Clear and type into input
    - type: Type without clearing
    - press: Press key/combination
    - hover: Hover over element
    - scroll: Scroll page
    - get_text: Get element text
    - get_html: Get element innerHTML
    - get_value: Get input value
    - get_title: Get page title
    - get_url: Get current URL
    - screenshot: Take screenshot
    - pdf: Save as PDF
    - wait: Wait for condition
    - is_visible: Check visibility
    - is_enabled: Check enabled state
    - is_checked: Check checkbox state
    - eval: Execute JavaScript
    - cookies_get: Get cookies
    - cookies_set: Set cookie
    - cookies_clear: Clear cookies
    - set_viewport: Set viewport size
    - set_device: Emulate device
    - tab_list: List tabs
    - tab_new: Open new tab
    - tab_switch: Switch to tab
    - tab_close: Close tab

    Args:
        action: Action to perform
        format: "voice" or "standard"
        **kwargs: Action-specific arguments
    """
    from mcp.tools.browser_tools import (
        browser_open, browser_back, browser_forward, browser_reload, browser_close,
        browser_snapshot, browser_click, browser_fill, browser_type, browser_press,
        browser_hover, browser_check, browser_uncheck, browser_select,
        browser_scroll, browser_scroll_into_view,
        browser_get_text, browser_get_html, browser_get_value, browser_get_attribute,
        browser_get_title, browser_get_url,
        browser_screenshot, browser_pdf, browser_wait,
        browser_is_visible, browser_is_enabled, browser_is_checked,
        browser_eval, browser_cookies_get, browser_cookies_set, browser_cookies_clear,
        browser_set_viewport, browser_set_device,
        browser_tab_list, browser_tab_new, browser_tab_switch, browser_tab_close,
    )

    action_map = {
        "open": browser_open,
        "back": browser_back,
        "forward": browser_forward,
        "reload": browser_reload,
        "close": browser_close,
        "snapshot": browser_snapshot,
        "click": browser_click,
        "fill": browser_fill,
        "type": browser_type,
        "press": browser_press,
        "hover": browser_hover,
        "check": browser_check,
        "uncheck": browser_uncheck,
        "select": browser_select,
        "scroll": browser_scroll,
        "scroll_into_view": browser_scroll_into_view,
        "get_text": browser_get_text,
        "get_html": browser_get_html,
        "get_value": browser_get_value,
        "get_attribute": browser_get_attribute,
        "get_title": browser_get_title,
        "get_url": browser_get_url,
        "screenshot": browser_screenshot,
        "pdf": browser_pdf,
        "wait": browser_wait,
        "is_visible": browser_is_visible,
        "is_enabled": browser_is_enabled,
        "is_checked": browser_is_checked,
        "eval": browser_eval,
        "cookies_get": browser_cookies_get,
        "cookies_set": browser_cookies_set,
        "cookies_clear": browser_cookies_clear,
        "set_viewport": browser_set_viewport,
        "set_device": browser_set_device,
        "tab_list": browser_tab_list,
        "tab_new": browser_tab_new,
        "tab_switch": browser_tab_switch,
        "tab_close": browser_tab_close,
    }

    if action not in action_map:
        return {
            "error": f"Unknown action '{action}'",
            "available_actions": list(action_map.keys())
        }

    try:
        result = action_map[action](**kwargs)
        return _format_result(result, format, f"browser_{action}")
    except TypeError as e:
        return {"error": f"Invalid arguments for {action}: {str(e)}"}
    except Exception as e:
        logger.error(f"Browser ops error: {e}")
        return {"error": str(e)}


def _format_result(result: Any, format: str, tool_name: str) -> Any:
    """Format result based on mode."""
    if format != "voice":
        return result

    from .formatter import format_response, VoiceFormat
    return format_response(result, VoiceFormat.VOICE, tool_name)


def register_meta_tools(server) -> int:
    """Register all Tier 2 meta-tools with the MCP server."""

    server.register_tool(
        name="aws_ops",
        description="AWS operations: Lambda invoke/list/logs, S3 list/get/put, DynamoDB list/scan, Cost reports",
        input_schema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["lambda_list", "lambda_invoke", "lambda_logs", "s3_list", "s3_get", "s3_put", "dynamodb_list", "dynamodb_scan", "cost_usage", "cost_forecast"],
                    "description": "Action to perform"
                },
                "format": {
                    "type": "string",
                    "enum": ["voice", "standard"],
                    "default": "voice"
                }
            },
            "required": ["action"]
        },
        handler=aws_ops,
        requires_approval=True,
        category="aws"
    )

    server.register_tool(
        name="github_ops",
        description="Advanced GitHub: create/merge/review PRs, create/comment issues, workflows",
        input_schema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["pr_create", "pr_merge", "pr_review", "pr_checkout", "issue_create", "issue_comment", "workflow_list", "workflow_view"],
                    "description": "Action to perform"
                },
                "format": {
                    "type": "string",
                    "enum": ["voice", "standard"],
                    "default": "voice"
                }
            },
            "required": ["action"]
        },
        handler=github_ops,
        requires_approval=True,
        category="github"
    )

    server.register_tool(
        name="content_ops",
        description="Content operations: WordPress posts, SEO analysis",
        input_schema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["wp_create_post", "wp_update_post", "wp_list_posts"],
                    "description": "Action to perform"
                },
                "format": {
                    "type": "string",
                    "enum": ["voice", "standard"],
                    "default": "voice"
                }
            },
            "required": ["action"]
        },
        handler=content_ops,
        requires_approval=True,
        category="content"
    )

    server.register_tool(
        name="image_ops",
        description="Image operations: generate images, icons, send to Slack",
        input_schema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["generate", "generate_icon", "send_slack"],
                    "description": "Action to perform"
                },
                "prompt": {
                    "type": "string",
                    "description": "Image description"
                },
                "format": {
                    "type": "string",
                    "enum": ["voice", "standard"],
                    "default": "voice"
                }
            },
            "required": ["action"]
        },
        handler=image_ops,
        requires_approval=True,
        category="image"
    )

    server.register_tool(
        name="email_ops",
        description="Advanced email: threads, labels, drafts, attachments",
        input_schema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list", "send", "read"],
                    "description": "Action to perform"
                },
                "format": {
                    "type": "string",
                    "enum": ["voice", "standard"],
                    "default": "voice"
                }
            },
            "required": ["action"]
        },
        handler=email_ops,
        requires_approval=False,
        category="email"
    )

    server.register_tool(
        name="skill_ops",
        description="Advanced skill operations: marketplace, scripts, references",
        input_schema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["marketplace_search", "marketplace_install", "marketplace_info", "add_script", "add_reference", "view", "delete"],
                    "description": "Action to perform"
                },
                "format": {
                    "type": "string",
                    "enum": ["voice", "standard"],
                    "default": "voice"
                }
            },
            "required": ["action"]
        },
        handler=skill_ops,
        requires_approval=False,
        category="skills"
    )

    server.register_tool(
        name="linear_ops",
        description="Linear operations: issues, projects, teams, cycles, labels, comments, users, workflow states",
        input_schema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "list_issues", "create_issue", "get_issue", "update_issue", "delete_issue", "search_issues",
                        "list_teams", "get_team", "list_projects", "get_project", "create_project",
                        "list_cycles", "get_active_cycle", "create_cycle",
                        "list_labels", "create_label", "add_comment",
                        "list_users", "get_viewer", "get_workflow_states", "get_organization"
                    ],
                    "description": "Action to perform"
                },
                "format": {
                    "type": "string",
                    "enum": ["voice", "standard"],
                    "default": "voice"
                }
            },
            "required": ["action"]
        },
        handler=linear_ops,
        requires_approval=False,
        category="linear"
    )

    server.register_tool(
        name="browser_ops",
        description="Browser automation: navigate, interact, screenshot, test web pages",
        input_schema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "open", "back", "forward", "reload", "close",
                        "snapshot", "click", "fill", "type", "press", "hover",
                        "check", "uncheck", "select", "scroll", "scroll_into_view",
                        "get_text", "get_html", "get_value", "get_attribute", "get_title", "get_url",
                        "screenshot", "pdf", "wait",
                        "is_visible", "is_enabled", "is_checked",
                        "eval", "cookies_get", "cookies_set", "cookies_clear",
                        "set_viewport", "set_device",
                        "tab_list", "tab_new", "tab_switch", "tab_close"
                    ],
                    "description": "Browser action to perform"
                },
                "url": {"type": "string", "description": "URL for open action"},
                "ref": {"type": "string", "description": "Element ref (e.g., @e1) for interactions"},
                "text": {"type": "string", "description": "Text for fill/type actions"},
                "key": {"type": "string", "description": "Key for press action"},
                "script": {"type": "string", "description": "JavaScript for eval action"},
                "path": {"type": "string", "description": "File path for screenshot/pdf"},
                "format": {
                    "type": "string",
                    "enum": ["voice", "standard"],
                    "default": "voice"
                }
            },
            "required": ["action"]
        },
        handler=browser_ops,
        requires_approval=False,
        category="browser"
    )

    return 8
