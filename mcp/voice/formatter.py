"""
Voice Response Formatter

Formats tool responses for voice/conversational consumption:
- Lead with the answer
- Use relative time ("2 hours ago" not "2024-01-15 14:32:00")
- Show deltas ("up 15%" not raw numbers)
- Keep responses concise and speakable
"""

from enum import Enum
from datetime import datetime, timedelta
from typing import Any, Optional
import json
import re


class VoiceFormat(Enum):
    """Response format modes."""
    STANDARD = "standard"  # Full JSON/structured response
    VOICE = "voice"        # Conversational, speakable response


def format_response(
    result: Any,
    format_mode: VoiceFormat = VoiceFormat.STANDARD,
    tool_name: Optional[str] = None
) -> str:
    """
    Format a tool result for the specified mode.

    Args:
        result: Raw tool result
        format_mode: STANDARD or VOICE
        tool_name: Optional tool name for context-specific formatting

    Returns:
        Formatted response string
    """
    if format_mode == VoiceFormat.STANDARD:
        return _format_standard(result)

    return _format_voice(result, tool_name)


def _format_standard(result: Any) -> str:
    """Standard JSON formatting."""
    if isinstance(result, str):
        return result
    return json.dumps(result, indent=2, default=str)


def _format_voice(result: Any, tool_name: Optional[str] = None) -> str:
    """Voice-optimized conversational formatting."""
    if isinstance(result, str):
        return _humanize_text(result, tool_name)

    if isinstance(result, dict):
        return _format_dict_voice(result, tool_name)

    if isinstance(result, list):
        return _format_list_voice(result, tool_name)

    return str(result)


def _humanize_text(text: str, tool_name: Optional[str] = None) -> str:
    """Make text more conversational."""
    # Convert timestamps to relative time
    text = _convert_timestamps(text)

    # Simplify technical terms
    text = _simplify_technical(text)

    # Remove excessive detail for voice
    if len(text) > 500:
        text = _summarize_long_text(text, tool_name)

    return text


def _format_dict_voice(data: dict, tool_name: Optional[str] = None) -> str:
    """Format dictionary data for voice."""
    # Handle common response patterns
    if "error" in data:
        return f"Error: {data['error']}"

    if "message" in data and len(data) <= 2:
        return data["message"]

    if "count" in data and "items" in data:
        count = data["count"]
        items = data["items"]
        if isinstance(items, list) and len(items) > 0:
            preview = ", ".join(str(items[i]) for i in range(min(3, len(items))))
            if count > 3:
                return f"Found {count} items. First few: {preview}"
            return f"Found {count}: {preview}"

    # Tool-specific formatting
    if tool_name:
        formatter = _get_tool_formatter(tool_name)
        if formatter:
            return formatter(data)

    # Generic dict formatting
    parts = []
    for key, value in list(data.items())[:5]:  # Limit to 5 fields
        key_human = key.replace("_", " ").title()
        if isinstance(value, (int, float)):
            parts.append(f"{key_human}: {_format_number(value)}")
        elif isinstance(value, str) and len(value) < 50:
            parts.append(f"{key_human}: {value}")

    return ". ".join(parts) if parts else json.dumps(data)


def _format_list_voice(items: list, tool_name: Optional[str] = None) -> str:
    """Format list data for voice."""
    if not items:
        return "No items found"

    count = len(items)

    # For short lists, enumerate
    if count <= 3:
        formatted = []
        for i, item in enumerate(items, 1):
            if isinstance(item, dict):
                # Extract most important field
                name = item.get("name") or item.get("title") or item.get("subject") or str(item)
                formatted.append(f"{i}. {name}")
            else:
                formatted.append(f"{i}. {item}")
        return "\n".join(formatted)

    # For longer lists, summarize
    preview = []
    for item in items[:3]:
        if isinstance(item, dict):
            name = item.get("name") or item.get("title") or item.get("subject") or str(item)
            preview.append(str(name))
        else:
            preview.append(str(item))

    return f"Found {count} items. First few: {', '.join(preview)}"


def _convert_timestamps(text: str) -> str:
    """Convert ISO timestamps to relative time."""
    # Match ISO timestamps
    iso_pattern = r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}'

    def replace_timestamp(match):
        try:
            ts_str = match.group(0).replace("T", " ")
            ts = datetime.fromisoformat(ts_str.split(".")[0])
            return _relative_time(ts)
        except:
            return match.group(0)

    return re.sub(iso_pattern, replace_timestamp, text)


def _relative_time(dt: datetime) -> str:
    """Convert datetime to relative time string."""
    now = datetime.now()
    diff = now - dt

    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        mins = int(diff.total_seconds() / 60)
        return f"{mins} minute{'s' if mins != 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < timedelta(days=7):
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif diff < timedelta(days=30):
        weeks = diff.days // 7
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    else:
        return dt.strftime("%B %d")


