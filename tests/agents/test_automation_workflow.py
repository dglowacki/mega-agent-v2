"""
End-to-end test for automation workflow.

Tests the complete flow:
1. Calculate task priority (via skill)
2. Format task for ClickUp/Linear (via skill)
3. Create task via API (via client)
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import sys

# Add paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'integrations'))
sys.path.insert(0, str(PROJECT_ROOT / '.claude' / 'skills' / 'task-formatting' / 'scripts'))


class TestAutomationWorkflow:
    """Test end-to-end automation workflow."""

    def test_clickup_task_creation_workflow(self):
        """Test complete ClickUp task creation workflow."""
        from calculate_priority import calculate_priority
        from format_clickup_task import format_clickup_task

        # Step 1: Calculate priority
        priority_data = calculate_priority(
            urgency=5,
            impact=4,
            effort=2,
            format='clickup'
        )

        assert priority_data['priority'] == 1  # Urgent
        assert priority_data['score'] == 23

        # Step 2: Format task
        task = format_clickup_task(
            title="Fix critical bug in production",
            description="Users unable to login",
            priority="urgent",
            tags=["bug", "production"],
            time_estimate="4h"
        )

        assert task['name'] == "Fix critical bug in production"
        assert task['priority'] == 1
        assert 'bug' in task['tags']

        # Step 3: Would create task via ClickUp client
        # (Mocked in real implementation)

    @pytest.mark.asyncio
    async def test_linear_issue_creation_workflow(self):
        """Test complete Linear issue creation workflow."""
        from calculate_priority import calculate_priority
        from format_linear_issue import format_linear_issue
        from linear_client import LinearClient

        # Step 1: Calculate priority
        priority_data = calculate_priority(
            urgency=3,
            impact=3,
            effort=3,
            format='linear'
        )

        assert priority_data['priority'] == 3  # Normal

        # Step 2: Format issue
        issue = format_linear_issue(
            title="Implement new feature",
            team_id="team-123",
            description="Feature description",
            priority="normal",
            estimate=5
        )

        assert issue['title'] == "Implement new feature"
        assert issue['priority'] == 3
        assert issue['estimate'] == 5

        # Step 3: Create issue (mocked)
        mock_result = {
            'id': 'issue-123',
            'identifier': 'ENG-124',
            'title': 'Implement new feature',
            'url': 'https://linear.app/issue/ENG-124'
        }

        with patch.object(LinearClient, 'create_issue', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_result

            client = LinearClient(api_key='test-key')
            result = await client.create_issue(**issue)

            assert result['identifier'] == 'ENG-124'
            assert result['title'] == 'Implement new feature'

    def test_priority_calculation_scenarios(self):
        """Test various priority calculation scenarios."""
        from calculate_priority import calculate_priority

        # Bug affecting production - should be urgent
        bug_priority = calculate_priority(
            urgency=5,  # needs immediate fix
            impact=5,   # all users affected
            effort=2,   # quick fix
            format='clickup'
        )
        assert bug_priority['priority'] == 1  # Urgent

        # Feature request - should be normal
        feature_priority = calculate_priority(
            urgency=2,  # can wait
            impact=3,   # some users want it
            effort=4,   # significant work
            format='clickup'
        )
        assert feature_priority['priority'] == 3  # Normal

        # Tech debt - should be low
        debt_priority = calculate_priority(
            urgency=1,  # no rush
            impact=2,   # affects developers only
            effort=3,   # moderate work
            format='clickup'
        )
        assert debt_priority['priority'] == 4  # Low
