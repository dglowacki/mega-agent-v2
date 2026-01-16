# MCP Server v2 Setup Guide

## Overview

MCP Server v2 provides Model Context Protocol (MCP) support for the ElevenLabs voice assistant, enabling access to:
- **63 tools** across file, bash, git, GitHub, AWS, email, and calendar operations
- **27 skills** from the Claude skillz library
- **Safe/Trust approval modes** with verbal confirmation for write operations
- **"do it" trigger phrase** to enable trust mode

## Architecture

```
ElevenLabs Voice Widget
        ↓
  Native Claude LLM
        ↓
   MCP Protocol (SSE)
        ↓
    MCP Server v2
        ↓
  Tools & Skills
```

## Server Endpoints

| Endpoint | Description |
|----------|-------------|
| `https://a.fcow.ca/av/mcp/sse` | SSE transport for MCP communication |
| `https://a.fcow.ca/av/mcp/message` | HTTP POST for single messages |
| `https://a.fcow.ca/av/mcp/health` | Health check endpoint |
| `https://a.fcow.ca/av/mcp/tools` | List available tools |
| `https://a.fcow.ca/av/mcp/prompts` | List available prompts (skills) |

## Tool Categories

### File Tools (7 tools)
- `file_read` - Read file contents with line numbers
- `file_write` - Write content to a file
- `file_edit` - Edit file by replacing text
- `file_glob` - Find files by pattern
- `file_grep` - Search for patterns in files
- `file_delete` - Delete a file
- `file_list` - List directory contents

### Bash Tools (5 tools)
- `bash_execute` - Run a command
- `bash_background` - Start command in background
- `bash_check_process` - Check background process status
- `bash_kill_process` - Kill a background process
- `bash_list_processes` - List background processes

### Git Tools (11 tools)
- `git_status`, `git_diff`, `git_log`, `git_branch`
- `git_checkout`, `git_add`, `git_commit`
- `git_push`, `git_pull`, `git_stash`, `git_reset`

### GitHub Tools (14 tools)
- `github_pr_list`, `github_pr_view`, `github_pr_create`
- `github_pr_merge`, `github_pr_checkout`, `github_pr_review`
- `github_issue_list`, `github_issue_view`, `github_issue_create`
- `github_issue_comment`, `github_repo_view`
- `github_workflow_list`, `github_workflow_view`

### Web Tools (3 tools)
- `web_search` - Search the web via DuckDuckGo
- `web_fetch` - Fetch content from a URL
- `web_api_call` - Make HTTP API calls

### AWS Tools (11 tools)
- Lambda: `aws_lambda_list`, `aws_lambda_invoke`, `aws_lambda_logs`
- S3: `aws_s3_list`, `aws_s3_get`, `aws_s3_put`
- DynamoDB: `aws_dynamodb_list_tables`, `aws_dynamodb_scan`, `aws_dynamodb_query`
- Costs: `aws_cost_get_usage`, `aws_cost_get_forecast`

### Communications Tools (6 tools)
- Email: `email_send`, `email_draft`
- Calendar: `calendar_list`, `calendar_add`, `calendar_search`, `calendar_delete`

### Session Tools (6 tools)
- `session_get_mode` - Get current approval mode
- `session_enable_trust` - Enable trust mode
- `session_enable_safe` - Enable safe mode
- `session_get_stats` - Get session statistics
- `session_list_approved` - List approved tools
- `session_clear_approvals` - Clear tool approvals

## Approval Modes

### Safe Mode (Default)
- Read operations auto-approved
- Write operations require verbal confirmation
- Claude asks: "Should I write to file X?" and waits for yes/no

### Trust Mode
- All operations auto-approved
- No confirmation required
- Enable by saying **"do it"**

## ElevenLabs Configuration

### Via API

1. **Create MCP Server:**

```bash
curl -X POST 'https://api.elevenlabs.io/v1/convai/mcp-servers' \
  -H 'xi-api-key: YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "config": {
      "name": "mega-agent-v2",
      "url": "https://a.fcow.ca/av/mcp/sse",
      "transport": "SSE",
      "approval_policy": "require_approval_per_tool"
    }
  }'
```

2. **Link to Agent:**

```bash
curl -X PATCH 'https://api.elevenlabs.io/v1/convai/agents/YOUR_AGENT_ID' \
  -H 'xi-api-key: YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "conversation_config": {
      "agent": {
        "prompt": {
          "mcp_servers": ["MCP_SERVER_ID_FROM_STEP_1"]
        }
      }
    }
  }'
```

### Via Dashboard

1. Go to ElevenLabs Conversational AI dashboard
2. Navigate to **MCP Server Integrations**
3. Click **Add Custom MCP Server**
4. Configure:
   - **Name:** mega-agent-v2
   - **URL:** https://a.fcow.ca/av/mcp/sse
   - **Transport:** SSE
   - **Approval Policy:** Fine-Grained Tool Approval
5. Save and link to your agent

## Testing

### Health Check
```bash
curl https://a.fcow.ca/av/mcp/health
```

### List Tools
```bash
curl https://a.fcow.ca/av/mcp/tools
```

### Test Message
```bash
curl -X POST https://a.fcow.ca/av/mcp/message \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}'
```

## Service Management

```bash
# Check status
sudo systemctl status mcp-server-v2

# View logs
sudo journalctl -u mcp-server-v2 -f

# Restart
sudo systemctl restart mcp-server-v2
```

## Files

| File | Description |
|------|-------------|
| `/home/ec2-user/mega-agent2/mcp_server_v2.py` | Main server entry point |
| `/home/ec2-user/mega-agent2/mcp/protocol.py` | MCP protocol handler |
| `/home/ec2-user/mega-agent2/mcp/security.py` | Security/approval layer |
| `/home/ec2-user/mega-agent2/mcp/prompts.py` | Skills loader |
| `/home/ec2-user/mega-agent2/mcp/tools/` | Tool implementations |
| `/etc/systemd/system/mcp-server-v2.service` | Systemd service |
