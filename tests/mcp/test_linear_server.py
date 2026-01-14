"""
Tests for Linear MCP server.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock


class TestLinearMCPServer:
    """Test Linear MCP server tools."""

    @pytest.fixture
    def server(self):
        """Import and return MCP server."""
        from integrations.mcp_servers.linear_server import linear_mcp_server
        return linear_mcp_server

    def test_server_exists(self, server):
        """Test MCP server is properly created."""
        assert server is not None
        assert hasattr(server, 'name')
        assert server.name == 'linear'

    @pytest.mark.asyncio
    async def test_get_teams_tool(self):
        """Test linear_get_teams tool."""
        from integrations.mcp_servers.linear_server import linear_get_teams

        mock_teams = [
            {'name': 'Engineering', 'key': 'ENG', 'issueCount': 10}
        ]

        with patch('integrations.mcp_servers.linear_server.LinearClient') as MockClient:
            mock_instance = AsyncMock()
            mock_instance.get_teams.return_value = mock_teams
            MockClient.return_value = mock_instance

            result = await linear_get_teams({})

            assert result is not None
            assert 'content' in result
            assert 'Engineering' in result['content'][0]['text']

    @pytest.mark.asyncio
    async def test_get_issues_tool(self):
        """Test linear_get_issues tool."""
        from integrations.mcp_servers.linear_server import linear_get_issues

        mock_issues = [
            {
                'identifier': 'ENG-123',
                'title': 'Test Issue',
                'state': {'name': 'In Progress'}
            }
        ]

        with patch('integrations.mcp_servers.linear_server.LinearClient') as MockClient:
            mock_instance = AsyncMock()
            mock_instance.get_issues.return_value = mock_issues
            MockClient.return_value = mock_instance

            args = {'limit': 10}
            result = await linear_get_issues(args)

            assert result is not None
            assert 'content' in result
            assert 'ENG-123' in result['content'][0]['text']

    @pytest.mark.asyncio
    async def test_create_issue_tool(self):
        """Test linear_create_issue tool."""
        from integrations.mcp_servers.linear_server import linear_create_issue

        mock_issue = {
            'identifier': 'ENG-124',
            'title': 'New Issue',
            'url': 'https://linear.app/issue/ENG-124'
        }

        with patch('integrations.mcp_servers.linear_server.LinearClient') as MockClient:
            mock_instance = AsyncMock()
            mock_instance.create_issue.return_value = mock_issue
            MockClient.return_value = mock_instance

            args = {
                'team_id': 'team-1',
                'title': 'New Issue',
                'description': 'Issue description'
            }
            result = await linear_create_issue(args)

            assert result is not None
            assert 'content' in result
            assert 'ENG-124' in result['content'][0]['text']

    @pytest.mark.asyncio
    async def test_search_issues_tool(self):
        """Test linear_search_issues tool."""
        from integrations.mcp_servers.linear_server import linear_search_issues

        mock_issues = [
            {'identifier': 'ENG-125', 'title': 'Search Result'}
        ]

        with patch('integrations.mcp_servers.linear_server.LinearClient') as MockClient:
            mock_instance = AsyncMock()
            mock_instance.search_issues.return_value = mock_issues
            MockClient.return_value = mock_instance

            args = {'query': 'test', 'limit': 20}
            result = await linear_search_issues(args)

            assert result is not None
            assert 'content' in result
