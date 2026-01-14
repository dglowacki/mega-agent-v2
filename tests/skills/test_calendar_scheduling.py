"""
Tests for calendar-scheduling skill.
"""

import pytest
from datetime import datetime
from pathlib import Path
import sys

# Add skills to path
SKILLS_PATH = Path(__file__).parent.parent.parent / '.claude' / 'skills' / 'calendar-scheduling' / 'scripts'
sys.path.insert(0, str(SKILLS_PATH))


class TestCalendarScheduling:
    """Test calendar scheduling skill scripts."""

    def test_format_event(self):
        """Test event formatting."""
        from format_event import format_event

        event = format_event(
            title="Team Meeting",
            start="2026-01-20 14:00",
            duration="1h",
            attendees=["user1@example.com", "user2@example.com"],
            location="Conference Room A",
            reminder_minutes=15
        )

        assert event['summary'] == "Team Meeting"
        assert event['location'] == "Conference Room A"
        assert len(event['attendees']) == 2
        assert event['reminders']['overrides'][0]['minutes'] == 15

    def test_parse_duration(self):
        """Test duration parsing."""
        from format_event import parse_duration

        assert parse_duration("30m") == 30
        assert parse_duration("1h") == 60
        assert parse_duration("1h30m") == 90
        assert parse_duration("2h") == 120

    def test_detect_conflicts_overlap(self, mock_calendar_event):
        """Test conflict detection with overlapping events."""
        from detect_conflicts import detect_conflicts

        existing_events = [mock_calendar_event]

        # Create overlapping event
        new_event = {
            'summary': 'Conflicting Meeting',
            'start': {'dateTime': '2026-01-20T14:30:00-08:00'},
            'end': {'dateTime': '2026-01-20T15:30:00-08:00'}
        }

        result = detect_conflicts(existing_events, new_event)

        assert result['has_conflicts'] is True
        assert len(result['hard_conflicts']) == 1

    def test_detect_conflicts_no_overlap(self, mock_calendar_event):
        """Test no conflicts when events don't overlap."""
        from detect_conflicts import detect_conflicts

        existing_events = [mock_calendar_event]

        # Create non-overlapping event
        new_event = {
            'summary': 'Later Meeting',
            'start': {'dateTime': '2026-01-20T16:00:00-08:00'},
            'end': {'dateTime': '2026-01-20T17:00:00-08:00'}
        }

        result = detect_conflicts(existing_events, new_event)

        assert result['has_conflicts'] is False
        assert len(result['hard_conflicts']) == 0

    def test_detect_conflicts_with_buffer(self, mock_calendar_event):
        """Test conflict detection with buffer time."""
        from detect_conflicts import detect_conflicts

        existing_events = [mock_calendar_event]

        # Create back-to-back event (no buffer)
        new_event = {
            'summary': 'Back to Back Meeting',
            'start': {'dateTime': '2026-01-20T15:00:00-08:00'},
            'end': {'dateTime': '2026-01-20T16:00:00-08:00'}
        }

        result = detect_conflicts(existing_events, new_event, buffer_minutes=15)

        assert result['has_conflicts'] is False  # No hard conflict
        assert len(result['soft_conflicts']) == 1  # But soft conflict due to buffer
