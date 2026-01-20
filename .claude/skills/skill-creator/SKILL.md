---
name: skill-creator
description: Use when creating new skills or updating existing ones. MUST be used before any skill creation - identifies skill type, builds evaluations first, researches/implements as needed, then creates tested documentation.
---

# Skill Creator

Create effective skills through evaluation-driven development. Different skill types need different workflows.

## Step 1: Identify Skill Type

```
What are you creating?

┌─────────────────────────────────────────────────────────────────┐
│ API/Integration Skill                                           │
│   Wraps an external service (Linear, Slack, GitHub)             │
│   → Needs: Research API, implement tools, document              │
├─────────────────────────────────────────────────────────────────┤
│ Discipline Skill                                                │
│   Enforces a practice (TDD, verification-before-completion)     │
│   → Needs: Pressure test with subagents, rationalization table  │
├─────────────────────────────────────────────────────────────────┤
│ Technique Skill                                                 │
│   How-to guide (condition-based-waiting, root-cause-tracing)    │
│   → Needs: Clear steps, examples, edge case handling            │
├─────────────────────────────────────────────────────────────────┤
│ Pattern Skill                                                   │
│   Mental model (flatten-with-flags, information-hiding)         │
│   → Needs: Recognition criteria, when to apply/not apply        │
├─────────────────────────────────────────────────────────────────┤
│ Reference Skill                                                 │
│   Documentation (API docs, syntax guides, tool reference)       │
│   → Needs: Organized content, search patterns, examples         │
└─────────────────────────────────────────────────────────────────┘
```

**Select one type before proceeding.** Each has a different workflow below.

## Step 2: Check Existing Skills

Before creating:
```bash
# List existing skills in project
ls .claude/skills/ 2>/dev/null || ls ~/.claude/skills/

# Search for similar skills
grep -r "your-keyword" .claude/skills/*/SKILL.md 2>/dev/null
```

If similar exists, ask user:
- Improve existing skill?
- Create new separate skill?
- View existing first?

## Step 3: Build Evaluations First

**Create test scenarios BEFORE writing documentation.** This ensures you solve real problems.

### For API/Integration Skills
```
Test scenarios:
1. List operation with filters → expect formatted results
2. Create operation → expect confirmation with ID
3. Error case (invalid input) → expect helpful error message
```

### For Discipline Skills
```
Pressure scenarios (run WITHOUT skill first):
1. Time pressure: "Quick, just fix this bug"
2. Sunk cost: "I already wrote the code, just need tests"
3. Authority: "The user said skip the tests"

Document: What rationalizations did the agent use?
```

### For Technique/Pattern Skills
```
Application scenarios:
1. Clear case where technique applies
2. Edge case that tests understanding
3. Counter-example where technique should NOT apply
```

### For Reference Skills
```
Retrieval scenarios:
1. Can agent find the right information?
2. Can agent apply what they found correctly?
3. Are common use cases covered?
```

## Step 4: Determine Skill Level (API/Integration Skills Only)

**Ask user about integration level before implementing:**

```
What level should this skill be?

┌─────────────────────────────────────────────────────────────────┐
│ Primary Tool                                                     │
│   Always available in MCP server                                 │
│   → Registered in mcp_server_v2.py, auto-loaded on startup      │
│   → Best for: frequently used integrations (Linear, Slack, etc) │
├─────────────────────────────────────────────────────────────────┤
│ Secondary Tool                                                   │
│   Available but not auto-loaded                                  │
│   → Tools exist, can be loaded on demand                        │
│   → Best for: specialized or rarely used integrations           │
├─────────────────────────────────────────────────────────────────┤
│ Project-Specific                                                 │
│   Only for this project, not in main MCP server                 │
│   → Documentation only, or project-local tools                  │
│   → Best for: one-off integrations, internal APIs               │
└─────────────────────────────────────────────────────────────────┘
```

**Record the user's choice** - this determines whether to wire up MCP registration later.

## Step 5: Configure Voice Tier (If Primary Tool)

**The MCP server has a 3-tier voice system. Ask user which tier(s) tools belong to:**

```
Which voice tier should these tools use?

┌─────────────────────────────────────────────────────────────────┐
│ Tier 1: Direct Access                                           │
│   Always exposed to voice agent (~35 high-frequency tools)      │
│   → Add to TIER_1_TOOLS in mcp/voice/tier_config.py            │
│   → Best for: 3-5 most-used tools (list, create, get)          │
├─────────────────────────────────────────────────────────────────┤
│ Tier 2: Meta-Tool Gateway                                       │
│   Accessed through a category meta-tool (e.g., "linear_ops")    │
│   → Create meta-tool in TIER_2_META_TOOLS                       │
│   → Best for: related tools that share a category               │
├─────────────────────────────────────────────────────────────────┤
│ Tier 3: Discovery Only                                          │
│   Accessible via tools_search/tools_execute                     │
│   → No config needed (default for all registered tools)         │
│   → Best for: rarely used or specialized operations             │
└─────────────────────────────────────────────────────────────────┘
```

