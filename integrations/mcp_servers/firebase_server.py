"""
Firebase MCP Server for Claude Agent SDK

Exposes Firebase/Firestore operations as MCP tools that agents can use directly.
"""

import os
import sys
from pathlib import Path

# Add integrations to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_agent_sdk import create_sdk_mcp_server, tool
from firebase_client import FirebaseClient


@tool(
    name="firebase_read_document",
    description="Read a document from Firebase Firestore",
    input_schema={
        "type": "object",
        "properties": {
            "collection": {
                "type": "string",
                "description": "Collection name"
            },
            "document_id": {
                "type": "string",
                "description": "Document ID"
            }
        },
        "required": ["collection", "document_id"]
    }
)
async def firebase_read_document(args):
    """Read a Firestore document."""
    try:
        client = FirebaseClient()

        doc = await client.read_document(
            collection=args["collection"],
            document_id=args["document_id"]
        )

        if doc:
            return {
                "content": [{
                    "type": "text",
                    "text": f"✓ Document found in {args['collection']}/{args['document_id']}\n"
                           f"Fields: {', '.join(doc.keys())}"
                }]
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": f"Document not found: {args['collection']}/{args['document_id']}"
                }]
            }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to read document: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="firebase_write_document",
    description="Write a document to Firebase Firestore",
    input_schema={
        "type": "object",
        "properties": {
            "collection": {
                "type": "string",
                "description": "Collection name"
            },
            "document_id": {
                "type": "string",
                "description": "Document ID"
            },
            "data": {
                "type": "object",
                "description": "Document data (JSON object)"
            }
        },
        "required": ["collection", "document_id", "data"]
    }
)
async def firebase_write_document(args):
    """Write a Firestore document."""
    try:
        client = FirebaseClient()

        await client.write_document(
            collection=args["collection"],
            document_id=args["document_id"],
            data=args["data"]
        )

        return {
            "content": [{
                "type": "text",
                "text": f"✓ Document written to {args['collection']}/{args['document_id']}"
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to write document: {str(e)}"
            }],
            "isError": True
        }


@tool(
    name="firebase_query_collection",
    description="Query a Firebase Firestore collection",
    input_schema={
        "type": "object",
        "properties": {
            "collection": {
                "type": "string",
                "description": "Collection name"
            },
            "limit": {
                "type": "number",
                "description": "Maximum number of results",
                "default": 100
            }
        },
        "required": ["collection"]
    }
)
async def firebase_query_collection(args):
    """Query a Firestore collection."""
    try:
        client = FirebaseClient()

        docs = await client.query_collection(
            collection=args["collection"],
            limit=args.get("limit", 100)
        )

        return {
            "content": [{
                "type": "text",
                "text": f"✓ Found {len(docs)} documents in collection '{args['collection']}'"
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"✗ Failed to query collection: {str(e)}"
            }],
            "isError": True
        }


# Create and export the MCP server
firebase_mcp_server = create_sdk_mcp_server(
    name="firebase",
    version="1.0.0",
    tools=[
        firebase_read_document,
        firebase_write_document,
        firebase_query_collection
    ]
)
