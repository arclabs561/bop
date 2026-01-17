"""Edge case tests for adaptive quality manager."""

import tempfile
from pathlib import Path

from pran.adaptive_quality import AdaptiveQualityManager
from pran.quality_feedback import QualityFeedbackLoop


def test_adaptive_manager_empty_history():
    """Test adaptive manager with no history."""
    with tempfile.TemporaryDirectory() as tmpdir:
        feedback = QualityFeedbackLoop(
            evaluation_history_path=Path(tmpdir) / "history.json",
            use_sessions=False,
        )

        manager = AdaptiveQualityManager(feedback)

        # Should still provide strategy
        strategy = manager.get_adaptive_strategy("test query")
        assert strategy is not None
        assert strategy.schema_selection is not None
        assert 0.0 <= strategy.confidence <= 1.0


def test_adaptive_manager_corrupted_learning_file():
    """Test recovery from corrupted learning data file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        learning_path = Path(tmpdir) / "learning.json"
        learning_path.write_text("corrupted json {")

        feedback = QualityFeedbackLoop(
            evaluation_history_path=Path(tmpdir) / "history.json",
        )

        # Should handle gracefully and rebuild from history
        manager = AdaptiveQualityManager(feedback, learning_data_path=learning_path)

        # Should still work
        strategy = manager.get_adaptive_strategy("test")
        assert strategy is not None


def test_adaptive_manager_session_learning_failure():
    """Test adaptive manager handles session learning failures."""
    with tempfile.TemporaryDirectory() as tmpdir:
        feedback = QualityFeedbackLoop(
            evaluation_history_path=Path(tmpdir) / "history.json",
            use_sessions=True,
        )

        # Mock session manager to fail
        if feedback.session_manager:

            def failing_list(*args, **kwargs):
                raise Exception("Session list failure")

            feedback.session_manager.list_sessions = failing_list

        # Should handle gracefully
        manager = AdaptiveQualityManager(feedback)
        manager._learn_from_sessions()  # Should not crash

        strategy = manager.get_adaptive_strategy("test")
        assert strategy is not None


def test_adaptive_manager_invalid_query():
    """Test adaptive manager with edge case queries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        feedback = QualityFeedbackLoop(
            evaluation_history_path=Path(tmpdir) / "history.json",
        )
        manager = AdaptiveQualityManager(feedback)

        # Empty query
        strategy = manager.get_adaptive_strategy("")
        assert strategy is not None

        # Very long query
        long_query = "x" * 10000
        strategy = manager.get_adaptive_strategy(long_query)
        assert strategy is not None

        # Query with special characters
        special_query = "What is trust? @#$%^&*()"
        strategy = manager.get_adaptive_strategy(special_query)
        assert strategy is not None

