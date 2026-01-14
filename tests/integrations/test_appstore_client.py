"""
Tests for App Store Connect client.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from integrations.appstore_client import AppStoreClient


class TestAppStoreClient:
    """Test App Store Connect client functionality."""

    @pytest.fixture
    def client(self):
        """Create client instance with mock credentials."""
        with patch('integrations.appstore_client.Path'):
            return AppStoreClient()

    def test_initialization(self, client):
        """Test client initializes correctly."""
        assert client is not None
        assert hasattr(client, 'key_id')
        assert hasattr(client, 'issuer_id')

    @pytest.mark.asyncio
    async def test_list_apps_mock(self, client, mock_appstore_response):
        """Test list_apps with mocked response."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_appstore_response

            result = await client.list_apps()

            assert result['status'] == 'success'
            assert 'apps' in result
            assert len(result['apps']) > 0
            assert result['apps'][0]['name'] == 'Test App'

    @pytest.mark.asyncio
    async def test_get_sales_report_mock(self, client):
        """Test get_sales_report with mocked response."""
        mock_tsv_data = b"""Provider\tSKU\tTitle\tUnits\tDeveloper Proceeds
Apple\tAPP001\tTest App\t10\t5.99"""

        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_tsv_data

            result = await client.get_sales_report(
                vendor_number='12345',
                report_date='2026-01-14'
            )

            assert result['status'] == 'success'
            assert 'data' in result
            assert len(result['data']) > 0

    @pytest.mark.asyncio
    @pytest.mark.live
    async def test_list_apps_live(self, client):
        """Test list_apps with live API (requires credentials)."""
        result = await client.list_apps()

        assert result['status'] == 'success'
        assert 'apps' in result
        # Should have at least one app
        assert isinstance(result['apps'], list)

    @pytest.mark.asyncio
    async def test_error_handling(self, client):
        """Test error handling for API failures."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = Exception("API Error")

            result = await client.list_apps()

            assert result['status'] == 'failed'
            assert 'error' in result
            assert 'API Error' in result['error']
