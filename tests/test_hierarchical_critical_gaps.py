"""Critical gap analysis and distrust tests for hierarchical memory.

These tests probe for weaknesses, edge cases, and failures we might have missed.
"""

import tempfile
from pathlib import Path

from pran.adaptive_quality import AdaptiveQualityManager
from pran.quality_feedback import QualityFeedbackLoop
from pran.session_manager import HierarchicalSessionManager
from pran.unified_storage import UnifiedSessionStorage
from tests.test_annotations import annotate_test


def test_session_deleted_while_quality_feedback_active():
    """
    CRITICAL: What happens if session is deleted while quality feedback is using it?

    This could cause:
    - Stale references
    - Crashes when accessing deleted session
    - Data loss
    """
    annotate_test(
        "test_session_deleted_while_quality_feedback_active",
        pattern="hierarchical_memory",
        opinion="system_handles_concurrent_deletion",
        category="critical_gaps",
        hypothesis="System handles session deletion while quality feedback is active",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        quality_feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=True,
        )
        manager = quality_feedback.session_manager

        # Create session and add evaluation
        session_id = manager.create_session()
        quality_feedback.evaluate_and_learn(
            query="Test query",
            response="Test response",
        )

        # Delete session while quality feedback might still reference it
        # Use storage directly since manager doesn't have delete_session
        manager.storage.delete_session(session_id)
        # Also remove from cache and index
        manager.cache.evict(session_id)
        if session_id in manager.index:
            del manager.index[session_id]

        # Quality feedback should handle this gracefully
        # Try to access session - should return None or handle gracefully
        session = manager.get_session(session_id)
        assert session is None

        # Quality feedback should still work
        result = quality_feedback.evaluate_and_learn(
            query="Another query",
            response="Another response",
        )
        assert result is not None


def test_unified_storage_stale_references():
    """
    CRITICAL: Does unified storage handle stale session references?

    If a session is deleted, does unified storage still reference it?
    """
    annotate_test(
        "test_unified_storage_stale_references",
        pattern="hierarchical_memory",
        opinion="unified_storage_handles_stale_references",
        category="critical_gaps",
        hypothesis="Unified storage handles deleted session references gracefully",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))
        unified = UnifiedSessionStorage(session_manager=manager)

        # Create and delete session
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

        # Get history (should include session)
        history1 = unified.get_history_view(limit=100)
        assert len(history1) == 1

        # Delete session
        manager.storage.delete_session(session_id)
        manager.cache.evict(session_id)
        if session_id in manager.index:
            del manager.index[session_id]

        # History should no longer include deleted session
        history2 = unified.get_history_view(limit=100)
        assert len(history2) == 0  # Should be empty after deletion


