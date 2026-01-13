"""Query refinement based on provenance data.

Enables interactive exploration by suggesting follow-up queries
based on provenance information.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def suggest_followup_queries(
    claim: str,
    provenance_info: Dict[str, Any],
    max_suggestions: int = 3,
) -> List[Dict[str, Any]]:
    """
    Suggest follow-up queries based on provenance data.

    Enhanced with:
    - Smarter concept extraction
    - Context-aware suggestions
    - Quality-based prioritization

    Args:
        claim: The claim that user wants to explore further
        provenance_info: Provenance information for the claim
        max_suggestions: Maximum number of suggestions to return

    Returns:
        List of suggested query dictionaries with:
        - query: The suggested query text
        - rationale: Why this query was suggested
        - type: Type of query (deep_dive, alternative, related, verification)
        - priority: Suggestion priority (high, medium, low)
    """
    suggestions = []
    sources = provenance_info.get("sources", [])

    if not sources:
        # No sources - suggest verification query
        suggestions.append({
            "query": f"Verify: {claim[:60]}",
            "rationale": "No sources found for this claim. Verify its accuracy.",
            "type": "verification",
            "priority": "high",
        })
        return suggestions[:max_suggestions]

    top_source = sources[0]
    token_matches = top_source.get("token_matches", {})
    relevance_breakdown = top_source.get("relevance_breakdown", {})
    overlap_ratio = top_source.get("overlap_ratio", 0.0)
    semantic_similarity = top_source.get("semantic_similarity", 0.0)

    # Extract key concepts more intelligently
    # Prioritize longer, more specific terms
    if token_matches:
        token_scores = []
        for query_token, matches in token_matches.items():
            if matches:
                best_score = max(score for _, score in matches)
                # Weight by token length (longer = more specific)
                length_weight = min(1.2, 1.0 + (len(query_token) - 3) * 0.1)
                weighted_score = best_score * length_weight
                token_scores.append((query_token, weighted_score, best_score))

        # Sort by weighted score
        token_scores.sort(key=lambda x: x[1], reverse=True)
        top_tokens = token_scores[:3]

        if top_tokens:
            # Extract meaningful concepts (filter stop words, short words)
            key_concepts = []
            stop_words = {"the", "and", "for", "are", "but", "not", "you", "all", "can", "her", "was", "one", "our", "out", "day", "get", "has", "him", "his", "how", "its", "may", "new", "now", "old", "see", "two", "way", "who", "boy", "did", "its", "let", "put", "say", "she", "too", "use"}

            for token, weighted_score, raw_score in top_tokens:
                if len(token) >= 4 and token not in stop_words and raw_score > 0.7:
                    key_concepts.append(token)

            if key_concepts:
                # Create more natural query
                if len(key_concepts) == 1:
                    query = f"Explain {key_concepts[0]} in detail"
                elif len(key_concepts) == 2:
                    query = f"Explain {key_concepts[0]} and {key_concepts[1]} in detail"
                else:
                    query = f"Explain {', '.join(key_concepts[:2])} and {key_concepts[2]} in detail"

                suggestions.append({
                    "query": query,
                    "rationale": f"Explore key concepts ({', '.join(key_concepts[:3])}) that strongly matched this claim.",
                    "type": "deep_dive",
                    "priority": "high" if any(score > 0.9 for _, _, score in top_tokens) else "medium",
                })

    # Suggestion 2: Alternative perspectives (only if multiple sources)
    if len(sources) > 1:
        source_names = [s.get("source", "unknown") for s in sources[1:3] if s.get("source") != "unknown"]
        if source_names:
            # Create more natural query
            claim_short = claim[:50].rstrip('.!?')
            if len(source_names) == 1:
                query = f"What does {source_names[0]} say about {claim_short}?"
            else:
                query = f"What do {', '.join(source_names)} say about {claim_short}?"

            suggestions.append({
                "query": query,
                "rationale": f"Get alternative perspectives from {len(source_names)} other source(s).",
                "type": "alternative",
                "priority": "medium",
            })

    # Suggestion 3: Related concepts (only if semantic similarity is high)
    if relevance_breakdown:
        components = relevance_breakdown.get("components", {})
        semantic_sim = components.get("semantic_similarity", semantic_similarity)

        if semantic_sim > 0.6:
            # High semantic similarity - suggest exploring related concepts
            claim_short = claim[:50].rstrip('.!?')
            query = f"What concepts are related to {claim_short}?"
            suggestions.append({
                "query": query,
                "rationale": f"High semantic similarity ({semantic_sim:.1%}) suggests related concepts exist.",
                "type": "related",
                "priority": "medium",
            })

    # Suggestion 4: Verification query (only if relevance is low)
    if overlap_ratio < 0.5 or (relevance_breakdown and relevance_breakdown.get("overall_score", 1.0) < 0.6):
        claim_short = claim[:60].rstrip('.!?')
        query = f"Verify the claim: {claim_short}"
        suggestions.append({
            "query": query,
            "rationale": f"Low relevance ({overlap_ratio:.1%} overlap) suggests need for verification.",
            "type": "verification",
            "priority": "high" if overlap_ratio < 0.3 else "medium",
        })

    # Sort by priority (high first) then by type
    priority_order = {"high": 0, "medium": 1, "low": 2}
    suggestions.sort(key=lambda x: (priority_order.get(x.get("priority", "low"), 2), x.get("type", "")))

    return suggestions[:max_suggestions]


def refine_query_from_provenance(
    original_query: str,
    provenance_data: Dict[str, Any],
    claim: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Refine a query based on provenance data.

    Args:
        original_query: The original query
        provenance_data: Full provenance map
        claim: Optional specific claim to focus on

    Returns:
        List of refined query suggestions
    """
    if not provenance_data:
        return []

    suggestions = []

    if claim and claim in provenance_data:
        # Focus on specific claim
        provenance_info = provenance_data[claim]
        suggestions.extend(suggest_followup_queries(claim, provenance_info))
    else:
        # General refinement based on all provenance
        # Find claims with low relevance scores
        low_relevance_claims = []
        for claim_text, prov_info in provenance_data.items():
            sources = prov_info.get("sources", [])
            if sources:
                top_source = sources[0]
                relevance = top_source.get("relevance_breakdown", {}).get("overall_score", 1.0)
                if relevance < 0.6:
                    low_relevance_claims.append((claim_text, relevance))

        # Suggest queries to improve low-relevance claims
        if low_relevance_claims:
            low_relevance_claims.sort(key=lambda x: x[1])
            claim_text, score = low_relevance_claims[0]
            suggestions.append({
                "query": f"Find more sources for: {claim_text[:60]}",
                "rationale": f"Current sources have low relevance ({score:.2f}). Find better matches.",
                "type": "refinement",
            })

    # Add general exploration suggestions
    if not suggestions:
        suggestions.append({
            "query": f"Explore more about: {original_query}",
            "rationale": "General exploration of the topic.",
            "type": "exploration",
        })

    return suggestions


