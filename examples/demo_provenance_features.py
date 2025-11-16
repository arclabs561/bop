"""Interactive demo showing provenance features in action.

This script demonstrates the complete user experience with provenance features,
showing before/after comparisons and real usage scenarios.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bop.agent import KnowledgeAgent
from bop.provenance_viz import create_relevance_breakdown_display, format_clickable_source
from bop.query_refinement import refine_query_from_provenance, create_query_refinement_panel
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

console = Console()


async def demo_basic_provenance():
    """Demonstrate basic provenance workflow."""
    console.print(Panel.fit("[bold blue]Demo 1: Basic Provenance Workflow[/bold blue]", border_style="blue"))
    
    agent = KnowledgeAgent(enable_quality_feedback=True)
    
    query = "What is d-separation and how does it relate to causal inference?"
    console.print(f"\n[bold]User Query:[/bold] {query}\n")
    
    try:
        response = await agent.chat(
            message=query,
            use_schema="decompose_and_synthesize",
            use_research=True,
        )
        
        if response.get("research_conducted"):
            console.print("[green]✓ Research conducted[/green]")
            
            research_data = response.get("research", {})
            provenance = research_data.get("provenance", {})
            
            if provenance:
                console.print(f"[green]✓ Provenance created: {len(provenance)} claims[/green]\n")
                
                # Show first claim with provenance
                first_claim = list(provenance.keys())[0]
                prov_info = provenance[first_claim]
                
                console.print(f"[bold]Claim:[/bold] {first_claim[:80]}...")
                console.print(f"[dim]Sources: {prov_info.get('num_sources', 0)}[/dim]")
                
                sources = prov_info.get("sources", [])
                if sources:
                    top_source = sources[0]
                    relevance = top_source.get("relevance_breakdown", {}).get("overall_score")
                    if relevance:
                        console.print(f"[bold green]Relevance Score: {relevance:.2f}[/bold green]")
            else:
                console.print("[yellow]⚠ No provenance data (may need API keys for research)[/yellow]")
        else:
            console.print("[yellow]⚠ Research not conducted (may need API keys)[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[dim]Note: This demo requires API keys for full functionality[/dim]")


async def demo_relevance_breakdowns():
    """Demonstrate relevance score breakdowns."""
    console.print("\n" + "="*80)
    console.print(Panel.fit("[bold cyan]Demo 2: Relevance Score Breakdowns[/bold cyan]", border_style="cyan"))
    
    # Simulate provenance with relevance breakdown
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
                        "explanation": "High word overlap (65.0%). Strong semantic similarity (72.0%). Key token matches: d-separation(0.95), graphical(0.90), criterion(0.88).",
                        "top_token_matches": [
                            ("d-separation", 0.95),
                            ("graphical", 0.90),
                            ("criterion", 0.88),
                        ],
                    },
                }
            ],
            "num_sources": 1,
        }
    }
    
    claim = "D-separation is a graphical criterion"
    prov_info = provenance_data[claim]
    sources = prov_info["sources"]
    breakdown = sources[0]["relevance_breakdown"]
    
    console.print(f"\n[bold]Claim:[/bold] {claim}\n")
    
    # Display relevance breakdown
    breakdown_display = create_relevance_breakdown_display(breakdown)
    console.print(Markdown(breakdown_display))


async def demo_query_refinement():
    """Demonstrate query refinement suggestions."""
    console.print("\n" + "="*80)
    console.print(Panel.fit("[bold green]Demo 3: Query Refinement[/bold green]", border_style="green"))
    
    original_query = "What is d-separation?"
    
    provenance_data = {
        "D-separation is a graphical criterion": {
            "sources": [
                {
                    "source": "perplexity_deep_research",
                    "token_matches": {
                        "d-separation": [("d-separation", 0.95)],
                        "graphical": [("graphical", 0.90)],
                    },
                    "relevance_breakdown": {
                        "overall_score": 0.74,
                        "components": {
                            "semantic_similarity": 0.72,
                        },
                    },
                }
            ],
            "num_sources": 1,
        }
    }
    
    console.print(f"\n[bold]Original Query:[/bold] {original_query}\n")
    
    # Get refinement suggestions
    suggestions = refine_query_from_provenance(original_query, provenance_data)
    
    if suggestions:
        console.print("[bold]Suggested Follow-up Queries:[/bold]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="cyan", width=3)
        table.add_column("Query", style="yellow", width=50)
        table.add_column("Type", style="green", width=15)
        table.add_column("Rationale", style="blue", width=40)
        
        for i, suggestion in enumerate(suggestions, 1):
            table.add_row(
                str(i),
                suggestion["query"],
                suggestion["type"],
                suggestion["rationale"],
            )
        
        console.print(table)
    else:
        console.print("[dim]No refinement suggestions generated[/dim]")


async def demo_clickable_sources():
    """Demonstrate clickable source interaction."""
    console.print("\n" + "="*80)
    console.print(Panel.fit("[bold yellow]Demo 4: Clickable Sources[/bold yellow]", border_style="yellow"))
    
    claim = "D-separation is a graphical criterion for determining conditional independence"
    
    provenance_info = {
        "sources": [
            {
                "source": "perplexity_deep_research",
                "matching_passage": "D-separation is a graphical criterion for determining conditional independence in directed acyclic graphs. It helps identify when variables are conditionally independent given a set of conditioning variables.",
                "overlap_ratio": 0.65,
                "semantic_similarity": 0.72,
                "token_matches": {
                    "d-separation": [("d-separation", 0.95), ("separation", 0.80)],
                    "graphical": [("graphical", 0.90)],
                    "criterion": [("criterion", 0.88)],
                },
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
    }
    
    console.print(f"\n[bold]Claim in Response:[/bold]")
    console.print(f"{claim}\n")
    
    # Format as clickable
    formatted_text, tooltip_data = format_clickable_source(claim, provenance_info)
    
    console.print("[bold]Clickable Format:[/bold]")
    console.print(f"{formatted_text}\n")
    
    console.print("[bold]Tooltip Data (shown on click/hover):[/bold]")
    
    tooltip_table = Table(show_header=False, box=None, padding=(0, 2))
    tooltip_table.add_column("Field", style="cyan", width=25)
    tooltip_table.add_column("Value", style="white", width=55)
    
    if tooltip_data:
        tooltip_table.add_row("Source", tooltip_data.get("source", "N/A"))
        tooltip_table.add_row("Matching Passage", tooltip_data.get("passage", "N/A")[:50] + "...")
        tooltip_table.add_row("Overlap Ratio", f"{tooltip_data.get('overlap', 0):.2f}")
        tooltip_table.add_row("Semantic Similarity", f"{tooltip_data.get('semantic_similarity', 0):.2f}")
        
        breakdown = tooltip_data.get("relevance_breakdown", {})
        if breakdown:
            tooltip_table.add_row("Relevance Score", f"{breakdown.get('overall_score', 0):.2f}")
    
    console.print(tooltip_table)


async def demo_complete_workflow():
    """Demonstrate complete workflow from query to refinement."""
    console.print("\n" + "="*80)
    console.print(Panel.fit("[bold magenta]Demo 5: Complete User Workflow[/bold magenta]", border_style="magenta"))
    
    console.print("""
    [bold]User Journey:[/bold]
    
    1. [cyan]User asks:[/cyan] "What is d-separation?"
    2. [green]System responds:[/green] "D-separation is a graphical criterion..."
    3. [yellow]User sees:[/yellow] Source references with relevance scores
    4. [blue]User clicks:[/blue] On a claim to see source details
    5. [magenta]User explores:[/magenta] Uses query refinement suggestions
    6. [green]User verifies:[/green] Checks relevance breakdown to trust decision
    """)
    
    # Simulate the workflow
    agent = KnowledgeAgent(enable_quality_feedback=True)
    query = "What is d-separation?"
    
    try:
        response = await agent.chat(
            message=query,
            use_research=True,
        )
        
        if response.get("research_conducted"):
            research_data = response.get("research", {})
            provenance = research_data.get("provenance", {})
            refinement_suggestions = response.get("query_refinement_suggestions", [])
            
            console.print("\n[bold green]✓ Step 1-2: Query & Response[/bold green]")
            console.print(f"Response generated: {len(response.get('response', ''))} characters")
            
            if provenance:
                console.print(f"\n[bold green]✓ Step 3: Provenance Created[/bold green]")
                console.print(f"Claims with sources: {len(provenance)}")
                
                # Show relevance scores
                for claim, prov_info in list(provenance.items())[:1]:
                    sources = prov_info.get("sources", [])
                    if sources:
                        top_source = sources[0]
                        relevance = top_source.get("relevance_breakdown", {}).get("overall_score")
                        if relevance:
                            console.print(f"  Relevance score: {relevance:.2f}")
                
                console.print(f"\n[bold green]✓ Step 4: Clickable Sources Available[/bold green]")
                console.print("  (In Web UI, users can click to see tooltips)")
                
                if refinement_suggestions:
                    console.print(f"\n[bold green]✓ Step 5: Query Refinement Suggestions[/bold green]")
                    console.print(f"  {len(refinement_suggestions)} suggestions generated")
                    for i, suggestion in enumerate(refinement_suggestions[:2], 1):
                        console.print(f"  {i}. {suggestion['query']} ({suggestion['type']})")
                
                console.print(f"\n[bold green]✓ Step 6: Relevance Breakdowns Available[/bold green]")
                console.print("  (Users can verify why sources were selected)")
            else:
                console.print("\n[yellow]⚠ No provenance data (may need API keys)[/yellow]")
        else:
            console.print("\n[yellow]⚠ Research not conducted (may need API keys)[/yellow]")
            
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        console.print("[dim]Note: Full demo requires API keys for research[/dim]")


async def main():
    """Run all demos."""
    console.print("\n")
    console.print(Panel.fit(
        "[bold blue]Provenance Features: Qualitative User Experience Demo[/bold blue]\n\n"
        "This demo shows how provenance features improve the user experience\n"
        "through transparency, verifiability, and interactive exploration.",
        border_style="blue"
    ))
    
    await demo_basic_provenance()
    await demo_relevance_breakdowns()
    await demo_query_refinement()
    await demo_clickable_sources()
    await demo_complete_workflow()
    
    console.print("\n" + "="*80)
    console.print(Panel.fit(
        "[bold green]✓ All Provenance Features Demonstrated[/bold green]\n\n"
        "Key Improvements:\n"
        "• Transparency: See WHY sources were selected\n"
        "• Verifiability: Click to verify source passages\n"
        "• Exploration: Guided query refinement suggestions\n"
        "• Trust: Relevance scores help make informed decisions",
        border_style="green"
    ))


if __name__ == "__main__":
    asyncio.run(main())

