# Superpowers Skills → Agent Integration Map

**Analysis Date:** 2026-01-06

This document maps which Superpowers skills should enhance which agents in mega-agent2.

---

## Executive Summary

**Most Impactful Integrations:**

1. **Code Agent** → TDD, systematic-debugging, code review skills
2. **Agent Improvement Agent** → writing-skills, brainstorming
3. **Game Prototyper Agent** → TDD, brainstorming, writing-plans
4. **Workflow Agent** → dispatching-parallel-agents, executing-plans
5. **All Agents** → systematic-debugging, verification-before-completion

---

## Priority 1: Critical Integrations (Immediate Value)

### Code Agent
**Current**: GitHub operations, code analysis, commit reviews, PR management
**Add Skills:**
- ✅ **test-driven-development** - CRITICAL for any code written
- ✅ **systematic-debugging** - When investigating bugs
- ✅ **requesting-code-review** - Before creating PRs
- ✅ **receiving-code-review** - When processing PR feedback
- ✅ **verification-before-completion** - Ensure code actually works
- ✅ **using-git-worktrees** - For parallel development
- ✅ **finishing-a-development-branch** - PR/merge workflow

**Integration:**
```python
"code-agent": AgentDefinition(
    prompt="""You are the Code Agent.

# IMPORTANT: Skills Available

Before ANY code implementation:
- Use **test-driven-development** skill - Write tests FIRST, watch them fail, then implement
- Use **systematic-debugging** skill when bugs occur - 4-phase root cause analysis

Before creating PRs:
- Use **requesting-code-review** skill - Self-review checklist

When receiving PR feedback:
- Use **receiving-code-review** skill - Systematic response process

For feature branches:
- Use **using-git-worktrees** skill - Isolated development
- Use **finishing-a-development-branch** skill - Merge/PR decisions

# Enforcement

The test-driven-development skill states:
"NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST"

If you write code before tests, you MUST delete it and start over.

[Rest of existing prompt...]
""",
    tools=["Read", "Write", "Bash", "Grep", "Glob", "Task", "Skill"],
    model="sonnet"
)
```

**Expected Benefits:**
- Fewer bugs (tests catch issues early)
- Better code quality (TDD enforces good design)
- Faster PR reviews (self-review first)
- No regression bugs (tests prevent)

---

### Agent Improvement Agent
**Current**: System analysis and improvements
**Add Skills:**
- ✅ **writing-skills** - Perfect for creating new agent capabilities
- ✅ **brainstorming** - When designing new agents
- ✅ **writing-plans** - Breaking down agent improvements
- ✅ **systematic-debugging** - Debugging agent issues

**Integration:**
```python
"agent-improvement-agent": AgentDefinition(
    prompt="""You are the Agent Improvement Agent.

# Skills for Agent Development

When creating new agent capabilities:
1. Use **brainstorming** skill to refine requirements
2. Use **writing-plans** skill to break into implementation steps
3. Use **writing-skills** skill to create new skills following best practices
4. Use **test-driven-development** if writing code

When debugging agents:
- Use **systematic-debugging** skill for root cause analysis

# Workflow for New Agent Creation

1. **Brainstorm** (brainstorming skill):
   - Clarify vague requirements
   - Explore design alternatives
   - Get user sign-off

2. **Plan** (writing-plans skill):
   - Break into 2-5 min tasks
   - Define verification steps
   - Specify exact files

3. **Implement with TDD** (test-driven-development skill):
   - Write test, watch fail, implement, watch pass

4. **Create Skill** (writing-skills skill):
   - Follow skill best practices
   - Include testing methodology

[Rest of existing prompt...]
""",
    tools=["Read", "Write", "Bash", "Grep", "Glob", "Task", "Skill"],
    model="sonnet"
)
```

**Expected Benefits:**
- Better designed agents (brainstorming upfront)
- More maintainable skills (writing-skills best practices)
- Systematic improvements (not ad-hoc)

---

### Game Prototyper Agent
**Current**: Game prototyping
**Add Skills:**
- ✅ **test-driven-development** - When building prototypes
- ✅ **brainstorming** - Refining game concepts
- ✅ **writing-plans** - Breaking down game features
- ✅ **verification-before-completion** - Ensure prototype works

