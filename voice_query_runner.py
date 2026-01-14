#!/usr/bin/env python3.11
"""
Voice Query Runner - Runs Claude query in isolated process.

Usage:
    python voice_query_runner.py "prompt text"

Outputs JSON: {"success": true, "response": "..."}
"""

import asyncio
import json
import sys
from claude_agent_sdk import query
from claude_agent_sdk.types import ClaudeAgentOptions


async def run_query(prompt: str) -> dict:
    """Run a query and return the result."""
    options = ClaudeAgentOptions(
        cwd="/home/ec2-user/mega-agent2",
        allowed_tools=["Read", "Bash", "Grep", "Glob"],
        system_prompt="You are a helpful voice assistant. Keep responses concise and conversational, suitable for spoken output. Avoid code blocks, markdown, and long lists. When asked for the time, use bash to run 'date' command."
    )

    response_text = ""

    try:
        async for message in query(prompt=prompt, options=options):
            # Stream content
            if hasattr(message, "content"):
                for content in message.content:
                    if hasattr(content, "text"):
                        response_text += content.text

            # Final result
            if hasattr(message, "result"):
                if message.result:
                    response_text = str(message.result)

    except BaseException as e:
        if not response_text:
            response_text = f"I encountered an error processing your request."

    return {"success": bool(response_text), "response": response_text}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "response": "No prompt provided"}))
        sys.exit(1)

    prompt = sys.argv[1]
    result = asyncio.run(run_query(prompt))
    print(json.dumps(result))


if __name__ == "__main__":
    main()
