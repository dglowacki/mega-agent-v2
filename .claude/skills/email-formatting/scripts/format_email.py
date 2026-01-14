#!/usr/bin/env python3
"""
Email formatting script with neo-brutal design templates.

Usage:
    python format_email.py --template daily-report --data data.json
    python format_email.py --template simple --title "Test" --body "Message"
"""

import json
import sys
from pathlib import Path


def format_daily_report(data):
    """Format daily report template."""
    sections_html = ""
    for section in data.get("sections", []):
        items_html = ""
        if "items" in section:
            items_html = "<ul>" + "".join(f"<li>{item}</li>" for item in section["items"]) + "</ul>"

        sections_html += f"""
        <div class="section">
            <div class="section-title">{section['title']}</div>
            <div>{section.get('content', '')}</div>
            {items_html}
        </div>
        """

    stats_html = ""
    if "stats" in data:
        stats_html = '<div class="section">'
        for key, value in data["stats"].items():
            label = key.replace("_", " ").title()
            stats_html += f'<div class="stat-box">{label}: <strong>{value}</strong></div>'
        stats_html += '</div>'

    return get_base_template().format(
        title=data.get("title", "Report"),
        content=sections_html + stats_html
    )


def format_simple(data):
    """Format simple message template."""
    content = f"""
    <div class="section">
        <div>{data.get('body', '')}</div>
    </div>
    """
    if "footer" in data:
        content += f"""
        <div class="footer">
            {data['footer']}
        </div>
        """

    return get_base_template().format(
        title=data.get("title", "Message"),
        content=content
    )


def format_data_table(data):
    """Format data table template."""
    headers = "".join(f"<th>{h}</th>" for h in data.get("headers", []))
    rows = ""
    for row in data.get("rows", []):
        rows += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"

    content = f"""
    <div class="section">
        <table>
            <thead><tr>{headers}</tr></thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
    """

    return get_base_template().format(
        title=data.get("title", "Data Report"),
        content=content
    )


def get_base_template():
    """Get base HTML template."""
    return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: white;
            border: 4px solid black;
            padding: 0;
        }}
        .header {{
            background-color: black;
            color: white;
            padding: 20px;
            font-size: 24px;
            font-weight: 900;
            border-bottom: 4px solid black;
        }}
        .section {{
            padding: 20px;
            border-bottom: 3px solid black;
        }}
        .section:last-child {{
            border-bottom: none;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: 800;
            margin-bottom: 10px;
            text-transform: uppercase;
        }}
        .stat-box {{
            display: inline-block;
            background-color: #ffeb3b;
            border: 3px solid black;
            padding: 10px 15px;
            margin: 5px;
            font-weight: 700;
        }}
        ul {{
            list-style: none;
            padding: 0;
        }}
        li {{
            padding: 8px;
            margin: 5px 0;
            background-color: #f5f5f5;
            border-left: 4px solid black;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border: 2px solid black;
        }}
        th {{
            background-color: black;
            color: white;
            font-weight: 800;
        }}
        .footer {{
            padding: 15px 20px;
            background-color: #f5f5f5;
            border-top: 3px solid black;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">{title}</div>
        {content}
    </div>
</body>
</html>"""


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Format emails with neo-brutal templates")
    parser.add_argument("--template", required=True, choices=["daily-report", "simple", "data-table"])
    parser.add_argument("--data", help="JSON data file")
    parser.add_argument("--title", help="Title (for simple template)")
    parser.add_argument("--body", help="Body (for simple template)")
    args = parser.parse_args()

    # Load data
    if args.data:
        with open(args.data) as f:
            data = json.load(f)
    else:
        # Build from args
        data = {
            "title": args.title or "Message",
            "body": args.body or ""
        }

    # Format based on template
    if args.template == "daily-report":
        html = format_daily_report(data)
    elif args.template == "simple":
        html = format_simple(data)
    elif args.template == "data-table":
        html = format_data_table(data)

    print(html)


if __name__ == "__main__":
    main()