**Integration:**
```python
"game-prototyper-agent": AgentDefinition(
    prompt="""You are the Game Prototyper Agent.

# Skills for Game Development

Before prototyping:
- Use **brainstorming** skill to refine game concept
- Use **writing-plans** skill to break into features

During development:
- Use **test-driven-development** skill for game logic
- Write tests for: collision detection, scoring, game rules

Before completion:
- Use **verification-before-completion** skill
- Ensure prototype is playable and meets requirements

# TDD for Games

Example - Testing game collision:
1. Write test: "Player collides with wall → position unchanged"
2. Watch test fail
3. Implement collision detection
4. Watch test pass

[Rest of existing prompt...]
""",
    tools=["Read", "Write", "Bash", "Task", "Skill"],
    model="sonnet"
)
```

**Expected Benefits:**
- Fewer bugs in prototypes (TDD catches logic errors)
- Better designed games (brainstorming before coding)
- Working prototypes (verification ensures playability)

---

## Priority 2: High-Value Integrations

### WordPress Agent
**Current**: Content generation, SEO
**Add Skills:**
- ✅ **brainstorming** - For content strategy and SEO planning
- ✅ **writing-plans** - Breaking down content generation tasks
- ✅ **verification-before-completion** - Ensure content meets requirements

**Integration:**
```python
"wordpress-agent": AgentDefinition(
    prompt="""You are the WordPress Agent.

# Skills for Content Creation

Before generating content:
- Use **brainstorming** skill for SEO and content strategy
- Use **writing-plans** skill to break down content tasks

After generation:
- Use **verification-before-completion** skill
- Verify SEO requirements met, content published, no errors

[Rest of existing prompt...]
""",
    model="sonnet"
)
```

---

### Workflow Agent
**Current**: Automation workflows
**Add Skills:**
- ✅ **dispatching-parallel-agents** - Natural fit for workflow orchestration
- ✅ **writing-plans** - Breaking down workflows
- ✅ **executing-plans** - Batch workflow execution
- ✅ **systematic-debugging** - When workflows fail

**Integration:**
```python
"workflow-agent": AgentDefinition(
    prompt="""You are the Workflow Agent.

# Skills for Workflow Management

When creating workflows:
- Use **writing-plans** skill to break into steps
- Use **dispatching-parallel-agents** skill for concurrent execution

When executing workflows:
- Use **executing-plans** skill for batch execution with checkpoints

When workflows fail:
- Use **systematic-debugging** skill for root cause analysis

# Parallel Execution

The dispatching-parallel-agents skill enables:
- Launch multiple agents concurrently
- Two-stage review (compliance, then quality)
- Autonomous work for hours

[Rest of existing prompt...]
""",
    model="sonnet"
)
```

---

### Automation Agent
**Current**: ClickUp and Linear task management
**Add Skills:**
- ✅ **test-driven-development** - When building automations
- ✅ **systematic-debugging** - When automations fail
- ✅ **verification-before-completion** - Ensure automations work

**Integration:**
```python
"automation-agent": AgentDefinition(
    prompt="""You are the Automation Agent.

# Skills for Automation

When building automations:
- Use **test-driven-development** skill
- Write tests for automation logic before implementing

When automations fail:
- Use **systematic-debugging** skill (4-phase process)

Before marking complete:
- Use **verification-before-completion** skill
- Actually run the automation and verify it works

[Rest of existing prompt...]
""",
    model="sonnet"
)
```

---

## Priority 3: Universal Benefits (All Agents)

### Universal Skills for Error Handling

**Every agent should reference:**

1. **systematic-debugging** - When any error occurs
2. **verification-before-completion** - Before marking tasks done

**Template Addition to All Agent Prompts:**

```python
# Universal Skills (Available to ALL Agents)

When you encounter errors:
- Use **systematic-debugging** skill
  - Phase 1: Reproduce reliably
  - Phase 2: Isolate root cause
  - Phase 3: Implement fix
  - Phase 4: Verify actually fixed

Before completing tasks:
- Use **verification-before-completion** skill
- Don't just claim it works - VERIFY it works
- Run the code, check the output, confirm success

These skills prevent:
- Ad-hoc debugging (use systematic process)
- False completion claims (verify before declaring done)
```

---

## Implementation Strategy

### Phase 1: Code Agent (Week 1)
**Why First**: Highest impact, code quality foundation

1. Update code-agent prompt with TDD skills
2. Test with sample GitHub task
3. Verify TDD enforcement works
4. Add code review skills
5. Test PR workflow

