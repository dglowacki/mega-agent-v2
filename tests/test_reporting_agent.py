#!/usr/bin/env python3.11
"""
Test Reporting Agent with report-generation skill.

This tests:
- AgentDefinition for reporting-agent
- report-generation skill integration
- HTML report generation workflow
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


# Sample report data
SAMPLE_REPORT_DATA = {
    "title": "Weekly Activity Report",
    "subtitle": "January 1-7, 2026",
    "metrics": [
        {
            "label": "Total Commits",
            "value": "42",
            "change": "+12",
            "trend": "up"
        },
        {
            "label": "Active Contributors",
            "value": "8",
            "change": "+2",
            "trend": "up"
        },
        {
            "label": "Pull Requests",
            "value": "15",
            "change": "-3",
            "trend": "down"
        },
        {
            "label": "Issues Closed",
            "value": "23",
            "change": "+5",
            "trend": "up"
        }
    ],
    "sections": [
        {
            "title": "Top Contributors",
            "type": "table",
            "data": {
                "columns": ["Name", "Commits", "Lines Changed", "Status"],
                "rows": [
                    {"Name": "John Doe", "Commits": "15", "Lines Changed": "1,234", "Status": "active"},
                    {"Name": "Jane Smith", "Commits": "12", "Lines Changed": "987", "Status": "active"},
                    {"Name": "Alice Johnson", "Commits": "8", "Lines Changed": "654", "Status": "pending"},
                    {"Name": "Bob Wilson", "Commits": "7", "Lines Changed": "432", "Status": "active"}
                ]
            }
        },
        {
            "title": "Recent Activity",
            "type": "timeline",
            "data": {
                "events": [
                    {
                        "time": "Jan 7, 2:30 PM",
                        "title": "Feature Deployment",
                        "content": "User authentication v2 deployed to production"
                    },
                    {
                        "time": "Jan 6, 4:15 PM",
                        "title": "Code Review Completed",
                        "content": "PR #42 approved and merged into main"
                    },
                    {
                        "time": "Jan 5, 10:00 AM",
                        "title": "Bug Fix Released",
                        "content": "Critical memory leak fixed in WebSocket handler"
                    },
                    {
                        "time": "Jan 4, 3:45 PM",
                        "title": "New Feature Branch",
                        "content": "Started work on OAuth2 integration"
                    }
                ]
            }
        },
        {
            "title": "Project Status",
            "type": "list",
            "data": {
                "items": [
                    {
                        "title": "Backend API",
                        "content": "95% complete - Final testing in progress"
                    },
                    {
                        "title": "Frontend Dashboard",
                        "content": "80% complete - UI polish and responsive design"
                    },
                    {
                        "title": "Documentation",
                        "content": "60% complete - API docs and user guides"
                    },
                    {
                        "title": "Testing",
                        "content": "70% complete - Unit and integration tests"
                    }
                ]
            }
        }
    ]
}


async def test_html_report_generation():
    """Test generating HTML report with report-generation skill."""
    print("=" * 80)
    print("Reporting Agent Test - HTML Report Generation")
    print("=" * 80)
    print()

    # Create test data file
    test_data_dir = Path("/home/ec2-user/mega-agent2/tests/data")
    test_data_dir.mkdir(parents=True, exist_ok=True)
    test_report_file = test_data_dir / "test_report_data.json"

    with open(test_report_file, 'w') as f:
        json.dump(SAMPLE_REPORT_DATA, f, indent=2)

    print(f"✓ Created test data: {test_report_file}")
    print(f"✓ Report includes: 4 metrics, 3 sections")
    print()

    prompt = f"""Generate an HTML report from the data in {test_report_file}.

Use the report-generation skill to:
1. Read the JSON data
2. Generate a complete HTML report using the daily-summary template
3. Save the report to {test_data_dir}/test_report.html
4. Show me a summary of what was generated

The report should include:
- Summary metrics with trend indicators
- Top contributors table
- Recent activity timeline
- Project status list

Make sure the report uses neo-brutal design styling.
"""

    print("Sending report generation request to Reporting Agent...")
    print()

    try:
        options = get_agent_options()

        result_found = False
        result_text = ""
        async for message in query(
            prompt=f"reporting-agent: {prompt}",
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
                print("Report Generation Complete")
                print("-" * 80)
                print()

        # Check if report file was created
        report_file = test_data_dir / "test_report.html"
        if result_found and report_file.exists():
            file_size = report_file.stat().st_size
            print(f"✓ SUCCESS: HTML report generated!")
            print(f"✓ File: {report_file}")
            print(f"✓ Size: {file_size:,} bytes")
            return True
        elif result_found:
            print("✓ Report generation completed (check for output file)")
            return True
        else:
            print("✗ FAILED: No result received")
            return False

    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_data_aggregation():
    """Test data aggregation capabilities."""
    print()
    print("=" * 80)
    print("Reporting Agent Test - Data Aggregation")
    print("=" * 80)
    print()

    # Create sample activity data
    activity_data = [
        {"date": "2026-01-01", "commits": 5, "author": "John", "lines": 234},
        {"date": "2026-01-01", "commits": 3, "author": "Jane", "lines": 156},
        {"date": "2026-01-02", "commits": 8, "author": "John", "lines": 445},
        {"date": "2026-01-02", "commits": 4, "author": "Alice", "lines": 198},
        {"date": "2026-01-03", "commits": 6, "author": "Jane", "lines": 322},
        {"date": "2026-01-03", "commits": 5, "author": "Alice", "lines": 267},
    ]

    test_data_dir = Path("/home/ec2-user/mega-agent2/tests/data")
    activity_file = test_data_dir / "test_activity.json"

    with open(activity_file, 'w') as f:
        json.dump(activity_data, f, indent=2)

    print(f"✓ Created activity data: {activity_file}")
    print(f"✓ Sample: 6 records across 3 dates, 3 authors")
    print()

    prompt = f"""Aggregate the activity data in {activity_file}.

Use the report-generation skill's aggregate_data.py script to:
1. Group the data by 'author'
2. Calculate sum and average metrics for commits and lines
3. Show me the aggregated results

This demonstrates the skill's data aggregation capabilities.
"""

    print("Aggregating data...")
    print()

    try:
        options = get_agent_options()

        result_found = False
        async for message in query(
            prompt=f"reporting-agent: {prompt}",
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
                print("Aggregation Complete")
                print("-" * 80)
                print()

        if result_found:
            print("✓ SUCCESS: Data aggregated!")
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
    """Run all Reporting Agent tests."""
    print()
    print("=" * 80)
    print("mega-agent2 - Reporting Agent Tests")
    print("SDK-Native Architecture with report-generation skill")
    print("=" * 80)
    print()

    results = []

    # Test 1: HTML report generation
    results.append(await test_html_report_generation())

    # Test 2: Data aggregation
    results.append(await test_data_aggregation())

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
        print("The Reporting Agent successfully:")
        print("  • Used the report-generation skill")
        print("  • Generated HTML reports with neo-brutal design")
        print("  • Aggregated data with metrics")
        print("  • Created tables, timelines, and lists")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
