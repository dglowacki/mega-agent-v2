#!/usr/bin/env python3
"""
Basic test script for mega-agent2 core infrastructure.

Tests:
- Package imports
- Orchestrator initialization
- Context management
- LLM routing configuration
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mega_agent2 import MegaAgentOrchestrator, AgentType, Task


async def test_imports():
    """Test that all core imports work."""
    print("Testing imports...")

    from mega_agent2.core import AsyncContextManager, MultiProviderRouter, SDKAgentWrapper
    from mega_agent2.types import AgentMetadata

    print("✓ All imports successful")


async def test_orchestrator_init():
    """Test orchestrator initialization."""
    print("\nTesting orchestrator initialization...")

    orchestrator = MegaAgentOrchestrator()
    await orchestrator.initialize()

    print(f"✓ Orchestrator initialized")
    print(f"✓ MCP coordinator created: {orchestrator.mcp_coordinator}")
    print(f"✓ Context manager initialized")
    print(f"✓ LLM router loaded")

    return orchestrator


async def test_task_creation(orchestrator):
    """Test task creation."""
    print("\nTesting task creation...")

    task = await orchestrator.create_task(
        agent_type=AgentType.COMMUNICATION,
        description="Test task",
        context={"test": "data"},
        priority=5
    )

    print(f"✓ Task created: {task.id}")
    print(f"  Type: {task.type.value}")
    print(f"  Description: {task.description}")
    print(f"  Status: {task.status}")

    return task


async def test_context_persistence(orchestrator):
    """Test context management."""
    print("\nTesting context persistence...")

    # Add memory
    await orchestrator.context_manager.add_memory("test_key", "test_value")

    # Retrieve memory
    value = await orchestrator.context_manager.get_memory("test_key")

    assert value == "test_value", f"Expected 'test_value', got {value}"
    print("✓ Memory storage and retrieval working")

    # Get recent tasks
    tasks = await orchestrator.context_manager.get_recent_tasks(5)
    print(f"✓ Recent tasks retrieved: {len(tasks)} tasks")


async def test_llm_routing():
    """Test LLM routing configuration."""
    print("\nTesting LLM routing...")

    from mega_agent2.core import MultiProviderRouter

    router = MultiProviderRouter()

    # Test routing rules
    provider, model_id, config = router.get_model_for_task("communication", "slack_summary")
    print(f"✓ Routing for communication.slack_summary: {provider}/{model_id}")

    # Get routing rules for domain
    rules = router.get_routing_rules_for_domain("communication")
    print(f"✓ Communication agent has {len(rules)} routing rules")


async def main():
    """Run all tests."""
    print("=" * 80)
    print("Mega-Agent2 Core Infrastructure Test")
    print("=" * 80)

    try:
        # Test imports
        await test_imports()

        # Test orchestrator
        orchestrator = await test_orchestrator_init()

        # Test task creation
        task = await test_task_creation(orchestrator)

        # Test context
        await test_context_persistence(orchestrator)

        # Test LLM routing
        await test_llm_routing()

        # Shutdown
        print("\nShutting down...")
        await orchestrator.shutdown()

        print("\n" + "=" * 80)
        print("✓ ALL TESTS PASSED")
        print("=" * 80)

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
