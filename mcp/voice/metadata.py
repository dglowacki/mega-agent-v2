"""
Voice Tool Metadata

Defines latency tiers and confirmation requirements for tools.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class LatencyTier(Enum):
    """Expected latency for tool execution."""
    INSTANT = "instant"    # <100ms - local lookups, time, cached data
    FAST = "fast"          # <1s - simple API calls, file reads
    MEDIUM = "medium"      # 1-5s - web searches, API queries
    SLOW = "slow"          # >5s - image generation, complex operations


@dataclass
class ToolMetadata:
    """Metadata for voice-optimized tool behavior."""
    latency: LatencyTier
    requires_confirmation: bool = False
    confirmation_message: Optional[str] = None
    voice_description: Optional[str] = None  # Shorter description for voice
    suggested_followups: Optional[list[str]] = None


# Tool metadata registry
TOOL_METADATA: dict[str, ToolMetadata] = {
    # Basics - instant
    "get_time": ToolMetadata(
        latency=LatencyTier.INSTANT,
        voice_description="Get current time"
    ),
    "get_weather": ToolMetadata(
        latency=LatencyTier.FAST,
        voice_description="Get weather forecast"
    ),
    "list_capabilities": ToolMetadata(
        latency=LatencyTier.INSTANT,
        voice_description="List what I can do"
    ),

    # App Store - fast
    "appstore_sales": ToolMetadata(
        latency=LatencyTier.FAST,
        voice_description="Get app sales data"
    ),
    "appstore_downloads": ToolMetadata(
        latency=LatencyTier.FAST,
        voice_description="Get download stats"
    ),
    "appstore_ratings": ToolMetadata(
        latency=LatencyTier.FAST,
        voice_description="Get app ratings"
    ),

    # Files - fast
    "file_read": ToolMetadata(
        latency=LatencyTier.FAST,
        voice_description="Read a file"
    ),
    "file_write": ToolMetadata(
        latency=LatencyTier.FAST,
        requires_confirmation=True,
        confirmation_message="Write to {path}?",
        voice_description="Write to a file"
    ),
    "file_edit": ToolMetadata(
        latency=LatencyTier.FAST,
        requires_confirmation=True,
        confirmation_message="Edit {path}?",
        voice_description="Edit a file"
    ),
    "file_list": ToolMetadata(
        latency=LatencyTier.FAST,
        voice_description="List files"
    ),
    "file_grep": ToolMetadata(
        latency=LatencyTier.FAST,
        voice_description="Search in files"
    ),

    # Git - fast
    "git_status": ToolMetadata(
        latency=LatencyTier.FAST,
        voice_description="Check git status"
    ),
    "git_diff": ToolMetadata(
        latency=LatencyTier.FAST,
        voice_description="Show changes"
    ),
    "git_log": ToolMetadata(
        latency=LatencyTier.FAST,
        voice_description="Show commit history"
    ),
    "git_commit": ToolMetadata(
        latency=LatencyTier.FAST,
        requires_confirmation=True,
        confirmation_message="Commit with message: {message}?",
        voice_description="Commit changes"
    ),
    "git_push": ToolMetadata(
        latency=LatencyTier.MEDIUM,
        requires_confirmation=True,
        confirmation_message="Push to {remote}?",
        voice_description="Push to remote"
    ),

    # GitHub - fast/medium
    "github_pr_list": ToolMetadata(
        latency=LatencyTier.FAST,
        voice_description="List pull requests"
    ),
    "github_pr_view": ToolMetadata(
        latency=LatencyTier.FAST,
        voice_description="View a pull request"
    ),
    "github_issue_list": ToolMetadata(
        latency=LatencyTier.FAST,
        voice_description="List issues"
    ),

    # Bash - variable
    "bash_execute": ToolMetadata(
        latency=LatencyTier.MEDIUM,
        requires_confirmation=True,
        confirmation_message="Run: {command}?",
        voice_description="Run a command"
    ),
    "bash_background": ToolMetadata(
        latency=LatencyTier.FAST,
        requires_confirmation=True,
        confirmation_message="Run in background: {command}?",
        voice_description="Run command in background"
    ),

    # Skills - fast
    "skill_list": ToolMetadata(
        latency=LatencyTier.INSTANT,
        voice_description="List available skills"
    ),
    "skill_create": ToolMetadata(
        latency=LatencyTier.FAST,
        requires_confirmation=True,
        confirmation_message="Create skill: {name}?",
        voice_description="Create a new skill"
    ),
    "skill_edit": ToolMetadata(
        latency=LatencyTier.FAST,
        requires_confirmation=True,
        voice_description="Edit a skill"
    ),
    "skill_activate": ToolMetadata(
        latency=LatencyTier.FAST,
        voice_description="Activate a skill"
    ),
    "skill_validate": ToolMetadata(
        latency=LatencyTier.FAST,
        voice_description="Validate a skill"
    ),

    # Slack - fast
    "slack_get_unread": ToolMetadata(
        latency=LatencyTier.FAST,
        voice_description="Check unread messages"
    ),
    "slack_get_mentions": ToolMetadata(
        latency=LatencyTier.FAST,
        voice_description="Check mentions"
    ),
    "slack_send_dm": ToolMetadata(
        latency=LatencyTier.FAST,
        requires_confirmation=True,
        confirmation_message="Send DM to {recipient}?",
        voice_description="Send direct message"
    ),
    "slack_send_channel": ToolMetadata(
        latency=LatencyTier.FAST,
        requires_confirmation=True,
        confirmation_message="Post to {channel}?",
        voice_description="Post to channel"
    ),

    # Gmail - fast
    "gmail_list": ToolMetadata(
        latency=LatencyTier.FAST,
        voice_description="List emails"
    ),
    "gmail_search": ToolMetadata(
        latency=LatencyTier.FAST,
        voice_description="Search emails"
    ),
    "gmail_send": ToolMetadata(
        latency=LatencyTier.FAST,
        requires_confirmation=True,
        confirmation_message="Send email to {to}?",
        voice_description="Send email"
    ),

    # Calendar - fast
    "gcal_list_events": ToolMetadata(
        latency=LatencyTier.FAST,
        voice_description="List calendar events"
    ),
    "gcal_create_event": ToolMetadata(
        latency=LatencyTier.FAST,
        requires_confirmation=True,
        confirmation_message="Create event: {title}?",
        voice_description="Create calendar event"
    ),

    # Linear - fast
    "linear_list_issues": ToolMetadata(
        latency=LatencyTier.FAST,
        voice_description="List Linear issues"
    ),
    "linear_create_issue": ToolMetadata(
        latency=LatencyTier.FAST,
        requires_confirmation=True,
        confirmation_message="Create issue: {title}?",
        voice_description="Create Linear issue"
    ),
    "linear_get_issue": ToolMetadata(
        latency=LatencyTier.FAST,
        voice_description="Get issue details"
    ),

    # ClickUp - fast
    "clickup_list_tasks": ToolMetadata(
        latency=LatencyTier.FAST,
        voice_description="List ClickUp tasks"
    ),
    "clickup_create_task": ToolMetadata(
        latency=LatencyTier.FAST,
        requires_confirmation=True,
        confirmation_message="Create task: {name}?",
        voice_description="Create ClickUp task"
    ),
    "clickup_get_task": ToolMetadata(
        latency=LatencyTier.FAST,
        voice_description="Get task details"
    ),

    # Google Tasks - fast
    "tasks_list": ToolMetadata(
        latency=LatencyTier.FAST,
        voice_description="List tasks"
    ),
    "tasks_create": ToolMetadata(
        latency=LatencyTier.FAST,
        requires_confirmation=True,
        confirmation_message="Create task: {title}?",
        voice_description="Create task"
    ),
    "tasks_complete": ToolMetadata(
        latency=LatencyTier.FAST,
        voice_description="Complete a task"
    ),

    # Web - medium
    "web_search": ToolMetadata(
        latency=LatencyTier.MEDIUM,
        voice_description="Search the web"
    ),

    # Image - slow
    "image_generate": ToolMetadata(
        latency=LatencyTier.SLOW,
        requires_confirmation=True,
        confirmation_message="Generate image: {prompt}?",
        voice_description="Generate an image"
    ),
}


def get_tool_metadata(tool_name: str) -> ToolMetadata:
    """Get metadata for a tool, with sensible defaults."""
    # Normalize tool name (handle both underscore and dot notation)
    normalized = tool_name.replace(".", "_")

    if normalized in TOOL_METADATA:
        return TOOL_METADATA[normalized]

    # Default metadata for unknown tools
    return ToolMetadata(
        latency=LatencyTier.MEDIUM,
        requires_confirmation=False,
        voice_description=tool_name.replace("_", " ").title()
    )
