"""
Tests for MCP Voice Adapter

Tests the 3-tier voice tool system:
- Tier 1: Direct access tools
- Tier 2: Meta-tools
- Tier 3: Discovery tools
"""

import pytest
from datetime import datetime


class TestVoiceModuleImports:
    """Test that all voice module components import correctly."""

    def test_import_formatter(self):
        from mcp.voice.formatter import format_response, VoiceFormat
        assert format_response is not None
        assert VoiceFormat.VOICE.value == "voice"
        assert VoiceFormat.STANDARD.value == "standard"

    def test_import_metadata(self):
        from mcp.voice.metadata import (
            ToolMetadata, LatencyTier, get_tool_metadata, TOOL_METADATA
        )
        assert LatencyTier.INSTANT.value == "instant"
        assert LatencyTier.FAST.value == "fast"
        assert LatencyTier.MEDIUM.value == "medium"
        assert LatencyTier.SLOW.value == "slow"
        assert len(TOOL_METADATA) > 30  # Should have metadata for 30+ tools

    def test_import_tier_config(self):
        from mcp.voice.tier_config import (
            TIER_1_TOOLS, TIER_2_META_TOOLS, TIER_3_DISCOVERY,
            get_tier_for_tool, get_all_exposed_tools
        )
        assert len(TIER_1_TOOLS) >= 35
        assert len(TIER_2_META_TOOLS) == 8
        assert len(TIER_3_DISCOVERY) == 3

    def test_import_tools(self):
        from mcp.voice.tools import get_time, get_weather, list_capabilities
        assert callable(get_time)
        assert callable(get_weather)
        assert callable(list_capabilities)

    def test_import_meta_tools(self):
        from mcp.voice.meta_tools import (
            aws_ops, github_ops, content_ops, image_ops, email_ops, skill_ops
        )
        assert callable(aws_ops)
        assert callable(github_ops)

    def test_import_discovery(self):
        from mcp.voice.discovery import tools_search, tools_schema, tools_execute
        assert callable(tools_search)
        assert callable(tools_schema)
        assert callable(tools_execute)


class TestTierConfig:
    """Test tier configuration."""

    def test_tier1_contains_expected_tools(self):
        from mcp.voice.tier_config import TIER_1_TOOLS

        expected = [
            "get_time", "get_weather", "list_capabilities",
            "file_read", "file_write", "file_edit",
            "git_status", "git_diff", "git_commit",
            "github_pr_list", "github_issue_list",
            "slack_send_dm", "slack_get_unread",
            "gmail_list", "gmail_send",
            "clickup_list_tasks", "clickup_create_task",
            "tasks_list", "tasks_create",
        ]
        for tool in expected:
            assert tool in TIER_1_TOOLS, f"Missing Tier 1 tool: {tool}"

    def test_tier2_meta_tools_structure(self):
        from mcp.voice.tier_config import TIER_2_META_TOOLS

        expected_meta = ["aws_ops", "github_ops", "content_ops", "image_ops", "email_ops", "skill_ops", "linear_ops", "browser_ops"]
        for meta in expected_meta:
            assert meta in TIER_2_META_TOOLS
            assert "description" in TIER_2_META_TOOLS[meta]
            assert "actions" in TIER_2_META_TOOLS[meta]
            assert "internal_tools" in TIER_2_META_TOOLS[meta]

    def test_tier3_discovery_structure(self):
        from mcp.voice.tier_config import TIER_3_DISCOVERY

        expected = ["tools_search", "tools_schema", "tools_execute"]
        for tool in expected:
            assert tool in TIER_3_DISCOVERY
            assert "description" in TIER_3_DISCOVERY[tool]
            assert "input_schema" in TIER_3_DISCOVERY[tool]

    def test_get_tier_for_tool(self):
        from mcp.voice.tier_config import get_tier_for_tool

        assert get_tier_for_tool("get_time") == 1
        assert get_tier_for_tool("slack_send_dm") == 1
        assert get_tier_for_tool("aws_ops") == 2
        assert get_tier_for_tool("github_ops") == 2
        assert get_tier_for_tool("tools_search") == 3
        assert get_tier_for_tool("unknown_tool") == 3  # Default to discovery


