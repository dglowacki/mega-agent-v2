"""
Tests for Linear GraphQL client.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from integrations.linear_client import LinearClient


class TestLinearClient:
    """Test Linear client functionality."""

    @pytest.fixture
    def client(self):
        """Create client instance."""
        return LinearClient(api_key="test-key")

    def test_initialization(self, client):
        """Test client initializes correctly."""
        assert client is not None
        assert client.api_key == "test-key"
        assert hasattr(client, 'base_url')

    @pytest.mark.asyncio
    async def test_get_teams_mock(self, client):
        """Test get_teams with mocked response."""
        mock_response = {
            "data": {
                "teams": {
                    "nodes": [
                        {"id": "team-1", "name": "Engineering", "key": "ENG"}
                    ]
                }
            }
        }

        with patch.object(client, '_graphql_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await client.get_teams()

            assert len(result) == 1
            assert result[0]['name'] == 'Engineering'
            assert result[0]['key'] == 'ENG'

    @pytest.mark.asyncio
    async def test_get_issues_mock(self, client):
        """Test get_issues with mocked response."""
        mock_response = {
            "data": {
                "issues": {
                    "nodes": [
                        {
                            "id": "issue-1",
                            "identifier": "ENG-123",
                            "title": "Test Issue",
                            "state": {"name": "In Progress"}
                        }
                    ]
                }
            }
        }

        with patch.object(client, '_graphql_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await client.get_issues(limit=10)

            assert len(result) == 1
            assert result[0]['identifier'] == 'ENG-123'
            assert result[0]['title'] == 'Test Issue'

    @pytest.mark.asyncio
    async def test_create_issue_mock(self, client):
        """Test create_issue with mocked response."""
        mock_response = {
            "data": {
                "issueCreate": {
                    "issue": {
                        "id": "new-issue",
                        "identifier": "ENG-124",
                        "title": "New Issue"
                    }
                }
            }
        }

        with patch.object(client, '_graphql_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await client.create_issue(
                team_id="team-1",
                title="New Issue",
                description="Issue description"
            )

            assert result['identifier'] == 'ENG-124'
            assert result['title'] == 'New Issue'

    @pytest.mark.asyncio
    @pytest.mark.live
    async def test_get_teams_live(self, client):
        """Test get_teams with live API (requires credentials)."""
        result = await client.get_teams()

        assert isinstance(result, list)
        # Should have at least one team
        if len(result) > 0:
            assert 'name' in result[0]
            assert 'key' in result[0]
