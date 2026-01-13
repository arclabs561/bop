"""Tests for token importance tracking and visualization."""

from bop.token_importance import (
    compute_term_importance,
    compute_token_importance_for_results,
    extract_key_terms,
    format_token_importance,
)


def test_extract_key_terms_basic():
    """Test basic key term extraction."""
    text = "Machine learning is a subset of artificial intelligence that focuses on algorithms."
    terms = extract_key_terms(text)

    assert isinstance(terms, list)
    assert len(terms) > 0
    assert "machine" in terms or "learning" in terms
    assert "artificial" in terms or "intelligence" in terms


def test_extract_key_terms_filters_stop_words():
    """Test that stop words are filtered out."""
    text = "The quick brown fox jumps over the lazy dog"
    terms = extract_key_terms(text)

    assert "the" not in terms
    assert "over" not in terms
    assert "quick" in terms or "brown" in terms or "fox" in terms


def test_extract_key_terms_empty():
    """Test extraction with empty text."""
    terms = extract_key_terms("")
    assert terms == []


def test_extract_key_terms_max_limit():
    """Test that max_terms limit is respected."""
    text = " ".join([f"word{i}" for i in range(100)])
    terms = extract_key_terms(text, max_terms=10)
    assert len(terms) <= 10


def test_compute_term_importance_basic():
    """Test basic term importance computation."""
    query = "machine learning algorithms"
    result = "Machine learning algorithms use statistical methods to learn from data."

    importance = compute_term_importance(query, result)

    assert isinstance(importance, dict)
    assert len(importance) > 0
    # Terms from query should have higher importance
    assert any(term in importance for term in ["machine", "learning", "algorithms"])


def test_compute_term_importance_query_boost():
    """Test that query terms get boosted importance."""
    query = "neural networks"
    result = "Neural networks are computing systems inspired by biological neural networks."

    importance = compute_term_importance(query, result)

    # Query terms should have higher scores
    neural_score = importance.get("neural", 0)
    networks_score = importance.get("networks", 0)

    # At least one query term should have high importance
    assert max(neural_score, networks_score) > 0.3


def test_compute_term_importance_empty():
    """Test importance computation with empty result."""
    importance = compute_term_importance("query", "")
    assert importance == {}


def test_compute_token_importance_for_results():
    """Test token importance computation across multiple results."""
    query = "artificial intelligence"
    results = [
        {"result": "Artificial intelligence is the simulation of human intelligence."},
        {"result": "AI systems can learn and adapt from experience."},
        {"result": "Machine learning is a key component of artificial intelligence."},
    ]

    importance_data = compute_token_importance_for_results(query, results)

    assert "term_importance" in importance_data
    assert "per_result_importance" in importance_data
    assert "top_terms" in importance_data
    assert "query_terms" in importance_data

    assert isinstance(importance_data["term_importance"], dict)
    assert len(importance_data["per_result_importance"]) == 3
    assert len(importance_data["top_terms"]) > 0


def test_compute_token_importance_empty_results():
    """Test with empty results list."""
    importance_data = compute_token_importance_for_results("query", [])

    assert importance_data["term_importance"] == {}
    assert importance_data["per_result_importance"] == []
    assert importance_data["top_terms"] == []


def test_compute_token_importance_aggregates_scores():
    """Test that importance scores are aggregated across results."""
    query = "test query"
    results = [
        {"result": "test result one"},
        {"result": "test result two"},
        {"result": "test result three"},
    ]

    importance_data = compute_token_importance_for_results(query, results)

    # "test" should appear in all results and have aggregated importance
    test_score = importance_data["term_importance"].get("test", 0)
    assert test_score > 0


def test_format_token_importance():
    """Test formatting of token importance data."""
    importance_data = {
        "term_importance": {
            "machine": 0.8,
            "learning": 0.7,
            "algorithm": 0.6,
        },
        "top_terms": ["machine", "learning", "algorithm"],
    }

    formatted = format_token_importance(importance_data, max_display=3)

    assert isinstance(formatted, str)
    assert "Key Terms" in formatted
    assert "machine" in formatted.lower()
    assert "learning" in formatted.lower()


def test_format_token_importance_empty():
    """Test formatting with empty data."""
    formatted = format_token_importance({})
    assert formatted == ""


def test_format_token_importance_respects_max_display():
    """Test that max_display limit is respected."""
    importance_data = {
        "term_importance": {f"term{i}": 0.5 for i in range(20)},
        "top_terms": [f"term{i}" for i in range(20)],
    }

    formatted = format_token_importance(importance_data, max_display=5)

    # Should only show top 5 terms
    lines = [line for line in formatted.split("\n") if line.strip().startswith("  ")]
    assert len(lines) <= 5

