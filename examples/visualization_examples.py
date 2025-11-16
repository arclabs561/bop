"""
Concrete examples of visualization improvements.

This script demonstrates the enhanced visualization features:
- Source matrix heatmaps
- Token importance charts
- Document relationship graphs
- Trust metrics charts
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import Dict, Any, List

console = Console()

def example_source_matrix():
    """Example: Source agreement matrix heatmap"""
    console.print("\n[bold yellow]Source Agreement Matrix[/bold yellow]")
    
    # Simulated source matrix data
    source_matrix = {
        "D-separation determines independence": {
            "consensus": "strong_agreement",
            "sources": {
                "arXiv:2401.12345": "agree",
                "Wikipedia": "agree",
                "Research Paper": "agree",
            },
            "agreement_score": 0.95,
        },
        "Bayesian networks use DAGs": {
            "consensus": "strong_agreement",
            "sources": {
                "arXiv:2401.12345": "agree",
                "Wikipedia": "agree",
                "Research Paper": "agree",
                "Blog Post": "agree",
            },
            "agreement_score": 1.0,
        },
        "Colliders block paths": {
            "consensus": "moderate_agreement",
            "sources": {
                "arXiv:2401.12345": "agree",
                "Wikipedia": "disagree",
            },
            "agreement_score": 0.5,
        },
    }
    
    table = Table(show_header=True, header_style="bold")
    table.add_column("Claim", style="cyan", width=40)
    table.add_column("Consensus", style="green")
    table.add_column("Agreement", style="yellow")
    table.add_column("Sources", style="dim")
    
    for claim, data in list(source_matrix.items())[:5]:
        consensus = data["consensus"]
        score = data["agreement_score"]
        source_count = len(data["sources"])
        
        # Visual indicator
        if consensus == "strong_agreement":
            indicator = "🟢 Strong"
        elif consensus == "moderate_agreement":
            indicator = "🟡 Moderate"
        else:
            indicator = "🔴 Weak"
        
        # Agreement bar
        bar_length = int(score * 20)
        bar = "█" * bar_length + "░" * (20 - bar_length)
        
        table.add_row(
            claim[:38] + "..." if len(claim) > 40 else claim,
            indicator,
            f"[green]{bar}[/green] {score:.2f}",
            f"{source_count} sources"
        )
    
    console.print(table)


def example_token_importance():
    """Example: Token importance chart"""
    console.print("\n[bold yellow]Token Importance[/bold yellow]")
    
    # Simulated token importance data
    term_importance = {
        "d-separation": 0.95,
        "bayesian": 0.87,
        "independence": 0.82,
        "graph": 0.75,
        "causal": 0.68,
        "networks": 0.65,
        "conditional": 0.62,
        "variables": 0.58,
    }
    
    table = Table(show_header=True, header_style="bold")
    table.add_column("Term", style="cyan", width=20)
    table.add_column("Importance", style="green", width=35)
    table.add_column("Score", style="yellow")
    
    for term, importance in sorted(term_importance.items(), key=lambda x: x[1], reverse=True)[:8]:
        bar_length = int(importance * 30)
        bar = "█" * bar_length + "░" * (30 - bar_length)
        color = "green" if importance > 0.7 else "yellow" if importance > 0.5 else "red"
        table.add_row(term, f"[{color}]{bar}[/{color}]", f"{importance:.2f}")
    
    console.print(table)


def example_document_relationships():
    """Example: Document relationship graph"""
    console.print("\n[bold yellow]Document Relationships[/bold yellow]")
    
    # Simulated clique data
    cliques = [
        {
            "sources": ["arXiv:2401.12345", "arXiv:2402.23456", "Research Paper"],
            "trust": 0.82,
            "diversity": 3,
            "verifications": 7,
            "size": 3,
        },
        {
            "sources": ["Wikipedia", "Blog Post"],
            "trust": 0.65,
            "diversity": 2,
            "verifications": 3,
            "size": 2,
        },
    ]
    
    table = Table(show_header=True, header_style="bold")
    table.add_column("Cluster", style="cyan")
    table.add_column("Trust", style="green")
    table.add_column("Size", style="yellow")
    table.add_column("Diversity", style="blue")
    table.add_column("Sources", style="dim")
    
    for i, clique in enumerate(cliques, 1):
        trust = clique["trust"]
        trust_emoji = "🟢" if trust > 0.7 else "🟡" if trust > 0.5 else "🔴"
        sources_str = ", ".join(clique["sources"][:2])
        if len(clique["sources"]) > 2:
            sources_str += f" (+{len(clique['sources']) - 2} more)"
        
        table.add_row(
            f"Cluster {i}",
            f"{trust_emoji} {trust:.2f}",
            str(clique["size"]),
            str(clique["diversity"]),
            sources_str
        )
    
    console.print(table)


def example_trust_metrics():
    """Example: Trust metrics chart"""
    console.print("\n[bold magenta]📊 Trust & Uncertainty Metrics[/bold magenta]")
    console.print("="*80)
    
    # Trust summary
    trust_summary = {
        "avg_trust": 0.75,
        "avg_credibility": 0.72,
        "avg_confidence": 0.68,
        "calibration_error": 0.12,
    }
    
    # Average trust
    avg_trust = trust_summary["avg_trust"]
    trust_bar_length = int(avg_trust * 40)
    trust_bar = "█" * trust_bar_length + "░" * (40 - trust_bar_length)
    trust_color = "green" if avg_trust > 0.7 else "yellow" if avg_trust > 0.5 else "red"
    console.print(f"\nAverage Trust: [{trust_color}]{trust_bar}[/{trust_color}] {avg_trust:.3f}")
    
    # Credibility
    avg_cred = trust_summary["avg_credibility"]
    cred_bar_length = int(avg_cred * 40)
    cred_bar = "█" * cred_bar_length + "░" * (40 - cred_bar_length)
    console.print(f"Source Credibility: [cyan]{cred_bar}[/cyan] {avg_cred:.3f}")
    
    # Confidence
    avg_conf = trust_summary["avg_confidence"]
    conf_bar_length = int(avg_conf * 40)
    conf_bar = "█" * conf_bar_length + "░" * (40 - conf_bar_length)
    console.print(f"Structural Confidence: [blue]{conf_bar}[/blue] {avg_conf:.3f}")
    
    # Calibration error
    cal_error = trust_summary["calibration_error"]
    cal_style = "green" if cal_error < 0.1 else "yellow" if cal_error < 0.2 else "red"
    cal_bar_length = int((cal_error / 0.3) * 40)
    cal_bar = "█" * cal_bar_length + "░" * (40 - cal_bar_length)
    console.print(f"Calibration Error: [{cal_style}]{cal_bar}[/{cal_style}] {cal_error:.3f}")


if __name__ == "__main__":
    console.print(Panel.fit("[bold blue]Visualization Examples[/bold blue]", border_style="blue"))
    console.print("\nDemonstrating enhanced visualization features:\n")
    
    example_trust_metrics()
    example_source_matrix()
    example_token_importance()
    example_document_relationships()
    
    console.print("\n" + "="*80)
    console.print("[bold green]✅ All visualization examples displayed[/bold green]")
    console.print("="*80)

