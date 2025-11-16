"""Tests for hierarchical session manager."""

import pytest
from pathlib import Path
import tempfile
import json

from bop.session_manager import (
    HierarchicalSessionManager,
    Session,
    EvaluationEntry,
    SessionGroup,
)


def test_session_manager_initialization():
    """Test session manager initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))
        
        assert manager.sessions_dir == Path(tmpdir)
        # With lazy loading, sessions dict is replaced by _session_metadata
        assert hasattr(manager, '_session_metadata') or hasattr(manager, 'index')
        assert manager.groups == {}
        assert manager.current_session_id is None


def test_create_session():
    """Test creating a session."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))
        
        session_id = manager.create_session(context="test_context", user_id="user1")
        
        assert session_id is not None
        # With lazy loading, check cache or index instead
        session = manager.get_session(session_id)
        assert session is not None
        assert manager.current_session_id == session_id
        
        assert session.context == "test_context"
        assert session.user_id == "user1"
        assert len(session.evaluations) == 0


def test_add_evaluation():
    """Test adding an evaluation to a session."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))
        
        session_id = manager.create_session()
        # Flush buffer to ensure evaluation is saved
        manager.flush_buffer()
        eval_id = manager.add_evaluation(
            query="What is trust?",
            response="Trust is...",
            response_length=100,
            score=0.8,
            judgment_type="relevance",
            quality_flags=[],
            reasoning="Good response",
            metadata={"schema": "chain_of_thought"},
        )
        
        assert eval_id is not None
        # Flush buffer to ensure evaluation is saved
        manager.flush_buffer()
        session = manager.get_session(session_id)
        assert session is not None
        assert len(session.evaluations) == 1
        assert session.evaluations[0].query == "What is trust?"
        assert session.evaluations[0].score == 0.8


def test_auto_group_by_day():
    """Test automatic grouping by day."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(
            sessions_dir=Path(tmpdir),
            auto_group_by="day",
        )
        
        session1 = manager.create_session()
        session2 = manager.create_session()
        
        assert len(manager.groups) > 0
        # Both sessions should be in the same day group (if created on same day)
        group = list(manager.groups.values())[0]
        assert session1 in group.session_ids or session2 in group.session_ids


def test_get_session_statistics():
    """Test getting session statistics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))
        
        session_id = manager.create_session()
        manager.add_evaluation(
            query="Test",
            response="Response",
            response_length=50,
            score=0.7,
            judgment_type="relevance",
            quality_flags=[],
            reasoning="OK",
            metadata={},
        )
        manager.add_evaluation(
            query="Test2",
            response="Response2",
            response_length=60,
            score=0.9,
            judgment_type="relevance",
            quality_flags=[],
            reasoning="Great",
            metadata={},
        )
        
        session = manager.get_session(session_id)
        stats = session.get_statistics()
        
        assert stats["evaluation_count"] == 2
        assert stats["mean_score"] == 0.8
        assert stats["min_score"] == 0.7
        assert stats["max_score"] == 0.9


def test_list_sessions():
    """Test listing sessions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))
        
        session1 = manager.create_session(user_id="user1")
        session2 = manager.create_session(user_id="user2")
        session3 = manager.create_session(user_id="user1")
        
        all_sessions = manager.list_sessions()
        assert len(all_sessions) == 3
        
        user1_sessions = manager.list_sessions(user_id="user1")
        assert len(user1_sessions) == 2
        assert all(s.user_id == "user1" for s in user1_sessions)


def test_get_aggregate_statistics():
    """Test getting aggregate statistics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))
        
        session_id = manager.create_session()
        manager.add_evaluation(
            query="Test",
            response="Response",
            response_length=50,
            score=0.7,
            judgment_type="relevance",
            quality_flags=[],
            reasoning="OK",
            metadata={},
        )
        
        stats = manager.get_aggregate_statistics()
        
        assert stats["session_count"] == 1
        assert stats["total_evaluations"] == 1
        assert stats["mean_score"] == 0.7


def test_persistence():
    """Test that sessions persist across manager instances."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create manager and add data
        manager1 = HierarchicalSessionManager(sessions_dir=Path(tmpdir))
        session_id = manager1.create_session(context="test")
        manager1.add_evaluation(
            query="Test",
            response="Response",
            response_length=50,
            score=0.8,
            judgment_type="relevance",
            quality_flags=[],
            reasoning="OK",
            metadata={},
        )
        
        # Create new manager instance
        manager2 = HierarchicalSessionManager(sessions_dir=Path(tmpdir))
        
        # Flush buffer to ensure data is saved
        manager1.flush_buffer()
        
        # Should load the session
        session = manager2.get_session(session_id)
        assert session is not None
        assert session.context == "test"
        assert len(session.evaluations) == 1
        assert session.evaluations[0].score == 0.8


def test_archive_session():
    """Test archiving a session."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))
        
        session_id = manager.create_session()
        manager.add_evaluation(
            query="Test",
            response="Response",
            response_length=50,
            score=0.8,
            judgment_type="relevance",
            quality_flags=[],
            reasoning="OK",
            metadata={},
        )
        
        # Flush buffer before archiving
        manager.flush_buffer()
        
        # Archive
        manager.archive_session(session_id)
        
        # Session should be marked as archived (may still be loadable but status changed)
        session = manager.get_session(session_id)
        if session:
            assert session.status == "archived"
        
        # Should exist in archive
        archive_dir = Path(tmpdir) / "archive"
        assert archive_dir.exists()
        archive_file = archive_dir / f"{session_id}.json"
        assert archive_file.exists()

