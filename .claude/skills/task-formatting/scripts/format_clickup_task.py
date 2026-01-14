#!/usr/bin/env python3
"""
Format a task for ClickUp.

Usage:
    python format_clickup_task.py --title "Add feature" --description desc.md --priority high --output task.json
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


def parse_time_estimate(estimate_str: str) -> int:
    """
    Parse time estimate string to milliseconds.

    Examples:
        "30m" → 1,800,000
        "2h" → 7,200,000
        "1d" → 28,800,000 (8 hours)
        "2d" → 57,600,000 (16 hours)
    """
    estimate_str = estimate_str.lower().strip()

    # Parse number and unit
    if estimate_str.endswith('m'):
        minutes = int(estimate_str[:-1])
        return minutes * 60 * 1000
    elif estimate_str.endswith('h'):
        hours = float(estimate_str[:-1])
        return int(hours * 60 * 60 * 1000)
    elif estimate_str.endswith('d'):
        days = float(estimate_str[:-1])
        return int(days * 8 * 60 * 60 * 1000)  # 8 hours per day
    else:
        # Assume minutes
        return int(estimate_str) * 60 * 1000


def format_clickup_task(
    title: str,
    description: str = "",
    priority: str = "normal",
    tags: list = None,
    due_date: str = None,
    time_estimate: str = None,
    status: str = "to do"
) -> Dict:
    """
    Format a task for ClickUp API.

    Args:
        title: Task title
        description: Task description (markdown supported)
        priority: Priority level (urgent, high, normal, low)
        tags: List of tags
        due_date: Due date (YYYY-MM-DD format)
        time_estimate: Time estimate (e.g., "4h", "2d")
        status: Task status

    Returns:
        Dictionary formatted for ClickUp API
    """
    # Map priority to ClickUp values
    priority_map = {
        'urgent': 1,
        'high': 2,
        'normal': 3,
        'low': 4
    }

    task = {
        'name': title,
        'description': description,
        'status': status
    }

    # Add priority
    if priority.lower() in priority_map:
        task['priority'] = priority_map[priority.lower()]

    # Add tags
    if tags:
        task['tags'] = tags

    # Add due date (convert to Unix timestamp in milliseconds)
    if due_date:
        try:
            dt = datetime.strptime(due_date, '%Y-%m-%d')
            task['due_date'] = int(dt.timestamp() * 1000)
        except ValueError:
            pass  # Skip invalid date

    # Add time estimate
    if time_estimate:
        try:
            task['time_estimate'] = parse_time_estimate(time_estimate)
        except ValueError:
            pass  # Skip invalid estimate

    return task


def main():
    parser = argparse.ArgumentParser(description='Format ClickUp task')
    parser.add_argument('--title', required=True, help='Task title')
    parser.add_argument('--description', help='Description text or markdown file')
    parser.add_argument('--priority', default='normal', choices=['urgent', 'high', 'normal', 'low'], help='Priority level')
    parser.add_argument('--tags', help='Comma-separated tags')
    parser.add_argument('--due-date', help='Due date (YYYY-MM-DD)')
    parser.add_argument('--estimate', help='Time estimate (e.g., 4h, 2d)')
    parser.add_argument('--status', default='to do', help='Task status')
    parser.add_argument('--output', help='Output JSON file')

    args = parser.parse_args()

    # Load description if it's a file
    description = ""
    if args.description:
        desc_path = Path(args.description)
        if desc_path.exists():
            with open(desc_path, 'r') as f:
                description = f.read()
        else:
            description = args.description

    # Parse tags
    tags = None
    if args.tags:
        tags = [tag.strip() for tag in args.tags.split(',')]

    # Format task
    task = format_clickup_task(
        title=args.title,
        description=description,
        priority=args.priority,
        tags=tags,
        due_date=args.due_date,
        time_estimate=args.estimate,
        status=args.status
    )

    # Output
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(task, f, indent=2)
        print(f"✓ Task formatted and saved to {args.output}")
    else:
        print(json.dumps(task, indent=2))


if __name__ == '__main__':
    main()
