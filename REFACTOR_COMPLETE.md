# SDK-Native Refactor Complete

## Major Architecture Change

Migrated from custom orchestrator to **pure Claude Agent SDK** architecture.

## What Changed

### DELETED (Custom Approach)
- ❌ `src/mega_agent2/orchestrator.py` - Custom MegaAgentOrchestrator
- ❌ `src/mega_agent2/core/base_agent.py` - SDKAgentWrapper class
- ❌ `src/mega_agent2/types.py` - Custom Task dataclass
- ❌ `src/mega_agent2/agents/communication_agent.py` - Custom agent class
- ❌ Entire `src/mega_agent2/` directory structure

### CREATED (SDK-Native)
- ✅ `agents.py` - All 16 AgentDefinition configurations
- ✅ `main.py` - SDK `query()` entry point
- ✅ `mcp_coordinator.py` - Hybrid MCP (shared state + files)
- ✅ `integrations/` - Root-level integration clients (moved from src/)
- ✅ `.claude/skills/email-formatting/` - First skill with neo-brutal design
- ✅ `tests/test_communication.py` - SDK-based test

---

## New Architecture

```
query(prompt, options)
    ↓
Orchestrator Agent
    ↓ (Task tool delegation)
Communication Agent
    ↓ (Uses)
- integrations/slack_client.py
- .claude/skills/email-formatting/
    ↓ (Uses)
MCP Coordinator (shared context)
```

### Entry Points

**Interactive:**
```bash
python main.py
```

**Direct query:**
```bash
python main.py "Send Slack message to myself"
```

**Specific agent (workflows):**
```bash
python main.py "communication-agent: Send test DM"
```

### Agent Delegation

Agents use Task tool to coordinate:
```
Reporting Agent
  → Task tool → Code Agent (get GitHub data)
  → Task tool → Communication Agent (send email)
```

---

## Configuration

### AgentDefinition Structure

Each agent configured with:
```python
"agent-name": AgentDefinition(
    description="What the agent does",
    prompt="System prompt with instructions",
    tools=["Read", "Write", "Bash", "Skill", "Task"],
    model="sonnet" | "haiku" | "opus"
)
```

### Models (Native SDK Way)

Hardcoded in AgentDefinitions (not loaded from config):
- **Orchestrator**: sonnet
- **Communication**: haiku (fast)
- **Code**: sonnet
- **Reporting**: sonnet
- **Fieldy**: haiku
- **WordPress**: sonnet
- **Agent Improvement**: opus (most powerful)

### MCP Coordinator (Hybrid)

**Shared state via MCP tools:**
- `get_memory(key)` - Shared memory
- `set_memory(key, value)` - Shared memory
- `log_task(agent, description, status)` - Task logging
- `get_task_history(limit)` - Recent tasks

**Domain data via direct files:**
- `data/fieldy/*.json` - Fieldy data
- `data/github_daily_reviews/*.json` - GitHub data
- `data/skillz_events/*.json` - Skillz events
- `data/wordpress/*.json` - WordPress content

---

## Skills Created

### 1. email-formatting

**Location:** `.claude/skills/email-formatting/`

**Purpose:** Format emails with neo-brutal design aesthetic

**Features:**
- Neo-brutal design (bold, high contrast, thick borders)
- Templates: daily-report, simple, data-table
- Python script: `scripts/format_email.py`

**Used by:** Communication Agent, Reporting Agent, all email-sending agents

---

## Integration Clients (Kept)

All Python API clients moved to `integrations/`:
- `slack_client.py` - SlackMessageReader (workspaces: flycow, trailmix)
- `gmail_client.py` - GmailClient (accounts: flycow, aquarius)
- `github_client.py` - GitHubClient
- `calendar_client.py` - Google Calendar
- `clickup_client.py` - ClickUp API
- `linear_client.py` - Linear API
- `wordpress_client.py` - WordPress API
- `supabase_client.py` - Supabase client

Agents import and use these directly via Python.

---

## Testing

### Communication Agent Test

**File:** `tests/test_communication.py`

**Tests:**
1. Slack DM sending via SDK
2. Email formatting skill usage

**Run:**
```bash
python3.11 tests/test_communication.py
```

### Manual Testing

**Test Slack:**
```bash
python main.py "Send me a Slack DM saying hello"
```

**Test Skills:**
```bash
python main.py "communication-agent: Create a formatted HTML email with title 'Test' and body 'Hello'"
```

---

## Workflows (To Be Updated)

Scheduled workflows will use:
```python
from claude_agent_sdk import query
from agents import get_agent_options

# Direct to specific agent (Option A - faster)
async for message in query(
    prompt="reporting-agent: Generate daily GitHub report",
    options=get_agent_options()
):
    print(message.result)
```

---

## Next Steps

1. ✅ Test Communication Agent
2. ⏭️ Create github-analysis skill
3. ⏭️ Create report-generation skill
4. ⏭️ Create fieldy-analysis skill
5. ⏭️ Test end-to-end workflows
6. ⏭️ Update remaining 11 agents
7. ⏭️ Port workflow scripts to SDK
8. ⏭️ Delete old `src/` directory

---

## Key Benefits

**SDK-Native:**
- ✅ Uses Claude Agent SDK properly (not custom orchestrator)
- ✅ Simpler architecture (no custom classes)
- ✅ Skills for reusable logic
- ✅ Direct Python integration clients
- ✅ Hybrid MCP (structured + flexible)

**Maintains:**
- ✅ 16 domain agents
- ✅ All external integrations
- ✅ Scheduled workflows (systemd)
- ✅ Data persistence

---

Built with [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python)
