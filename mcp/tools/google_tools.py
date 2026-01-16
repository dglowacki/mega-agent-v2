"""
Google Tools - Calendar, Tasks, and Gmail.

Provides Google Workspace integration for the voice assistant.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "integrations"))

logger = logging.getLogger(__name__)

_calendar_client = None
_tasks_client = None
_gmail_client = None


def _get_calendar():
    """Get Google Calendar client."""
    global _calendar_client
    if _calendar_client is None:
        try:
            from google_calendar_client import GoogleCalendarClient
            _calendar_client = GoogleCalendarClient()
        except Exception as e:
            logger.error(f"Failed to init Google Calendar: {e}")
            return None
    return _calendar_client


def _get_tasks():
    """Get Google Tasks client."""
    global _tasks_client
    if _tasks_client is None:
        try:
            from google_tasks_client import GoogleTasksClient
            _tasks_client = GoogleTasksClient()
        except Exception as e:
            logger.error(f"Failed to init Google Tasks: {e}")
            return None
    return _tasks_client


def _get_gmail():
    """Get Gmail client."""
    global _gmail_client
    if _gmail_client is None:
        try:
            from gmail_client import GmailClient
            _gmail_client = GmailClient()
        except Exception as e:
            logger.error(f"Failed to init Gmail: {e}")
            return None
    return _gmail_client


# Google Calendar Tools

def gcal_list_events(days: int = 7, calendar_id: str = "primary") -> str:
    """List upcoming Google Calendar events."""
    client = _get_calendar()
    if not client:
        return "Error: Google Calendar not configured"

    try:
        events = client.get_upcoming_events(days=days, calendar_id=calendar_id)

        if not events:
            return f"No events in the next {days} days"

        lines = [f"Calendar events (next {days} days):"]
        for event in events:
            start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date', ''))
            summary = event.get('summary', 'No title')
            lines.append(f"  - {start}: {summary}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error listing events: {str(e)}"


def gcal_create_event(
    title: str,
    start_time: str,
    end_time: str = None,
    description: str = "",
    location: str = "",
    calendar_id: str = "primary"
) -> str:
    """Create a Google Calendar event."""
    client = _get_calendar()
    if not client:
        return "Error: Google Calendar not configured"

    try:
        event = client.create_event(
            summary=title,
            start_time=start_time,
            end_time=end_time,
            description=description,
            location=location,
            calendar_id=calendar_id
        )

        if event:
            return f"Created event: {title}"
        return "Failed to create event"
    except Exception as e:
        return f"Error creating event: {str(e)}"


def gcal_search_events(query: str, days: int = 30) -> str:
    """Search Google Calendar events."""
    client = _get_calendar()
    if not client:
        return "Error: Google Calendar not configured"

    try:
        events = client.search_events(query=query, days=days)

        if not events:
            return f"No events matching '{query}'"

        lines = [f"Events matching '{query}':"]
        for event in events:
            start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date', ''))
            summary = event.get('summary', 'No title')
            lines.append(f"  - {start}: {summary}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error searching events: {str(e)}"


# Google Tasks Tools

def gtasks_list_tasks(list_name: str = None) -> str:
    """List Google Tasks."""
    client = _get_tasks()
    if not client:
        return "Error: Google Tasks not configured"

    try:
        tasks = client.get_tasks(list_name=list_name)

        if not tasks:
            return "No tasks found"

        lines = ["Google Tasks:"]
        for task in tasks:
            status = "✓" if task.get('status') == 'completed' else "○"
            title = task.get('title', 'No title')
            lines.append(f"  {status} {title}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error listing tasks: {str(e)}"


def gtasks_create_task(title: str, notes: str = "", list_name: str = None) -> str:
    """Create a Google Task."""
    client = _get_tasks()
    if not client:
        return "Error: Google Tasks not configured"

    try:
        task = client.create_task(title=title, notes=notes, list_name=list_name)

        if task:
            return f"Created task: {title}"
        return "Failed to create task"
    except Exception as e:
        return f"Error creating task: {str(e)}"


def gtasks_complete_task(task_id: str) -> str:
    """Mark a Google Task as complete."""
    client = _get_tasks()
    if not client:
        return "Error: Google Tasks not configured"

    try:
        result = client.complete_task(task_id)

        if result:
            return f"Completed task {task_id}"
        return f"Failed to complete task {task_id}"
    except Exception as e:
        return f"Error completing task: {str(e)}"


# Gmail Tools

def gmail_list_messages(query: str = "is:unread", limit: int = 10) -> str:
    """List Gmail messages."""
    client = _get_gmail()
    if not client:
        return "Error: Gmail not configured"

    try:
        messages = client.list_messages(query=query, max_results=limit)

        if not messages:
            return "No messages found"

        lines = [f"Gmail messages ({query}):"]
        for msg in messages:
            subject = msg.get('subject', 'No subject')
            sender = msg.get('from', 'Unknown')
            lines.append(f"  - From: {sender[:30]}")
            lines.append(f"    Subject: {subject[:50]}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error listing messages: {str(e)}"


def gmail_send(to: str, subject: str, body: str) -> str:
    """Send a Gmail message."""
    client = _get_gmail()
    if not client:
        return "Error: Gmail not configured"

    try:
        result = client.send_message(to=to, subject=subject, body=body)

        if result:
            return f"Email sent to {to}"
        return "Failed to send email"
    except Exception as e:
        return f"Error sending email: {str(e)}"


def gmail_search(query: str, limit: int = 10) -> str:
    """Search Gmail messages."""
    client = _get_gmail()
    if not client:
        return "Error: Gmail not configured"

    try:
        messages = client.search_messages(query=query, max_results=limit)

        if not messages:
            return f"No messages matching '{query}'"

        lines = [f"Gmail search results for '{query}':"]
        for msg in messages:
            subject = msg.get('subject', 'No subject')
            sender = msg.get('from', 'Unknown')
            lines.append(f"  - {sender[:20]}: {subject[:40]}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error searching: {str(e)}"


def register_google_tools(server) -> int:
    """Register Google tools."""

    # Calendar
    server.register_tool(
        name="gcal_list_events",
        description="List upcoming Google Calendar events.",
        input_schema={
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Days ahead", "default": 7},
                "calendar_id": {"type": "string", "description": "Calendar ID", "default": "primary"}
            }
        },
        handler=gcal_list_events,
        requires_approval=False,
        category="google"
    )

    server.register_tool(
        name="gcal_create_event",
        description="Create a Google Calendar event.",
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Event title"},
                "start_time": {"type": "string", "description": "Start time (ISO format or natural)"},
                "end_time": {"type": "string", "description": "End time"},
                "description": {"type": "string", "description": "Event description"},
                "location": {"type": "string", "description": "Event location"},
                "calendar_id": {"type": "string", "description": "Calendar ID", "default": "primary"}
            },
            "required": ["title", "start_time"]
        },
        handler=gcal_create_event,
        requires_approval=True,
        category="google"
    )

    server.register_tool(
        name="gcal_search_events",
        description="Search Google Calendar events.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "days": {"type": "integer", "description": "Days to search", "default": 30}
            },
            "required": ["query"]
        },
        handler=gcal_search_events,
        requires_approval=False,
        category="google"
    )

    # Tasks
    server.register_tool(
        name="gtasks_list_tasks",
        description="List Google Tasks.",
        input_schema={
            "type": "object",
            "properties": {
                "list_name": {"type": "string", "description": "Task list name"}
            }
        },
        handler=gtasks_list_tasks,
        requires_approval=False,
        category="google"
    )

    server.register_tool(
        name="gtasks_create_task",
        description="Create a Google Task.",
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Task title"},
                "notes": {"type": "string", "description": "Task notes"},
                "list_name": {"type": "string", "description": "Task list name"}
            },
            "required": ["title"]
        },
        handler=gtasks_create_task,
        requires_approval=True,
        category="google"
    )

    server.register_tool(
        name="gtasks_complete_task",
        description="Mark a Google Task as complete.",
        input_schema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task ID"}
            },
            "required": ["task_id"]
        },
        handler=gtasks_complete_task,
        requires_approval=True,
        category="google"
    )

    # Gmail
    server.register_tool(
        name="gmail_list_messages",
        description="List Gmail messages (default: unread).",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Gmail query", "default": "is:unread"},
                "limit": {"type": "integer", "description": "Max messages", "default": 10}
            }
        },
        handler=gmail_list_messages,
        requires_approval=False,
        category="google"
    )

    server.register_tool(
        name="gmail_send",
        description="Send an email via Gmail.",
        input_schema={
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email"},
                "subject": {"type": "string", "description": "Email subject"},
                "body": {"type": "string", "description": "Email body"}
            },
            "required": ["to", "subject", "body"]
        },
        handler=gmail_send,
        requires_approval=True,
        category="google"
    )

    server.register_tool(
        name="gmail_search",
        description="Search Gmail messages.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results", "default": 10}
            },
            "required": ["query"]
        },
        handler=gmail_search,
        requires_approval=False,
        category="google"
    )

    return 9
