"""
File Tools - Read, write, edit, glob, grep operations.

Provides comprehensive file system access for the voice assistant.
"""

import os
import re
import glob as glob_module
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Base directory for file operations (security boundary)
BASE_DIR = Path("/home/ec2-user")


def _validate_path(path: str) -> Path:
    """
    Validate and resolve a file path.

    Args:
        path: File path to validate

    Returns:
        Resolved Path object

    Raises:
        ValueError: If path is outside allowed directory
    """
    resolved = Path(path).resolve()

    # Check if path is within allowed directory
    if not str(resolved).startswith(str(BASE_DIR)):
        raise ValueError(f"Path {path} is outside allowed directory")

    return resolved


def file_read(path: str, offset: int = 0, limit: int = 2000) -> str:
    """
    Read contents of a file.

    Args:
        path: Absolute path to the file
        offset: Line number to start reading from (0-based)
        limit: Maximum number of lines to read

    Returns:
        File contents with line numbers
    """
    resolved = _validate_path(path)

    if not resolved.exists():
        return f"Error: File not found: {path}"

    if resolved.is_dir():
        return f"Error: Path is a directory: {path}"

    try:
        with open(resolved, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()

        total_lines = len(lines)

        # Apply offset and limit
        start = max(0, offset)
        end = min(total_lines, start + limit)
        selected = lines[start:end]

        # Format with line numbers
        result_lines = []
        for i, line in enumerate(selected, start=start + 1):
            result_lines.append(f"{i:>6}| {line.rstrip()}")

        if end < total_lines:
            result_lines.append(f"\n... ({total_lines - end} more lines)")

        return "\n".join(result_lines)

    except Exception as e:
        return f"Error reading file: {str(e)}"


def file_write(path: str, content: str) -> str:
    """
    Write content to a file.

    Args:
        path: Absolute path to the file
        content: Content to write

    Returns:
        Success or error message
    """
    resolved = _validate_path(path)

    try:
        # Create parent directories if needed
        resolved.parent.mkdir(parents=True, exist_ok=True)

        with open(resolved, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"Successfully wrote {len(content)} bytes to {path}"

    except Exception as e:
        return f"Error writing file: {str(e)}"


def file_edit(path: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
    """
    Edit a file by replacing text.

    Args:
        path: Absolute path to the file
        old_string: Text to find
        new_string: Replacement text
        replace_all: Replace all occurrences if True

    Returns:
        Success or error message
    """
    resolved = _validate_path(path)

    if not resolved.exists():
        return f"Error: File not found: {path}"

    try:
        with open(resolved, 'r', encoding='utf-8') as f:
            content = f.read()

        # Count occurrences
        count = content.count(old_string)

        if count == 0:
            return f"Error: String not found in file"

        if count > 1 and not replace_all:
            return f"Error: String found {count} times. Use replace_all=true to replace all."

        # Perform replacement
        if replace_all:
            new_content = content.replace(old_string, new_string)
            replaced = count
        else:
            new_content = content.replace(old_string, new_string, 1)
            replaced = 1

        with open(resolved, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return f"Successfully replaced {replaced} occurrence(s)"

    except Exception as e:
        return f"Error editing file: {str(e)}"


def file_glob(pattern: str, path: str = None) -> str:
    """
    Find files matching a glob pattern.

    Args:
        pattern: Glob pattern (e.g., "**/*.py")
        path: Base directory to search in

    Returns:
        List of matching files
    """
    base = Path(path) if path else BASE_DIR
    base = _validate_path(str(base))

    try:
        matches = list(base.glob(pattern))
        matches = sorted(matches, key=lambda p: p.stat().st_mtime, reverse=True)[:100]

        if not matches:
            return "No files found matching pattern"

        result = [f"Found {len(matches)} files:"]
        for match in matches:
            rel_path = match.relative_to(base) if match.is_relative_to(base) else match
            result.append(f"  {rel_path}")

        return "\n".join(result)

    except Exception as e:
        return f"Error searching files: {str(e)}"


def file_grep(
    pattern: str,
    path: str = None,
    glob_pattern: str = None,
    case_insensitive: bool = False,
    context_lines: int = 0
) -> str:
    """
    Search for pattern in files.

    Args:
        pattern: Regex pattern to search for
        path: File or directory to search in
        glob_pattern: Filter files by glob pattern
        case_insensitive: Case-insensitive search
        context_lines: Number of context lines before/after match

    Returns:
        Matching lines with file and line info
    """
    base = Path(path) if path else BASE_DIR
    base = _validate_path(str(base))

    flags = re.IGNORECASE if case_insensitive else 0

    try:
        regex = re.compile(pattern, flags)
    except re.error as e:
        return f"Invalid regex pattern: {str(e)}"

    results = []
    files_searched = 0
    matches_found = 0

    try:
        if base.is_file():
            files = [base]
        else:
            if glob_pattern:
                files = list(base.glob(glob_pattern))
            else:
                files = list(base.rglob("*"))

        files = [f for f in files if f.is_file()][:1000]

        for file_path in files:
            # Skip binary files
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
            except Exception:
                continue

            files_searched += 1

            for i, line in enumerate(lines):
                if regex.search(line):
                    matches_found += 1

                    # Get context
                    start = max(0, i - context_lines)
                    end = min(len(lines), i + context_lines + 1)

                    rel_path = file_path.relative_to(BASE_DIR) if file_path.is_relative_to(BASE_DIR) else file_path
                    results.append(f"\n{rel_path}:{i + 1}:")

                    for j in range(start, end):
                        prefix = ">" if j == i else " "
                        results.append(f"  {prefix} {j + 1}: {lines[j].rstrip()}")

                    if matches_found >= 50:
                        break

            if matches_found >= 50:
                results.append("\n... (truncated at 50 matches)")
                break

        if not results:
            return f"No matches found in {files_searched} files"

        return f"Found {matches_found} matches in {files_searched} files:" + "\n".join(results)

    except Exception as e:
        return f"Error searching: {str(e)}"


def file_delete(path: str) -> str:
    """
    Delete a file.

    Args:
        path: Absolute path to the file

    Returns:
        Success or error message
    """
    resolved = _validate_path(path)

    if not resolved.exists():
        return f"Error: File not found: {path}"

    if resolved.is_dir():
        return f"Error: Cannot delete directory with this tool"

    try:
        resolved.unlink()
        return f"Successfully deleted {path}"
    except Exception as e:
        return f"Error deleting file: {str(e)}"


def file_list(path: str = None) -> str:
    """
    List contents of a directory.

    Args:
        path: Directory path

    Returns:
        Directory listing
    """
    base = Path(path) if path else Path.cwd()
    base = _validate_path(str(base))

    if not base.exists():
        return f"Error: Directory not found: {path}"

    if not base.is_dir():
        return f"Error: Path is not a directory: {path}"

    try:
        items = sorted(base.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))

        result = [f"Contents of {base}:", ""]
        for item in items[:100]:
            if item.is_dir():
                result.append(f"  [dir]  {item.name}/")
            else:
                size = item.stat().st_size
                result.append(f"  {size:>8}  {item.name}")

        if len(list(base.iterdir())) > 100:
            result.append("\n... (truncated)")

        return "\n".join(result)

    except Exception as e:
        return f"Error listing directory: {str(e)}"


def register_file_tools(server) -> int:
    """Register all file tools with the MCP server."""

    server.register_tool(
        name="file_read",
        description="Read contents of a file with line numbers. Use offset and limit for large files.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute path to the file"},
                "offset": {"type": "integer", "description": "Line number to start from (0-based)", "default": 0},
                "limit": {"type": "integer", "description": "Maximum lines to read", "default": 2000}
            },
            "required": ["path"]
        },
        handler=file_read,
        requires_approval=False,
        category="file"
    )

    server.register_tool(
        name="file_write",
        description="Write content to a file, creating it if it doesn't exist.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute path to the file"},
                "content": {"type": "string", "description": "Content to write"}
            },
            "required": ["path", "content"]
        },
        handler=file_write,
        requires_approval=True,
        category="file"
    )

    server.register_tool(
        name="file_edit",
        description="Edit a file by replacing text. Finds and replaces exact string matches.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute path to the file"},
                "old_string": {"type": "string", "description": "Text to find and replace"},
                "new_string": {"type": "string", "description": "Replacement text"},
                "replace_all": {"type": "boolean", "description": "Replace all occurrences", "default": False}
            },
            "required": ["path", "old_string", "new_string"]
        },
        handler=file_edit,
        requires_approval=True,
        category="file"
    )

    server.register_tool(
        name="file_glob",
        description="Find files matching a glob pattern (e.g., '**/*.py' for all Python files).",
        input_schema={
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern to match"},
                "path": {"type": "string", "description": "Base directory to search in"}
            },
            "required": ["pattern"]
        },
        handler=file_glob,
        requires_approval=False,
        category="file"
    )

    server.register_tool(
        name="file_grep",
        description="Search for a regex pattern in files. Returns matching lines with context.",
        input_schema={
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern to search for"},
                "path": {"type": "string", "description": "File or directory to search in"},
                "glob_pattern": {"type": "string", "description": "Filter files (e.g., '*.py')"},
                "case_insensitive": {"type": "boolean", "description": "Case-insensitive search", "default": False},
                "context_lines": {"type": "integer", "description": "Context lines before/after", "default": 0}
            },
            "required": ["pattern"]
        },
        handler=file_grep,
        requires_approval=False,
        category="file"
    )

    server.register_tool(
        name="file_delete",
        description="Delete a file (not directories).",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute path to the file to delete"}
            },
            "required": ["path"]
        },
        handler=file_delete,
        requires_approval=True,
        category="file"
    )

    server.register_tool(
        name="file_list",
        description="List contents of a directory with file sizes.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path to list"}
            },
            "required": []
        },
        handler=file_list,
        requires_approval=False,
        category="file"
    )

    return 7  # Number of tools registered
