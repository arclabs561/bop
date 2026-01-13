"""Skills system for dynamic context loading.

Skills are markdown files containing domain-specific guidance that can be
loaded on demand to provide specialized context without permanent overhead.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class Skill:
    """Represents a single skill file."""

    def __init__(self, name: str, path: Path, content: str):
        """
        Initialize a skill.

        Args:
            name: Skill name (filename without .md)
            path: Path to skill file
            content: Skill content (markdown)
        """
        self.name = name
        self.path = path
        self.content = content
        self._extract_metadata()

    def _extract_metadata(self):
        """Extract metadata from skill content."""
        # Extract purpose from first line or header
        purpose_match = re.search(r'#\s+(.+?)\s*\n', self.content)
        self.purpose = purpose_match.group(1) if purpose_match else self.name

        # Extract tags/keywords
        tag_match = re.search(r'\*\*Tags?:\*\*\s*(.+?)(?:\n|$)', self.content, re.IGNORECASE)
        self.tags = [t.strip() for t in tag_match.group(1).split(',')] if tag_match else []

        # Extract usage section
        usage_match = re.search(r'##\s+Usage\s*\n(.*?)(?=\n##|\Z)', self.content, re.DOTALL)
        self.usage = usage_match.group(1).strip() if usage_match else ""

    def __repr__(self):
        return f"Skill(name={self.name}, purpose={self.purpose})"


class SkillsManager:
    """Manages loading and discovery of skills."""

    def __init__(self, skills_dir: Optional[Path] = None):
        """
        Initialize skills manager.

        Args:
            skills_dir: Directory containing skill files (default: skills/)
        """
        if skills_dir is None:
            # Default to skills/ directory in project root
            project_root = Path(__file__).parent.parent.parent
            skills_dir = project_root / "skills"

        self.skills_dir = Path(skills_dir)
        self.skills: Dict[str, Skill] = {}
        self._load_skills()

    def _load_skills(self):
        """Load all skills from skills directory."""
        if not self.skills_dir.exists():
            logger.warning(f"Skills directory not found: {self.skills_dir}")
            return

        for skill_file in self.skills_dir.glob("*.md"):
            try:
                name = skill_file.stem
                content = skill_file.read_text(encoding="utf-8")
                skill = Skill(name, skill_file, content)
                self.skills[name] = skill
                logger.debug(f"Loaded skill: {name}")
            except Exception as e:
                logger.error(f"Error loading skill {skill_file}: {e}")

    def get_skill(self, name: str) -> Optional[Skill]:
        """
        Get a skill by name.

        Args:
            name: Skill name (with or without .md extension)

        Returns:
            Skill object or None if not found
        """
        # Remove .md extension if present
        name = name.replace(".md", "")
        return self.skills.get(name)

    def list_skills(self) -> List[str]:
        """
        List all available skill names.

        Returns:
            List of skill names
        """
        return list(self.skills.keys())

    def find_relevant_skills(self, query: str, limit: int = 3) -> List[Skill]:
        """
        Find skills relevant to a query.

        Args:
            query: Query text
            limit: Maximum number of skills to return

        Returns:
            List of relevant skills, sorted by relevance
        """
        query_lower = query.lower()
        scored_skills = []

        for skill in self.skills.values():
            score = 0

            # Check name match
            if query_lower in skill.name.lower():
                score += 10

            # Check purpose match
            if query_lower in skill.purpose.lower():
                score += 5

            # Check tag matches
            for tag in skill.tags:
                if query_lower in tag.lower():
                    score += 3

            # Check content match (simple keyword matching)
            content_lower = skill.content.lower()
            keywords = query_lower.split()
            for keyword in keywords:
                if len(keyword) > 3 and keyword in content_lower:
                    score += 1

            if score > 0:
                scored_skills.append((score, skill))

        # Sort by score (descending) and return top N
        scored_skills.sort(key=lambda x: x[0], reverse=True)
        return [skill for _, skill in scored_skills[:limit]]

    def get_skill_content(self, name: str) -> Optional[str]:
        """
        Get skill content as string.

        Args:
            name: Skill name

        Returns:
            Skill content or None if not found
        """
        skill = self.get_skill(name)
        return skill.content if skill else None

