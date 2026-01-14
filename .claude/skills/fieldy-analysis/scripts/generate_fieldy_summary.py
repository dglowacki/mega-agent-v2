#!/usr/bin/env python3
"""
Generate formatted Fieldy summary for email reports.

Usage:
    python generate_fieldy_summary.py analysis.json --output summary.json --format report
"""

import json
import sys
from datetime import datetime


def format_timestamp_pt(iso_timestamp):
    """Convert ISO timestamp to PT display format."""
    if not iso_timestamp:
        return "Unknown"

    try:
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        # Convert to PT (UTC-8)
        from datetime import timedelta
        dt_pt = dt - timedelta(hours=8)
        return dt_pt.strftime("%I:%M %p PT")
    except:
        return "Unknown"


def format_date_full(date_str):
    """Format date as 'Friday, January 4, 2026'."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%A, %B %d, %Y")
    except:
        return date_str


def generate_report_format(analysis_data):
    """Generate report-compatible JSON format."""
    date = analysis_data.get('date', '')
    summary = analysis_data.get('summary', {})
    sessions = analysis_data.get('sessions', [])
    keywords = analysis_data.get('keywords', [])

    # Format metrics
    metrics = [
        {
            'label': 'Total Sessions',
            'value': str(summary.get('total_sessions', 0))
        },
        {
            'label': 'Total Duration',
            'value': f"{summary.get('total_duration_minutes', 0)} min"
        },
        {
            'label': 'Avg Session Length',
            'value': f"{summary.get('avg_session_minutes', 0)} min"
        },
        {
            'label': 'Total Words',
            'value': f"{summary.get('total_words', 0):,}"
        }
    ]

    # Build timeline section
    timeline_events = []
    for i, session in enumerate(sessions[:10]):  # Top 10 sessions
        timestamp = session.get('timestamp', '')
        timeline_events.append({
            'time': format_timestamp_pt(timestamp),
            'title': f"Session {i + 1}",
            'content': f"Duration: {session.get('duration_minutes', 0)} min, "
                      f"Words: {session.get('word_count', 0)}"
        })

    sections = []

    # Session timeline section
    if timeline_events:
        sections.append({
            'title': 'Session Timeline',
            'type': 'timeline',
            'data': {
                'events': timeline_events
            }
        })

    # Activity summary section
    first_session = format_timestamp_pt(summary.get('first_session'))
    last_session = format_timestamp_pt(summary.get('last_session'))

    sections.append({
        'title': 'Daily Activity',
        'type': 'list',
        'data': {
            'items': [
                {
                    'title': 'First Session',
                    'content': first_session
                },
                {
                    'title': 'Last Session',
                    'content': last_session
                },
                {
                    'title': 'Session Distribution',
                    'content': f"{len(sessions)} coaching sessions throughout the day"
                }
            ]
        }
    })

    # Top keywords section
    if keywords:
        keyword_rows = []
        for kw in keywords[:10]:
            keyword_rows.append({
                'Keyword': kw.get('word', ''),
                'Count': str(kw.get('count', 0))
            })

        sections.append({
            'title': 'Top Keywords',
            'type': 'table',
            'data': {
                'columns': ['Keyword', 'Count'],
                'rows': keyword_rows
            }
        })

    # Build report JSON
    report = {
        'title': 'Fieldy Daily Summary',
        'subtitle': format_date_full(date),
        'metrics': metrics,
        'sections': sections,
        'footer': f'Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br>'
                 f'Fieldy coaching data from {date}'
    }

    return report


def generate_simple_format(analysis_data):
    """Generate simple text summary."""
    date = analysis_data.get('date', '')
    summary = analysis_data.get('summary', {})

    text = f"Fieldy Daily Summary - {format_date_full(date)}\n\n"
    text += "Summary:\n"
    text += f"• {summary.get('total_sessions', 0)} total coaching sessions\n"
    text += f"• {summary.get('total_duration_minutes', 0)} minutes total duration\n"
    text += f"• {summary.get('avg_session_minutes', 0)} minutes average session length\n"
    text += f"• {summary.get('total_words', 0):,} total words transcribed\n\n"

    text += "Timeline:\n"
    text += f"• First session: {format_timestamp_pt(summary.get('first_session'))}\n"
    text += f"• Last session: {format_timestamp_pt(summary.get('last_session'))}\n"

    return {'text': text}


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Generate Fieldy summary')
    parser.add_argument('input', help='Input analysis JSON file')
    parser.add_argument('--output', default='summary.json', help='Output summary file')
    parser.add_argument('--format', default='report',
                       choices=['report', 'simple'],
                       help='Output format (report for HTML generation, simple for text)')
    args = parser.parse_args()

    # Load analysis
    with open(args.input) as f:
        analysis = json.load(f)

    # Generate summary
    if args.format == 'report':
        summary = generate_report_format(analysis)
    else:
        summary = generate_simple_format(analysis)

    # Save
    with open(args.output, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"✓ Generated {args.format} format summary")
    print(f"✓ Saved to {args.output}")

    if args.format == 'simple':
        print()
        print("Summary:")
        print(summary['text'])


if __name__ == '__main__':
    main()
