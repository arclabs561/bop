"""Edge case tests for quality feedback loop."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from bop.quality_feedback import QualityFeedbackLoop
from bop.session_manager import HierarchicalSessionManager


def test_quality_feedback_without_sessions():
    """Test quality feedback works without session management."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=False,
        )
        
        result = feedback.evaluate_and_learn(
            query="test",
            response="response",
        )
        
        assert "relevance" in result
        assert result["relevance"] >= 0.0
        assert len(feedback.history) > 0


def test_quality_feedback_session_failure():
    """Test quality feedback handles session manager failures."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=True,
        )
        
        # Mock session manager to fail
        if feedback.session_manager:
            original_add = feedback.session_manager.add_evaluation
            
            def failing_add(*args, **kwargs):
                raise Exception("Session manager failure")
            
            feedback.session_manager.add_evaluation = failing_add
        
        # Should still work (fallback to flat history)
        result = feedback.evaluate_and_learn(
            query="test",
            response="response",
        )
        
        assert "relevance" in result


def test_quality_feedback_empty_response():
    """Test quality feedback with empty response."""
    with tempfile.TemporaryDirectory() as tmpdir:
        feedback = QualityFeedbackLoop(
            evaluation_history_path=Path(tmpdir) / "history.json",
        )
        
        result = feedback.evaluate_and_learn(
            query="test query",
            response="",  # Empty response
        )
        
        assert "relevance" in result
        assert "too_short" in result.get("quality_flags", [])


def test_quality_feedback_very_long_response():
    """Test quality feedback with very long response."""
    with tempfile.TemporaryDirectory() as tmpdir:
        feedback = QualityFeedbackLoop(
            evaluation_history_path=Path(tmpdir) / "history.json",
        )
        
        long_response = "x" * 10000
        result = feedback.evaluate_and_learn(
            query="test",
            response=long_response,
        )
        
        assert "relevance" in result
        # Response should be truncated in storage
        if feedback.session_manager:
            manager = feedback.session_manager
            manager.flush_buffer()
            session = manager.get_current_session()
            if session and session.evaluations:
                stored_response = session.evaluations[0].response
                assert len(stored_response) <= 1000  # Truncated


def test_quality_feedback_history_loading_failure():
    """Test recovery from corrupted history file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        
        # Create corrupted history
        history_path.write_text("corrupted json {")
        
        # Should handle gracefully
        feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=False,
        )
        
        # Should still work
        assert feedback.history == [] or isinstance(feedback.history, list)


def test_quality_feedback_unified_storage_failure():
    """Test quality feedback handles unified storage failures."""
    with tempfile.TemporaryDirectory() as tmpdir:
        feedback = QualityFeedbackLoop(
            evaluation_history_path=Path(tmpdir) / "history.json",
            use_sessions=True,
        )
        
        # Mock unified storage to fail
        if hasattr(feedback, 'unified_storage') and feedback.unified_storage:
            original_get = feedback.unified_storage.get_history_view
            
            def failing_get(*args, **kwargs):
                raise Exception("Unified storage failure")
            
            feedback.unified_storage.get_history_view = failing_get
        
        # Should fallback gracefully
        result = feedback.evaluate_and_learn(
            query="test",
            response="response",
        )
        
        assert "relevance" in result

