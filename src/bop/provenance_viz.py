"""Visualization helpers for provenance data."""

from typing import Any, Dict, Tuple

from rich.console import Console
from rich.table import Table

console = Console()


def create_provenance_heatmap(
    provenance_data: Dict[str, Any],
    max_claims: int = 5,
) -> Table:
    """
    Create a heatmap showing token matches between query and documents.

    Enhanced with:
    - Relevance score display
    - Better claim prioritization
    - More informative token display

    Shows which query tokens matched which document tokens for each claim.
    """
    table = Table(
        title="Token-Level Provenance",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Claim", style="yellow", width=35)
    table.add_column("Relevance", style="green", width=10)
    table.add_column("Query Tokens", style="cyan", width=18)
    table.add_column("Matched Tokens", style="blue", width=25)
    table.add_column("Sources", style="magenta", width=12)

    if not provenance_data:
        table.add_row("No provenance data", "", "", "", "")
        return table

    # Get top claims by combined quality and relevance
    def get_claim_sort_key(item):
        claim_text, prov_info = item
        quality = prov_info.get("quality_score", 0.5)
        relevance = prov_info.get("top_source_relevance", 0.0)
        num_sources = prov_info.get("num_sources", 0)
        # Sort by: relevance first, then quality, then source count
        return (relevance, quality, num_sources)

    sorted_claims = sorted(
        provenance_data.items(),
        key=get_claim_sort_key,
        reverse=True
    )[:max_claims]

    for claim_text, provenance_info in sorted_claims:
        claim_short = claim_text[:50] + "..." if len(claim_text) > 50 else claim_text
        sources = provenance_info.get("sources", [])

        if not sources:
            continue

        top_source = sources[0]
        token_matches = top_source.get("token_matches", {})
        relevance_breakdown = top_source.get("relevance_breakdown", {})

        # Get relevance score
        relevance_score = None
        if relevance_breakdown:
            relevance_score = relevance_breakdown.get("overall_score")
        else:
            relevance_score = top_source.get("overlap_ratio", 0.0)

        # Format relevance with color indicator
        if relevance_score is not None:
            if relevance_score > 0.7:
                relevance_str = f"[green]{relevance_score:.2f}[/green]"
            elif relevance_score > 0.5:
                relevance_str = f"[yellow]{relevance_score:.2f}[/yellow]"
            else:
                relevance_str = f"[red]{relevance_score:.2f}[/red]"
        else:
            relevance_str = "N/A"

        # Extract query tokens and their matches
        query_tokens = list(token_matches.keys())[:4]  # Top 4 query tokens
        if not query_tokens:
            query_tokens_str = "[dim]None[/dim]"
            doc_tokens_str = "[dim]None[/dim]"
        else:
            query_tokens_str = ", ".join(query_tokens[:3])
            if len(query_tokens) > 3:
                query_tokens_str += "..."

            # Get matched document tokens with scores
            all_doc_tokens = []
            for q_token in query_tokens[:3]:
                matches = token_matches.get(q_token, [])
                if matches:
                    # Get top match
                    doc_token, score = matches[0]
                    # Format with color based on score
                    if score > 0.9:
                        token_display = f"[green]{doc_token}[/green]"
                    elif score > 0.7:
                        token_display = f"[yellow]{doc_token}[/yellow]"
                    else:
                        token_display = doc_token
                    all_doc_tokens.append(token_display)

            doc_tokens_str = ", ".join(all_doc_tokens) if all_doc_tokens else "[dim]No matches[/dim]"

        # Source count
        num_sources = provenance_info.get("num_sources", 0)
        source_str = f"{num_sources}" if num_sources > 0 else "[dim]0[/dim]"

        table.add_row(
            claim_short,
            relevance_str,
            query_tokens_str,
            doc_tokens_str,
            source_str,
        )

    return table


def format_clickable_source(
    claim: str,
    provenance_info: Dict[str, Any],
) -> Tuple[str, Dict[str, Any]]:
    """
    Format a claim with clickable source information for Web UI.

    Enhanced with:
    - Relevance score in display
    - Better tooltip organization
    - Multiple source support

    Returns tuple of (formatted_text, tooltip_data) for interactive display.
    """
    sources = provenance_info.get("sources", [])
    if not sources:
        return claim, {}

    top_source = sources[0]
    source_name = top_source.get("source", "unknown")
    passage = top_source.get("matching_passage", "")
    overlap = top_source.get("overlap_ratio", 0)
    relevance_breakdown = top_source.get("relevance_breakdown", {})
    semantic_similarity = top_source.get("semantic_similarity", 0.0)

    # Get relevance score for display
    relevance_score = None
    if relevance_breakdown:
        relevance_score = relevance_breakdown.get("overall_score")
    elif overlap:
        relevance_score = overlap

    # Create clickable reference with relevance indicator
    # In Web UI, this can be made interactive with JavaScript
    if relevance_score is not None:
        # Add relevance indicator
        if relevance_score > 0.7:
            relevance_indicator = "🟢"
        elif relevance_score > 0.5:
            relevance_indicator = "🟡"
        else:
            relevance_indicator = "🔴"

        source_ref = f"[{relevance_indicator} {source_name}](provenance:{claim[:50]})"
    else:
        source_ref = f"[{source_name}](provenance:{claim[:50]})"

    formatted = f"{claim} {source_ref}"

    # Enhanced tooltip data with better organization
    tooltip_data = {
        "source": source_name,
        "passage": passage[:300],  # Longer passage for better context
        "overlap": overlap,
        "semantic_similarity": semantic_similarity,
        "relevance_breakdown": relevance_breakdown,
        "token_matches": top_source.get("token_matches", {}),
        "num_sources": len(sources),
        "all_sources": [s.get("source", "unknown") for s in sources[:3]],  # Top 3 sources
    }

    return formatted, tooltip_data


def create_relevance_breakdown_display(
    relevance_breakdown: Dict[str, Any],
) -> str:
    """
    Create a formatted display of relevance score breakdown.

    Returns markdown-formatted string showing why source was selected.
    """
    if not relevance_breakdown:
        return "No relevance breakdown available."

    overall_score = relevance_breakdown.get("overall_score", 0.0)
    components = relevance_breakdown.get("components", {})
    explanation = relevance_breakdown.get("explanation", "")
    top_tokens = relevance_breakdown.get("top_token_matches", [])

    lines = [
        f"**Relevance Score: {overall_score:.2f}**",
        "",
        "**Components:**",
        f"- Word Overlap: {components.get('word_overlap', 0):.2f}",
        f"- Semantic Similarity: {components.get('semantic_similarity', 0):.2f}",
        f"- Token Match Average: {components.get('token_match_avg', 0):.2f}",
    ]

    if top_tokens:
        lines.append("")
        lines.append("**Top Token Matches:**")
        for token, score in top_tokens[:5]:
            lines.append(f"- `{token}`: {score:.2f}")

    if explanation:
        lines.append("")
        lines.append(f"**Explanation:** {explanation}")

    return "\n".join(lines)


def create_provenance_summary(
    provenance_data: Dict[str, Any],
) -> str:
    """Create a text summary of provenance information."""
    if not provenance_data:
        return "No provenance data available."

    total_claims = len(provenance_data)
    claims_with_sources = sum(1 for p in provenance_data.values() if p.get("num_sources", 0) > 0)

    summary = "**Provenance Summary:**\n"
    summary += f"- Total claims analyzed: {total_claims}\n"
    summary += f"- Claims with source matches: {claims_with_sources}\n"

    # Show top sources
    all_sources = set()
    for provenance_info in provenance_data.values():
        sources = provenance_info.get("sources", [])
        for source_info in sources:
            all_sources.add(source_info.get("source", "unknown"))

    if all_sources:
        summary += f"- Unique sources: {len(all_sources)}\n"
        summary += f"- Sources: {', '.join(list(all_sources)[:5])}\n"

    return summary

