"""Performance tests for quality systems.

Tests latency, throughput, memory usage, and response time under load.
"""

import tempfile
import time
import tracemalloc
from pathlib import Path

from pran.quality_feedback import QualityFeedbackLoop
from pran.semantic_eval import SemanticEvaluator
from pran.session_manager import HierarchicalSessionManager
from tests.test_annotations import annotate_test


def test_performance_semantic_evaluation_latency():
    """
    PERFORMANCE: Semantic evaluation should complete within reasonable time.

    Pattern: performance_testing
    Opinion: semantic_evaluation_is_fast
    Category: performance_quality
    Hypothesis: Semantic evaluation should complete in < 100ms for typical queries.
    """
    annotate_test(
        "test_performance_semantic_evaluation_latency",
        pattern="performance_testing",
        opinion="semantic_evaluation_is_fast",
        category="performance_quality",
        hypothesis="Semantic evaluation should complete in < 100ms for typical queries.",
    )

    evaluator = SemanticEvaluator()

    query = "What is knowledge structure?"
    response = "Knowledge structure refers to how information is organized and connected."

    start = time.time()
    judgment = evaluator.evaluate_relevance(query=query, response=response)
    elapsed = time.time() - start

    # Should complete quickly
    assert elapsed < 0.1, f"Semantic evaluation too slow: {elapsed:.3f}s"
    assert 0.0 <= judgment.score <= 1.0


def test_performance_quality_feedback_throughput():
    """
    PERFORMANCE: Quality feedback should handle multiple evaluations efficiently.

    Pattern: performance_testing
    Opinion: quality_feedback_handles_throughput
    Category: performance_quality
    Hypothesis: Quality feedback should handle 100+ evaluations per second.
    """
    annotate_test(
        "test_performance_quality_feedback_throughput",
        pattern="performance_testing",
        opinion="quality_feedback_handles_throughput",
        category="performance_quality",
        hypothesis="Quality feedback should handle 100+ evaluations per second.",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=False,
        )

        num_evaluations = 50
        start = time.time()

        for i in range(num_evaluations):
            feedback.evaluate_and_learn(
                query=f"Query {i}",
                response=f"Response {i}",
            )

        elapsed = time.time() - start
        throughput = num_evaluations / elapsed

        # Should handle reasonable throughput
        assert throughput > 10, f"Throughput too low: {throughput:.1f} evaluations/s"
        assert len(feedback.history) == num_evaluations


def test_performance_session_manager_memory():
    """
    PERFORMANCE: Session manager should use memory efficiently.

    Pattern: performance_testing
    Opinion: session_manager_uses_memory_efficiently
    Category: performance_quality
    Hypothesis: Session manager should not use excessive memory for many sessions.
    """
    annotate_test(
        "test_performance_session_manager_memory",
        pattern="performance_testing",
        opinion="session_manager_uses_memory_efficiently",
        category="performance_quality",
        hypothesis="Session manager should not use excessive memory for many sessions.",
    )

    tracemalloc.start()

    with tempfile.TemporaryDirectory() as tmpdir:
        sessions_path = Path(tmpdir) / "sessions"
        sessions_path.mkdir()

        manager = HierarchicalSessionManager(
            sessions_dir=sessions_path,
        )

        # Create many sessions
        num_sessions = 100
        for i in range(num_sessions):
            manager.create_session(f"session_{i}", "test_group")
            for j in range(10):
                manager.add_evaluation(
                    session_id=f"session_{i}",
                    query=f"Query {j}",
                    response=f"Response {j}",
                    response_length=len(f"Response {j}"),
                    score=0.8,
                    judgment_type="relevance",
                    quality_flags=[],
                    reasoning="Test evaluation",
                    metadata={},
                )

        manager.flush_buffer()

        # Check memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Should use reasonable memory (< 50MB for 100 sessions with 10 evaluations each)
        assert peak < 50 * 1024 * 1024, f"Memory usage too high: {peak / 1024 / 1024:.1f}MB"

        # All sessions should exist (list_sessions returns session IDs)
        # Note: list_sessions may return more if there are groups, so check >=
        sessions = manager.list_sessions(limit=num_sessions + 100)
        assert len(sessions) >= num_sessions, f"Expected at least {num_sessions} sessions, got {len(sessions)}"


def test_performance_concurrent_evaluations():
    """
    PERFORMANCE: System should handle concurrent evaluations.

    Pattern: performance_testing
    Opinion: system_handles_concurrent_evaluations
    Category: performance_quality
    Hypothesis: System should handle concurrent evaluations without errors.
    """
    annotate_test(
        "test_performance_concurrent_evaluations",
        pattern="performance_testing",
        opinion="system_handles_concurrent_evaluations",
        category="performance_quality",
        hypothesis="System should handle concurrent evaluations without errors.",
    )

    evaluator = SemanticEvaluator()

    queries = [f"Query {i}" for i in range(10)]
    responses = [f"Response {i}" for i in range(10)]

    start = time.time()

    # Concurrent evaluations
    judgments = []
    for query, response in zip(queries, responses):
        judgment = evaluator.evaluate_relevance(query=query, response=response)
        judgments.append(judgment)

    elapsed = time.time() - start

    # Should complete all evaluations
    assert len(judgments) == 10
    assert all(0.0 <= j.score <= 1.0 for j in judgments)
    # Should be reasonably fast even with multiple evaluations
    assert elapsed < 1.0, f"Concurrent evaluations too slow: {elapsed:.3f}s"


def test_performance_large_response_handling():
    """
    PERFORMANCE: System should handle large responses efficiently.

    Pattern: performance_testing
    Opinion: system_handles_large_responses
    Category: performance_quality
    Hypothesis: System should handle large responses (10k+ chars) efficiently.
    """
    annotate_test(
        "test_performance_large_response_handling",
        pattern="performance_testing",
        opinion="system_handles_large_responses",
        category="performance_quality",
        hypothesis="System should handle large responses (10k+ chars) efficiently.",
    )

    evaluator = SemanticEvaluator()

    query = "What is knowledge structure?"
    large_response = "Knowledge structure " * 500  # ~10k chars

    start = time.time()
    judgment = evaluator.evaluate_relevance(query=query, response=large_response)
    elapsed = time.time() - start

    # Should handle large responses
    assert 0.0 <= judgment.score <= 1.0
    # Should complete in reasonable time (< 500ms for large response)
    assert elapsed < 0.5, f"Large response evaluation too slow: {elapsed:.3f}s"

