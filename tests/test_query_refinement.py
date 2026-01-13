"""Tests for query refinement features."""

from bop.query_refinement import (
    create_query_refinement_panel,
    refine_query_from_provenance,
    suggest_followup_queries,
)


def test_suggest_followup_queries():
    """Test follow-up query suggestions."""
    claim = "D-separation is a fundamental concept"
    provenance_info = {
        "sources": [
            {
                "source": "perplexity_deep_research",
                "token_matches": {
                    "d-separation": [("d-separation", 0.95)],
                    "concept": [("concept", 0.80)],
                },
                "overlap_ratio": 0.6,
                "relevance_breakdown": {
                    "overall_score": 0.7,
                    "components": {
                        "semantic_similarity": 0.65,
                    },
                },
            }
        ],
    }

    suggestions = suggest_followup_queries(claim, provenance_info)

    assert len(suggestions) > 0
    assert all("query" in s for s in suggestions)
    assert all("rationale" in s for s in suggestions)
    assert all("type" in s for s in suggestions)


def test_suggest_followup_queries_no_sources():
    """Test follow-up suggestions when no sources available."""
    claim = "Test claim"
    provenance_info = {"sources": []}

    suggestions = suggest_followup_queries(claim, provenance_info)

    assert len(suggestions) > 0
    # Should suggest verification query
    assert any(s["type"] == "verification" for s in suggestions)


def test_refine_query_from_provenance():
    """Test query refinement from provenance data."""
    original_query = "What is d-separation?"
    provenance_data = {
        "D-separation is a graphical criterion": {
            "sources": [
                {
                    "source": "test_source",
                    "relevance_breakdown": {
                        "overall_score": 0.5,  # Low relevance
                    },
                }
            ],
        }
    }

    suggestions = refine_query_from_provenance(original_query, provenance_data)

    assert len(suggestions) > 0
    assert all("query" in s for s in suggestions)


def test_create_query_refinement_panel():
    """Test query refinement panel creation."""
    provenance_data = {
        "Claim 1": {
            "sources": [
                {
                    "source": "source1",
                    "token_matches": {"key": [("key", 0.9)]},
                }
            ],
        }
    }
    original_query = "Test query"

    panel = create_query_refinement_panel(provenance_data, original_query)

    assert isinstance(panel, str)
    assert len(panel) > 0
    assert "Query Refinement" in panel or "Suggestions" in panel

