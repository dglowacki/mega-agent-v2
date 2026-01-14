"""
Gmail MCP Server for Claude Agent SDK

Exposes Gmail operations as MCP tools that agents can use directly.
"""

import os
import sys
from pathlib import Path

# Add integrations to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_agent_sdk import create_sdk_mcp_server, tool
from gmail_client import GmailClient


@tool(
    name="send_email",
    description="Send an email via Gmail",
    input_schema={
        "type": "object",
        "properties": {
            "to": {
                "type": "string",
                "description": "Recipient email address"
            },
            "subject": {
                "type": "string",
                "description": "Email subject line"
            },
            "body": {
                "type": "string",
                "description": "Plain text email body (optional if body_html provided)"
            },
            "body_html": {
                "type": "string",
                "description": "HTML email body (optional)"
            },
            "account": {
                "type": "string",
                "description": "Gmail account: 'flycow' or 'aquarius'",
                "enum": ["flycow", "aquarius"],
                "default": "flycow"
            }
        },
        "required": ["to", "subject"]
    }
)
def send_email(args):
    """Send email via Gmail."""
    try:
        account = args.get("account", "flycow")
        gmail = GmailClient(account=account)

        # Require either body or body_html
        if not args.get("body") and not args.get("body_html"):
            return {
                "content": [{
                    "type": "text",
                    "text": "✗ Error: Must provide either 'body' or 'body_html'"
                }],
                "isError": True
            }

        result = gmail.send_email(
            to=args["to"],
            subject=args["subject"],
            body=args.get("body", ""),
            body_html=args.get("body_html")
        )

        return {
            "content": [{
                "type": "text",
                "text": f"✓ Email sent successfully to {args['to']} from {account} account\n"
                       f"Subject: {args['subject']}"
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to send email: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="send_email_with_attachment",
    description="Send an email with file attachments via Gmail",
    input_schema={
        "type": "object",
        "properties": {
            "to": {
                "type": "string",
                "description": "Recipient email address"
            },
            "subject": {
                "type": "string",
                "description": "Email subject line"
            },
            "body": {
                "type": "string",
                "description": "Plain text email body"
            },
            "body_html": {
                "type": "string",
                "description": "HTML email body (optional)"
            },
            "attachment_path": {
                "type": "string",
                "description": "Path to file to attach"
            },
            "account": {
                "type": "string",
                "description": "Gmail account: 'flycow' or 'aquarius'",
                "enum": ["flycow", "aquarius"],
                "default": "flycow"
            }
        },
        "required": ["to", "subject", "body", "attachment_path"]
    }
)
def send_email_with_attachment(args):
    """Send email with attachment via Gmail."""
    try:
        account = args.get("account", "flycow")
        gmail = GmailClient(account=account)

        # Check if attachment exists
        attachment_path = args["attachment_path"]
        if not os.path.exists(attachment_path):
            return {
                "content": [{
                    "type": "text",
                    "text": f"✗ Error: Attachment not found: {attachment_path}"
                }],
                "isError": True
            }

        result = gmail.send_email(
            to=args["to"],
            subject=args["subject"],
            body=args["body"],
            body_html=args.get("body_html"),
            attachment_path=attachment_path
        )

        return {
            "content": [{
                "type": "text",
                "text": f"✓ Email with attachment sent successfully to {args['to']}\n"
                       f"Subject: {args['subject']}\n"
                       f"Attachment: {os.path.basename(attachment_path)}"
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to send email with attachment: {str(e)}"
            }],
            "isError": True
        }


# Create and export the MCP server
gmail_mcp_server = create_sdk_mcp_server(
    name="gmail",
    version="1.0.0",
    tools=[send_email, send_email_with_attachment]
)
