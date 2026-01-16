"""
Skill Creation Tools - Create and manage Claude skills.

Provides a step-by-step workflow for creating new skills that extend
Claude's capabilities with specialized knowledge, workflows, and tools.
"""

import os
import sys
import logging
import subprocess
import re
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

SKILLS_DIR = "/home/ec2-user/mega-agent2/.claude/skills"
SKILL_CREATOR_SCRIPTS = f"{SKILLS_DIR}/skill-creator/scripts"
SKILLSMP_API_SCRIPT = f"{SKILLS_DIR}/skill-find/scripts/skillsmp_api.py"


def skill_create_start(
    name: str,
    description: str,
    use_cases: str = ""
) -> str:
    """
    Step 1: Start creating a new skill by initializing the directory structure.

    Args:
        name: Skill name in hyphen-case (e.g., 'pdf-editor', 'data-analyzer')
        description: What the skill does and when to use it
        use_cases: Example use cases or triggers for this skill

    Returns:
        Status message with next steps
    """
    # Validate name format
    if not re.match(r'^[a-z0-9-]+$', name):
        return f"Error: Skill name must be hyphen-case (lowercase letters, digits, hyphens only). Got: {name}"

    if name.startswith('-') or name.endswith('-') or '--' in name:
        return "Error: Name cannot start/end with hyphen or contain consecutive hyphens"

    if len(name) > 64:
        return f"Error: Name too long ({len(name)} chars). Maximum is 64 characters."

    skill_path = Path(SKILLS_DIR) / name
    if skill_path.exists():
        return f"Error: Skill '{name}' already exists at {skill_path}"

    try:
        # Run init_skill.py
        result = subprocess.run(
            [sys.executable, f"{SKILL_CREATOR_SCRIPTS}/init_skill.py", name, "--path", SKILLS_DIR],
            capture_output=True,
            text=True,
            cwd=SKILLS_DIR
        )

        if result.returncode != 0:
            return f"Error initializing skill: {result.stderr}"

        # Update SKILL.md with provided description
        skill_md = skill_path / "SKILL.md"
        if skill_md.exists():
            content = skill_md.read_text()
            # Replace TODO description with actual description
            content = re.sub(
                r'description: \[TODO:.*?\]',
                f'description: {description}',
                content
            )
            skill_md.write_text(content)

        response = f"""Skill '{name}' initialized successfully!

Location: {skill_path}

Created files:
  - SKILL.md (main skill file)
  - scripts/ (for executable code)
  - references/ (for documentation)
  - assets/ (for templates, images)

Next steps:
1. Use skill_edit_instructions to add the main skill content
2. Use skill_add_script to add any helper scripts
3. Use skill_validate to check the skill
4. Use skill_activate to make it available

Description set to: {description}
"""
        if use_cases:
            response += f"\nUse cases noted: {use_cases}"

        logger.info(f"Created skill: {name}")
        return response

    except Exception as e:
        logger.error(f"Failed to create skill: {e}")
        return f"Error creating skill: {str(e)}"


def skill_edit_instructions(
    name: str,
    instructions: str,
    section: str = "main"
) -> str:
    """
    Step 2: Add or update the skill's instructions in SKILL.md.

    Args:
        name: Name of the skill to edit
        instructions: The instruction content to add (markdown format)
        section: Which section to update ('main' replaces TODO sections, 'append' adds to end)

    Returns:
        Status message
    """
    skill_path = Path(SKILLS_DIR) / name
    skill_md = skill_path / "SKILL.md"

    if not skill_md.exists():
        return f"Error: Skill '{name}' not found. Use skill_create_start first."

    try:
        content = skill_md.read_text()

        if section == "main":
            # Find and replace the TODO sections
            # Remove the "Structuring This Skill" section and replace with actual content
            content = re.sub(
                r'## Structuring This Skill.*?(?=## Resources|## \[TODO|\Z)',
                '',
                content,
                flags=re.DOTALL
            )
            # Replace [TODO: ...] section with actual instructions
            content = re.sub(
                r'## \[TODO:.*?\].*?(?=## Resources|\Z)',
                instructions + '\n\n',
                content,
                flags=re.DOTALL
            )
        elif section == "append":
            # Append to end of file
            content = content.rstrip() + '\n\n' + instructions + '\n'
        else:
            return f"Error: Unknown section '{section}'. Use 'main' or 'append'."

        skill_md.write_text(content)

        return f"""Updated SKILL.md for '{name}'.

Content added to {section} section.

Next steps:
- Use skill_add_script to add helper scripts if needed
- Use skill_validate to check the skill structure
- Use skill_activate to make it available to the agent
"""

    except Exception as e:
        logger.error(f"Failed to edit skill: {e}")
        return f"Error editing skill: {str(e)}"


