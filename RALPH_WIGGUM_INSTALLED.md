# Ralph Wiggum Installed ✅

**Date:** 2026-01-06
**Source:** https://github.com/anthropics/claude-plugins-official/tree/main/plugins/ralph-wiggum
**Status:** Fully installed and configured

---

## What is Ralph Wiggum?

Ralph Wiggum is a Claude Code plugin that implements **continuous self-referential AI development loops**. It allows Claude to iteratively work on tasks by feeding the same prompt back repeatedly until completion.

### Core Concept

Named after Ralph Wiggum from The Simpsons, this plugin embodies persistent iteration despite setbacks. It uses a **Stop hook** that intercepts Claude's exit attempts and feeds the same prompt back, creating a self-referential feedback loop.

**How it works:**
1. You run `/ralph-loop "Your task"` ONCE
2. Claude works on the task
3. Claude tries to exit
4. Stop hook blocks exit and feeds the SAME prompt back
5. Claude sees modified files and continues iterating
6. Repeat until completion or max iterations

---

## Installation Location

```
/home/ec2-user/mega-agent2/.claude/
├── commands/
│   ├── cancel-ralph.md         # /cancel-ralph command
│   ├── help.md                 # Ralph help documentation
│   └── ralph-loop.md           # /ralph-loop command
├── hooks/
│   ├── hooks.json              # Stop hook configuration
│   └── stop-hook.sh            # Core loop logic (executable)
└── scripts/
    └── setup-ralph-loop.sh     # Loop initialization (executable)
```

---

## Available Commands

### /ralph-loop

Start a Ralph loop in your current session.

**Usage:**
```bash
/ralph-loop "Build a REST API for todos with CRUD operations, input validation, and tests. Output <promise>COMPLETE</promise> when done." --max-iterations 50 --completion-promise "COMPLETE"
```

**Options:**
- `--max-iterations <n>` - Stop after N iterations (default: unlimited)
- `--completion-promise <text>` - Phrase that signals completion (exact match)

### /cancel-ralph

Cancel the active Ralph loop.

**Usage:**
```bash
/cancel-ralph
```

---

## How The Stop Hook Works

The `stop-hook.sh` script:
1. Checks for active loop state (`.claude/ralph-loop.local.md`)
2. Parses iteration count and max iterations
3. Checks if max iterations reached
4. Reads Claude's last output from transcript
5. Checks for completion promise (if set)
6. If not complete: blocks exit, increments iteration, feeds prompt back
7. If complete: allows exit and cleans up state file

**State File Format:**
```markdown
---
iteration: 5
max_iterations: 50
completion_promise: "COMPLETE"
---

Your original prompt goes here...
```

---

## Best Practices

### 1. Always Set Max Iterations

```bash
# GOOD: Safety net prevents infinite loops
/ralph-loop "Implement feature X" --max-iterations 20

# RISKY: Could run forever if task impossible
/ralph-loop "Implement feature X"
```

### 2. Clear Completion Criteria

❌ **Bad:** "Build a todo API and make it good."

✅ **Good:**
```markdown
Build a REST API for todos.

When complete:
- All CRUD endpoints working
- Input validation in place
- Tests passing (coverage > 80%)
- README with API docs
- Output: <promise>COMPLETE</promise>
```

### 3. Use Test-Driven Iteration

```markdown
Implement feature X following TDD:
1. Write failing tests
2. Implement feature
3. Run tests
4. If any fail, debug and fix
5. Refactor if needed
6. Repeat until all green
7. Output: <promise>COMPLETE</promise>
```

### 4. Include Escape Instructions

```markdown
Try to implement feature X.

After 15 iterations, if not complete:
- Document what's blocking progress
- List what was attempted
- Suggest alternative approaches
- Output: <promise>BLOCKED</promise>
```

---

## When to Use Ralph

**Good for:**
- Well-defined tasks with clear success criteria
- Tasks requiring iteration and refinement (e.g., getting tests to pass)
- Greenfield projects where you can walk away
- Tasks with automatic verification (tests, linters)

