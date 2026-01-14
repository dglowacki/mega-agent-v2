"""
Google Ads MCP Server for Claude Agent SDK

Exposes Google Ads API operations as MCP tools that agents can use directly.
"""

import os
import sys
from pathlib import Path

# Add integrations to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_agent_sdk import create_sdk_mcp_server, tool
from google_ads_client import GoogleAdsClient


@tool(
    name="google_ads_list_customers",
    description="List all accessible Google Ads customer accounts",
    input_schema={
        "type": "object",
        "properties": {}
    }
)
async def google_ads_list_customers(args):
    """List Google Ads customers."""
    try:
        client = GoogleAdsClient()
        customers = await client.list_accessible_customers()

        customer_lines = [f"Found {len(customers)} accessible customers:\n"]
        for customer in customers:
            customer_id = customer.get("customer_id")
            customer_lines.append(f"- Customer ID: {customer_id}")

        return {
            "content": [{
                "type": "text",
                "text": "\n".join(customer_lines)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to list customers: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="google_ads_get_campaigns",
    description="Get all campaigns for a Google Ads customer",
    input_schema={
        "type": "object",
        "properties": {
            "customer_id": {
                "type": "string",
                "description": "Google Ads customer ID"
            }
        },
        "required": ["customer_id"]
    }
)
async def google_ads_get_campaigns(args):
    """Get Google Ads campaigns."""
    try:
        client = GoogleAdsClient()
        campaigns = await client.get_campaigns(customer_id=args["customer_id"])

        campaign_lines = [f"Found {len(campaigns)} campaigns:\n"]
        for campaign in campaigns:
            name = campaign.get("name", "Unnamed")
            status = campaign.get("status", "Unknown")
            campaign_id = campaign.get("id")
            campaign_lines.append(f"- [{status}] {name} (ID: {campaign_id})")

        return {
            "content": [{
                "type": "text",
                "text": "\n".join(campaign_lines)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to get campaigns: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="google_ads_get_account_summary",
    description="Get performance summary for a Google Ads account",
    input_schema={
        "type": "object",
        "properties": {
            "customer_id": {
                "type": "string",
                "description": "Google Ads customer ID"
            },
            "days": {
                "type": "number",
                "description": "Number of days to analyze",
                "default": 30
            }
        },
        "required": ["customer_id"]
    }
)
async def google_ads_get_account_summary(args):
    """Get Google Ads account summary."""
    try:
        client = GoogleAdsClient()
        summary = await client.get_account_summary(
            customer_id=args["customer_id"],
            days=args.get("days", 30)
        )

        return {
            "content": [{
                "type": "text",
                "text": f"✓ Google Ads Summary ({summary.get('period_days')} days):\n"
                       f"Impressions: {summary.get('impressions', 0):,}\n"
                       f"Clicks: {summary.get('clicks', 0):,}\n"
                       f"CTR: {summary.get('ctr', 0)}%\n"
                       f"Avg CPC: ${summary.get('average_cpc', 0)}\n"
                       f"Total Cost: ${summary.get('total_cost', 0)}\n"
                       f"Conversions: {summary.get('conversions', 0)}\n"
                       f"Conversion Value: ${summary.get('conversions_value', 0)}\n"
                       f"ROAS: {summary.get('roas', 0)}"
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to get account summary: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="google_ads_get_campaign_performance",
    description="Get performance metrics for Google Ads campaigns",
    input_schema={
        "type": "object",
        "properties": {
            "customer_id": {
                "type": "string",
                "description": "Google Ads customer ID"
            },
            "campaign_id": {
                "type": "string",
                "description": "Optional specific campaign ID"
            },
            "date_range": {
                "type": "number",
                "description": "Number of days to look back",
                "default": 30
            }
        },
        "required": ["customer_id"]
    }
)
async def google_ads_get_campaign_performance(args):
    """Get Google Ads campaign performance."""
    try:
        client = GoogleAdsClient()

        performance = await client.get_campaign_performance(
            customer_id=args["customer_id"],
            campaign_id=args.get("campaign_id"),
            date_range=args.get("date_range", 30)
        )

        perf_lines = [f"Found {len(performance)} performance records:\n"]

        # Group by campaign
        campaigns = {}
        for record in performance:
            campaign_name = record.get("campaign_name", "Unknown")
            if campaign_name not in campaigns:
                campaigns[campaign_name] = {
                    "impressions": 0,
                    "clicks": 0,
                    "cost": 0,
                    "conversions": 0
                }
            campaigns[campaign_name]["impressions"] += record.get("impressions", 0)
            campaigns[campaign_name]["clicks"] += record.get("clicks", 0)
            campaigns[campaign_name]["cost"] += record.get("cost", 0)
            campaigns[campaign_name]["conversions"] += record.get("conversions", 0)

        for campaign_name, stats in campaigns.items():
            perf_lines.append(
                f"- {campaign_name}:\n"
                f"  Impressions: {stats['impressions']:,}, "
                f"Clicks: {stats['clicks']:,}, "
                f"Cost: ${stats['cost']:.2f}, "
                f"Conversions: {stats['conversions']}"
            )

        return {
            "content": [{
                "type": "text",
                "text": "\n".join(perf_lines)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to get campaign performance: {str(e)}"
            }],
            "isError": True
        }


# Create and export the MCP server
google_ads_mcp_server = create_sdk_mcp_server(
    name="google_ads",
    version="1.0.0",
    tools=[
        google_ads_list_customers,
        google_ads_get_campaigns,
        google_ads_get_account_summary,
        google_ads_get_campaign_performance
    ]
)
