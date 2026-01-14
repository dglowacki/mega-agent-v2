"""
App Store Connect MCP Server for Claude Agent SDK

Exposes App Store Connect operations as MCP tools that agents can use directly.
"""

import os
import sys
from pathlib import Path

# Add integrations to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_agent_sdk import create_sdk_mcp_server, tool
from appstore_client import AppStoreConnectClient


@tool(
    name="appstore_list_apps",
    description="List all apps from App Store Connect",
    input_schema={
        "type": "object",
        "properties": {
            "account": {
                "type": "string",
                "description": "Account name (default: 'primary', can be 'account_2', etc.)",
                "default": "primary"
            }
        }
    }
)
async def appstore_list_apps(args):
    """List all App Store Connect apps."""
    try:
        client = AppStoreConnectClient()
        account = args.get("account", "primary")

        result = await client.list_apps(account=account)

        if result.get("status") == "success":
            apps = result.get("apps", [])
            app_lines = [f"Found {result.get('count', 0)} apps in {account} account:\n"]

            for app in apps:
                app_lines.append(
                    f"- {app.get('name')} (Bundle ID: {app.get('bundle_id')})\n"
                    f"  SKU: {app.get('sku')}, App ID: {app.get('id')}"
                )

            return {
                "content": [{
                    "type": "text",
                    "text": "\n".join(app_lines)
                }]
            }
        else:
            raise Exception(result.get("error", "Unknown error"))

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to list apps: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="appstore_get_sales_report",
    description="Get sales report from App Store Connect",
    input_schema={
        "type": "object",
        "properties": {
            "account": {
                "type": "string",
                "description": "Account name",
                "default": "primary"
            },
            "frequency": {
                "type": "string",
                "description": "Report frequency",
                "enum": ["DAILY", "WEEKLY", "MONTHLY", "YEARLY"],
                "default": "DAILY"
            },
            "report_date": {
                "type": "string",
                "description": "Report date in YYYY-MM-DD format (defaults to yesterday)"
            }
        }
    }
)
async def appstore_get_sales_report(args):
    """Get App Store sales report."""
    try:
        client = AppStoreConnectClient()
        account = args.get("account", "primary")
        frequency = args.get("frequency", "DAILY")
        report_date = args.get("report_date")

        result = await client.get_sales_report(
            account=account,
            frequency=frequency,
            report_date=report_date
        )

        if result.get("status") == "success":
            row_count = result.get("row_count", 0)
            return {
                "content": [{
                    "type": "text",
                    "text": f"✓ Sales report retrieved: {row_count} rows\n"
                           f"Account: {account}\n"
                           f"Frequency: {frequency}\n"
                           f"Date: {result.get('report_date', 'N/A')}"
                }]
            }
        else:
            raise Exception(result.get("error", "Unknown error"))

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to get sales report: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="appstore_get_analytics",
    description="Get app analytics from App Store Connect",
    input_schema={
        "type": "object",
        "properties": {
            "app_id": {
                "type": "string",
                "description": "App ID"
            },
            "account": {
                "type": "string",
                "description": "Account name",
                "default": "primary"
            }
        },
        "required": ["app_id"]
    }
)
async def appstore_get_analytics(args):
    """Get app analytics data."""
    try:
        client = AppStoreConnectClient()
        account = args.get("account", "primary")
        app_id = args["app_id"]

        result = await client.get_app_analytics(
            app_id=app_id,
            account=account
        )

        if result.get("status") == "success":
            return {
                "content": [{
                    "type": "text",
                    "text": f"✓ Analytics retrieved for app {app_id}\n"
                           f"Account: {account}"
                }]
            }
        else:
            raise Exception(result.get("error", "Unknown error"))

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to get analytics: {str(e)}"
            }],
            "isError": True
        }


# Create and export the MCP server
appstore_mcp_server = create_sdk_mcp_server(
    name="appstore",
    version="1.0.0",
    tools=[
        appstore_list_apps,
        appstore_get_sales_report,
        appstore_get_analytics
    ]
)