**Not good for:**
- Tasks requiring human judgment or design decisions
- One-shot operations
- Tasks with unclear success criteria
- Production debugging (use targeted debugging instead)

---

## Philosophy

Ralph embodies several key principles:

### 1. Iteration > Perfection
Don't aim for perfect on first try. Let the loop refine the work.

### 2. Failures Are Data
"Deterministically bad" means failures are predictable and informative. Use them to tune prompts.

### 3. Operator Skill Matters
Success depends on writing good prompts, not just having a good model.

### 4. Persistence Wins
Keep trying until success. The loop handles retry logic automatically.

---

## Example Usage

### Basic Loop
```bash
/ralph-loop "Create a Python function that validates email addresses. Include tests. Output <promise>DONE</promise> when tests pass." --max-iterations 10 --completion-promise "DONE"
```

### TDD Loop
```bash
/ralph-loop "Implement user authentication using TDD. Write tests first, then implementation. All tests must pass. Output <promise>COMPLETE</promise> when done." --max-iterations 30 --completion-promise "COMPLETE"
```

### Fix Failing Tests
```bash
/ralph-loop "Fix all failing tests in the test suite. Run tests each iteration. Output <promise>ALL GREEN</promise> when all tests pass." --max-iterations 15 --completion-promise "ALL GREEN"
```

### Cancel Active Loop
```bash
/cancel-ralph
```

---

## Integration with Superpowers

Ralph Wiggum works beautifully with Superpowers skills:

```bash
# Combine Ralph loop with TDD skill
/ralph-loop "Implement new feature following test-driven-development skill. Use RED-GREEN-REFACTOR cycle. Output <promise>FEATURE COMPLETE</promise> when all tests pass." --max-iterations 25 --completion-promise "FEATURE COMPLETE"
```

The `test-driven-development` skill will guide each iteration to follow proper TDD practices, while Ralph ensures the loop continues until all tests pass.

---

## Technical Details

### State Persistence
- Loop state stored in `.claude/ralph-loop.local.md`
- Markdown file with YAML frontmatter
- Automatically cleaned up on completion or cancellation

### Hook Integration
- Stop hook registered in `.claude/hooks/hooks.json`
- Executes on every Claude exit attempt
- Uses advanced Stop hook API (receives transcript path)
- Returns JSON with decision: "block" (continue) or allows exit

### Transcript Parsing
- Reads JSONL transcript from Claude Code
- Extracts last assistant message
- Parses completion promise from `<promise>` tags
- Uses exact string matching (not regex)

---

## Real-World Results

According to the plugin documentation:
- Successfully generated 6 repositories overnight in Y Combinator hackathon testing
- One $50k contract completed for $297 in API costs
- Created entire programming language ("cursed") over 3 months using this approach

---

## Learn More

- **Original technique:** https://ghuntley.com/ralph/
- **Ralph Orchestrator:** https://github.com/mikeyobrien/ralph-orchestrator
- **Plugin source:** https://github.com/anthropics/claude-plugins-official/tree/main/plugins/ralph-wiggum

---

## Integration with mega-agent2

Ralph Wiggum is now available in mega-agent2 and works alongside:
- **Superpowers skills** (18 development workflow skills)
- **Claude Agent SDK** (SDK-native architecture)
- **Custom agents** (16 domain-specific agents)

You can use Ralph loops to have agents iteratively work on tasks until completion, with automatic retry and refinement.

---

## License

MIT License (inherited from claude-plugins-official)

---

## Credits

**Ralph Wiggum Plugin** created by Anthropic
**Ralph Technique** by Geoffrey Huntley (@ghuntley)
**Installed in:** mega-agent2 (2026-01-06)

---

Built with [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python)
Enhanced with [Superpowers](https://github.com/obra/superpowers)
Powered by [Ralph Wiggum](https://github.com/anthropics/claude-plugins-official)
