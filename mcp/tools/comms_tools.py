"""
Communications Tools - Email and calendar operations.

Provides email sending and calendar management for the voice assistant.
"""

import subprocess
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional
import os

logger = logging.getLogger(__name__)

# Email configuration (from environment)
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
DEFAULT_FROM = os.environ.get("EMAIL_FROM", "voice-assistant@example.com")


def email_send(
    to: str,
    subject: str,
    body: str,
    html: bool = False,
    cc: str = None,
    from_addr: str = None
) -> str:
    """
    Send an email.

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body
        html: Send as HTML email
        cc: CC recipients (comma-separated)
        from_addr: From address

    Returns:
        Send result
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        return "Error: Email not configured. Set SMTP_USER and SMTP_PASSWORD environment variables."

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_addr or DEFAULT_FROM
        msg['To'] = to

        if cc:
            msg['Cc'] = cc

        if html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))

        # Connect and send
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)

            recipients = [to]
            if cc:
                recipients.extend(cc.split(','))

            server.sendmail(msg['From'], recipients, msg.as_string())

        return f"Email sent successfully to {to}"

    except smtplib.SMTPAuthenticationError:
        return "Error: SMTP authentication failed"
    except smtplib.SMTPException as e:
        return f"Error sending email: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


def email_draft(
    to: str,
    subject: str,
    body: str,
    format: str = "text"
) -> str:
    """
    Create an email draft (returns formatted email without sending).

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body
        format: Output format (text or json)

    Returns:
        Formatted draft
    """
    draft = {
        "to": to,
        "subject": subject,
        "body": body,
        "from": DEFAULT_FROM,
        "timestamp": datetime.now().isoformat()
    }

    if format == "json":
        return json.dumps(draft, indent=2)

    return f"""
Email Draft
-----------
To: {to}
Subject: {subject}
From: {DEFAULT_FROM}

