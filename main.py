#!/usr/bin/env python3.11
"""
mega-agent2 - SDK-native multi-agent system.

Usage:
    # Interactive mode
    python main.py

    # Direct query
    python main.py "Send a test Slack message to myself"

    # Specific agent
    python main.py --agent reporting-agent "Generate daily GitHub report"
"""

import asyncio
import sys
from claude_agent_sdk import query
from agents import get_agent_options


async def main():
    """Main entry point for mega-agent2."""

    # Parse arguments
    if len(sys.argv) > 1:
        # Check for --agent flag
        if "--agent" in sys.argv:
            agent_idx = sys.argv.index("--agent")
            agent_name = sys.argv[agent_idx + 1]
            prompt_text = " ".join(sys.argv[agent_idx + 2:])
            agent_override = agent_name
        else:
            # Direct query through orchestrator
            prompt_text = " ".join(sys.argv[1:])
            agent_override = None
    else:
        # Interactive mode
        print("=" * 80)
        print("mega-agent2 (Claude Agent SDK)")
        print("=" * 80)
        print()
        prompt_text = input("What would you like me to do? ")
        agent_override = None

    if not prompt_text.strip():
        print("No prompt provided.")
        return

    # Get agent options
    options = get_agent_options()

    # Query with optional agent override
    print()
    print("Processing...")
    print()

    async for message in query(
        prompt=prompt_text,
        options=options,
        agent=agent_override  # None = orchestrator decides, or specific agent
    ):
        # Stream output
        if hasattr(message, "content"):
            for content in message.content:
                if hasattr(content, "text"):
                    print(content.text, end="", flush=True)

        # Final result
        if hasattr(message, "result"):
            print()
            print()
            print("=" * 80)
            print("Result:")
            print("=" * 80)
            print(message.result)
            print()


if __name__ == "__main__":
    asyncio.run(main())
