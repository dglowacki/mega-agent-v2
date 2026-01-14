# Mega-Agent2 Capabilities

## System Overview

**Mega-Agent2** is a multi-agent orchestrator system built with the [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python) that coordinates 16 specialized AI agents to automate operations for mobile gaming development and business management.

**Architecture**: Event-driven, async/await, SDK-based multi-agent orchestration
**Platform**: AWS EC2 (Amazon Linux 2023)
**Location**: `/home/ec2-user/mega-agent2/`

---

## Current Status (Phase 1 - ✅ COMPLETE)

### Core Infrastructure

✅ **MegaAgentOrchestrator** - Central coordination system
- Async task creation and execution
- Task queue (asyncio.Queue)
- Event processing and routing
- MCP coordinator server for inter-agent communication

✅ **AsyncContextManager** - Persistent state management
- Async file I/O with aiofiles
- Automatic context rotation (10MB or 1000 tasks)
- Compressed task archiving (gzip)
- 7-day active retention, 90-day archive retention

✅ **MultiProviderRouter** - Multi-LLM support
- Bedrock (Claude Sonnet 4.5, Haiku 4.5)
- Google (Gemini 2.5 Pro, Flash)
- OpenAI (GPT-5, GPT-4o)
- Cerebras (Llama 3.3 70B, Llama 3.1 8B, Qwen, GPT-OSS)

✅ **SDKAgentWrapper** - Base agent class
- Wraps ClaudeSDKClient
- Pre/post tool hooks
- LLM routing integration
- Data storage utilities

✅ **Configuration System**
- model-routing.json (multi-provider routing)
- pyproject.toml (modern Python packaging)
- Environment variable management

---

## Planned Capabilities (Phases 2-4)

### 16 Specialized Agents

#### 1. Communication Agent (Phase 2)
**Status**: Pending implementation
**Purpose**: Manages all communication channels

**Capabilities**:
- ✓ Slack message monitoring and sending (FlyCow workspace)
- ✓ Email management for multiple Gmail accounts (Aquarius & FlyCow)
- ✓ @mention tracking
- ✓ Direct message monitoring
- ✓ Unread message aggregation
- ✓ Channel listing and management

**Actions**:
- `read_mentions` - Get Slack mentions
- `read_dms` - Get direct messages
- `send_message` - Send Slack messages
- `list_channels` - List all Slack channels
- `search` - Search Slack messages or emails
- `read` - Read emails with query support
- `send` - Send emails with attachments and HTML
- `summary` - Generate communication summary

**External APIs**: Slack SDK, Gmail API

---

#### 2. Code Operations Agent (Phase 2)
**Status**: Pending implementation
**Purpose**: GitHub repositories, code reviews, AI-powered development

**Capabilities**:
- ✓ GitHub repository management (clone, pull, push)
- ✓ Repository listing and exploration
- ✓ Commit history retrieval (multi-branch support)
- ✓ Issue creation and listing
- ✓ Pull request creation and listing
- ✓ Code review workflows
- ✓ Build and CI/CD monitoring
- ✓ Cursor Cloud Agent creation and management
- ✓ AI-powered code tasks via Cursor Cloud Agents
- ✓ Automated PR creation via Cursor

**Actions**:
- `clone` - Clone GitHub repository
- `pull` - Pull latest changes
- `push` - Push changes to repository
- `list_repos` - List all GitHub repositories
- `get_commits` - Get recent commits (all branches)
- `create_issue` - Create GitHub issue
- `list_issues` - List issues
- `create_pr` - Create pull request
- `list_prs` - List pull requests
- `cursor_create_agent` - Create Cursor Cloud Agent
- `cursor_run_task` - Create agent and wait for completion

**External APIs**: GitHub API, git CLI, Cursor API

---

#### 3. Reporting Agent (Phase 2)
**Status**: Pending implementation
**Purpose**: Analytics, App Store metrics, Skillz events, business reporting

**Capabilities**:
- ✓ App Store Connect integration (multiple accounts)
- ✓ App availability management (countries/territories)
- ✓ ASO keyword management (App Store Optimization)
- ✓ Firebase integration (Firestore, project management)
- ✓ Skillz Developer Portal integration
- ✓ Skillz live events monitoring and reporting
- ✓ Daily and weekly report generation
- ✓ Sales report retrieval
- ✓ Multi-account support

