"""Qualitative examples showing provenance user experience improvements.

This script demonstrates how provenance features improve the user experience
through concrete examples and scenarios.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

console = Console()


def show_before_after_comparison():
    """Show before/after comparison of provenance features."""
    console.print(Panel.fit("[bold blue]Before vs. After: Provenance Features[/bold blue]", border_style="blue"))
    
    console.print("\n[bold red]BEFORE:[/bold red]")
    console.print("""
    User asks: "What is d-separation?"
    
    Response:
    "D-separation is a graphical criterion for determining conditional independence.
    It helps identify when variables are conditionally independent."
    
    Sources:
    - perplexity_deep_research
    
    ❌ Problems:
    - No explanation of WHY this source was selected
    - Can't verify if source actually supports the claim
    - No way to explore related concepts
    - No transparency into matching logic
    """)
    
    console.print("\n[bold green]AFTER:[/bold green]")
    console.print("""
    User asks: "What is d-separation?"
    
    Response:
    "D-separation is a graphical criterion for determining conditional independence.
    It helps identify when variables are conditionally independent."
    
    Sources:
    - D-separation is a graphical criterion [perplexity_deep_research] (Relevance: 0.78)
      ↳ Click to see: source passage, token matches, relevance breakdown
    
    ✅ Improvements:
    - Relevance score shows WHY source was selected (0.78 = strong match)
    - Clickable sources show matching passage and token-level details
    - Query refinement suggests: "Explain graphical criterion in detail"
    - Transparency: See word overlap (65%), semantic similarity (72%), token matches
    """)


def show_relevance_breakdown_example():
    """Show example of relevance breakdown display."""
    console.print("\n" + "="*80)
    console.print(Panel.fit("[bold cyan]Relevance Score Breakdown Example[/bold cyan]", border_style="cyan"))
    
    table = Table(title="Why was this source selected?", show_header=True, header_style="bold magenta")
    table.add_column("Component", style="yellow", width=30)
    table.add_column("Score", justify="right", style="green")
    table.add_column("Interpretation", style="blue", width=40)
    
    table.add_row("Word Overlap", "0.65", "65% of claim words appear in source")
    table.add_row("Semantic Similarity", "0.72", "Strong conceptual alignment")
    table.add_row("Token Match Average", "0.85", "Excellent token-level matching")
    table.add_row("", "", "")
    table.add_row("[bold]Overall Relevance[/bold]", "[bold green]0.74[/bold green]", "[bold]Strong match - source is highly relevant[/bold]")
    
    console.print(table)
    
    console.print("\n[dim]Explanation:[/dim]")
    console.print("High word overlap (65.0%). Strong semantic similarity (72.0%). ")
    console.print("Key token matches: d-separation(0.95), graphical(0.90), criterion(0.88).")


def show_query_refinement_example():
    """Show example of query refinement suggestions."""
    console.print("\n" + "="*80)
    console.print(Panel.fit("[bold green]Query Refinement Example[/bold green]", border_style="green"))
    
    console.print("\n[bold]Original Query:[/bold] \"What is d-separation?\"\n")
    
    suggestions_table = Table(show_header=True, header_style="bold magenta")
    suggestions_table.add_column("Suggestion", style="cyan", width=50)
    suggestions_table.add_column("Type", style="yellow", width=20)
    suggestions_table.add_column("Why Suggested", style="blue", width=40)
    
    suggestions_table.add_row(
        "Explain d-separation, graphical, criterion in detail",
        "deep_dive",
        "Key concepts that matched this claim"
    )
    suggestions_table.add_row(
        "What do other sources say about d-separation?",
        "alternative",
        "Multiple sources available for comparison"
    )
    suggestions_table.add_row(
        "What concepts are related to d-separation?",
        "related",
        "High semantic similarity suggests related topics"
    )
    
    console.print(suggestions_table)
    
    console.print("\n[dim]User Experience:[/dim]")
    console.print("Instead of guessing what to ask next, users get guided suggestions")
    console.print("based on what the system actually found. This enables iterative")
    console.print("exploration and deeper understanding.")


def show_clickable_sources_example():
    """Show example of clickable source interaction."""
    console.print("\n" + "="*80)
    console.print(Panel.fit("[bold yellow]Clickable Sources Example[/bold yellow]", border_style="yellow"))
    
    console.print("\n[bold]Response Text:[/bold]")
    console.print("""
    D-separation is a graphical criterion for determining conditional independence.
    It helps identify when variables are conditionally independent.
    """)
    
    console.print("\n[bold]Interactive Source Reference:[/bold]")
    console.print("""
    D-separation is a graphical criterion [perplexity_deep_research] ← Click here
    """)
    
    console.print("\n[bold]On Click/Hover, User Sees:[/bold]")
    
    tooltip_table = Table(show_header=False, box=None, padding=(0, 2))
    tooltip_table.add_column("Field", style="cyan", width=25)
    tooltip_table.add_column("Value", style="white", width=50)
    
    tooltip_table.add_row("Source", "perplexity_deep_research")
    tooltip_table.add_row("Matching Passage", "D-separation is a graphical criterion for determining conditional independence in directed acyclic graphs.")
    tooltip_table.add_row("Overlap Ratio", "0.65 (65% word overlap)")
    tooltip_table.add_row("Semantic Similarity", "0.72 (strong conceptual match)")
    tooltip_table.add_row("Token Matches", "d-separation(0.95), graphical(0.90), criterion(0.88)")
    tooltip_table.add_row("Relevance Score", "0.74 (strong match)")
    
    console.print(tooltip_table)
    
    console.print("\n[dim]User Experience:[/dim]")
    console.print("Users can verify sources without leaving the conversation context.")
    console.print("This builds trust through transparency and enables fact-checking.")


def show_progressive_disclosure_example():
    """Show example of progressive disclosure with provenance."""
    console.print("\n" + "="*80)
    console.print(Panel.fit("[bold magenta]Progressive Disclosure with Provenance[/bold magenta]", border_style="magenta"))
    
    console.print("\n[bold]Level 1: Summary (Default View)[/bold]")
    console.print("[dim]D-separation determines conditional independence in graphs.[/dim]")
    console.print("[dim]Sources: 1 | Relevance: 0.74[/dim]")
    
    console.print("\n[bold]Level 2: Detailed (Click to Expand)[/bold]")
    console.print("""
    D-separation is a graphical criterion for determining conditional independence
    in directed acyclic graphs. It helps identify when variables are conditionally
    independent given a set of conditioning variables.
    
    Sources:
    - D-separation is a graphical criterion [perplexity_deep_research] (0.74)
    """)
    
    console.print("\n[bold]Level 3: Evidence (Full Provenance)[/bold]")
    console.print("""
    [Full response text]
    
    Provenance Details:
    - Token-level matches: d-separation(0.95), graphical(0.90)
    - Relevance breakdown: Word overlap 65%, Semantic 72%, Tokens 85%
    - Source passage: "D-separation is a graphical criterion for determining..."
    
    Query Refinement:
    1. Explain d-separation, graphical, criterion in detail
    2. What do other sources say about d-separation?
    """)


def show_trust_building_example():
    """Show how provenance builds trust."""
    console.print("\n" + "="*80)
    console.print(Panel.fit("[bold green]How Provenance Builds Trust[/bold green]", border_style="green"))
    
    trust_points = [
        ("Transparency", "Users see WHY sources were selected, not just citations"),
        ("Verifiability", "Click any claim to see the exact source passage"),
        ("Token-Level Detail", "See which query words matched which document words"),
        ("Relevance Scores", "Understand match quality (high = good, low = weak)"),
        ("Query Refinement", "Get suggestions based on what was actually found"),
    ]
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Trust Factor", style="cyan", width=25)
    table.add_column("How Provenance Helps", style="white", width=55)
    
    for factor, explanation in trust_points:
        table.add_row(factor, explanation)
    
    console.print(table)
    
    console.print("\n[dim]Before:[/dim] \"Why should I trust this?\"")
    console.print("[bold green]After:[/bold green] \"I can see exactly why this source was selected and verify it myself.\"")


def main():
    """Run all qualitative examples."""
    console.print("\n")
    show_before_after_comparison()
    show_relevance_breakdown_example()
    show_query_refinement_example()
    show_clickable_sources_example()
    show_progressive_disclosure_example()
    show_trust_building_example()
    
    console.print("\n" + "="*80)
    console.print(Panel.fit(
        "[bold green]✓ Provenance Features Transform User Experience[/bold green]\n\n"
        "From opaque citations to transparent, verifiable, interactive exploration.",
        border_style="green"
    ))


if __name__ == "__main__":
    main()

