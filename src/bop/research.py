"""Deep research integration using MCP tools."""

import os
from typing import Any, Dict, List, Optional
from pathlib import Path


class ResearchAgent:
    """Agent for conducting deep research using MCP tools."""

    def __init__(self, use_mcp: bool = True):
        """
        Initialize the research agent.

        Args:
            use_mcp: Whether to use MCP tools (requires MCP server connection)
        """
        self.research_history: List[Dict[str, Any]] = []
        self.use_mcp = use_mcp

    async def deep_research(
        self,
        query: str,
        focus_areas: Optional[List[str]] = None,
        max_results: int = 10,
    ) -> Dict[str, Any]:
        """
        Conduct deep research on a topic using MCP tools.

        Args:
            query: Research query
            focus_areas: Optional focus areas for the research
            max_results: Maximum number of results

        Returns:
            Research results dictionary
        """
        if self.use_mcp:
            try:
                # Call actual MCP tool - this will be handled by the orchestrator
                # For now, return structure indicating MCP should be used
                return {
                    "query": query,
                    "focus_areas": focus_areas or [],
                    "results": [],
                    "summary": f"Deep research initiated for: {query}",
                    "sources": [],
                    "mcp_used": True,
                    "needs_mcp_call": True,
                    "tool": "perplexity_deep_research",
                }
            except Exception as e:
                return {
                    "query": query,
                    "focus_areas": focus_areas or [],
                    "results": [],
                    "summary": f"Research error: {str(e)}",
                    "sources": [],
                    "mcp_used": False,
                    "error": str(e),
            }
        else:
            return {
                "query": query,
                "focus_areas": focus_areas or [],
                "results": [],
                "summary": f"Research results for: {query}",
                "sources": [],
                "mcp_used": False,
            }

    async def search(
        self,
        query: str,
        limit: int = 5,
        sources: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Search for information on a topic.

        Args:
            query: Search query
            limit: Maximum number of results
            sources: Optional list of source types (web, images, news)

        Returns:
            Search results dictionary
        """
        return {
            "query": query,
            "results": [],
            "count": 0,
            "needs_mcp_call": True,
            "tool": "perplexity_search",
        }

    async def extract_content(self, urls: List[str]) -> Dict[str, Any]:
        """
        Extract content from URLs.

        Args:
            urls: List of URLs to extract

        Returns:
            Extracted content dictionary
        """
        return {
            "urls": urls,
            "content": [],
            "needs_mcp_call": True,
            "tool": "firecrawl_scrape",
        }

    def add_to_history(self, research: Dict[str, Any]) -> None:
        """Add research result to history."""
        self.research_history.append(research)

    def get_history(self) -> List[Dict[str, Any]]:
        """Get research history."""
        return self.research_history


def load_content(content_dir: Path) -> Dict[str, str]:
    """Load content from markdown files."""
    content = {}
    if content_dir.exists():
        for md_file in content_dir.glob("*.md"):
            content[md_file.stem] = md_file.read_text()
    return content

