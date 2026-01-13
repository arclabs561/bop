"""Integration tests for quality systems working together.

Tests interactions between: LLM, MCP tools, quality feedback, adaptive learning,
semantic evaluation, hierarchical session management.
"""

import tempfile
from pathlib import Path

import pytest

from bop.adaptive_quality import AdaptiveQualityManager
from bop.quality_feedback import QualityFeedbackLoop
from bop.semantic_eval import SemanticEvaluator
from bop.session_manager import HierarchicalSessionManager
from tests.test_annotations import annotate_test


@pytest.mark.asyncio
async def test_integration_quality_feedback_with_adaptive_learning():
    """
    INTEGRATION: Quality feedback should inform adaptive learning.

    Pattern: integration_testing
    Opinion: quality_feedback_informs_adaptive_learning
    Category: integration_quality
    Hypothesis: Quality feedback loop should provide data to adaptive quality manager.
    """
    annotate_test(
        "test_integration_quality_feedback_with_adaptive_learning",
        pattern="integration_testing",
        opinion="quality_feedback_informs_adaptive_learning",
        category="integration_quality",
        hypothesis="Quality feedback loop should provide data to adaptive quality manager.",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        learning_path = Path(tmpdir) / "learning.json"

        feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=False,
        )

        adaptive = AdaptiveQualityManager(
            quality_feedback=feedback,
            learning_data_path=learning_path,
        )

        # Evaluate a response
        result = feedback.evaluate_and_learn(
            query="What is knowledge structure?",
            response="Knowledge structure refers to how information is organized.",
            schema="chain_of_thought",
        )

        # Adaptive manager should be able to learn from feedback
        assert result is not None
        assert len(feedback.history) > 0

        # Adaptive manager should be able to get optimal schema
        strategy = adaptive.get_adaptive_strategy(
            query="What is knowledge structure?",
        )
        assert strategy is not None
        assert strategy.schema_selection is not None


@pytest.mark.asyncio
async def test_integration_semantic_eval_with_quality_feedback():
    """
    INTEGRATION: Semantic evaluation should integrate with quality feedback.

    Pattern: integration_testing
    Opinion: semantic_eval_integrates_with_quality_feedback
    Category: integration_quality
    Hypothesis: Semantic evaluator should provide judgments to quality feedback loop.
    """
    annotate_test(
        "test_integration_semantic_eval_with_quality_feedback",
        pattern="integration_testing",
        opinion="semantic_eval_integrates_with_quality_feedback",
        category="integration_quality",
        hypothesis="Semantic evaluator should provide judgments to quality feedback loop.",
    )

    evaluator = SemanticEvaluator()
    feedback = QualityFeedbackLoop(use_sessions=False)

    query = "What is knowledge structure?"
    response = "Knowledge structure refers to how information is organized and connected."

    # Semantic evaluation
    relevance_judgment = evaluator.evaluate_relevance(query=query, response=response)

    # Quality feedback should use semantic evaluation
    feedback_result = feedback.evaluate_and_learn(
        query=query,
        response=response,
    )

    # Both should produce valid results
    assert 0.0 <= relevance_judgment.score <= 1.0
    assert feedback_result is not None
    assert len(feedback.history) > 0


