"""
External API integrations for mega-agent2.

All integration clients for external services and APIs.
"""

# Core communication
from .slack_client import SlackMessageReader as SlackClient
from .gmail_client import GmailClient

# Google services
from .google_calendar_client import GoogleCalendarClient
from .google_tasks_client import GoogleTasksClient
from .google_ads_client import GoogleAdsClient

# Project management
from .clickup_client import ClickUpClient
from .linear_client import LinearClient

# Development platforms
from .firebase_client import FirebaseClient
from .supabase_client import SupabaseClient

# Content & publishing
from .wordpress_client import WordPressClient
from .appstore_client import AppStoreConnectClient as AppStoreClient

# Cloud & infrastructure
from .aws_client import AWSClient

# Voice & AI
from .grok_voice_client import GrokVoiceClient

__all__ = [
    # Core communication
    'SlackClient',
    'GmailClient',
    # Google services
    'GoogleCalendarClient',
    'GoogleTasksClient',
    'GoogleAdsClient',
    # Project management
    'ClickUpClient',
    'LinearClient',
    # Development platforms
    'FirebaseClient',
    'SupabaseClient',
    # Content & publishing
    'WordPressClient',
    'AppStoreClient',
    # Cloud & infrastructure
    'AWSClient',
    # Voice & AI
    'GrokVoiceClient',
]
