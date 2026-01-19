"""
MCP Voice Adapter

Provides voice-friendly tool exposure with:
- Tiered tool access (direct, meta-tools, discovery)
- Voice-optimized response formatting
- Tool metadata for latency and confirmation

Tier 1: ~35 direct tools (daily use)
Tier 2: 6 meta-tools (category gateways)
Tier 3: 3 discovery tools (search/schema/execute)
"""

from .formatter import format_response, VoiceFormat
from .metadata import ToolMetadata, LatencyTier, get_tool_metadata
from .tier_config import (
    TIER_1_TOOLS,
    TIER_2_META_TOOLS,
    TIER_3_DISCOVERY,
    get_tier_for_tool,
    get_all_exposed_tools,
)
from .tools import register_basic_tools
from .meta_tools import register_meta_tools
from .discovery import register_discovery_tools


def register_voice_tools(server) -> int:
    """
    Register all voice-related tools with the MCP server.

    Returns:
        Total number of voice tools registered
    """
    count = 0
    count += register_basic_tools(server)
    count += register_meta_tools(server)
    count += register_discovery_tools(server)
    return count


__all__ = [
    # Formatting
    "format_response",
    "VoiceFormat",
    # Metadata
    "ToolMetadata",
    "LatencyTier",
    "get_tool_metadata",
    # Tier config
    "TIER_1_TOOLS",
    "TIER_2_META_TOOLS",
    "TIER_3_DISCOVERY",
    "get_tier_for_tool",
    "get_all_exposed_tools",
    # Registration
    "register_voice_tools",
    "register_basic_tools",
    "register_meta_tools",
    "register_discovery_tools",
]
