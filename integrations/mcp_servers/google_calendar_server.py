"""
Google Calendar MCP Server for Claude Agent SDK

Exposes Google Calendar operations as MCP tools that agents can use directly.
"""

import os
import sys
from pathlib import Path

# Add integrations to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_agent_sdk import create_sdk_mcp_server, tool
from google_calendar_client import GoogleCalendarClient


@tool(
    name="calendar_list_events",
    description="List upcoming calendar events",
    input_schema={
        "type": "object",
        "properties": {
            "calendar_id": {
                "type": "string",
                "description": "Calendar ID (default: 'primary')",
                "default": "primary"
            },
            "max_results": {
                "type": "number",
                "description": "Maximum number of events to return",
                "default": 10
            },
            "days_ahead": {
                "type": "number",
                "description": "Number of days ahead to fetch events",
                "default": 7
            },
            "user_email": {
                "type": "string",
                "description": "Email to impersonate (requires domain-wide delegation)"
            }
        }
    }
)
async def calendar_list_events(args):
    """List upcoming calendar events."""
    try:
        user_email = args.get("user_email")
        client = GoogleCalendarClient(user_email=user_email)

        calendar_id = args.get("calendar_id", "primary")
        max_results = args.get("max_results", 10)
        days_ahead = args.get("days_ahead", 7)

        events = await client.list_events(
            calendar_id=calendar_id,
            max_results=max_results,
            days_ahead=days_ahead
        )

        event_lines = [f"Found {len(events)} upcoming events:\n"]
        for event in events:
            summary = event.get("summary", "No title")
            start = event.get("start", {}).get("dateTime", event.get("start", {}).get("date", "No start time"))
            event_lines.append(f"- {summary} @ {start}")

        return {
            "content": [{
                "type": "text",
                "text": "\n".join(event_lines)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to list events: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="calendar_create_event",
    description="Create a calendar event",
    input_schema={
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "Event title"
            },
            "start_time": {
                "type": "string",
                "description": "Start time (ISO format, e.g., '2024-12-25T10:00:00')"
            },
            "end_time": {
                "type": "string",
                "description": "End time (ISO format)"
            },
            "description": {
                "type": "string",
                "description": "Event description"
            },
            "attendees": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of attendee email addresses"
            },
            "location": {
                "type": "string",
                "description": "Event location"
            },
            "calendar_id": {
                "type": "string",
                "description": "Calendar ID",
                "default": "primary"
            },
            "user_email": {
                "type": "string",
                "description": "Email to impersonate"
            }
        },
        "required": ["summary", "start_time", "end_time"]
    }
)
async def calendar_create_event(args):
    """Create a calendar event."""
    try:
        user_email = args.get("user_email")
        client = GoogleCalendarClient(user_email=user_email)

        event = await client.create_event(
            summary=args["summary"],
            start_time=args["start_time"],
            end_time=args["end_time"],
            description=args.get("description", ""),
            calendar_id=args.get("calendar_id", "primary"),
            attendees=args.get("attendees"),
            location=args.get("location")
        )

        return {
            "content": [{
                "type": "text",
                "text": f"✓ Event created: {event.get('summary', 'Untitled')}\n"
                       f"Event ID: {event.get('id')}\n"
                       f"Link: {event.get('htmlLink', 'N/A')}"
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to create event: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="calendar_find_free_time",
    description="Find free time slots in calendars",
    input_schema={
        "type": "object",
        "properties": {
            "start_time": {
                "type": "string",
                "description": "Start of search window (ISO format)"
            },
            "end_time": {
                "type": "string",
                "description": "End of search window (ISO format)"
            },
            "duration_minutes": {
                "type": "number",
                "description": "Required slot duration in minutes",
                "default": 30
            },
            "user_email": {
                "type": "string",
                "description": "Email to impersonate"
            }
        },
        "required": ["start_time", "end_time"]
    }
)
async def calendar_find_free_time(args):
    """Find free time slots."""
    try:
        user_email = args.get("user_email")
        client = GoogleCalendarClient(user_email=user_email)

        free_slots = await client.find_free_time(
            start_time=args["start_time"],
            end_time=args["end_time"],
            duration_minutes=args.get("duration_minutes", 30)
        )

        slot_lines = [f"Found {len(free_slots)} free time slots:\n"]
        for slot in free_slots[:10]:  # Limit to first 10
            slot_lines.append(f"- {slot.get('start')} to {slot.get('end')}")

        return {
            "content": [{
                "type": "text",
                "text": "\n".join(slot_lines)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to find free time: {str(e)}"
            }],
            "isError": True
        }


# Create and export the MCP server
google_calendar_mcp_server = create_sdk_mcp_server(
    name="google_calendar",
    version="1.0.0",
    tools=[
        calendar_list_events,
        calendar_create_event,
        calendar_find_free_time
    ]
)