def skill_add_script(
    name: str,
    script_name: str,
    script_content: str,
    executable: bool = True
) -> str:
    """
    Step 3: Add a helper script to the skill.

    Args:
        name: Name of the skill
        script_name: Name of the script file (e.g., 'process_data.py')
        script_content: The script content
        executable: Whether to make the script executable

    Returns:
        Status message
    """
    skill_path = Path(SKILLS_DIR) / name
    scripts_dir = skill_path / "scripts"

    if not skill_path.exists():
        return f"Error: Skill '{name}' not found."

    try:
        scripts_dir.mkdir(exist_ok=True)

        # Remove example.py if it exists
        example_script = scripts_dir / "example.py"
        if example_script.exists():
            example_script.unlink()

        script_path = scripts_dir / script_name
        script_path.write_text(script_content)

        if executable:
            script_path.chmod(0o755)

        return f"""Added script '{script_name}' to skill '{name}'.

Path: {script_path}
Executable: {executable}

You can reference this script in SKILL.md instructions.
"""

    except Exception as e:
        logger.error(f"Failed to add script: {e}")
        return f"Error adding script: {str(e)}"


def skill_add_reference(
    name: str,
    ref_name: str,
    ref_content: str
) -> str:
    """
    Add a reference document to the skill.

    Args:
        name: Name of the skill
        ref_name: Name of the reference file (e.g., 'api_docs.md')
        ref_content: The reference content (markdown)

    Returns:
        Status message
    """
    skill_path = Path(SKILLS_DIR) / name
    refs_dir = skill_path / "references"

    if not skill_path.exists():
        return f"Error: Skill '{name}' not found."

    try:
        refs_dir.mkdir(exist_ok=True)

        # Remove example reference if it exists
        example_ref = refs_dir / "api_reference.md"
        if example_ref.exists():
            example_ref.unlink()

        ref_path = refs_dir / ref_name
        ref_path.write_text(ref_content)

        return f"""Added reference '{ref_name}' to skill '{name}'.

Path: {ref_path}

Reference docs are loaded into context when Claude needs them.
"""

    except Exception as e:
        logger.error(f"Failed to add reference: {e}")
        return f"Error adding reference: {str(e)}"


