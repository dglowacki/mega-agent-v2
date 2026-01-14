#!/usr/bin/env python3.11
"""Test SDK with agents but no MCP."""

import asyncio
from dotenv import load_dotenv
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition

load_dotenv()


async def main():
    print("Testing SDK with agents...")

    options = ClaudeAgentOptions(
        cwd="/home/ec2-user/mega-agent2",
        allowed_tools=["Read", "Write", "Bash", "Task"],
        agents={
            "orchestrator": AgentDefinition(
                description="Main coordinator",
                prompt="You are the main orchestrator. Respond to requests.",
                tools=["Read", "Write", "Bash"],
                model="sonnet"
            ),
            "test-agent": AgentDefinition(
                description="Test agent",
                prompt="You are a test agent. Say hello.",
                tools=["Read", "Write"],
                model="haiku"
            )
        }
    )

    try:
        result_found = False
        async for message in query(
            prompt="test-agent: Say hello",
            options=options
        ):
            if hasattr(message, "content"):
                for content in message.content:
                    if hasattr(content, "text"):
                        print(content.text, end="", flush=True)

            if hasattr(message, "result"):
                result_found = True
                # Don't break - let loop complete naturally

        if result_found:
            print()
            print("\n✓ SDK with agents working!")
        else:
            print("\n✗ No result received")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
