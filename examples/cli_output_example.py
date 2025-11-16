"""
Concrete examples of CLI output improvements.

This script demonstrates the enhanced TUI features:
- Visual separators (═, ─)
- Emoji indicators (🟢🟡🔴)
- Progress bars
- Enhanced color coding
- Better section organization
"""

from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from rich.panel import Panel

console = Console()

def example_trust_metrics():
    """Example: Trust & Uncertainty Metrics display"""
    console.print("\n" + "="*80)
    console.print("[bold magenta]📊 Trust & Uncertainty Metrics[/bold magenta]")
    console.print("="*80)
    
    # Trust chart with progress bars
    avg_trust = 0.75
    trust_bar_length = int(avg_trust * 40)
    trust_bar = "█" * trust_bar_length + "░" * (40 - trust_bar_length)
    console.print(f"\nAverage Trust: [green]{trust_bar}[/green] {avg_trust:.3f}")
    
    # Source credibility with bars
    console.print("\n[bold cyan]📚 Source Credibility[/bold cyan]")
    sources = [
        ("arXiv:2401.12345", 0.85),
        ("Wikipedia", 0.72),
        ("Research Paper", 0.68),
        ("Blog Post", 0.45),
    ]
    for source, cred in sources:
        color = "green" if cred > 0.7 else "yellow" if cred > 0.5 else "red"
        bar_length = int(cred * 20)
        bar = "█" * bar_length + "░" * (20 - bar_length)
        console.print(f"  [{color}]{bar}[/{color}] {source[:30]:30s} {cred:.3f}")
    
    # Verification info with emojis
    console.print("\n[bold cyan]✅ Source Verification & Diversity[/bold cyan]")
    verifications = [
        ("arXiv:2401.12345", 5, 3),
        ("Wikipedia", 3, 2),
        ("Research Paper", 2, 1),
    ]
    for source, verif_count, nodes in verifications:
        diversity_emoji = "🟢" if nodes >= 3 else "🟡" if nodes >= 2 else "🔴"
        console.print(f"  {diversity_emoji} {source[:30]:30s} {verif_count} verifications, {nodes} nodes")
    
    # Clique clusters
    console.print("\n[bold cyan]🔗 Source Agreement Clusters[/bold cyan]")
    cliques = [
        {"trust": 0.82, "sources": ["arXiv:2401.12345", "arXiv:2402.23456"], "diversity": 3, "verifications": 7},
        {"trust": 0.65, "sources": ["Wikipedia", "Blog Post"], "diversity": 2, "verifications": 3},
    ]
    for i, clique in enumerate(cliques, 1):
        trust = clique["trust"]
        trust_emoji = "🟢" if trust > 0.7 else "🟡" if trust > 0.5 else "🔴"
        console.print(f"  {trust_emoji} Cluster {i}: {len(clique['sources'])} sources agree ({', '.join(clique['sources'][:2])})")
        console.print(f"     Trust: {trust:.3f} | Diversity: {clique['diversity']} | Verifications: {clique['verifications']}")


def example_progressive_disclosure():
    """Example: Progressive disclosure (summary vs full)"""
    console.print("\n" + "─"*80)
    console.print("[bold cyan]📋 Summary[/bold cyan]")
    console.print("─"*80)
    console.print(Markdown(
        "D-separation is a graphical criterion for determining conditional independence "
        "in Bayesian networks. It provides a way to read independence relationships "
        "directly from the graph structure."
    ))
    console.print("\n[dim italic]💡 Tip: Use [bold]--show-details[/bold] to see full response with all details[/dim italic]")
    
    console.print("\n" + "="*80)
    console.print("[bold cyan]📖 Full Response[/bold cyan]")
    console.print("="*80)
    console.print(Markdown(
        """# D-Separation

D-separation is a fundamental concept in causal inference and Bayesian networks. 
It provides a graphical criterion for determining conditional independence relationships.

## Key Concepts

1. **Paths**: A path between two nodes in a directed acyclic graph (DAG)
2. **Blocking**: A path is blocked if it contains a collider or a non-collider in the conditioning set
3. **D-separation**: Two nodes are d-separated if all paths between them are blocked

## Applications

- Causal inference
- Bayesian network analysis
- Structural equation modeling

## Sources

- Pearl (2009) - Causality
- Spirtes et al. (2000) - Causation, Prediction, and Search"""
    ))


