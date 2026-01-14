"""
Google Tasks API Client for mega-agent2.

Async wrapper around Google Tasks API.
Uses service account with domain-wide delegation.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleTasksClient:
    """Async client for Google Tasks API operations."""

    SCOPES = ['https://www.googleapis.com/auth/tasks']

    def __init__(self, credential_file: str = 'google-credentials-aquarius.json', user_email: Optional[str] = None):
        """
        Initialize Tasks client.

        Args:
            credential_file: Path to service account credentials
            user_email: Email to impersonate (requires domain-wide delegation)
        """
        credentials = service_account.Credentials.from_service_account_file(
            credential_file,
            scopes=self.SCOPES
        )

        if user_email:
            credentials = credentials.with_subject(user_email)

        self.service = build('tasks', 'v1', credentials=credentials)
        self.user_email = user_email
        self._default_task_list_id = None  # Cache for default list ID

    async def get_default_task_list_id(self) -> Optional[str]:
        """
        Get the default task list ID (Inbox or My Tasks).
        Caches the result for performance.

        Returns:
            Task list ID string or None if not found
        """
        if self._default_task_list_id:
            return self._default_task_list_id

        task_lists = await self.list_task_lists()

        # Look for "Inbox" first, then "My Tasks" (default Google Tasks list)
        for task_list in task_lists:
            title = task_list.get('title', '').lower()
            if title == 'inbox' or title == 'my tasks':
                self._default_task_list_id = task_list.get('id')
                return self._default_task_list_id

        # If no Inbox/My Tasks found, use the first list
        if task_lists:
            self._default_task_list_id = task_lists[0].get('id')
            return self._default_task_list_id

        return None

    # ============================================================================
    # Task Lists
    # ============================================================================

    async def list_task_lists(self) -> List[Dict[str, Any]]:
        """List all task lists.

        Returns:
            List of task list objects
        """
        def _list():
            try:
                result = self.service.tasklists().list().execute()
                return result.get('items', [])
            except HttpError as e:
                raise Exception(f"Error listing task lists: {e}")

        return await asyncio.to_thread(_list)

    async def get_task_list(self, task_list_id: str) -> Dict[str, Any]:
        """Get a specific task list by ID.

        Args:
            task_list_id: Task list ID

        Returns:
            Task list object
        """
        def _get():
            try:
                return self.service.tasklists().get(tasklist=task_list_id).execute()
            except HttpError as e:
                raise Exception(f"Error getting task list: {e}")

        return await asyncio.to_thread(_get)

    async def create_task_list(self, title: str) -> Dict[str, Any]:
        """Create a new task list.

        Args:
            title: Title of the task list

        Returns:
            Created task list object
        """
        def _create():
            try:
                return self.service.tasklists().insert(body={'title': title}).execute()
            except HttpError as e:
                raise Exception(f"Error creating task list: {e}")

        return await asyncio.to_thread(_create)

    async def update_task_list(self, task_list_id: str, title: str) -> Dict[str, Any]:
        """Update a task list.

        Args:
            task_list_id: Task list ID
            title: New title for the task list

        Returns:
            Updated task list object
        """
        def _update():
            try:
                return self.service.tasklists().update(
                    tasklist=task_list_id,
                    body={'id': task_list_id, 'title': title}
                ).execute()
            except HttpError as e:
                raise Exception(f"Error updating task list: {e}")

        return await asyncio.to_thread(_update)

    async def delete_task_list(self, task_list_id: str) -> bool:
        """Delete a task list.

        Args:
            task_list_id: Task list ID

        Returns:
            True if successful
        """
        def _delete():
            try:
                self.service.tasklists().delete(tasklist=task_list_id).execute()
                return True
            except HttpError as e:
                raise Exception(f"Error deleting task list: {e}")

        return await asyncio.to_thread(_delete)

    # ============================================================================
    # Tasks
    # ============================================================================

    async def list_tasks(
        self,
        task_list_id: Optional[str] = None,
        show_completed: bool = False,
        show_deleted: bool = False,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List tasks in a task list.

        Args:
            task_list_id: Task list ID (default: None uses Inbox/My Tasks)
            show_completed: Whether to show completed tasks
            show_deleted: Whether to show deleted tasks
            max_results: Maximum number of results to return

        Returns:
            List of task objects
        """
        if task_list_id is None:
            task_list_id = await self.get_default_task_list_id()
            if not task_list_id:
                raise Exception("No default task list found")

        def _list():
            try:
                result = self.service.tasks().list(
                    tasklist=task_list_id,
                    showCompleted=show_completed,
                    showDeleted=show_deleted,
                    maxResults=max_results
                ).execute()
                return result.get('items', [])
            except HttpError as e:
                raise Exception(f"Error listing tasks: {e}")

        return await asyncio.to_thread(_list)

    async def get_task(self, task_list_id: str, task_id: str) -> Dict[str, Any]:
        """Get a specific task by ID.

        Args:
            task_list_id: Task list ID
            task_id: Task ID

        Returns:
            Task object
        """
        def _get():
            try:
                return self.service.tasks().get(
                    tasklist=task_list_id,
                    task=task_id
                ).execute()
            except HttpError as e:
                raise Exception(f"Error getting task: {e}")

        return await asyncio.to_thread(_get)

    async def create_task(
        self,
        title: str,
        task_list_id: Optional[str] = None,
        notes: Optional[str] = None,
        due: Optional[str] = None,
        status: str = 'needsAction',
        parent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new task.

        Args:
            title: Title of the task (required)
            task_list_id: Task list ID (default: None uses Inbox/My Tasks)
            notes: Optional notes/description for the task
            due: Optional due date (RFC 3339 timestamp string, e.g., '2025-12-31T23:59:59Z')
            status: Task status ('needsAction' or 'completed')
            parent: Optional parent task ID for subtasks

        Returns:
            Created task object
        """
        if task_list_id is None:
            task_list_id = await self.get_default_task_list_id()
            if not task_list_id:
                raise Exception("No default task list found")

        def _create():
            try:
                task_body = {
                    'title': title,
                    'status': status
                }

                if notes:
                    task_body['notes'] = notes
                if due:
                    task_body['due'] = due
                if parent:
                    task_body['parent'] = parent

                return self.service.tasks().insert(
                    tasklist=task_list_id,
                    body=task_body
                ).execute()
            except HttpError as e:
                raise Exception(f"Error creating task: {e}")

        return await asyncio.to_thread(_create)

    async def update_task(
        self,
        task_list_id: str,
        task_id: str,
        title: Optional[str] = None,
        notes: Optional[str] = None,
        due: Optional[str] = None,
        status: Optional[str] = None,
        completed: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing task.

        Args:
            task_list_id: Task list ID
            task_id: Task ID to update
            title: Optional new title
            notes: Optional new notes
            due: Optional new due date (RFC 3339 timestamp string)
            status: Optional new status ('needsAction' or 'completed')
            completed: Optional completion timestamp (RFC 3339 timestamp string)

        Returns:
            Updated task object
        """
        def _update():
            try:
                # Get current task to preserve existing fields
                current_task = self.service.tasks().get(
                    tasklist=task_list_id,
                    task=task_id
                ).execute()

                # Update only provided fields
                if title is not None:
                    current_task['title'] = title
                if notes is not None:
                    current_task['notes'] = notes
                if due is not None:
                    current_task['due'] = due
                if status is not None:
                    current_task['status'] = status
                if completed is not None:
                    current_task['completed'] = completed

                return self.service.tasks().update(
                    tasklist=task_list_id,
                    task=task_id,
                    body=current_task
                ).execute()
            except HttpError as e:
                raise Exception(f"Error updating task: {e}")

        return await asyncio.to_thread(_update)

    async def delete_task(self, task_list_id: str, task_id: str) -> bool:
        """Delete a task.

        Args:
            task_list_id: Task list ID
            task_id: Task ID to delete

        Returns:
            True if successful
        """
        def _delete():
            try:
                self.service.tasks().delete(
                    tasklist=task_list_id,
                    task=task_id
                ).execute()
                return True
            except HttpError as e:
                raise Exception(f"Error deleting task: {e}")

        return await asyncio.to_thread(_delete)

    async def complete_task(self, task_list_id: str, task_id: str) -> Dict[str, Any]:
        """Mark a task as completed.

        Args:
            task_list_id: Task list ID
            task_id: Task ID to complete

        Returns:
            Updated task object
        """
        return await self.update_task(
            task_list_id=task_list_id,
            task_id=task_id,
            status='completed',
            completed=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z')
        )

    async def uncomplete_task(self, task_list_id: str, task_id: str) -> Dict[str, Any]:
        """Mark a task as not completed.

        Args:
            task_list_id: Task list ID
            task_id: Task ID to uncomplete

        Returns:
            Updated task object
        """
        # Get current task to remove 'completed' field
        current_task = await self.get_task(task_list_id, task_id)
        if 'completed' in current_task:
            del current_task['completed']

        current_task['status'] = 'needsAction'

        def _update():
            try:
                return self.service.tasks().update(
                    tasklist=task_list_id,
                    task=task_id,
                    body=current_task
                ).execute()
            except HttpError as e:
                raise Exception(f"Error uncompleting task: {e}")

        return await asyncio.to_thread(_update)

    async def move_task(
        self,
        task_list_id: str,
        task_id: str,
        parent: Optional[str] = None,
        previous: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Move a task to a different position or make it a subtask.

        Args:
            task_list_id: Task list ID
            task_id: Task ID to move
            parent: Optional parent task ID to make this a subtask
            previous: Optional previous sibling task ID to position after

        Returns:
            Updated task object
        """
        def _move():
            try:
                return self.service.tasks().move(
                    tasklist=task_list_id,
                    task=task_id,
                    parent=parent,
                    previous=previous
                ).execute()
            except HttpError as e:
                raise Exception(f"Error moving task: {e}")

        return await asyncio.to_thread(_move)

    async def clear_completed_tasks(self, task_list_id: str) -> bool:
        """Clear all completed tasks from a task list.

        Args:
            task_list_id: Task list ID

        Returns:
            True if successful
        """
        def _clear():
            try:
                self.service.tasks().clear(tasklist=task_list_id).execute()
                return True
            except HttpError as e:
                raise Exception(f"Error clearing completed tasks: {e}")

        return await asyncio.to_thread(_clear)
