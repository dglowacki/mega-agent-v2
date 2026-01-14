#!/usr/bin/env python3
"""
Generate HTML reports with neo-brutal design.

Usage:
    python generate_html_report.py data.json --template daily-summary --output report.html
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def get_base_template():
    """Get base HTML template with neo-brutal styling."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Arial', sans-serif;
            background: #f5f5f5;
            padding: 20px;
            line-height: 1.6;
            color: #000;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border: 4px solid #000;
            box-shadow: 8px 8px 0 #000;
        }}

        .header {{
            background: #000;
            color: white;
            padding: 40px;
            border-bottom: 4px solid #000;
        }}

        .header h1 {{
            font-size: 2.5em;
            font-weight: 900;
            margin-bottom: 10px;
        }}

        .header .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}

        .content {{
            padding: 40px;
        }}

        .section {{
            margin-bottom: 40px;
        }}

        .section-title {{
            font-size: 1.8em;
            font-weight: 900;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #000;
        }}

        .section-content {{
            padding: 20px 0;
        }}

        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .metric-card {{
            background: #fff;
            border: 3px solid #000;
            padding: 25px;
            position: relative;
        }}

        .metric-value {{
            font-size: 3em;
            font-weight: 900;
            color: #000;
            line-height: 1;
        }}

        .metric-label {{
            font-size: 0.9em;
            text-transform: uppercase;
            font-weight: 700;
            color: #666;
            margin-top: 10px;
        }}

        .metric-change {{
            font-size: 0.9em;
            font-weight: 700;
            margin-top: 8px;
        }}

        .metric-change.positive {{
            color: #4ade80;
        }}

        .metric-change.negative {{
            color: #f87171;
        }}

        .metric-change.neutral {{
            color: #666;
        }}

        .data-table {{
            width: 100%;
            border-collapse: collapse;
            border: 3px solid #000;
            margin: 20px 0;
        }}

        .data-table th {{
            background: #000;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 900;
            border: 3px solid #000;
        }}

        .data-table td {{
            padding: 12px 15px;
            border: 2px solid #000;
        }}

        .data-table tr:nth-child(even) {{
            background: #f9f9f9;
        }}

        .data-table tr:hover {{
            background: #f5f5f5;
        }}

        .badge {{
            display: inline-block;
            padding: 6px 12px;
            border: 2px solid #000;
            font-weight: 700;
            font-size: 0.85em;
            margin: 2px;
        }}

        .badge-success {{
            background: #4ade80;
            color: #000;
        }}

        .badge-warning {{
            background: #fbbf24;
            color: #000;
        }}

        .badge-error {{
            background: #f87171;
            color: #000;
        }}

        .badge-info {{
            background: #60a5fa;
            color: #000;
        }}

        .badge-neutral {{
            background: #e5e5e5;
            color: #000;
        }}

        .timeline {{
            border-left: 4px solid #000;
            padding-left: 30px;
            margin-left: 20px;
        }}

        .timeline-item {{
            margin-bottom: 30px;
            position: relative;
        }}

        .timeline-item::before {{
            content: '';
            position: absolute;
            left: -37px;
            top: 5px;
            width: 14px;
            height: 14px;
            background: #000;
            border: 3px solid #fff;
        }}

        .timeline-time {{
            font-size: 0.9em;
            font-weight: 700;
            color: #666;
            margin-bottom: 5px;
        }}

        .timeline-content {{
            background: #fff;
            border: 3px solid #000;
            padding: 15px;
        }}

        .timeline-title {{
            font-weight: 700;
            margin-bottom: 5px;
        }}

        .list-group {{
            border: 3px solid #000;
        }}

        .list-item {{
            padding: 15px;
            border-bottom: 2px solid #000;
        }}

        .list-item:last-child {{
            border-bottom: none;
        }}

        .list-item:nth-child(even) {{
            background: #f9f9f9;
        }}

        .footer {{
            background: #f5f5f5;
            padding: 30px;
            border-top: 3px solid #000;
            text-align: center;
            font-size: 0.9em;
        }}

        .empty-state {{
            text-align: center;
            padding: 60px 20px;
            color: #666;
            border: 3px dashed #ccc;
        }}

        .empty-state-icon {{
            font-size: 4em;
            margin-bottom: 20px;
        }}

        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.8em;
            }}

            .metric-grid {{
                grid-template-columns: 1fr;
            }}

            .data-table {{
                font-size: 0.9em;
            }}

            .data-table th,
            .data-table td {{
                padding: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <div class="subtitle">{subtitle}</div>
        </div>
        <div class="content">
            {content}
        </div>
        <div class="footer">
            {footer}
        </div>
    </div>
</body>
</html>
"""


def generate_daily_summary(data):
    """Generate daily summary report."""
    content = ""

    # Summary metrics
    if "metrics" in data:
        content += '<div class="section">'
        content += '<div class="section-title">Summary</div>'
        content += '<div class="metric-grid">'

        for metric in data["metrics"]:
            change_class = "neutral"
            if "change" in metric:
                if metric.get("trend") == "up":
                    change_class = "positive"
                elif metric.get("trend") == "down":
                    change_class = "negative"

            content += f'''
                <div class="metric-card">
                    <div class="metric-value">{metric.get('value', '0')}</div>
                    <div class="metric-label">{metric.get('label', '')}</div>
                    {f'<div class="metric-change {change_class}">{metric["change"]}</div>' if "change" in metric else ''}
                </div>
            '''

        content += '</div></div>'

    # Sections
    if "sections" in data:
        for section in data["sections"]:
            content += '<div class="section">'
            content += f'<div class="section-title">{section.get("title", "")}</div>'
            content += '<div class="section-content">'

            section_type = section.get("type", "text")
            section_data = section.get("data", {})

            if section_type == "table":
                content += generate_table(section_data)
            elif section_type == "list":
                content += generate_list(section_data)
            elif section_type == "timeline":
                content += generate_timeline(section_data)
            elif section_type == "text":
                content += f'<p>{section_data.get("content", "")}</p>'

            content += '</div></div>'

    # Empty state if no content
    if not content:
        content = '''
            <div class="empty-state">
                <div class="empty-state-icon">📊</div>
                <div>No data available for this report.</div>
            </div>
        '''

    return content


def generate_table(data):
    """Generate HTML table from data."""
    if "rows" not in data or not data["rows"]:
        return '<p>No data available.</p>'

    columns = data.get("columns", [])
    rows = data["rows"]

    html = '<table class="data-table">'

    # Header
    html += '<thead><tr>'
    for col in columns:
        html += f'<th>{col}</th>'
    html += '</tr></thead>'

    # Body
    html += '<tbody>'
    for row in rows:
        html += '<tr>'
        for col in columns:
            value = row.get(col, '')
            # Check if value should be a badge
            if col.lower() in ['status', 'state', 'type']:
                badge_class = get_badge_class(value)
                html += f'<td><span class="badge {badge_class}">{value}</span></td>'
            else:
                html += f'<td>{value}</td>'
        html += '</tr>'
    html += '</tbody>'

    html += '</table>'
    return html


def generate_list(data):
    """Generate HTML list from data."""
    if "items" not in data or not data["items"]:
        return '<p>No items available.</p>'

    html = '<div class="list-group">'
    for item in data["items"]:
        html += '<div class="list-item">'
        if "title" in item:
            html += f'<strong>{item["title"]}</strong><br>'
        if "content" in item:
            html += item["content"]
        html += '</div>'
    html += '</div>'

    return html


def generate_timeline(data):
    """Generate HTML timeline from data."""
    if "events" not in data or not data["events"]:
        return '<p>No events available.</p>'

    html = '<div class="timeline">'
    for event in data["events"]:
        html += '<div class="timeline-item">'
        html += f'<div class="timeline-time">{event.get("time", "")}</div>'
        html += '<div class="timeline-content">'
        if "title" in event:
            html += f'<div class="timeline-title">{event["title"]}</div>'
        if "content" in event:
            html += f'<div>{event["content"]}</div>'
        html += '</div></div>'
    html += '</div>'

    return html


def get_badge_class(value):
    """Get badge class based on value."""
    value_lower = str(value).lower()

    if value_lower in ['active', 'success', 'completed', 'passed', 'approved']:
        return 'badge-success'
    elif value_lower in ['pending', 'in progress', 'warning', 'review']:
        return 'badge-warning'
    elif value_lower in ['failed', 'error', 'rejected', 'critical']:
        return 'badge-error'
    elif value_lower in ['info', 'new', 'updated']:
        return 'badge-info'
    else:
        return 'badge-neutral'


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Generate HTML report')
    parser.add_argument('input', help='Input JSON data file')
    parser.add_argument('--template', default='daily-summary',
                       choices=['daily-summary', 'dashboard', 'comparison', 'leaderboard', 'timeline'],
                       help='Report template')
    parser.add_argument('--title', help='Report title (overrides data)')
    parser.add_argument('--subtitle', help='Report subtitle (overrides data)')
    parser.add_argument('--output', default='report.html', help='Output HTML file')
    args = parser.parse_args()

    # Load data
    with open(args.input) as f:
        data = json.load(f)

    # Get title and subtitle
    title = args.title or data.get('title', 'Report')
    subtitle = args.subtitle or data.get('subtitle', datetime.now().strftime("%B %d, %Y"))

    # Generate content based on template
    if args.template == 'daily-summary':
        content = generate_daily_summary(data)
    else:
        # Other templates use same generator for now
        content = generate_daily_summary(data)

    # Get footer
    footer = data.get('footer', f'Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br>Built with Claude Agent SDK')

    # Generate HTML
    html = get_base_template().format(
        title=title,
        subtitle=subtitle,
        content=content,
        footer=footer
    )

    # Save
    with open(args.output, 'w') as f:
        f.write(html)

    print(f"✓ Report generated: {args.output}")
    print(f"✓ Template: {args.template}")
    print(f"✓ Title: {title}")


if __name__ == '__main__':
    main()
