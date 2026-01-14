# Mega-Agent2

Multi-agent orchestrator system built with the Claude Agent SDK.

## Overview

Mega-Agent2 is a complete rewrite of the mega-agent system using the official [Claude Agent SDK for Python](https://github.com/anthropics/claude-agent-sdk-python). It maintains feature parity with the original system while leveraging modern async/await patterns and the SDK's native capabilities.

## Features

- **16 Specialized Agents**: Communication, Code Operations, Reporting, Scheduling, Automation, Creative, Life, Web Browser, Game Ideas, Agent Improvement, Game Prototyper, Fieldy, WordPress, Supabase, Workflow, Google Ads
- **Multi-Provider LLM Routing**: Support for Claude (Bedrock), Gemini, OpenAI, and Cerebras via configuration-driven routing
- **Persistent Context**: Async-safe context management with automatic rotation and archiving
- **Inter-Agent Communication**: Agents coordinate via shared MCP coordinator server
- **External Integrations**: Slack, Gmail, GitHub, Google Calendar/Tasks, ClickUp, Linear, WordPress, Supabase, Google Ads, and more

## Architecture

```
MegaAgentOrchestrator
  ├── Task Queue (asyncio.Queue)
  ├── Agent Pool (16 SDKAgentWrapper instances)
  ├── Shared MCP Coordinator Server
  │   ├── dispatch_task tool
  │   ├── get_context tool
  │   └── set_context tool
  └── AsyncContextManager
```

Each agent is a `ClaudeSDKClient` instance with:
- Custom system prompt
- Shared MCP coordinator for inter-agent communication
- Hooks for tool use interception and logging

## Installation

```bash
# Clone repository
git clone https://github.com/flycowgames/mega-agent2
cd mega-agent2

# Install dependencies
pip install -r requirements.txt

# Or install as package
pip install -e .
```

## Configuration

1. Copy environment template:
```bash
cp .env.example .env
```

2. Configure API keys in `.env`:
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `GOOGLE_API_KEY`
- Slack, Gmail, GitHub tokens
- etc.

3. Copy model routing config from mega-agent:
```bash
cp ../mega-agent/config/model-routing.json config/
```

## Usage

```python
import asyncio
from mega_agent2.orchestrator import MegaAgentOrchestrator
from mega_agent2.types import AgentType

async def main():
    # Initialize orchestrator
    orchestrator = MegaAgentOrchestrator()

    # Create task
    task = await orchestrator.create_task(
        agent_type=AgentType.COMMUNICATION,
        description="Send Slack message",
        context={
            "action": "send_slack",
            "channel": "#general",
            "message": "Hello from mega-agent2!"
        },
        priority=8
    )

    # Execute task
    result = await orchestrator.execute_task(task)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

## Key Differences from Mega-Agent (v1)

| Feature | Mega-Agent v1 | Mega-Agent2 |
|---------|---------------|-------------|
| **Architecture** | Custom orchestrator | Claude Agent SDK |
| **Execution Model** | Synchronous | Async/await |
| **Agent Base** | Custom BaseAgent | SDKAgentWrapper (wraps ClaudeSDKClient) |
| **Inter-Agent Comms** | Direct dispatch_task() | MCP coordinator server |
| **File Locking** | fcntl | asyncio.Lock |
| **LLM Calls** | Direct API calls | SDK for Claude, direct for others |
| **Context Manager** | Sync ContextManager | AsyncContextManager |

## Project Structure

```
mega-agent2/
├── src/mega_agent2/
│   ├── types.py               # Task, AgentType, AgentMetadata
│   ├── orchestrator.py        # Main orchestrator
│   ├── core/
│   │   ├── base_agent.py      # SDKAgentWrapper
│   │   ├── context_manager.py # Async context persistence
│   │   ├── llm_router.py      # Multi-provider routing
│   │   └── mcp_coordinator.py # Shared MCP server
│   ├── agents/                # 16 agent implementations
│   └── integrations/          # External API clients
├── config/                    # Configuration files
├── data/                      # Runtime data & context
├── workflows/                 # Automated workflows
├── scripts/                   # Utility scripts
└── tests/                     # Test suite
```

## Development

```bash
# Run tests
pytest

# Format code
black src/ tests/

# Type checking
mypy src/

# Linting
ruff check src/
```

## Migration from Mega-Agent v1

See [MIGRATION.md](MIGRATION.md) for detailed migration guide.

## License

MIT

## Credits

Built with the [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python) by Anthropic.
