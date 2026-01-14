# SDK-Native Architecture for mega-agent2

## The Fundamental Shift

**OLD (Phase 1-2)**: Custom orchestrator mimicking mega-agent
**NEW**: Pure Claude Agent SDK with subagents + skills

---

## Correct SDK Architecture

### Core Structure

```python
# main.py - Single entry point
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition

async def main():
    options = ClaudeAgentOptions(
        cwd="/home/ec2-user/mega-agent2",

        # Enable skills
        setting_sources=["user", "project"],

        # Enable all tools including Task for delegation
        allowed_tools=["Read", "Write", "Bash", "Grep", "Glob", "Task", "Skill"],

        # Define all 16 agents as subagents
        agents={
            # Main orchestrator
            "orchestrator": AgentDefinition(
                description="Main coordinator for all tasks",
                prompt="""You are the main orchestrator.

Delegate tasks to specialized agents:
- communication-agent: Slack, email, messaging
- code-agent: GitHub operations, code analysis
- reporting-agent: Generate reports and analytics
- scheduling-agent: Calendar and task scheduling
- automation-agent: ClickUp, Linear task management
- creative-agent: Image generation, creative content
- life-agent: Personal assistant tasks
- web-agent: Web scraping and research
- fieldy-agent: Fieldy coaching data analysis
- wordpress-agent: WordPress content management
- supabase-agent: Database operations
- workflow-agent: Automation workflows
- google-ads-agent: Google Ads campaigns
- agent-improvement-agent: System analysis
- game-ideas-agent: Game concept generation
- game-prototyper-agent: Game prototyping

Use Task tool to delegate to appropriate agent.""",
                tools=["Read", "Write", "Bash", "Task", "Skill"],
                model="sonnet"
            ),

            # Communication Agent
            "communication-agent": AgentDefinition(
                description="Handles Slack, Gmail, and messaging",
                prompt="""You are the Communication Agent.

Available integrations (via Python):
- Slack: SlackMessageReader class in integrations/slack_client.py
- Gmail: GmailClient class in integrations/gmail_client.py

Available skills:
- email-formatting: Email templates and formatting

For Slack operations:
```python
from integrations.slack_client import SlackMessageReader
slack = SlackMessageReader(workspace='flycow')
result = slack.send_dm(recipient, message)
```

For Gmail operations:
```python
from integrations.gmail_client import GmailClient
gmail = GmailClient(account='flycow')
result = gmail.send_email(to, subject, body)
```""",
                tools=["Read", "Write", "Bash", "Skill"],
                model="haiku"  # Fast for messaging
            ),

            # Code Agent
            "code-agent": AgentDefinition(
                description="GitHub operations and code analysis",
                prompt="""You are the Code Agent.

Available integrations:
- GitHub: GitHubClient class in integrations/github_client.py

Available skills:
- github-analysis: Commit analysis, PR reviews, leaderboards

For GitHub operations:
```python
from integrations.github_client import GitHubClient
github = GitHubClient()
commits = github.get_commits(repo, days=1)
```

Use github-analysis skill for analyzing commits and generating reports.""",
                tools=["Read", "Write", "Bash", "Grep", "Glob", "Task", "Skill"],
                model="sonnet"
            ),

            # Reporting Agent
            "reporting-agent": AgentDefinition(
                description="Generate reports and analytics",
                prompt="""You are the Reporting Agent.

Available skills:
- report-generation: HTML reports, charts, dashboards
- data-processing: Data aggregation and transformation
- email-formatting: Email templates

Workflow for reports:
1. Gather data (use Task tool to delegate to domain agents)
2. Process with data-processing skill
3. Generate HTML with report-generation skill
4. Format email with email-formatting skill
5. Send via communication-agent (Task tool)""",
                tools=["Read", "Write", "Bash", "Task", "Skill"],
                model="sonnet"
            ),

            # Fieldy Agent
            "fieldy-agent": AgentDefinition(
                description="Fieldy coaching data analysis and reporting",
                prompt="""You are the Fieldy Agent.

Available skills:
- fieldy-analysis: Coaching data processing
- report-generation: HTML report generation
- data-processing: Data transformation

Workflow:
1. Read Fieldy data files from data/fieldy/
2. Process with fieldy-analysis skill
3. Generate report with report-generation skill
4. Send via communication-agent""",
                tools=["Read", "Write", "Bash", "Task", "Skill"],
                model="haiku"
            ),

            # WordPress Agent
            "wordpress-agent": AgentDefinition(
                description="WordPress content management and SEO",
                prompt="""You are the WordPress Agent.

Available integrations:
- WordPress: WordPressClient class in integrations/wordpress_client.py

Available skills:
- wordpress-content: SEO optimization, content rewriting

For WordPress operations:
```python
from integrations.wordpress_client import WordPressClient
wp = WordPressClient(site='example.com')
posts = wp.get_posts(status='pending')
wp.update_post(post_id, content, metadata)
```

Use wordpress-content skill for SEO and content optimization.""",
                tools=["Read", "Write", "Bash", "Skill"],
                model="sonnet"
            ),

            # Scheduling Agent
            "scheduling-agent": AgentDefinition(
                description="Google Calendar and task scheduling",
                prompt="""You are the Scheduling Agent.

Available integrations:
- Google Calendar: CalendarClient class
- Google Tasks: TasksClient class

Available skills:
- calendar-management: Scheduling rules, conflict detection""",
                tools=["Read", "Write", "Bash", "Skill"],
                model="haiku"
            ),

            # Automation Agent
            "automation-agent": AgentDefinition(
                description="ClickUp and Linear task management",
                prompt="""You are the Automation Agent.

Available integrations:
- ClickUp: ClickUpClient class
- Linear: LinearClient class

Available skills:
- task-management: Task formatting, priority calculation""",
                tools=["Read", "Write", "Bash", "Skill"],
                model="haiku"
            ),

            # Additional agents (Creative, Life, Web, etc.)
            # ... (continuing with all 16 agents)
        }
    )

    # Single query interface
    async for message in query(
        prompt="Your task here",
        options=options
    ):
        if hasattr(message, "result"):
            print(message.result)

asyncio.run(main())
```