def _format_number(num: float) -> str:
    """Format numbers for voice readability."""
    if isinstance(num, int) or num == int(num):
        num = int(num)
        if num >= 1_000_000:
            return f"{num / 1_000_000:.1f} million"
        elif num >= 1_000:
            return f"{num / 1_000:.1f}K"
        return str(num)
    else:
        return f"{num:.2f}"


def _simplify_technical(text: str) -> str:
    """Simplify technical terms for voice."""
    replacements = {
        "repository": "repo",
        "pull request": "PR",
        "null": "none",
        "undefined": "not set",
        "[]": "empty list",
        "{}": "empty",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _summarize_long_text(text: str, tool_name: Optional[str] = None) -> str:
    """Summarize text that's too long for voice."""
    # Take first paragraph or 300 chars
    paragraphs = text.split("\n\n")
    if paragraphs:
        first = paragraphs[0]
        if len(first) <= 300:
            remaining = len(paragraphs) - 1
            if remaining > 0:
                return f"{first}\n\n...and {remaining} more sections"
            return first

    return text[:300] + "..."


def _get_tool_formatter(tool_name: str):
    """Get tool-specific formatter function."""
    formatters = {
        "get_time": _format_time,
        "get_weather": _format_weather,
        "appstore_sales": _format_sales,
        "slack_get_unread": _format_unread,
        "gmail_list": _format_emails,
        "gcal_list_events": _format_events,
        "git_status": _format_git_status,
        "linear_list_issues": _format_issues,
        "clickup_list_tasks": _format_tasks,
        "tasks_list": _format_tasks,
    }
    return formatters.get(tool_name.replace(".", "_"))


# Tool-specific formatters

def _format_time(data: dict) -> str:
    """Format time response."""
    time = data.get("time", data.get("current_time", ""))
    timezone = data.get("timezone", "")
    if timezone:
        return f"It's {time} {timezone}"
    return f"It's {time}"


def _format_weather(data: dict) -> str:
    """Format weather response."""
    temp = data.get("temperature", data.get("temp", ""))
    condition = data.get("condition", data.get("description", ""))
    location = data.get("location", "")

    parts = []
    if temp:
        parts.append(f"{temp}°")
    if condition:
        parts.append(condition)
    if location:
        return f"{' and '.join(parts)} in {location}"
    return " and ".join(parts)


def _format_sales(data: dict) -> str:
    """Format app sales response."""
    total = data.get("total", data.get("revenue", 0))
    units = data.get("units", data.get("downloads", 0))
    period = data.get("period", "today")

    parts = []
    if total:
        parts.append(f"${_format_number(total)} revenue")
    if units:
        parts.append(f"{_format_number(units)} units")

    return f"{', '.join(parts)} {period}" if parts else str(data)


def _format_unread(data: dict) -> str:
    """Format Slack unread response."""
    channels = data.get("channels", [])
    total = data.get("total", sum(c.get("count", 0) for c in channels))

    if total == 0:
        return "No unread messages"

    if len(channels) == 1:
        ch = channels[0]
        return f"{ch.get('count', total)} unread in {ch.get('name', 'channel')}"

    return f"{total} unread across {len(channels)} channels"


def _format_emails(data: dict) -> str:
    """Format email list response."""
    emails = data.get("messages", data.get("emails", []))
    if not emails:
        return "No emails"

    unread = sum(1 for e in emails if not e.get("read", True))
    if unread:
        return f"{len(emails)} emails, {unread} unread"
    return f"{len(emails)} emails"


def _format_events(data: dict) -> str:
    """Format calendar events response."""
    events = data.get("events", data.get("items", []))
    if not events:
        return "No upcoming events"

    next_event = events[0]
    title = next_event.get("summary", next_event.get("title", "Event"))
    start = next_event.get("start", {})
    time = start.get("dateTime", start.get("date", ""))

    if len(events) == 1:
        return f"Next: {title}"

    return f"Next: {title}. {len(events) - 1} more events today"


def _format_git_status(data: dict) -> str:
    """Format git status response."""
    modified = data.get("modified", [])
    staged = data.get("staged", [])
    untracked = data.get("untracked", [])

    parts = []
    if staged:
        parts.append(f"{len(staged)} staged")
    if modified:
        parts.append(f"{len(modified)} modified")
    if untracked:
        parts.append(f"{len(untracked)} untracked")

    if not parts:
        return "Working tree clean"

    return ", ".join(parts)


def _format_issues(data: dict) -> str:
    """Format Linear/GitHub issues response."""
    issues = data.get("issues", data.get("items", []))
    if not issues:
        return "No issues"

    open_count = sum(1 for i in issues if i.get("state", "").lower() in ("open", "todo", "in_progress"))
    return f"{len(issues)} issues, {open_count} open"


def _format_tasks(data: dict) -> str:
    """Format tasks response."""
    tasks = data.get("tasks", data.get("items", []))
    if not tasks:
        return "No tasks"

    incomplete = sum(1 for t in tasks if not t.get("completed", False))
    if incomplete:
        return f"{len(tasks)} tasks, {incomplete} to do"
    return f"All {len(tasks)} tasks complete"
