"""
Bash Tools - Command execution capabilities.

Provides shell command execution with safety controls.
"""

import os
import subprocess
import asyncio
import logging
import shlex
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Working directory for commands
WORKING_DIR = Path("/home/ec2-user/mega-agent2")

# Maximum command output length
MAX_OUTPUT = 30000

# Default timeout (2 minutes)
DEFAULT_TIMEOUT = 120

# Dangerous commands that are blocked
BLOCKED_COMMANDS = {
    "rm -rf /",
    "rm -rf /*",
    "mkfs",
    "dd if=/dev/zero",
    ":(){:|:&};:",
    "chmod -R 777 /",
    "chown -R",
}

# Patterns that indicate potentially dangerous commands
DANGEROUS_PATTERNS = [
    "rm -rf /",
    "> /dev/sda",
    "mkfs.",
    "dd if=",
    ":(){ :|:",
]

# Background processes tracking
_background_processes: Dict[str, subprocess.Popen] = {}
_process_counter = 0


def _is_dangerous(command: str) -> Optional[str]:
    """
    Check if a command is dangerous.

    Args:
        command: Command to check

    Returns:
        Warning message if dangerous, None otherwise
    """
    cmd_lower = command.lower()

    # Check blocked commands
    for blocked in BLOCKED_COMMANDS:
        if blocked in cmd_lower:
            return f"Blocked dangerous command pattern: {blocked}"

    # Check dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if pattern in cmd_lower:
            return f"Command contains dangerous pattern: {pattern}"

    return None


def bash_execute(
    command: str,
    working_dir: str = None,
    timeout: int = DEFAULT_TIMEOUT,
    description: str = None
) -> str:
    """
    Execute a bash command.

    Args:
        command: Command to execute
        working_dir: Working directory for the command
        timeout: Timeout in seconds (max 600)
        description: Human-readable description of the command

    Returns:
        Command output or error message
    """
    # Safety check
    warning = _is_dangerous(command)
    if warning:
        return f"Error: {warning}"

    # Validate working directory
    cwd = Path(working_dir) if working_dir else WORKING_DIR
    if not cwd.exists():
        cwd = WORKING_DIR

    # Clamp timeout
    timeout = min(max(timeout, 1), 600)

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "TERM": "dumb"}
        )

        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr}"

        # Truncate if too long
        if len(output) > MAX_OUTPUT:
            output = output[:MAX_OUTPUT] + f"\n\n... (truncated, {len(output) - MAX_OUTPUT} bytes omitted)"

        # Add return code info
        if result.returncode != 0:
            output += f"\n\n[Exit code: {result.returncode}]"

        return output if output.strip() else "[No output]"

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds"
    except Exception as e:
        return f"Error executing command: {str(e)}"


def bash_background(
    command: str,
    working_dir: str = None,
    description: str = None
) -> str:
    """
    Start a command in the background.

    Args:
        command: Command to execute
        working_dir: Working directory for the command
        description: Human-readable description

    Returns:
        Process ID or error message
    """
    global _process_counter

    # Safety check
    warning = _is_dangerous(command)
    if warning:
        return f"Error: {warning}"

    # Validate working directory
    cwd = Path(working_dir) if working_dir else WORKING_DIR
    if not cwd.exists():
        cwd = WORKING_DIR

    try:
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={**os.environ, "TERM": "dumb"}
        )

        _process_counter += 1
        process_id = f"bg_{_process_counter}"
        _background_processes[process_id] = process

        return f"Started background process: {process_id} (PID: {process.pid})"

    except Exception as e:
        return f"Error starting background process: {str(e)}"


def bash_check_process(process_id: str) -> str:
    """
    Check status of a background process.

    Args:
        process_id: Process ID from bash_background

    Returns:
        Process status and any available output
    """
    process = _background_processes.get(process_id)
    if not process:
        return f"Error: Unknown process ID: {process_id}"

    poll_result = process.poll()

    if poll_result is None:
        return f"Process {process_id} is still running (PID: {process.pid})"

    # Process completed
    stdout, stderr = process.communicate()
    output = stdout
    if stderr:
        output += f"\n[stderr]\n{stderr}"

    # Truncate if needed
    if len(output) > MAX_OUTPUT:
        output = output[:MAX_OUTPUT] + f"\n\n... (truncated)"

    status = "completed successfully" if poll_result == 0 else f"exited with code {poll_result}"
    return f"Process {process_id} {status}:\n\n{output}"


def bash_kill_process(process_id: str) -> str:
    """
    Kill a background process.

    Args:
        process_id: Process ID from bash_background

    Returns:
        Success or error message
    """
    process = _background_processes.get(process_id)
    if not process:
        return f"Error: Unknown process ID: {process_id}"

    try:
        process.terminate()
        process.wait(timeout=5)
        del _background_processes[process_id]
        return f"Process {process_id} terminated"
    except subprocess.TimeoutExpired:
        process.kill()
        del _background_processes[process_id]
        return f"Process {process_id} killed (did not respond to terminate)"
    except Exception as e:
        return f"Error killing process: {str(e)}"


def bash_list_processes() -> str:
    """
    List all background processes.

    Returns:
        List of background processes and their status
    """
    if not _background_processes:
        return "No background processes running"

    lines = ["Background processes:"]
    for pid, process in _background_processes.items():
        poll_result = process.poll()
        if poll_result is None:
            status = "running"
        elif poll_result == 0:
            status = "completed"
        else:
            status = f"exited ({poll_result})"
        lines.append(f"  {pid}: PID {process.pid} - {status}")

    return "\n".join(lines)


def register_bash_tools(server) -> int:
    """Register all bash tools with the MCP server."""

    server.register_tool(
        name="bash_execute",
        description="Execute a bash command and return its output. Use for system commands, build tools, etc.",
        input_schema={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The bash command to execute"},
                "working_dir": {"type": "string", "description": "Working directory for the command"},
                "timeout": {"type": "integer", "description": "Timeout in seconds (max 600)", "default": 120},
                "description": {"type": "string", "description": "Human-readable description of what the command does"}
            },
            "required": ["command"]
        },
        handler=bash_execute,
        requires_approval=True,
        category="bash"
    )

    server.register_tool(
        name="bash_background",
        description="Start a command in the background. Returns a process ID for later checking.",
        input_schema={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The bash command to execute"},
                "working_dir": {"type": "string", "description": "Working directory for the command"},
                "description": {"type": "string", "description": "Description of the command"}
            },
            "required": ["command"]
        },
        handler=bash_background,
        requires_approval=True,
        category="bash"
    )

    server.register_tool(
        name="bash_check_process",
        description="Check the status and output of a background process.",
        input_schema={
            "type": "object",
            "properties": {
                "process_id": {"type": "string", "description": "Process ID from bash_background"}
            },
            "required": ["process_id"]
        },
        handler=bash_check_process,
        requires_approval=False,
        category="bash"
    )

    server.register_tool(
        name="bash_kill_process",
        description="Kill a running background process.",
        input_schema={
            "type": "object",
            "properties": {
                "process_id": {"type": "string", "description": "Process ID to kill"}
            },
            "required": ["process_id"]
        },
        handler=bash_kill_process,
        requires_approval=True,
        category="bash"
    )

    server.register_tool(
        name="bash_list_processes",
        description="List all background processes and their status.",
        input_schema={
            "type": "object",
            "properties": {}
        },
        handler=bash_list_processes,
        requires_approval=False,
        category="bash"
    )

    return 5  # Number of tools registered
