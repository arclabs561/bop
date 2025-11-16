"""Visualization helpers for knowledge display features."""

from typing import Dict, List, Any, Optional
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
import logging

logger = logging.getLogger(__name__)
console = Console()


def create_source_matrix_heatmap(
    source_matrix: Dict[str, Dict[str, Any]],
    max_claims: int = 10,
) -> Table:
    """
    Create a heatmap-style table showing source agreement/disagreement.
    
    Args:
        source_matrix: Source relationship matrix
        max_claims: Maximum number of claims to display
        
    Returns:
        Rich Table with heatmap visualization
    """
    if not source_matrix:
        return Table(title="Source Agreement Matrix (empty)")
    
    # Get top claims by number of sources
    claims = sorted(
        source_matrix.items(),
        key=lambda x: len(x[1].get("sources", {})),
        reverse=True
    )[:max_claims]
    
    if not claims:
        return Table(title="Source Agreement Matrix (empty)")
    
    # Collect all unique sources
    all_sources = set()
    for _, data in claims:
        all_sources.update(data.get("sources", {}).keys())
    all_sources = sorted(list(all_sources))
    
    # Create table
    table = Table(title="Source Agreement Matrix", show_header=True, header_style="bold cyan")
    table.add_column("Claim", style="cyan", width=40)
    
    for source in all_sources:
        table.add_column(source[:15], justify="center", width=12)
    
    table.add_column("Consensus", style="yellow", width=15)
    
    # Add rows
    for claim, data in claims:
        sources = data.get("sources", {})
        consensus = data.get("consensus", "unknown")
        
        # Truncate claim for display
        claim_display = claim[:37] + "..." if len(claim) > 40 else claim
        
        row = [claim_display]
        
        # Add source positions
        for source in all_sources:
            position = sources.get(source, "—")
            if position == "supports":
                cell = "[green]✓[/green]"
            elif position == "contradicts":
                cell = "[red]✗[/red]"
            elif position == "neutral":
                cell = "[yellow]○[/yellow]"
            else:
                cell = "[dim]—[/dim]"
            row.append(cell)
        
        # Add consensus
        consensus_display = consensus.replace("_", " ").title()
        if consensus == "strong_agreement":
            consensus_style = "[green]"
        elif consensus == "weak_agreement":
            consensus_style = "[yellow]"
        elif consensus == "disagreement":
            consensus_style = "[red]"
        else:
            consensus_style = "[dim]"
        row.append(f"{consensus_style}{consensus_display}[/{consensus_style}]")
        
        table.add_row(*row)
    
    return table


def create_trust_metrics_chart(
    trust_summary: Dict[str, Any],
    source_credibility: Optional[Dict[str, float]] = None,
) -> Panel:
    """
    Create a visual chart/panel for trust metrics.
    
    Args:
        trust_summary: Trust summary dictionary
        source_credibility: Optional source credibility mapping
        
    Returns:
        Rich Panel with trust metrics visualization
    """
    parts = []
    
    # Average trust (visual bar using characters)
    avg_trust = trust_summary.get("avg_trust", 0.5)
    trust_bar_length = int(avg_trust * 40)
    trust_bar = "█" * trust_bar_length + "░" * (40 - trust_bar_length)
    trust_color = "green" if avg_trust > 0.7 else "yellow" if avg_trust > 0.5 else "red"
    parts.append(f"Average Trust: [{trust_color}]{trust_bar}[/{trust_color}] {avg_trust:.3f}")
    
    # Credibility vs confidence
    avg_cred = trust_summary.get("avg_credibility", 0.5)
    avg_conf = trust_summary.get("avg_confidence", 0.5)
    cred_bar_length = int(avg_cred * 40)
    conf_bar_length = int(avg_conf * 40)
    cred_bar = "█" * cred_bar_length + "░" * (40 - cred_bar_length)
    conf_bar = "█" * conf_bar_length + "░" * (40 - conf_bar_length)
    parts.append(f"Source Credibility: [cyan]{cred_bar}[/cyan] {avg_cred:.3f}")
    parts.append(f"Structural Confidence: [blue]{conf_bar}[/blue] {avg_conf:.3f}")
    
    # Calibration error
    cal_error = trust_summary.get("calibration_error")
    if cal_error is not None:
        cal_style = "green" if cal_error < 0.1 else "yellow" if cal_error < 0.2 else "red"
        cal_bar_length = int((cal_error / 0.3) * 40)  # Scale to 0.3 max
        cal_bar = "█" * cal_bar_length + "░" * (40 - cal_bar_length)
        parts.append(f"Calibration Error: [{cal_style}]{cal_bar}[/{cal_style}] {cal_error:.3f}")
    
    # Source credibility breakdown
    if source_credibility:
        parts.append("\n**Per-Source Credibility:**")
        sorted_sources = sorted(source_credibility.items(), key=lambda x: x[1], reverse=True)
        for source, cred in sorted_sources[:5]:
            cred_bar_length = int(cred * 30)
            cred_bar = "█" * cred_bar_length + "░" * (30 - cred_bar_length)
            cred_color = "green" if cred > 0.7 else "yellow" if cred > 0.5 else "red"
            parts.append(f"  {source[:25]:25s} [{cred_color}]{cred_bar}[/{cred_color}] {cred:.2f}")
    
    return Panel("\n".join(parts), title="Trust Metrics", border_style="cyan")


