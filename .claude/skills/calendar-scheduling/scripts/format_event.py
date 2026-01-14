#!/usr/bin/env python3
"""
Format a calendar event for Google Calendar API.

Usage:
    python format_event.py --title "Meeting" --start "2026-01-20 14:00" --duration "1h" --output event.json
"""

import argparse
import json
from datetime import datetime, timedelta
from typing import Dict, List


def parse_duration(duration_str: str) -> int:
    """
    Parse duration string to minutes.

    Examples:
        "30m" → 30
        "1h" → 60
        "1h30m" → 90
        "2h" → 120
    """
    duration_str = duration_str.lower().strip()
    total_minutes = 0

    # Parse hours
    if 'h' in duration_str:
        parts = duration_str.split('h')
        hours = int(parts[0])
        total_minutes += hours * 60
        duration_str = parts[1] if len(parts) > 1 else ""

    # Parse minutes
    if 'm' in duration_str:
        minutes = int(duration_str.replace('m', ''))
        total_minutes += minutes
    elif duration_str and not total_minutes:
        # Assume minutes if no unit
        total_minutes = int(duration_str)

    return total_minutes


def format_event(
    title: str,
    start: str,
    duration: str = "1h",
    attendees: List[str] = None,
    location: str = None,
    description: str = None,
    reminder_minutes: int = 15,
    timezone: str = "America/Los_Angeles"
) -> Dict:
    """
    Format a calendar event for Google Calendar API.

    Args:
        title: Event title
        start: Start date/time (YYYY-MM-DD HH:MM)
        duration: Duration (e.g., "1h", "30m")
        attendees: List of attendee email addresses
        location: Meeting location or video link
        description: Event description
        reminder_minutes: Minutes before event for reminder
        timezone: Timezone for event

    Returns:
        Dictionary formatted for Google Calendar API
    """
    # Parse start time
    try:
        start_dt = datetime.strptime(start, '%Y-%m-%d %H:%M')
    except ValueError:
        # Try date only (all-day event)
        start_dt = datetime.strptime(start, '%Y-%m-%d')
        is_all_day = True
    else:
        is_all_day = False

    # Calculate end time
    duration_minutes = parse_duration(duration)
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    # Build event
    event = {
        'summary': title
    }

    # Add date/time
    if is_all_day:
        event['start'] = {
            'date': start_dt.strftime('%Y-%m-%d')
        }
        event['end'] = {
            'date': end_dt.strftime('%Y-%m-%d')
        }
    else:
        event['start'] = {
            'dateTime': start_dt.isoformat(),
            'timeZone': timezone
        }
        event['end'] = {
            'dateTime': end_dt.isoformat(),
            'timeZone': timezone
        }

    # Add optional fields
    if description:
        event['description'] = description

    if location:
        event['location'] = location

    if attendees:
        event['attendees'] = [{'email': email} for email in attendees]

    # Add reminders
    if reminder_minutes:
        event['reminders'] = {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': reminder_minutes}
            ]
        }

    return event


def main():
    parser = argparse.ArgumentParser(description='Format calendar event')
    parser.add_argument('--title', required=True, help='Event title')
    parser.add_argument('--start', required=True, help='Start date/time (YYYY-MM-DD HH:MM)')
    parser.add_argument('--duration', default='1h', help='Duration (e.g., 1h, 30m)')
    parser.add_argument('--attendees', help='Comma-separated email addresses')
    parser.add_argument('--location', help='Location or video link')
    parser.add_argument('--description', help='Event description')
    parser.add_argument('--reminder', type=int, default=15, help='Reminder minutes before event')
    parser.add_argument('--timezone', default='America/Los_Angeles', help='Timezone')
    parser.add_argument('--output', help='Output JSON file')

    args = parser.parse_args()

    # Parse attendees
    attendees = None
    if args.attendees:
        attendees = [email.strip() for email in args.attendees.split(',')]

    # Format event
    event = format_event(
        title=args.title,
        start=args.start,
        duration=args.duration,
        attendees=attendees,
        location=args.location,
        description=args.description,
        reminder_minutes=args.reminder,
        timezone=args.timezone
    )

    # Output
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(event, f, indent=2)
        print(f"✓ Event formatted and saved to {args.output}")
    else:
        print(json.dumps(event, indent=2))


if __name__ == '__main__':
    main()
