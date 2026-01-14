#!/usr/bin/env python3
"""
Calculate contributor leaderboard from commit data.

Usage:
    python calculate_leaderboard.py commits.json --period week --output leaderboard.json
"""

import json
import sys
from datetime import datetime, timedelta
from collections import defaultdict


def calculate_leaderboard(commits_data, period="week"):
    """
    Calculate contributor leaderboard with weighted scoring.

    Scoring formula:
    Total Score = (commits × 1) +
                  (lines_changed / 100 × 0.5) +
                  (avg_quality × 2) +
                  (pr_reviews × 1.5) +
                  (10 - avg_response_hours × 1)
    """

    # Filter by period
    if period == "week":
        cutoff = datetime.now() - timedelta(days=7)
    elif period == "month":
        cutoff = datetime.now() - timedelta(days=30)
    elif period == "year":
        cutoff = datetime.now() - timedelta(days=365)
    else:
        cutoff = None  # All time

    # Filter commits by date
    if cutoff:
        filtered_commits = [
            c for c in commits_data
            if datetime.fromisoformat(c.get('date', '').replace('Z', '+00:00')) >= cutoff
        ]
    else:
        filtered_commits = commits_data

    # Aggregate by contributor
    contributors = defaultdict(lambda: {
        'name': '',
        'email': '',
        'commits': 0,
        'lines_added': 0,
        'lines_deleted': 0,
        'lines_changed': 0,
        'quality_scores': [],
        'pr_reviews': 0,
        'response_times': []
    })

    for commit in filtered_commits:
        author = commit.get('author', 'Unknown')
        email = commit.get('email', '')

        contrib = contributors[author]
        contrib['name'] = author
        contrib['email'] = email
        contrib['commits'] += 1
        contrib['lines_added'] += commit.get('additions', 0)
        contrib['lines_deleted'] += commit.get('deletions', 0)
        contrib['lines_changed'] += commit.get('additions', 0) + commit.get('deletions', 0)

        # Quality score (if available from analysis)
        if 'quality' in commit:
            contrib['quality_scores'].append(commit['quality'])

        # PR review count (if available)
        if 'pr_reviews' in commit:
            contrib['pr_reviews'] += commit['pr_reviews']

        # Response time (if available)
        if 'response_time_hours' in commit:
            contrib['response_times'].append(commit['response_time_hours'])

    # Calculate scores
    leaderboard = []
    for author, data in contributors.items():
        # Calculate averages
        avg_quality = sum(data['quality_scores']) / len(data['quality_scores']) if data['quality_scores'] else 5.0
        avg_response = sum(data['response_times']) / len(data['response_times']) if data['response_times'] else 5.0

        # Calculate total score
        score = (
            data['commits'] * 1.0 +
            data['lines_changed'] / 100 * 0.5 +
            avg_quality * 2.0 +
            data['pr_reviews'] * 1.5 +
            (10 - avg_response) * 1.0
        )

        leaderboard.append({
            'rank': 0,  # Will be filled after sorting
            'contributor': data['name'],
            'email': data['email'],
            'score': round(score, 1),
            'commits': data['commits'],
            'lines_changed': data['lines_changed'],
            'lines_added': data['lines_added'],
            'lines_deleted': data['lines_deleted'],
            'avg_quality': round(avg_quality, 1),
            'pr_reviews': data['pr_reviews'],
            'avg_response_hours': round(avg_response, 1) if data['response_times'] else None
        })

    # Sort by score (descending)
    leaderboard.sort(key=lambda x: x['score'], reverse=True)

    # Assign ranks
    for i, entry in enumerate(leaderboard):
        entry['rank'] = i + 1

    return {
        'period': period,
        'total_contributors': len(leaderboard),
        'total_commits': sum(e['commits'] for e in leaderboard),
        'total_lines': sum(e['lines_changed'] for e in leaderboard),
        'generated_at': datetime.now().isoformat(),
        'leaderboard': leaderboard
    }


def format_markdown(leaderboard_data):
    """Format leaderboard as markdown table."""
    md = f"# GitHub Contributor Leaderboard\n"
    md += f"## Period: {leaderboard_data['period'].title()}\n\n"
    md += f"**Summary:** {leaderboard_data['total_contributors']} contributors, "
    md += f"{leaderboard_data['total_commits']} commits, "
    md += f"{leaderboard_data['total_lines']:,} lines changed\n\n"

    md += "| Rank | Contributor | Score | Commits | Lines | Quality | Reviews |\n"
    md += "|------|-------------|-------|---------|-------|---------|---------|\n"

    for entry in leaderboard_data['leaderboard'][:20]:  # Top 20
        md += f"| {entry['rank']} | {entry['contributor']} | {entry['score']} | "
        md += f"{entry['commits']} | {entry['lines_changed']:,} | "
        md += f"{entry['avg_quality']} | {entry['pr_reviews']} |\n"

    return md


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Calculate contributor leaderboard')
    parser.add_argument('input', help='Input commits JSON file')
    parser.add_argument('--period', default='week',
                       choices=['week', 'month', 'year', 'all'],
                       help='Time period for leaderboard')
    parser.add_argument('--output', default='leaderboard.json',
                       help='Output leaderboard file')
    parser.add_argument('--markdown', help='Also generate markdown output file')
    args = parser.parse_args()

    # Load commits
    with open(args.input) as f:
        commits = json.load(f)

    # Calculate leaderboard
    leaderboard = calculate_leaderboard(commits, period=args.period)

    # Save JSON
    with open(args.output, 'w') as f:
        json.dump(leaderboard, f, indent=2)

    print(f"✓ Analyzed {leaderboard['total_commits']} commits")
    print(f"✓ {leaderboard['total_contributors']} contributors")
    print(f"✓ Period: {args.period}")
    print(f"✓ Saved to {args.output}")

    # Save markdown if requested
    if args.markdown:
        md = format_markdown(leaderboard)
        with open(args.markdown, 'w') as f:
            f.write(md)
        print(f"✓ Markdown saved to {args.markdown}")

    # Show top 5
    print(f"\n{'='*60}")
    print("Top 5 Contributors:")
    print(f"{'='*60}")
    for entry in leaderboard['leaderboard'][:5]:
        print(f"{entry['rank']}. {entry['contributor']:25s} Score: {entry['score']:6.1f} "
              f"({entry['commits']:2d} commits, {entry['lines_changed']:5d} lines, "
              f"quality: {entry['avg_quality']}/10)")


if __name__ == '__main__':
    main()
