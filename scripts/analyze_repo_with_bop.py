#!/usr/bin/env python3
"""
Use BOP to analyze the repository and suggest improvements.
Meta-analysis: BOP analyzing itself.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bop.agent import KnowledgeAgent


async def analyze_repository():
    """Use BOP to analyze the repository structure and git history."""
    agent = KnowledgeAgent(enable_quality_feedback=True)
    
    # Analyze git history quality
    print("🔍 Analyzing git commit history quality...")
    history_query = """
    Analyze the git commit history of this repository. Review:
    1. Commit message quality and consistency
    2. Commit frequency and size patterns
    3. Areas for improvement in commit hygiene
    4. Recommendations for better git practices
    
    Focus on identifying:
    - Commits that could be squashed
    - Missing scopes in commit messages
    - Documentation commits that could be consolidated
    - Any anti-patterns in the commit history
    """
    
    # Analyze repository structure
    print("\n📁 Analyzing repository structure...")
    structure_query = """
    Analyze the repository structure and organization:
    1. Directory organization quality
    2. File naming consistency
    3. Documentation organization
    4. Test organization
    5. Configuration file placement
    
    Provide specific recommendations for improvement.
    """
    
    # Analyze hookwise configuration
    print("\n⚙️  Analyzing hookwise configuration...")
    hookwise_query = """
    Review the hookwise configuration for this Python research project:
    1. Are the commit message rules appropriate?
    2. Is the documentation bloat detection configured correctly?
    3. Are there missing checks that should be enabled?
    4. Can the configuration be improved?
    
    Provide specific recommendations for enhancing hookwise setup.
    """
    
    queries = [
        ("Git History", history_query),
        ("Repository Structure", structure_query),
        ("Hookwise Configuration", hookwise_query),
    ]
    
    results = []
    for name, query in queries:
        print(f"\n{'='*60}")
        print(f"Analyzing: {name}")
        print('='*60)
        
        try:
            response = await agent.chat(
                message=query,
                use_schema="decompose_and_synthesize",
                use_research=True,  # Enable MCP tools for best practices research
            )
            
            results.append({
                "topic": name,
                "response": response.get("response", ""),
                "tiers": response.get("response_tiers", {}),
            })
            
            print(f"\n{response.get('response', '')[:500]}...")
            
        except Exception as e:
            print(f"Error analyzing {name}: {e}")
            results.append({
                "topic": name,
                "error": str(e),
            })
    
    return results


if __name__ == "__main__":
    results = asyncio.run(analyze_repository())
    print("\n" + "="*60)
    print("Analysis Complete")
    print("="*60)

