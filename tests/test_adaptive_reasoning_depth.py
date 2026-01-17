"""Tests for adaptive reasoning depth allocation."""

import tempfile
from pathlib import Path

from pran.adaptive_quality import AdaptiveQualityManager
from pran.quality_feedback import QualityFeedbackLoop


def test_estimate_reasoning_depth():
    """Test reasoning depth estimation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)

        # Add learning data: 3 subproblems achieves 0.8 quality
        for _ in range(5):
            manager.update_from_evaluation(
                query="What is d-separation?",
                schema="decompose_and_synthesize",
                used_research=True,
                response_length=200,
                quality_score=0.8,
                num_subproblems=3,
            )

        depth = manager.estimate_reasoning_depth("What is d-separation?")
        assert depth == 3


def test_estimate_reasoning_depth_default():
    """Test reasoning depth estimation with no learning data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)

        depth = manager.estimate_reasoning_depth("What is trust?")
        assert depth == 3  # Default


def test_should_early_stop():
    """Test early stopping logic."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)

        # Add learning: 3 subproblems achieves 0.8 quality
        manager.update_from_evaluation(
            query="What is trust?",
            schema="decompose_and_synthesize",
            used_research=True,
            response_length=200,
            quality_score=0.8,
            num_subproblems=3,
        )

        query_type = manager._classify_query("What is trust?")

        # Should stop early if quality threshold met (95% of 0.8 = 0.76)
        should_stop = manager.should_early_stop(
            current_quality=0.78,  # Above threshold
            query_type=query_type,
            num_subproblems_completed=3,
        )
        assert should_stop is True

        # Should not stop if quality below threshold
        should_stop = manager.should_early_stop(
            current_quality=0.70,  # Below threshold
            query_type=query_type,
            num_subproblems_completed=3,
        )
        assert should_stop is False


def test_should_early_stop_no_data():
    """Test early stopping with no learning data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)

        should_stop = manager.should_early_stop(
            current_quality=0.8,
            query_type="analytical",
            num_subproblems_completed=3,
        )
        assert should_stop is False  # No data, continue


def test_get_early_stop_threshold():
    """Test getting early stop threshold."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)

        # Add learning data
        manager.update_from_evaluation(
            query="What is trust?",
            schema="decompose_and_synthesize",
            used_research=True,
            response_length=200,
            quality_score=0.8,
            num_subproblems=3,
        )

        query_type = manager._classify_query("What is trust?")
        threshold = manager._get_early_stop_threshold(query_type)

        assert threshold is not None
        assert 0.0 <= threshold <= 1.0
        assert threshold <= 0.8  # Should be 95% of learned threshold


def test_adaptive_strategy_includes_reasoning_depth():
    """Test that AdaptiveStrategy includes reasoning depth."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)

        strategy = manager.get_adaptive_strategy("What is d-separation?")

        assert hasattr(strategy, 'reasoning_depth')
        assert strategy.reasoning_depth >= 1
        assert hasattr(strategy, 'early_stop_threshold')
        # early_stop_threshold may be None if no data


def test_update_from_evaluation_tracks_depth():
    """Test that update_from_evaluation tracks reasoning depth."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)

        manager.update_from_evaluation(
            query="What is trust?",
            schema="decompose_and_synthesize",
            used_research=True,
            response_length=200,
            quality_score=0.7,
            num_subproblems=4,
        )

        query_type = manager._classify_query("What is trust?")
        depth_data = manager.query_type_to_depth.get(query_type, [])

        assert len(depth_data) > 0
        assert (4, 0.7) in depth_data

