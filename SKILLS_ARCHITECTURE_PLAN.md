# Skills Architecture Plan for mega-agent2

## Executive Summary

This plan outlines the integration of **Claude Agent SDK Skills** into mega-agent2 architecture. Skills will handle reusable workflows and domain expertise, while agents provide orchestration and integration with external systems.

---

## Architecture Decision: Skills vs Agent Methods

### The Hybrid Approach

**Skills**: Reusable workflows, business logic, domain expertise
**Agents**: Orchestration, external API integration, task management

```
┌─────────────────────────────────────────────────────────────┐
│                   MegaAgentOrchestrator                      │
│  - Task queue, routing, context management                   │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐   ┌───────▼────────┐
│ SDKAgentWrapper│   │ SDKAgentWrapper│
│ (Communication)│   │ (Code)         │
│                │   │                │
│ Integrations:  │   │ Integrations:  │
│ - Slack API    │   │ - GitHub API   │
│ - Gmail API    │   │ - Git commands │
└───────┬────────┘   └───────┬────────┘
        │                     │
        │  Uses Skills        │  Uses Skills
        ↓                     ↓
┌─────────────────────────────────────────┐
│      Shared Skills (.claude/skills/)    │
│                                         │
│  - email-formatting/                    │
│  - github-analysis/                     │
│  - report-generation/                   │
│  - data-processing/                     │
│  - wordpress-content/                   │
│  - financial-analysis/                  │
└─────────────────────────────────────────┘
```

---

## What Should Be Skills vs Agent Methods

### Skills (Reusable Workflows)

These should be **skills** in `.claude/skills/`:

1. **Report Generation** (`report-generation/`)
   - HTML email templates
   - Data formatting patterns
   - Chart generation workflows
   - Used by: Reporting Agent, Fieldy Agent, Code Agent

2. **GitHub Analysis** (`github-analysis/`)
   - Commit analysis patterns
   - PR review templates
   - Leaderboard calculation
   - Code quality metrics
   - Used by: Code Agent, Reporting Agent

3. **Email Formatting** (`email-formatting/`)
   - HTML email templates
   - Text formatting
   - Subject line patterns
   - Used by: Communication Agent, all reporting agents

4. **Data Processing** (`data-processing/`)
   - JSON transformations
   - CSV processing
   - Data aggregation patterns
   - Used by: Reporting Agent, Fieldy Agent, WordPress Agent

5. **WordPress Content** (`wordpress-content/`)
   - SEO optimization rules
   - Content rewriting patterns
   - Metadata generation
   - Used by: WordPress Agent

6. **Skillz Event Analysis** (`skillz-analysis/`)
   - Event aggregation logic
   - Report formatting
   - Metrics calculation
   - Used by: Reporting Agent

7. **Calendar Management** (`calendar-management/`)
   - Event formatting
   - Scheduling logic
   - Conflict detection
   - Used by: Scheduling Agent, Life Agent

8. **Task Management** (`task-management/`)
   - Priority calculation
   - Task formatting (ClickUp, Linear)
   - Status tracking patterns
   - Used by: Automation Agent, Life Agent

### Agent Methods (External Integrations)

These should remain as **agent integration code**:

1. **Slack API Integration** (Communication Agent)
   - `send_dm()`, `send_message()`, `list_users()`
   - Direct API calls
   - Authentication handling

2. **GitHub API Integration** (Code Agent)
   - `get_commits()`, `create_pr()`, `get_issues()`
   - Direct API calls
   - Authentication handling

3. **Google Calendar API** (Scheduling Agent)
   - `create_event()`, `list_events()`, `update_event()`
   - OAuth handling
   - Direct API calls

4. **ClickUp/Linear API** (Automation Agent)
   - `create_task()`, `get_tasks()`, `update_task()`
   - Direct API calls
   - Authentication handling

5. **WordPress API** (WordPress Agent)
   - `get_posts()`, `update_post()`
   - Direct API calls
   - Authentication handling

6. **Supabase API** (Supabase Agent)
   - Database queries
   - Authentication
   - Direct API calls

---

## Skill Organization Structure

