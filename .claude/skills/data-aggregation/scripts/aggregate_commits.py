#!/usr/bin/env python3
"""
Aggregate GitHub commit data.

Usage:
    python aggregate_commits.py --input commits.json --period week --output summary.json
"""

import argparse
import json
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Any


def aggregate_by_author(commits: List[Dict]) -> Dict:
    """Aggregate commits by author."""
    aggregated = defaultdict(lambda: {
        'commits': 0,
        'lines_added': 0,
        'lines_deleted': 0,
        'files_changed': 0,
        'email': ''
    })

    for commit in commits:
        # Extract author info
        author = commit.get('commit', {}).get('author', {})
        author_name = author.get('name', 'Unknown')
        author_email = author.get('email', '')

        # Extract stats
        stats = commit.get('stats', {})
        additions = stats.get('additions', 0)
        deletions = stats.get('deletions', 0)
        total = stats.get('total', additions + deletions)

        files = commit.get('files', [])
        file_count = len(files) if files else 0

        # Aggregate
        aggregated[author_name]['commits'] += 1
        aggregated[author_name]['lines_added'] += additions
        aggregated[author_name]['lines_deleted'] += deletions
        aggregated[author_name]['files_changed'] += file_count
        aggregated[author_name]['email'] = author_email

    return dict(aggregated)


def aggregate_by_time(commits: List[Dict], period: str = 'day') -> Dict:
    """Aggregate commits by time period."""
    aggregated = defaultdict(lambda: {
        'commits': 0,
        'lines': 0,
        'files': 0
    })

    for commit in commits:
        # Parse date
        author = commit.get('commit', {}).get('author', {})
        date_str = author.get('date', '')

        if not date_str:
            continue

        # Parse ISO 8601
        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))

        # Determine period key
        if period == 'day':
            key = date.strftime('%Y-%m-%d')
        elif period == 'week':
            start = date - timedelta(days=date.weekday())
            key = start.strftime('%Y-%m-%d')
        elif period == 'month':
            key = date.strftime('%Y-%m')
        else:
            key = date_str

        # Extract stats
        stats = commit.get('stats', {})
        additions = stats.get('additions', 0)
        deletions = stats.get('deletions', 0)

        files = commit.get('files', [])
        file_count = len(files) if files else 0

        # Aggregate
        aggregated[key]['commits'] += 1
        aggregated[key]['lines'] += additions + deletions
        aggregated[key]['files'] += file_count

    return dict(aggregated)


def calculate_summary(commits: List[Dict]) -> Dict:
    """Calculate summary statistics."""
    if not commits:
        return {}

    total_commits = len(commits)
    total_lines_added = 0
    total_lines_deleted = 0
    total_files = 0
    authors = set()

    for commit in commits:
        # Stats
        stats = commit.get('stats', {})
        total_lines_added += stats.get('additions', 0)
        total_lines_deleted += stats.get('deletions', 0)

        files = commit.get('files', [])
        total_files += len(files) if files else 0

        # Authors
        author = commit.get('commit', {}).get('author', {})
        author_name = author.get('name')
        if author_name:
            authors.add(author_name)

    return {
        'total_commits': total_commits,
        'total_contributors': len(authors),
        'total_lines_added': total_lines_added,
        'total_lines_deleted': total_lines_deleted,
        'total_lines': total_lines_added + total_lines_deleted,
        'total_files': total_files
    }


def aggregate_commits(commits: List[Dict], period: str = 'week', metrics: List[str] = None) -> Dict:
    """
    Aggregate commit data.

    Args:
        commits: List of commit objects from GitHub API
        period: Time period (day, week, month)
        metrics: Metrics to calculate (author, time, summary)

    Returns:
        Aggregated data dictionary
    """
    if not metrics:
        metrics = ['summary', 'author', 'time']

    result = {
        'period': period
    }

    if 'summary' in metrics:
        result['summary'] = calculate_summary(commits)

    if 'author' in metrics or 'commits' in metrics:
        result['by_author'] = aggregate_by_author(commits)

    if 'time' in metrics:
        result['by_day'] = aggregate_by_time(commits, period)

    return result


def main():
    parser = argparse.ArgumentParser(description='Aggregate GitHub commit data')
    parser.add_argument('--input', required=True, help='Input JSON file with commits')
    parser.add_argument('--period', default='week', choices=['day', 'week', 'month'], help='Time period')
    parser.add_argument('--metrics', default='summary,author,time', help='Metrics to calculate (comma-separated)')
    parser.add_argument('--output', help='Output JSON file')

    args = parser.parse_args()

    # Load commits
    with open(args.input, 'r') as f:
        commits = json.load(f)

    # Parse metrics
    metrics = [m.strip() for m in args.metrics.split(',')]

    # Aggregate
    result = aggregate_commits(commits, args.period, metrics)

    # Output
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"✓ Aggregated data saved to {args.output}")
    else:
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
