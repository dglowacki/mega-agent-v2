# Mega-Agent2 Migration Plan - Skills-Centric Approach

**Date**: 2026-01-14
**Status**: Planning
**Architecture**: Claude Agent SDK with Skills-First Design

---

## Executive Summary

Continue migration of mega-agent (v1) to mega-agent2 using a **skills-centric approach** where:
- **Reusable workflows and business logic** → Skills (`.claude/skills/`)
- **External API integrations** → Agent integration code (`integrations/`)
- **Task orchestration** → Agent definitions (`agents.py`)

---

## Current Status

### ✅ Completed (Phase 1-2)
- Core infrastructure (async orchestrator, context management, LLM routing)
- Communication Agent (Slack/Gmail)
- AWS Integration (boto3 + aws-skills)
- Existing Skills:
  - github-analysis ✅
  - report-generation ✅
  - fieldy-analysis ✅
  - email-formatting ✅
  - AWS skills (4 skills) ✅

### 📦 Agent Definitions Created (agents.py)
All 18 agents defined as `AgentDefinition`:
1. orchestrator
2. communication-agent
3. code-agent
4. reporting-agent
5. fieldy-agent
6. wordpress-agent
7. automation-agent
8. scheduling-agent
9. creative-agent
10. life-agent
11. web-agent
12. supabase-agent
13. workflow-agent
14. google-ads-agent
15. aws-agent
16. agent-improvement-agent
17. game-ideas-agent
18. game-prototyper-agent

### 🚧 Needs Implementation
- Integration clients for most agents
- Skills for remaining workflows
- MCP servers for integrations
- End-to-end testing

---

## Skills-Centric Migration Strategy

### Phase 3: Core Business Skills (Priority 1)

**Goal**: Implement skills for high-value, reusable workflows

#### 3.1 Communication Skills
**Skill**: `email-templates` (expand existing)
- Daily summary email template
- GitHub activity digest template
- App Store metrics email template
- Calendar event notifications

**Integration**: Remains in agent code
- Slack API (send_dm, send_message)
- Gmail API (send, read, search)

#### 3.2 Data Processing Skills
**Skill**: `data-aggregation`
- App Store sales aggregation
- GitHub commit aggregation
- Skillz event aggregation
- Multi-source data merging

**Integration**: Remains in agent code
- App Store Connect API
- Skillz Developer Portal API
- Firebase Admin SDK

#### 3.3 WordPress Skills
**Skill**: `wordpress-seo-optimization`
- Content rewriting patterns
- SEO metadata generation
- Readability scoring
- Keyword optimization

**Integration**: Remains in agent code
- WordPress REST API
- Post CRUD operations

#### 3.4 Task Management Skills
**Skill**: `task-formatting`
- ClickUp task creation patterns
- Linear issue formatting
- Priority calculation algorithms
- Status mapping logic

**Integration**: Remains in agent code
- ClickUp API
- Linear API

#### 3.5 Calendar Skills
**Skill**: `calendar-scheduling`
- Event formatting patterns
- Conflict detection algorithms
- Meeting optimization logic
- Reminder scheduling

**Integration**: Remains in agent code
- Google Calendar API
- Google Tasks API

---

## Phase 3 Implementation Plan

### Step 1: Port Integration Clients (Week 1)

Port existing integration code from `/home/ec2-user/mega-agent/` to `/home/ec2-user/mega-agent2/integrations/`:

**Priority Order**:
1. ✅ `slack_client.py` (already ported)
2. ✅ `github_client.py` (basic version exists)
3. `appstore_client.py` (App Store Connect API)
4. `wordpress_api.py` (WordPress REST API)
5. `google_calendar.py` (Google Calendar + Tasks)
6. `clickup_client.py` (ClickUp API)
7. `linear_client.py` (Linear API)
8. `supabase_client.py` (Supabase Admin)
9. `firebase_client.py` (Firebase Admin SDK)
10. `google_ads_client.py` (Google Ads API)

**For Each Client**:
- Copy from mega-agent
- Convert to async/await where needed
- Update authentication (use .env from mega-agent2)
- Add type hints
- Create basic tests