@pytest.mark.asyncio
async def test_integration_hierarchical_sessions_with_quality_feedback():
    """
    INTEGRATION: Hierarchical session management should work with quality feedback.

    Pattern: integration_testing
    Opinion: hierarchical_sessions_work_with_quality_feedback
    Category: integration_quality
    Hypothesis: Quality feedback should store evaluations in hierarchical sessions.
    """
    annotate_test(
        "test_integration_hierarchical_sessions_with_quality_feedback",
        pattern="integration_testing",
        opinion="hierarchical_sessions_work_with_quality_feedback",
        category="integration_quality",
        hypothesis="Quality feedback should store evaluations in hierarchical sessions.",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        sessions_path = Path(tmpdir) / "sessions"
        sessions_path.mkdir()

        HierarchicalSessionManager(
            sessions_dir=sessions_path,
        )

        feedback = QualityFeedbackLoop(
            evaluation_history_path=sessions_path.parent / "history.json",
            use_sessions=True,
        )

        # Evaluate with session management
        feedback.evaluate_and_learn(
            query="What is knowledge structure?",
            response="Knowledge structure refers to how information is organized.",
        )

        # Session should contain evaluation (feedback manages its own sessions)
        sessions = feedback.session_manager.list_sessions(limit=1)
        assert len(sessions) > 0
        session = sessions[0]  # list_sessions returns Session objects directly
        assert session is not None
        assert len(session.evaluations) > 0


@pytest.mark.asyncio
async def test_integration_adaptive_learning_with_sessions():
    """
    INTEGRATION: Adaptive learning should work with hierarchical sessions.

    Pattern: integration_testing
    Opinion: adaptive_learning_works_with_sessions
    Category: integration_quality
    Hypothesis: Adaptive quality manager should learn from hierarchical session data.
    """
    annotate_test(
        "test_integration_adaptive_learning_with_sessions",
        pattern="integration_testing",
        opinion="adaptive_learning_works_with_sessions",
        category="integration_quality",
        hypothesis="Adaptive quality manager should learn from hierarchical session data.",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        sessions_path = Path(tmpdir) / "sessions"
        sessions_path.mkdir()
        learning_path = Path(tmpdir) / "learning.json"

        session_manager = HierarchicalSessionManager(
            sessions_dir=sessions_path,
        )

        feedback = QualityFeedbackLoop(
            evaluation_history_path=sessions_path.parent / "history.json",
            use_sessions=True,
        )
        adaptive = AdaptiveQualityManager(
            quality_feedback=feedback,
            learning_data_path=learning_path,
        )

        # Create session with evaluations
        session_manager.create_session("test_session", "test_group")
        session_manager.add_evaluation(
            session_id="test_session",
            query="What is knowledge structure?",
            response="Knowledge structure refers to how information is organized.",
            response_length=len("Knowledge structure refers to how information is organized."),
            score=0.8,
            judgment_type="relevance",
            quality_flags=[],
            reasoning="Test evaluation",
            metadata={"schema": "chain_of_thought"},
        )
        session_manager.flush_buffer()

        # Adaptive manager should be able to learn from sessions
        strategy = adaptive.get_adaptive_strategy(
            query="What is knowledge structure?",
        )
        assert strategy is not None
        assert strategy.schema_selection is not None


@pytest.mark.asyncio
async def test_integration_end_to_end_quality_pipeline():
    """
    INTEGRATION: End-to-end quality pipeline should work.

    Pattern: integration_testing
    Opinion: end_to_end_quality_pipeline_works
    Category: integration_quality
    Hypothesis: Complete quality pipeline (evaluation → feedback → learning → adaptation) should work.
    """
    annotate_test(
        "test_integration_end_to_end_quality_pipeline",
        pattern="integration_testing",
        opinion="end_to_end_quality_pipeline_works",
        category="integration_quality",
        hypothesis="Complete quality pipeline should work end-to-end.",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        sessions_path = Path(tmpdir) / "sessions"
        sessions_path.mkdir()
        history_path = Path(tmpdir) / "history.json"
        learning_path = Path(tmpdir) / "learning.json"

        HierarchicalSessionManager(
            sessions_dir=sessions_path,
        )

        feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=True,
        )

        adaptive = AdaptiveQualityManager(
            quality_feedback=feedback,
            learning_data_path=learning_path,
        )

        evaluator = SemanticEvaluator()

        # Complete pipeline
        query = "What is knowledge structure?"
        response = "Knowledge structure refers to how information is organized and connected."

        # 1. Semantic evaluation
        judgment = evaluator.evaluate_relevance(query=query, response=response)

        # 2. Quality feedback
        feedback_result = feedback.evaluate_and_learn(
            query=query,
            response=response,
            schema="chain_of_thought",
        )

        # 3. Adaptive learning
        feedback.session_manager.flush_buffer()
        strategy = adaptive.get_adaptive_strategy(
            query=query,
        )

        # All components should work together
        assert 0.0 <= judgment.score <= 1.0
        assert feedback_result is not None
        assert strategy is not None
        assert len(feedback.history) > 0

