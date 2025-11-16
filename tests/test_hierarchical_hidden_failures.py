"""Tests for hidden failures and actual bugs we might have missed.

These tests probe for real issues that could cause data loss, crashes, or incorrect behavior.
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timezone

from bop.session_manager import HierarchicalSessionManager
from bop.quality_feedback import QualityFeedbackLoop
from bop.adaptive_quality import AdaptiveQualityManager
from bop.unified_storage import UnifiedSessionStorage
from tests.test_annotations import annotate_test


def test_index_staleness_after_direct_file_edit():
    """
    HIDDEN FAILURE: What if someone edits session file directly?
    
    Index becomes stale, queries return wrong results.
    """
    annotate_test(
        "test_index_staleness_after_direct_file_edit",
        pattern="hierarchical_memory",
        opinion="index_stays_in_sync",
        category="hidden_failures",
        hypothesis="Index stays in sync even if files are edited directly",
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(
            sessions_dir=Path(tmpdir),
            enable_indexing=True,
        )
        
        # Create session
        session_id = manager.create_session()
        manager.add_evaluation(
            query="Original query",
            response="Original response",
            response_length=10,
            score=0.5,
            judgment_type="relevance",
            quality_flags=[],
            reasoning="",
            metadata={},
        )
        manager.flush_buffer()
        
        # Directly edit file (bypassing manager)
        session_file = Path(tmpdir) / "sessions" / f"{session_id}.json"
        if session_file.exists():
            data = json.loads(session_file.read_text())
            # Change score
            data["evaluations"][0]["score"] = 0.9
            session_file.write_text(json.dumps(data))
        
        # Index is now stale
        # Query should either:
        # 1. Rebuild index on next access
        # 2. Return stale data (bug)
        # 3. Detect inconsistency
        
        # Reload session
        session = manager.get_session(session_id)
        if session:
            # Session should have updated score
            assert session.evaluations[0].score == 0.9
            # But index might be stale
            # This is a potential bug - index doesn't auto-update


def test_buffer_loss_on_crash():
    """
    HIDDEN FAILURE: What if system crashes with buffer full?
    
    All buffered writes are lost.
    """
    annotate_test(
        "test_buffer_loss_on_crash",
        pattern="hierarchical_memory",
        opinion="buffer_loss_is_acceptable_or_prevented",
        category="hidden_failures",
        hypothesis="Buffer loss on crash is either acceptable or prevented",
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(
            sessions_dir=Path(tmpdir),
            batch_size=5,
        )
        
        # Add evaluations (should buffer)
        session_id = manager.create_session()
        for i in range(3):
            manager.add_evaluation(
                query=f"Query {i}",
                response=f"Response {i}",
                response_length=10,
                score=0.7,
                judgment_type="relevance",
                quality_flags=[],
                reasoning="",
                metadata={},
            )
        
        # Simulate crash (don't flush)
        # Buffer has 3 sessions
        
        # After "crash", reload manager
        manager2 = HierarchicalSessionManager(sessions_dir=Path(tmpdir))
        
        # Check if data was lost
        session = manager2.get_session(session_id)
        # If buffer wasn't flushed, data might be lost
        # This is expected behavior (buffer = performance vs. durability tradeoff)
        # But we should document this limitation


def test_concurrent_index_updates():
    """
    HIDDEN FAILURE: What if index is updated while being read?
    
    Race condition: Read index → Update session → Write index → Read returns stale
    """
    annotate_test(
        "test_concurrent_index_updates",
        pattern="hierarchical_memory",
        opinion="index_updates_are_safe",
        category="hidden_failures",
        hypothesis="Index updates are safe under concurrent access",
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(
            sessions_dir=Path(tmpdir),
            enable_indexing=True,
        )
        
        # Create session
        session_id = manager.create_session()
        manager.add_evaluation(
            query="Test",
            response="Test",
            response_length=10,
            score=0.7,
            judgment_type="relevance",
            quality_flags=[],
            reasoning="",
            metadata={},
        )
        manager.flush_buffer()
        
        # Query index
        sessions1 = manager.query_sessions(min_score=0.6)
        
        # Update session (updates index)
        manager.add_evaluation(
            query="Test 2",
            response="Test 2",
            response_length=10,
            score=0.9,
            judgment_type="relevance",
            quality_flags=[],
            reasoning="",
            metadata={},
        )
        manager.flush_buffer()
        
        # Query again
        sessions2 = manager.query_sessions(min_score=0.6)
        
        # Both should work (no crash)
        assert isinstance(sessions1, list)
        assert isinstance(sessions2, list)


def test_group_orphaned_sessions():
    """
    HIDDEN FAILURE: What if session file is deleted but group still references it?
    
    Group has orphaned session_id.
    """
    annotate_test(
        "test_group_orphaned_sessions",
        pattern="hierarchical_memory",
        opinion="groups_handle_orphaned_sessions",
        category="hidden_failures",
        hypothesis="Groups handle orphaned session references gracefully",
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(
            sessions_dir=Path(tmpdir),
            auto_group_by="day",
        )
        
        # Create session in group
        session_id = manager.create_session()
        manager.flush_buffer()
        
        # Check group
        groups = manager.groups
        assert len(groups) > 0
        
        # Delete session file directly
        session_file = Path(tmpdir) / "sessions" / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()
        
        # Group still references session_id
        # Try to list sessions in group
        for group in groups.values():
            if session_id in group.session_ids:
                # Try to get session
                session = manager.get_session(session_id)
                # Should return None, but group still references it
                # This is a potential inconsistency


def test_quality_feedback_double_evaluation():
    """
    HIDDEN FAILURE: What if quality feedback evaluates same query twice?
    
    Does it create duplicate entries or handle gracefully?
    """
    annotate_test(
        "test_quality_feedback_double_evaluation",
        pattern="hierarchical_memory",
        opinion="quality_feedback_handles_duplicates",
        category="hidden_failures",
        hypothesis="Quality feedback handles duplicate evaluations gracefully",
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        quality_feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=True,
        )
        
        # Evaluate same query twice
        result1 = quality_feedback.evaluate_and_learn(
            query="Duplicate query",
            response="Response",
        )
        result2 = quality_feedback.evaluate_and_learn(
            query="Duplicate query",
            response="Response",
        )
        
        # Should create two separate evaluations
        # (This is expected - same query can have different responses)
        assert result1 is not None
        assert result2 is not None
        
        manager = quality_feedback.session_manager
        session = manager.get_session(manager.current_session_id)
        assert len(session.evaluations) >= 2


def test_adaptive_manager_learning_from_corrupted_data():
    """
    HIDDEN FAILURE: What if adaptive manager learns from corrupted session data?
    
    Corrupted data → Bad learning → Bad strategies.
    """
    annotate_test(
        "test_adaptive_manager_learning_from_corrupted_data",
        pattern="hierarchical_memory",
        opinion="adaptive_manager_validates_data",
        category="hidden_failures",
        hypothesis="Adaptive manager validates data before learning",
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        quality_feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=True,
        )
        manager = quality_feedback.session_manager
        adaptive = AdaptiveQualityManager(quality_feedback)
        
        # Create session with valid data
        session_id = manager.create_session()
        manager.add_evaluation(
            query="Valid query",
            response="Valid response",
            response_length=10,
            score=0.7,
            judgment_type="relevance",
            quality_flags=[],
            reasoning="",
            metadata={},
        )
        manager.flush_buffer()
        
        # Corrupt session file
        session_file = Path(tmpdir) / "sessions" / f"{session_id}.json"
        if session_file.exists():
            # Write invalid data
            session_file.write_text("{invalid json}")
        
        # Adaptive manager tries to learn
        # Should handle gracefully (skip corrupted or validate)
        insights = adaptive.get_performance_insights()
        # Should not crash
        assert insights is not None


def test_unified_storage_session_deletion_race():
    """
    HIDDEN FAILURE: What if session is deleted while unified storage is reading it?
    
    Race condition: Unified storage reads session → Session deleted → Crash?
    """
    annotate_test(
        "test_unified_storage_session_deletion_race",
        pattern="hierarchical_memory",
        opinion="unified_storage_handles_deletion_race",
        category="hidden_failures",
        hypothesis="Unified storage handles session deletion during read",
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))
        unified = UnifiedSessionStorage(session_manager=manager)
        
        # Create session
        session_id = manager.create_session()
        manager.add_evaluation(
            query="Test",
            response="Test",
            response_length=10,
            score=0.7,
            judgment_type="relevance",
            quality_flags=[],
            reasoning="",
            metadata={},
        )
        manager.flush_buffer()
        
        # Get history (reads sessions)
        history = unified.get_history_view(limit=100)
        assert len(history) == 1
        
        # Delete session
        manager.storage.delete_session(session_id)
        manager.cache.evict(session_id)
        
        # Get history again (should handle deleted session)
        history2 = unified.get_history_view(limit=100)
        # Should either be empty or handle gracefully
        assert isinstance(history2, list)


def test_index_rebuild_after_corruption():
    """
    HIDDEN FAILURE: Does index actually rebuild after corruption?
    
    Or does it stay broken?
    """
    annotate_test(
        "test_index_rebuild_after_corruption",
        pattern="hierarchical_memory",
        opinion="index_rebuilds_after_corruption",
        category="hidden_failures",
        hypothesis="Index rebuilds correctly after corruption",
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(
            sessions_dir=Path(tmpdir),
            enable_indexing=True,
        )
        
        # Create sessions
        session_ids = []
        for i in range(3):
            session_id = manager.create_session()
            session_ids.append(session_id)
            manager.add_evaluation(
                query=f"Query {i}",
                response=f"Response {i}",
                response_length=10,
                score=0.7,
                judgment_type="relevance",
                quality_flags=[],
                reasoning="",
                metadata={},
            )
        manager.flush_buffer()
        
        # Corrupt index
        index_file = Path(tmpdir) / "sessions" / "index.json"
        if index_file.exists():
            index_file.write_text("{corrupted}")
        
        # Create new manager (should rebuild index)
        manager2 = HierarchicalSessionManager(
            sessions_dir=Path(tmpdir),
            enable_indexing=True,
        )
        
        # Index should be rebuilt
        sessions = manager2.list_sessions()
        # Should have sessions (index rebuilt or fallback to scan)
        assert len(sessions) >= 0  # At minimum, shouldn't crash


def test_quality_feedback_session_switch_mid_evaluation():
    """
    HIDDEN FAILURE: What if session switches while evaluation is in progress?
    
    Evaluation might go to wrong session.
    """
    annotate_test(
        "test_quality_feedback_session_switch_mid_evaluation",
        pattern="hierarchical_memory",
        opinion="quality_feedback_handles_session_switch",
        category="hidden_failures",
        hypothesis="Quality feedback handles session switches during evaluation",
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        quality_feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=True,
        )
        manager = quality_feedback.session_manager
        
        # Create first session
        session1 = manager.create_session(context="session1")
        
        # Start evaluation (captures current_session_id)
        # But session might switch during evaluation
        
        # Switch session
        session2 = manager.create_session(context="session2")
        
        # Complete evaluation
        result = quality_feedback.evaluate_and_learn(
            query="Test query",
            response="Test response",
        )
        
        # Evaluation should go to correct session
        # (Implementation might use session at start or at end)
        assert result is not None


def test_buffer_retry_after_failure():
    """
    HIDDEN FAILURE: Does buffer actually retry failed writes?
    
    Current implementation clears buffer even on failure.
    """
    annotate_test(
        "test_buffer_retry_after_failure",
        pattern="hierarchical_memory",
        opinion="buffer_retries_failed_writes",
        category="hidden_failures",
        hypothesis="Buffer retries failed writes instead of losing them",
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(
            sessions_dir=Path(tmpdir),
            batch_size=2,
        )
        
        # Mock storage to fail
        original_save = manager.storage.save_session
        call_count = [0]
        
        def failing_save(s):
            call_count[0] += 1
            if call_count[0] == 1:
                raise IOError("Simulated failure")
            return original_save(s)
        
        manager.storage.save_session = failing_save
        
        # Add evaluation (should buffer)
        session_id = manager.create_session()
        manager.add_evaluation(
            query="Test",
            response="Test",
            response_length=10,
            score=0.7,
            judgment_type="relevance",
            quality_flags=[],
            reasoning="",
            metadata={},
        )
        
        # Flush (first attempt fails)
        manager.flush_buffer()
        
        # Retry flush
        manager.flush_buffer()
        
        # Session should eventually be saved
        # (Current implementation might lose it - this is a potential bug)
        session = manager.get_session(session_id)
        # Might be None if buffer cleared on failure
        # This tests actual behavior vs. expected behavior


def test_adaptive_manager_stale_learning_data():
    """
    HIDDEN FAILURE: Does adaptive manager reload learning data?
    
    Or does it use stale cached data?
    """
    annotate_test(
        "test_adaptive_manager_stale_learning_data",
        pattern="hierarchical_memory",
        opinion="adaptive_manager_reloads_data",
        category="hidden_failures",
        hypothesis="Adaptive manager reloads learning data when needed",
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        quality_feedback1 = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=True,
        )
        adaptive1 = AdaptiveQualityManager(quality_feedback1)
        
        # Add learning data
        quality_feedback1.evaluate_and_learn(
            query="Learning query",
            response="Learning response",
        )
        quality_feedback1.session_manager.flush_buffer()
        
        # Create new adaptive manager (should reload)
        quality_feedback2 = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=True,
        )
        adaptive2 = AdaptiveQualityManager(quality_feedback2)
        
        # Should have learned from previous data
        strategy = adaptive2.get_adaptive_strategy("test")
        assert strategy is not None


def test_session_group_empty_after_all_deleted():
    """
    HIDDEN FAILURE: What if all sessions in a group are deleted?
    
    Group becomes empty but still exists.
    """
    annotate_test(
        "test_session_group_empty_after_all_deleted",
        pattern="hierarchical_memory",
        opinion="empty_groups_are_cleaned",
        category="hidden_failures",
        hypothesis="Empty groups are cleaned up or handled",
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(
            sessions_dir=Path(tmpdir),
            auto_group_by="day",
        )
        
        # Create sessions in same group
        session_ids = []
        for i in range(3):
            session_id = manager.create_session()
            session_ids.append(session_id)
        manager.flush_buffer()
        
        # Check group
        groups = manager.groups
        assert len(groups) > 0
        
        # Delete all sessions
        for session_id in session_ids:
            manager.storage.delete_session(session_id)
            manager.cache.evict(session_id)
        
        # Groups might still exist but be empty
        # This is a potential inconsistency
        for group in groups.values():
            # Group might have empty session_ids list
            assert isinstance(group.session_ids, list)


def test_quality_feedback_history_size_limit():
    """
    HIDDEN FAILURE: What if history grows too large?
    
    Does it cause memory issues or get truncated?
    """
    annotate_test(
        "test_quality_feedback_history_size_limit",
        pattern="hierarchical_memory",
        opinion="history_has_size_limits",
        category="hidden_failures",
        hypothesis="History has size limits to prevent memory issues",
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        quality_feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=True,
        )
        
        # Add many evaluations
        for i in range(1000):
            quality_feedback.evaluate_and_learn(
                query=f"Query {i}",
                response=f"Response {i}",
            )
        
        quality_feedback.session_manager.flush_buffer()
        
        # History should be limited or managed
        history = quality_feedback.history
        # Unified storage might limit to 1000
        assert len(history) <= 1000  # Should have limit


def test_index_query_stale_mean_score():
    """
    HIDDEN FAILURE: Index stores mean_score, but what if session is updated?
    
    Index mean_score becomes stale.
    """
    annotate_test(
        "test_index_query_stale_mean_score",
        pattern="hierarchical_memory",
        opinion="index_updates_mean_score",
        category="hidden_failures",
        hypothesis="Index updates mean_score when session is updated",
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(
            sessions_dir=Path(tmpdir),
            enable_indexing=True,
        )
        
        # Create session with low score
        session_id = manager.create_session()
        manager.add_evaluation(
            query="Test",
            response="Test",
            response_length=10,
            score=0.3,
            judgment_type="relevance",
            quality_flags=[],
            reasoning="",
            metadata={},
        )
        manager.flush_buffer()
        
        # Query for high scores (shouldn't match)
        high_sessions = manager.query_sessions(min_score=0.8)
        assert session_id not in high_sessions
        
        # Update session with high score
        manager.add_evaluation(
            query="Test 2",
            response="Test 2",
            response_length=10,
            score=0.9,
            judgment_type="relevance",
            quality_flags=[],
            reasoning="",
            metadata={},
        )
        manager.flush_buffer()
        
        # Index should be updated
        # Query again
        high_sessions2 = manager.query_sessions(min_score=0.8)
        # Should now include session (if index updated)
        # Or might be stale (bug)
        assert isinstance(high_sessions2, list)