**Success Metrics:**
- Code agent writes tests before implementation
- Tests fail correctly before code written
- All code has test coverage

### Phase 2: Agent Improvement Agent (Week 1)
**Why Second**: Enables self-improvement

1. Add writing-skills and brainstorming
2. Test by creating a new skill
3. Verify skill follows best practices

**Success Metrics:**
- Agent improvement agent uses brainstorming for new features
- New skills follow writing-skills guidelines

### Phase 3: Game Prototyper + WordPress (Week 2)
**Why Third**: Domain-specific improvements

1. Add TDD to game prototyper
2. Add brainstorming to wordpress agent
3. Test with sample tasks

### Phase 4: Workflow + Automation (Week 2)
**Why Fourth**: Workflow orchestration

1. Add dispatching-parallel-agents to workflow agent
2. Add TDD to automation agent
3. Test parallel execution

### Phase 5: Universal Skills (Week 3)
**Why Last**: Foundation for all agents

1. Add systematic-debugging reference to all agents
2. Add verification-before-completion to all agents
3. Test error scenarios across agents

---

## Skill Usage Patterns

### Pattern 1: TDD Enforcement (Code Agent, Game Prototyper, Automation)

```
Agent receives task → Checks if code needed → Uses test-driven-development skill

Skill enforces:
1. Write test first
2. Watch it fail
3. Write minimal code
4. Watch it pass
5. Refactor

Agent CANNOT skip steps - skill has strict enforcement
```

### Pattern 2: Brainstorming Before Building (Agent Improvement, Game Prototyper, WordPress)

```
Agent receives vague request → Uses brainstorming skill

Skill provides:
1. Socratic questioning
2. Design alternatives
3. Iterative refinement
4. User sign-off

Agent produces: Design document before implementation
```

### Pattern 3: Systematic Debugging (All Agents)

```
Agent encounters error → Uses systematic-debugging skill

Skill enforces 4-phase process:
1. Reproduce reliably
2. Isolate root cause
3. Implement fix
4. Verify actually fixed

No ad-hoc fixes allowed
```

### Pattern 4: Verification (All Agents)

```
Agent completes task → Uses verification-before-completion skill

Skill checklist:
- Actually run the code
- Check the output
- Verify requirements met
- Not just "I think it works"

Agent marks complete only after verification
```

---

## Expected System-Wide Benefits

### Quality Improvements
- **50-80% fewer bugs** (TDD catches issues early)
- **Better designed features** (brainstorming before coding)
- **No false completions** (verification enforced)

### Velocity Improvements
- **Faster debugging** (systematic process vs. ad-hoc)
- **Fewer rework cycles** (design before implement)
- **Parallel execution** (dispatching-parallel-agents)

### Maintainability Improvements
- **Test coverage** (TDD by default)
- **Better documentation** (skills document processes)
- **Consistent patterns** (skills enforce methodology)

---

## Integration Checklist

### For Each Agent:

- [ ] Identify which Superpowers skills apply
- [ ] Add skill references to agent prompt
- [ ] Add enforcement language (e.g., TDD "Iron Law")
- [ ] Add workflow examples
- [ ] Test with sample task
- [ ] Verify skill is actually used
- [ ] Document usage in agent description

### Testing:

For each integration:
1. Give agent a task that should trigger skill
2. Verify agent invokes skill (Skill tool call)
3. Verify agent follows skill guidance
4. Verify output quality improves

---

## Skills Not Assigned (Orchestrator-Level)

These skills are more appropriate for orchestrator or manual use:

- **executing-plans** - Batch execution (orchestrator)
- **subagent-driven-development** - Multi-agent orchestration (orchestrator)
- **using-superpowers** - Introduction (manual/help)

---

## Next Steps

1. **Review this mapping** with user
2. **Select priority agents** to integrate first
3. **Update agent prompts** with skill references
4. **Test each integration** with sample tasks
5. **Measure improvement** (bug rates, completion accuracy)
6. **Iterate** based on results

---

## References

- **Superpowers Skills:** `/home/ec2-user/mega-agent2/.claude/skills/`
- **Agent Definitions:** `/home/ec2-user/mega-agent2/agents.py`
- **Custom Skills:** email-formatting, github-analysis, report-generation, fieldy-analysis

---

**Recommendation:** Start with Code Agent TDD integration - it's the highest impact and will establish patterns for other integrations.
