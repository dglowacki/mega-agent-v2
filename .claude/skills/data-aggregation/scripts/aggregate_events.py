#!/usr/bin/env python3
"""
Aggregate Skillz event data.

Usage:
    python aggregate_events.py --input events/ --status active,completed --output summary.json
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any


def load_events(input_path: str, status_filter: List[str] = None) -> List[Dict]:
    """Load event JSON files from directory."""
    path = Path(input_path)
    events = []

    if path.is_file():
        with open(path, 'r') as f:
            event = json.load(f)
            events.append(event)
    elif path.is_dir():
        # Load all JSON files
        for file_path in path.glob('event_*_*.json'):
            with open(file_path, 'r') as f:
                event = json.load(f)

                # Filter by status if provided
                if status_filter:
                    event_status = file_path.stem.split('_')[-1]  # e.g., "active", "completed"
                    if event_status not in status_filter:
                        continue

                events.append(event)

    return events


def aggregate_by_status(events: List[Dict]) -> Dict:
    """Aggregate events by status."""
    aggregated = defaultdict(lambda: {
        'count': 0,
        'prize_pool': 0,
        'entries': 0
    })

    for event in events:
        status = event.get('status', 'unknown')
        prize_pool = event.get('prize_pool', 0)
        entries = event.get('entries', 0)

        aggregated[status]['count'] += 1
        aggregated[status]['prize_pool'] += prize_pool
        aggregated[status]['entries'] += entries

    return dict(aggregated)


def calculate_summary(events: List[Dict]) -> Dict:
    """Calculate summary statistics."""
    if not events:
        return {}

    total_events = len(events)
    total_prize_pool = sum(event.get('prize_pool', 0) for event in events)
    total_entries = sum(event.get('entries', 0) for event in events)

    # Average metrics
    avg_prize_pool = total_prize_pool / total_events if total_events > 0 else 0
    avg_entries = total_entries / total_events if total_events > 0 else 0

    return {
        'total_events': total_events,
        'total_prize_pool': total_prize_pool,
        'total_entries': total_entries,
        'avg_prize_pool': round(avg_prize_pool, 2),
        'avg_entries': round(avg_entries, 2)
    }


def aggregate_events(input_path: str, status_filter: List[str] = None) -> Dict:
    """
    Aggregate Skillz event data.

    Args:
        input_path: Path to event file or directory
        status_filter: List of statuses to include

    Returns:
        Aggregated data dictionary
    """
    # Load events
    events = load_events(input_path, status_filter)

    if not events:
        return {'error': 'No events found'}

    # Calculate aggregations
    summary = calculate_summary(events)
    by_status = aggregate_by_status(events)

    # Top events by prize pool
    top_events = sorted(events, key=lambda e: e.get('prize_pool', 0), reverse=True)[:5]

    return {
        'summary': summary,
        'by_status': by_status,
        'top_events': [
            {
                'event_id': e.get('event_id'),
                'name': e.get('name'),
                'prize_pool': e.get('prize_pool'),
                'entries': e.get('entries')
            }
            for e in top_events
        ]
    }


def main():
    parser = argparse.ArgumentParser(description='Aggregate Skillz event data')
    parser.add_argument('--input', required=True, help='Input file or directory')
    parser.add_argument('--status', help='Filter by status (comma-separated)')
    parser.add_argument('--output', help='Output JSON file')

    args = parser.parse_args()

    # Parse status filter
    status_filter = None
    if args.status:
        status_filter = [s.strip() for s in args.status.split(',')]

    # Aggregate
    result = aggregate_events(args.input, status_filter)

    # Output
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"✓ Aggregated data saved to {args.output}")
    else:
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
