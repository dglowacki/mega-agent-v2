#!/usr/bin/env python3
"""
Render HTML email templates with data.

Usage:
    python render_template.py --template daily-summary --data data.json --output email.html
"""

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict


def render_template(template_name: str, data: Dict[str, Any]) -> str:
    """
    Render a template with data using simple variable substitution.

    Supports:
    - {{variable}} - Simple variable substitution
    - {{#if variable}}...{{/if}} - Conditional blocks
    - {{#each items}}...{{/each}} - Loop blocks
    """
    # Load template
    template_path = Path(__file__).parent.parent / 'templates' / f'{template_name}.html'

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_name}.html")

    with open(template_path, 'r') as f:
        template = f.read()

    # Render template (simple substitution)
    rendered = template

    # Handle simple variables {{variable}}
    for key, value in data.items():
        if isinstance(value, (str, int, float)):
            rendered = rendered.replace(f'{{{{{key}}}}}', str(value))

    # Handle nested objects {{object.property}}
    def replace_nested(match):
        path = match.group(1).split('.')
        value = data
        for key in path:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return match.group(0)  # Keep original if path not found
        return str(value)

    rendered = re.sub(r'\{\{([a-zA-Z0-9_.]+)\}\}', replace_nested, rendered)

    # Handle {{#each items}}...{{/each}} loops
    def render_loop(match):
        var_name = match.group(1)
        content = match.group(2)

        if var_name not in data or not isinstance(data[var_name], list):
            return ''

        result = []
        for i, item in enumerate(data[var_name]):
            item_html = content

            # Replace {{@index}} with index
            item_html = item_html.replace('{{@index}}', str(i + 1))

            # Replace item properties
            if isinstance(item, dict):
                for key, value in item.items():
                    item_html = item_html.replace(f'{{{{{key}}}}}', str(value))

            result.append(item_html)

        return ''.join(result)

    rendered = re.sub(r'\{\{#each ([a-zA-Z0-9_]+)\}\}(.*?)\{\{/each\}\}', render_loop, rendered, flags=re.DOTALL)

    # Handle {{#if variable}}...{{/if}} conditionals
    def render_if(match):
        var_name = match.group(1)
        content = match.group(2)

        # Check if variable exists and is truthy
        value = data.get(var_name)
        if value and (not isinstance(value, list) or len(value) > 0):
            return content
        return ''

    rendered = re.sub(r'\{\{#if ([a-zA-Z0-9_]+)\}\}(.*?)\{\{/if\}\}', render_if, rendered, flags=re.DOTALL)

    return rendered


def main():
    parser = argparse.ArgumentParser(description='Render HTML email template')
    parser.add_argument('--template', required=True, help='Template name (without .html)')
    parser.add_argument('--data', required=True, help='JSON data file')
    parser.add_argument('--output', help='Output HTML file (optional, prints to stdout if not provided)')

    args = parser.parse_args()

    # Load data
    with open(args.data, 'r') as f:
        data = json.load(f)

    # Render template
    html = render_template(args.template, data)

    # Output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(html)
        print(f"✓ Template rendered to {args.output}")
    else:
        print(html)


if __name__ == '__main__':
    main()
