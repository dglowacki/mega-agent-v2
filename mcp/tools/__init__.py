"""
MCP Tools - 106+ tools across multiple categories.

Categories:
- file: read, write, edit, glob, grep
- bash: execute, background
- git: status, diff, commit, push, log
- github: PRs, issues, reviews
- web: search, fetch
- aws: lambda, s3, costs
- comms: email, calendar
- session: approval mode control
- slack: messages, channels, users
- google: calendar, tasks, gmail
- linear: issues, projects
- clickup: tasks, spaces
- wordpress: posts, content
- appstore: apps, sales, downloads
- image: generate, icon, banner
- skill: create, edit, validate, activate
"""

from .file_tools import register_file_tools
from .bash_tools import register_bash_tools
from .git_tools import register_git_tools
from .github_tools import register_github_tools
from .web_tools import register_web_tools
from .aws_tools import register_aws_tools
from .comms_tools import register_comms_tools
from .session_tools import register_session_tools
from .slack_tools import register_slack_tools
from .google_tools import register_google_tools
from .linear_tools import register_linear_tools
from .clickup_tools import register_clickup_tools
from .wordpress_tools import register_wordpress_tools
from .appstore_tools import register_appstore_tools
from .image_tools import register_image_tools
from .skill_tools import register_skill_tools


def register_all_tools(server, security_manager=None, session_id: str = "default"):
    """
    Register all tools with the MCP server.

    Args:
        server: MCPServer instance
        security_manager: SecurityManager instance
        session_id: Session identifier for approval tracking

    Returns:
        Total number of tools registered
    """
    count = 0
    count += register_file_tools(server)
    count += register_bash_tools(server)
    count += register_git_tools(server)
    count += register_github_tools(server)
    count += register_web_tools(server)
    count += register_aws_tools(server)
    count += register_comms_tools(server)
    count += register_slack_tools(server)
    count += register_google_tools(server)
    count += register_linear_tools(server)
    count += register_clickup_tools(server)
    count += register_wordpress_tools(server)
    count += register_appstore_tools(server)
    count += register_image_tools(server)
    count += register_skill_tools(server)
    count += register_session_tools(server, security_manager, session_id)
    return count


__all__ = [
    "register_all_tools",
    "register_file_tools",
    "register_bash_tools",
    "register_git_tools",
    "register_github_tools",
    "register_web_tools",
    "register_aws_tools",
    "register_comms_tools",
    "register_slack_tools",
    "register_google_tools",
    "register_linear_tools",
    "register_clickup_tools",
    "register_wordpress_tools",
    "register_appstore_tools",
    "register_image_tools",
    "register_skill_tools",
    "register_session_tools"
]
