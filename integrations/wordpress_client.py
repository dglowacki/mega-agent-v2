"""
WordPress REST API Client for mega-agent2.

Async client for interacting with WordPress sites via REST API.
Supports posts, pages, categories, tags, media, comments, and search.
"""

import base64
import mimetypes
from typing import Dict, List, Optional, Any
from pathlib import Path
import aiohttp
import aiofiles


class WordPressClient:
    """Async client for WordPress REST API operations."""

    def __init__(self, site_url: str, username: str, app_password: str):
        """
        Initialize WordPress API client.

        Args:
            site_url: WordPress site URL (e.g., https://listorati.com)
            username: WordPress username
            app_password: Application password
        """
        # Remove trailing slash and wp-admin if present
        self.site_url = site_url.rstrip('/').replace('/wp-admin', '')
        self.username = username
        self.app_password = app_password

        # Create base64 encoded credentials
        credentials = f"{username}:{app_password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json',
            'Accept': 'application/json, */*',
            'User-Agent': 'Mozilla/5.0 (compatible; Mega-Agent2/1.0)',
            'X-Requested-With': 'XMLHttpRequest'
        }

        self.api_base = f"{self.site_url}/wp-json/wp/v2"

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        timeout: int = 30
    ) -> Any:
        """
        Make API request.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (relative to /wp-json/wp/v2)
            params: Query parameters
            json_data: JSON request body
            timeout: Request timeout in seconds

        Returns:
            Response data as dict or list

        Raises:
            aiohttp.ClientError: On request failure
        """
        url = f"{self.api_base}/{endpoint.lstrip('/')}"

        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                url,
                headers=self.headers,
                params=params,
                json=json_data,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                response.raise_for_status()

                # Handle empty responses (204 No Content)
                if response.status == 204:
                    return {}

                return await response.json()

    # ============================================================================
    # Posts
    # ============================================================================

    async def get_posts(
        self,
        per_page: int = 10,
        page: int = 1,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Get posts.

        Args:
            per_page: Posts per page
            page: Page number
            **kwargs: Additional query parameters

        Returns:
            List of post objects
        """
        params = {'per_page': per_page, 'page': page, **kwargs}
        return await self._request('GET', 'posts', params=params)

    async def get_post(
        self,
        post_id: int,
        context: str = 'edit'
    ) -> Dict[str, Any]:
        """Get single post by ID.

        Args:
            post_id: Post ID
            context: Context (view, embed, edit)

        Returns:
            Post object
        """
        return await self._request('GET', f'posts/{post_id}', params={'context': context})

    async def create_post(
        self,
        title: str,
        content: str,
        status: str = 'draft',
        **kwargs
    ) -> Dict[str, Any]:
        """Create new post.

        Args:
            title: Post title
            content: Post content (HTML)
            status: Post status (draft, publish, pending, etc.)
            **kwargs: Additional fields

        Returns:
            Created post object
        """
        data = {
            'title': title,
            'content': content,
            'status': status,
            **kwargs
        }
        return await self._request('POST', 'posts', json_data=data)

    async def update_post(self, post_id: int, **kwargs) -> Dict[str, Any]:
        """Update existing post.

        Args:
            post_id: Post ID
            **kwargs: Fields to update

        Returns:
            Updated post object
        """
        return await self._request('POST', f'posts/{post_id}', json_data=kwargs)

    async def delete_post(
        self,
        post_id: int,
        force: bool = True
    ) -> Dict[str, Any]:
        """Delete post.

        Args:
            post_id: Post ID
            force: Whether to permanently delete (True) or move to trash (False)

        Returns:
            Deletion result
        """
        return await self._request('DELETE', f'posts/{post_id}', params={'force': force})

    # ============================================================================
    # Revisions
    # ============================================================================

    async def get_revisions(self, post_id: int) -> List[Dict[str, Any]]:
        """Get revisions for a post.

        Args:
            post_id: Post ID

        Returns:
            List of revision objects
        """
        return await self._request('GET', f'posts/{post_id}/revisions')

    async def get_revision(
        self,
        post_id: int,
        revision_id: int
    ) -> Dict[str, Any]:
        """Get specific revision.

        Args:
            post_id: Post ID
            revision_id: Revision ID

        Returns:
            Revision object
        """
        return await self._request('GET', f'posts/{post_id}/revisions/{revision_id}')

    async def restore_revision(
        self,
        post_id: int,
        revision_id: int
    ) -> Dict[str, Any]:
        """
        Restore a post to a specific revision.

        Args:
            post_id: Post ID
            revision_id: Revision ID to restore to

        Returns:
            Updated post data
        """
        # Get the revision content
        revision = await self.get_revision(post_id, revision_id)

        # Extract content - handle both 'raw' and 'rendered' formats
        title_data = revision.get('title', {})
        if isinstance(title_data, dict):
            title = title_data.get('raw', '') or title_data.get('rendered', '')
        else:
            title = title_data or ''

        content_data = revision.get('content', {})
        if isinstance(content_data, dict):
            content = content_data.get('raw', '') or content_data.get('rendered', '')
        else:
            content = content_data or ''

        excerpt_data = revision.get('excerpt', {})
        if isinstance(excerpt_data, dict):
            excerpt = excerpt_data.get('raw', '') or excerpt_data.get('rendered', '')
        else:
            excerpt = excerpt_data or ''

        # Restore by updating post with revision data
        restore_data = {}

        if title and title.strip():
            restore_data['title'] = title.strip()
        if content and content.strip():
            restore_data['content'] = content.strip()
        if excerpt and excerpt.strip():
            restore_data['excerpt'] = excerpt.strip()

        if not restore_data:
            raise ValueError(f"Revision {revision_id} has no restorable content")

        return await self.update_post(post_id, **restore_data)

    # ============================================================================
    # Pages
    # ============================================================================

    async def get_pages(
        self,
        per_page: int = 10,
        page: int = 1,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Get pages."""
        params = {'per_page': per_page, 'page': page, **kwargs}
        return await self._request('GET', 'pages', params=params)

    async def get_page(self, page_id: int) -> Dict[str, Any]:
        """Get single page by ID."""
        return await self._request('GET', f'pages/{page_id}')

    async def create_page(
        self,
        title: str,
        content: str,
        status: str = 'draft',
        **kwargs
    ) -> Dict[str, Any]:
        """Create new page."""
        data = {
            'title': title,
            'content': content,
            'status': status,
            **kwargs
        }
        return await self._request('POST', 'pages', json_data=data)

    async def update_page(self, page_id: int, **kwargs) -> Dict[str, Any]:
        """Update existing page."""
        return await self._request('POST', f'pages/{page_id}', json_data=kwargs)

    async def delete_page(
        self,
        page_id: int,
        force: bool = True
    ) -> Dict[str, Any]:
        """Delete page."""
        return await self._request('DELETE', f'pages/{page_id}', params={'force': force})

    # ============================================================================
    # Categories
    # ============================================================================

    async def get_categories(
        self,
        per_page: int = 100,
        page: int = 1,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Get categories."""
        params = {'per_page': per_page, 'page': page, **kwargs}
        return await self._request('GET', 'categories', params=params)

    async def get_category(self, category_id: int) -> Dict[str, Any]:
        """Get single category by ID."""
        return await self._request('GET', f'categories/{category_id}')

    async def create_category(self, name: str, **kwargs) -> Dict[str, Any]:
        """Create new category."""
        data = {'name': name, **kwargs}
        return await self._request('POST', 'categories', json_data=data)

    async def update_category(self, category_id: int, **kwargs) -> Dict[str, Any]:
        """Update existing category."""
        return await self._request('POST', f'categories/{category_id}', json_data=kwargs)

    async def delete_category(
        self,
        category_id: int,
        force: bool = True
    ) -> Dict[str, Any]:
        """Delete category."""
        return await self._request('DELETE', f'categories/{category_id}', params={'force': force})

    # ============================================================================
    # Tags
    # ============================================================================

    async def get_tags(
        self,
        per_page: int = 100,
        page: int = 1,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Get tags."""
        params = {'per_page': per_page, 'page': page, **kwargs}
        return await self._request('GET', 'tags', params=params)

    async def get_tag(self, tag_id: int) -> Dict[str, Any]:
        """Get single tag by ID."""
        return await self._request('GET', f'tags/{tag_id}')

    async def create_tag(self, name: str, **kwargs) -> Dict[str, Any]:
        """Create new tag."""
        data = {'name': name, **kwargs}
        return await self._request('POST', 'tags', json_data=data)

    async def update_tag(self, tag_id: int, **kwargs) -> Dict[str, Any]:
        """Update existing tag."""
        return await self._request('POST', f'tags/{tag_id}', json_data=kwargs)

    async def delete_tag(
        self,
        tag_id: int,
        force: bool = True
    ) -> Dict[str, Any]:
        """Delete tag."""
        return await self._request('DELETE', f'tags/{tag_id}', params={'force': force})

    # ============================================================================
    # Media
    # ============================================================================

    async def get_media(
        self,
        per_page: int = 10,
        page: int = 1,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Get media items."""
        params = {'per_page': per_page, 'page': page, **kwargs}
        return await self._request('GET', 'media', params=params)

    async def get_media_item(self, media_id: int) -> Dict[str, Any]:
        """Get single media item by ID."""
        return await self._request('GET', f'media/{media_id}')

    async def upload_media(
        self,
        file_path: str,
        title: Optional[str] = None,
        alt_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload media file.

        Args:
            file_path: Path to file to upload
            title: Optional title for media
            alt_text: Optional alt text

        Returns:
            Created media object
        """
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path_obj))
        if not mime_type:
            mime_type = 'application/octet-stream'

        # Read file
        async with aiofiles.open(file_path_obj, 'rb') as f:
            file_content = await f.read()

        # Update headers for multipart/form-data
        headers = {k: v for k, v in self.headers.items() if k != 'Content-Type'}

        data = aiohttp.FormData()
        data.add_field('file', file_content, filename=file_path_obj.name, content_type=mime_type)

        if title:
            data.add_field('title', title)
        if alt_text:
            data.add_field('alt_text', alt_text)

        url = f"{self.api_base}/media"

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=data) as response:
                response.raise_for_status()
                return await response.json()

    async def delete_media(
        self,
        media_id: int,
        force: bool = True
    ) -> Dict[str, Any]:
        """Delete media item."""
        return await self._request('DELETE', f'media/{media_id}', params={'force': force})

    # ============================================================================
    # Comments
    # ============================================================================

    async def get_comments(
        self,
        per_page: int = 10,
        page: int = 1,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Get comments."""
        params = {'per_page': per_page, 'page': page, **kwargs}
        return await self._request('GET', 'comments', params=params)

    async def get_comment(self, comment_id: int) -> Dict[str, Any]:
        """Get single comment by ID."""
        return await self._request('GET', f'comments/{comment_id}')

    async def create_comment(
        self,
        post_id: int,
        content: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Create new comment."""
        data = {
            'post': post_id,
            'content': content,
            **kwargs
        }
        return await self._request('POST', 'comments', json_data=data)

    async def update_comment(self, comment_id: int, **kwargs) -> Dict[str, Any]:
        """Update existing comment."""
        return await self._request('POST', f'comments/{comment_id}', json_data=kwargs)

    async def delete_comment(
        self,
        comment_id: int,
        force: bool = True
    ) -> Dict[str, Any]:
        """Delete comment."""
        return await self._request('DELETE', f'comments/{comment_id}', params={'force': force})

    # ============================================================================
    # Search
    # ============================================================================

    async def search(
        self,
        search_term: str,
        type: str = 'post',
        per_page: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search WordPress content.

        Args:
            search_term: Search query
            type: Content type (post, page, etc.)
            per_page: Results per page

        Returns:
            List of matching content
        """
        params = {
            'search': search_term,
            'type': type,
            'per_page': per_page
        }
        return await self._request('GET', 'search', params=params)