### Step 2: Create MCP Servers (Week 1-2)

Update `integrations/mcp_servers.py` with MCP tool definitions:

**Already Defined**:
- ✅ Slack MCP (send_dm, send_message, list_users)
- ✅ Gmail MCP (send, read, search)
- ✅ GitHub MCP (get_repos, get_commits, create_pr)

**To Add**:
- App Store MCP (list_apps, get_sales, get_analytics)
- WordPress MCP (get_posts, update_post, rewrite_content)
- Calendar MCP (create_event, list_events, check_conflicts)
- ClickUp MCP (create_task, get_tasks, update_task)
- Linear MCP (create_issue, get_issues)
- Supabase MCP (query, insert, update, delete)
- Google Ads MCP (get_campaigns, get_metrics)

### Step 3: Create Priority Skills (Week 2)

**Skill 1: `email-templates`**
```bash
.claude/skills/email-templates/
├── SKILL.md
├── templates/
│   ├── daily-summary.html
│   ├── github-digest.html
│   ├── appstore-metrics.html
│   └── calendar-reminder.html
└── scripts/
    ├── render_template.py
    └── format_email.py
```

**Skill 2: `data-aggregation`**
```bash
.claude/skills/data-aggregation/
├── SKILL.md
├── scripts/
│   ├── aggregate_sales.py
│   ├── aggregate_commits.py
│   ├── aggregate_events.py
│   └── merge_sources.py
└── examples/
    └── sample_aggregations.json
```

**Skill 3: `wordpress-seo`**
```bash
.claude/skills/wordpress-seo/
├── SKILL.md
├── scripts/
│   ├── optimize_content.py
│   ├── generate_metadata.py
│   └── calculate_readability.py
└── rules/
    └── seo_guidelines.md
```

**Skill 4: `task-formatting`**
```bash
.claude/skills/task-formatting/
├── SKILL.md
├── scripts/
│   ├── format_clickup_task.py
│   ├── format_linear_issue.py
│   └── calculate_priority.py
└── templates/
    └── task_templates.json
```

**Skill 5: `calendar-scheduling`**
```bash
.claude/skills/calendar-scheduling/
├── SKILL.md
├── scripts/
│   ├── format_event.py
│   ├── detect_conflicts.py
│   └── optimize_schedule.py
└── rules/
    └── scheduling_rules.md
```

### Step 4: Update Agent Prompts (Week 2-3)

Update agent prompts in `agents.py` to reference available skills:

**Example: reporting-agent**
```python
"reporting-agent": AgentDefinition(
    description="Generate reports, analytics, dashboards",
    prompt="""You are the Reporting Agent.

You have access to these skills:
- /github-analysis - Analyze commits and generate leaderboards
- /report-generation - Create HTML reports and dashboards
- /fieldy-analysis - Analyze coaching data
- /data-aggregation - Aggregate data from multiple sources
- /email-templates - Format reports as HTML emails

You have access to these MCP tools via the reporting MCP server:
- appstore_list_apps - List App Store apps
- appstore_get_sales - Get sales reports
- appstore_get_analytics - Get app analytics
- skillz_get_events - Get Skillz event data
- firebase_read - Read from Firestore

When generating reports:
1. Use data-aggregation skill to process raw data
2. Use report-generation skill to create HTML
3. Use email-templates skill to format for email
4. Use MCP tools to fetch fresh data

Example workflow:
- User: "Generate daily App Store report"
- You:
  1. Fetch sales data via appstore_get_sales MCP tool
  2. Aggregate data using /data-aggregation skill
  3. Generate HTML using /report-generation skill
  4. Format email using /email-templates skill
  5. Return formatted report
"""
)
```

### Step 5: Testing & Validation (Week 3)

**For Each Agent**:
1. Create test script (`tests/test_{agent}_agent.py`)
2. Test integration client works
3. Test MCP tools work
4. Test skills are invoked correctly
5. Test end-to-end workflow

