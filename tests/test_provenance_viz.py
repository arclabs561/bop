"""Tests for provenance visualization helpers."""

import pytest
from bop.provenance_viz import (
    create_provenance_heatmap,
    format_clickable_source,
    create_provenance_summary,
)


def test_create_provenance_heatmap():
    """Test creating provenance heatmap table."""
    provenance_data = {
        "D-separation determines conditional independence.": {
            "claim": "D-separation determines conditional independence.",
            "position": 0,
            "sources": [
                {
                    "source": "perplexity_deep_research",
                    "overlap_ratio": 0.8,
                    "matching_passage": "D-separation is a criterion for conditional independence.",
                    "token_matches": {
                        "separation": [("separation", 1.0)],
                        "conditional": [("conditional", 1.0)],
                    },
                },
            ],
            "num_sources": 1,
        },
    }
    
    heatmap = create_provenance_heatmap(provenance_data, max_claims=5)
    
    # Should return a Rich Table
    assert hasattr(heatmap, "columns")
    assert len(heatmap.columns) == 5  # Claim, Relevance, Query Tokens, Matched Tokens, Sources


def test_create_provenance_heatmap_empty():
    """Test heatmap with empty provenance."""
    heatmap = create_provenance_heatmap({}, max_claims=5)
    
    assert hasattr(heatmap, "columns")
    # Should have a placeholder row
    assert len(heatmap.rows) >= 0


def test_format_clickable_source():
    """Test formatting clickable source reference."""
    claim = "D-separation determines conditional independence."
    provenance_info = {
        "sources": [
            {
                "source": "perplexity_deep_research",
                "overlap_ratio": 0.8,
                "matching_passage": "D-separation is a criterion...",
                "token_matches": {"separation": [("separation", 1.0)]},
            },
        ],
    }
    
    formatted, tooltip_data = format_clickable_source(claim, provenance_info)
    
    assert isinstance(formatted, str)
    assert "perplexity_deep_research" in formatted or "provenance:" in formatted
    assert isinstance(tooltip_data, dict)
    assert "source" in tooltip_data
    assert "passage" in tooltip_data


def test_create_provenance_summary():
    """Test creating provenance summary text."""
    provenance_data = {
        "Claim 1": {
            "claim": "Claim 1",
            "sources": [
                {"source": "perplexity_deep_research"},
                {"source": "firecrawl_search"},
            ],
            "num_sources": 2,
        },
        "Claim 2": {
            "claim": "Claim 2",
            "sources": [{"source": "perplexity_deep_research"}],
            "num_sources": 1,
        },
    }
    
    summary = create_provenance_summary(provenance_data)
    
    assert "Total claims analyzed" in summary
    assert "Claims with source matches" in summary
    assert "Unique sources" in summary


def test_create_provenance_summary_empty():
    """Test summary with empty provenance."""
    summary = create_provenance_summary({})
    
    assert "No provenance data available" in summary

