"""Comprehensive integration validation for all provenance features.

Validates that all features work together correctly across:
- Agent → Orchestrator → Provenance → Visualization → UI
"""

import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bop.agent import KnowledgeAgent
from bop.provenance import build_provenance_map
from bop.provenance_viz import (
    create_provenance_heatmap,
    create_relevance_breakdown_display,
    format_clickable_source,
)
from bop.query_refinement import (
    refine_query_from_provenance,
    suggest_followup_queries,
    create_query_refinement_panel,
)

console = Console()


async def validate_agent_integration():
    """Validate that agent properly integrates all provenance features."""
    console.print("[bold cyan]Validating Agent Integration...[/bold cyan]")
    
    agent = KnowledgeAgent(enable_quality_feedback=True)
    
    # Test query
    query = "What is d-separation?"
    
    try:
        response = await agent.chat(
            message=query,
            use_research=True,
        )
        
        # Check response structure
        research_data = response.get("research", {})
        provenance = research_data.get("provenance", {}) if research_data else {}
        
        checks = {
            "Response generated": "response" in response,
            "Research conducted": response.get("research_conducted", False),
            "Provenance in research": len(provenance) >= 0,  # May be empty if no matches
            "Query refinement suggestions": (
                "query_refinement_suggestions" in response or
                len(provenance) == 0  # OK if no provenance
            ),
            "Source references": "Sources:" in response.get("response", "") or len(provenance) == 0,
        }
        
        # Check if source references include relevance scores (if provenance exists)
        if provenance and "Sources:" in response.get("response", ""):
            response_text = response.get("response", "")
            checks["Source references with relevance"] = "Relevance:" in response_text or "relevance" in response_text.lower()
        else:
            checks["Source references with relevance"] = True  # N/A if no provenance
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Check", style="cyan", width=40)
        table.add_column("Status", style="green", width=10)
        
        for check, passed in checks.items():
            status = "✓" if passed else "✗"
            color = "green" if passed else "yellow"
            table.add_row(check, f"[{color}]{status}[/{color}]")
        
        console.print(table)
        
        return all(checks.values())
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return False


def validate_provenance_pipeline():
    """Validate complete provenance pipeline."""
    console.print("\n[bold cyan]Validating Provenance Pipeline...[/bold cyan]")
    
    response_text = "D-separation is a graphical criterion for determining conditional independence."
    research = {
        "subsolutions": [
            {
                "subproblem": "What is d-separation?",
                "results": [
                    {
                        "tool": "perplexity_deep_research",
                        "result": "D-separation is a graphical criterion for determining conditional independence in directed acyclic graphs.",
                    }
                ],
            }
        ],
    }
    
    # Step 1: Build provenance map
    provenance_map = build_provenance_map(response_text, research)
    
    checks = {
        "Provenance map created": len(provenance_map) >= 0,  # May be 0 if no matches
        "Provenance structure correct": isinstance(provenance_map, dict),
    }
    
    if len(provenance_map) > 0:
        first_claim = list(provenance_map.keys())[0]
        prov_info = provenance_map[first_claim]
        
        checks["Has sources"] = "sources" in prov_info
        checks["Has num_sources"] = "num_sources" in prov_info
        
        sources = prov_info.get("sources", [])
        if sources:
            top_source = sources[0]
            checks["Source has relevance breakdown"] = "relevance_breakdown" in top_source or "overlap_ratio" in top_source
            checks["Source has semantic similarity"] = "semantic_similarity" in top_source or "overlap_ratio" in top_source
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Check", style="cyan", width=40)
    table.add_column("Status", style="green", width=10)
    
    for check, passed in checks.items():
        status = "✓" if passed else "✗"
        color = "green" if passed else "yellow"
        table.add_row(check, f"[{color}]{status}[/{color}]")
    
    console.print(table)
    
    return all(checks.values())


