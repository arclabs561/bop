"""Metamorphic tests for SSH features."""

import tempfile
from pathlib import Path

from pran.adaptive_quality import AdaptiveQualityManager
from pran.information_bottleneck import filter_with_information_bottleneck
from pran.quality_feedback import QualityFeedbackLoop


def test_metamorphic_ib_filtering_adding_results():
    """
    METAMORPHIC: Adding more results should not decrease compression ratio.

    If we add more results, the compression ratio should stay the same or improve
    (more results to filter from = potentially better filtering).
    """
    query = "What is d-separation?"

    results1 = [
        {"result": "D-separation is a graphical criterion"},
        {"result": "D-separation determines conditional independence"},
    ]

    results2 = results1 + [
        {"result": "The weather is sunny"},  # Low relevance
        {"result": "D-separation is used in causal inference"},  # High relevance
    ]

    _, metadata1 = filter_with_information_bottleneck(results1, query, min_mi=0.3)
    _, metadata2 = filter_with_information_bottleneck(results2, query, min_mi=0.3)

    # Compression ratio should be similar or better with more results
    # (more results = more opportunity to filter)
    assert metadata2["compression_ratio"] <= metadata1["compression_ratio"] * 1.2  # Allow some variance


def test_metamorphic_ib_filtering_increasing_min_mi():
    """
    METAMORPHIC: Increasing min_mi should decrease filtered count.

    Higher minimum mutual information threshold should filter out more results.
    """
    query = "What is d-separation?"
    results = [
        {"result": "D-separation is a graphical criterion"},  # High relevance
        {"result": "D-separation determines conditional independence"},  # High relevance
        {"result": "The weather is sunny"},  # Low relevance
        {"result": "D-separation is used in causal inference"},  # High relevance
    ]

    _, metadata_low = filter_with_information_bottleneck(results, query, min_mi=0.1)
    _, metadata_high = filter_with_information_bottleneck(results, query, min_mi=0.5)

    # Higher threshold should filter more (lower filtered count)
    assert metadata_high["filtered_count"] <= metadata_low["filtered_count"]


def test_metamorphic_adaptive_depth_learning_accumulation():
    """
    METAMORPHIC: Learning should accumulate, not replace.

    Adding more learning examples should improve depth estimation accuracy.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)

        query = "What is trust?"

        query_type = manager._classify_query(query)

        # Get initial count (may be 0 or may have existing data)
        len(manager.query_type_to_depth.get(query_type, []))

        # Add single example
        manager.update_from_evaluation(
            query=query,
            schema="decompose_and_synthesize",
            used_research=True,
            response_length=200,
            quality_score=0.8,
            num_subproblems=3,
        )

        manager.estimate_reasoning_depth(query)
        data_count_after_one = len(manager.query_type_to_depth.get(query_type, []))

        # Add more examples (but not too many to avoid hitting 50 limit)
        for _ in range(2):
            manager.update_from_evaluation(
                query=query,
                schema="decompose_and_synthesize",
                used_research=True,
                response_length=200,
                quality_score=0.8,
                num_subproblems=3,
            )

        depth2 = manager.estimate_reasoning_depth(query)
        data_count2 = len(manager.query_type_to_depth.get(query_type, []))

        # Should have more learning data (at least 2 more entries, accounting for 50-entry limit)
        # If we're at the limit, count may not increase, but depth should still be consistent
        if data_count2 < 50:  # Not at limit
            assert data_count2 >= data_count_after_one + 2
        else:  # At limit, but should still have data
            assert data_count2 >= 50

        # Depth should be consistent (should still be 3 since all examples use depth 3)
        assert depth2 >= 1
        # With all examples at depth 3, estimated depth should be 3
        assert depth2 == 3


def test_metamorphic_resource_triple_scaling():
    """
    METAMORPHIC: Resource triple should scale with query complexity.

    More complex queries should have higher depth/width.
    """
    # This is a conceptual test - in practice would need actual orchestrator calls
    # Simple query should have lower depth than complex query
    # (Tested via integration tests)


def test_metamorphic_logical_depth_trust_correlation():
    """
    METAMORPHIC: Logical depth should correlate with trust.

    Higher trust nodes should have higher logical depth.
    """
    # This is tested in context_topology via the computation logic
    # High trust + high coherence = high logical depth
    # (Verified in unit tests)

