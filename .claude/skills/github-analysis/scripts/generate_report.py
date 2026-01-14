#!/usr/bin/env python3
"""
Generate HTML report from GitHub analysis data.

Usage:
    python generate_report.py analysis.json --template github-summary --output report.html
"""

import json
import sys
from datetime import datetime


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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            background: #f5f5f5;
            padding: 20px;
            line-height: 1.6;
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
            padding: 30px;
            border-bottom: 4px solid #000;
        }}

        .header h1 {{
            font-size: 2.5em;
            font-weight: 900;
            margin-bottom: 10px;
        }}

        .header .subtitle {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .content {{
            padding: 30px;
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

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: #fff;
            border: 3px solid #000;
            padding: 20px;
        }}

        .stat-value {{
            font-size: 2.5em;
            font-weight: 900;
            color: #000;
        }}

        .stat-label {{
            font-size: 0.9em;
            text-transform: uppercase;
            font-weight: 700;
            color: #666;
            margin-top: 5px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            border: 3px solid #000;
            margin-bottom: 20px;
        }}

        th {{
            background: #000;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 900;
            border: 3px solid #000;
        }}

        td {{
            padding: 12px 15px;
            border: 2px solid #000;
        }}

        tr:nth-child(even) {{
            background: #f9f9f9;
        }}

        .quality-badge {{
            display: inline-block;
            padding: 4px 12px;
            border: 2px solid #000;
            font-weight: 700;
            font-size: 0.9em;
        }}

        .quality-excellent {{
            background: #4ade80;
        }}

        .quality-good {{
            background: #fbbf24;
        }}

        .quality-poor {{
            background: #f87171;
        }}

        .footer {{
            background: #f5f5f5;
            padding: 20px 30px;
            border-top: 3px solid #000;
            text-align: center;
            font-size: 0.9em;
        }}

        .badge {{
            display: inline-block;
            padding: 6px 12px;
            border: 2px solid #000;
            font-weight: 700;
            margin: 2px;
            font-size: 0.85em;
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
            Generated on {timestamp}<br>
            Built with Claude Agent SDK
        </div>
    </div>
</body>
</html>
"""


def generate_github_summary(analysis_data):
    """Generate GitHub activity summary report."""
    summary = analysis_data.get('summary', {})
    contributors = analysis_data.get('contributors', [])
    hot_files = analysis_data.get('hot_files', [])

    # Summary stats
    content = '<div class="section">'
    content += '<div class="section-title">Summary</div>'
    content += '<div class="stats-grid">'
    content += f'''
        <div class="stat-card">
            <div class="stat-value">{summary.get('total_commits', 0)}</div>
            <div class="stat-label">Total Commits</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{summary.get('total_contributors', 0)}</div>
            <div class="stat-label">Contributors</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{summary.get('total_files', 0)}</div>
            <div class="stat-label">Files Changed</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{summary.get('total_lines_added', 0):,}</div>
            <div class="stat-label">Lines Added</div>
        </div>
    '''
    content += '</div></div>'

    # Top contributors
    if contributors:
        content += '<div class="section">'
        content += '<div class="section-title">Top Contributors</div>'
        content += '<table>'
        content += '<tr><th>Rank</th><th>Name</th><th>Commits</th><th>Lines Changed</th><th>Quality</th><th>Score</th></tr>'

        for i, contrib in enumerate(contributors[:10], 1):
            quality = contrib.get('avg_quality', 0)
            quality_class = 'excellent' if quality >= 8 else 'good' if quality >= 5 else 'poor'

            content += f'''
                <tr>
                    <td><strong>#{i}</strong></td>
                    <td>{contrib.get('name', 'Unknown')}</td>
                    <td>{contrib.get('commits', 0)}</td>
                    <td>{contrib.get('lines_changed', 0):,}</td>
                    <td><span class="quality-badge quality-{quality_class}">{quality}/10</span></td>
                    <td><strong>{contrib.get('score', 0)}</strong></td>
                </tr>
            '''

        content += '</table></div>'

    # Hot files
    if hot_files:
        content += '<div class="section">'
        content += '<div class="section-title">Most Changed Files</div>'
        content += '<table>'
        content += '<tr><th>File</th><th>Changes</th></tr>'

        for file_info in hot_files[:15]:
            content += f'''
                <tr>
                    <td><code>{file_info.get('file', '')}</code></td>
                    <td><strong>{file_info.get('changes', 0)}</strong></td>
                </tr>
            '''

        content += '</table></div>'

    return content


def generate_pr_review_summary(pr_data):
    """Generate PR review summary report."""
    content = '<div class="section">'
    content += '<div class="section-title">Pull Request Review</div>'

    # PR details
    content += f'''
        <p><strong>PR #{pr_data.get('pr_number')}:</strong> {pr_data.get('title', 'N/A')}</p>
        <p><strong>Author:</strong> {pr_data.get('author', 'N/A')}</p>
        <p><strong>Branch:</strong> {pr_data.get('branch', 'N/A')}</p>
    '''

    # Quality assessment
    assessment = pr_data.get('assessment', {})
    if assessment:
        content += '<div class="section">'
        content += '<div class="section-title">Code Quality Assessment</div>'

        for category, rating in assessment.items():
            badge_class = 'quality-excellent' if 'good' in rating.lower() else 'quality-good' if 'needs' in rating.lower() else 'quality-poor'
            content += f'<p><strong>{category}:</strong> <span class="quality-badge {badge_class}">{rating}</span></p>'

        content += '</div>'

    # Issues found
    issues = pr_data.get('issues', [])
    if issues:
        content += '<div class="section">'
        content += '<div class="section-title">Issues Found</div>'
        content += '<ul>'
        for issue in issues:
            severity = issue.get('severity', 'info')
            content += f'<li><span class="badge quality-{severity}">{severity.upper()}</span> {issue.get("description", "")}</li>'
        content += '</ul></div>'

    content += '</div>'
    return content


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Generate HTML report from analysis')
    parser.add_argument('input', help='Input analysis JSON file')
    parser.add_argument('--template', default='github-summary',
                       choices=['github-summary', 'pr-review'],
                       help='Report template to use')
    parser.add_argument('--output', default='report.html',
                       help='Output HTML file')
    args = parser.parse_args()

    # Load analysis data
    with open(args.input) as f:
        data = json.load(f)

    # Generate content based on template
    if args.template == 'github-summary':
        title = "GitHub Activity Report"
        subtitle = f"Analysis of {data.get('summary', {}).get('total_commits', 0)} commits"
        content = generate_github_summary(data)
    elif args.template == 'pr-review':
        title = "Pull Request Review"
        subtitle = f"PR #{data.get('pr_number', 'N/A')}"
        content = generate_pr_review_summary(data)
    else:
        print(f"Unknown template: {args.template}")
        return 1

    # Generate HTML
    html = get_base_template().format(
        title=title,
        subtitle=subtitle,
        content=content,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    # Save
    with open(args.output, 'w') as f:
        f.write(html)

    print(f"✓ Report generated: {args.output}")
    print(f"✓ Template: {args.template}")


if __name__ == '__main__':
    main()
