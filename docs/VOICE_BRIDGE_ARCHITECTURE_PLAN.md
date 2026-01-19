# Voice Bridge Architecture Plan

## Executive Summary

Transform voice_bridge from a simple passthrough into an intelligent conversation orchestrator that maintains context, understands available capabilities, and provides Claude with the full picture needed to give excellent responses.

---

## Current State Analysis

### What We Have
```
Browser ←→ Gateway ←→ Voice Bridge ←→ Grok (STT/TTS)
                          ↓
                    Claude Agent SDK (stateless query())
```

### Current Limitations
1. **No conversation memory** - Each Claude query is isolated
2. **No skills awareness** - Claude doesn't know what capabilities exist
3. **No user context** - No awareness of preferences, timezone, etc.
4. **No session persistence** - Everything lost on disconnect
5. **Basic error handling** - No graceful degradation

---

## Proposed Architecture

### High-Level Design
```
┌─────────────────────────────────────────────────────────────────┐
│                      VOICE BRIDGE (Orchestrator)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │ ConversationMgr  │  │  SkillsRegistry  │  │ UserContext   │ │
│  │                  │  │                  │  │               │ │
│  │ • Message history│  │ • Skill discovery│  │ • Preferences │ │
│  │ • Token tracking │  │ • Capability map │  │ • Timezone    │ │
│  │ • Summarization  │  │ • Trigger words  │  │ • Session     │ │
│  └────────┬─────────┘  └────────┬─────────┘  └───────┬───────┘ │
│           │                     │                     │         │
│           └─────────────────────┼─────────────────────┘         │
│                                 ▼                               │
│                    ┌──────────────────────┐                     │
│                    │    ContextBuilder    │                     │
│                    │                      │                     │
│                    │  Assembles complete  │                     │
│                    │  context for Claude  │                     │
│                    └──────────┬───────────┘                     │
│                               ▼                                 │
│                    ┌──────────────────────┐                     │
│                    │    QueryExecutor     │                     │
│                    │                      │                     │
│                    │  Runs Claude with    │                     │
│                    │  full context        │                     │
│                    └──────────────────────┘                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. ConversationManager

**Purpose**: Maintain conversation state across turns

**Responsibilities**:
- Store message history (user + assistant)
- Track token usage per message
- Manage context window (truncate/summarize when needed)
- Provide conversation summary for long sessions

**Data Structure**:
```
Message {
    role: "user" | "assistant"
    content: string
    timestamp: datetime
    token_count: int
    metadata: {
        source: "voice" | "text"
        latency_ms: int
        skill_invoked: string | null
    }
}

Conversation {
    id: string
    messages: [Message]
    total_tokens: int
    summary: string | null  // compressed old context
    created_at: datetime
    last_activity: datetime
}
```

**Context Window Strategy**:
```
┌─────────────────────────────────────────────────┐
│  CONTEXT BUDGET: ~8000 tokens                   │
├─────────────────────────────────────────────────┤
│  System context (skills, user prefs): ~2000    │
│  Conversation summary (if needed):    ~1000    │
│  Recent messages (last N turns):      ~4000    │
│  Current query:                       ~1000    │
└─────────────────────────────────────────────────┘

When total_tokens > threshold:
  1. Summarize oldest 50% of messages
  2. Replace with summary
  3. Keep recent messages verbatim