---

## Key Differences from Current Implementation

### What Changes

| Component | Current (Wrong) | New (SDK-Native) |
|-----------|----------------|------------------|
| **Orchestrator** | Custom MegaAgentOrchestrator class | ClaudeAgentOptions.agents={} |
| **Task Queue** | asyncio.Queue | SDK handles internally |
| **Agent Pool** | Dict[AgentType, SDKAgentWrapper] | AgentDefinition objects |
| **Inter-agent** | Custom MCP coordinator | Task tool (built-in) |
| **Context** | Custom AsyncContextManager | SDK manages sessions |
| **Entry Point** | orchestrator.execute_task() | query() with delegation |
| **Agent Base** | SDKAgentWrapper class | AgentDefinition (config only) |

### What Stays

| Component | Status |
|-----------|--------|
| **Integrations** | Keep - Slack, GitHub, Gmail API clients |
| **Skills** | Create - New .claude/skills/ directory |
| **Workflows** | Keep - Scheduled scripts calling SDK |
| **Data** | Keep - JSON data files |
| **Config** | Keep - model-routing.json (adapt for SDK) |

---

## Directory Structure (Revised)

```
mega-agent2/
├── main.py                      # NEW: Single SDK entry point
├── agents.py                    # NEW: AgentDefinition configurations
├── requirements.txt
├── .env
│
├── .claude/
│   └── skills/                  # NEW: Shared skills
│       ├── email-formatting/
│       ├── github-analysis/
│       ├── report-generation/
│       ├── wordpress-content/
│       ├── fieldy-analysis/
│       ├── skillz-analysis/
│       ├── data-processing/
│       ├── calendar-management/
│       └── task-management/
│
├── integrations/                # KEEP: API clients
│   ├── slack_client.py
│   ├── github_client.py
│   ├── gmail_client.py
│   ├── calendar_client.py
│   ├── clickup_client.py
│   ├── linear_client.py
│   ├── wordpress_client.py
│   └── supabase_client.py
│
├── workflows/                   # KEEP: Scheduled scripts
│   ├── daily_github_email.py
│   ├── daily_fieldy_email.py
│   ├── skillz_report.py
│   └── daily_wordpress_rewrite.py
│
├── tests/                       # NEW: Test scripts per agent
│   ├── test_communication.py
│   ├── test_code.py
│   ├── test_reporting.py
│   └── test_fieldy.py
│
├── data/                        # KEEP: Runtime data
│   ├── fieldy/
│   ├── skillz_events/
│   ├── github_daily_reviews/
│   └── wordpress/
│
├── config/                      # KEEP: Configuration
│   ├── model-routing.json
│   └── wordpress_sites.json
│
└── src/                         # DELETE: No longer needed
    └── mega_agent2/             # Custom orchestrator removed
```

