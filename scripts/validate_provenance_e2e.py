"""End-to-end validation script for provenance features.

Tests provenance accuracy with real queries and validates:
- Source matching accuracy
- Relevance score correctness
- Token-level matching
- Query refinement suggestions
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bop.agent import KnowledgeAgent
from bop.provenance import build_provenance_map
from bop.query_refinement import suggest_followup_queries, refine_query_from_provenance

console = Console()

# Test queries that should produce good provenance data
TEST_QUERIES = [
    "What is d-separation and how does it relate to causal inference?",
    "Explain information geometry and its applications.",
    "How do trust metrics work in knowledge systems?",
]


async def validate_provenance_accuracy(
    query: str,
    response: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Validate provenance accuracy for a response.
    
    Returns:
        Dictionary with validation results
    """
    validation_results = {
        "query": query,
        "has_provenance": False,
        "num_claims": 0,
        "claims_with_sources": 0,
        "avg_relevance_score": 0.0,
        "relevance_breakdowns": [],
        "token_matches": 0,
        "issues": [],
    }
    
    if not response.get("research_conducted"):
        validation_results["issues"].append("No research conducted")
        return validation_results
    
    research_data = response.get("research", {})
    provenance = research_data.get("provenance", {})
    
    if not provenance:
        validation_results["issues"].append("No provenance data found")
        return validation_results
    
    validation_results["has_provenance"] = True
    validation_results["num_claims"] = len(provenance)
    
    relevance_scores = []
    total_token_matches = 0
    
    for claim_text, provenance_info in provenance.items():
        sources = provenance_info.get("sources", [])
        
        if sources:
            validation_results["claims_with_sources"] += 1
            
            for source in sources:
                # Check relevance breakdown
                relevance_breakdown = source.get("relevance_breakdown", {})
                if relevance_breakdown:
                    overall_score = relevance_breakdown.get("overall_score", 0.0)
                    relevance_scores.append(overall_score)
                    
                    validation_results["relevance_breakdowns"].append({
                        "claim": claim_text[:60],
                        "source": source.get("source", "unknown"),
                        "score": overall_score,
                        "components": relevance_breakdown.get("components", {}),
                    })
                
                # Count token matches
                token_matches = source.get("token_matches", {})
                if token_matches:
                    total_token_matches += len(token_matches)
    
    if relevance_scores:
        validation_results["avg_relevance_score"] = sum(relevance_scores) / len(relevance_scores)
    
    validation_results["token_matches"] = total_token_matches
    
    # Validation checks
    if validation_results["claims_with_sources"] == 0:
        validation_results["issues"].append("No claims have source matches")
    
    if validation_results["avg_relevance_score"] < 0.3:
        validation_results["issues"].append(f"Low average relevance score: {validation_results['avg_relevance_score']:.2f}")
    
    if total_token_matches == 0:
        validation_results["issues"].append("No token matches found")
    
    return validation_results


async def validate_query_refinement(
    query: str,
    provenance: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Validate query refinement suggestions.
    
    Returns:
        Dictionary with refinement validation results
    """
    validation_results = {
        "query": query,
        "has_suggestions": False,
        "num_suggestions": 0,
        "suggestion_types": [],
        "issues": [],
    }
    
    if not provenance:
        validation_results["issues"].append("No provenance data for refinement")
        return validation_results
    
    # Get suggestions
    suggestions = refine_query_from_provenance(query, provenance)
    
    if not suggestions:
        validation_results["issues"].append("No refinement suggestions generated")
        return validation_results
    
    validation_results["has_suggestions"] = True
    validation_results["num_suggestions"] = len(suggestions)
    
    suggestion_types = set()
    for suggestion in suggestions:
        suggestion_type = suggestion.get("type", "unknown")
        suggestion_types.add(suggestion_type)
        validation_results["suggestion_types"].append({
            "type": suggestion_type,
            "query": suggestion.get("query", ""),
            "rationale": suggestion.get("rationale", ""),
        })
    
    validation_results["suggestion_types"] = list(suggestion_types)
    
    # Validation checks
    if len(suggestions) < 1:
        validation_results["issues"].append("Too few suggestions (expected at least 1)")
    
    return validation_results


async def run_validation():
    """Run end-to-end validation."""
    console.print(Panel.fit("[bold blue]Provenance End-to-End Validation[/bold blue]", border_style="blue"))
    
    agent = KnowledgeAgent(enable_quality_feedback=True)
    
    all_results = []
    
    for i, query in enumerate(TEST_QUERIES, 1):
        console.print(f"\n[bold cyan]Test {i}/{len(TEST_QUERIES)}:[/bold cyan] {query}")
        
        try:
            # Get response with research
            response = await agent.chat(
                message=query,
                use_schema="decompose_and_synthesize",
                use_research=True,
            )
            
            # Validate provenance accuracy
            provenance_validation = await validate_provenance_accuracy(query, response)
            all_results.append(provenance_validation)
            
            # Validate query refinement
            provenance = response.get("research", {}).get("provenance", {})
            refinement_validation = await validate_query_refinement(query, provenance)
            
            # Display results
            console.print(f"  [green]✓[/green] Provenance: {provenance_validation['num_claims']} claims, "
                        f"{provenance_validation['claims_with_sources']} with sources")
            
            if provenance_validation["avg_relevance_score"] > 0:
                console.print(f"  [green]✓[/green] Avg relevance: {provenance_validation['avg_relevance_score']:.2f}")
            
            if refinement_validation["has_suggestions"]:
                console.print(f"  [green]✓[/green] Query refinement: {refinement_validation['num_suggestions']} suggestions")
            
            if provenance_validation["issues"]:
                for issue in provenance_validation["issues"]:
                    console.print(f"  [yellow]⚠[/yellow] {issue}")
            
        except Exception as e:
            console.print(f"  [red]✗[/red] Error: {e}")
            all_results.append({
                "query": query,
                "error": str(e),
            })
    
    # Summary table
    console.print("\n" + "="*80)
    console.print("[bold]Validation Summary[/bold]")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Query", style="cyan", width=50)
    table.add_column("Claims", justify="right")
    table.add_column("With Sources", justify="right")
    table.add_column("Avg Relevance", justify="right")
    table.add_column("Token Matches", justify="right")
    table.add_column("Issues", style="yellow")
    
    for result in all_results:
        if "error" in result:
            table.add_row(
                result["query"][:50],
                "ERROR",
                "-",
                "-",
                "-",
                result["error"][:30],
            )
        else:
            issues_str = ", ".join(result["issues"]) if result["issues"] else "None"
            table.add_row(
                result["query"][:50],
                str(result["num_claims"]),
                str(result["claims_with_sources"]),
                f"{result['avg_relevance_score']:.2f}" if result["avg_relevance_score"] > 0 else "-",
                str(result["token_matches"]),
                issues_str[:30],
            )
    
    console.print(table)
    
    # Overall status
    total_tests = len(all_results)
    passed_tests = sum(1 for r in all_results if r.get("has_provenance") and not r.get("issues"))
    
    console.print(f"\n[bold]Overall:[/bold] {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        console.print("[bold green]✓ All provenance features validated successfully![/bold green]")
        return 0
    else:
        console.print("[bold yellow]⚠ Some issues found. Review validation results above.[/bold yellow]")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_validation())
    sys.exit(exit_code)