**Example Test: reporting-agent**
```bash
# Test App Store integration
python tests/test_reporting_agent.py --test appstore

# Test Skillz integration
python tests/test_reporting_agent.py --test skillz

# Test end-to-end report generation
python tests/test_reporting_agent.py --test report
```

---

## Migration Priority Matrix

| Agent | Integration Complexity | Skill Complexity | Priority | Est. Days |
|-------|----------------------|------------------|----------|-----------|
| reporting-agent | High (App Store, Skillz, Firebase) | Medium | P0 | 4 |
| wordpress-agent | Medium (WordPress API) | High | P0 | 3 |
| automation-agent | Medium (ClickUp, Linear) | Low | P1 | 2 |
| scheduling-agent | Medium (Google Calendar) | Low | P1 | 2 |
| supabase-agent | Low (Supabase SDK) | None | P2 | 1 |
| google-ads-agent | Medium (Google Ads API) | Low | P2 | 2 |
| workflow-agent | Low (File-based) | Medium | P2 | 2 |
| creative-agent | Low (DALL-E) | None | P3 | 1 |
| life-agent | Low (Wrapper) | Low | P3 | 1 |
| web-agent | Low (Requests) | None | P3 | 1 |
| agent-improvement-agent | Low (Internal) | Low | P3 | 1 |
| game-ideas-agent | Low (JSON DB) | Medium | P3 | 2 |
| game-prototyper-agent | Low (File gen) | High | P3 | 3 |

**Total Estimated**: 25 days (5 weeks)

---

## Implementation Checklist

### Week 1: Foundation
- [ ] Port App Store Connect client
- [ ] Port WordPress API client
- [ ] Port Google Calendar client
- [ ] Port ClickUp/Linear clients
- [ ] Create App Store MCP server
- [ ] Create WordPress MCP server

### Week 2: Skills
- [ ] Create email-templates skill
- [ ] Create data-aggregation skill
- [ ] Create wordpress-seo skill
- [ ] Create task-formatting skill
- [ ] Create calendar-scheduling skill
- [ ] Update agent prompts to reference skills

### Week 3: Testing
- [ ] Test reporting-agent end-to-end
- [ ] Test wordpress-agent end-to-end
- [ ] Test automation-agent end-to-end
- [ ] Test scheduling-agent end-to-end
- [ ] Create integration test suite

### Week 4-5: Remaining Agents
- [ ] Implement P2 agents (supabase, google-ads, workflow)
- [ ] Implement P3 agents (creative, life, web, game-related)
- [ ] Full system integration tests
- [ ] Update documentation

---

## Success Criteria

### Phase 3 Complete When:
1. ✅ All P0 agents operational (reporting, wordpress)
2. ✅ All P1 agents operational (automation, scheduling)
3. ✅ Core skills implemented and tested
4. ✅ Integration clients ported and working
5. ✅ MCP servers functional
6. ✅ End-to-end tests passing
7. ✅ Documentation updated

### Production Ready When:
1. All agents operational
2. All workflows ported from mega-agent
3. Performance meets/exceeds mega-agent
4. Error handling robust
5. Monitoring in place
6. Deployment automated

---

## Risk Mitigation

**Risk**: Breaking changes in Claude Agent SDK
**Mitigation**: Pin SDK version, test before upgrading

**Risk**: Integration API rate limits
**Mitigation**: Implement rate limiting, caching, retry logic

**Risk**: Skills not invoked correctly
**Mitigation**: Clear skill documentation, example prompts in agent definitions

**Risk**: Context file corruption
**Mitigation**: Regular backups, rotation logic, integrity checks

**Risk**: Performance degradation
**Mitigation**: Benchmark against mega-agent, optimize hot paths

---

## Next Steps

1. **Start Week 1 Implementation** (This week)
   - Port App Store Connect client
   - Port WordPress API client
   - Create corresponding MCP servers

2. **Begin Skills Development** (Parallel to Week 1)
   - Start with email-templates skill
   - Create template structure

3. **Set Up Testing Framework**
   - Create tests/ structure
   - Define test patterns

---

**Built with**: [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python)
**Target Completion**: February 2026
**Status**: Ready to begin Phase 3