```
mega-agent2/
├── .claude/
│   └── skills/
│       ├── email-formatting/
│       │   ├── SKILL.md
│       │   ├── templates/
│       │   │   ├── daily-report.html
│       │   │   ├── github-summary.html
│       │   │   └── fieldy-summary.html
│       │   └── scripts/
│       │       └── format_email.py
│       │
│       ├── github-analysis/
│       │   ├── SKILL.md
│       │   ├── reference/
│       │   │   ├── metrics.md
│       │   │   └── patterns.md
│       │   └── scripts/
│       │       ├── analyze_commits.py
│       │       ├── calculate_leaderboard.py
│       │       └── review_code.py
│       │
│       ├── report-generation/
│       │   ├── SKILL.md
│       │   ├── templates/
│       │   │   ├── html-report.html
│       │   │   ├── markdown-report.md
│       │   │   └── charts.html
│       │   └── scripts/
│       │       ├── generate_chart.py
│       │       └── aggregate_data.py
│       │
│       ├── wordpress-content/
│       │   ├── SKILL.md
│       │   ├── reference/
│       │   │   ├── seo-rules.md
│       │   │   └── content-guidelines.md
│       │   └── scripts/
│       │       ├── optimize_seo.py
│       │       └── generate_metadata.py
│       │
│       ├── skillz-analysis/
│       │   ├── SKILL.md
│       │   ├── reference/
│       │   │   └── event-types.md
│       │   └── scripts/
│       │       ├── aggregate_events.py
│       │       └── calculate_metrics.py
│       │
│       ├── data-processing/
│       │   ├── SKILL.md
│       │   └── scripts/
│       │       ├── transform_json.py
│       │       ├── process_csv.py
│       │       └── aggregate_data.py
│       │
│       ├── calendar-management/
│       │   ├── SKILL.md
│       │   ├── reference/
│       │   │   └── scheduling-rules.md
│       │   └── scripts/
│       │       └── detect_conflicts.py
│       │
│       └── task-management/
│           ├── SKILL.md
│           ├── reference/
│           │   ├── clickup-patterns.md
│           │   └── linear-patterns.md
│           └── scripts/
│               ├── calculate_priority.py
│               └── format_task.py
│
├── src/mega_agent2/
│   ├── agents/
│   │   ├── communication_agent.py  (uses email-formatting skill)
│   │   ├── code_agent.py           (uses github-analysis skill)
│   │   ├── reporting_agent.py      (uses report-generation skill)
│   │   ├── wordpress_agent.py      (uses wordpress-content skill)
│   │   ├── fieldy_agent.py         (uses report-generation, data-processing)
│   │   ├── scheduling_agent.py     (uses calendar-management skill)
│   │   └── automation_agent.py     (uses task-management skill)
│   │
│   └── integrations/
│       ├── slack_client.py         (Slack API integration)
│       ├── github_client.py        (GitHub API integration)
│       ├── calendar_client.py      (Google Calendar API)
│       ├── clickup_client.py       (ClickUp API)
│       ├── linear_client.py        (Linear API)
│       └── wordpress_client.py     (WordPress API)
```

---

## Migration Strategy: Three-Phase Approach

### Phase 3A: Core Agents WITHOUT Skills (Week 1)

**Goal**: Get agents working with direct integration code first

**Agents to implement**:
1. **Code Agent** - GitHub integration only (no skills yet)
2. **Reporting Agent** - Basic reporting (no skills yet)
3. **Fieldy Agent** - Simple data fetch and format (no skills yet)
4. **WordPress Agent** - Basic content operations (no skills yet)

**Why start without skills?**
- Validate agent architecture works
- Test external integrations
- Establish baseline functionality
- Understand actual reuse patterns

**Deliverable**: 4 working agents with basic functionality

---

### Phase 3B: Extract Skills (Week 2)

**Goal**: Identify and extract common patterns into skills

**Process**:
1. Review code from Phase 3A agents
2. Identify repeated patterns:
   - Report generation across multiple agents
   - Email formatting in Communication + Reporting
   - GitHub analysis patterns
   - Data processing logic
3. Extract into skills following best practices
4. Refactor agents to use skills

**Skills to create** (based on actual usage):
- `report-generation/` - Used by 3+ agents
- `email-formatting/` - Used by 2+ agents
- `github-analysis/` - Used by Code + Reporting agents
- `data-processing/` - Used by 2+ agents

**Deliverable**: 4-6 skills with real usage patterns

---

### Phase 3C: Remaining Agents WITH Skills (Week 3)

**Goal**: Implement remaining agents using skills from the start