**Actions**:
- `list_apps` - List all apps for App Store Connect account
- `sales_report` - Get App Store sales reports
- `app_analytics` - Get app analytics data
- `get_availability` - Get app availability (countries/territories)
- `update_availability` - Update app availability
- `list_territories` - List all available territories
- `get_keywords` - Get ASO keywords
- `update_keywords` - Update ASO keywords
- `firebase_project_info` - Get Firebase project information
- `firebase_read/write/query` - Firestore operations
- `skillz_events` - Get Skillz game events report
- `skillz_game_info` - Get Skillz game information
- `daily/weekly` - Generate reports
- `metrics` - Analytics and metrics tasks

**External APIs**: App Store Connect API, Firebase Admin SDK, Skillz Developer Portal

---

#### 4. Scheduling Agent (Phase 2)
**Status**: Pending implementation
**Purpose**: Google Calendar and meeting coordination

**Capabilities**:
- ✓ Calendar management
- ✓ Meeting scheduling and coordination
- ✓ Reminder management
- ✓ Time management

**Actions**:
- `meeting` - Handle meeting-related tasks
- `calendar` - Manage calendar events
- `reminder` - Set reminders

**External APIs**: Google Calendar API, Google Tasks API

---

#### 5. Automation Agent (Phase 2)
**Status**: Pending implementation
**Purpose**: Task management, workflow automation, ClickUp and Linear integration

**Capabilities**:
- ✓ ClickUp task creation and management
- ✓ Linear issue creation and management
- ✓ Task retrieval and updates
- ✓ List/workspace/team management
- ✓ Project and cycle tracking
- ✓ Workflow automation

**Actions**:
- `clickup_create_task` - Create ClickUp task
- `clickup_get_tasks` - Get tasks from a list
- `clickup_get_workspaces` - Get all workspaces/teams
- `linear_get_teams` - Get Linear teams
- `linear_get_issues` - Get issues with filters
- `linear_create_issue` - Create Linear issue
- `linear_update_issue` - Update Linear issue
- `linear_get_projects` - Get Linear projects
- `linear_search` - Search Linear issues

**External APIs**: ClickUp API, Linear API

---

#### 6. Creative Agent (Phase 3)
**Status**: Pending implementation
**Purpose**: Image generation, content creation, creative workflows

**Capabilities**:
- ✓ Image generation using AI models (DALL-E, Gemini)
- ✓ Image editing capabilities
- ✓ Content creation
- ✓ Design workflows

**Actions**:
- `image_generation` - Generate images with AI
- `image_editing` - Edit images
- `content_creation` - Create content
- `design` - Handle design tasks

**External APIs**: OpenAI API (DALL-E), Google AI (Gemini)

---

#### 7. Life Agent (Phase 3)
**Status**: Pending implementation
**Purpose**: Personal assistant for life organization

**Capabilities**:
- ✓ Reminder management
- ✓ Note-taking
- ✓ Personal task tracking
- ✓ Life organization
- ✓ Daily email summary generation

**Actions**:
- `reminder` - Create and manage reminders
- `note` - Take notes
- `personal` - Handle personal tasks
- `daily_summary` - Send daily email summary

---

#### 8. Web Browser Agent (Phase 3)
**Status**: Pending implementation
**Purpose**: Web page navigation, parsing, data extraction

**Capabilities**:
- ✓ HTTP requests (GET/POST)
- ✓ HTML parsing with BeautifulSoup
- ✓ Data extraction (links, images, tables, text)
- ✓ Page searching
- ✓ Link following
- ✓ Session management with cookies

**Actions**:
- `fetch` - Fetch web page
- `parse` - Parse HTML content
- `extract` - Extract data
- `search` - Search for content on page
- `follow_links` - Follow and gather information from links

**External APIs**: requests, BeautifulSoup

---

#### 9. Game Ideas Agent (Phase 3)
**Status**: Pending implementation
**Purpose**: Creative game idea generation

**Capabilities**:
- ✓ AI-powered game idea generation
- ✓ Market research via GitHub repos and web trends
- ✓ Compelling description generation
- ✓ HTML page generation with neo-brutal styling
- ✓ Idea storage and retrieval
- ✓ Daily batch generation

**Actions**:
- `generate` - Generate new game ideas
- `daily_generation` - Daily batch of 10 ideas
- `refresh_descriptions` - Regenerate AI descriptions
- `request_prototype` - Request game prototyper
- `query` - Advanced filtering
- `list` - List all ideas
- `search` - Search ideas by keyword

---

#### 10. Agent Improvement Agent (Phase 3)
**Status**: Pending implementation
**Purpose**: System analysis and improvement suggestions

