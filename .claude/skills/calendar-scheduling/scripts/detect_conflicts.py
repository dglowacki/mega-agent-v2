#!/usr/bin/env python3
"""
Detect scheduling conflicts between events.

Usage:
    python detect_conflicts.py --events existing_events.json --new-event new_event.json --buffer 15
"""

import argparse
import json
from datetime import datetime, timedelta
from typing import Dict, List


def parse_event_time(event: Dict) -> tuple:
    """
    Parse event start and end times.

    Returns: (start_datetime, end_datetime)
    """
    start = event.get('start', {})
    end = event.get('end', {})

    # Handle date vs dateTime
    if 'dateTime' in start:
        start_dt = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end['dateTime'].replace('Z', '+00:00'))
    elif 'date' in start:
        # All-day event
        start_dt = datetime.strptime(start['date'], '%Y-%m-%d')
        end_dt = datetime.strptime(end['date'], '%Y-%m-%d')
    else:
        raise ValueError("Event missing start time")

    return start_dt, end_dt


def detect_conflicts(
    existing_events: List[Dict],
    new_event: Dict,
    buffer_minutes: int = 0
) -> Dict:
    """
    Detect scheduling conflicts.

    Args:
        existing_events: List of existing calendar events
        new_event: New event to check
        buffer_minutes: Required buffer time between events

    Returns:
        Dictionary with conflict information
    """
    new_start, new_end = parse_event_time(new_event)

    # Apply buffer to new event
    if buffer_minutes > 0:
        buffer = timedelta(minutes=buffer_minutes)
        new_start_buffered = new_start - buffer
        new_end_buffered = new_end + buffer
    else:
        new_start_buffered = new_start
        new_end_buffered = new_end

    hard_conflicts = []
    soft_conflicts = []

    for event in existing_events:
        try:
            event_start, event_end = parse_event_time(event)
        except ValueError:
            continue  # Skip invalid events

        # Check for hard conflict (overlapping time)
        if new_start < event_end and new_end > event_start:
            hard_conflicts.append({
                'event': event.get('summary', 'Unnamed Event'),
                'start': event_start.isoformat(),
                'end': event_end.isoformat(),
                'reason': 'Overlapping time slot'
            })

        # Check for soft conflict (insufficient buffer)
        elif buffer_minutes > 0:
            # Check if events are adjacent without buffer
            if new_start_buffered < event_end and new_end_buffered > event_start:
                soft_conflicts.append({
                    'event': event.get('summary', 'Unnamed Event'),
                    'start': event_start.isoformat(),
                    'end': event_end.isoformat(),
                    'reason': f'Insufficient buffer (need {buffer_minutes} minutes)'
                })

    result = {
        'has_conflicts': len(hard_conflicts) > 0,
        'hard_conflicts': hard_conflicts,
        'soft_conflicts': soft_conflicts,
        'new_event': {
            'title': new_event.get('summary', 'Unnamed Event'),
            'start': new_start.isoformat(),
            'end': new_end.isoformat()
        }
    }

    return result


def main():
    parser = argparse.ArgumentParser(description='Detect scheduling conflicts')
    parser.add_argument('--events', required=True, help='JSON file with existing events')
    parser.add_argument('--new-event', required=True, help='JSON file with new event')
    parser.add_argument('--buffer', type=int, default=0, help='Required buffer minutes between events')

    args = parser.parse_args()

    # Load events
    with open(args.events, 'r') as f:
        existing_events = json.load(f)
        # Handle both array and object with events array
        if isinstance(existing_events, dict) and 'events' in existing_events:
            existing_events = existing_events['events']

    with open(args.new_event, 'r') as f:
        new_event = json.load(f)

    # Detect conflicts
    result = detect_conflicts(existing_events, new_event, args.buffer)

    # Output
    print(json.dumps(result, indent=2))

    # Return exit code based on conflicts
    return 1 if result['has_conflicts'] else 0


if __name__ == '__main__':
    exit(main())