**Agents to implement**:
5. **Automation Agent** - Uses task-management skill
6. **Scheduling Agent** - Uses calendar-management skill
7. **Creative Agent** - Direct OpenAI integration
8. **Web Agent** - Web scraping (may need web-research skill)
9. **Life Agent** - Uses multiple skills
10. **Supabase Agent** - Direct API integration
11. **Workflow Agent** - Orchestration logic
12. **Google Ads Agent** - Direct API integration
13. **Agent Improvement** - System analysis (may need analysis skill)
14. **Game Ideas Agent** - Creative generation
15. **Game Prototyper Agent** - Code generation

**Deliverable**: All 16 agents complete with skills where appropriate

---

## Agent Implementation with Skills

### Example: Code Agent with github-analysis Skill

**Agent Code** (handles API integration):
```python
# src/mega_agent2/agents/code_agent.py
from ..core.base_agent import SDKAgentWrapper
from ..integrations.github_client import GitHubClient

class CodeAgent(SDKAgentWrapper):
    SYSTEM_PROMPT = """
You are the Code Operations Agent.

You handle GitHub operations including commit analysis, PR reviews, and code quality checks.

Available integrations:
- GitHub API (via self.github)

Available skills (automatically discovered):
- github-analysis: Commit analysis, PR review templates, leaderboard calculations

When analyzing code or generating reports, use the github-analysis skill.
"""

    def __init__(self, orchestrator):
        super().__init__(
            agent_name="Code Agent",
            agent_domain="code",
            orchestrator=orchestrator,
            system_prompt=self.SYSTEM_PROMPT,
            allowed_tools=["Read", "Write", "Bash", "Skill"]  # Enable skills
        )

        # Initialize GitHub client
        self.github = GitHubClient()

    async def handle_task(self, task: Task) -> Any:
        action = task.context.get("action")

        if action == "get_commits":
            # Use GitHub API to get raw data
            commits = self.github.get_recent_commits(
                repo=task.context.get("repo"),
                days=task.context.get("days", 1)
            )

            # Let SDK + skills analyze the commits
            # The agent will autonomously use github-analysis skill
            return await super().handle_task(task)

        elif action == "code_review":
            # Delegate to SDK with skill support
            return await super().handle_task(task)
```

**Skill Definition** (reusable logic):
```markdown
---
name: github-analysis
description: Analyze GitHub commits, generate PR reviews, calculate leaderboards, and assess code quality. Use when analyzing git commits, reviewing code, or generating GitHub activity reports.
---

# GitHub Analysis

## Commit Analysis

When analyzing commits, extract:
- Author and timestamp
- Commit message quality (clear/vague/cryptic)
- Files changed (count and types)
- Lines added/removed
- Potential issues (TODO, FIXME, debugging code)

Run analysis script:
```bash
python scripts/analyze_commits.py commits.json
```

## PR Review Template

Use this structure for code reviews:

### Summary
[1-2 sentence overview]

### Code Quality
- **Structure**: [assessment]
- **Naming**: [assessment]
- **Documentation**: [assessment]

### Issues Found
- 🔴 Critical: [list]
- 🟡 Warning: [list]
- 🔵 Suggestion: [list]

### Security Check
- [ ] No hardcoded credentials
- [ ] No SQL injection risks
- [ ] No XSS vulnerabilities

## Leaderboard Calculation

Calculate contributor rankings:
```bash
python scripts/calculate_leaderboard.py commits.json --output leaderboard.json
```

Metrics:
- Total commits
- Lines of code
- Code quality score
- Review participation

## Reference

See [reference/metrics.md](reference/metrics.md) for detailed scoring algorithms.
```

**Benefits of This Approach**:
1. ✅ Agent handles API integration (GitHub client)
2. ✅ Skill handles analysis logic (reusable)
3. ✅ Other agents can use github-analysis skill
4. ✅ Easy to update analysis logic in one place
5. ✅ Progressive disclosure (scripts executed, not loaded)

---

## SDK Configuration for mega-agent2

**Updated SDKAgentWrapper base class**:

```python
# src/mega_agent2/core/base_agent.py
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

class SDKAgentWrapper:
    def __init__(
        self,
        agent_name: str,
        agent_domain: str,
        orchestrator,
        system_prompt: str,
        allowed_tools: list[str] = None
    ):
        self.agent_name = agent_name
        self.agent_domain = agent_domain
        self.orchestrator = orchestrator

        # CRITICAL: Enable skills in SDK options
        self.options = ClaudeAgentOptions(
            system_prompt=system_prompt,
            cwd="/home/ec2-user/mega-agent2",

            # REQUIRED for skills
            setting_sources=["user", "project"],

            # Enable Skill tool
            allowed_tools=allowed_tools or ["Read", "Write", "Bash", "Skill"],

            # MCP coordinator for inter-agent communication
            mcp_servers={
                "coordinator": orchestrator.mcp_coordinator
            },

            hooks={
                "PreToolUse": [self._pre_tool_hook],
            }
        )

        self.client: Optional[ClaudeSDKClient] = None
        self.tasks_completed = 0

    async def handle_task(self, task: Task) -> Any:
        """Handle task using SDK client with skill support"""
        async with ClaudeSDKClient(options=self.options) as client:
            self.client = client

            # Build prompt from task
            prompt = self._build_prompt(task)

            # Query agent - skills will be automatically discovered
            await client.query(prompt)

            # Collect response
            result = await self._collect_response(client)

            self.tasks_completed += 1
            return result
```

---

## Skill Development Best Practices for mega-agent2

### 1. Start Simple

```markdown
---
name: report-generation
description: Generate HTML email reports with charts and tables. Use when creating daily summaries, activity reports, or data visualizations.
---

# Report Generation

## Quick start

Create HTML report:
```bash
python scripts/generate_report.py data.json --template daily-summary
```

Available templates:
- daily-summary: Daily activity report
- github-summary: GitHub commit summary
- fieldy-summary: Coaching data report

## Templates

See [templates/](templates/) directory for HTML templates.
```

### 2. Use Scripts for Complex Logic

```python
# .claude/skills/report-generation/scripts/generate_report.py
#!/usr/bin/env python3
"""Generate HTML reports from JSON data."""
import json
import sys
from pathlib import Path

def generate_report(data_file, template_name):
    # Load data
    with open(data_file) as f:
        data = json.load(f)

    # Load template
    template_path = Path(__file__).parent.parent / "templates" / f"{template_name}.html"
    with open(template_path) as f:
        template = f.read()

    # Simple template substitution
    # (In production, use Jinja2 or similar)
    html = template
    for key, value in data.items():
        html = html.replace(f"{{{{{key}}}}}", str(value))

    return html

if __name__ == "__main__":
    result = generate_report(sys.argv[1], sys.argv[2])
    print(result)
```

### 3. Progressive Disclosure for Complex Skills

```markdown
---
name: wordpress-content
description: WordPress SEO optimization, content rewriting, and metadata generation. Use when improving WordPress posts or optimizing for search engines.
---

# WordPress Content Optimization

## Quick reference

**SEO**: See [reference/seo-rules.md](reference/seo-rules.md)
**Content**: See [reference/content-guidelines.md](reference/content-guidelines.md)

## Workflow

- [ ] Analyze current content
- [ ] Apply SEO optimization
- [ ] Rewrite for clarity
- [ ] Generate metadata
- [ ] Validate changes

### Step 1: SEO Analysis

```bash
python scripts/optimize_seo.py input.html
```

### Step 2: Generate Metadata

```bash
python scripts/generate_metadata.py --title "..." --content content.txt
```
```

---

## Questions Before We Start Coding

### 1. Skill Granularity

**Question**: How granular should skills be?

**Option A: Coarse-grained** (fewer, broader skills)
- `reporting/` - All report types (GitHub, Fieldy, Skillz, etc.)
- `api-integrations/` - All API patterns
- Pros: Simpler structure, fewer files
- Cons: Larger skills, less targeted

**Option B: Fine-grained** (more, focused skills)
- `github-analysis/`, `fieldy-analysis/`, `skillz-analysis/`
- `email-formatting/`, `html-generation/`, `chart-generation/`
- Pros: Targeted, reusable, efficient context
- Cons: More files to manage

**Recommendation**: Fine-grained (Option B)
- Better progressive disclosure
- More reusable across agents
- Easier to maintain

**Your preference?**

---

### 2. Workflow Script Complexity

**Question**: How much logic should go into skill scripts?

**Option A: Minimal** (scripts as utilities)
- Scripts do deterministic operations only
- Claude handles business logic
- Example: `validate_data.py` checks format, Claude decides what to do