**Capabilities**:
- ✓ Deep system analysis using thinking models
- ✓ Architecture and technical debt identification
- ✓ Agent enhancement suggestions
- ✓ New agent ideas based on context
- ✓ Suggestion tracking (pending/implemented/discarded)

**Actions**:
- `analyze` - Analyze system and generate suggestions
- `email_report` - Generate HTML report and email
- `list` - List all suggestions
- `implement` - Mark suggestion as implemented
- `discard` - Mark suggestion as discarded

---

#### 11. Game Prototyper Agent (Phase 3)
**Status**: Pending implementation
**Purpose**: Design and implement web-based game prototypes

**Capabilities**:
- ✓ Complete game prototyping pipeline (design → assets → code → deploy)
- ✓ Integration with Game Ideas Agent
- ✓ AI-powered game design
- ✓ Architecture and technology stack planning
- ✓ Asset generation via Creative Agent
- ✓ Full game implementation in HTML5/JavaScript
- ✓ Automated web deployment
- ✓ Games directory page maintenance

**Actions**:
- `prototype` - Create complete game from concept
- `design` - Design game architecture and mechanics
- `implement` - Generate game code
- `deploy` - Deploy game to web server
- `list` - List all prototyped games
- `refresh` - Regenerate games directory page

---

#### 12. Fieldy Agent (Phase 3)
**Status**: Pending implementation
**Purpose**: Conversation analysis and coaching insights

**Capabilities**:
- ✓ Fieldy conversation data loading and analysis
- ✓ Daily conversation summary generation
- ✓ Followup suggestion extraction
- ✓ Communication coaching insights
- ✓ Timeline generation from conversations

**Actions**:
- `daily_summary` - Generate and send daily summary email
- `analyze_conversations` - Analyze conversations for a date
- `generate_insights` - Generate followup and coaching insights

---

#### 13. WordPress Agent (Phase 3)
**Status**: Pending implementation
**Purpose**: WordPress site management and content creation

**Capabilities**:
- ✓ WordPress site management (multiple sites)
- ✓ Post and page CRUD operations
- ✓ Category and tag management
- ✓ Media upload and management
- ✓ Comment management
- ✓ Article rewriting with structured templates
- ✓ Content generation using LLM
- ✓ Scheduled publishing
- ✓ Multi-site operations

**Actions**:
- `create_post` - Create new WordPress post
- `update_post` - Update existing WordPress post
- `rewrite_post` - Rewrite post using structured template
- `restyle_post` - Restyle/reformat existing post
- `create_content` - Generate new content from template
- `manage_categories/tags` - Manage categories and tags
- `upload_media` - Upload media files
- `list_posts` - List posts with filters
- `search_content` - Search WordPress content

**External APIs**: WordPress REST API

---

#### 14. Supabase Agent (Phase 3)
**Status**: Pending implementation
**Purpose**: Supabase project management

**Capabilities**:
- ✓ List Supabase projects
- ✓ Get project details
- ✓ Update authentication configuration
- ✓ Manage OTP rate limits
- ✓ Get auth configuration

**Actions**:
- `list_projects` - List all Supabase projects
- `get_project` - Get project details
- `update_auth_config` - Update authentication configuration
- `set_otp_limit` - Set OTP rate limit
- `get_auth_config` - Get authentication configuration

**External APIs**: Supabase Admin API

---

#### 15. Workflow Agent (Phase 3)
**Status**: Pending implementation
**Purpose**: Automated workflow management

**Capabilities**:
- ✓ Email workflow automation
- ✓ Slack workflow automation
- ✓ Rule-based message processing
- ✓ Action sequence execution
- ✓ Template variable extraction
- ✓ LLM-based fuzzy matching

**Actions**:
- `workflow_list` - List all workflow rules
- `workflow_add` - Add a new workflow rule
- `workflow_update` - Update a workflow rule
- `workflow_delete` - Delete a workflow rule
- `workflow_test` - Test a workflow rule
- `workflow_monitor_start/stop` - Monitor control
- `workflow_status` - Get system status

**External APIs**: Gmail API, Slack API, Google Tasks API, Linear API

---

#### 16. Google Ads Agent (Phase 3)
**Status**: Pending implementation
**Purpose**: Google Ads campaign management

**Capabilities**:
- ✓ List accessible Google Ads customer accounts
- ✓ Campaign management and monitoring
- ✓ Campaign performance reporting and analytics
- ✓ Budget management and optimization
- ✓ Campaign status control (pause/enable)
- ✓ Account-level performance summaries
- ✓ Multi-account support
- ✓ ROI and ROAS tracking

