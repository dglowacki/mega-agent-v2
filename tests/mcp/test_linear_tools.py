"""
Tests for Linear MCP tools (mcp/tools/linear_tools.py).

Tests the 21 Linear tools for issue, project, team, cycle, label,
comment, user, and organization operations.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock


class TestLinearToolImports:
    """Test that Linear tools import correctly."""

    def test_import_linear_tools(self):
        from mcp.tools.linear_tools import (
            linear_list_issues,
            linear_create_issue,
            linear_get_issue,
            linear_update_issue,
            linear_delete_issue,
            linear_search_issues,
        )
        assert callable(linear_list_issues)
        assert callable(linear_create_issue)

    def test_import_team_tools(self):
        from mcp.tools.linear_tools import linear_list_teams, linear_get_team
        assert callable(linear_list_teams)
        assert callable(linear_get_team)

    def test_import_project_tools(self):
        from mcp.tools.linear_tools import (
            linear_list_projects,
            linear_get_project,
            linear_create_project,
        )
        assert callable(linear_list_projects)

    def test_import_cycle_tools(self):
        from mcp.tools.linear_tools import (
            linear_list_cycles,
            linear_get_active_cycle,
            linear_create_cycle,
        )
        assert callable(linear_list_cycles)

    def test_import_label_tools(self):
        from mcp.tools.linear_tools import linear_list_labels, linear_create_label
        assert callable(linear_list_labels)

    def test_import_user_tools(self):
        from mcp.tools.linear_tools import linear_list_users, linear_get_viewer
        assert callable(linear_list_users)

    def test_import_comment_tools(self):
        from mcp.tools.linear_tools import linear_add_comment
        assert callable(linear_add_comment)

    def test_import_workflow_org_tools(self):
        from mcp.tools.linear_tools import (
            linear_get_workflow_states,
            linear_get_organization,
        )
        assert callable(linear_get_workflow_states)


class TestToolRegistration:
    """Test that Linear tools register correctly with MCP server."""

    def test_register_linear_tools(self):
        from mcp.protocol import MCPServer
        from mcp.tools.linear_tools import register_linear_tools

        server = MCPServer()
        count = register_linear_tools(server)

        assert count == 21

        # Verify all tools are registered
        expected_tools = [
            "linear_list_issues",
            "linear_create_issue",
            "linear_get_issue",
            "linear_update_issue",
            "linear_delete_issue",
            "linear_search_issues",
            "linear_add_comment",
            "linear_list_teams",
            "linear_get_team",
            "linear_list_projects",
            "linear_get_project",
            "linear_create_project",
            "linear_list_cycles",
            "linear_get_active_cycle",
            "linear_create_cycle",
            "linear_list_labels",
            "linear_create_label",
            "linear_list_users",
            "linear_get_viewer",
            "linear_get_workflow_states",
            "linear_get_organization",
        ]

        for tool in expected_tools:
            assert tool in server._tools, f"Missing Linear tool: {tool}"

    def test_tools_have_correct_category(self):
        from mcp.protocol import MCPServer
        from mcp.tools.linear_tools import register_linear_tools

        server = MCPServer()
        register_linear_tools(server)

        for name, tool in server._tools.items():
            if name.startswith("linear_"):
                assert tool.category == "linear", f"{name} has wrong category"

    def test_write_tools_require_approval(self):
        from mcp.protocol import MCPServer
        from mcp.tools.linear_tools import register_linear_tools

        server = MCPServer()
        register_linear_tools(server)

        write_tools = [
            "linear_create_issue",
            "linear_update_issue",
            "linear_delete_issue",
            "linear_add_comment",
            "linear_create_project",
            "linear_create_cycle",
            "linear_create_label",
        ]

        for tool_name in write_tools:
            tool = server._tools[tool_name]
            assert tool.requires_approval, f"{tool_name} should require approval"

    def test_read_tools_no_approval(self):
        from mcp.protocol import MCPServer
        from mcp.tools.linear_tools import register_linear_tools

        server = MCPServer()
        register_linear_tools(server)

        read_tools = [
            "linear_list_issues",
            "linear_get_issue",
            "linear_search_issues",
            "linear_list_teams",
            "linear_get_team",
            "linear_list_projects",
            "linear_get_project",
            "linear_list_cycles",
            "linear_get_active_cycle",
            "linear_list_labels",
            "linear_list_users",
            "linear_get_viewer",
            "linear_get_workflow_states",
            "linear_get_organization",
        ]

        for tool_name in read_tools:
            tool = server._tools[tool_name]
            assert not tool.requires_approval, f"{tool_name} should not require approval"


class TestIssueTools:
    """Test issue-related tools."""

    @patch('mcp.tools.linear_tools._get_linear')
    def test_list_issues_success(self, mock_get_linear):
        from mcp.tools.linear_tools import linear_list_issues

        mock_client = Mock()
        mock_client.get_issues = AsyncMock(return_value=[
            {
                'identifier': 'PROJ-123',
                'title': 'Test Issue',
                'state': {'name': 'In Progress'},
                'assignee': {'name': 'John Doe'}
            },
            {
                'identifier': 'PROJ-124',
                'title': 'Another Issue',
                'state': {'name': 'Done'},
                'assignee': None
            }
        ])
        mock_get_linear.return_value = mock_client

        result = linear_list_issues()

        assert "Linear Issues (2)" in result
        assert "PROJ-123" in result
        assert "Test Issue" in result
        assert "In Progress" in result
        assert "John Doe" in result
        assert "PROJ-124" in result
        assert "Unassigned" in result

    @patch('mcp.tools.linear_tools._get_linear')
    def test_list_issues_empty(self, mock_get_linear):
        from mcp.tools.linear_tools import linear_list_issues

        mock_client = Mock()
        mock_client.get_issues = AsyncMock(return_value=[])
        mock_get_linear.return_value = mock_client

        result = linear_list_issues()
        assert "No issues found" in result

    @patch('mcp.tools.linear_tools._get_linear')
    def test_list_issues_not_configured(self, mock_get_linear):
        from mcp.tools.linear_tools import linear_list_issues

        mock_get_linear.return_value = None

        result = linear_list_issues()
        assert "Error: Linear not configured" in result

    @patch('mcp.tools.linear_tools._get_linear')
    def test_create_issue_success(self, mock_get_linear):
        from mcp.tools.linear_tools import linear_create_issue

        mock_client = Mock()
        mock_client.create_issue = AsyncMock(return_value={
            'identifier': 'PROJ-125',
            'title': 'New Issue',
            'url': 'https://linear.app/team/issue/PROJ-125'
        })
        mock_get_linear.return_value = mock_client

        result = linear_create_issue(
            title="New Issue",
            team_id="team-123",
            description="A test issue",
            priority=2
        )

        assert "Created issue: PROJ-125" in result
        assert "New Issue" in result
        assert "https://linear.app" in result

    @patch('mcp.tools.linear_tools._get_linear')
    def test_get_issue_success(self, mock_get_linear):
        from mcp.tools.linear_tools import linear_get_issue

        mock_client = Mock()
        mock_client.get_issue = AsyncMock(return_value={
            'identifier': 'PROJ-123',
            'title': 'Test Issue',
            'state': {'name': 'In Progress'},
            'priorityLabel': 'High',
            'team': {'name': 'Engineering'},
            'assignee': {'name': 'John Doe'},
            'description': 'Test description',
            'url': 'https://linear.app/issue/PROJ-123',
            'labels': {'nodes': [{'name': 'Bug'}, {'name': 'P1'}]},
            'children': {'nodes': []},
            'comments': {'nodes': []}
        })
        mock_get_linear.return_value = mock_client

        result = linear_get_issue("PROJ-123")

        assert "PROJ-123" in result
        assert "Test Issue" in result
        assert "In Progress" in result
        assert "High" in result
        assert "Engineering" in result
        assert "John Doe" in result
        assert "Bug" in result
        assert "P1" in result

    @patch('mcp.tools.linear_tools._get_linear')
    def test_update_issue_success(self, mock_get_linear):
        from mcp.tools.linear_tools import linear_update_issue

        mock_client = Mock()
        mock_client.update_issue = AsyncMock(return_value={
            'url': 'https://linear.app/issue/PROJ-123'
        })
        mock_get_linear.return_value = mock_client

        result = linear_update_issue(
            identifier="PROJ-123",
            title="Updated Title",
            priority=1
        )

        assert "Updated issue PROJ-123" in result

    @patch('mcp.tools.linear_tools._get_linear')
    def test_search_issues_success(self, mock_get_linear):
        from mcp.tools.linear_tools import linear_search_issues

        mock_client = Mock()
        mock_client.search_issues = AsyncMock(return_value=[
            {
                'identifier': 'PROJ-100',
                'title': 'Auth bug',
                'state': {'name': 'Open'},
                'team': {'key': 'ENG'}
            }
        ])
        mock_get_linear.return_value = mock_client

        result = linear_search_issues("auth bug")

        assert "Search Results" in result
        assert "auth bug" in result
        assert "PROJ-100" in result
        assert "Auth bug" in result


class TestTeamTools:
    """Test team-related tools."""

    @patch('mcp.tools.linear_tools._get_linear')
    def test_list_teams_success(self, mock_get_linear):
        from mcp.tools.linear_tools import linear_list_teams

        mock_client = Mock()
        mock_client.get_teams = AsyncMock(return_value=[
            {'key': 'ENG', 'name': 'Engineering', 'issueCount': 42},
            {'key': 'DES', 'name': 'Design', 'issueCount': 15}
        ])
        mock_get_linear.return_value = mock_client

        result = linear_list_teams()

        assert "Linear Teams" in result
        assert "[ENG] Engineering" in result
        assert "42 issues" in result
        assert "[DES] Design" in result

    @patch('mcp.tools.linear_tools._get_linear')
    def test_get_team_with_states_and_labels(self, mock_get_linear):
        from mcp.tools.linear_tools import linear_get_team

        mock_client = Mock()
        mock_client.get_team = AsyncMock(return_value={
            'name': 'Engineering',
            'key': 'ENG',
            'issueCount': 42,
            'description': 'The engineering team',
            'states': {
                'nodes': [
                    {'name': 'Backlog', 'type': 'backlog', 'id': 'state-1'},
                    {'name': 'In Progress', 'type': 'started', 'id': 'state-2'},
                    {'name': 'Done', 'type': 'completed', 'id': 'state-3'}
                ]
            },
            'labels': {
                'nodes': [
                    {'name': 'Bug', 'id': 'label-1'},
                    {'name': 'Feature', 'id': 'label-2'}
                ]
            }
        })
        mock_get_linear.return_value = mock_client

        result = linear_get_team("team-123")

        assert "Engineering" in result
        assert "ENG" in result
        assert "Workflow States" in result
        assert "Backlog" in result
        assert "In Progress" in result
        assert "Labels" in result
        assert "Bug" in result


class TestProjectTools:
    """Test project-related tools."""

    @patch('mcp.tools.linear_tools._get_linear')
    def test_list_projects_success(self, mock_get_linear):
        from mcp.tools.linear_tools import linear_list_projects

        mock_client = Mock()
        mock_client.get_projects = AsyncMock(return_value=[
            {'id': 'proj-1', 'name': 'Q1 Launch', 'state': 'started', 'progress': 0.75},
            {'id': 'proj-2', 'name': 'API Redesign', 'state': 'planned', 'progress': 0.1}
        ])
        mock_get_linear.return_value = mock_client

        result = linear_list_projects()

        assert "Linear Projects" in result
        assert "Q1 Launch" in result
        assert "75%" in result
        assert "API Redesign" in result

    @patch('mcp.tools.linear_tools._get_linear')
    def test_create_project_success(self, mock_get_linear):
        from mcp.tools.linear_tools import linear_create_project

        mock_client = Mock()
        mock_client.create_project = AsyncMock(return_value={
            'id': 'proj-new',
            'name': 'New Project',
            'url': 'https://linear.app/project/proj-new'
        })
        mock_get_linear.return_value = mock_client

        result = linear_create_project(
            name="New Project",
            team_ids="team-1,team-2",
            description="Test project"
        )

        assert "Created project: New Project" in result


class TestCycleTools:
    """Test cycle-related tools."""

    @patch('mcp.tools.linear_tools._get_linear')
    def test_list_cycles_success(self, mock_get_linear):
        from mcp.tools.linear_tools import linear_list_cycles

        mock_client = Mock()
        mock_client.get_cycles = AsyncMock(return_value=[
            {
                'id': 'cycle-1',
                'name': 'Sprint 1',
                'number': 1,
                'progress': 0.5,
                'startsAt': '2026-01-01T00:00:00Z',
                'endsAt': '2026-01-15T00:00:00Z'
            }
        ])
        mock_get_linear.return_value = mock_client

        result = linear_list_cycles("team-123")

        assert "Cycles for team" in result
        assert "Sprint 1" in result
        assert "50%" in result

    @patch('mcp.tools.linear_tools._get_linear')
    def test_get_active_cycle_with_issues(self, mock_get_linear):
        from mcp.tools.linear_tools import linear_get_active_cycle

        mock_client = Mock()
        mock_client.get_active_cycle = AsyncMock(return_value={
            'name': 'Sprint 5',
            'number': 5,
            'progress': 0.3,
            'startsAt': '2026-01-13T00:00:00Z',
            'endsAt': '2026-01-27T00:00:00Z',
            'issues': {
                'nodes': [
                    {
                        'identifier': 'PROJ-50',
                        'title': 'Sprint task',
                        'state': {'name': 'In Progress'},
                        'assignee': {'name': 'Dev'}
                    }
                ]
            }
        })
        mock_get_linear.return_value = mock_client

        result = linear_get_active_cycle("team-123")

        assert "Active Cycle: Sprint 5" in result
        assert "30%" in result
        assert "PROJ-50" in result
        assert "Sprint task" in result


class TestLabelTools:
    """Test label-related tools."""

    @patch('mcp.tools.linear_tools._get_linear')
    def test_list_labels_success(self, mock_get_linear):
        from mcp.tools.linear_tools import linear_list_labels

        mock_client = Mock()
        mock_client.get_labels = AsyncMock(return_value=[
            {'id': 'label-1', 'name': 'Bug', 'team': {'name': 'Engineering'}},
            {'id': 'label-2', 'name': 'Feature', 'team': None}
        ])
        mock_get_linear.return_value = mock_client

        result = linear_list_labels()

        assert "Linear Labels" in result
        assert "Bug" in result
        assert "Feature" in result

    @patch('mcp.tools.linear_tools._get_linear')
    def test_create_label_success(self, mock_get_linear):
        from mcp.tools.linear_tools import linear_create_label

        mock_client = Mock()
        mock_client.create_label = AsyncMock(return_value={
            'id': 'label-new',
            'name': 'P0'
        })
        mock_get_linear.return_value = mock_client

        result = linear_create_label(
            team_id="team-123",
            name="P0",
            color="#ff0000"
        )

        assert "Created label: P0" in result


class TestUserTools:
    """Test user-related tools."""

    @patch('mcp.tools.linear_tools._get_linear')
    def test_list_users_success(self, mock_get_linear):
        from mcp.tools.linear_tools import linear_list_users

        mock_client = Mock()
        mock_client.get_users = AsyncMock(return_value=[
            {'id': 'user-1', 'name': 'John Doe', 'email': 'john@example.com', 'active': True, 'admin': False},
            {'id': 'user-2', 'name': 'Admin User', 'email': 'admin@example.com', 'active': True, 'admin': True}
        ])
        mock_get_linear.return_value = mock_client

        result = linear_list_users()

        assert "Linear Users" in result
        assert "John Doe" in result
        assert "john@example.com" in result
        assert "Admin User" in result
        assert "(Admin)" in result

    @patch('mcp.tools.linear_tools._get_linear')
    def test_get_viewer_success(self, mock_get_linear):
        from mcp.tools.linear_tools import linear_get_viewer

        mock_client = Mock()
        mock_client.get_viewer = AsyncMock(return_value={
            'name': 'Current User',
            'email': 'me@example.com',
            'displayName': 'Me',
            'admin': False,
            'assignedIssues': {
                'nodes': [
                    {'identifier': 'PROJ-1', 'title': 'My task', 'state': {'name': 'Todo'}}
                ]
            }
        })
        mock_get_linear.return_value = mock_client

        result = linear_get_viewer()

        assert "Current User" in result
        assert "me@example.com" in result
        assert "Assigned Issues" in result
        assert "PROJ-1" in result
        assert "My task" in result


class TestCommentTools:
    """Test comment-related tools."""

    @patch('mcp.tools.linear_tools._get_linear')
    def test_add_comment_success(self, mock_get_linear):
        from mcp.tools.linear_tools import linear_add_comment

        mock_client = Mock()
        mock_client.add_comment = AsyncMock(return_value={'id': 'comment-1'})
        mock_get_linear.return_value = mock_client

        result = linear_add_comment("PROJ-123", "This is a comment")

        assert "Added comment to PROJ-123" in result


class TestWorkflowOrgTools:
    """Test workflow and organization tools."""

    @patch('mcp.tools.linear_tools._get_linear')
    def test_get_workflow_states_success(self, mock_get_linear):
        from mcp.tools.linear_tools import linear_get_workflow_states

        mock_client = Mock()
        mock_client.get_workflow_states = AsyncMock(return_value=[
            {'id': 'state-1', 'name': 'Backlog', 'type': 'backlog'},
            {'id': 'state-2', 'name': 'In Progress', 'type': 'started'},
            {'id': 'state-3', 'name': 'Done', 'type': 'completed'}
        ])
        mock_get_linear.return_value = mock_client

        result = linear_get_workflow_states("team-123")

        assert "Workflow States" in result
        assert "Backlog" in result
        assert "In Progress" in result
        assert "Done" in result
        assert "state-1" in result

    @patch('mcp.tools.linear_tools._get_linear')
    def test_get_organization_success(self, mock_get_linear):
        from mcp.tools.linear_tools import linear_get_organization

        mock_client = Mock()
        mock_client.get_organization = AsyncMock(return_value={
            'name': 'Acme Corp',
            'urlKey': 'acme',
            'createdAt': '2024-01-01T00:00:00Z'
        })
        mock_get_linear.return_value = mock_client

        result = linear_get_organization()

        assert "Acme Corp" in result
        assert "acme" in result


class TestErrorHandling:
    """Test error handling across tools."""

    @patch('mcp.tools.linear_tools._get_linear')
    def test_handles_api_error(self, mock_get_linear):
        from mcp.tools.linear_tools import linear_list_issues

        mock_client = Mock()
        mock_client.get_issues = AsyncMock(side_effect=Exception("API rate limit exceeded"))
        mock_get_linear.return_value = mock_client

        result = linear_list_issues()
        assert "Error listing issues" in result
        assert "rate limit" in result

    @patch('mcp.tools.linear_tools._get_linear')
    def test_handles_not_found(self, mock_get_linear):
        from mcp.tools.linear_tools import linear_get_issue

        mock_client = Mock()
        mock_client.get_issue = AsyncMock(return_value=None)
        mock_get_linear.return_value = mock_client

        result = linear_get_issue("INVALID-123")
        assert "not found" in result


class TestAsyncWrapper:
    """Test the async wrapper function."""

    def test_run_async_new_loop(self):
        from mcp.tools.linear_tools import _run_async
        import asyncio

        async def simple_coro():
            return "success"

        result = _run_async(simple_coro())
        assert result == "success"


class TestIntegration:
    """Integration tests for the Linear tools."""

    def test_full_registration_includes_linear(self):
        from mcp.protocol import MCPServer
        from mcp.tools import register_all_tools

        server = MCPServer()
        count = register_all_tools(server)

        # Should have Linear tools
        linear_tools = [
            "linear_list_issues", "linear_create_issue",
            "linear_list_teams", "linear_get_viewer"
        ]
        for tool in linear_tools:
            assert tool in server._tools, f"Missing Linear tool: {tool}"

    def test_all_linear_tools_have_descriptions(self):
        from mcp.protocol import MCPServer
        from mcp.tools.linear_tools import register_linear_tools

        server = MCPServer()
        register_linear_tools(server)

        for name, tool in server._tools.items():
            assert tool.description, f"{name} missing description"
            assert len(tool.description) > 10, f"{name} description too short"

    def test_all_linear_tools_have_input_schema(self):
        from mcp.protocol import MCPServer
        from mcp.tools.linear_tools import register_linear_tools

        server = MCPServer()
        register_linear_tools(server)

        for name, tool in server._tools.items():
            assert tool.input_schema is not None, f"{name} missing input_schema"
            assert "type" in tool.input_schema, f"{name} schema missing type"
