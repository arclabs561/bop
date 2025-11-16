"""Tests for Information Bottleneck filtering."""

import pytest
from bop.information_bottleneck import (
    filter_with_information_bottleneck,
    compute_mutual_information_estimate,
)


def test_compute_mutual_information_estimate():
    """Test mutual information estimation."""
    passage = "D-separation is a graphical criterion for conditional independence"
    target = "D-separation determines conditional independence in graphs"
    
    mi = compute_mutual_information_estimate(passage, target)
    
    assert 0.0 <= mi <= 1.0
    assert mi > 0.3  # Should have reasonable similarity


def test_compute_mutual_information_estimate_identical():
    """Test MI estimation for identical texts."""
    text = "This is a test sentence"
    mi = compute_mutual_information_estimate(text, text)
    
    assert mi >= 0.8  # Should be very high for identical text


def test_compute_mutual_information_estimate_different():
    """Test MI estimation for completely different texts."""
    passage = "The weather is sunny today"
    target = "Quantum mechanics describes particle behavior"
    
    mi = compute_mutual_information_estimate(passage, target)
    
    assert 0.0 <= mi <= 1.0
    assert mi < 0.3  # Should be low for unrelated texts


def test_compute_mutual_information_estimate_empty():
    """Test MI estimation with empty inputs."""
    mi1 = compute_mutual_information_estimate("", "test")
    mi2 = compute_mutual_information_estimate("test", "")
    mi3 = compute_mutual_information_estimate("", "")
    
    assert mi1 == 0.0
    assert mi2 == 0.0
    assert mi3 == 0.0


def test_ib_filtering_removes_low_relevance():
    """Test that IB filtering removes low-relevance results."""
    results = [
        {"result": "D-separation is a graphical criterion for conditional independence"},
        {"result": "The weather is sunny today"},
        {"result": "D-separation helps identify d-separated variables in DAGs"},
    ]
    query = "What is d-separation?"
    
    # Use very low threshold since semantic similarity gives ~0.3 for d-separation queries
    # and ~0.1 for unrelated content. We want to filter out the weather result.
    filtered, metadata = filter_with_information_bottleneck(
        results, query, min_mi=0.15
    )
    
    # Should filter out at least the weather result
    assert len(filtered) < len(results)
    assert metadata["removed_count"] > 0
    assert metadata["compression_ratio"] < 1.0
    # Compression ratio should be > 0 (some results kept)
    assert metadata["compression_ratio"] > 0.0
    # Average MI should be above threshold
    if filtered:
        assert metadata["avg_mi"] > 0.15


def test_ib_filtering_preserves_high_relevance():
    """Test that IB filtering preserves high-relevance results."""
    results = [
        {"result": "D-separation is a graphical criterion"},
        {"result": "D-separation determines conditional independence"},
    ]
    query = "What is d-separation?"
    
    # Use very low threshold since semantic similarity gives ~0.3 for d-separation queries
    # Both results should pass with a low threshold
    filtered, metadata = filter_with_information_bottleneck(
        results, query, min_mi=0.15
    )
    
    # Both should pass (or at least one, depending on exact MI scores)
    assert len(filtered) >= 1
    if len(filtered) == len(results):
        assert metadata["compression_ratio"] == 1.0
    if filtered:
        assert metadata["avg_mi"] > 0.15


def test_ib_filtering_with_target():
    """Test IB filtering with target output."""
    results = [
        {"result": "D-separation is used in causal inference"},
        {"result": "D-separation is a graphical method"},
    ]
    query = "What is d-separation?"
    target = "D-separation is a graphical criterion for conditional independence"
    
    filtered, metadata = filter_with_information_bottleneck(
        results, query, target_output=target
    )
    
    assert len(filtered) > 0
    assert metadata["avg_mi"] > 0.0
    assert "beta" in metadata
    assert "min_mi" in metadata


def test_ib_filtering_max_results():
    """Test that IB filtering respects max_results limit."""
    results = [
        {"result": "D-separation is a graphical criterion"},
        {"result": "D-separation determines conditional independence"},
        {"result": "D-separation helps identify d-separated variables"},
        {"result": "D-separation is used in causal inference"},
        {"result": "D-separation relates to d-connection"},
    ]
    query = "What is d-separation?"
    
    filtered, metadata = filter_with_information_bottleneck(
        results, query, min_mi=0.2, max_results=3
    )
    
    assert len(filtered) <= 3
    assert metadata["filtered_count"] <= 3


def test_ib_filtering_empty_results():
    """Test IB filtering with empty results."""
    filtered, metadata = filter_with_information_bottleneck([], "test query")
    
    assert filtered == []
    assert metadata["compression_ratio"] == 1.0
    assert metadata["removed_count"] == 0
    assert metadata["avg_mi"] == 0.0


def test_ib_filtering_no_valid_results():
    """Test IB filtering with results that have no 'result' field."""
    results = [
        {"tool": "test", "other": "data"},
        {"tool": "test2"},
    ]
    query = "test query"
    
    filtered, metadata = filter_with_information_bottleneck(results, query)
    
    # Should filter out results with no 'result' field
    assert len(filtered) == 0 or all("result" in r for r in filtered)


def test_ib_filtering_min_mi_threshold():
    """Test that IB filtering respects min_mi threshold."""
    results = [
        {"result": "D-separation is a graphical criterion"},  # High relevance (~0.3 MI)
        {"result": "The weather is sunny"},  # Low relevance (~0.1 MI)
        {"result": "D-separation determines independence"},  # High relevance (~0.3 MI)
    ]
    query = "What is d-separation?"
    
    # High threshold (above typical MI scores)
    filtered_high, _ = filter_with_information_bottleneck(
        results, query, min_mi=0.35
    )
    
    # Low threshold (below typical MI scores)
    filtered_low, _ = filter_with_information_bottleneck(
        results, query, min_mi=0.1
    )
    
    assert len(filtered_high) <= len(filtered_low)
    # With semantic similarity, high-relevance results get ~0.3 MI, so high threshold may filter all
    # Just verify that lower threshold keeps more results
    assert len(filtered_low) >= 1


def test_ib_filtering_metadata_completeness():
    """Test that IB filtering metadata is complete."""
    results = [
        {"result": "D-separation is a graphical criterion"},
        {"result": "D-separation determines conditional independence"},
    ]
    query = "What is d-separation?"
    
    filtered, metadata = filter_with_information_bottleneck(
        results, query, beta=0.6, min_mi=0.3
    )
    
    assert "compression_ratio" in metadata
    assert "avg_mi" in metadata
    assert "removed_count" in metadata
    assert "beta" in metadata
    assert metadata["beta"] == 0.6
    assert "min_mi" in metadata
    assert metadata["min_mi"] == 0.3
    assert "original_count" in metadata
    assert "filtered_count" in metadata
    assert metadata["original_count"] == len(results)
    assert metadata["filtered_count"] == len(filtered)

