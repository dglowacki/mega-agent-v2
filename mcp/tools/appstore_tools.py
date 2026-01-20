"""
App Store Connect Tools - iOS app management, analytics, and TestFlight.

Provides comprehensive App Store Connect integration including:
- App listing and management
- Sales and download metrics
- TestFlight builds, beta testers, and beta groups
"""

import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Optional, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "integrations"))

logger = logging.getLogger(__name__)

_appstore_client = None


def _get_client():
    """Get App Store Connect client."""
    global _appstore_client
    if _appstore_client is None:
        try:
            from appstore_client import AppStoreConnectClient
            _appstore_client = AppStoreConnectClient()
        except Exception as e:
            logger.error(f"Failed to init App Store Connect: {e}")
            return None
    return _appstore_client


def _run_async(coro):
    """Run async coroutine in sync context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ============================================================================
# App Management Tools
# ============================================================================

def appstore_list_apps() -> str:
    """List all apps in App Store Connect."""
    client = _get_client()
    if not client:
        return "Error: App Store Connect not configured"

    try:
        result = _run_async(client.list_apps())

        if result.get("status") != "success":
            return f"Error: {result.get('error', 'Unknown error')}"

        apps = result.get("apps", [])
        if not apps:
            return "No apps found"

        lines = ["App Store Connect Apps:"]
        for app in apps:
            lines.append(f"  - {app['name']} (ID: {app['id']})")
            lines.append(f"    Bundle: {app['bundle_id']}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error listing apps: {str(e)}"


# ============================================================================
# TestFlight - Builds
# ============================================================================

def testflight_list_builds(
    app_id: Optional[str] = None,
    limit: int = 10
) -> str:
    """List TestFlight builds with status."""
    client = _get_client()
    if not client:
        return "Error: App Store Connect not configured"

    try:
        result = _run_async(client.list_builds(app_id=app_id, limit=limit))

        if result.get("status") != "success":
            return f"Error: {result.get('error', 'Unknown error')}"

        builds = result.get("builds", [])
        if not builds:
            return "No builds found"

        lines = ["TestFlight Builds:"]
        for build in builds:
            version = build.get('version', 'N/A')
            build_num = build.get('build_number', 'N/A')
            state = build.get('processing_state', 'Unknown')
            review = build.get('beta_review_state') or 'Not submitted'
            uploaded = build.get('uploaded_date', 'Unknown')

            lines.append(f"\n  Version {version} (Build {build_num})")
            lines.append(f"    ID: {build['id']}")
            lines.append(f"    Processing: {state}")
            lines.append(f"    Beta Review: {review}")
            lines.append(f"    Uploaded: {uploaded}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error listing builds: {str(e)}"


def testflight_get_build(build_id: str) -> str:
    """Get details for a specific TestFlight build."""
    client = _get_client()
    if not client:
        return "Error: App Store Connect not configured"

    try:
        result = _run_async(client.get_build(build_id))

        if result.get("status") != "success":
            return f"Error: {result.get('error', 'Unknown error')}"

        build = result.get("build", {})

        lines = [f"Build Details:"]
        lines.append(f"  App: {build.get('app_name', 'Unknown')}")
        lines.append(f"  Version: {build.get('version', 'N/A')} (Build {build.get('build_number', 'N/A')})")
        lines.append(f"  ID: {build.get('id')}")
        lines.append(f"  Processing State: {build.get('processing_state', 'Unknown')}")
        lines.append(f"  Beta Review State: {build.get('beta_review_state') or 'Not submitted'}")
        if build.get('beta_review_submitted'):
            lines.append(f"  Review Submitted: {build.get('beta_review_submitted')}")
        lines.append(f"  Uploaded: {build.get('uploaded_date', 'Unknown')}")
        lines.append(f"  Expires: {build.get('expiration_date', 'Unknown')}")
        lines.append(f"  Min OS: {build.get('min_os_version', 'Unknown')}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error getting build: {str(e)}"


def testflight_check_build_status(app_id: str) -> str:
    """Check status of latest TestFlight build for an app."""
    client = _get_client()
    if not client:
        return "Error: App Store Connect not configured"

    try:
        result = _run_async(client.list_builds(app_id=app_id, limit=1))

        if result.get("status") != "success":
            return f"Error: {result.get('error', 'Unknown error')}"

        builds = result.get("builds", [])
        if not builds:
            return "No builds found for this app"

        build = builds[0]
        version = build.get('version', 'N/A')
        build_num = build.get('build_number', 'N/A')
        state = build.get('processing_state', 'Unknown')
        review = build.get('beta_review_state') or 'Not submitted'
        uploaded = build.get('uploaded_date', 'Unknown')

        status_emoji = {
            'APPROVED': 'Approved',
            'IN_REVIEW': 'In Review',
            'WAITING_FOR_REVIEW': 'Waiting for Review',
            'REJECTED': 'Rejected'
        }.get(review, review)

        return f"Latest Build: {version} (Build {build_num})\n  Processing: {state}\n  Beta Review: {status_emoji}\n  Uploaded: {uploaded}"
    except Exception as e:
        return f"Error checking build status: {str(e)}"


# ============================================================================
# TestFlight - Beta Review
# ============================================================================

def testflight_submit_for_review(build_id: str) -> str:
    """Submit a build for TestFlight beta review."""
    client = _get_client()
    if not client:
        return "Error: App Store Connect not configured"

    try:
        result = _run_async(client.submit_for_beta_review(build_id))

        if result.get("status") != "success":
            return f"Error: {result.get('error', 'Unknown error')}"

        return f"Build submitted for beta review.\n  Submission ID: {result.get('submission_id')}\n  Status: {result.get('beta_review_state')}"
    except Exception as e:
        return f"Error submitting for review: {str(e)}"


def testflight_get_review_status(build_id: str) -> str:
    """Get beta review status for a build."""
    client = _get_client()
    if not client:
        return "Error: App Store Connect not configured"

    try:
        result = _run_async(client.get_beta_review_status(build_id))

        if result.get("status") != "success":
            return f"Error: {result.get('error', 'Unknown error')}"

        if not result.get("submitted"):
            return f"Build {build_id} has not been submitted for beta review."

        lines = [f"Beta Review Status:"]
        lines.append(f"  Build ID: {build_id}")
        lines.append(f"  Status: {result.get('beta_review_state', 'Unknown')}")
        if result.get("submitted_date"):
            lines.append(f"  Submitted: {result.get('submitted_date')}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error getting review status: {str(e)}"


# ============================================================================
# TestFlight - Beta Testers
# ============================================================================

def testflight_list_testers(
    app_id: Optional[str] = None,
    email: Optional[str] = None,
    group_id: Optional[str] = None,
    limit: int = 50
) -> str:
    """List beta testers."""
    client = _get_client()
    if not client:
        return "Error: App Store Connect not configured"

    try:
        result = _run_async(client.list_beta_testers(
            app_id=app_id,
            email=email,
            beta_group_id=group_id,
            limit=limit
        ))

        if result.get("status") != "success":
            return f"Error: {result.get('error', 'Unknown error')}"

        testers = result.get("testers", [])
        if not testers:
            return "No beta testers found"

        lines = [f"Beta Testers ({len(testers)}):"]
        for tester in testers:
            name = f"{tester.get('first_name', '')} {tester.get('last_name', '')}".strip() or "No name"
            email = tester.get('email', 'No email')
            state = tester.get('state', 'Unknown')
            lines.append(f"  - {name} <{email}>")
            lines.append(f"    ID: {tester['id']} | State: {state}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error listing testers: {str(e)}"


def testflight_add_tester(
    email: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    group_ids: Optional[str] = None
) -> str:
    """Add a new beta tester."""
    client = _get_client()
    if not client:
        return "Error: App Store Connect not configured"

    try:
        # Parse group_ids if provided as comma-separated string
        beta_group_ids = None
        if group_ids:
            beta_group_ids = [g.strip() for g in group_ids.split(",")]

        result = _run_async(client.add_beta_tester(
            email=email,
            first_name=first_name,
            last_name=last_name,
            beta_group_ids=beta_group_ids
        ))

        if result.get("status") != "success":
            return f"Error: {result.get('error', 'Unknown error')}"

        tester = result.get("tester", {})
        return f"Beta tester added:\n  Email: {tester.get('email')}\n  ID: {tester.get('id')}\n  State: {tester.get('state')}"
    except Exception as e:
        return f"Error adding tester: {str(e)}"


def testflight_remove_tester(tester_id: str) -> str:
    """Remove a beta tester."""
    client = _get_client()
    if not client:
        return "Error: App Store Connect not configured"

    try:
        result = _run_async(client.remove_beta_tester(tester_id))

        if result.get("status") != "success":
            return f"Error: {result.get('error', 'Unknown error')}"

        return f"Beta tester {tester_id} removed successfully."
    except Exception as e:
        return f"Error removing tester: {str(e)}"


# ============================================================================
# TestFlight - Beta Groups
# ============================================================================

def testflight_list_groups(
    app_id: Optional[str] = None,
    is_internal: Optional[bool] = None,
    limit: int = 50
) -> str:
    """List beta groups."""
    client = _get_client()
    if not client:
        return "Error: App Store Connect not configured"

    try:
        result = _run_async(client.list_beta_groups(
            app_id=app_id,
            is_internal=is_internal,
            limit=limit
        ))

        if result.get("status") != "success":
            return f"Error: {result.get('error', 'Unknown error')}"

        groups = result.get("groups", [])
        if not groups:
            return "No beta groups found"

        lines = [f"Beta Groups ({len(groups)}):"]
        for group in groups:
            name = group.get('name', 'Unnamed')
            group_type = "Internal" if group.get('is_internal') else "External"
            lines.append(f"\n  {name} ({group_type})")
            lines.append(f"    ID: {group['id']}")
            if group.get('public_link_enabled'):
                lines.append(f"    Public Link: {group.get('public_link', 'Enabled')}")
                if group.get('public_link_limit'):
                    lines.append(f"    Link Limit: {group.get('public_link_limit')}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error listing groups: {str(e)}"


def testflight_create_group(
    app_id: str,
    name: str,
    is_internal: bool = False,
    public_link_enabled: bool = False
) -> str:
    """Create a new beta group."""
    client = _get_client()
    if not client:
        return "Error: App Store Connect not configured"

    try:
        result = _run_async(client.create_beta_group(
            app_id=app_id,
            name=name,
            is_internal=is_internal,
            public_link_enabled=public_link_enabled
        ))

        if result.get("status") != "success":
            return f"Error: {result.get('error', 'Unknown error')}"

        group = result.get("group", {})
        lines = [f"Beta group created:"]
        lines.append(f"  Name: {group.get('name')}")
        lines.append(f"  ID: {group.get('id')}")
        lines.append(f"  Type: {'Internal' if group.get('is_internal') else 'External'}")
        if group.get('public_link'):
            lines.append(f"  Public Link: {group.get('public_link')}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error creating group: {str(e)}"


def testflight_delete_group(group_id: str) -> str:
    """Delete a beta group."""
    client = _get_client()
    if not client:
        return "Error: App Store Connect not configured"

    try:
        result = _run_async(client.delete_beta_group(group_id))

        if result.get("status") != "success":
            return f"Error: {result.get('error', 'Unknown error')}"

        return f"Beta group {group_id} deleted successfully."
    except Exception as e:
        return f"Error deleting group: {str(e)}"


def testflight_add_build_to_group(group_id: str, build_ids: str) -> str:
    """Add builds to a beta group."""
    client = _get_client()
    if not client:
        return "Error: App Store Connect not configured"

    try:
        # Parse build_ids as comma-separated string
        bid_list = [b.strip() for b in build_ids.split(",")]

        result = _run_async(client.add_build_to_group(group_id, bid_list))

        if result.get("status") != "success":
            return f"Error: {result.get('error', 'Unknown error')}"

        return f"Added {len(bid_list)} build(s) to group {group_id}."
    except Exception as e:
        return f"Error adding builds to group: {str(e)}"


def testflight_add_testers_to_group(group_id: str, tester_ids: str) -> str:
    """Add testers to a beta group."""
    client = _get_client()
    if not client:
        return "Error: App Store Connect not configured"

    try:
        # Parse tester_ids as comma-separated string
        tid_list = [t.strip() for t in tester_ids.split(",")]

        result = _run_async(client.add_testers_to_group(group_id, tid_list))

        if result.get("status") != "success":
            return f"Error: {result.get('error', 'Unknown error')}"

        return f"Added {len(tid_list)} tester(s) to group {group_id}."
    except Exception as e:
        return f"Error adding testers to group: {str(e)}"


def testflight_remove_testers_from_group(group_id: str, tester_ids: str) -> str:
    """Remove testers from a beta group."""
    client = _get_client()
    if not client:
        return "Error: App Store Connect not configured"

    try:
        # Parse tester_ids as comma-separated string
        tid_list = [t.strip() for t in tester_ids.split(",")]

        result = _run_async(client.remove_testers_from_group(group_id, tid_list))

        if result.get("status") != "success":
            return f"Error: {result.get('error', 'Unknown error')}"

        return f"Removed {len(tid_list)} tester(s) from group {group_id}."
    except Exception as e:
        return f"Error removing testers from group: {str(e)}"


# ============================================================================
# Tool Registration
# ============================================================================

def register_appstore_tools(server) -> int:
    """Register all App Store Connect tools including TestFlight."""
    count = 0

    # App Management
    server.register_tool(
        name="appstore_list_apps",
        description="List all apps in App Store Connect with their IDs and bundle identifiers.",
        input_schema={
            "type": "object",
            "properties": {}
        },
        handler=appstore_list_apps,
        requires_approval=False,
        category="appstore"
    )
    count += 1

    # TestFlight - Builds
    server.register_tool(
        name="testflight_list_builds",
        description="List TestFlight builds with processing state and beta review status.",
        input_schema={
            "type": "object",
            "properties": {
                "app_id": {"type": "string", "description": "Filter by app ID"},
                "limit": {"type": "integer", "description": "Max builds to return", "default": 10}
            }
        },
        handler=testflight_list_builds,
        requires_approval=False,
        category="testflight"
    )
    count += 1

    server.register_tool(
        name="testflight_get_build",
        description="Get detailed information for a specific TestFlight build.",
        input_schema={
            "type": "object",
            "properties": {
                "build_id": {"type": "string", "description": "Build ID"}
            },
            "required": ["build_id"]
        },
        handler=testflight_get_build,
        requires_approval=False,
        category="testflight"
    )
    count += 1

    server.register_tool(
        name="testflight_check_build_status",
        description="Check the status of the latest TestFlight build for an app - useful for quick status checks.",
        input_schema={
            "type": "object",
            "properties": {
                "app_id": {"type": "string", "description": "App ID to check"}
            },
            "required": ["app_id"]
        },
        handler=testflight_check_build_status,
        requires_approval=False,
        category="testflight"
    )
    count += 1

    # TestFlight - Beta Review
    server.register_tool(
        name="testflight_submit_for_review",
        description="Submit a TestFlight build for beta app review.",
        input_schema={
            "type": "object",
            "properties": {
                "build_id": {"type": "string", "description": "Build ID to submit"}
            },
            "required": ["build_id"]
        },
        handler=testflight_submit_for_review,
        requires_approval=True,
        category="testflight"
    )
    count += 1

    server.register_tool(
        name="testflight_get_review_status",
        description="Get the beta review status for a specific build.",
        input_schema={
            "type": "object",
            "properties": {
                "build_id": {"type": "string", "description": "Build ID to check"}
            },
            "required": ["build_id"]
        },
        handler=testflight_get_review_status,
        requires_approval=False,
        category="testflight"
    )
    count += 1

    # TestFlight - Beta Testers
    server.register_tool(
        name="testflight_list_testers",
        description="List beta testers, optionally filtered by app, email, or group.",
        input_schema={
            "type": "object",
            "properties": {
                "app_id": {"type": "string", "description": "Filter by app ID"},
                "email": {"type": "string", "description": "Filter by email address"},
                "group_id": {"type": "string", "description": "Filter by beta group ID"},
                "limit": {"type": "integer", "description": "Max testers to return", "default": 50}
            }
        },
        handler=testflight_list_testers,
        requires_approval=False,
        category="testflight"
    )
    count += 1

    server.register_tool(
        name="testflight_add_tester",
        description="Add a new beta tester to TestFlight.",
        input_schema={
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Tester's email address"},
                "first_name": {"type": "string", "description": "Tester's first name"},
                "last_name": {"type": "string", "description": "Tester's last name"},
                "group_ids": {"type": "string", "description": "Comma-separated beta group IDs to add tester to"}
            },
            "required": ["email"]
        },
        handler=testflight_add_tester,
        requires_approval=True,
        category="testflight"
    )
    count += 1

    server.register_tool(
        name="testflight_remove_tester",
        description="Remove a beta tester from TestFlight.",
        input_schema={
            "type": "object",
            "properties": {
                "tester_id": {"type": "string", "description": "Beta tester ID to remove"}
            },
            "required": ["tester_id"]
        },
        handler=testflight_remove_tester,
        requires_approval=True,
        category="testflight"
    )
    count += 1

    # TestFlight - Beta Groups
    server.register_tool(
        name="testflight_list_groups",
        description="List beta groups for TestFlight testing.",
        input_schema={
            "type": "object",
            "properties": {
                "app_id": {"type": "string", "description": "Filter by app ID"},
                "is_internal": {"type": "boolean", "description": "Filter by internal/external"},
                "limit": {"type": "integer", "description": "Max groups to return", "default": 50}
            }
        },
        handler=testflight_list_groups,
        requires_approval=False,
        category="testflight"
    )
    count += 1

    server.register_tool(
        name="testflight_create_group",
        description="Create a new beta group for TestFlight.",
        input_schema={
            "type": "object",
            "properties": {
                "app_id": {"type": "string", "description": "App ID to create group for"},
                "name": {"type": "string", "description": "Group name"},
                "is_internal": {"type": "boolean", "description": "Internal group (team members)", "default": False},
                "public_link_enabled": {"type": "boolean", "description": "Enable public invite link", "default": False}
            },
            "required": ["app_id", "name"]
        },
        handler=testflight_create_group,
        requires_approval=True,
        category="testflight"
    )
    count += 1

    server.register_tool(
        name="testflight_delete_group",
        description="Delete a beta group from TestFlight.",
        input_schema={
            "type": "object",
            "properties": {
                "group_id": {"type": "string", "description": "Beta group ID to delete"}
            },
            "required": ["group_id"]
        },
        handler=testflight_delete_group,
        requires_approval=True,
        category="testflight"
    )
    count += 1

    server.register_tool(
        name="testflight_add_build_to_group",
        description="Add builds to a beta group, making them available to testers in that group.",
        input_schema={
            "type": "object",
            "properties": {
                "group_id": {"type": "string", "description": "Beta group ID"},
                "build_ids": {"type": "string", "description": "Comma-separated build IDs to add"}
            },
            "required": ["group_id", "build_ids"]
        },
        handler=testflight_add_build_to_group,
        requires_approval=True,
        category="testflight"
    )
    count += 1

    server.register_tool(
        name="testflight_add_testers_to_group",
        description="Add testers to a beta group.",
        input_schema={
            "type": "object",
            "properties": {
                "group_id": {"type": "string", "description": "Beta group ID"},
                "tester_ids": {"type": "string", "description": "Comma-separated tester IDs to add"}
            },
            "required": ["group_id", "tester_ids"]
        },
        handler=testflight_add_testers_to_group,
        requires_approval=True,
        category="testflight"
    )
    count += 1

    server.register_tool(
        name="testflight_remove_testers_from_group",
        description="Remove testers from a beta group.",
        input_schema={
            "type": "object",
            "properties": {
                "group_id": {"type": "string", "description": "Beta group ID"},
                "tester_ids": {"type": "string", "description": "Comma-separated tester IDs to remove"}
            },
            "required": ["group_id", "tester_ids"]
        },
        handler=testflight_remove_testers_from_group,
        requires_approval=True,
        category="testflight"
    )
    count += 1

    return count
