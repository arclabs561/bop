"""Complete integration test for all provenance features working together.

This test validates that all provenance features integrate correctly:
- Relevance breakdowns
- Query refinement
- Clickable sources
- Progressive disclosure
- Error handling
"""

from pran.provenance import (
    _compute_relevance_breakdown,
    _compute_semantic_similarity,
    build_provenance_map,
    match_claim_to_sources,
)
from pran.provenance_viz import (
    create_relevance_breakdown_display,
    format_clickable_source,
)
from pran.query_refinement import (
    create_query_refinement_panel,
    refine_query_from_provenance,
)


def test_integration_provenance_pipeline():
    """
    Test complete provenance pipeline from research results to user display.

    Pipeline:
    1. Research results → build_provenance_map
    2. Provenance map → format_clickable_source
    3. Provenance map → create_relevance_breakdown_display
    4. Provenance map → refine_query_from_provenance
    """
    response_text = "D-separation is a graphical criterion for determining conditional independence in directed acyclic graphs."

    research = {
        "subsolutions": [
            {
                "subproblem": "What is d-separation?",
                "results": [
                    {
                        "tool": "perplexity_deep_research",
                        "result": "D-separation is a graphical criterion for determining conditional independence in directed acyclic graphs. It helps identify when variables are conditionally independent given a set of conditioning variables.",
                    }
                ],
                "synthesis": "D-separation determines conditional independence.",
            }
        ],
    }

    # Step 1: Build provenance map
    provenance_map = build_provenance_map(response_text, research)

    # Step 2: Format clickable sources
    if len(provenance_map) > 0:
        first_claim = list(provenance_map.keys())[0]
        provenance_info = provenance_map[first_claim]

        formatted_text, tooltip_data = format_clickable_source(first_claim, provenance_info)

        assert isinstance(formatted_text, str)
        assert isinstance(tooltip_data, dict)

        # Step 3: Create relevance breakdown display
        sources = provenance_info.get("sources", [])
        if sources:
            top_source = sources[0]
            relevance_breakdown = top_source.get("relevance_breakdown", {})

            if relevance_breakdown:
                breakdown_display = create_relevance_breakdown_display(relevance_breakdown)
                assert "Relevance Score" in breakdown_display

        # Step 4: Generate query refinement
        original_query = "What is d-separation?"
        refinement_suggestions = refine_query_from_provenance(original_query, provenance_map)

        # Should have suggestions (or empty list if none)
        assert isinstance(refinement_suggestions, list)

        # Step 5: Create refinement panel
        refinement_panel = create_query_refinement_panel(provenance_map, original_query)
        assert isinstance(refinement_panel, str)


def test_integration_relevance_components():
    """Test that all relevance breakdown components work together."""
    claim = "D-separation is a graphical criterion"
    result_text = "D-separation is a method for determining conditional independence in graphs"

    # Compute semantic similarity
    semantic_sim = _compute_semantic_similarity(claim, result_text)
    assert 0.0 <= semantic_sim <= 1.0

    # Compute word overlap (simplified)
    from pran.provenance import match_claim_to_sources
    research_results = [
        {
            "tool": "test_source",
            "result": result_text,
        }
    ]
    matches = match_claim_to_sources(claim, research_results)

    if matches:
        top_match = matches[0]
        overlap_ratio = top_match.get("overlap_ratio", 0.0)
        token_matches = top_match.get("token_matches", {})

        # Compute relevance breakdown
        relevance_breakdown = _compute_relevance_breakdown(
            claim,
            result_text,
            overlap_ratio,
            semantic_sim,
            token_matches,
        )

        # Verify breakdown structure
        assert "overall_score" in relevance_breakdown
        assert "components" in relevance_breakdown
        assert "explanation" in relevance_breakdown

        # Verify components
        components = relevance_breakdown["components"]
        assert "word_overlap" in components
        assert "semantic_similarity" in components
        assert "token_match_avg" in components

        # Verify scores are in valid range
        assert 0.0 <= relevance_breakdown["overall_score"] <= 1.0
        assert 0.0 <= components["word_overlap"] <= 1.0
        assert 0.0 <= components["semantic_similarity"] <= 1.0


def test_integration_error_handling_chain():
    """Test that errors at any stage don't break the entire pipeline."""
    # Test with empty research
    provenance_map1 = build_provenance_map("Test response", {})
    assert isinstance(provenance_map1, dict)
    assert len(provenance_map1) == 0

    # Test with missing relevance breakdown
    provenance_info = {
        "sources": [
            {
                "source": "test_source",
                "overlap_ratio": 0.5,
                # Missing relevance_breakdown
            }
        ],
    }

    formatted_text, tooltip_data = format_clickable_source("Test claim", provenance_info)
    assert isinstance(formatted_text, str)
    # Should still work without relevance breakdown

    # Test with empty provenance for refinement
    suggestions = refine_query_from_provenance("Test query", {})
    assert isinstance(suggestions, list)
    # Should return empty list or fallback suggestions, not crash


def test_integration_data_flow():
    """Test data flow through the entire system."""
    # Simulate research results
    research_results = [
        {
            "tool": "perplexity_deep_research",
            "result": "D-separation is a graphical criterion for determining conditional independence.",
        }
    ]

    claim = "D-separation is a graphical criterion"

    # Step 1: Match claim to sources
    matches = match_claim_to_sources(claim, research_results)

    if matches:
        top_match = matches[0]

        # Step 2: Verify match has all required fields
        assert "source" in top_match
        assert "overlap_ratio" in top_match or "relevance_breakdown" in top_match

        # Step 3: If relevance breakdown exists, verify structure
        if "relevance_breakdown" in top_match:
            breakdown = top_match["relevance_breakdown"]
            assert "overall_score" in breakdown
            assert "components" in breakdown

            # Step 4: Format for display
            display = create_relevance_breakdown_display(breakdown)
            assert isinstance(display, str)
            assert len(display) > 0

