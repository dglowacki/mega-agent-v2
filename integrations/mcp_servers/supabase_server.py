"""
Supabase MCP Server for Claude Agent SDK

Exposes Supabase Admin API operations as MCP tools that agents can use directly.
"""

import os
import sys
from pathlib import Path

# Add integrations to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_agent_sdk import create_sdk_mcp_server, tool
from supabase_client import SupabaseClient


@tool(
    name="supabase_list_projects",
    description="List all Supabase projects",
    input_schema={
        "type": "object",
        "properties": {}
    }
)
async def supabase_list_projects(args):
    """List Supabase projects."""
    try:
        client = SupabaseClient()
        projects = await client.list_projects()

        project_lines = [f"Found {len(projects)} projects:\n"]
        for project in projects:
            name = project.get("name", "Unnamed")
            project_ref = project.get("ref", "N/A")
            region = project.get("region", "N/A")
            project_lines.append(f"- {name} (Ref: {project_ref}, Region: {region})")

        return {
            "content": [{
                "type": "text",
                "text": "\n".join(project_lines)
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to list projects: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="supabase_set_otp_limit",
    description="Set OTP rate limit for a Supabase project",
    input_schema={
        "type": "object",
        "properties": {
            "project_ref": {
                "type": "string",
                "description": "Project reference ID"
            },
            "limit": {
                "type": "number",
                "description": "OTP rate limit (requests per hour)"
            }
        },
        "required": ["project_ref", "limit"]
    }
)
async def supabase_set_otp_limit(args):
    """Set Supabase OTP rate limit."""
    try:
        client = SupabaseClient()

        result = await client.set_otp_limit(
            project_ref=args["project_ref"],
            limit=args["limit"]
        )

        return {
            "content": [{
                "type": "text",
                "text": f"✓ OTP rate limit updated for project {args['project_ref']}\n"
                       f"New limit: {args['limit']} requests/hour"
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to set OTP limit: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="supabase_get_auth_config",
    description="Get authentication configuration for a Supabase project",
    input_schema={
        "type": "object",
        "properties": {
            "project_ref": {
                "type": "string",
                "description": "Project reference ID"
            }
        },
        "required": ["project_ref"]
    }
)
async def supabase_get_auth_config(args):
    """Get Supabase auth configuration."""
    try:
        client = SupabaseClient()

        config = await client.get_auth_config(project_ref=args["project_ref"])

        return {
            "content": [{
                "type": "text",
                "text": f"✓ Auth configuration for {args['project_ref']}:\n"
                       f"OTP Rate Limit: {config.get('rate_limit_otp', 'N/A')}"
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to get auth config: {str(e)}"
            }],
            "isError": True
        }


# Create and export the MCP server
supabase_mcp_server = create_sdk_mcp_server(
    name="supabase",
    version="1.0.0",
    tools=[
        supabase_list_projects,
        supabase_set_otp_limit,
        supabase_get_auth_config
    ]
)