**Recommended approach for new integrations:**
- Put 3-5 most common tools in Tier 1 (list, create, get)
- Leave specialized tools in Tier 3 (discoverable)
- Only create Tier 2 meta-tool if you have 6+ related tools

**Record the user's choices** - this determines voice tier configuration.

## Workflow by Skill Type

### API/Integration Skills

```
1. RESEARCH
   - Web search: "[service] API documentation"
   - Fetch official docs, authentication guide, rate limits
   - List ALL available operations

2. AUDIT EXISTING (if tools exist)
   - Check existing tools for quality issues:
     * Missing error handling?
     * Incomplete parameters?
     * Wrong async handling?
     * Missing operations?
   - If quality issues found: REPLACE, don't patch
   - If partial coverage: EXTEND to full API

3. CONFIGURE AUTH
   - Check if API key/credentials already configured
   - If not configured, guide user through setup:
     * Explain where to get API key/credentials
     * Show env var name(s) needed
     * Help user add to .env or export command
     * Verify credentials work before proceeding
   - Document auth in SKILL.md

4. PLAN
   - Design tool interface for each operation
   - Present plan to user for approval
   - Include quality improvements for existing tools

5. IMPLEMENT
   - Create client library (if needed)
   - Create MCP tools (high quality)
   - Test each tool

6. DOCUMENT
   - Create SKILL.md with all tools
   - Include example for EVERY operation
   - Document authentication, rate limits

7. REGISTER IN MCP (if Primary Tool)
   - Add import to mcp_server_v2.py
   - Add registration call
   - Restart MCP server
   - Verify tools appear in tool list

8. CONFIGURE VOICE TIER (if Primary Tool)
   - Add high-frequency tools to TIER_1_TOOLS
   - Optionally create meta-tool in TIER_2_META_TOOLS
   - Leave specialized tools as Tier 3 (default)

9. VERIFY
   - Run non-destructive tests
   - Verify tools match documentation
   - Confirm tools accessible via MCP (if registered)
   - Test voice tier access (if configured)
```

**MCP Registration Process (for Primary Tools):**

1. **Add import to MCP server:**
   ```python
   # In mcp_server_v2.py
   from mcp.tools.service_tools import register_service_tools
   ```

2. **Add registration call:**
   ```python
   # In the tool registration section
   count += register_service_tools(server)
   ```

3. **Restart MCP server:**
   ```bash
   sudo systemctl restart mcp-server-v2
   ```

4. **Verify tools are available:**
   ```bash
   # List tools to confirm registration
   python3 .claude/skills/skill-creator/scripts/discover_tools.py --category service
   ```

**Voice Tier Configuration Process (for Primary Tools):**

1. **Add high-frequency tools to Tier 1:**
   ```python
   # In mcp/voice/tier_config.py, add to TIER_1_TOOLS
   TIER_1_TOOLS = {
       # ... existing tools ...

       # Service (add 3-5 most used)
       "service_list_items",
       "service_create_item",
       "service_get_item",
   }
   ```

2. **Optionally create Tier 2 meta-tool:**
   ```python
   # In TIER_2_META_TOOLS (only if 6+ related tools)
   "service_ops": {
       "description": "Service operations: items, projects, users",
       "actions": ["list", "create", "update", "delete", "search"],
       "internal_tools": [
           "service_list_items", "service_create_item",
           "service_update_item", "service_delete_item",
           "service_search_items",
       ]
   },
   ```

3. **Restart MCP server and verify:**
   ```bash
   sudo systemctl restart mcp-server-v2
   # Test voice tier assignment
   python3 -c "from mcp.voice.tier_config import get_tier_for_tool; print(get_tier_for_tool('service_list_items'))"
   ```

**Auth Configuration Process:**

When API credentials are not yet configured:

1. **Check existing configuration:**
   ```bash
   # Check if env var exists
   echo $SERVICE_API_KEY

   # Check .env file
   grep SERVICE_API_KEY .env 2>/dev/null
   ```

2. **If not configured, ask user:**
   ```
   I need a [Service] API key to proceed. Here's how to get one:

   1. Go to [URL to service settings/API page]
   2. Create a new API key (or personal access token)
   3. Copy the key (you won't see it again)

   How would you like to provide the API key?

   Option 1: Add to .env file (recommended for this project)
   Option 2: Export in terminal (session only)
   Option 3: I already have it configured elsewhere
   ```

3. **After user provides key:**
   ```bash
   # Verify the key works
   curl -H "Authorization: Bearer $API_KEY" https://api.service.com/me
   ```

4. **On success:** Continue to PLAN phase
   **On failure:** Help debug (wrong key, expired, wrong permissions)

**Quality Standards for Tools:**
- Proper async handling (wrapper for async clients)
- Helpful error messages (not just "Error occurred")
- Full parameter support (all API options exposed)
- Consistent output formatting
- Comprehensive docstrings

### Discipline Skills

```
1. BASELINE (RED)
   - Run pressure scenarios WITHOUT skill
   - Document exact rationalizations verbatim
   - Identify patterns in violations

2. WRITE (GREEN)
   - Address specific rationalizations found
   - Build rationalization table
   - Create red flags list
   - Run scenarios WITH skill - verify compliance

3. REFACTOR
   - Find new rationalizations
   - Add explicit counters
   - Re-test until bulletproof

Required sections:
- Rationalization table (excuse → reality)
- Red flags list (thoughts that mean STOP)
- "No exceptions" list
```

