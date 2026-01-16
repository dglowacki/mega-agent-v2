"""
MCP Prompts Loader - Load skills as MCP prompts.

Discovers and registers all 27 skills from .claude/skills/ as MCP prompts,
allowing ElevenLabs' native Claude to access specialized capabilities.
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .protocol import MCPServer, PromptDefinition

logger = logging.getLogger(__name__)


class PromptsLoader:
    """
    Load skills as MCP prompts.

    Scans .claude/skills/ directory and registers each skill as an MCP prompt
    that can be invoked by the LLM.
    """

    def __init__(self, skills_path: str = ".claude/skills"):
        """
        Initialize PromptsLoader.

        Args:
            skills_path: Path to skills directory
        """
        self.skills_path = Path(skills_path)
        self._skills_cache: Dict[str, Tuple[str, str, str]] = {}  # name -> (description, content, category)

    def discover_skills(self, base_path: Optional[str] = None) -> Dict[str, Tuple[str, str, str]]:
        """
        Discover all skills in the skills directory.

        Args:
            base_path: Base path to search from

        Returns:
            Dictionary of skill name -> (description, content, category)
        """
        base = Path(base_path) if base_path else Path.cwd()
        skills_dir = base / self.skills_path

        if not skills_dir.exists():
            logger.warning(f"Skills directory not found: {skills_dir}")
            return {}

        self._skills_cache.clear()

        for skill_file in skills_dir.glob("*/SKILL.md"):
            skill_info = self._parse_skill_file(skill_file)
            if skill_info:
                name, description, content, category = skill_info
                self._skills_cache[name] = (description, content, category)
                logger.debug(f"Discovered skill: {name}")

        logger.info(f"Discovered {len(self._skills_cache)} skills")
        return self._skills_cache

    def _parse_skill_file(self, path: Path) -> Optional[Tuple[str, str, str, str]]:
        """
        Parse a SKILL.md file.

        Args:
            path: Path to SKILL.md file

        Returns:
            Tuple of (name, description, content, category) or None
        """
        try:
            content = path.read_text()
        except Exception as e:
            logger.error(f"Failed to read {path}: {e}")
            return None

        # Parse YAML frontmatter
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n?(.*)', content, re.DOTALL)
        if not frontmatter_match:
            return None

        frontmatter = frontmatter_match.group(1)
        body = frontmatter_match.group(2).strip()

        # Extract name
        name_match = re.search(r'^name:\s*(.+)$', frontmatter, re.MULTILINE)
        if not name_match:
            return None
        name = name_match.group(1).strip()

        # Extract description
        desc_match = re.search(r'^description:\s*(.+)$', frontmatter, re.MULTILINE)
        description = desc_match.group(1).strip() if desc_match else f"Skill: {name}"

        # Infer category
        category = self._infer_category(name, description)

        return name, description, body, category

    def _infer_category(self, name: str, description: str) -> str:
        """Infer skill category from name and description."""
        text = f"{name} {description}".lower()

        category_patterns = {
            "aws": ["aws", "lambda", "dynamodb", "s3", "cdk", "serverless", "bedrock"],
            "development": ["debug", "test", "tdd", "git", "code review", "worktree"],
            "automation": ["email", "template", "report", "calendar", "task"],
            "analysis": ["analysis", "github", "metrics", "data", "aggregate"],
            "planning": ["plan", "brainstorm", "design", "architect"]
        }

        for category, patterns in category_patterns.items():
            if any(p in text for p in patterns):
                return category

        return "general"

    def register_skills_as_prompts(
        self,
        server: MCPServer,
        base_path: Optional[str] = None
    ) -> int:
        """
        Register all skills as MCP prompts.

        Args:
            server: MCPServer instance
            base_path: Base path to search from

        Returns:
            Number of prompts registered
        """
        skills = self.discover_skills(base_path)

        for name, (description, content, category) in skills.items():
            # Create arguments based on skill content
            arguments = self._extract_arguments(content)

            # Register as prompt
            server.register_prompt(
                name=f"skill_{name.replace('-', '_')}",
                description=description,
                arguments=arguments,
                content=content
            )

        logger.info(f"Registered {len(skills)} skills as prompts")
        return len(skills)

    def _extract_arguments(self, content: str) -> List[Dict[str, str]]:
        """
        Extract potential arguments from skill content.

        Looks for placeholder patterns like {topic}, {file_path}, etc.

        Args:
            content: Skill content

        Returns:
            List of argument definitions
        """
        # Find {placeholder} patterns
        placeholders = re.findall(r'\{(\w+)\}', content)

        arguments = []
        seen = set()

        for placeholder in placeholders:
            if placeholder not in seen:
                seen.add(placeholder)
                arguments.append({
                    "name": placeholder,
                    "description": f"Value for {placeholder.replace('_', ' ')}",
                    "required": False
                })

        return arguments

    def get_skill_content(self, name: str) -> Optional[str]:
        """
        Get the content of a specific skill.

        Args:
            name: Skill name

        Returns:
            Skill content or None
        """
        if name in self._skills_cache:
            return self._skills_cache[name][1]
        return None

    def get_skills_by_category(self, category: str) -> List[str]:
        """
        Get all skill names in a category.

        Args:
            category: Category name

        Returns:
            List of skill names
        """
        return [
            name for name, (_, _, cat) in self._skills_cache.items()
            if cat == category
        ]

    def format_skills_summary(self) -> str:
        """
        Format a summary of all skills for context.

        Returns:
            Formatted summary string
        """
        if not self._skills_cache:
            self.discover_skills()

        lines = ["# Available Skills\n"]

        # Group by category
        by_category: Dict[str, List[Tuple[str, str]]] = {}
        for name, (description, _, category) in self._skills_cache.items():
            if category not in by_category:
                by_category[category] = []
            by_category[category].append((name, description))

        category_order = ["aws", "development", "automation", "analysis", "planning", "general"]

        for category in category_order:
            if category not in by_category:
                continue

            lines.append(f"\n## {category.title()}\n")
            for name, description in by_category[category]:
                lines.append(f"- **{name}**: {description}")

        return "\n".join(lines)