def create_query_refinement_panel(
    provenance_data: Dict[str, Any],
    original_query: str,
) -> str:
    """
    Create a formatted panel showing query refinement suggestions.

    Enhanced with:
    - Priority-based ordering
    - Better claim selection
    - More informative formatting

    Returns markdown-formatted string.
    """
    if not provenance_data:
        return ""

    lines = [
        "**🔍 Query Refinement Suggestions:**",
        "",
    ]

    # Get suggestions for top claims (prioritize by quality and relevance)
    def get_claim_priority(item):
        claim_text, prov_info = item
        quality = prov_info.get("quality_score", 0.5)
        relevance = prov_info.get("top_source_relevance", 0.0)
        num_sources = prov_info.get("num_sources", 0)
        # Combined priority: quality * relevance * source diversity
        return quality * relevance * (1.0 + num_sources * 0.1)

    sorted_claims = sorted(
        provenance_data.items(),
        key=get_claim_priority,
        reverse=True
    )[:3]

    all_suggestions = []
    seen_queries = set()

    for claim_text, provenance_info in sorted_claims:
        suggestions = suggest_followup_queries(claim_text, provenance_info, max_suggestions=2)
        if suggestions:
            claim_short = claim_text[:60] + "..." if len(claim_text) > 60 else claim_text
            claim_relevance = provenance_info.get("top_source_relevance", 0.0)

            for suggestion in suggestions:
                query = suggestion.get("query", "")
                # Deduplicate similar queries
                query_key = query.lower().strip()
                if query_key not in seen_queries and len(query) > 10:
                    seen_queries.add(query_key)
                    suggestion["claim_context"] = claim_short
                    suggestion["claim_relevance"] = claim_relevance
                    all_suggestions.append(suggestion)

    # Sort all suggestions by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    all_suggestions.sort(key=lambda x: (
        priority_order.get(x.get("priority", "low"), 2),
        -x.get("claim_relevance", 0.0)  # Higher relevance = better
    ))

    # Display top suggestions
    for i, suggestion in enumerate(all_suggestions[:5], 1):  # Top 5 across all claims
        priority = suggestion.get("priority", "medium")
        priority_emoji = "🔴" if priority == "high" else "🟡" if priority == "medium" else "⚪"
        query = suggestion.get("query", "")
        query_type = suggestion.get("type", "exploration")
        rationale = suggestion.get("rationale", "")

        lines.append(f"{priority_emoji} **{i}. {query}**")
        lines.append(f"   *Type:* {query_type} | *Rationale:* {rationale}")
        lines.append("")

    if not all_suggestions:
        # Fallback: general exploration
        lines.append(f"💡 **Explore more about:** {original_query}")
        lines.append("   *Type:* exploration | *Rationale:* General exploration of the topic.")

    return "\n".join(lines)

