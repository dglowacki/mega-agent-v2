#!/usr/bin/env python3.11
"""
Test Communication Agent using Claude Agent SDK.

This tests the SDK-native architecture:
- AgentDefinition configuration
- query() interface
- Slack integration
- Email formatting skill
"""

import asyncio
import os
import sys
from pathlib import Path

# Add mega-agent2 to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from claude_agent_sdk import query
from agents import get_agent_options

load_dotenv()


async def test_slack_dm():
    """Test sending Slack DM via Communication Agent."""
    print("=" * 80)
    print("Communication Agent Test - Slack DM")
    print("=" * 80)
    print()

    # Check for Slack token
    slack_token = os.getenv("SLACK_FLYCOW_ACCESS_TOKEN") or os.getenv("SLACK_TRAILMIX_ACCESS_TOKEN")
    if not slack_token:
        print("✗ Error: No Slack token found!")
        print("  Set SLACK_FLYCOW_ACCESS_TOKEN or SLACK_TRAILMIX_ACCESS_TOKEN")
        return False

    print("✓ Slack token found")
    print()

    # Test message
    prompt = """Send a Slack DM to myself with this message:

🤖 mega-agent2 Test - SDK Native

This message confirms:
✓ Claude Agent SDK integration working
✓ AgentDefinition configuration correct
✓ Communication Agent operational
✓ Slack integration functional

System: mega-agent2 (SDK-native architecture)
Timestamp: {timestamp}

Built with Claude Agent SDK
"""

    print("Sending test DM...")
    print()

    try:
        # Get options
        options = get_agent_options()

        # Query through orchestrator (which will delegate to communication-agent)
        result_text = ""
        result_found = False
        async for message in query(
            prompt=f"communication-agent: {prompt}",  # Prefix indicates which agent
            options=options
        ):
            # Stream output
            if hasattr(message, "content"):
                for content in message.content:
                    if hasattr(content, "text"):
                        print(content.text, end="", flush=True)
                        result_text += content.text

            # Final result
            if hasattr(message, "result"):
                result_found = True
                print()
                print()
                print("-" * 80)
                print("Result:")
                print("-" * 80)
                print(message.result)
                print()

        if not result_found:
            print("No result received")
            return False

        print("✓ SUCCESS: Slack DM sent via SDK!")
        return True

    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_email_formatting():
    """Test email formatting skill."""
    print("=" * 80)
    print("Communication Agent Test - Email Formatting")
    print("=" * 80)
    print()

    prompt = """Using the email-formatting skill, create a simple HTML email with:
- Title: "Test Email"
- Body: "This tests the neo-brutal email formatting skill"
- Show me the generated HTML

Do not send the email, just show the HTML output."""

    print("Generating formatted email...")
    print()

    try:
        options = get_agent_options()

        result_found = False
        async for message in query(
            prompt=f"communication-agent: {prompt}",
            options=options
        ):
            if hasattr(message, "content"):
                for content in message.content:
                    if hasattr(content, "text"):
                        print(content.text, end="", flush=True)

            if hasattr(message, "result"):
                result_found = True

        if result_found:
            print()
            print()
            print("✓ SUCCESS: Email formatting skill working!")
            return True
        else:
            print("\nNo result received")
            return False

    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print()
    print("=" * 80)
    print("mega-agent2 - Communication Agent Tests")
    print("SDK-Native Architecture")
    print("=" * 80)
    print()

    results = []

    # Test 1: Slack DM
    print()
    results.append(await test_slack_dm())

    # Test 2: Email formatting
    print()
    results.append(await test_email_formatting())

    # Summary
    print()
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Tests passed: {sum(results)}/{len(results)}")
    print()

    if all(results):
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