def create_document_relationship_graph(
    cliques: List[Dict[str, Any]],
    max_cliques: int = 5,
) -> Table:
    """
    Create a table showing document relationship clusters.
    
    Args:
        cliques: List of clique detail dictionaries
        max_cliques: Maximum number of cliques to display
        
    Returns:
        Rich Table showing relationship clusters
    """
    if not cliques:
        return Table(title="Document Relationships (empty)")
    
    # Filter and sort cliques
    # Note: risk < 0.5 means low risk (good), so we want cliques with low risk
    trusted_cliques = [
        c for c in cliques
        if c.get("trust", 0) > 0.5 and c.get("risk", 1.0) < 0.5
    ]
    trusted_cliques.sort(key=lambda x: x.get("trust", 0), reverse=True)
    trusted_cliques = trusted_cliques[:max_cliques]
    
    table = Table(title="Document Relationship Clusters", show_header=True, header_style="bold magenta")
    table.add_column("Cluster", style="cyan", width=5)
    table.add_column("Sources", style="green", width=40)
    table.add_column("Trust", style="yellow", width=10)
    table.add_column("Coherence", style="blue", width=10)
    table.add_column("Size", style="dim", width=5)
    
    if not trusted_cliques:
        table.add_row("—", "No trusted clusters found", "—", "—", "—")
        return table
    
    for i, clique in enumerate(trusted_cliques, 1):
        sources = clique.get("node_sources", [])
        trust = clique.get("trust", 0)
        coherence = clique.get("coherence", 0)
        size = clique.get("size", len(sources) if sources else 0)
        
        # Format sources
        if sources:
            unique_sources = list(set(sources))[:5]
            sources_str = ", ".join(unique_sources)
            if len(set(sources)) > 5:
                sources_str += f" (+{len(set(sources)) - 5} more)"
        else:
            sources_str = "—"
        
        table.add_row(
            str(i),
            sources_str,
            f"{trust:.3f}",
            f"{coherence:.3f}",
            str(size),
        )
    
    return table


def create_token_importance_chart(
    importance_data: Dict[str, Any],
    max_terms: int = 15,
) -> Table:
    """
    Create a table/chart showing token importance scores.
    
    Args:
        importance_data: Output from token_importance.compute_token_importance_for_results
        max_terms: Maximum number of terms to display
        
    Returns:
        Rich Table with token importance visualization
    """
    if not importance_data or not importance_data.get("term_importance"):
        return Table(title="Token Importance (empty)")
    
    term_importance = importance_data["term_importance"]
    top_terms = importance_data.get("top_terms", [])[:max_terms]
    
    if not top_terms:
        return Table(title="Token Importance (no terms)")
    
    table = Table(title="Token Importance (Terms Driving Retrieval)", show_header=True, header_style="bold green")
    table.add_column("Rank", style="cyan", width=5)
    table.add_column("Term", style="green", width=20)
    table.add_column("Importance", style="yellow", width=30)
    table.add_column("Score", style="blue", width=8)
    
    for i, term in enumerate(top_terms, 1):
        score = term_importance.get(term, 0.0)
        # Create visual bar
        bar_length = int(score * 25)  # Scale to 25 chars
        bar = "█" * bar_length + "░" * (25 - bar_length)
        
        # Color based on score
        if score > 0.7:
            bar_style = "[green]"
        elif score > 0.4:
            bar_style = "[yellow]"
        else:
            bar_style = "[dim]"
        
        table.add_row(
            str(i),
            term,
            f"{bar_style}{bar}[/{bar_style}]",
            f"{score:.3f}",
        )
    
    return table

