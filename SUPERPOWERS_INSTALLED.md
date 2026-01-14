# Superpowers Installed ✅

**Date:** 2026-01-06
**Source:** https://github.com/obra/superpowers
**Status:** 14 Superpowers skills installed and available

---

## What is Superpowers?

Superpowers is a comprehensive development workflow system built on composable skills. It provides:

- **Structured workflows** - From brainstorming to completion
- **Test-Driven Development** - RED-GREEN-REFACTOR enforcement
- **Subagent workflows** - Parallel agent execution patterns
- **Code review processes** - Pre and post-review workflows
- **Git worktree management** - Isolated development branches
- **Systematic debugging** - 4-phase root cause analysis

## Skills Installed

### Development Workflow (Core)

1. **brainstorming** - Interactive design refinement through Socratic questioning
2. **writing-plans** - Create detailed implementation plans (2-5 min tasks)
3. **executing-plans** - Batch execution with human checkpoints
4. **subagent-driven-development** - Fast iteration with two-stage review

### Testing & Quality

5. **test-driven-development** - RED-GREEN-REFACTOR cycle with anti-patterns
6. **requesting-code-review** - Pre-review checklist and self-assessment
7. **receiving-code-review** - Responding to feedback systematically
8. **verification-before-completion** - Ensure fixes actually work

### Debugging

9. **systematic-debugging** - 4-phase root cause process
   - Root-cause tracing techniques
   - Defense-in-depth strategies
   - Condition-based waiting patterns

### Git & Branch Management

10. **using-git-worktrees** - Parallel development branches
11. **finishing-a-development-branch** - Merge/PR decision workflow

### Meta Skills

12. **dispatching-parallel-agents** - Concurrent subagent workflows
13. **using-superpowers** - Introduction to the skills system
14. **writing-skills** - Create new skills following best practices

---

## Our Custom Skills (Still Available)

15. **email-formatting** - Neo-brutal email templates
16. **github-analysis** - Commit analysis and leaderboards
17. **report-generation** - HTML reports with charts
18. **fieldy-analysis** - Coaching data processing

---

## Total Skills Available: 18

All skills are available to agents via the Skill tool:

```
Agent: Skill("test-driven-development")
SDK: Returns comprehensive TDD guide

Agent: Skill("brainstorming")
SDK: Returns design refinement workflow

Agent: Skill("github-analysis")
SDK: Returns commit analysis documentation
```

---

## How Agents Use Superpowers

### Automatic Activation

Superpowers skills are designed to activate automatically when agents encounter relevant situations:

- **Before writing code** → test-driven-development activates
- **When bugs occur** → systematic-debugging activates
- **When design needed** → brainstorming activates
- **When plan needed** → writing-plans activates

### Integration with mega-agent2

Our agents can now:

1. **Code Agent** - Use TDD, code review, git worktrees for development tasks
2. **Agent Improvement Agent** - Use writing-skills to create new capabilities
3. **All Agents** - Use systematic-debugging when encountering errors

### Example Workflow

```
User: "Add user authentication feature"
  ↓
Orchestrator → Code Agent
  ↓
Code Agent: Skill("brainstorming")
  → Asks clarifying questions
  → Presents design options
  → Gets user approval
  ↓
Code Agent: Skill("writing-plans")
  → Breaks into 2-5 min tasks
  → Defines verification steps
  ↓
Code Agent: Skill("test-driven-development")
  → Writes failing test
  → Writes minimal code
  → Verifies passes
  ↓
Code Agent: Skill("requesting-code-review")
  → Self-reviews against plan
  → Reports issues
  ↓
Communication Agent: Sends completion notification
```

---

## Superpowers Philosophy

- **Test-Driven Development** - Write tests first, always
- **Systematic over ad-hoc** - Process over guessing
- **Complexity reduction** - Simplicity as primary goal
- **Evidence over claims** - Verify before declaring success

---

## Integration Notes

### Compatible with Our Architecture ✅

- **Works with** - Claude Agent SDK
- **Works with** - Our AgentDefinition pattern
- **Works with** - Task tool delegation
- **Works with** - File-based state

### No Conflicts

- Superpowers skills don't conflict with our custom skills
- They complement our reporting/analysis skills
- They add development workflow capabilities we didn't have

### Usage Pattern

Skills are discovered progressively:
1. Agent encounters situation (e.g., needs to write code)
2. Agent uses Skill tool to invoke relevant skill
3. SDK returns skill documentation
4. Agent follows skill guidance

---

## Key Superpowers Features

### 1. Test-Driven Development (TDD)

**The Iron Law:** NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST

**RED-GREEN-REFACTOR:**
```
RED    → Write failing test, watch it fail
GREEN  → Write minimal code to pass
REFACTOR → Clean up while staying green
```

### 2. Brainstorming Workflow

- Socratic questioning to refine vague ideas
- Present design in digestible chunks
- Get user sign-off before implementation
- Save design documents

### 3. Implementation Planning

- Break work into 2-5 minute tasks
- Each task has exact file paths and complete code
- Verification steps for each task
- Clear enough for "junior engineer with poor taste"

### 4. Subagent-Driven Development

- Dispatch fresh subagent per task
- Two-stage review: spec compliance, then code quality
- Autonomous work for hours at a time
- Stays on track with approved plans

### 5. Systematic Debugging

**4-Phase Process:**
1. Reproduce reliably
2. Isolate root cause
3. Implement fix
4. Verify actually fixed

**Techniques:**
- Root-cause tracing
- Defense-in-depth
- Condition-based waiting

### 6. Git Worktrees

- Isolated workspace on new branch
- Run project setup
- Verify clean test baseline
- Parallel development without conflicts

---

## Next Steps

### Immediate Benefits

1. **Code Agent** can now use TDD for all development
2. **All agents** can use systematic-debugging for errors
3. **Agent Improvement Agent** can use writing-skills for new capabilities

### Suggested Usage

1. **Enable TDD** in Code Agent workflows
2. **Use brainstorming** for complex feature requests
3. **Use writing-plans** for multi-step tasks
4. **Use systematic-debugging** when agents encounter errors

### Testing Superpowers

Try asking:
- "Create a new feature using TDD"
- "Help me brainstorm a solution for X"
- "Create an implementation plan for Y"
- "Debug this issue systematically"

---

## Documentation

- **README:** `/tmp/superpowers/README.md`
- **Skills:** `/home/ec2-user/mega-agent2/.claude/skills/`
- **Blog Post:** https://blog.fsck.com/2025/10/09/superpowers/
- **Repository:** https://github.com/obra/superpowers

---

## License

MIT License (inherited from Superpowers)

---

## Credits

**Superpowers** created by Jesse Vincent (@obra)
**Installed in:** mega-agent2 (2026-01-06)

---

Built with [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python)
Enhanced with [Superpowers](https://github.com/obra/superpowers)
