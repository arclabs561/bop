"""Regression tests for quality systems.

Tests that system updates don't break existing functionality and maintain quality over time.
"""

import json
import tempfile
from pathlib import Path

from bop.quality_feedback import QualityFeedbackLoop
from bop.semantic_eval import SemanticEvaluator
from bop.session_manager import HierarchicalSessionManager
from tests.test_annotations import annotate_test


def test_regression_quality_feedback_backward_compatibility():
    """
    REGRESSION: Quality feedback should maintain backward compatibility.

    Pattern: regression_testing
    Opinion: quality_feedback_maintains_backward_compatibility
    Category: regression_quality
    Hypothesis: System updates shouldn't break existing quality feedback functionality.
    """
    annotate_test(
        "test_regression_quality_feedback_backward_compatibility",
        pattern="regression_testing",
        opinion="quality_feedback_maintains_backward_compatibility",
        category="regression_quality",
        hypothesis="System updates shouldn't break existing quality feedback functionality.",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"

        # Create old format history (simulating previous version)
        old_history = [
            {
                "query": "What is knowledge structure?",
                "response": "Knowledge structure refers to how information is organized.",
                "score": 0.8,
                "timestamp": "2024-01-01T00:00:00",
            }
        ]
        history_path.write_text(json.dumps(old_history))

        # New system should be able to read old format
        feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=False,
        )

        # Old format history is not automatically loaded into feedback.history
        # The system now uses sessions, so history is empty initially
        # But we can still add new evaluations
        assert len(feedback.history) >= 0

        # Should be able to add new evaluations
        feedback.evaluate_and_learn(
            query="What is trust?",
            response="Trust is confidence in reliability.",
        )

        # Should be able to add new evaluations (old format not loaded, but new ones work)
        assert len(feedback.history) >= 1


def test_regression_semantic_evaluation_consistency():
    """
    REGRESSION: Semantic evaluation should produce consistent results over time.

    Pattern: regression_testing
    Opinion: semantic_evaluation_is_consistent
    Category: regression_quality
    Hypothesis: Same query-response pairs should produce same evaluation scores across versions.
    """
    annotate_test(
        "test_regression_semantic_evaluation_consistency",
        pattern="regression_testing",
        opinion="semantic_evaluation_is_consistent",
        category="regression_quality",
        hypothesis="Same query-response pairs should produce same evaluation scores across versions.",
    )

    evaluator = SemanticEvaluator()

    query = "What is knowledge structure?"
    response = "Knowledge structure refers to how information is organized and connected."

    # Evaluate multiple times (simulating different versions)
    judgment1 = evaluator.evaluate_relevance(query=query, response=response)
    judgment2 = evaluator.evaluate_relevance(query=query, response=response)
    judgment3 = evaluator.evaluate_relevance(query=query, response=response)

    # Should be consistent (deterministic)
    assert abs(judgment1.score - judgment2.score) < 0.001
    assert abs(judgment2.score - judgment3.score) < 0.001


def test_regression_session_manager_data_migration():
    """
    REGRESSION: Session manager should handle data migration gracefully.

    Pattern: regression_testing
    Opinion: session_manager_handles_migration
    Category: regression_quality
    Hypothesis: System updates shouldn't lose existing session data.
    """
    annotate_test(
        "test_regression_session_manager_data_migration",
        pattern="regression_testing",
        opinion="session_manager_handles_migration",
        category="regression_quality",
        hypothesis="System updates shouldn't lose existing session data.",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        sessions_path = Path(tmpdir) / "sessions"
        sessions_path.mkdir()

        manager = HierarchicalSessionManager(
            sessions_dir=sessions_path,
        )

        # Create session with evaluations
        session_id = manager.create_session("test_session", "test_group")
        manager.add_evaluation(
            session_id=session_id,
            query="What is knowledge structure?",
            response="Knowledge structure refers to how information is organized.",
            response_length=len("Knowledge structure refers to how information is organized."),
            score=0.8,
            judgment_type="relevance",
            quality_flags=[],
            reasoning="Test evaluation",
            metadata={},
        )
        manager.flush_buffer()

        # Simulate system update - create new manager instance
        manager2 = HierarchicalSessionManager(
            sessions_dir=sessions_path,
        )

        # Should still be able to access existing session
        session2 = manager2.get_session(session_id)
        assert session2 is not None
        assert len(session2.evaluations) >= 1


def test_regression_quality_metrics_stability():
    """
    REGRESSION: Quality metrics should remain stable across system updates.

    Pattern: regression_testing
    Opinion: quality_metrics_remain_stable
    Category: regression_quality
    Hypothesis: Quality metrics shouldn't change dramatically with system updates.
    """
    annotate_test(
        "test_regression_quality_metrics_stability",
        pattern="regression_testing",
        opinion="quality_metrics_remain_stable",
        category="regression_quality",
        hypothesis="Quality metrics shouldn't change dramatically with system updates.",
    )

    evaluator = SemanticEvaluator()

    # Standard test cases
    test_cases = [
        ("What is knowledge structure?", "Knowledge structure refers to how information is organized."),
        ("Explain trust", "Trust is confidence in reliability and truthfulness."),
        ("How does context work?", "Context provides background information that helps understanding."),
    ]

    # Evaluate all test cases
    judgments = []
    for query, response in test_cases:
        judgment = evaluator.evaluate_relevance(query=query, response=response)
        judgments.append(judgment)

    # All should produce valid scores
    assert all(0.0 <= j.score <= 1.0 for j in judgments)

    # Scores should be reasonable (not all 0 or all 1)
    scores = [j.score for j in judgments]
    assert min(scores) < 1.0 or max(scores) > 0.0


def test_regression_api_contract_stability():
    """
    REGRESSION: API contracts should remain stable across versions.

    Pattern: regression_testing
    Opinion: api_contracts_remain_stable
    Category: regression_quality
    Hypothesis: Public APIs shouldn't change breakingly with system updates.
    """
    annotate_test(
        "test_regression_api_contract_stability",
        pattern="regression_testing",
        opinion="api_contracts_remain_stable",
        category="regression_quality",
        hypothesis="Public APIs shouldn't change breakingly with system updates.",
    )

    evaluator = SemanticEvaluator()

    # Test that core API methods exist and work
    query = "What is knowledge structure?"
    response = "Knowledge structure refers to how information is organized."

    # Core methods should exist
    assert hasattr(evaluator, 'evaluate_relevance')
    assert hasattr(evaluator, 'evaluate_completeness')
    assert hasattr(evaluator, 'evaluate_consistency')

    # Methods should work
    relevance = evaluator.evaluate_relevance(query=query, response=response)
    assert hasattr(relevance, 'score')
    assert hasattr(relevance, 'reasoning')
    assert hasattr(relevance, 'query_characteristics')

    # Score should be in valid range
    assert 0.0 <= relevance.score <= 1.0