def skill_validate(name: str) -> str:
    """
    Step 4: Validate the skill structure and content.

    Args:
        name: Name of the skill to validate

    Returns:
        Validation result
    """
    skill_path = Path(SKILLS_DIR) / name

    if not skill_path.exists():
        return f"Error: Skill '{name}' not found."

    try:
        result = subprocess.run(
            [sys.executable, f"{SKILL_CREATOR_SCRIPTS}/quick_validate.py", str(skill_path)],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return f"""Skill '{name}' is valid!

The skill is ready to be activated.
Use skill_activate to make it available to the agent.
"""
        else:
            return f"""Validation failed for skill '{name}':

{result.stdout}
{result.stderr}

Please fix the issues and validate again.
"""

    except Exception as e:
        logger.error(f"Validation error: {e}")
        return f"Error validating skill: {str(e)}"


def skill_activate(name: str) -> str:
    """
    Step 5: Activate the skill, making it available to the agent.

    This restarts the MCP server to load the new skill as a prompt.

    Args:
        name: Name of the skill to activate

    Returns:
        Activation status
    """
    skill_path = Path(SKILLS_DIR) / name

    if not skill_path.exists():
        return f"Error: Skill '{name}' not found."

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return f"Error: SKILL.md not found in skill '{name}'."

    try:
        # Validate first
        result = subprocess.run(
            [sys.executable, f"{SKILL_CREATOR_SCRIPTS}/quick_validate.py", str(skill_path)],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return f"Error: Skill validation failed. Please fix issues first:\n{result.stdout}"

        # Restart MCP server to load new skill
        restart_result = subprocess.run(
            ["sudo", "systemctl", "restart", "mcp-server-v2"],
            capture_output=True,
            text=True
        )

        if restart_result.returncode != 0:
            return f"Warning: Could not restart MCP server: {restart_result.stderr}\nSkill may need manual activation."

        # Wait a moment and check status
        import time
        time.sleep(2)

        status_result = subprocess.run(
            ["sudo", "systemctl", "status", "mcp-server-v2"],
            capture_output=True,
            text=True
        )

        # Count skills in output
        skills_match = re.search(r'Registered (\d+) skills', status_result.stdout)
        skills_count = skills_match.group(1) if skills_match else "unknown"

        return f"""Skill '{name}' activated successfully!

The MCP server has been restarted.
Total skills now available: {skills_count}

The skill is now available to the agent. You can use it by describing tasks that match the skill's description.
"""

    except Exception as e:
        logger.error(f"Activation error: {e}")
        return f"Error activating skill: {str(e)}"


def skill_list() -> str:
    """
    List all available skills.

    Returns:
        List of skills with their descriptions
    """
    skills_path = Path(SKILLS_DIR)

    if not skills_path.exists():
        return "No skills directory found."

    try:
        skills = []
        for skill_dir in sorted(skills_path.iterdir()):
            if skill_dir.is_dir():
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    content = skill_md.read_text()
                    # Extract description from frontmatter
                    desc_match = re.search(r'description:\s*(.+?)(?:\n---|\n[a-z]+:)', content, re.DOTALL)
                    desc = desc_match.group(1).strip()[:100] if desc_match else "No description"
                    skills.append(f"  - {skill_dir.name}: {desc}")

        if not skills:
            return "No skills found."

        return f"Available skills ({len(skills)}):\n" + "\n".join(skills)

    except Exception as e:
        logger.error(f"Error listing skills: {e}")
        return f"Error listing skills: {str(e)}"


def skill_view(name: str) -> str:
    """
    View the contents of a skill's SKILL.md file.

    Args:
        name: Name of the skill to view

    Returns:
        The skill's SKILL.md content
    """
    skill_path = Path(SKILLS_DIR) / name
    skill_md = skill_path / "SKILL.md"

    if not skill_md.exists():
        return f"Error: Skill '{name}' not found."

    try:
        content = skill_md.read_text()
        return f"=== SKILL.md for '{name}' ===\n\n{content}"
    except Exception as e:
        return f"Error reading skill: {str(e)}"


def skill_delete(name: str, confirm: bool = False) -> str:
    """
    Delete a skill.

    Args:
        name: Name of the skill to delete
        confirm: Must be True to actually delete

    Returns:
        Status message
    """
    if not confirm:
        return f"To delete skill '{name}', call again with confirm=True"

    skill_path = Path(SKILLS_DIR) / name

    if not skill_path.exists():
        return f"Error: Skill '{name}' not found."

    # Don't allow deleting core skills
    protected = ['skill-creator', 'image-generation']
    if name in protected:
        return f"Error: Cannot delete protected skill '{name}'."

    try:
        import shutil
        shutil.rmtree(skill_path)
        return f"Skill '{name}' deleted. Restart MCP server to update available skills."
    except Exception as e:
        return f"Error deleting skill: {str(e)}"


def skill_marketplace_search(
    query: str,
    ai_search: bool = False
) -> str:
    """
    Search for skills on SkillsMP marketplace.

    Args:
        query: Search query (keywords or natural language)
        ai_search: Use AI semantic search instead of keyword search

    Returns:
        Search results with skill names, descriptions, and URLs
    """
    try:
        search_type = "ai-search" if ai_search else "search"
        result = subprocess.run(
            [sys.executable, SKILLSMP_API_SCRIPT, search_type, query],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            return f"Search error: {result.stderr}"

        return result.stdout or "No results found."

    except subprocess.TimeoutExpired:
        return "Error: Search timed out. Try a simpler query."
    except Exception as e:
        logger.error(f"Marketplace search error: {e}")
        return f"Error searching marketplace: {str(e)}"


def skill_marketplace_install(skill_url: str) -> str:
    """
    Install a skill from SkillsMP marketplace.

    Args:
        skill_url: SkillsMP URL for the skill to install (e.g., https://skillsmp.com/skills/...)

    Returns:
        Installation status
    """
    if "skillsmp.com" not in skill_url:
        return "Error: URL must be from skillsmp.com"

    try:
        result = subprocess.run(
            [sys.executable, SKILLSMP_API_SCRIPT, "install", skill_url],
            capture_output=True,
            text=True,
            timeout=120
        )

        output = result.stdout + result.stderr

        if "success" in output.lower():
            # After successful install, restart MCP server
            restart_result = subprocess.run(
                ["sudo", "systemctl", "restart", "mcp-server-v2"],
                capture_output=True,
                text=True
            )

            if restart_result.returncode == 0:
                return f"Skill installed and activated!\n\n{output}\n\nMCP server restarted - skill is now available."
            else:
                return f"Skill installed but needs manual activation:\n\n{output}\n\nRun: sudo systemctl restart mcp-server-v2"

        return output or "Installation completed."

    except subprocess.TimeoutExpired:
        return "Error: Installation timed out."
    except Exception as e:
        logger.error(f"Marketplace install error: {e}")
        return f"Error installing skill: {str(e)}"


def skill_marketplace_info(skill_url: str) -> str:
    """
    Get information about a skill on SkillsMP marketplace.

    Args:
        skill_url: SkillsMP URL for the skill

    Returns:
        Skill information (name, description, author, etc.)
    """
    if "skillsmp.com" not in skill_url:
        return "Error: URL must be from skillsmp.com"

    try:
        result = subprocess.run(
            [sys.executable, SKILLSMP_API_SCRIPT, "info", skill_url],
            capture_output=True,
            text=True,
            timeout=30
        )

        return result.stdout or result.stderr or "No information available."

    except Exception as e:
        logger.error(f"Marketplace info error: {e}")
        return f"Error getting skill info: {str(e)}"


def register_skill_tools(server) -> int:
    """Register skill creation tools."""

    server.register_tool(
        name="skill_create_start",
        description="Step 1: Start creating a new skill. Initializes the skill directory with template files.",
        input_schema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Skill name in hyphen-case (e.g., 'pdf-editor', 'data-analyzer')"
                },
                "description": {
                    "type": "string",
                    "description": "What the skill does and when to use it (max 1024 chars)"
                },
                "use_cases": {
                    "type": "string",
                    "description": "Example use cases or trigger phrases for this skill"
                }
            },
            "required": ["name", "description"]
        },
        handler=skill_create_start,
        requires_approval=True,
        category="skill"
    )

    server.register_tool(
        name="skill_edit_instructions",
        description="Step 2: Add the main instructions to a skill's SKILL.md file.",
        input_schema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the skill to edit"
                },
                "instructions": {
                    "type": "string",
                    "description": "Markdown content with skill instructions, workflows, examples"
                },
                "section": {
                    "type": "string",
                    "description": "Where to add content: 'main' replaces TODOs, 'append' adds to end",
                    "enum": ["main", "append"],
                    "default": "main"
                }
            },
            "required": ["name", "instructions"]
        },
        handler=skill_edit_instructions,
        requires_approval=True,
        category="skill"
    )

    server.register_tool(
        name="skill_add_script",
        description="Step 3: Add a helper script to the skill.",
        input_schema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the skill"
                },
                "script_name": {
                    "type": "string",
                    "description": "Script filename (e.g., 'process.py')"
                },
                "script_content": {
                    "type": "string",
                    "description": "The script content"
                },
                "executable": {
                    "type": "boolean",
                    "description": "Make script executable",
                    "default": True
                }
            },
            "required": ["name", "script_name", "script_content"]
        },
        handler=skill_add_script,
        requires_approval=True,
        category="skill"
    )

    server.register_tool(
        name="skill_add_reference",
        description="Add a reference document to the skill for additional context.",
        input_schema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the skill"
                },
                "ref_name": {
                    "type": "string",
                    "description": "Reference filename (e.g., 'api_docs.md')"
                },
                "ref_content": {
                    "type": "string",
                    "description": "Reference content in markdown"
                }
            },
            "required": ["name", "ref_name", "ref_content"]
        },
        handler=skill_add_reference,
        requires_approval=True,
        category="skill"
    )

    server.register_tool(
        name="skill_validate",
        description="Step 4: Validate a skill's structure and content before activation.",
        input_schema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the skill to validate"
                }
            },
            "required": ["name"]
        },
        handler=skill_validate,
        requires_approval=False,
        category="skill"
    )

    server.register_tool(
        name="skill_activate",
        description="Step 5: Activate a skill, making it available to the agent. Restarts MCP server.",
        input_schema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the skill to activate"
                }
            },
            "required": ["name"]
        },
        handler=skill_activate,
        requires_approval=True,
        category="skill"
    )

    server.register_tool(
        name="skill_list",
        description="List all available skills with their descriptions.",
        input_schema={
            "type": "object",
            "properties": {}
        },
        handler=skill_list,
        requires_approval=False,
        category="skill"
    )

    server.register_tool(
        name="skill_view",
        description="View a skill's SKILL.md content.",
        input_schema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the skill to view"
                }
            },
            "required": ["name"]
        },
        handler=skill_view,
        requires_approval=False,
        category="skill"
    )

    server.register_tool(
        name="skill_delete",
        description="Delete a skill (requires confirmation).",
        input_schema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the skill to delete"
                },
                "confirm": {
                    "type": "boolean",
                    "description": "Must be true to confirm deletion",
                    "default": False
                }
            },
            "required": ["name"]
        },
        handler=skill_delete,
        requires_approval=True,
        category="skill"
    )

    # Marketplace tools
    server.register_tool(
        name="skill_marketplace_search",
        description="Search for skills on SkillsMP marketplace (63,000+ skills). Use ai_search=true for semantic natural language queries.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query - keywords or natural language description"
                },
                "ai_search": {
                    "type": "boolean",
                    "description": "Use AI semantic search (better for natural language queries)",
                    "default": False
                }
            },
            "required": ["query"]
        },
        handler=skill_marketplace_search,
        requires_approval=False,
        category="skill"
    )

    server.register_tool(
        name="skill_marketplace_install",
        description="Install a skill from SkillsMP marketplace by URL. Automatically activates the skill after installation.",
        input_schema={
            "type": "object",
            "properties": {
                "skill_url": {
                    "type": "string",
                    "description": "SkillsMP skill URL (e.g., https://skillsmp.com/skills/...)"
                }
            },
            "required": ["skill_url"]
        },
        handler=skill_marketplace_install,
        requires_approval=True,
        category="skill"
    )

    server.register_tool(
        name="skill_marketplace_info",
        description="Get detailed information about a skill on SkillsMP marketplace.",
        input_schema={
            "type": "object",
            "properties": {
                "skill_url": {
                    "type": "string",
                    "description": "SkillsMP skill URL"
                }
            },
            "required": ["skill_url"]
        },
        handler=skill_marketplace_info,
        requires_approval=False,
        category="skill"
    )

    return 12
