#!/usr/bin/env python3.11
"""Minimal SDK test to isolate issues."""

import asyncio
from dotenv import load_dotenv
from claude_agent_sdk import query, ClaudeAgentOptions

load_dotenv()


async def main():
    print("Testing minimal SDK query...")

    options = ClaudeAgentOptions(
        cwd="/home/ec2-user/mega-agent2",
        allowed_tools=["Read", "Write", "Bash"]
    )

    try:
        async for message in query(
            prompt="Say hello",
            options=options
        ):
            if hasattr(message, "content"):
                for content in message.content:
                    if hasattr(content, "text"):
                        print(content.text, end="", flush=True)

            if hasattr(message, "result"):
                print()
                print("Result:", message.result)

        print("\n✓ SDK working!")

    except Exception as e:
        print(f"\n✗ SDK error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
