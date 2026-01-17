"""
Nova Tool Registry

Converts MCP tools to Nova 2 Sonic tool format.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def get_tool_definitions() -> list[dict]:
    """
    Get all tool definitions in Nova format.

    Returns:
        List of tool specs for Nova promptStart
    """
    tools = []

    # ask_claude - always available
    tools.append({
        "toolSpec": {
            "name": "ask_claude",
            "description": "Ask Claude for help with complex reasoning, analysis, code review, document processing, or multi-step tasks. Use when you need deep thinking or access to specialized capabilities.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The question or task for Claude"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    })

    # Weather
    tools.append({
        "toolSpec": {
            "name": "get_weather",
            "description": "Get current weather and forecast for a location",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name or location (default: Parksville, BC)"
                        }
                    },
                    "required": []
                }
            }
        }
    })

    # Web search
    tools.append({
        "toolSpec": {
            "name": "web_search",
            "description": "Search the web for current information",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    })

    # Calendar
    tools.append({
        "toolSpec": {
            "name": "list_calendar_events",
            "description": "List upcoming calendar events",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Number of days to look ahead (default: 7)"
                        }
                    },
                    "required": []
                }
            }
        }
    })

    tools.append({
        "toolSpec": {
            "name": "create_calendar_event",
            "description": "Create a new calendar event",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Event title"
                        },
                        "start_time": {
                            "type": "string",
                            "description": "Start time (ISO format or natural language)"
                        },
                        "duration_minutes": {
                            "type": "integer",
                            "description": "Duration in minutes (default: 60)"
                        },
                        "description": {
                            "type": "string",
                            "description": "Event description"
                        }
                    },
                    "required": ["title", "start_time"]
                }
            }
        }
    })

    # Email
    tools.append({
        "toolSpec": {
            "name": "send_email",
            "description": "Send an email",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "string",
                            "description": "Recipient email address"
                        },
                        "subject": {
                            "type": "string",
                            "description": "Email subject"
                        },
                        "body": {
                            "type": "string",
                            "description": "Email body"
                        }
                    },
                    "required": ["to", "subject", "body"]
                }
            }
        }
    })

    tools.append({
        "toolSpec": {
            "name": "list_emails",
            "description": "List recent emails from inbox",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "count": {
                            "type": "integer",
                            "description": "Number of emails to list (default: 10)"
                        },
                        "unread_only": {
                            "type": "boolean",
                            "description": "Only show unread emails"
                        }
                    },
                    "required": []
                }
            }
        }
    })

    # Slack
    tools.append({
        "toolSpec": {
            "name": "send_slack_message",
            "description": "Send a Slack message",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "channel": {
                            "type": "string",
                            "description": "Channel name or user for DM"
                        },
                        "message": {
                            "type": "string",
                            "description": "Message to send"
                        }
                    },
                    "required": ["channel", "message"]
                }
            }
        }
    })

    # Tasks
    tools.append({
        "toolSpec": {
            "name": "list_tasks",
            "description": "List tasks from task manager",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["open", "completed", "all"],
                            "description": "Filter by status"
                        }
                    },
                    "required": []
                }
            }
        }
    })

    tools.append({
        "toolSpec": {
            "name": "create_task",
            "description": "Create a new task",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Task title"
                        },
                        "description": {
                            "type": "string",
                            "description": "Task description"
                        },
                        "due_date": {
                            "type": "string",
                            "description": "Due date"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "urgent"],
                            "description": "Priority level"
                        }
                    },
                    "required": ["title"]
                }
            }
        }
    })

    # App analytics
    tools.append({
        "toolSpec": {
            "name": "keno_analytics",
            "description": "Get Keno Empire app analytics - revenue, DAU, retention",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "metric": {
                            "type": "string",
                            "enum": ["revenue", "dau", "retention", "summary"],
                            "description": "Metric to fetch"
                        },
                        "date": {
                            "type": "string",
                            "description": "Date to query (default: today)"
                        }
                    },
                    "required": []
                }
            }
        }
    })

    tools.append({
        "toolSpec": {
            "name": "appstore_sales",
            "description": "Get App Store sales data",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "app": {
                            "type": "string",
                            "description": "App name or ID"
                        },
                        "period": {
                            "type": "string",
                            "enum": ["today", "week", "month"],
                            "description": "Time period"
                        }
                    },
                    "required": []
                }
            }
        }
    })

    # Shortcuts
    tools.append({
        "toolSpec": {
            "name": "list_shortcuts",
            "description": "List available shortcuts/automations",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    })

    tools.append({
        "toolSpec": {
            "name": "run_shortcut",
            "description": "Run a shortcut/automation",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Shortcut name"
                        },
                        "input": {
                            "type": "string",
                            "description": "Optional input for the shortcut"
                        }
                    },
                    "required": ["name"]
                }
            }
        }
    })

    # File operations (basic)
    tools.append({
        "toolSpec": {
            "name": "read_file",
            "description": "Read contents of a file",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File path"
                        }
                    },
                    "required": ["path"]
                }
            }
        }
    })

    tools.append({
        "toolSpec": {
            "name": "list_files",
            "description": "List files in a directory",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path"
                        },
                        "pattern": {
                            "type": "string",
                            "description": "File pattern (e.g., *.py)"
                        }
                    },
                    "required": []
                }
            }
        }
    })

    # Time
    tools.append({
        "toolSpec": {
            "name": "get_time",
            "description": "Get current time in a timezone",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "description": "Timezone name (default: America/Los_Angeles)"
                        }
                    },
                    "required": []
                }
            }
        }
    })

    # Image generation
    tools.append({
        "toolSpec": {
            "name": "generate_image",
            "description": "Generate an AI image from a text description using DALL-E/GPT-Image",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Detailed description of the image to generate"
                        }
                    },
                    "required": ["prompt"]
                }
            }
        }
    })

    # Send image to Slack
    tools.append({
        "toolSpec": {
            "name": "send_image_to_slack",
            "description": "Generate an AI image and send it to a Slack user or channel",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Description of the image to generate"
                        },
                        "recipient": {
                            "type": "string",
                            "description": "Slack recipient: @username, #channel, or 'self'"
                        },
                        "message": {
                            "type": "string",
                            "description": "Optional message to include with the image"
                        }
                    },
                    "required": ["prompt", "recipient"]
                }
            }
        }
    })

    logger.info(f"Registered {len(tools)} tools for Nova")
    return tools


def get_tool_count() -> int:
    """Get the number of registered tools."""
    return len(get_tool_definitions())
