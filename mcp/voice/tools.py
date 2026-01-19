"""
Basic Voice Tools

Core tools that every voice agent needs:
- get_time: Current time in any timezone
- get_weather: Weather forecast
- list_capabilities: What the agent can do
"""

import logging
from datetime import datetime
from typing import Optional

from .tier_config import TIER_1_TOOLS, TIER_2_META_TOOLS, TIER_3_DISCOVERY
from .metadata import TOOL_METADATA

logger = logging.getLogger(__name__)


def get_time(timezone: str = "America/Los_Angeles", format: str = "voice") -> dict:
    """
    Get current time in a timezone.

    Args:
        timezone: IANA timezone name (default: America/Los_Angeles for Pacific)
        format: "voice" for conversational, "standard" for full details

    Returns:
        Time information
    """
    try:
        import pytz
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)

        if format == "voice":
            # Conversational format
            time_str = now.strftime("%I:%M %p").lstrip("0")
            day_str = now.strftime("%A")
            return {
                "time": time_str,
                "day": day_str,
                "timezone": timezone.split("/")[-1].replace("_", " "),
                "spoken": f"It's {time_str} on {day_str}"
            }
        else:
            # Full details
            return {
                "time": now.strftime("%I:%M:%S %p"),
                "date": now.strftime("%Y-%m-%d"),
                "day": now.strftime("%A"),
                "timezone": timezone,
                "iso": now.isoformat(),
                "unix": int(now.timestamp())
            }

    except Exception as e:
        logger.error(f"Error getting time for {timezone}: {e}")
        return {"error": f"Could not get time for timezone '{timezone}': {str(e)}"}


def get_weather(
    location: str = "Parksville,CA",
    units: str = "metric",
    format: str = "voice"
) -> dict:
    """
    Get weather forecast for a location.

    Args:
        location: City name or OpenWeatherMap location code
        units: "metric" (Celsius) or "imperial" (Fahrenheit)
        format: "voice" for conversational, "standard" for full details

    Returns:
        Weather information
    """
    import os
    import httpx

    api_key = os.environ.get("OPENWEATHERMAP_API_KEY")
    if not api_key:
        return {"error": "Weather API not configured"}

    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": location,
            "appid": api_key,
            "units": units
        }

        response = httpx.get(url, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()

        temp = round(data["main"]["temp"])
        feels_like = round(data["main"]["feels_like"])
        condition = data["weather"][0]["description"]
        humidity = data["main"]["humidity"]
        city = data["name"]

        unit_symbol = "°C" if units == "metric" else "°F"

        if format == "voice":
            return {
                "temperature": temp,
                "unit": unit_symbol,
                "condition": condition,
                "location": city,
                "spoken": f"It's {temp}{unit_symbol} and {condition} in {city}"
            }
        else:
            return {
                "temperature": temp,
                "feels_like": feels_like,
                "condition": condition,
                "humidity": humidity,
                "location": city,
                "unit": unit_symbol,
                "wind_speed": data["wind"]["speed"],
                "raw": data
            }

    except httpx.HTTPStatusError as e:
        return {"error": f"Weather API error: {e.response.status_code}"}
    except Exception as e:
        logger.error(f"Error getting weather for {location}: {e}")
        return {"error": f"Could not get weather: {str(e)}"}


def list_capabilities(
    category: Optional[str] = None,
    format: str = "voice"
) -> dict:
    """
    List what the voice agent can do.

    Args:
        category: Optional filter by category (e.g., "slack", "git", "files")
        format: "voice" for summary, "standard" for full list

    Returns:
        List of capabilities
    """
    # Build capability categories from tiers
    categories = {
        "basics": ["get time", "get weather", "list capabilities"],
        "apps": ["check app sales", "get downloads", "see ratings"],
        "files": ["read files", "write files", "edit files", "search files"],
        "git": ["check status", "see changes", "view history", "commit", "push"],
        "github": ["list PRs", "view PRs", "list issues"],
        "bash": ["run commands", "background processes"],
        "skills": ["list skills", "create skills", "edit skills", "activate skills"],
        "slack": ["check unread", "see mentions", "send DMs", "post to channels"],
        "email": ["list emails", "search emails", "send emails"],
        "calendar": ["list events", "create events"],
        "linear": ["list issues", "create issues", "view issues"],
        "clickup": ["list tasks", "create tasks", "view tasks"],
        "tasks": ["list tasks", "create tasks", "complete tasks"],
        "web": ["search the web"],
        "images": ["generate images", "create icons"],
        "aws": ["CDK operations", "Lambda", "S3"],
    }

    if category:
        cat_lower = category.lower()
        if cat_lower in categories:
            caps = categories[cat_lower]
            if format == "voice":
                return {
                    "category": category,
                    "capabilities": caps,
                    "spoken": f"For {category}, I can: {', '.join(caps)}"
                }
            return {"category": category, "capabilities": caps}
        else:
            return {"error": f"Unknown category '{category}'. Available: {', '.join(categories.keys())}"}

    # All capabilities
    if format == "voice":
        # Summarize for voice
        highlights = [
            "manage files and code",
            "work with Git and GitHub",
            "send Slack messages and emails",
            "manage calendar and tasks",
            "track Linear and ClickUp issues",
            "check app store metrics",
            "search the web",
            "generate images",
            "build and manage skills",
        ]
        return {
            "summary": highlights,
            "categories": list(categories.keys()),
            "tier1_count": len(TIER_1_TOOLS),
            "meta_tools": list(TIER_2_META_TOOLS.keys()),
            "spoken": f"I can {', '.join(highlights[:5])}, and more. Ask about a specific category for details."
        }
    else:
        return {
            "categories": categories,
            "tier1_tools": sorted(TIER_1_TOOLS),
            "tier2_meta_tools": list(TIER_2_META_TOOLS.keys()),
            "tier3_discovery": list(TIER_3_DISCOVERY.keys()),
            "total_direct": len(TIER_1_TOOLS),
        }


def register_basic_tools(server) -> int:
    """Register basic voice tools with the MCP server."""

    server.register_tool(
        name="get_time",
        description="Get current time in any timezone. Default: Pacific Time.",
        input_schema={
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "IANA timezone (e.g., America/Los_Angeles, Europe/London)",
                    "default": "America/Los_Angeles"
                },
                "format": {
                    "type": "string",
                    "enum": ["voice", "standard"],
                    "description": "Response format",
                    "default": "voice"
                }
            }
        },
        handler=get_time,
        requires_approval=False,
        category="basics"
    )

    server.register_tool(
        name="get_weather",
        description="Get weather forecast. Default location: Parksville, BC.",
        input_schema={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name or location code",
                    "default": "Parksville,CA"
                },
                "units": {
                    "type": "string",
                    "enum": ["metric", "imperial"],
                    "description": "Temperature units",
                    "default": "metric"
                },
                "format": {
                    "type": "string",
                    "enum": ["voice", "standard"],
                    "description": "Response format",
                    "default": "voice"
                }
            }
        },
        handler=get_weather,
        requires_approval=False,
        category="basics"
    )

    server.register_tool(
        name="list_capabilities",
        description="List what I can do. Optionally filter by category.",
        input_schema={
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Filter by category (slack, git, files, email, etc.)"
                },
                "format": {
                    "type": "string",
                    "enum": ["voice", "standard"],
                    "description": "Response format",
                    "default": "voice"
                }
            }
        },
        handler=list_capabilities,
        requires_approval=False,
        category="basics"
    )

    return 3
