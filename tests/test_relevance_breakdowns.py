"""Tests for relevance score breakdowns."""

from bop.provenance import (
    _compute_relevance_breakdown,
    _compute_semantic_similarity,
    match_claim_to_sources,
)


def test_compute_semantic_similarity():
    """Test semantic similarity calculation."""
    text1 = "D-separation is a fundamental concept in causal inference"
    text2 = "D-separation determines conditional independence in graphs"

    similarity = _compute_semantic_similarity(text1, text2)

    assert 0.0 <= similarity <= 1.0
    assert similarity > 0.2  # Should have some similarity (lowered threshold for different phrasing)


def test_compute_semantic_similarity_identical():
    """Test semantic similarity for identical texts."""
    text = "This is a test sentence"
    similarity = _compute_semantic_similarity(text, text)

    assert similarity >= 0.8  # Should be very high for identical text


def test_compute_semantic_similarity_different():
    """Test semantic similarity for completely different texts."""
    text1 = "The weather is sunny today"
    text2 = "Quantum mechanics describes particle behavior"

    similarity = _compute_semantic_similarity(text1, text2)

    assert 0.0 <= similarity <= 1.0
    assert similarity < 0.3  # Should be low for unrelated texts


def test_compute_relevance_breakdown():
    """Test relevance breakdown computation."""
    claim = "D-separation is a graphical criterion"
    result_text = "D-separation is a method for determining conditional independence in directed acyclic graphs"
    overlap_ratio = 0.6
    semantic_similarity = 0.7
    token_matches = {
        "d-separation": [("d-separation", 0.95), ("separation", 0.80)],
        "graphical": [("graphical", 0.90)],
    }

    breakdown = _compute_relevance_breakdown(
        claim,
        result_text,
        overlap_ratio,
        semantic_similarity,
        token_matches,
    )

    assert "overall_score" in breakdown
    assert "components" in breakdown
    assert "explanation" in breakdown
    assert "top_token_matches" in breakdown

    assert 0.0 <= breakdown["overall_score"] <= 1.0
    assert breakdown["components"]["word_overlap"] == overlap_ratio
    assert breakdown["components"]["semantic_similarity"] == semantic_similarity
    assert len(breakdown["top_token_matches"]) > 0


def test_match_claim_to_sources_includes_relevance_breakdown():
    """Test that match_claim_to_sources includes relevance breakdown."""
    claim = "D-separation is a fundamental concept in causal inference"
    research_results = [
        {
            "tool": "perplexity_deep_research",
            "result": "D-separation is a graphical criterion for determining conditional independence in causal inference. It helps identify when variables are conditionally independent given a set of conditioning variables in directed acyclic graphs.",
        }
    ]

    matches = match_claim_to_sources(claim, research_results)

    assert len(matches) > 0
    top_match = matches[0]

    assert "relevance_breakdown" in top_match
    assert "semantic_similarity" in top_match

    breakdown = top_match["relevance_breakdown"]
    assert breakdown["overall_score"] > 0.0
    assert "explanation" in breakdown

