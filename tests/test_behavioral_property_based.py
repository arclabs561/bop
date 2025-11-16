"""Property-based tests for behavioral properties using Hypothesis."""

import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import List, Dict, Any
import tempfile
from pathlib import Path

from bop.quality_feedback import QualityFeedbackLoop
from bop.semantic_eval import SemanticEvaluator
from tests.test_annotations import annotate_test


# Property: Context should be preserved across evaluations
@given(
    query1=st.text(min_size=5, max_size=200),
    query2=st.text(min_size=5, max_size=200),
    response1=st.text(min_size=5, max_size=500),
    response2=st.text(min_size=5, max_size=500),
)
@settings(max_examples=15, deadline=None)
def test_property_context_preservation(query1: str, query2: str, response1: str, response2: str):
    """
    PROPERTY: Context should be preserved across multiple evaluations.
    
    Pattern: property_based_behavioral
    Opinion: context_is_preserved
    Category: behavioral_property
    Hypothesis: Quality feedback should preserve context across evaluations.
    """
    annotate_test(
        "test_property_context_preservation",
        pattern="property_based_behavioral",
        opinion="context_is_preserved",
        category="behavioral_property",
        hypothesis="Quality feedback should preserve context across evaluations.",
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=False,
        )
        
        # Evaluate first query
        result1 = feedback.evaluate_and_learn(
            query=query1,
            response=response1,
            context="test_context",
        )
        
        # Evaluate second query
        result2 = feedback.evaluate_and_learn(
            query=query2,
            response=response2,
            context="test_context",
        )
        
        # History should contain both
        assert len(feedback.history) >= 2
        # Both should have context
        assert any("context" in str(e) or "test_context" in str(e) for e in feedback.history)


# Property: Schema performance tracking should be monotonic
@given(
    query=st.text(min_size=5, max_size=200),
    response=st.text(min_size=5, max_size=500),
    schema=st.sampled_from(["chain_of_thought", "iterative_elaboration", "decompose_and_synthesize"]),
    num_evaluations=st.integers(min_value=2, max_value=5),
)
@settings(max_examples=10, deadline=None)
def test_property_schema_performance_tracking(
    query: str, response: str, schema: str, num_evaluations: int
):
    """
    PROPERTY: Schema performance tracking should accumulate correctly.
    
    Pattern: property_based_behavioral
    Opinion: schema_performance_accumulates
    Category: behavioral_property
    Hypothesis: Multiple evaluations with same schema should accumulate in performance tracking.
    """
    annotate_test(
        "test_property_schema_performance_tracking",
        pattern="property_based_behavioral",
        opinion="schema_performance_accumulates",
        category="behavioral_property",
        hypothesis="Multiple evaluations with same schema should accumulate in performance tracking.",
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=False,
        )
        
        # Evaluate multiple times with same schema
        for _ in range(num_evaluations):
            feedback.evaluate_and_learn(
                query=query,
                response=response,
                schema=schema,
            )
        
        # Schema should be tracked
        assert schema in feedback.schema_scores
        # Should have num_evaluations scores
        assert len(feedback.schema_scores[schema]) == num_evaluations


# Property: Quality issue counts should be monotonic
@given(
    query=st.text(min_size=5, max_size=200),
    placeholder_response=st.sampled_from([
        "[LLM service not available]",
        "[MCP integration ready]",
        "Response to:",
    ]),
    num_evaluations=st.integers(min_value=2, max_value=5),
)
@settings(max_examples=10, deadline=None)
def test_property_quality_issue_counts_monotonic(
    query: str, placeholder_response: str, num_evaluations: int
):
    """
    PROPERTY: Quality issue counts should increase monotonically.
    
    Pattern: property_based_behavioral
    Opinion: quality_issues_accumulate
    Category: behavioral_property
    Hypothesis: Quality issue counts should increase with each evaluation that has issues.
    """
    annotate_test(
        "test_property_quality_issue_counts_monotonic",
        pattern="property_based_behavioral",
        opinion="quality_issues_accumulate",
        category="behavioral_property",
        hypothesis="Quality issue counts should increase with each evaluation that has issues.",
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=False,
        )
        
        initial_count = feedback.quality_issue_counts.get("placeholder", 0)
        
        # Evaluate multiple times with placeholder
        for _ in range(num_evaluations):
            feedback.evaluate_and_learn(
                query=query,
                response=placeholder_response,
            )
        
        # Placeholder count should have increased
        final_count = feedback.quality_issue_counts.get("placeholder", 0)
        assert final_count >= initial_count + num_evaluations, (
            f"Quality issue count didn't increase: {initial_count} -> {final_count}"
        )


# Property: History should grow monotonically
@given(
    queries=st.lists(st.text(min_size=5, max_size=200), min_size=1, max_size=5),
    responses=st.lists(st.text(min_size=5, max_size=500), min_size=1, max_size=5),
)
@settings(max_examples=10, deadline=None)
def test_property_history_grows_monotonically(queries: List[str], responses: List[str]):
    """
    PROPERTY: History should grow monotonically with each evaluation.
    
    Pattern: property_based_behavioral
    Opinion: history_grows_monotonically
    Category: behavioral_property
    Hypothesis: History should grow with each evaluation.
    """
    annotate_test(
        "test_property_history_grows_monotonically",
        pattern="property_based_behavioral",
        opinion="history_grows_monotonically",
        category="behavioral_property",
        hypothesis="History should grow with each evaluation.",
    )
    
    assume(len(queries) == len(responses))  # Same length
    
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=False,
        )
        
        initial_length = len(feedback.history)
        
        # Evaluate each query-response pair
        for query, response in zip(queries, responses):
            feedback.evaluate_and_learn(query=query, response=response)
            # History should have grown
            assert len(feedback.history) > initial_length
            initial_length = len(feedback.history)
        
        # Final history should have all evaluations
        assert len(feedback.history) == len(queries)