class TestBasicVoiceTools:
    """Test Tier 1 basic voice tools."""

    def test_get_time_voice_format(self):
        from mcp.voice.tools import get_time

        result = get_time(format="voice")
        assert "time" in result
        assert "day" in result
        assert "spoken" in result
        assert "It's" in result["spoken"]

    def test_get_time_standard_format(self):
        from mcp.voice.tools import get_time

        result = get_time(format="standard")
        assert "time" in result
        assert "date" in result
        assert "iso" in result
        assert "unix" in result

    def test_get_time_different_timezone(self):
        from mcp.voice.tools import get_time

        result = get_time(timezone="Europe/London", format="voice")
        assert "time" in result
        assert "London" in result.get("timezone", "")

    def test_get_time_invalid_timezone(self):
        from mcp.voice.tools import get_time

        result = get_time(timezone="Invalid/Zone")
        assert "error" in result

    def test_list_capabilities_voice(self):
        from mcp.voice.tools import list_capabilities

        result = list_capabilities(format="voice")
        assert "summary" in result
        assert "categories" in result
        assert "spoken" in result
        assert "tier1_count" in result
        assert result["tier1_count"] >= 35

    def test_list_capabilities_category_filter(self):
        from mcp.voice.tools import list_capabilities

        result = list_capabilities(category="slack", format="voice")
        assert "category" in result
        assert result["category"] == "slack"
        assert "capabilities" in result
        assert "spoken" in result

    def test_list_capabilities_invalid_category(self):
        from mcp.voice.tools import list_capabilities

        result = list_capabilities(category="invalid_category")
        assert "error" in result


class TestVoiceFormatter:
    """Test voice response formatting."""

    def test_format_dict_voice(self):
        from mcp.voice.formatter import format_response, VoiceFormat

        data = {"count": 5, "items": ["a", "b", "c", "d", "e"]}
        result = format_response(data, VoiceFormat.VOICE)
        assert "5" in result
        assert "items" in result.lower() or "found" in result.lower()

    def test_format_list_voice(self):
        from mcp.voice.formatter import format_response, VoiceFormat

        data = [{"name": "Task 1"}, {"name": "Task 2"}]
        result = format_response(data, VoiceFormat.VOICE)
        assert "Task 1" in result or "2" in result

    def test_format_git_status(self):
        from mcp.voice.formatter import format_response, VoiceFormat

        data = {"modified": ["a.py", "b.py"], "staged": ["c.py"], "untracked": []}
        result = format_response(data, VoiceFormat.VOICE, "git_status")
        assert "staged" in result.lower() or "modified" in result.lower()

    def test_format_slack_unread(self):
        from mcp.voice.formatter import format_response, VoiceFormat

        data = {"channels": [{"name": "general", "count": 5}], "total": 5}
        result = format_response(data, VoiceFormat.VOICE, "slack_get_unread")
        assert "5" in result
        assert "unread" in result.lower() or "general" in result.lower()

    def test_format_standard_preserves_json(self):
        from mcp.voice.formatter import format_response, VoiceFormat

        data = {"key": "value", "number": 42}
        result = format_response(data, VoiceFormat.STANDARD)
        assert "key" in result
        assert "value" in result
        assert "42" in result

    def test_format_long_text_truncated(self):
        from mcp.voice.formatter import format_response, VoiceFormat

        long_text = "This is a test. " * 100  # ~1600 chars
        result = format_response(long_text, VoiceFormat.VOICE)
        assert len(result) < len(long_text)


class TestToolMetadata:
    """Test tool metadata system."""

    def test_get_known_tool_metadata(self):
        from mcp.voice.metadata import get_tool_metadata, LatencyTier

        meta = get_tool_metadata("get_time")
        assert meta.latency == LatencyTier.INSTANT
        assert not meta.requires_confirmation

    def test_write_tools_require_confirmation(self):
        from mcp.voice.metadata import get_tool_metadata

        write_tools = ["file_write", "git_commit", "slack_send_dm", "gmail_send"]
        for tool in write_tools:
            meta = get_tool_metadata(tool)
            assert meta.requires_confirmation, f"{tool} should require confirmation"

    def test_read_tools_no_confirmation(self):
        from mcp.voice.metadata import get_tool_metadata

        read_tools = ["get_time", "file_read", "git_status", "slack_get_unread"]
        for tool in read_tools:
            meta = get_tool_metadata(tool)
            assert not meta.requires_confirmation, f"{tool} should not require confirmation"

    def test_latency_tiers_assigned(self):
        from mcp.voice.metadata import get_tool_metadata, LatencyTier

        # Instant tools
        assert get_tool_metadata("get_time").latency == LatencyTier.INSTANT
        assert get_tool_metadata("list_capabilities").latency == LatencyTier.INSTANT

        # Fast tools
        assert get_tool_metadata("file_read").latency == LatencyTier.FAST
        assert get_tool_metadata("git_status").latency == LatencyTier.FAST

        # Medium tools
        assert get_tool_metadata("web_search").latency == LatencyTier.MEDIUM

        # Slow tools
        assert get_tool_metadata("image_generate").latency == LatencyTier.SLOW

    def test_unknown_tool_defaults(self):
        from mcp.voice.metadata import get_tool_metadata, LatencyTier

        meta = get_tool_metadata("completely_unknown_tool")
        assert meta.latency == LatencyTier.MEDIUM  # Default
        assert not meta.requires_confirmation  # Default


