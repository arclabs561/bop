"""Tests for visualization helpers."""

from pran.visualizations import (
    create_document_relationship_graph,
    create_source_matrix_heatmap,
    create_token_importance_chart,
    create_trust_metrics_chart,
)


def test_create_source_matrix_heatmap_basic():
    """Test basic source matrix heatmap creation."""
    source_matrix = {
        "claim1": {
            "sources": {
                "perplexity": "supports",
                "tavily": "supports",
            },
            "consensus": "strong_agreement",
        },
        "claim2": {
            "sources": {
                "perplexity": "supports",
                "firecrawl": "contradicts",
            },
            "consensus": "disagreement",
        },
    }

    table = create_source_matrix_heatmap(source_matrix)

    assert table is not None
    # Table should have columns for claims and sources
    assert len(table.columns) > 0


def test_create_source_matrix_heatmap_empty():
    """Test heatmap creation with empty matrix."""
    table = create_source_matrix_heatmap({})
    assert table is not None
    assert "empty" in table.title.lower()


def test_create_source_matrix_heatmap_respects_max_claims():
    """Test that max_claims limit is respected."""
    source_matrix = {
        f"claim{i}": {
            "sources": {"source1": "supports"},
            "consensus": "strong_agreement",
        }
        for i in range(20)
    }

    table = create_source_matrix_heatmap(source_matrix, max_claims=5)
    # Should only show top 5 claims
    assert len(table.rows) <= 5


def test_create_trust_metrics_chart():
    """Test trust metrics chart creation."""
    trust_summary = {
        "avg_trust": 0.75,
        "avg_credibility": 0.70,
        "avg_confidence": 0.80,
        "calibration_error": 0.12,
    }

    source_credibility = {
        "perplexity": 0.75,
        "tavily": 0.65,
    }

    panel = create_trust_metrics_chart(trust_summary, source_credibility)

    assert panel is not None
    assert "Trust Metrics" in panel.title


def test_create_trust_metrics_chart_minimal():
    """Test chart creation with minimal data."""
    trust_summary = {"avg_trust": 0.5}
    panel = create_trust_metrics_chart(trust_summary)
    assert panel is not None


def test_create_document_relationship_graph():
    """Test document relationship graph creation."""
    cliques = [
        {
            "node_sources": ["perplexity", "tavily", "firecrawl"],
            "trust": 0.8,
            "coherence": 0.75,
            "size": 3,
        },
        {
            "node_sources": ["perplexity", "tavily"],
            "trust": 0.6,
            "coherence": 0.65,
            "size": 2,
        },
    ]

    table = create_document_relationship_graph(cliques)

    assert table is not None
    assert len(table.rows) > 0


def test_create_document_relationship_graph_empty():
    """Test graph creation with empty cliques."""
    table = create_document_relationship_graph([])
    assert table is not None
    assert "empty" in table.title.lower()


def test_create_document_relationship_graph_filters_low_trust():
    """Test that low-trust cliques are filtered out."""
    cliques = [
        {
            "node_sources": ["source1"],
            "trust": 0.3,  # Low trust
            "coherence": 0.5,
            "size": 1,
        },
        {
            "node_sources": ["source2"],
            "trust": 0.8,  # High trust
            "coherence": 0.7,
            "size": 1,
        },
    ]

    table = create_document_relationship_graph(cliques)
    # Should only show high-trust clique
    assert len(table.rows) == 1


def test_create_token_importance_chart():
    """Test token importance chart creation."""
    importance_data = {
        "term_importance": {
            "machine": 0.8,
            "learning": 0.7,
            "algorithm": 0.6,
        },
        "top_terms": ["machine", "learning", "algorithm"],
    }

    table = create_token_importance_chart(importance_data)

    assert table is not None
    assert len(table.rows) == 3


def test_create_token_importance_chart_empty():
    """Test chart creation with empty data."""
    table = create_token_importance_chart({})
    assert table is not None
    assert "empty" in table.title.lower()


def test_create_token_importance_chart_respects_max_terms():
    """Test that max_terms limit is respected."""
    importance_data = {
        "term_importance": {f"term{i}": 0.5 for i in range(20)},
        "top_terms": [f"term{i}" for i in range(20)],
    }

    table = create_token_importance_chart(importance_data, max_terms=5)
    assert len(table.rows) <= 5