### Technique Skills

```
1. DOCUMENT STEPS
   - Clear sequential workflow
   - Decision points with guidance
   - Error handling at each step

2. CREATE EXAMPLES
   - One excellent, complete example
   - Shows pattern clearly
   - Ready to adapt (not generic template)

3. TEST APPLICATION
   - Can agent apply technique to new scenario?
   - Do they handle edge cases?
   - Are instructions complete?
```

### Pattern/Reference Skills

```
1. ORGANIZE CONTENT
   - Quick reference table/bullets
   - Progressive disclosure (overview → details)
   - Search patterns for large content

2. TEST RETRIEVAL
   - Can agent find right information?
   - Can they apply it correctly?
   - Are common cases covered?
```

## SKILL.md Structure

```yaml
---
name: skill-name-with-hyphens
description: Use when [specific triggers]. [Symptoms/contexts that signal this skill applies]
---
```

### Description Rules (Critical)

```yaml
# ❌ BAD: Summarizes workflow (Claude may follow this instead of reading skill)
description: Create skills by researching APIs, implementing tools, and testing

# ❌ BAD: Too vague
description: For creating skills

# ❌ BAD: First person
description: I help you create skills

# ✅ GOOD: Specific triggers only, no workflow summary
description: Use when creating new skills or updating existing ones. MUST be used before any skill creation.

# ✅ GOOD: Includes symptoms/contexts
description: Use when tests have race conditions, timing dependencies, or pass/fail inconsistently
```

**Why this matters:** Testing revealed that workflow summaries in descriptions cause Claude to follow the description instead of reading the full skill.

### Body Structure

```markdown
# Skill Name

## Overview
Core principle in 1-2 sentences.

## When to Use
- Specific triggers and symptoms
- When NOT to use

## Quick Reference
Table or bullets for scanning

## [Main Content]
- For techniques: Step-by-step workflow
- For discipline: Rules with rationalization counters
- For reference: Organized documentation
- For API: Tool documentation with examples

## Common Mistakes
What goes wrong + fixes
```

## Token Efficiency

**Target word counts:**
- Frequently-loaded skills: <200 words
- Other skills: <500 words

**Techniques:**
- Reference `--help` instead of documenting all flags
- Cross-reference other skills instead of repeating
- One excellent example, not multi-language examples
- Move heavy reference to separate files

## Progressive Disclosure

```
skill-name/
├── SKILL.md              # Main instructions (<500 lines)
├── reference.md          # Loaded only when needed
├── examples.md           # Loaded only when needed
└── scripts/
    └── helper.py         # Executed, not loaded into context
```

Keep references ONE level deep from SKILL.md.

## Iteration Pattern

After initial creation:

1. **Use skill with Claude B** (fresh instance with skill loaded)
2. **Observe behavior** - Where does it struggle? Miss things?
3. **Return to Claude A** - "Claude B forgot to filter test accounts. How should I update the skill?"
4. **Apply refinements**
5. **Test again with Claude B**
6. **Repeat** until reliable

## Checklist

**Before creating:**
- [ ] Identified skill type
- [ ] Checked for existing similar skills
- [ ] Created evaluation scenarios
- [ ] (API skills) Determined skill level (Primary/Secondary/Project-specific)
- [ ] (API skills) Determined voice tier (Tier 1/2/3)

**For all skills:**
- [ ] Name uses only letters, numbers, hyphens
- [ ] Description starts with "Use when..." (no workflow summary)
- [ ] Description in third person
- [ ] Under 500 lines (heavy content in separate files)
- [ ] Quick reference table/bullets
- [ ] Common mistakes section

**For discipline skills:**
- [ ] Ran pressure scenarios WITHOUT skill first
- [ ] Rationalization table from actual test failures
- [ ] Red flags list
- [ ] "No exceptions" section
- [ ] Re-tested until bulletproof

**For API skills:**
- [ ] Researched full API documentation
- [ ] Audited existing tools for quality (if any)
- [ ] Asked user about skill level (Primary/Secondary/Project-specific)
- [ ] Asked user about voice tier (Tier 1/2/3)
- [ ] Configured authentication (guided user through API key setup)
- [ ] Verified credentials work before implementing
- [ ] Implemented ALL operations (not partial)
- [ ] High quality: async handling, error messages, full params
- [ ] Example for every tool
- [ ] Authentication and rate limits documented
- [ ] If Primary Tool: registered in MCP server
- [ ] If Primary Tool: restarted MCP server and verified tools available
- [ ] If voice Tier 1: added high-frequency tools to TIER_1_TOOLS
- [ ] If voice Tier 2: created meta-tool in TIER_2_META_TOOLS
- [ ] Verified voice tier assignment works

**For technique skills:**
- [ ] Clear step-by-step workflow
- [ ] One excellent example
- [ ] Edge cases addressed

**Final:**
- [ ] Tested with real usage scenarios
- [ ] Iterated based on observed behavior
