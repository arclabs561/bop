"""Tests for adaptive quality manager."""

import tempfile
from pathlib import Path

from bop.adaptive_quality import AdaptiveQualityManager, AdaptiveStrategy
from bop.quality_feedback import QualityFeedbackLoop


def test_adaptive_manager_initialization():
    """Test adaptive manager initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        learning_path = Path(tmpdir) / "test_learning.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback, learning_data_path=learning_path)

        assert manager.quality_feedback == feedback
        # Structures may be empty or populated from history
        assert isinstance(manager.query_type_to_schema, dict)
        assert isinstance(manager.query_type_to_length, dict)


def test_query_classification():
    """Test query classification."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)

        assert manager._classify_query("What is trust?") == "factual"
        assert manager._classify_query("How does it work?") == "procedural"
        assert manager._classify_query("Why is this important?") == "analytical"
        assert manager._classify_query("Compare A and B") == "comparative"
        assert manager._classify_query("Analyze the results") == "evaluative"


def test_get_adaptive_strategy():
    """Test getting adaptive strategy."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)

        strategy = manager.get_adaptive_strategy("What is trust?")

        assert isinstance(strategy, AdaptiveStrategy)
        assert strategy.schema_selection is not None
        assert strategy.expected_length > 0
        assert isinstance(strategy.should_use_research, bool)
        assert 0.0 <= strategy.confidence <= 1.0


def test_update_from_evaluation():
    """Test updating learning from evaluation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)

        manager.update_from_evaluation(
            query="What is trust?",
            schema="chain_of_thought",
            used_research=False,
            response_length=150,
            quality_score=0.7,
        )

        # Should have learned something
        assert len(manager.query_type_to_schema) > 0 or len(manager.query_type_to_length) > 0


def test_get_improvement_suggestions():
    """Test getting improvement suggestions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)

        # Add some learning data
        manager.update_from_evaluation(
            query="What is trust?",
            schema="chain_of_thought",
            used_research=False,
            response_length=150,
            quality_score=0.8,
        )

        suggestions = manager.get_improvement_suggestions("What is trust?", 0.5)

        assert isinstance(suggestions, list)
        # May or may not have suggestions depending on learning data
        for suggestion in suggestions:
            assert "type" in suggestion
            assert "message" in suggestion
            assert "priority" in suggestion


def test_get_performance_insights():
    """Test getting performance insights."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)

        # Add some learning data
        manager.update_from_evaluation(
            query="What is trust?",
            schema="chain_of_thought",
            used_research=False,
            response_length=150,
            quality_score=0.7,
        )

        manager.update_from_evaluation(
            query="What is trust?",
            schema="chain_of_thought",
            used_research=True,
            response_length=200,
            quality_score=0.8,
        )

        insights = manager.get_performance_insights()

        assert "query_type_performance" in insights
        assert "schema_recommendations" in insights
        assert "research_effectiveness" in insights
        assert "length_preferences" in insights


def test_agent_integration():
    """Test that agent integrates adaptive manager."""
    from bop.agent import KnowledgeAgent

    agent = KnowledgeAgent(enable_quality_feedback=True)

    assert agent.adaptive_manager is not None
    assert isinstance(agent.adaptive_manager, AdaptiveQualityManager)

