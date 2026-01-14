#!/usr/bin/env python3
"""
Test script for sending a Slack DM via mega-agent2.

This tests:
- CommunicationAgent initialization
- Task creation and execution
- Slack integration
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mega_agent2 import MegaAgentOrchestrator, AgentType


async def main():
    """Send a test Slack DM."""
    print("=" * 80)
    print("Mega-Agent2 Slack DM Test")
    print("=" * 80)
    print()

    # Check for Slack token (workspace-specific)
    from dotenv import load_dotenv
    load_dotenv()

    slack_token = os.getenv("SLACK_FLYCOW_ACCESS_TOKEN") or os.getenv("SLACK_TRAILMIX_ACCESS_TOKEN")
    if not slack_token:
        print("✗ Error: No Slack token found!")
        print("  Set SLACK_FLYCOW_ACCESS_TOKEN or SLACK_TRAILMIX_ACCESS_TOKEN environment variable")
        sys.exit(1)

    print("✓ Slack token found (workspace token)")
    print()

    # Initialize orchestrator
    print("Initializing orchestrator...")
    orchestrator = MegaAgentOrchestrator()
    await orchestrator.initialize()
    print(f"✓ Orchestrator initialized with {len(orchestrator.agents)} agent(s)")
    print()

    # Check if Communication Agent is available
    if AgentType.COMMUNICATION not in orchestrator.agents:
        print("✗ Error: Communication Agent not initialized!")
        sys.exit(1)

    print("✓ Communication Agent ready")
    print()

    # For testing, we'll send to yourself (DM to your own account)
    # This is the safest test that works for any authenticated user
    recipient = "self"  # Special value to send to yourself

    message = """
🤖 **Mega-Agent2 Test Message**

Hello from mega-agent2! This is a test message sent via:
- MegaAgentOrchestrator
- CommunicationAgent
- Claude Agent SDK

System is operational! ✓

Built with [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python)
""".strip()

    print(f"Sending DM to {recipient}...")
    print()

    try:
        # Create task
        task = await orchestrator.create_task(
            agent_type=AgentType.COMMUNICATION,
            description="Send test Slack DM",
            context={
                "action": "send_dm",
                "recipient": recipient,
                "message": message
            },
            priority=8
        )

        print(f"✓ Task created: {task.id}")
        print()

        # Execute task
        result = await orchestrator.execute_task(task)

        print("Result:")
        print("-" * 80)
        print(result)
        print("-" * 80)
        print()

        if result.get("status") == "success":
            print("✓ SUCCESS: Slack DM sent!")
        else:
            print(f"✗ FAILED: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        # Shutdown
        print()
        print("Shutting down...")
        await orchestrator.shutdown()

    print()
    print("=" * 80)
    print("Test complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
