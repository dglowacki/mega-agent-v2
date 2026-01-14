#!/usr/bin/env python3
"""
Gmail Client for mega-agent2

Simplified Gmail integration without core dependencies.
"""

import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

load_dotenv()

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
]


class GmailClient:
    """Simplified Gmail client for mega-agent2."""

    def __init__(self, account='flycow'):
        """
        Initialize Gmail client.

        Args:
            account: 'flycow' or 'aquarius' - determines which credentials to use
        """
        if not GOOGLE_AVAILABLE:
            raise Exception("Google API libraries not installed. Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")

        # Determine credential file based on account
        if account == 'flycow':
            credential_file = 'google-credentials-flycow.json'
            user_email = 'dave@flycowgames.com'
        elif account == 'aquarius':
            credential_file = 'google-credentials-aquarius.json'
            user_email = 'dave@aquariusinternet.com'
        else:
            raise ValueError(f"Unknown account: {account}")

        # Check if credential file exists
        if not os.path.exists(credential_file):
            raise FileNotFoundError(f"Credential file not found: {credential_file}")

        credentials = service_account.Credentials.from_service_account_file(
            credential_file,
            scopes=SCOPES
        )

        # Impersonate user
        credentials = credentials.with_subject(user_email)

        self.service = build('gmail', 'v1', credentials=credentials)
        self.user_id = 'me'
        self.account = account

    def send_email(self, to, subject, body, body_html=None, attachment_path=None):
        """
        Send an email.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text body
            body_html: HTML body (optional)
            attachment_path: Path to file to attach (optional)

        Returns:
            Message object
        """
        try:
            # Create message
            if body_html:
                message = MIMEMultipart('alternative')
                message['to'] = to
                message['subject'] = subject

                # Add plain text and HTML parts
                part1 = MIMEText(body, 'plain')
                part2 = MIMEText(body_html, 'html')
                message.attach(part1)
                message.attach(part2)
            else:
                message = MIMEText(body)
                message['to'] = to
                message['subject'] = subject

            # Add attachment if provided
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(attachment_path)}'
                    )
                    message.attach(part)

            # Encode and send
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            send_message = {'raw': raw}

            result = self.service.users().messages().send(
                userId=self.user_id,
                body=send_message
            ).execute()

            print(f"Email sent! Message ID: {result['id']}")
            return result

        except HttpError as error:
            print(f"An error occurred: {error}")
            raise
