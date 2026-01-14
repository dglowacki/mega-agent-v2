#!/usr/bin/env python3
"""
Format and optionally send HTML emails using templates.

Usage:
    # Just render
    python format_email.py --template daily-summary --data data.json

    # Render and send
    python format_email.py --template github-digest --data data.json --subject "GitHub Digest" --to user@example.com --send
"""

import argparse
import json
import sys
from pathlib import Path

# Add integrations to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'integrations'))

from render_template import render_template


def format_email(template: str, data: dict, subject: str = None, to: str = None, send: bool = False) -> str:
    """
    Format an email using a template.

    Args:
        template: Template name
        data: Template data
        subject: Email subject (for sending)
        to: Recipient email (for sending)
        send: Whether to send the email

    Returns:
        Rendered HTML
    """
    html = render_template(template, data)

    if send:
        if not subject or not to:
            raise ValueError("--subject and --to required when using --send")

        # Import gmail client
        try:
            from gmail_client import GmailClient

            client = GmailClient()
            result = client.send_email(
                to=to,
                subject=subject,
                body_html=html
            )

            if result.get('status') == 'success':
                print(f"✓ Email sent to {to}")
            else:
                print(f"✗ Failed to send email: {result.get('error')}")

        except Exception as e:
            print(f"✗ Error sending email: {str(e)}")

    return html


def main():
    parser = argparse.ArgumentParser(description='Format and send HTML emails')
    parser.add_argument('--template', required=True, help='Template name')
    parser.add_argument('--data', required=True, help='JSON data file')
    parser.add_argument('--subject', help='Email subject')
    parser.add_argument('--to', help='Recipient email')
    parser.add_argument('--send', action='store_true', help='Send the email')
    parser.add_argument('--output', help='Save HTML to file')

    args = parser.parse_args()

    # Load data
    with open(args.data, 'r') as f:
        data = json.load(f)

    # Format email
    html = format_email(
        template=args.template,
        data=data,
        subject=args.subject,
        to=args.to,
        send=args.send
    )

    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            f.write(html)
        print(f"✓ HTML saved to {args.output}")

    # Print to stdout if not sending or saving
    if not args.send and not args.output:
        print(html)


if __name__ == '__main__':
    main()