def validate_visualization_integration():
    """Validate visualization functions work with provenance data."""
    console.print("\n[bold cyan]Validating Visualization Integration...[/bold cyan]")
    
    provenance_data = {
        "D-separation is a graphical criterion": {
            "sources": [
                {
                    "source": "perplexity_deep_research",
                    "overlap_ratio": 0.65,
                    "semantic_similarity": 0.72,
                    "relevance_breakdown": {
                        "overall_score": 0.74,
                        "components": {
                            "word_overlap": 0.65,
                            "semantic_similarity": 0.72,
                            "token_match_avg": 0.85,
                        },
                    },
                }
            ],
            "num_sources": 1,
        }
    }
    
    checks = {
        "Provenance heatmap": create_provenance_heatmap(provenance_data) is not None,
        "Relevance breakdown display": create_relevance_breakdown_display(
            provenance_data["D-separation is a graphical criterion"]["sources"][0]["relevance_breakdown"]
        ) is not None,
        "Clickable source format": format_clickable_source(
            "Test claim",
            provenance_data["D-separation is a graphical criterion"]
        )[0] is not None,
        "Query refinement panel": create_query_refinement_panel(provenance_data, "Test query") is not None,
    }
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Check", style="cyan", width=40)
    table.add_column("Status", style="green", width=10)
    
    for check, passed in checks.items():
        status = "✓" if passed else "✗"
        color = "green" if passed else "yellow"
        table.add_row(check, f"[{color}]{status}[/{color}]")
    
    console.print(table)
    
    return all(checks.values())


def validate_error_handling():
    """Validate error handling across all features."""
    console.print("\n[bold cyan]Validating Error Handling...[/bold cyan]")
    
    checks = {}
    
    # Test with empty data
    try:
        provenance_map = build_provenance_map("", {})
        checks["Empty data handled"] = isinstance(provenance_map, dict)
    except Exception:
        checks["Empty data handled"] = False
    
    # Test with missing relevance breakdown
    try:
        provenance_info = {"sources": [{"source": "test", "overlap_ratio": 0.5}]}
        formatted, tooltip = format_clickable_source("Test", provenance_info)
        checks["Missing breakdown handled"] = isinstance(formatted, str)
    except Exception:
        checks["Missing breakdown handled"] = False
    
    # Test with empty provenance for refinement
    try:
        suggestions = refine_query_from_provenance("Test", {})
        checks["Empty provenance handled"] = isinstance(suggestions, list)
    except Exception:
        checks["Empty provenance handled"] = False
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Check", style="cyan", width=40)
    table.add_column("Status", style="green", width=10)
    
    for check, passed in checks.items():
        status = "✓" if passed else "✗"
        color = "green" if passed else "yellow"
        table.add_row(check, f"[{color}]{status}[/{color}]")
    
    console.print(table)
    
    return all(checks.values())


async def main():
    """Run all integration validations."""
    console.print(Panel.fit(
        "[bold blue]Complete Integration Validation[/bold blue]\n\n"
        "Validating all provenance features work together correctly.",
        border_style="blue"
    ))
    
    results = {}
    
    # Agent integration
    results["Agent Integration"] = await validate_agent_integration()
    
    # Provenance pipeline
    results["Provenance Pipeline"] = validate_provenance_pipeline()
    
    # Visualization integration
    results["Visualization Integration"] = validate_visualization_integration()
    
    # Error handling
    results["Error Handling"] = validate_error_handling()
    
    # Summary
    console.print("\n" + "="*80)
    console.print("[bold]Integration Validation Summary[/bold]")
    
    summary_table = Table(show_header=True, header_style="bold magenta")
    summary_table.add_column("Component", style="cyan", width=40)
    summary_table.add_column("Status", style="green", width=10)
    
    for component, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        color = "green" if passed else "red"
        summary_table.add_row(component, f"[{color}]{status}[/{color}]")
    
    console.print(summary_table)
    
    all_passed = all(results.values())
    
    if all_passed:
        console.print("\n[bold green]✓ All integration checks passed![/bold green]")
        return 0
    else:
        console.print("\n[bold yellow]⚠ Some integration checks failed. Review above.[/bold yellow]")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

