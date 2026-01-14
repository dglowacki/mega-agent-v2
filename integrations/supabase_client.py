"""
Supabase Admin API Client for mega-agent2.

Async client for managing Supabase projects using the Admin API.
Supports project management and authentication configuration.
"""

import os
from typing import Dict, List, Optional, Any
import aiohttp


class SupabaseClient:
    """Async client for Supabase Admin API operations."""

    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize Supabase client.

        Args:
            access_token: Supabase access token (defaults to SUPABASE_ACCESS_TOKEN env var)
        """
        self.access_token = access_token or os.getenv('SUPABASE_ACCESS_TOKEN')
        if not self.access_token:
            raise ValueError("Supabase access token required. Set SUPABASE_ACCESS_TOKEN environment variable.")

        self.base_url = "https://api.supabase.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
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
            method: HTTP method (GET, POST, PATCH, DELETE)
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
    # Projects
    # ============================================================================

    async def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects.

        Returns:
            List of project objects
        """
        return await self._request('GET', 'projects')

    async def get_project(self, project_ref: str) -> Dict[str, Any]:
        """Get project details.

        Args:
            project_ref: Project reference ID

        Returns:
            Project object
        """
        return await self._request('GET', f'projects/{project_ref}')

    async def create_project(
        self,
        organization_id: str,
        name: str,
        region: str = 'us-east-1',
        plan: str = 'free',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new project.

        Args:
            organization_id: Organization ID
            name: Project name
            region: AWS region (default: us-east-1)
            plan: Subscription plan (free, pro, etc.)
            **kwargs: Additional project settings

        Returns:
            Created project object
        """
        data = {
            'organization_id': organization_id,
            'name': name,
            'region': region,
            'plan': plan,
            **kwargs
        }
        return await self._request('POST', 'projects', json_data=data)

    async def delete_project(self, project_ref: str) -> Dict[str, Any]:
        """Delete a project.

        Args:
            project_ref: Project reference ID

        Returns:
            Deletion result
        """
        return await self._request('DELETE', f'projects/{project_ref}')

    # ============================================================================
    # Authentication Configuration
    # ============================================================================

    async def get_auth_config(self, project_ref: str) -> Dict[str, Any]:
        """Get authentication configuration.

        Args:
            project_ref: Project reference ID

        Returns:
            Auth configuration object
        """
        return await self._request('GET', f'projects/{project_ref}/config/auth')

    async def update_auth_config(
        self,
        project_ref: str,
        rate_limit_otp: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Update authentication configuration.

        Args:
            project_ref: Project reference ID
            rate_limit_otp: OTP rate limit (requests per hour)
            **kwargs: Additional auth config parameters

        Returns:
            Updated configuration object
        """
        payload = {}

        if rate_limit_otp is not None:
            payload['rate_limit_otp'] = rate_limit_otp

        # Add any additional config parameters
        payload.update(kwargs)

        if not payload:
            raise ValueError("At least one configuration parameter must be provided")

        return await self._request('PATCH', f'projects/{project_ref}/config/auth', json_data=payload)

    async def set_otp_limit(self, project_ref: str, limit: int) -> Dict[str, Any]:
        """
        Set OTP rate limit for a project (convenience method).

        Args:
            project_ref: Project reference ID
            limit: OTP rate limit (requests per hour)

        Returns:
            Updated configuration object
        """
        return await self.update_auth_config(project_ref, rate_limit_otp=limit)

    # ============================================================================
    # Database Configuration
    # ============================================================================

    async def get_database_config(self, project_ref: str) -> Dict[str, Any]:
        """Get database configuration.

        Args:
            project_ref: Project reference ID

        Returns:
            Database configuration object
        """
        return await self._request('GET', f'projects/{project_ref}/config/database')

    async def update_database_config(
        self,
        project_ref: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Update database configuration.

        Args:
            project_ref: Project reference ID
            **kwargs: Database config parameters

        Returns:
            Updated configuration object
        """
        if not kwargs:
            raise ValueError("At least one configuration parameter must be provided")

        return await self._request('PATCH', f'projects/{project_ref}/config/database', json_data=kwargs)

    # ============================================================================
    # Organizations
    # ============================================================================

    async def list_organizations(self) -> List[Dict[str, Any]]:
        """List all organizations.

        Returns:
            List of organization objects
        """
        return await self._request('GET', 'organizations')

    async def get_organization(self, org_id: str) -> Dict[str, Any]:
        """Get organization details.

        Args:
            org_id: Organization ID

        Returns:
            Organization object
        """
        return await self._request('GET', f'organizations/{org_id}')

    # ============================================================================
    # API Keys
    # ============================================================================

    async def get_api_keys(self, project_ref: str) -> Dict[str, Any]:
        """Get API keys for a project.

        Args:
            project_ref: Project reference ID

        Returns:
            API keys object (anon key, service_role key, etc.)
        """
        return await self._request('GET', f'projects/{project_ref}/api-keys')

    # ============================================================================
    # Functions
    # ============================================================================

    async def list_functions(self, project_ref: str) -> List[Dict[str, Any]]:
        """List Edge Functions for a project.

        Args:
            project_ref: Project reference ID

        Returns:
            List of function objects
        """
        result = await self._request('GET', f'projects/{project_ref}/functions')
        return result if isinstance(result, list) else result.get('functions', [])

    async def get_function(self, project_ref: str, function_slug: str) -> Dict[str, Any]:
        """Get Edge Function details.

        Args:
            project_ref: Project reference ID
            function_slug: Function slug/name

        Returns:
            Function object
        """
        return await self._request('GET', f'projects/{project_ref}/functions/{function_slug}')

    async def delete_function(self, project_ref: str, function_slug: str) -> Dict[str, Any]:
        """Delete an Edge Function.

        Args:
            project_ref: Project reference ID
            function_slug: Function slug/name

        Returns:
            Deletion result
        """
        return await self._request('DELETE', f'projects/{project_ref}/functions/{function_slug}')
