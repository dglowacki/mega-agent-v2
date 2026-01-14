#!/usr/bin/env python3
"""
Format an issue for Linear.

Usage:
    python format_linear_issue.py --title "Fix bug" --team-id abc123 --priority urgent --output issue.json
"""

import argparse
import json
from pathlib import Path
from typing import Dict


def format_linear_issue(
    title: str,
    team_id: str,
    description: str = "",
    priority: str = "normal",
    labels: list = None,
    estimate: int = None,
    state: str = None
) -> Dict:
    """
    Format an issue for Linear API.

    Args:
        title: Issue title
        team_id: Team ID (required by Linear)
        description: Issue description (markdown supported)
        priority: Priority level (urgent, high, normal, low, none)
        labels: List of label names
        estimate: Story points (1-8)
        state: State name (Backlog, Todo, In Progress, etc.)

    Returns:
        Dictionary formatted for Linear GraphQL API
    """
    # Map priority to Linear values
    priority_map = {
        'none': 0,
        'urgent': 1,
        'high': 2,
        'normal': 3,
        'low': 4
    }

    issue = {
        'title': title,
        'teamId': team_id
    }

    # Add description
    if description:
        issue['description'] = description

    # Add priority
    if priority.lower() in priority_map:
        issue['priority'] = priority_map[priority.lower()]

    # Add labels (note: Linear uses label IDs, but we can pass names to be resolved)
    if labels:
        issue['labels'] = labels

    # Add estimate (story points)
    if estimate is not None:
        if 1 <= estimate <= 8:
            issue['estimate'] = estimate

    # Add state
    if state:
        issue['state'] = state

    return issue


def main():
    parser = argparse.ArgumentParser(description='Format Linear issue')
    parser.add_argument('--title', required=True, help='Issue title')
    parser.add_argument('--team-id', required=True, help='Team ID')
    parser.add_argument('--description', help='Description text or markdown file')
    parser.add_argument('--priority', default='normal', choices=['none', 'urgent', 'high', 'normal', 'low'], help='Priority level')
    parser.add_argument('--labels', help='Comma-separated labels')
    parser.add_argument('--estimate', type=int, help='Story points (1-8)')
    parser.add_argument('--state', help='State name')
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

    # Parse labels
    labels = None
    if args.labels:
        labels = [label.strip() for label in args.labels.split(',')]

    # Format issue
    issue = format_linear_issue(
        title=args.title,
        team_id=args.team_id,
        description=description,
        priority=args.priority,
        labels=labels,
        estimate=args.estimate,
        state=args.state
    )

    # Output
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(issue, f, indent=2)
        print(f"✓ Issue formatted and saved to {args.output}")
    else:
        print(json.dumps(issue, indent=2))


if __name__ == '__main__':
    main()