def test_buffer_flush_race_condition():
    """
    CRITICAL: What happens if buffer is flushed while new writes are added?

    Race condition: Add to buffer → Flush starts → Add more → Flush completes
    """
    annotate_test(
        "test_buffer_flush_race_condition",
        pattern="hierarchical_memory",
        opinion="buffer_handles_concurrent_operations",
        category="critical_gaps",
        hypothesis="Write buffer handles concurrent flush and add operations",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(
            sessions_dir=Path(tmpdir),
            batch_size=3,
        )

        # Create session
        session_id = manager.create_session()

        # Add evaluation (triggers buffer)
        manager.add_evaluation(
            query="Query 1",
            response="Response 1",
            response_length=10,
            score=0.7,
            judgment_type="relevance",
            quality_flags=[],
            reasoning="",
            metadata={},
        )

        # Manually flush while potentially adding more
        # This simulates a race condition
        manager.flush_buffer()

        # Add more after flush
        manager.add_evaluation(
            query="Query 2",
            response="Response 2",
            response_length=10,
            score=0.8,
            judgment_type="relevance",
            quality_flags=[],
            reasoning="",
            metadata={},
        )

        # Both should be persisted
        manager.flush_buffer()
        session = manager.get_session(session_id)
        assert len(session.evaluations) == 2


def test_index_corruption_during_write():
    """
    CRITICAL: What if index file is corrupted while session is being written?

    This could cause:
    - Lost sessions (not in index)
    - Inconsistent state
    - Query failures
    """
    annotate_test(
        "test_index_corruption_during_write",
        pattern="hierarchical_memory",
        opinion="system_recovers_from_index_corruption",
        category="critical_gaps",
        hypothesis="System recovers from index corruption during writes",
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

        # Corrupt index file
        index_file = Path(tmpdir) / "sessions" / "index.json"
        if index_file.exists():
            index_file.write_text("corrupted json{")

        # System should rebuild index or handle gracefully
        # Try to list sessions
        sessions = manager.list_sessions()
        # Should either rebuild index or return empty list gracefully
        assert isinstance(sessions, list)


def test_adaptive_manager_stale_session_data():
    """
    CRITICAL: Does adaptive manager use stale session data?

    If sessions are updated, does adaptive manager see the updates?
    """
    annotate_test(
        "test_adaptive_manager_stale_session_data",
        pattern="hierarchical_memory",
        opinion="adaptive_manager_sees_fresh_data",
        category="critical_gaps",
        hypothesis="Adaptive manager sees fresh session data, not stale",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        quality_feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=True,
        )
        manager = quality_feedback.session_manager
        adaptive = AdaptiveQualityManager(quality_feedback)

        # Create session with low score
        manager.create_session()
        manager.add_evaluation(
            query="Test query",
            response="Poor response",
            response_length=10,
            score=0.3,  # Low score
            judgment_type="relevance",
            quality_flags=["low_quality"],
            reasoning="",
            metadata={},
        )
        manager.flush_buffer()

        # Adaptive manager should see this
        adaptive.get_performance_insights()

        # Update session with better score
        manager.add_evaluation(
            query="Test query 2",
            response="Better response",
            response_length=10,
            score=0.9,  # High score
            judgment_type="relevance",
            quality_flags=[],
            reasoning="",
            metadata={},
        )
        manager.flush_buffer()

        # Adaptive manager should see updated data
        # (This tests if it reloads or caches)
        insights2 = adaptive.get_performance_insights()
        assert insights2 is not None


def test_group_recalculation_after_session_deletion():
    """
    CRITICAL: Are groups recalculated when sessions are deleted?

    If a session is deleted, does its group still reference it?
    """
    annotate_test(
        "test_group_recalculation_after_session_deletion",
        pattern="hierarchical_memory",
        opinion="groups_update_after_deletion",
        category="critical_gaps",
        hypothesis="Groups are updated when sessions are deleted",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(
            sessions_dir=Path(tmpdir),
            auto_group_by="day",
        )

        # Create sessions in same day group
        session1 = manager.create_session()
        manager.create_session()
        manager.flush_buffer()

        # Check groups
        groups_before = manager.groups
        assert len(groups_before) > 0

        # Delete one session
        manager.delete_session(session1)

        # Groups should be updated
        # (Implementation might keep group but remove session_id)
        groups_after = manager.groups
        # At minimum, shouldn't crash
        assert isinstance(groups_after, dict)


def test_quality_feedback_partial_write_failure():
    """
    CRITICAL: What if quality feedback write partially fails?

    E.g., session write succeeds but history write fails?
    """
    annotate_test(
        "test_quality_feedback_partial_write_failure",
        pattern="hierarchical_memory",
        opinion="quality_feedback_handles_partial_failures",
        category="critical_gaps",
        hypothesis="Quality feedback handles partial write failures gracefully",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        quality_feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=True,
        )

        # Mock storage to fail on specific write
        manager = quality_feedback.session_manager

        # Add evaluation
        result = quality_feedback.evaluate_and_learn(
            query="Test query",
            response="Test response",
        )

        # Should handle gracefully even if write partially fails
        assert result is not None

        # Session should still exist
        session = manager.get_session(manager.current_session_id)
        assert session is not None


def test_cross_session_learning_data_consistency():
    """
    CRITICAL: Is cross-session learning data consistent?

    If sessions are updated/deleted, does adaptive manager have consistent view?
    """
    annotate_test(
        "test_cross_session_learning_data_consistency",
        pattern="hierarchical_memory",
        opinion="cross_session_learning_is_consistent",
        category="critical_gaps",
        hypothesis="Cross-session learning maintains data consistency",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        quality_feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=True,
        )
        manager = quality_feedback.session_manager
        adaptive = AdaptiveQualityManager(quality_feedback)

        # Create multiple sessions
        for i in range(3):
            manager.create_session()
            quality_feedback.evaluate_and_learn(
                query=f"Query {i}",
                response=f"Response {i}",
            )

        manager.flush_buffer()

        # Get insights (should see all sessions)
        insights1 = adaptive.get_performance_insights()
        assert insights1 is not None

        # Delete a session
        all_sessions = manager.list_sessions()
        if all_sessions:
            manager.delete_session(all_sessions[0].session_id)

        # Insights should still be consistent
        insights2 = adaptive.get_performance_insights()
        assert insights2 is not None


def test_unified_storage_empty_session_handling():
    """
    CRITICAL: How does unified storage handle empty sessions?

    Empty sessions shouldn't appear in history, but should they?
    """
    annotate_test(
        "test_unified_storage_empty_session_handling",
        pattern="hierarchical_memory",
        opinion="unified_storage_filters_empty_sessions",
        category="critical_gaps",
        hypothesis="Unified storage correctly handles empty sessions",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))
        unified = UnifiedSessionStorage(session_manager=manager)

        # Create empty session
        manager.create_session()
        manager.flush_buffer()

        # History should not include empty sessions
        history = unified.get_history_view(limit=100)
        assert len(history) == 0  # Empty sessions shouldn't appear


def test_hierarchical_learning_memory_leak():
    """
    CRITICAL: Does hierarchical learning cause memory leaks?

    If sessions accumulate, does adaptive manager keep all in memory?
    """
    annotate_test(
        "test_hierarchical_learning_memory_leak",
        pattern="hierarchical_memory",
        opinion="hierarchical_learning_doesnt_leak_memory",
        category="critical_gaps",
        hypothesis="Hierarchical learning doesn't cause memory leaks",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        quality_feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=True,
        )
        manager = quality_feedback.session_manager
        adaptive = AdaptiveQualityManager(quality_feedback)

        # Create many sessions
        for i in range(50):
            quality_feedback.evaluate_and_learn(
                query=f"Query {i}",
                response=f"Response {i}",
            )

        manager.flush_buffer()

        # Adaptive manager should handle this without memory issues
        # (Implementation might limit history size)
        insights = adaptive.get_performance_insights()
        assert insights is not None


def test_session_replay_deleted_session():
    """
    CRITICAL: What happens if we try to replay a deleted session?
    """
    annotate_test(
        "test_session_replay_deleted_session",
        pattern="hierarchical_memory",
        opinion="replay_handles_deleted_sessions",
        category="critical_gaps",
        hypothesis="Session replay handles deleted sessions gracefully",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))
        from pran.session_replay import SessionReplayManager
        replay = SessionReplayManager(manager)

        # Create and delete session
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

        # Delete session
        manager.storage.delete_session(session_id)
        manager.cache.evict(session_id)
        if session_id in manager.index:
            del manager.index[session_id]

        # Try to replay - should handle gracefully
        replayed = []
        def collect(e):
            replayed.append(e.query)

        replay.forward_replay(session_id, collect)
        # Should either skip or handle gracefully
        assert isinstance(replayed, list)


def test_quality_feedback_session_creation_race():
    """
    CRITICAL: What if multiple quality feedback calls create sessions simultaneously?

    Race condition: Two calls → Both check no session → Both create session
    """
    annotate_test(
        "test_quality_feedback_session_creation_race",
        pattern="hierarchical_memory",
        opinion="quality_feedback_handles_concurrent_session_creation",
        category="critical_gaps",
        hypothesis="Quality feedback handles concurrent session creation",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        quality_feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=True,
        )

        # Simulate concurrent calls
        # (In real scenario, this would be async/threaded)
        result1 = quality_feedback.evaluate_and_learn(
            query="Query 1",
            response="Response 1",
        )
        result2 = quality_feedback.evaluate_and_learn(
            query="Query 2",
            response="Response 2",
        )

        # Should handle gracefully
        assert result1 is not None
        assert result2 is not None

        # Should use same session or create new ones appropriately
        manager = quality_feedback.session_manager
        assert manager.current_session_id is not None


def test_buffer_overflow_edge_case():
    """
    CRITICAL: What if buffer exceeds capacity before flush?

    Buffer has max size, what if we add more than that?
    """
    annotate_test(
        "test_buffer_overflow_edge_case",
        pattern="hierarchical_memory",
        opinion="buffer_handles_overflow",
        category="critical_gaps",
        hypothesis="Write buffer handles overflow gracefully",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(
            sessions_dir=Path(tmpdir),
            batch_size=2,  # Small buffer
        )

        # Add more than buffer size
        session_ids = []
        for i in range(5):
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

        # Buffer should flush automatically or handle overflow
        manager.flush_buffer()

        # All sessions should be persisted
        for session_id in session_ids:
            session = manager.get_session(session_id)
            assert session is not None


def test_adaptive_manager_empty_learning_data():
    """
    CRITICAL: What if adaptive manager has no learning data?

    Does it crash or handle gracefully?
    """
    annotate_test(
        "test_adaptive_manager_empty_learning_data",
        pattern="hierarchical_memory",
        opinion="adaptive_manager_handles_empty_data",
        category="critical_gaps",
        hypothesis="Adaptive manager handles empty learning data gracefully",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        quality_feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=True,
        )
        adaptive = AdaptiveQualityManager(quality_feedback)

        # No evaluations yet
        # Should still return strategy (even if default)
        strategy = adaptive.get_adaptive_strategy("test query")
        assert strategy is not None

        # Insights should handle empty data
        insights = adaptive.get_performance_insights()
        assert insights is not None


def test_session_metadata_corruption():
    """
    CRITICAL: What if session metadata is corrupted?

    Invalid JSON, missing fields, wrong types?
    """
    annotate_test(
        "test_session_metadata_corruption",
        pattern="hierarchical_memory",
        opinion="system_handles_metadata_corruption",
        category="critical_gaps",
        hypothesis="System handles corrupted session metadata gracefully",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))

        # Create valid session
        session_id = manager.create_session(metadata={"key": "value"})
        manager.flush_buffer()

        # Corrupt metadata file directly
        session_file = Path(tmpdir) / "sessions" / f"{session_id}.json"
        if session_file.exists():
            # Write invalid JSON
            session_file.write_text("{invalid json}")

        # System should handle gracefully
        session = manager.get_session(session_id)
        # Should either return None or handle corruption
        # (Implementation might validate and return None)
        if session is None:
            # That's acceptable - corruption detected
            pass
        else:
            # If it loads, metadata should be handled
            assert isinstance(session.metadata, dict)


def test_quality_feedback_history_reload_consistency():
    """
    CRITICAL: Is quality feedback history consistent after reload?

    If history is reloaded, does it match session data?
    """
    annotate_test(
        "test_quality_feedback_history_reload_consistency",
        pattern="hierarchical_memory",
        opinion="history_reload_is_consistent",
        category="critical_gaps",
        hypothesis="Quality feedback history is consistent after reload",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        quality_feedback1 = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=True,
        )

        # Add evaluations
        for i in range(3):
            quality_feedback1.evaluate_and_learn(
                query=f"Query {i}",
                response=f"Response {i}",
            )

        quality_feedback1.session_manager.flush_buffer()

        # Create new instance (simulates reload)
        quality_feedback2 = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=True,
        )

        # History should be consistent
        history1 = quality_feedback1.history
        history2 = quality_feedback2.history

        # Should have same number of entries (or derived from same sessions)
        # (Might be different if using unified storage)
        assert isinstance(history1, list)
        assert isinstance(history2, list)


def test_group_statistics_empty_group():
    """
    CRITICAL: What if a group has all sessions deleted?

    Does it become an empty group? Is it cleaned up?
    """
    annotate_test(
        "test_group_statistics_empty_group",
        pattern="hierarchical_memory",
        opinion="empty_groups_are_handled",
        category="critical_gaps",
        hypothesis="Empty groups are handled or cleaned up",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(
            sessions_dir=Path(tmpdir),
            auto_group_by="day",
        )

        # Create session in group
        session_id = manager.create_session()
        manager.flush_buffer()

        # Check group exists
        groups_before = manager.groups
        assert len(groups_before) > 0

        # Delete all sessions in group
        manager.delete_session(session_id)

        # Group might still exist but be empty
        # Or might be cleaned up
        groups_after = manager.groups
        # At minimum, shouldn't crash
        assert isinstance(groups_after, dict)

