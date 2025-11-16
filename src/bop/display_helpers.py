"""Helper functions for formatting and displaying knowledge information."""

from typing import Dict, Any, List, Optional
from rich.table import Table
from rich.console import Console

console = Console()


def format_trust_summary(trust_summary: Dict[str, Any]) -> str:
    """
    Format trust summary with explanations.
    
    Args:
        trust_summary: Trust summary dictionary from topology
        
    Returns:
        Formatted string with trust metrics and explanations
    """
    if not trust_summary:
        return ""
    
    parts = []
    
    # Average trust
    avg_trust = trust_summary.get("avg_trust", 0.5)
    trust_level = "high" if avg_trust > 0.7 else "medium" if avg_trust > 0.5 else "low"
    parts.append(f"**Average Trust**: {avg_trust:.2f} ({trust_level})")
    
    # Credibility vs confidence
    avg_cred = trust_summary.get("avg_credibility", 0.5)
    avg_conf = trust_summary.get("avg_confidence", 0.5)
    parts.append(f"**Source Credibility**: {avg_cred:.2f} | **Structural Confidence**: {avg_conf:.2f}")
    
    # Edge trust distribution
    high_trust = trust_summary.get("high_trust_edges", 0)
    low_trust = trust_summary.get("low_trust_edges", 0)
    if high_trust > 0 or low_trust > 0:
        parts.append(f"**Trust Distribution**: {high_trust} high-trust connections, {low_trust} low-trust connections")
    
    # Calibration error with explanation
    cal_error = trust_summary.get("calibration_error")
    if cal_error is not None:
        cal_level = "excellent" if cal_error < 0.1 else "good" if cal_error < 0.2 else "needs improvement"
        parts.append(
            f"**Calibration Error**: {cal_error:.3f} ({cal_level}) - "
            f"This measures how well confidence scores match actual accuracy. "
            f"Lower is better (ideal < 0.1)."
        )
    
    # Schema violations
    violations = trust_summary.get("schema_violations", 0)
    if violations > 0:
        parts.append(f"⚠️ **Schema Violations**: {violations} potential inconsistencies detected")
    
    return "\n".join(parts)


def format_source_credibility(source_credibility: Dict[str, float]) -> str:
    """
    Format source credibility scores.
    
    Args:
        source_credibility: Dictionary mapping source names to credibility scores
        
    Returns:
        Formatted string showing source credibility
    """
    if not source_credibility:
        return ""
    
    parts = ["**Source Credibility Scores:**"]
    
    # Sort by credibility (highest first)
    sorted_sources = sorted(
        source_credibility.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    for source, cred in sorted_sources:
        level = "high" if cred > 0.7 else "medium" if cred > 0.5 else "low"
        parts.append(f"  - {source}: {cred:.2f} ({level})")
    
    return "\n".join(parts)


def format_clique_clusters(cliques: List[Dict[str, Any]], max_display: int = 5) -> str:
    """
    Format clique clusters as source agreement groups.
    
    Args:
        cliques: List of clique detail dictionaries
        max_display: Maximum number of cliques to display
        
    Returns:
        Formatted string showing source clusters
    """
    if not cliques:
        return ""
    
    parts = ["**Source Clusters (Agreement Groups):**"]
    
    # Filter and sort by trust score
    trusted_cliques = [
        c for c in cliques 
        if c.get("trust", 0) > 0.5 and c.get("risk", 1.0) < 0.5
    ]
    trusted_cliques.sort(key=lambda x: x.get("trust", 0), reverse=True)
    
    for i, clique in enumerate(trusted_cliques[:max_display]):
        sources = clique.get("node_sources", [])
        trust = clique.get("trust", 0)
        coherence = clique.get("coherence", 0)
        size = clique.get("size", 0)
        
        if sources:
            # Get unique sources
            unique_sources = list(set(sources))
            source_str = ", ".join(unique_sources[:3])
            if len(unique_sources) > 3:
                source_str += f" (+{len(unique_sources) - 3} more)"
            
            parts.append(
                f"  {i+1}. **{size} sources agree** ({source_str}) - "
                f"Trust: {trust:.2f}, Coherence: {coherence:.2f}"
            )
    
    return "\n".join(parts)


def create_trust_table(trust_summary: Dict[str, Any], source_credibility: Optional[Dict[str, float]] = None) -> Table:
    """
    Create a Rich table for trust metrics.
    
    Args:
        trust_summary: Trust summary dictionary
        source_credibility: Optional source credibility mapping
        
    Returns:
        Rich Table object
    """
    table = Table(title="Trust Metrics", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Interpretation", style="dim")
    
    # Average trust
    avg_trust = trust_summary.get("avg_trust", 0.5)
    trust_level = "High" if avg_trust > 0.7 else "Medium" if avg_trust > 0.5 else "Low"
    table.add_row("Average Trust", f"{avg_trust:.3f}", trust_level)
    
    # Credibility
    avg_cred = trust_summary.get("avg_credibility", 0.5)
    cred_level = "High" if avg_cred > 0.7 else "Medium" if avg_cred > 0.5 else "Low"
    table.add_row("Source Credibility", f"{avg_cred:.3f}", cred_level)
    
    # Confidence
    avg_conf = trust_summary.get("avg_confidence", 0.5)
    conf_level = "High" if avg_conf > 0.7 else "Medium" if avg_conf > 0.5 else "Low"
    table.add_row("Structural Confidence", f"{avg_conf:.3f}", conf_level)
    
    # Calibration error
    cal_error = trust_summary.get("calibration_error")
    if cal_error is not None:
        cal_level = "Excellent" if cal_error < 0.1 else "Good" if cal_error < 0.2 else "Needs Improvement"
        table.add_row("Calibration Error", f"{cal_error:.3f}", cal_level)
    
    # Edge distribution
    high_trust = trust_summary.get("high_trust_edges", 0)
    low_trust = trust_summary.get("low_trust_edges", 0)
    table.add_row("High-Trust Connections", str(high_trust), f"{low_trust} low-trust")
    
    return table

