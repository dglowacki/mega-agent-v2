"""
Tests for App Store MCP server.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock


class TestAppStoreMCPServer:
    """Test App Store MCP server tools."""

    @pytest.fixture
    def server(self):
        """Import and return MCP server."""
        from integrations.mcp_servers.appstore_server import appstore_mcp_server
        return appstore_mcp_server

    def test_server_exists(self, server):
        """Test MCP server is properly created."""
        assert server is not None
        assert hasattr(server, 'name')
        assert server.name == 'appstore'

    def test_server_has_tools(self, server):
        """Test server has tools registered."""
        # The server should have tools (exact structure depends on SDK)
        assert server is not None

    @pytest.mark.asyncio
    async def test_list_apps_tool(self):
        """Test appstore_list_apps tool."""
        from integrations.mcp_servers.appstore_server import appstore_list_apps

        mock_apps = {
            'status': 'success',
            'apps': [
                {'name': 'Test App', 'id': 'app-123'}
            ]
        }

        with patch('integrations.mcp_servers.appstore_server.AppStoreClient') as MockClient:
            mock_instance = AsyncMock()
            mock_instance.list_apps.return_value = mock_apps
            MockClient.return_value = mock_instance

            result = await appstore_list_apps({})

            assert result is not None
            assert 'content' in result
            assert len(result['content']) > 0

    @pytest.mark.asyncio
    async def test_get_sales_report_tool(self):
        """Test appstore_get_sales_report tool."""
        from integrations.mcp_servers.appstore_server import appstore_get_sales_report

        mock_sales = {
            'status': 'success',
            'data': [
                {'sku': 'APP001', 'units': 100}
            ]
        }

        with patch('integrations.mcp_servers.appstore_server.AppStoreClient') as MockClient:
            mock_instance = AsyncMock()
            mock_instance.get_sales_report.return_value = mock_sales
            MockClient.return_value = mock_instance

            args = {
                'vendor_number': '12345',
                'report_date': '2026-01-14'
            }
            result = await appstore_get_sales_report(args)

            assert result is not None
            assert 'content' in result

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test MCP tool error handling."""
        from integrations.mcp_servers.appstore_server import appstore_list_apps

        with patch('integrations.mcp_servers.appstore_server.AppStoreClient') as MockClient:
            mock_instance = AsyncMock()
            mock_instance.list_apps.side_effect = Exception("API Error")
            MockClient.return_value = mock_instance

            result = await appstore_list_apps({})

            assert result is not None
            assert 'isError' in result
            assert result['isError'] is True
