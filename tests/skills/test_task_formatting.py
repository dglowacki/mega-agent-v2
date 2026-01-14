"""
Tests for task-formatting skill.
"""

import pytest
from pathlib import Path
import sys

# Add skills to path
SKILLS_PATH = Path(__file__).parent.parent.parent / '.claude' / 'skills' / 'task-formatting' / 'scripts'
sys.path.insert(0, str(SKILLS_PATH))


class TestTaskFormatting:
    """Test task formatting skill scripts."""

    def test_calculate_priority_urgent(self):
        """Test priority calculation for urgent task."""
        from calculate_priority import calculate_priority

        result = calculate_priority(
            urgency=5,
            impact=5,
            effort=2,
            format='clickup'
        )

        assert result['score'] == 23  # (5*3) + (5*2) + (2*-1)
        assert result['priority'] == 1  # Urgent
        assert result['priority_label'] == 'Urgent'

    def test_calculate_priority_normal(self):
        """Test priority calculation for normal task."""
        from calculate_priority import calculate_priority

        result = calculate_priority(
            urgency=2,
            impact=3,
            effort=4,
            format='clickup'
        )

        assert result['score'] == 8  # (2*3) + (3*2) + (4*-1)
        assert result['priority'] == 3  # Normal

    def test_calculate_priority_low(self):
        """Test priority calculation for low priority task."""
        from calculate_priority import calculate_priority

        result = calculate_priority(
            urgency=1,
            impact=2,
            effort=3,
            format='clickup'
        )

        assert result['score'] == 4  # (1*3) + (2*2) + (3*-1)
        assert result['priority'] == 4  # Low

    def test_format_clickup_task(self):
        """Test ClickUp task formatting."""
        from format_clickup_task import format_clickup_task

        task = format_clickup_task(
            title="Test Task",
            description="Task description",
            priority="high",
            tags=["bug", "urgent"],
            status="to do"
        )

        assert task['name'] == "Test Task"
        assert task['description'] == "Task description"
        assert task['priority'] == 2  # High
        assert task['tags'] == ["bug", "urgent"]
        assert task['status'] == "to do"

    def test_format_clickup_task_with_estimate(self):
        """Test ClickUp task with time estimate."""
        from format_clickup_task import format_clickup_task, parse_time_estimate

        # Test time parsing
        assert parse_time_estimate("1h") == 3600000  # 1 hour in ms
        assert parse_time_estimate("30m") == 1800000  # 30 min in ms
        assert parse_time_estimate("2d") == 57600000  # 2 days (16 hours) in ms

        task = format_clickup_task(
            title="Test Task",
            time_estimate="4h"
        )

        assert task['time_estimate'] == 14400000  # 4 hours in ms

    def test_format_linear_issue(self):
        """Test Linear issue formatting."""
        from format_linear_issue import format_linear_issue

        issue = format_linear_issue(
            title="Test Issue",
            team_id="team-123",
            description="Issue description",
            priority="urgent",
            labels=["bug"],
            estimate=3
        )

        assert issue['title'] == "Test Issue"
        assert issue['teamId'] == "team-123"
        assert issue['description'] == "Issue description"
        assert issue['priority'] == 1  # Urgent
        assert issue['labels'] == ["bug"]
        assert issue['estimate'] == 3
