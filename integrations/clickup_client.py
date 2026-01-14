"""
ClickUp API Client for mega-agent2.

Async client for interacting with ClickUp's REST API.
Supports tasks, lists, spaces, and workspaces management.
"""

import os
from typing import Dict, List, Optional, Any
import aiohttp


class ClickUpClient:
    """Async client for ClickUp API operations."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize ClickUp client.

        Args:
            api_key: ClickUp API key (defaults to CLICKUP_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("CLICKUP_API_KEY")
        if not self.api_key:
            raise ValueError("ClickUp API key not found. Set CLICKUP_API_KEY environment variable.")

        self.base_url = "https://api.clickup.com/api/v2"
        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }

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
            endpoint: API endpoint (relative to base_url)
            params: Query parameters
            json_data: JSON request body
            timeout: Request timeout in seconds

        Returns:
            Response data as dict or list

        Raises:
            aiohttp.ClientError: On request failure
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

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
                return await response.json()

    # ============================================================================
    # Workspaces (Teams)
    # ============================================================================

    async def get_workspaces(self) -> List[Dict[str, Any]]:
        """Get all authorized workspaces/teams.

        Returns:
            List of workspace objects
        """
        result = await self._request('GET', 'team')
        return result.get('teams', [])

    # ============================================================================
    # Spaces
    # ============================================================================

    async def get_spaces(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Get spaces from a workspace/team.

        Args:
            workspace_id: Workspace/team ID

        Returns:
            List of space objects
        """
        result = await self._request('GET', f'team/{workspace_id}/space')
        return result.get('spaces', [])

    async def get_space(self, space_id: str) -> Dict[str, Any]:
        """Get single space by ID.

        Args:
            space_id: Space ID

        Returns:
            Space object
        """
        return await self._request('GET', f'space/{space_id}')

    async def create_space(
        self,
        workspace_id: str,
        name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new space.

        Args:
            workspace_id: Workspace/team ID
            name: Space name
            **kwargs: Additional fields

        Returns:
            Created space object
        """
        data = {'name': name, **kwargs}
        return await self._request('POST', f'team/{workspace_id}/space', json_data=data)

    async def update_space(self, space_id: str, **kwargs) -> Dict[str, Any]:
        """Update a space.

        Args:
            space_id: Space ID
            **kwargs: Fields to update

        Returns:
            Updated space object
        """
        return await self._request('PUT', f'space/{space_id}', json_data=kwargs)

    async def delete_space(self, space_id: str) -> Dict[str, Any]:
        """Delete a space.

        Args:
            space_id: Space ID

        Returns:
            Deletion result
        """
        return await self._request('DELETE', f'space/{space_id}')

    # ============================================================================
    # Folders
    # ============================================================================

    async def get_folders(self, space_id: str) -> List[Dict[str, Any]]:
        """Get folders from a space.

        Args:
            space_id: Space ID

        Returns:
            List of folder objects
        """
        result = await self._request('GET', f'space/{space_id}/folder')
        return result.get('folders', [])

    async def create_folder(
        self,
        space_id: str,
        name: str
    ) -> Dict[str, Any]:
        """Create a new folder.

        Args:
            space_id: Space ID
            name: Folder name

        Returns:
            Created folder object
        """
        data = {'name': name}
        return await self._request('POST', f'space/{space_id}/folder', json_data=data)

    # ============================================================================
    # Lists
    # ============================================================================

    async def get_lists(
        self,
        space_id: Optional[str] = None,
        folder_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get lists from a space or folder.

        Args:
            space_id: Space ID (required if folder_id not provided)
            folder_id: Folder ID (required if space_id not provided)

        Returns:
            List of list objects
        """
        if folder_id:
            result = await self._request('GET', f'folder/{folder_id}/list')
        elif space_id:
            result = await self._request('GET', f'space/{space_id}/list')
        else:
            raise ValueError("Either space_id or folder_id is required")

        return result.get('lists', [])

    async def get_list(self, list_id: str) -> Dict[str, Any]:
        """Get single list by ID.

        Args:
            list_id: List ID

        Returns:
            List object
        """
        return await self._request('GET', f'list/{list_id}')

    async def create_list(
        self,
        folder_id: str,
        name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new list.

        Args:
            folder_id: Folder ID
            name: List name
            **kwargs: Additional fields

        Returns:
            Created list object
        """
        data = {'name': name, **kwargs}
        return await self._request('POST', f'folder/{folder_id}/list', json_data=data)

    async def update_list(self, list_id: str, **kwargs) -> Dict[str, Any]:
        """Update a list.

        Args:
            list_id: List ID
            **kwargs: Fields to update

        Returns:
            Updated list object
        """
        return await self._request('PUT', f'list/{list_id}', json_data=kwargs)

    async def delete_list(self, list_id: str) -> Dict[str, Any]:
        """Delete a list.

        Args:
            list_id: List ID

        Returns:
            Deletion result
        """
        return await self._request('DELETE', f'list/{list_id}')

    # ============================================================================
    # Tasks
    # ============================================================================

    async def get_tasks(
        self,
        list_id: str,
        archived: bool = False,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Get tasks from a list.

        Args:
            list_id: List ID
            archived: Include archived tasks
            **kwargs: Additional query parameters

        Returns:
            List of task objects
        """
        params = {'archived': str(archived).lower(), **kwargs}
        result = await self._request('GET', f'list/{list_id}/task', params=params)
        return result.get('tasks', [])

    async def get_task(self, task_id: str) -> Dict[str, Any]:
        """Get single task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task object
        """
        return await self._request('GET', f'task/{task_id}')

    async def create_task(
        self,
        list_id: str,
        name: str,
        description: Optional[str] = None,
        priority: Optional[int] = None,
        assignees: Optional[List[int]] = None,
        due_date: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new task.

        Args:
            list_id: List ID
            name: Task name (required)
            description: Task description
            priority: Priority (1=urgent, 2=high, 3=normal, 4=low)
            assignees: List of assignee user IDs
            due_date: Due date (Unix timestamp in milliseconds)
            **kwargs: Additional fields

        Returns:
            Created task object
        """
        data = {'name': name}

        if description:
            data['description'] = description
        if priority is not None:
            data['priority'] = priority
        if assignees:
            data['assignees'] = assignees
        if due_date:
            data['due_date'] = due_date

        data.update(kwargs)

        return await self._request('POST', f'list/{list_id}/task', json_data=data)

    async def update_task(self, task_id: str, **kwargs) -> Dict[str, Any]:
        """Update an existing task.

        Args:
            task_id: Task ID
            **kwargs: Fields to update

        Returns:
            Updated task object
        """
        return await self._request('PUT', f'task/{task_id}', json_data=kwargs)

    async def delete_task(self, task_id: str) -> Dict[str, Any]:
        """Delete a task.

        Args:
            task_id: Task ID

        Returns:
            Deletion result
        """
        return await self._request('DELETE', f'task/{task_id}')

    async def get_task_comments(self, task_id: str) -> List[Dict[str, Any]]:
        """Get comments for a task.

        Args:
            task_id: Task ID

        Returns:
            List of comment objects
        """
        result = await self._request('GET', f'task/{task_id}/comment')
        return result.get('comments', [])

    async def create_task_comment(
        self,
        task_id: str,
        comment_text: str
    ) -> Dict[str, Any]:
        """Create a comment on a task.

        Args:
            task_id: Task ID
            comment_text: Comment text

        Returns:
            Created comment object
        """
        data = {'comment_text': comment_text}
        return await self._request('POST', f'task/{task_id}/comment', json_data=data)

    # ============================================================================
    # Members
    # ============================================================================

    async def get_workspace_members(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Get members of a workspace/team.

        Args:
            workspace_id: Workspace/team ID

        Returns:
            List of member objects
        """
        result = await self._request('GET', f'team/{workspace_id}')
        return result.get('team', {}).get('members', [])

    # ============================================================================
    # Tags
    # ============================================================================

    async def get_space_tags(self, space_id: str) -> List[Dict[str, Any]]:
        """Get tags for a space.

        Args:
            space_id: Space ID

        Returns:
            List of tag objects
        """
        result = await self._request('GET', f'space/{space_id}/tag')
        return result.get('tags', [])

    async def create_tag(
        self,
        space_id: str,
        name: str,
        tag_fg: Optional[str] = None,
        tag_bg: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a tag.

        Args:
            space_id: Space ID
            name: Tag name
            tag_fg: Foreground color (hex)
            tag_bg: Background color (hex)

        Returns:
            Created tag object
        """
        data = {'tag': {'name': name}}
        if tag_fg:
            data['tag']['tag_fg'] = tag_fg
        if tag_bg:
            data['tag']['tag_bg'] = tag_bg

        return await self._request('POST', f'space/{space_id}/tag', json_data=data)