```

---

### 2. SkillsRegistry

**Purpose**: Discover and catalog available capabilities

**Responsibilities**:
- Scan .claude/skills/ directory
- Parse SKILL.md frontmatter (name, description)
- Build capability map for Claude
- Identify trigger phrases for each skill

**Discovery Process**:
```
1. Glob: .claude/skills/*/SKILL.md
2. For each file:
   - Parse YAML frontmatter
   - Extract name, description
   - Identify keywords/triggers from description
3. Build registry:
   {
     "aws-serverless-eda": {
       "name": "aws-serverless-eda",
       "description": "AWS serverless and event-driven...",
       "triggers": ["serverless", "lambda", "api gateway", "dynamodb"],
       "category": "aws"
     },
     ...
   }
```

**Skills Categories** (auto-detected or configured):
- **AWS**: aws-serverless-eda, aws-cdk-development, aws-cost-operations, aws-agentic-ai
- **Development**: test-driven-development, systematic-debugging, code-review, git-worktrees
- **Automation**: email-templates, report-generation, task-formatting, calendar-scheduling
- **Analysis**: github-analysis, fieldy-analysis, data-aggregation
- **Planning**: brainstorming, writing-plans, executing-plans

---

### 3. UserContext

**Purpose**: Maintain user-specific information

**Data**:
```
UserContext {
    // From CLAUDE.md
    timezone: "America/Los_Angeles"  // Pacific Time
    location: "Parksville, BC, Canada"

    // Contacts
    contacts: {
        "allen": "allen@alistsearch.com",
        "jess_work": "jess@ehnow.ca",
        "jess_personal": "jessglow@gmail.com"
    }

    // Projects
    projects: {
        "EH!": "Social media app (pronounced like letter A)",
        "TrailMix": "Trail Mix Technologies",
        "Fieldy": "Field Labs coaching app"
    }

    // Session
    session_start: datetime
    interaction_count: int
}
```

---

### 4. ContextBuilder

**Purpose**: Assemble complete context for each Claude query

**Output Structure**:
```
SYSTEM CONTEXT:
═══════════════════════════════════════════════════════════

CURRENT TIME: Tuesday, January 14, 2026 at 5:15 AM Pacific Time

USER CONTEXT:
- Location: Parksville, BC, Canada
- Known contacts: Allen (allen@alistsearch.com), Jess
- Active projects: EH! (social app), TrailMix, Fieldy

AVAILABLE CAPABILITIES:
You have access to these specialized skills:

AWS & Cloud:
  • aws-serverless-eda: Lambda, API Gateway, DynamoDB, Step Functions
  • aws-cdk-development: Infrastructure as code with CDK
  • aws-cost-operations: Cost optimization and monitoring

Development:
  • systematic-debugging: Root cause analysis, test isolation
  • test-driven-development: TDD patterns and practices
  • github-analysis: Commit analysis, PR reviews, leaderboards

Automation:
  • email-templates: HTML email formatting
  • calendar-scheduling: Event management, conflict detection
  • report-generation: Dashboards and data visualization

[...more categories...]

To use a skill, simply address the relevant topic - the appropriate
expertise will be applied automatically.

CONVERSATION HISTORY:
═══════════════════════════════════════════════════════════

[If long conversation, show summary first]
Summary of earlier discussion: User asked about deploying a
Lambda function and we discussed the architecture...

[Recent messages verbatim]
User: How do I set up the API Gateway?
Assistant: For API Gateway with Lambda, you'll want to...

User: What about authentication?
Assistant: There are several approaches...

CURRENT QUERY:
═══════════════════════════════════════════════════════════

User: Can you add JWT validation to that?
```

---

### 5. QueryExecutor

**Purpose**: Execute Claude queries with full context

**Responsibilities**:
- Build complete prompt from ContextBuilder
- Execute query via Agent SDK
- Handle streaming responses
- Manage timeouts and errors
- Update conversation history with response

**Error Handling**:
```
Timeout (>60s):
  → Return partial response if available
  → "I'm still thinking about this. Let me give you what I have so far..."

Rate limit:
  → Exponential backoff
  → "Give me a moment, I'm a bit busy..."

Connection error:
  → Retry with circuit breaker
  → "I lost my train of thought. Could you repeat that?"
```

---

## Innovation Opportunities

### 1. Proactive Skill Suggestion

When Claude detects a topic that matches a skill:
```
User: "I need to figure out why my tests are failing"

Claude: "I can help debug that. I have systematic debugging
capabilities that include test isolation and root cause analysis.
Would you like me to walk through a structured debugging process?"
```

### 2. Conversation Summarization

For long sessions, periodically compress old context:
```python
def summarize_old_messages(messages, token_limit):
    """
    Compress messages older than N turns into a summary.

    Input: 20 messages totaling 5000 tokens
    Output: 500-token summary + 5 recent messages
    """
    # Use Claude to summarize
    summary_prompt = f"""
    Summarize this conversation concisely, preserving:
    - Key decisions made
    - Important facts mentioned
    - Current task/goal
    - Any pending questions

    Conversation:
    {format_messages(old_messages)}
    """
    return claude_summarize(summary_prompt)
```

### 3. Intent Classification

Pre-classify queries before full processing:
```
Quick question → Short, direct response
Complex task   → Detailed, structured response
Clarification  → Ask follow-up before proceeding
Skill-specific → Route to appropriate expertise
```

### 4. Multi-Turn Task Tracking

Track ongoing tasks across conversation:
```
User: "Let's deploy a Lambda function"
[Task started: Lambda deployment]

User: "Use Python"
[Task updated: Lambda + Python]

User: "Actually, let's do TypeScript"
[Task updated: Lambda + TypeScript]

User: "What were we doing again?"
Assistant: "We're setting up a TypeScript Lambda function.
We haven't yet discussed the trigger or permissions..."
```

### 5. Session Persistence

Save/restore sessions for continuity:
```
Session saved: voice_session_2026-01-14_051500.json
- 15 messages
- Last topic: AWS deployment
- Open tasks: Lambda configuration

[Next day]
"Welcome back! Last time we were working on your Lambda
deployment. Want to continue where we left off?"
```

### 6. Voice-Optimized Responses

Detect when response needs voice optimization:
```python
def optimize_for_voice(response):
    """
    Adapt response for spoken delivery.

    - Shorten code examples
    - Add verbal signposts ("First...", "Next...")
    - Simplify complex explanations
    - Offer to send details to screen
    """
    if contains_code(response) and len(code) > 10_lines:
        return f"""
        {spoken_summary}

        I've prepared a code example - would you like me
        to show it on screen, or should I walk through
        the key parts verbally?
        """
```

---

## Data Flow

### Complete Request Flow
```
1. User speaks
   ↓
2. Grok transcribes → "How do I deploy to Lambda?"
   ↓
3. ConversationManager.add_user_message(transcript)
   ↓
4. ContextBuilder.build_context()
   ├── Get user context (timezone, preferences)
   ├── Get skills registry (capabilities)
   ├── Get conversation history
   └── Assemble full prompt
   ↓
5. QueryExecutor.execute(full_context)
   ├── Call Claude Agent SDK
   ├── Stream response
   └── Handle errors
   ↓
6. ConversationManager.add_assistant_message(response)
   ↓
7. Grok.add_assistant_context(response)  // For voice continuity
   ↓
8. Send to browser (text + audio)
```

---

## Configuration

```yaml
# voice_bridge_config.yaml

conversation:
  max_tokens: 8000
  summarize_threshold: 6000
  keep_recent_messages: 10
  summary_max_tokens: 1000

skills:
  discovery_path: ".claude/skills"
  refresh_interval: 300  # seconds

context:
  include_time: true
  include_location: true
  include_contacts: true
  include_skills: true

query:
  timeout_seconds: 60
  max_retries: 3
  streaming: true

voice:
  optimize_responses: true
  max_spoken_code_lines: 5
```

---

## Implementation Phases

### Phase 1: Core Memory (Foundation)
- [ ] Create ConversationManager class
- [ ] Implement message history storage
- [ ] Pass history to Claude queries
- [ ] Basic token tracking

**Deliverable**: Claude remembers previous turns

### Phase 2: Skills Awareness
- [ ] Create SkillsRegistry class
- [ ] Implement skill discovery from .claude/skills/
- [ ] Parse SKILL.md frontmatter
- [ ] Include skills context in prompts

**Deliverable**: Claude knows what capabilities exist

### Phase 3: Rich Context
- [ ] Create ContextBuilder class
- [ ] Include user preferences from CLAUDE.md
- [ ] Add current time/date
- [ ] Implement context assembly

**Deliverable**: Claude has full situational awareness

### Phase 4: Context Management
- [ ] Implement token counting
- [ ] Add conversation summarization
- [ ] Context window management
- [ ] Graceful truncation

**Deliverable**: Long conversations work smoothly

### Phase 5: Advanced Features
- [ ] Voice-optimized responses
- [ ] Session persistence
- [ ] Proactive skill suggestions
- [ ] Intent classification

**Deliverable**: Polished, intelligent assistant

---

## Success Metrics

1. **Context Retention**: Claude correctly references information from 5+ turns ago
2. **Skill Utilization**: Appropriate skills invoked based on conversation topic
3. **Response Quality**: Responses incorporate user preferences (timezone, contacts)
4. **Session Length**: Support 30+ minute conversations without degradation
5. **Error Recovery**: Graceful handling of timeouts/errors without losing context

---

## Open Questions

1. **Persistence**: Should sessions persist across browser refreshes? Across days?
2. **Multi-user**: Should voice_bridge support multiple concurrent users with separate contexts?
3. **Skill invocation**: Should skills be explicitly invoked or automatically applied?
4. **Token budget**: How to balance context richness vs response latency?
5. **Privacy**: Should conversation history be stored? For how long?

---

## Next Steps

1. Review and approve this plan
2. Clarify open questions
3. Begin Phase 1 implementation
4. Iterate based on testing feedback
