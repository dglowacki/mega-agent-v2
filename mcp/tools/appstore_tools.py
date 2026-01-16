"""
App Store Tools - iOS app analytics and sales data.

Provides App Store Connect integration for the voice assistant.
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "integrations"))

logger = logging.getLogger(__name__)

_appstore_client = None


def _get_appstore():
    """Get App Store client."""
    global _appstore_client
    if _appstore_client is None:
        try:
            from appstore_client import AppStoreClient
            _appstore_client = AppStoreClient()
        except Exception as e:
            logger.error(f"Failed to init App Store: {e}")
            return None
    return _appstore_client


def appstore_list_apps() -> str:
    """List all apps in App Store Connect."""
    client = _get_appstore()
    if not client:
        return "Error: App Store not configured"

    try:
        apps = client.get_apps()

        if not apps:
            return "No apps found"

        lines = ["App Store Apps:"]
        for app in apps:
            name = app.get('attributes', {}).get('name', 'Unknown')
            bundle_id = app.get('attributes', {}).get('bundleId', '')
            lines.append(f"  - {name} ({bundle_id})")

        return "\n".join(lines)
    except Exception as e:
        return f"Error listing apps: {str(e)}"


def appstore_get_sales(app_id: str = None, days: int = 7) -> str:
    """Get App Store sales data."""
    client = _get_appstore()
    if not client:
        return "Error: App Store not configured"

    try:
        sales = client.get_sales_report(app_id=app_id, days=days)

        if not sales:
            return f"No sales data for past {days} days"

        lines = [f"Sales Report (past {days} days):"]
        total_units = 0
        total_revenue = 0

        for record in sales:
            units = record.get('units', 0)
            revenue = record.get('revenue', 0)
            total_units += units
            total_revenue += revenue

        lines.append(f"  Total Units: {total_units}")
        lines.append(f"  Total Revenue: ${total_revenue:.2f}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error getting sales: {str(e)}"


def appstore_get_downloads(app_id: str = None, days: int = 7) -> str:
    """Get App Store download metrics."""
    client = _get_appstore()
    if not client:
        return "Error: App Store not configured"

    try:
        downloads = client.get_downloads(app_id=app_id, days=days)

        if not downloads:
            return f"No download data for past {days} days"

        lines = [f"Downloads (past {days} days):"]
        total = sum(d.get('count', 0) for d in downloads)
        lines.append(f"  Total Downloads: {total}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error getting downloads: {str(e)}"


def appstore_get_ratings(app_id: str) -> str:
    """Get App Store ratings and reviews summary."""
    client = _get_appstore()
    if not client:
        return "Error: App Store not configured"

    try:
        ratings = client.get_ratings(app_id)

        if not ratings:
            return "No ratings data"

        avg = ratings.get('average', 0)
        count = ratings.get('count', 0)

        return f"App Ratings:\n  Average: {avg:.1f}/5\n  Total Reviews: {count}"
    except Exception as e:
        return f"Error getting ratings: {str(e)}"


def register_appstore_tools(server) -> int:
    """Register App Store tools."""

    server.register_tool(
        name="appstore_list_apps",
        description="List all apps in App Store Connect.",
        input_schema={
            "type": "object",
            "properties": {}
        },
        handler=appstore_list_apps,
        requires_approval=False,
        category="appstore"
    )

    server.register_tool(
        name="appstore_get_sales",
        description="Get App Store sales data.",
        input_schema={
            "type": "object",
            "properties": {
                "app_id": {"type": "string", "description": "App ID (optional)"},
                "days": {"type": "integer", "description": "Days of data", "default": 7}
            }
        },
        handler=appstore_get_sales,
        requires_approval=False,
        category="appstore"
    )

    server.register_tool(
        name="appstore_get_downloads",
        description="Get App Store download metrics.",
        input_schema={
            "type": "object",
            "properties": {
                "app_id": {"type": "string", "description": "App ID (optional)"},
                "days": {"type": "integer", "description": "Days of data", "default": 7}
            }
        },
        handler=appstore_get_downloads,
        requires_approval=False,
        category="appstore"
    )

    server.register_tool(
        name="appstore_get_ratings",
        description="Get App Store ratings and reviews summary.",
        input_schema={
            "type": "object",
            "properties": {
                "app_id": {"type": "string", "description": "App ID"}
            },
            "required": ["app_id"]
        },
        handler=appstore_get_ratings,
        requires_approval=False,
        category="appstore"
    )

    return 4