def example_quality_score():
    """Example: Quality score with visual bar"""
    console.print("\n" + "─"*80)
    console.print("[bold]🟢 Quality Score:[/bold] [green]████████████████████████████░░░░[/green] 0.850")
    
    console.print("\n[bold]🟡 Quality Score:[/bold] [yellow]████████████████████░░░░░░░░░░[/yellow] 0.550")
    
    console.print("\n[bold]🔴 Quality Score:[/bold] [red]████████████░░░░░░░░░░░░░░░░░░[/red] 0.350")


def example_visualizations():
    """Example: Knowledge visualizations section"""
    console.print("\n" + "="*80)
    console.print("[bold green]📈 Knowledge Visualizations[/bold green]")
    console.print("="*80)
    
    # Source matrix
    console.print("\n[bold yellow]Source Agreement Matrix[/bold yellow]")
    table = Table(show_header=True, header_style="bold")
    table.add_column("Claim", style="cyan")
    table.add_column("Consensus", style="green")
    table.add_column("Sources", style="dim")
    
    table.add_row("D-separation determines independence", "🟢 Strong", "3 sources")
    table.add_row("Bayesian networks use DAGs", "🟢 Strong", "4 sources")
    table.add_row("Colliders block paths", "🟡 Moderate", "2 sources")
    
    console.print(table)
    
    # Token importance
    console.print("\n[bold yellow]Token Importance[/bold yellow]")
    table = Table(show_header=True, header_style="bold")
    table.add_column("Term", style="cyan")
    table.add_column("Importance", style="green")
    
    terms = [
        ("d-separation", 0.95),
        ("bayesian", 0.87),
        ("independence", 0.82),
        ("graph", 0.75),
        ("causal", 0.68),
    ]
    for term, importance in terms:
        bar_length = int(importance * 30)
        bar = "█" * bar_length + "░" * (30 - bar_length)
        table.add_row(term, f"[green]{bar}[/green] {importance:.2f}")
    
    console.print(table)
    
    # Document relationships
    console.print("\n[bold yellow]Document Relationships[/bold yellow]")
    table = Table(show_header=True, header_style="bold")
    table.add_column("Cluster", style="cyan")
    table.add_column("Trust", style="green")
    table.add_column("Sources", style="dim")
    
    table.add_row("Cluster 1", "🟢 0.82", "arXiv:2401.12345, arXiv:2402.23456")
    table.add_row("Cluster 2", "🟡 0.65", "Wikipedia, Blog Post")
    
    console.print(table)


def example_belief_alignment():
    """Example: Belief-evidence alignment"""
    console.print("\n" + "─"*80)
    console.print("[bold blue]🧠 Belief-Evidence Alignment[/bold blue]")
    console.print("─"*80)
    console.print("  📌 [italic]Your belief:[/italic] \"Trust is crucial for knowledge systems...\"")
    console.print("  📌 [italic]Your belief:[/italic] \"Uncertainty affects decision making...\"")
    console.print("  [dim]Evidence alignment computed based on your stated beliefs[/dim]")


if __name__ == "__main__":
    console.print(Panel.fit("[bold blue]BOP CLI Output Examples[/bold blue]", border_style="blue"))
    console.print("\nThese examples demonstrate the enhanced TUI features:\n")
    
    example_progressive_disclosure()
    example_trust_metrics()
    example_quality_score()
    example_visualizations()
    example_belief_alignment()
    
    console.print("\n" + "="*80)
    console.print("[bold green]✅ All examples displayed[/bold green]")
    console.print("="*80)

