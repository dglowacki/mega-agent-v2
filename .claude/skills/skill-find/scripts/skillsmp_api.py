#!/usr/bin/env python3
"""
SkillsMP API Client - Search and install skills from skillsmp.com

Usage:
    python skillsmp_api.py search "query"
    python skillsmp_api.py ai-search "natural language query"
    python skillsmp_api.py install <skill-url>
    python skillsmp_api.py info <skill-url>
"""

import argparse
import json
import os
import re
import sys
import zipfile
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    print("Error: requests package not installed. Run: pip install requests")
    sys.exit(1)

API_BASE = "https://skillsmp.com/api/v1"
API_KEY = os.getenv("SKILLSMP_API_KEY", "sk_live_skillsmp_K6fOZpyOxwCOnnfRfnOZJ6vooDlCg0uTusLvJ6ZBveU")
SKILLS_DIR = "/home/ec2-user/mega-agent2/.claude/skills"


def get_headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }


def search_skills(query: str, ai_search: bool = False) -> dict:
    """Search for skills using keyword or AI semantic search."""
    endpoint = "ai-search" if ai_search else "search"
    url = f"{API_BASE}/skills/{endpoint}"
    
    try:
        response = requests.get(
            url,
            params={"q": query},
            headers=get_headers(),
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def get_skill_info(skill_url: str) -> dict:
    """Get information about a specific skill."""
    # Extract skill path from URL
    parsed = urlparse(skill_url)
    if "skillsmp.com" not in parsed.netloc:
        return {"error": "Invalid SkillsMP URL"}
    
    # The skill path is like /skills/author-repo-path-skill-md
    skill_path = parsed.path.replace("/skills/", "")
    
    url = f"{API_BASE}/skills/{skill_path}"
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def install_skill(skill_url: str) -> dict:
    """Download and install a skill from SkillsMP."""
    # Get skill info first
    info = get_skill_info(skill_url)
    if "error" in info:
        return info
    
    skill_name = info.get("name", "unknown-skill")
    download_url = info.get("download_url") or info.get("raw_url")
    
    if not download_url:
        # Try to construct raw URL from skill URL
        # SkillsMP URLs often map to GitHub raw content
        parsed = urlparse(skill_url)
        skill_path = parsed.path.replace("/skills/", "")
        # Convert skillsmp path to GitHub raw path
        # Format: author-repo-path-to-skill-md -> github.com/author/repo/path/to/SKILL.md
        parts = skill_path.split("-")
        if len(parts) >= 2:
            author = parts[0]
            # This is a simplified conversion - actual mapping may vary
            download_url = f"https://raw.githubusercontent.com/{skill_path.replace('-', '/', 1)}/main/SKILL.md"
    
    if not download_url:
        return {"error": "Could not determine download URL for skill"}
    
    # Create skill directory
    skill_dir = Path(SKILLS_DIR) / skill_name
    if skill_dir.exists():
        return {"error": f"Skill '{skill_name}' already exists. Delete it first to reinstall."}
    
    try:
        skill_dir.mkdir(parents=True)
        
        # Download SKILL.md
        response = requests.get(download_url, timeout=30)
        response.raise_for_status()
        
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(response.text)
        
        return {
            "status": "success",
            "skill_name": skill_name,
            "installed_to": str(skill_dir),
            "message": f"Skill '{skill_name}' installed. Run skill_activate to enable it."
        }
    except Exception as e:
        # Clean up on failure
        if skill_dir.exists():
            import shutil
            shutil.rmtree(skill_dir)
        return {"error": f"Installation failed: {str(e)}"}


def format_search_results(results: dict) -> str:
    """Format search results for display."""
    if "error" in results:
        return f"Error: {results['error']}"
    
    skills = results.get("skills", results.get("results", []))
    if not skills:
        return "No skills found."
    
    output = [f"Found {len(skills)} skills:\n"]
    
    for skill in skills[:10]:  # Limit to 10 results
        name = skill.get("name", "Unknown")
        desc = skill.get("description", "No description")[:100]
        url = skill.get("url", skill.get("skillsmp_url", ""))
        author = skill.get("author", "Unknown")
        
        output.append(f"  - {name}")
        output.append(f"    Author: {author}")
        output.append(f"    {desc}...")
        if url:
            output.append(f"    URL: {url}")
        output.append("")
    
    if len(skills) > 10:
        output.append(f"... and {len(skills) - 10} more results")
    
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="SkillsMP API Client")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Keyword search for skills")
    search_parser.add_argument("query", help="Search query")
    
    # AI Search command
    ai_parser = subparsers.add_parser("ai-search", help="AI semantic search for skills")
    ai_parser.add_argument("query", help="Natural language query")
    
    # Install command
    install_parser = subparsers.add_parser("install", help="Install a skill")
    install_parser.add_argument("url", help="SkillsMP skill URL")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Get skill info")
    info_parser.add_argument("url", help="SkillsMP skill URL")
    
    args = parser.parse_args()
    
    if args.command == "search":
        results = search_skills(args.query, ai_search=False)
        print(format_search_results(results))
    elif args.command == "ai-search":
        results = search_skills(args.query, ai_search=True)
        print(format_search_results(results))
    elif args.command == "install":
        result = install_skill(args.url)
        print(json.dumps(result, indent=2))
    elif args.command == "info":
        result = get_skill_info(args.url)
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
