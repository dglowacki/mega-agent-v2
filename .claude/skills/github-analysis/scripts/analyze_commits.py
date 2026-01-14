#!/usr/bin/env python3
"""
Analyze GitHub commits and generate metrics.

Usage:
    python analyze_commits.py commits.json --output analysis.json
"""

import json
import sys
import re
from datetime import datetime
from collections import defaultdict


def analyze_commit_message(message):
    """Score commit message quality (0-10)."""
    message = message.strip().lower()

    # Bad patterns
    if message in ['wip', 'test', 'fix', 'update', '.']:
        return 0
    if len(message) < 10:
        return 2

    # Good patterns
    score = 5  # Base score

    # Has context (why)
    why_words = ['because', 'to', 'for', 'so that', 'fixes', 'addresses']
    if any(word in message for word in why_words):
        score += 2

    # Follows convention (type: description)
    if re.match(r'^(feat|fix|docs|style|refactor|test|chore):', message):
        score += 2

    # Has detail
    if len(message) > 50:
        score += 1

    return min(score, 10)


def analyze_commits(commits_data):
    """Analyze commit data and generate metrics."""

    # Initialize metrics
    contributors = defaultdict(lambda: {
        'name': '',
        'email': '',
        'commits': 0,
        'lines_added': 0,
        'lines_deleted': 0,
        'lines_changed': 0,
        'files_changed': set(),
        'quality_scores': [],
        'commits_detail': []
    })

    file_changes = defaultdict(int)
    total_stats = {
        'total_commits': len(commits_data),
        'total_contributors': 0,
        'total_files': 0,
        'total_lines_added': 0,
        'total_lines_deleted': 0
    }

    # Process each commit
    for commit in commits_data:
        author = commit.get('author', 'Unknown')
        email = commit.get('email', '')

        # Update contributor stats
        contrib = contributors[author]
        contrib['name'] = author
        contrib['email'] = email
        contrib['commits'] += 1
        contrib['lines_added'] += commit.get('additions', 0)
        contrib['lines_deleted'] += commit.get('deletions', 0)
        contrib['lines_changed'] += commit.get('additions', 0) + commit.get('deletions', 0)

        # Analyze commit message
        message = commit.get('message', '')
        quality = analyze_commit_message(message)
        contrib['quality_scores'].append(quality)

        # Track files
        for file in commit.get('files_changed', []):
            contrib['files_changed'].add(file)
            file_changes[file] += 1

        # Store commit detail
        contrib['commits_detail'].append({
            'sha': commit.get('sha', '')[:7],
            'message': message,
            'quality': quality,
            'date': commit.get('date', '')
        })

        # Update totals
        total_stats['total_lines_added'] += commit.get('additions', 0)
        total_stats['total_lines_deleted'] += commit.get('deletions', 0)

    # Calculate averages and scores
    contributor_list = []
    for author, data in contributors.items():
        avg_quality = sum(data['quality_scores']) / len(data['quality_scores']) if data['quality_scores'] else 0

        # Calculate score
        score = (
            data['commits'] * 1.0 +
            data['lines_changed'] / 100 * 0.5 +
            avg_quality * 2.0
        )

        contributor_list.append({
            'name': data['name'],
            'email': data['email'],
            'commits': data['commits'],
            'lines_added': data['lines_added'],
            'lines_deleted': data['lines_deleted'],
            'lines_changed': data['lines_changed'],
            'files_changed': len(data['files_changed']),
            'avg_quality': round(avg_quality, 1),
            'score': round(score, 1),
            'commits_detail': data['commits_detail']
        })

    # Sort by score
    contributor_list.sort(key=lambda x: x['score'], reverse=True)

    # Get hot files (most changed)
    hot_files = sorted(
        [{'file': f, 'changes': c} for f, c in file_changes.items()],
        key=lambda x: x['changes'],
        reverse=True
    )[:20]

    # Update totals
    total_stats['total_contributors'] = len(contributor_list)
    total_stats['total_files'] = len(file_changes)

    return {
        'summary': total_stats,
        'contributors': contributor_list,
        'hot_files': hot_files,
        'generated_at': datetime.now().isoformat()
    }


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Analyze GitHub commits')
    parser.add_argument('input', help='Input commits JSON file')
    parser.add_argument('--output', default='analysis.json', help='Output analysis file')
    args = parser.parse_args()

    # Load commits
    with open(args.input) as f:
        commits = json.load(f)

    # Analyze
    analysis = analyze_commits(commits)

    # Save
    with open(args.output, 'w') as f:
        json.dump(analysis, f, indent=2)

    print(f"✓ Analyzed {analysis['summary']['total_commits']} commits")
    print(f"✓ {analysis['summary']['total_contributors']} contributors")
    print(f"✓ Saved to {args.output}")


if __name__ == '__main__':
    main()
