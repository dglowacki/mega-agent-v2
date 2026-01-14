"""
Tests for WordPress client.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from integrations.wordpress_client import WordPressClient


class TestWordPressClient:
    """Test WordPress client functionality."""

    @pytest.fixture
    def client(self):
        """Create client instance."""
        return WordPressClient(
            site_url="https://example.com",
            username="testuser",
            password="testpass"
        )

    def test_initialization(self, client):
        """Test client initializes correctly."""
        assert client is not None
        assert client.site_url == "https://example.com"
        assert hasattr(client, 'auth_header')

    @pytest.mark.asyncio
    async def test_get_posts_mock(self, client, mock_wordpress_post):
        """Test get_posts with mocked response."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = [mock_wordpress_post]

            result = await client.get_posts(per_page=10)

            assert result['status'] == 'success'
            assert 'posts' in result
            assert len(result['posts']) == 1
            assert result['posts'][0]['title'] == 'Test Post'

    @pytest.mark.asyncio
    async def test_get_post_mock(self, client, mock_wordpress_post):
        """Test get_post with mocked response."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_wordpress_post

            result = await client.get_post(post_id=123)

            assert result['status'] == 'success'
            assert result['post']['id'] == 123
            assert result['post']['title'] == 'Test Post'

    @pytest.mark.asyncio
    async def test_update_post_mock(self, client, mock_wordpress_post):
        """Test update_post with mocked response."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_wordpress_post

            result = await client.update_post(
                post_id=123,
                title="Updated Title",
                content="Updated content"
            )

            assert result['status'] == 'success'
            assert result['post']['id'] == 123

    @pytest.mark.asyncio
    async def test_search_posts_mock(self, client, mock_wordpress_post):
        """Test search_posts with mocked response."""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = [mock_wordpress_post]

            result = await client.search_posts(query="test")

            assert result['status'] == 'success'
            assert 'posts' in result
            assert len(result['posts']) > 0

    @pytest.mark.asyncio
    @pytest.mark.live
    async def test_get_posts_live(self, client):
        """Test get_posts with live API (requires credentials)."""
        result = await client.get_posts(per_page=5)

        assert result['status'] == 'success'
        assert 'posts' in result
        assert isinstance(result['posts'], list)
