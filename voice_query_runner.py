#!/usr/bin/env python3.11
"""
Voice Query Runner - Runs Claude query in isolated process with full context.

Usage:
    python voice_query_runner.py "prompt text"
    python voice_query_runner.py --prompt "text" --system "system prompt" --history "conversation history"

Outputs JSON: {"success": true, "response": "..."}
"""

import argparse
import asyncio
import json
import sys
from claude_agent_sdk import query
from claude_agent_sdk.types import ClaudeAgentOptions


DEFAULT_SYSTEM_PROMPT = """You are a helpful voice assistant. Keep responses concise and conversational, suitable for spoken output. Avoid code blocks, markdown, and long lists. When asked for the time, use bash to run 'date' command."""


async def run_query(prompt: str, system_prompt: str, history: str = "") -> dict:
    """
    Run a query with full context and return the result.

    Args:
        prompt: The user's current query
        system_prompt: System prompt with context (skills, preferences, etc.)
        history: Conversation history string

    Returns:
        Dictionary with success flag and response text
    """
    # Build the full prompt with history if provided
    full_prompt = prompt
    if history:
        full_prompt = f"""CONVERSATION HISTORY:
{history}

CURRENT QUERY:
{prompt}"""

    options = ClaudeAgentOptions(
        cwd="/home/ec2-user/mega-agent2",
        allowed_tools=["Read", "Bash", "Grep", "Glob"],
        system_prompt=system_prompt
    )

    response_text = ""

    try:
        async for message in query(prompt=full_prompt, options=options):
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
    parser = argparse.ArgumentParser(description="Run Claude query with context")
    parser.add_argument("positional_prompt", nargs="?", help="Prompt text (positional)")
    parser.add_argument("--prompt", "-p", help="Prompt text")
    parser.add_argument("--system", "-s", default=DEFAULT_SYSTEM_PROMPT, help="System prompt")
    parser.add_argument("--history", default="", help="Conversation history")

    args = parser.parse_args()

    # Get prompt from either positional or named argument
    prompt = args.prompt or args.positional_prompt

    if not prompt:
        print(json.dumps({"success": False, "response": "No prompt provided"}))
        sys.exit(1)

    result = asyncio.run(run_query(prompt, args.system, args.history))
    print(json.dumps(result))


if __name__ == "__main__":
    main()