{body}
-----------
(Use email_send to send this email)
"""


# Calendar operations using gcalcli if available

def calendar_list(
    days: int = 7,
    calendar: str = None
) -> str:
    """
    List upcoming calendar events.

    Args:
        days: Number of days to look ahead
        calendar: Specific calendar to use

    Returns:
        List of events
    """
    try:
        cmd = ["gcalcli", "agenda", "--nocolor"]

        if calendar:
            cmd.extend(["--calendar", calendar])

        # Calculate end date
        end_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        cmd.append(end_date)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            if "not found" in result.stderr.lower():
                return "Error: gcalcli not installed. Install with: pip install gcalcli"
            return f"Error: {result.stderr}"

        return result.stdout if result.stdout.strip() else "No upcoming events"

    except FileNotFoundError:
        return "Error: gcalcli not installed. Install with: pip install gcalcli"
    except subprocess.TimeoutExpired:
        return "Error: Calendar command timed out"
    except Exception as e:
        return f"Error: {str(e)}"


def calendar_add(
    title: str,
    start: str,
    end: str = None,
    description: str = None,
    location: str = None,
    calendar: str = None
) -> str:
    """
    Add a calendar event.

    Args:
        title: Event title
        start: Start time (natural language or ISO format)
        end: End time (optional)
        description: Event description
        location: Event location
        calendar: Specific calendar to use

    Returns:
        Add result
    """
    try:
        cmd = ["gcalcli", "add", "--title", title, "--when", start, "--noprompt"]

        if end:
            cmd.extend(["--duration", end])
        if description:
            cmd.extend(["--description", description])
        if location:
            cmd.extend(["--where", location])
        if calendar:
            cmd.extend(["--calendar", calendar])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return f"Error: {result.stderr}"

        return f"Event '{title}' added successfully"

    except FileNotFoundError:
        return "Error: gcalcli not installed"
    except subprocess.TimeoutExpired:
        return "Error: Calendar command timed out"
    except Exception as e:
        return f"Error: {str(e)}"


def calendar_search(
    query: str,
    days: int = 30
) -> str:
    """
    Search calendar events.

    Args:
        query: Search text
        days: Days to search ahead

    Returns:
        Matching events
    """
    try:
        end_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

        result = subprocess.run(
            ["gcalcli", "search", query, end_date, "--nocolor"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return f"Error: {result.stderr}"

        return result.stdout if result.stdout.strip() else f"No events matching '{query}'"

    except FileNotFoundError:
        return "Error: gcalcli not installed"
    except subprocess.TimeoutExpired:
        return "Error: Calendar command timed out"
    except Exception as e:
        return f"Error: {str(e)}"


def calendar_delete(
    title: str,
    calendar: str = None
) -> str:
    """
    Delete a calendar event by title.

    Args:
        title: Event title to delete
        calendar: Specific calendar

    Returns:
        Delete result
    """
    try:
        cmd = ["gcalcli", "delete", title, "--nocolor"]

        if calendar:
            cmd.extend(["--calendar", calendar])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            input="y\n"  # Confirm deletion
        )

        if result.returncode != 0:
            return f"Error: {result.stderr}"

        return f"Event '{title}' deleted"

    except FileNotFoundError:
        return "Error: gcalcli not installed"
    except subprocess.TimeoutExpired:
        return "Error: Calendar command timed out"
    except Exception as e:
        return f"Error: {str(e)}"


def register_comms_tools(server) -> int:
    """Register all communication tools with the MCP server."""

    # Email tools
    server.register_tool(
        name="email_send",
        description="Send an email to a recipient.",
        input_schema={
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string", "description": "Email subject"},
                "body": {"type": "string", "description": "Email body"},
                "html": {"type": "boolean", "description": "Send as HTML", "default": False},
                "cc": {"type": "string", "description": "CC recipients (comma-separated)"},
                "from_addr": {"type": "string", "description": "From address"}
            },
            "required": ["to", "subject", "body"]
        },
        handler=email_send,
        requires_approval=True,
        category="comms"
    )

    server.register_tool(
        name="email_draft",
        description="Create an email draft without sending.",
        input_schema={
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string", "description": "Email subject"},
                "body": {"type": "string", "description": "Email body"},
                "format": {"type": "string", "description": "Output format (text/json)", "default": "text"}
            },
            "required": ["to", "subject", "body"]
        },
        handler=email_draft,
        requires_approval=False,
        category="comms"
    )

    # Calendar tools
    server.register_tool(
        name="calendar_list",
        description="List upcoming calendar events.",
        input_schema={
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Days to look ahead", "default": 7},
                "calendar": {"type": "string", "description": "Specific calendar to use"}
            }
        },
        handler=calendar_list,
        requires_approval=False,
        category="comms"
    )

    server.register_tool(
        name="calendar_add",
        description="Add a calendar event.",
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Event title"},
                "start": {"type": "string", "description": "Start time"},
                "end": {"type": "string", "description": "End time or duration"},
                "description": {"type": "string", "description": "Event description"},
                "location": {"type": "string", "description": "Event location"},
                "calendar": {"type": "string", "description": "Specific calendar"}
            },
            "required": ["title", "start"]
        },
        handler=calendar_add,
        requires_approval=True,
        category="comms"
    )

    server.register_tool(
        name="calendar_search",
        description="Search for calendar events.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search text"},
                "days": {"type": "integer", "description": "Days to search", "default": 30}
            },
            "required": ["query"]
        },
        handler=calendar_search,
        requires_approval=False,
        category="comms"
    )

    server.register_tool(
        name="calendar_delete",
        description="Delete a calendar event by title.",
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Event title to delete"},
                "calendar": {"type": "string", "description": "Specific calendar"}
            },
            "required": ["title"]
        },
        handler=calendar_delete,
        requires_approval=True,
        category="comms"
    )

    return 6  # Number of tools registered
