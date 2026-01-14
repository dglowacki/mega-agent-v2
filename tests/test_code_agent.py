#!/usr/bin/env python3.11
"""
Test Code Agent with github-analysis skill.

This tests:
- AgentDefinition for code-agent
- github-analysis skill integration
- Commit analysis workflow
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add mega-agent2 to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from claude_agent_sdk import query
from agents import get_agent_options

load_dotenv()


# Sample commit data for testing
SAMPLE_COMMITS = [
    {
        "sha": "abc123def456",
        "author": "John Doe",
        "email": "john@example.com",
        "date": "2026-01-03T10:30:00Z",
        "message": "feat: Add user authentication with JWT tokens",
        "files_changed": ["src/auth.js", "src/middleware/auth.js", "tests/auth.test.js"],
        "additions": 125,
        "deletions": 15,
        "files_count": 3
    },
    {
        "sha": "def456ghi789",
        "author": "Jane Smith",
        "email": "jane@example.com",
        "date": "2026-01-03T14:20:00Z",
        "message": "fix: Resolve memory leak in WebSocket handler",
        "files_changed": ["src/websocket.js"],
        "additions": 8,
        "deletions": 12,
        "files_count": 1
    },
    {
        "sha": "ghi789jkl012",
        "author": "John Doe",
        "email": "john@example.com",
        "date": "2026-01-03T16:45:00Z",
        "message": "wip",
        "files_changed": ["src/utils.js"],
        "additions": 3,
        "deletions": 1,
        "files_count": 1
    },
    {
        "sha": "jkl012mno345",
        "author": "Alice Johnson",
        "email": "alice@example.com",
        "date": "2026-01-04T09:15:00Z",
        "message": "refactor: Improve database query performance by adding indexes",
        "files_changed": ["db/schema.sql", "src/models/user.js"],
        "additions": 45,
        "deletions": 20,
        "files_count": 2
    },
    {
        "sha": "mno345pqr678",
        "author": "Jane Smith",
        "email": "jane@example.com",
        "date": "2026-01-04T11:30:00Z",
        "message": "docs: Update API documentation for v2 endpoints",
        "files_changed": ["docs/api.md", "README.md"],
        "additions": 78,
        "deletions": 12,
        "files_count": 2
    }
]


async def test_commit_analysis():
    """Test analyzing commits with github-analysis skill."""
    print("=" * 80)
    print("Code Agent Test - Commit Analysis")
    print("=" * 80)
    print()

    # Create test data file
    test_data_dir = Path("/home/ec2-user/mega-agent2/tests/data")
    test_data_dir.mkdir(parents=True, exist_ok=True)
    test_commits_file = test_data_dir / "test_commits.json"

    with open(test_commits_file, 'w') as f:
        json.dump(SAMPLE_COMMITS, f, indent=2)

    print(f"✓ Created test data: {test_commits_file}")
    print(f"✓ Sample: {len(SAMPLE_COMMITS)} commits from 3 contributors")
    print()

    prompt = f"""Analyze the commits in {test_commits_file} using the github-analysis skill.

Please:
1. Use the analyze_commits.py script to analyze the commit data
2. Show me the top contributors with their scores
3. Identify the most frequently changed files
4. Assess overall commit message quality

The file contains {len(SAMPLE_COMMITS)} commits from a recent project.
"""

    print("Sending analysis request to Code Agent...")
    print()

    try:
        options = get_agent_options()

        result_found = False
        result_text = ""
        async for message in query(
            prompt=f"code-agent: {prompt}",
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
                print("Analysis Complete")
                print("-" * 80)
                print()

        if result_found:
            print("✓ SUCCESS: Code Agent analyzed commits using github-analysis skill!")
            return True
        else:
            print("✗ FAILED: No result received")
            return False

    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_leaderboard_generation():
    """Test generating contributor leaderboard."""
    print()
    print("=" * 80)
    print("Code Agent Test - Leaderboard Generation")
    print("=" * 80)
    print()

    test_commits_file = Path("/home/ec2-user/mega-agent2/tests/data/test_commits.json")

    if not test_commits_file.exists():
        print("✗ Test data not found, run test_commit_analysis first")
        return False

    prompt = f"""Generate a contributor leaderboard from {test_commits_file}.

Use the calculate_leaderboard.py script from the github-analysis skill to:
1. Calculate contributor scores
2. Rank contributors by their overall score
3. Show the top contributors with their metrics

This should demonstrate the github-analysis skill's leaderboard functionality.
"""

    print("Generating leaderboard...")
    print()

    try:
        options = get_agent_options()

        result_found = False
        async for message in query(
            prompt=f"code-agent: {prompt}",
            options=options
        ):
            if hasattr(message, "content"):
                for content in message.content:
                    if hasattr(content, "text"):
                        print(content.text, end="", flush=True)

            if hasattr(message, "result"):
                result_found = True
                print()
                print()
                print("-" * 80)
                print("Leaderboard Generated")
                print("-" * 80)
                print()

        if result_found:
            print("✓ SUCCESS: Leaderboard generated!")
            return True
        else:
            print("✗ FAILED: No result received")
            return False

    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all Code Agent tests."""
    print()
    print("=" * 80)
    print("mega-agent2 - Code Agent Tests")
    print("SDK-Native Architecture with github-analysis skill")
    print("=" * 80)
    print()

    results = []

    # Test 1: Commit analysis
    results.append(await test_commit_analysis())

    # Test 2: Leaderboard generation
    results.append(await test_leaderboard_generation())

    # Summary
    print()
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Tests passed: {sum(results)}/{len(results)}")
    print()

    if all(results):
        print("✓ All tests passed!")
        print()
        print("The Code Agent successfully:")
        print("  • Used the github-analysis skill")
        print("  • Analyzed commit data")
        print("  • Generated contributor metrics")
        print("  • Calculated leaderboards")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