**Actions**:
- `list_accounts` - List all accessible customer accounts
- `list_campaigns` - List all campaigns
- `get_performance` - Get campaign performance metrics
- `get_summary` - Get account performance summary
- `pause_campaign` - Pause a campaign
- `enable_campaign` - Enable a paused campaign
- `daily_report` - Generate daily performance report
- `weekly_report` - Generate weekly performance report

**External APIs**: Google Ads API

---

## Automated Workflows (Phase 4)

### Daily Workflows

1. **Daily Email Summary** (4 AM PT)
   - AI-generated sunrise image
   - Inspirational quotes
   - Communications summary
   - Upcoming meetings (2 days ahead)
   - GitHub activity (24 hours)
   - Game ideas (10 new)
   - Weather forecast
   - News headlines

2. **Daily Agent Suggestions** (1 AM PT)
   - System analysis
   - Improvement suggestions
   - Architecture review

3. **Daily App Store Report** (3 AM PT)
   - Downloads, revenue, ratings
   - All apps analytics

4. **Daily Play Store Report** (3:15 AM PT)
   - Downloads, revenue, ratings
   - All apps analytics

5. **Daily Skillz Report** (6 AM PT)
   - Tournament events aggregation
   - Performance metrics

6. **Daily WordPress Pending Posts** (11 PM PT)
   - Rewrite pending posts
   - Publish and send summary

### On-Demand Workflows

- GitHub activity email
- GitHub review
- Business week summary
- Life summary

---

## Supported AI Models

### Claude (via Bedrock)
- claude-sonnet-4-5
- claude-haiku-4-5

### Google Gemini
- gemini-2.5-pro
- gemini-2.5-flash
- gemini-2.5-flash-image

### OpenAI
- gpt-5
- gpt-5-codex
- gpt-4o
- gpt-image-1 (DALL-E)

### Cerebras (Ultra-fast inference)
- llama-3.3-70b
- llama3.1-8b
- qwen-3-32b
- qwen-3-235b-instruct
- qwen-3-235b-thinking
- gpt-oss-120b

---

## External API Integrations

- ✅ Slack (FlyCow workspace)
- ✅ Gmail (Multiple accounts)
- ✅ GitHub
- ✅ ClickUp
- ✅ Linear
- ✅ App Store Connect (15+ apps)
- ✅ Firebase/Firestore
- ✅ Skillz Developer Portal
- ✅ Supabase
- ✅ WordPress (Multiple sites)
- ✅ Google Ads
- ✅ Google Calendar
- ✅ Google Tasks
- ✅ Cursor Cloud Agents
- ✅ OpenWeatherMap
- ✅ News API

---

## Key Features

### Architecture
- **Async/await throughout** - All operations are async
- **SDK-based** - Uses Claude Agent SDK for agent coordination
- **Multi-provider LLM** - Routes to optimal model per task
- **Persistent context** - Tasks and memory persist to disk
- **MCP coordination** - Shared MCP server for inter-agent communication
- **Configuration-driven** - model-routing.json for flexibility

### Operations
- **Event-driven** - Reactive to Slack, email, GitHub events
- **Task queue** - Async task queue with priority
- **Context rotation** - Automatic archiving of old tasks
- **Multi-account** - Supports multiple accounts per service
- **Comprehensive logging** - All actions logged with timestamps
- **Error handling** - Robust error handling and recovery

### Development
- **Modern packaging** - pyproject.toml with setuptools
- **Type hints** - Full type annotations throughout
- **Testing** - pytest with async support
- **Documentation** - Comprehensive docs and examples

---

## Implementation Timeline

### Phase 1: Core Infrastructure ✅ COMPLETE
- MegaAgentOrchestrator
- AsyncContextManager
- MultiProviderRouter
- SDKAgentWrapper
- Configuration system

### Phase 2: First 5 Agents (In Progress)
1. Communication Agent
2. Code Agent
3. Reporting Agent
4. Scheduling Agent
5. Automation Agent

### Phase 3: Remaining 11 Agents
6-16. All remaining agents

### Phase 4: Integration & Testing
- All workflows
- Integration tests
- End-to-end testing
- Documentation
- Performance optimization

---

## Installation & Usage

```bash
cd /home/ec2-user/mega-agent2

# Install dependencies
pip install -r requirements.txt

# Or install as package
pip install -e .

# Test core infrastructure
python test_basic.py
```

## Configuration

Required environment variables:
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `GOOGLE_API_KEY`
- Slack/Gmail/GitHub tokens
- Service-specific API keys

See `.env.example` for complete list.

---

Built with [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python)