**Option B: Maximal** (scripts encapsulate logic)
- Scripts handle complex workflows
- Claude just orchestrates
- Example: `generate_report.py` does all formatting, Claude just calls it

**Recommendation**: Balanced approach
- Deterministic operations → scripts
- Business decisions → Claude
- Template processing → scripts
- Content generation → Claude

**Your preference?**

---

### 3. Migration Timing

**Question**: When should we create skills?

**Option A: Incremental** (Phase 3A → 3B → 3C as planned)
- Build agents first without skills
- Extract common patterns
- Refactor to use skills
- Pros: Learn what's actually reusable
- Cons: Some rework needed

**Option B: Upfront** (create skills immediately)
- Design all skills based on mega-agent code review
- Build agents using skills from start
- Pros: No rework, cleaner from start
- Cons: May create skills that aren't needed

**Recommendation**: Incremental (Option A)
- Better fit with "series" approach
- Learn actual patterns before abstracting
- Validate agent architecture first

**Your preference?**

---

### 4. Skill Sharing Strategy

**Question**: Should skills be agent-specific or truly shared?

**Option A: Shared by default**
- All skills in `.claude/skills/`
- Any agent can use any skill
- Pros: Maximum reuse
- Cons: Potential for misuse

**Option B: Agent-specific namespaces**
- `.claude/skills/code-agent/github-analysis/`
- `.claude/skills/reporting-agent/report-generation/`
- Pros: Clear ownership
- Cons: Less reuse

**Option C: Domain-based organization**
- `.claude/skills/github/` (used by Code Agent, Reporting Agent)
- `.claude/skills/email/` (used by Communication Agent, all reporters)
- Pros: Logical grouping
- Cons: Need clear domain boundaries

**Recommendation**: Shared by default (Option A) with clear docs
- Document which agents use each skill
- Clear skill descriptions prevent misuse
- Maximum reuse benefit

**Your preference?**

---

### 5. Subagent Architecture

**Question**: Should mega-agent2 use SDK subagents feature?

**Current architecture**:
- MegaAgentOrchestrator manages agent pool
- Agents are SDKAgentWrapper instances
- Inter-agent communication via MCP coordinator

**SDK subagents approach**:
```python
options = ClaudeAgentOptions(
    agents={
        "orchestrator": AgentDefinition(...),
        "code-agent": AgentDefinition(...),
        "reporting-agent": AgentDefinition(...)
    }
)
```

**Option A: Keep current architecture**
- Custom orchestrator
- Manual agent management
- Pros: More control, matches mega-agent pattern
- Cons: Don't leverage SDK subagent features

**Option B: Migrate to SDK subagents**
- Use SDK's built-in subagent system
- Task tool for delegation
- Pros: Leverage SDK features, simpler
- Cons: Requires architecture change

**Recommendation**: Keep current for now (Option A)
- Already working well
- Maintains compatibility with mega-agent patterns
- Can consider SDK subagents in future refactor

**Your preference?**

---

### 6. Testing Strategy for Skills

**Question**: How should we test skills?

**Option A: Manual testing**
- Test via agents as we build them
- No dedicated skill tests
- Pros: Simple, realistic usage
- Cons: Hard to isolate issues

**Option B: Skill unit tests**
- Test each skill independently
- Test scripts directly
- Pros: Fast feedback, isolated testing
- Cons: More test infrastructure

**Recommendation**: Both
- Unit test scripts (deterministic logic)
- Integration test via agents (full workflow)

**Your preference?**

---

## Summary & Next Steps

### Recommended Approach

1. **Phase 3A** (Week 1): Build 4 core agents WITHOUT skills
   - Code Agent
   - Reporting Agent
   - Fieldy Agent
   - WordPress Agent

2. **Phase 3B** (Week 2): Extract common patterns into skills
   - Identify reuse patterns
   - Create 4-6 skills
   - Refactor agents to use skills

3. **Phase 3C** (Week 3): Build remaining agents WITH skills
   - 11 more agents
   - Use existing skills where applicable

### Key Decisions Needed

Please answer the 6 questions above so I can:
1. Finalize skill structure
2. Determine script complexity
3. Confirm migration approach
4. Start implementing Phase 3A

Once you provide answers, I'll create detailed implementation plans for:
- First 4 agents (Phase 3A)
- Skill extraction strategy (Phase 3B)
- Remaining agents (Phase 3C)

Ready to start coding once you provide direction on these architectural decisions.
