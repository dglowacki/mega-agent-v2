"""
Linear API Client for mega-agent2.

Async client for interacting with Linear's GraphQL API.
Supports issues, projects, teams, cycles, and more.
"""

import os
from typing import Dict, List, Optional, Any
import aiohttp


class LinearClient:
    """Async client for Linear GraphQL API operations."""

    BASE_URL = "https://api.linear.app/graphql"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Linear client.

        Args:
            api_key: Linear API key (defaults to LINEAR_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("LINEAR_API_KEY")
        if not self.api_key:
            raise ValueError("Linear API key not found. Set LINEAR_API_KEY environment variable.")

        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }

    async def _execute_query(
        self,
        query: str,
        variables: Optional[Dict] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute a GraphQL query against Linear API.

        Args:
            query: GraphQL query string
            variables: Query variables
            timeout: Request timeout in seconds

        Returns:
            Response data dict

        Raises:
            Exception: On GraphQL or HTTP errors
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.BASE_URL,
                headers=self.headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                response.raise_for_status()
                result = await response.json()

                if "errors" in result:
                    error_messages = [e.get("message", str(e)) for e in result["errors"]]
                    raise Exception(f"Linear API error: {'; '.join(error_messages)}")

                return result.get("data", {})

    # ============================================================================
    # Organization & Teams
    # ============================================================================

    async def get_organization(self) -> Dict[str, Any]:
        """Get organization information.

        Returns:
            Organization object
        """
        query = """
        query {
            organization {
                id
                name
                urlKey
                createdAt
            }
        }
        """
        data = await self._execute_query(query)
        return data.get("organization", {})

    async def get_teams(self) -> List[Dict[str, Any]]:
        """Get all teams in the organization.

        Returns:
            List of team objects
        """
        query = """
        query {
            teams {
                nodes {
                    id
                    name
                    key
                    description
                    color
                    icon
                    private
                    issueCount
                }
            }
        }
        """
        data = await self._execute_query(query)
        return data.get("teams", {}).get("nodes", [])

    async def get_team(self, team_id: str) -> Dict[str, Any]:
        """Get a specific team by ID.

        Args:
            team_id: Team ID

        Returns:
            Team object with states and labels
        """
        query = """
        query($id: String!) {
            team(id: $id) {
                id
                name
                key
                description
                color
                icon
                private
                issueCount
                states {
                    nodes {
                        id
                        name
                        color
                        type
                    }
                }
                labels {
                    nodes {
                        id
                        name
                        color
                    }
                }
            }
        }
        """
        data = await self._execute_query(query, {"id": team_id})
        return data.get("team", {})

    async def update_team(self, team_id: str, **kwargs) -> Dict[str, Any]:
        """
        Update team settings.

        Args:
            team_id: Team identifier
            **kwargs: Fields supported by TeamUpdateInput

        Returns:
            Updated team object
        """
        mutation = """
        mutation($id: String!, $input: TeamUpdateInput!) {
            teamUpdate(id: $id, input: $input) {
                team {
                    id
                    name
                    cycleDuration
                    cycleCooldownTime
                    cyclesEnabled
                }
            }
        }
        """
        data = await self._execute_query(mutation, {"id": team_id, "input": kwargs})
        return data.get("teamUpdate", {}).get("team", {})

    # ============================================================================
    # Issues
    # ============================================================================

    async def get_issues(
        self,
        team_id: Optional[str] = None,
        state: Optional[str] = None,
        assignee_id: Optional[str] = None,
        limit: int = 50,
        include_archived: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get issues with optional filters.

        Args:
            team_id: Filter by team ID
            state: Filter by state name
            assignee_id: Filter by assignee user ID
            limit: Maximum number of issues to return
            include_archived: Include archived issues

        Returns:
            List of issue objects
        """
        # Build filter
        filters = []
        if team_id:
            filters.append(f'team: {{ id: {{ eq: "{team_id}" }} }}')
        if state:
            filters.append(f'state: {{ name: {{ eq: "{state}" }} }}')
        if assignee_id:
            filters.append(f'assignee: {{ id: {{ eq: "{assignee_id}" }} }}')
        if not include_archived:
            filters.append('archivedAt: { null: true }')

        filter_str = ", ".join(filters) if filters else ""
        filter_clause = f"filter: {{ {filter_str} }}" if filter_str else ""

        query = f"""
        query {{
            issues(first: {limit}, {filter_clause}) {{
                nodes {{
                    id
                    identifier
                    title
                    description
                    priority
                    priorityLabel
                    estimate
                    url
                    createdAt
                    updatedAt
                    dueDate
                    state {{
                        id
                        name
                        color
                        type
                    }}
                    team {{
                        id
                        name
                        key
                    }}
                    assignee {{
                        id
                        name
                        email
                    }}
                    creator {{
                        id
                        name
                    }}
                    labels {{
                        nodes {{
                            id
                            name
                            color
                        }}
                    }}
                    project {{
                        id
                        name
                    }}
                    cycle {{
                        id
                        name
                        number
                    }}
                }}
            }}
        }}
        """
        data = await self._execute_query(query)
        return data.get("issues", {}).get("nodes", [])

    async def get_issue(self, issue_id: str) -> Dict[str, Any]:
        """Get a specific issue by ID or identifier.

        Args:
            issue_id: Issue ID or identifier (e.g., 'ABC-123')

        Returns:
            Issue object with full details
        """
        query = """
        query($id: String!) {
            issue(id: $id) {
                id
                identifier
                title
                description
                priority
                priorityLabel
                estimate
                url
                createdAt
                updatedAt
                dueDate
                completedAt
                canceledAt
                state {
                    id
                    name
                    color
                    type
                }
                team {
                    id
                    name
                    key
                }
                assignee {
                    id
                    name
                    email
                }
                creator {
                    id
                    name
                }
                labels {
                    nodes {
                        id
                        name
                        color
                    }
                }
                project {
                    id
                    name
                }
                cycle {
                    id
                    name
                    number
                }
                comments {
                    nodes {
                        id
                        body
                        createdAt
                        user {
                            name
                        }
                    }
                }
                parent {
                    id
                    identifier
                    title
                }
                children {
                    nodes {
                        id
                        identifier
                        title
                        state {
                            name
                        }
                    }
                }
            }
        }
        """
        data = await self._execute_query(query, {"id": issue_id})
        return data.get("issue", {})

    async def create_issue(
        self,
        team_id: str,
        title: str,
        description: Optional[str] = None,
        priority: Optional[int] = None,
        assignee_id: Optional[str] = None,
        state_id: Optional[str] = None,
        label_ids: Optional[List[str]] = None,
        project_id: Optional[str] = None,
        cycle_id: Optional[str] = None,
        due_date: Optional[str] = None,
        estimate: Optional[int] = None,
        parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new issue.

        Args:
            team_id: Team ID (required)
            title: Issue title (required)
            description: Issue description (markdown supported)
            priority: Priority (0=none, 1=urgent, 2=high, 3=normal, 4=low)
            assignee_id: User ID to assign
            state_id: Workflow state ID
            label_ids: List of label IDs
            project_id: Project ID
            cycle_id: Cycle ID
            due_date: Due date (ISO format)
            estimate: Point estimate
            parent_id: Parent issue ID (for sub-issues)

        Returns:
            Created issue object
        """
        mutation = """
        mutation($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    url
                    state {
                        name
                    }
                    team {
                        key
                    }
                }
            }
        }
        """

        input_data = {
            "teamId": team_id,
            "title": title
        }

        if description:
            input_data["description"] = description
        if priority is not None:
            input_data["priority"] = priority
        if assignee_id:
            input_data["assigneeId"] = assignee_id
        if state_id:
            input_data["stateId"] = state_id
        if label_ids:
            input_data["labelIds"] = label_ids
        if project_id:
            input_data["projectId"] = project_id
        if cycle_id:
            input_data["cycleId"] = cycle_id
        if due_date:
            input_data["dueDate"] = due_date
        if estimate is not None:
            input_data["estimate"] = estimate
        if parent_id:
            input_data["parentId"] = parent_id

        data = await self._execute_query(mutation, {"input": input_data})
        result = data.get("issueCreate", {})

        if not result.get("success"):
            raise Exception("Failed to create issue")

        return result.get("issue", {})

    async def update_issue(
        self,
        issue_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[int] = None,
        assignee_id: Optional[str] = None,
        state_id: Optional[str] = None,
        label_ids: Optional[List[str]] = None,
        due_date: Optional[str] = None,
        estimate: Optional[int] = None,
        cycle_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing issue.

        Args:
            issue_id: Issue ID to update
            title: New title
            description: New description
            priority: New priority
            assignee_id: New assignee
            state_id: New state
            label_ids: New labels (replaces existing)
            due_date: New due date
            estimate: New estimate
            cycle_id: New cycle ID

        Returns:
            Updated issue object
        """
        mutation = """
        mutation($id: String!, $input: IssueUpdateInput!) {
            issueUpdate(id: $id, input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    url
                    state {
                        name
                    }
                }
            }
        }
        """

        input_data = {}
        if title:
            input_data["title"] = title
        if description is not None:
            input_data["description"] = description
        if priority is not None:
            input_data["priority"] = priority
        if assignee_id:
            input_data["assigneeId"] = assignee_id
        if state_id:
            input_data["stateId"] = state_id
        if label_ids is not None:
            input_data["labelIds"] = label_ids
        if due_date:
            input_data["dueDate"] = due_date
        if estimate is not None:
            input_data["estimate"] = estimate
        if cycle_id is not None:
            input_data["cycleId"] = cycle_id

        if not input_data:
            raise ValueError("No updates provided")

        data = await self._execute_query(mutation, {"id": issue_id, "input": input_data})
        result = data.get("issueUpdate", {})

        if not result.get("success"):
            raise Exception("Failed to update issue")

        return result.get("issue", {})

    async def delete_issue(self, issue_id: str) -> bool:
        """Delete (archive) an issue.

        Args:
            issue_id: Issue ID to delete

        Returns:
            True if successful
        """
        mutation = """
        mutation($id: String!) {
            issueDelete(id: $id) {
                success
            }
        }
        """
        data = await self._execute_query(mutation, {"id": issue_id})
        return data.get("issueDelete", {}).get("success", False)

    # ============================================================================
    # Comments
    # ============================================================================

    async def add_comment(self, issue_id: str, body: str) -> Dict[str, Any]:
        """
        Add a comment to an issue.

        Args:
            issue_id: Issue ID
            body: Comment body (markdown supported)

        Returns:
            Created comment object
        """
        mutation = """
        mutation($input: CommentCreateInput!) {
            commentCreate(input: $input) {
                success
                comment {
                    id
                    body
                    createdAt
                    user {
                        name
                    }
                }
            }
        }
        """

        data = await self._execute_query(mutation, {"input": {"issueId": issue_id, "body": body}})
        result = data.get("commentCreate", {})

        if not result.get("success"):
            raise Exception("Failed to add comment")

        return result.get("comment", {})

    async def get_comments(self, issue_id: str) -> List[Dict[str, Any]]:
        """Get all comments for an issue.

        Args:
            issue_id: Issue ID

        Returns:
            List of comment objects
        """
        issue = await self.get_issue(issue_id)
        return issue.get("comments", {}).get("nodes", [])

    # ============================================================================
    # Projects
    # ============================================================================

    async def get_projects(self, team_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get projects, optionally filtered by team.

        Args:
            team_id: Filter by team ID
            limit: Maximum number of projects

        Returns:
            List of project objects
        """
        filter_clause = ""
        if team_id:
            filter_clause = f'filter: {{ accessibleTeams: {{ id: {{ eq: "{team_id}" }} }} }}'

        query = f"""
        query {{
            projects(first: {limit}, {filter_clause}) {{
                nodes {{
                    id
                    name
                    description
                    icon
                    color
                    state
                    progress
                    targetDate
                    startDate
                    url
                    teams {{
                        nodes {{
                            id
                            name
                            key
                        }}
                    }}
                    lead {{
                        id
                        name
                    }}
                }}
            }}
        }}
        """
        data = await self._execute_query(query)
        return data.get("projects", {}).get("nodes", [])

    async def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get a specific project by ID.

        Args:
            project_id: Project ID

        Returns:
            Project object with issues
        """
        query = """
        query($id: String!) {
            project(id: $id) {
                id
                name
                description
                icon
                color
                state
                progress
                targetDate
                startDate
                url
                teams {
                    nodes {
                        id
                        name
                        key
                    }
                }
                lead {
                    id
                    name
                }
                issues {
                    nodes {
                        id
                        identifier
                        title
                        state {
                            name
                        }
                    }
                }
            }
        }
        """
        data = await self._execute_query(query, {"id": project_id})
        return data.get("project", {})

    async def create_project(
        self,
        name: str,
        description: Optional[str] = None,
        team_ids: Optional[List[str]] = None,
        lead_id: Optional[str] = None,
        start_date: Optional[str] = None,
        target_date: Optional[str] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new project.

        Args:
            name: Project name (required)
            description: Project description
            team_ids: List of team IDs
            lead_id: User ID of project lead
            start_date: Start date (ISO format)
            target_date: Target completion date (ISO format)
            icon: Project icon
            color: Project color (hex code)
            state: Project state

        Returns:
            Created project object
        """
        mutation = """
        mutation($input: ProjectCreateInput!) {
            projectCreate(input: $input) {
                success
                project {
                    id
                    name
                    url
                }
            }
        }
        """

        input_data = {"name": name}

        if description:
            input_data["description"] = description
        if team_ids:
            input_data["teamIds"] = team_ids
        if lead_id:
            input_data["leadId"] = lead_id
        if start_date:
            input_data["startDate"] = start_date
        if target_date:
            input_data["targetDate"] = target_date
        if icon:
            input_data["icon"] = icon
        if color:
            input_data["color"] = color
        if state:
            input_data["state"] = state

        data = await self._execute_query(mutation, {"input": input_data})
        result = data.get("projectCreate", {})

        if not result.get("success"):
            raise Exception("Failed to create project")

        return result.get("project", {})

    # ============================================================================
    # Cycles
    # ============================================================================

    async def get_cycles(self, team_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get cycles for a team.

        Args:
            team_id: Team ID
            limit: Maximum number of cycles

        Returns:
            List of cycle objects
        """
        query = """
        query($teamId: String!, $limit: Int!) {
            team(id: $teamId) {
                cycles(first: $limit) {
                    nodes {
                        id
                        name
                        number
                        startsAt
                        endsAt
                        completedAt
                        progress
                    }
                }
            }
        }
        """
        data = await self._execute_query(query, {"teamId": team_id, "limit": limit})
        return data.get("team", {}).get("cycles", {}).get("nodes", [])

    async def get_active_cycle(self, team_id: str) -> Optional[Dict[str, Any]]:
        """Get the current active cycle for a team.

        Args:
            team_id: Team ID

        Returns:
            Active cycle object or None
        """
        query = """
        query($teamId: String!) {
            team(id: $teamId) {
                activeCycle {
                    id
                    name
                    number
                    startsAt
                    endsAt
                    progress
                    issues {
                        nodes {
                            id
                            identifier
                            title
                            state {
                                name
                                type
                            }
                            assignee {
                                name
                            }
                        }
                    }
                }
            }
        }
        """
        data = await self._execute_query(query, {"teamId": team_id})
        return data.get("team", {}).get("activeCycle")

    async def create_cycle(
        self,
        team_id: str,
        name: str,
        starts_at: str,
        ends_at: str
    ) -> Dict[str, Any]:
        """
        Create a cycle for a team.

        Args:
            team_id: Team ID
            name: Cycle name
            starts_at: ISO 8601 start datetime (UTC)
            ends_at: ISO 8601 end datetime (UTC)

        Returns:
            Created cycle object
        """
        mutation = """
        mutation($input: CycleCreateInput!) {
            cycleCreate(input: $input) {
                cycle {
                    id
                    name
                    number
                    startsAt
                    endsAt
                }
            }
        }
        """
        input_data = {
            "teamId": team_id,
            "name": name,
            "startsAt": starts_at,
            "endsAt": ends_at,
        }
        data = await self._execute_query(mutation, {"input": input_data})
        return data.get("cycleCreate", {}).get("cycle", {})

    # ============================================================================
    # Labels
    # ============================================================================

    async def get_labels(self, team_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get labels, optionally filtered by team.

        Args:
            team_id: Optional team ID filter

        Returns:
            List of label objects
        """
        if team_id:
            query = """
            query($teamId: String!) {
                team(id: $teamId) {
                    labels {
                        nodes {
                            id
                            name
                            color
                            description
                        }
                    }
                }
            }
            """
            data = await self._execute_query(query, {"teamId": team_id})
            return data.get("team", {}).get("labels", {}).get("nodes", [])
        else:
            query = """
            query {
                issueLabels {
                    nodes {
                        id
                        name
                        color
                        description
                        team {
                            name
                        }
                    }
                }
            }
            """
            data = await self._execute_query(query)
            return data.get("issueLabels", {}).get("nodes", [])

    async def create_label(
        self,
        team_id: str,
        name: str,
        color: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a label for a team.

        Args:
            team_id: Team ID
            name: Label name
            color: Hex color (e.g., "#ff0000")
            description: Optional description

        Returns:
            Created label object
        """
        mutation = """
        mutation($input: IssueLabelCreateInput!) {
            issueLabelCreate(input: $input) {
                issueLabel {
                    id
                    name
                    color
                }
            }
        }
        """
        input_data = {"teamId": team_id, "name": name}
        if color:
            input_data["color"] = color
        if description:
            input_data["description"] = description

        data = await self._execute_query(mutation, {"input": input_data})
        return data.get("issueLabelCreate", {}).get("issueLabel", {})

    # ============================================================================
    # Users
    # ============================================================================

    async def get_users(self) -> List[Dict[str, Any]]:
        """Get all users in the organization.

        Returns:
            List of user objects
        """
        query = """
        query {
            users {
                nodes {
                    id
                    name
                    email
                    displayName
                    active
                    admin
                    avatarUrl
                }
            }
        }
        """
        data = await self._execute_query(query)
        return data.get("users", {}).get("nodes", [])

    async def get_viewer(self) -> Dict[str, Any]:
        """Get the authenticated user.

        Returns:
            Viewer (authenticated user) object
        """
        query = """
        query {
            viewer {
                id
                name
                email
                displayName
                admin
                assignedIssues {
                    nodes {
                        id
                        identifier
                        title
                        state {
                            name
                        }
                    }
                }
            }
        }
        """
        data = await self._execute_query(query)
        return data.get("viewer", {})

    # ============================================================================
    # Workflow States
    # ============================================================================

    async def get_workflow_states(self, team_id: str) -> List[Dict[str, Any]]:
        """Get workflow states for a team.

        Args:
            team_id: Team ID

        Returns:
            List of workflow state objects
        """
        query = """
        query($teamId: String!) {
            team(id: $teamId) {
                states {
                    nodes {
                        id
                        name
                        color
                        type
                        position
                    }
                }
            }
        }
        """
        data = await self._execute_query(query, {"teamId": team_id})
        return data.get("team", {}).get("states", {}).get("nodes", [])

    # ============================================================================
    # Search
    # ============================================================================

    async def search_issues(self, query_text: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search issues by text.

        Args:
            query_text: Search query
            limit: Maximum results

        Returns:
            List of matching issues
        """
        query = """
        query($query: String!, $limit: Int!) {
            searchIssues(query: $query, first: $limit) {
                nodes {
                    id
                    identifier
                    title
                    description
                    url
                    state {
                        name
                    }
                    team {
                        key
                    }
                    assignee {
                        name
                    }
                }
            }
        }
        """
        data = await self._execute_query(query, {"query": query_text, "limit": limit})
        return data.get("searchIssues", {}).get("nodes", [])