---

## Migration Strategy

### Step 1: Create SDK-Native Foundation

**Files to create:**
1. `agents.py` - All 16 AgentDefinition configurations
2. `main.py` - SDK entry point with query()
3. `.claude/skills/` - Skill directory structure

**Files to delete:**
- `src/mega_agent2/orchestrator.py` - Custom orchestrator
- `src/mega_agent2/core/base_agent.py` - SDKAgentWrapper
- `src/mega_agent2/types.py` - Custom Task class
- `src/mega_agent2/agents/communication_agent.py` - Custom agent class

**Files to keep/move:**
- `src/mega_agent2/integrations/*` → `integrations/*`
- All integration clients

### Step 2: Refactor Communication Agent

**OLD** (Custom class):
```python
class CommunicationAgent(SDKAgentWrapper):
    def __init__(self, orchestrator):
        super().__init__(...)
        self.slack = SlackMessageReader()
```

**NEW** (AgentDefinition + integration):
```python
# agents.py
"communication-agent": AgentDefinition(
    description="Handles messaging",
    prompt="Use Slack/Gmail integrations via Python...",
    tools=["Bash", "Skill"]
)

# integrations/slack_client.py (keep as-is)
class SlackMessageReader:
    # ... existing code
```

### Step 3: Create Skills

Extract common patterns:
- `email-formatting/` - Used by communication, reporting, fieldy
- `github-analysis/` - Used by code, reporting
- `report-generation/` - Used by reporting, fieldy
- `data-processing/` - Used by multiple agents

### Step 4: Update Workflows

**OLD**:
```python
from mega_agent2 import MegaAgentOrchestrator, AgentType
orchestrator = MegaAgentOrchestrator()
task = await orchestrator.create_task(...)
```

**NEW**:
```python
from claude_agent_sdk import query, ClaudeAgentOptions
from agents import get_agent_options

async for message in query(
    prompt="Generate daily GitHub report",
    options=get_agent_options()
):
    print(message.result)
```

---

## What Needs Refactoring

### Phase 1-2 Code (Already Built)

1. **Communication Agent** - Refactor to AgentDefinition
2. **Test Script** - Update to use SDK query()
3. **Orchestrator** - Delete, replace with SDK
4. **Base Classes** - Delete, use AgentDefinition

### Integration Clients (Keep)

- ✅ `slack_client.py` - Keep as-is
- ✅ `gmail_client.py` - Keep as-is
- ✅ All other integration files - Keep as-is

---

## Next Steps

**What I need to understand:**

1. **Context Management**: How should persistent context work with SDK?
   - SDK manages sessions, but we need persistent data (tasks, memory)
   - Should we keep AsyncContextManager separately?
   - Or use files/database accessed via skills?

2. **MCP Coordinator**: Still needed?
   - Task tool handles agent delegation
   - Do we need custom MCP tools for context?
   - Or rely on filesystem + skills?

3. **Model Routing**: How to integrate with SDK?
   - Each AgentDefinition has `model` parameter
   - Do we still use model-routing.json?
   - Or configure directly in agents.py?

4. **Workflow Interface**: How do scheduled scripts interact?
   - Call `query()` directly?
   - Or create a helper function?
   - How to specify which agent to use?

**Please clarify these points so I can create the correct SDK-native architecture!**