class TestToolRegistration:
    """Test that voice tools register correctly with MCP server."""

    def test_register_basic_tools(self):
        from mcp.protocol import MCPServer
        from mcp.voice.tools import register_basic_tools

        server = MCPServer()
        count = register_basic_tools(server)

        assert count == 3
        assert "get_time" in server._tools
        assert "get_weather" in server._tools
        assert "list_capabilities" in server._tools

    def test_register_meta_tools(self):
        from mcp.protocol import MCPServer
        from mcp.voice.meta_tools import register_meta_tools

        server = MCPServer()
        count = register_meta_tools(server)

        assert count == 8
        assert "aws_ops" in server._tools
        assert "github_ops" in server._tools
        assert "content_ops" in server._tools
        assert "image_ops" in server._tools
        assert "email_ops" in server._tools
        assert "skill_ops" in server._tools
        assert "linear_ops" in server._tools
        assert "browser_ops" in server._tools

    def test_register_discovery_tools(self):
        from mcp.protocol import MCPServer
        from mcp.voice.discovery import register_discovery_tools

        server = MCPServer()
        count = register_discovery_tools(server)

        assert count == 3
        assert "tools_search" in server._tools
        assert "tools_schema" in server._tools
        assert "tools_execute" in server._tools

    def test_register_all_voice_tools(self):
        from mcp.protocol import MCPServer
        from mcp.voice import register_voice_tools

        server = MCPServer()
        count = register_voice_tools(server)

        assert count == 14  # 3 basic + 8 meta + 3 discovery

    def test_full_registration_includes_voice(self):
        from mcp.protocol import MCPServer
        from mcp.tools import register_all_tools

        server = MCPServer()
        count = register_all_tools(server)

        # Should have voice tools
        voice_tools = [
            "get_time", "get_weather", "list_capabilities",
            "aws_ops", "github_ops", "tools_search"
        ]
        for tool in voice_tools:
            assert tool in server._tools, f"Missing voice tool: {tool}"


class TestDiscoveryTools:
    """Test Tier 3 discovery tools."""

    def test_tools_search_finds_matches(self):
        from mcp.protocol import MCPServer
        from mcp.tools import register_all_tools
        from mcp.voice.discovery import tools_search

        server = MCPServer()
        register_all_tools(server)

        result = tools_search("send message", format="voice")
        assert "matches" in result or "spoken" in result
        assert "slack" in str(result).lower() or "send" in str(result).lower()

    def test_tools_search_no_matches(self):
        from mcp.protocol import MCPServer
        from mcp.tools import register_all_tools
        from mcp.voice.discovery import tools_search

        server = MCPServer()
        register_all_tools(server)

        result = tools_search("xyznonexistent123", format="voice")
        assert "no tools found" in result.get("spoken", "").lower() or len(result.get("matches", [])) == 0

    def test_tools_schema_returns_schema(self):
        from mcp.protocol import MCPServer
        from mcp.tools import register_all_tools
        from mcp.voice.discovery import tools_schema

        server = MCPServer()
        register_all_tools(server)

        result = tools_schema("get_time", format="standard")
        assert "name" in result
        assert "description" in result
        assert "input_schema" in result

    def test_tools_schema_not_found(self):
        from mcp.protocol import MCPServer
        from mcp.tools import register_all_tools
        from mcp.voice.discovery import tools_schema

        server = MCPServer()
        register_all_tools(server)

        result = tools_schema("nonexistent_tool_xyz")
        assert "error" in result


class TestMetaTools:
    """Test Tier 2 meta-tools."""

    def test_aws_ops_invalid_action(self):
        from mcp.voice.meta_tools import aws_ops

        result = aws_ops(action="invalid_action")
        assert "error" in result
        assert "available_actions" in result

    def test_github_ops_invalid_action(self):
        from mcp.voice.meta_tools import github_ops

        result = github_ops(action="invalid_action")
        assert "error" in result
        assert "available_actions" in result

    def test_image_ops_invalid_action(self):
        from mcp.voice.meta_tools import image_ops

        result = image_ops(action="invalid_action")
        assert "error" in result
        assert "available_actions" in result


class TestIntegration:
    """Integration tests for the voice adapter."""

    def test_full_server_starts(self):
        """Test that MCP server initializes with all tools."""
        from mcp.protocol import MCPServer
        from mcp.tools import register_all_tools

        server = MCPServer()
        count = register_all_tools(server)

        assert count >= 120  # Should have 120+ tools

        # Check voice tools present
        voice_tools = [
            "get_time", "get_weather", "list_capabilities",
            "aws_ops", "github_ops", "content_ops",
            "image_ops", "email_ops", "skill_ops",
            "tools_search", "tools_schema", "tools_execute"
        ]
        for tool in voice_tools:
            assert tool in server._tools

    def test_voice_tools_have_format_param(self):
        """Test that voice tools accept format parameter."""
        from mcp.protocol import MCPServer
        from mcp.voice import register_voice_tools

        server = MCPServer()
        register_voice_tools(server)

        # Check format param in schema
        for name in ["get_time", "get_weather", "list_capabilities"]:
            tool = server._tools[name]
            props = tool.input_schema.get("properties", {})
            assert "format" in props, f"{name} missing format param"
            assert "voice" in props["format"].get("enum", [])
