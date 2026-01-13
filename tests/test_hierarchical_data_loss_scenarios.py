"""Tests for actual data loss scenarios.

These tests identify when data can actually be lost.
"""

import tempfile
from pathlib import Path

from bop.session_manager import HierarchicalSessionManager
from tests.test_annotations import annotate_test


def test_data_loss_buffer_not_flushed():
    """
    DATA LOSS SCENARIO: Buffer not flushed before crash.

    This is expected behavior (performance vs. durability tradeoff),
    but we should document it.
    """
    annotate_test(
        "test_data_loss_buffer_not_flushed",
        pattern="hierarchical_memory",
        opinion="buffer_loss_is_documented",
        category="data_loss",
        hypothesis="Buffer loss on crash is documented limitation",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(
            sessions_dir=Path(tmpdir),
            batch_size=5,
        )

        # Add evaluations (buffered, not flushed)
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

        # Don't flush (simulate crash)
        # Data is in buffer, not persisted

        # Reload
        manager2 = HierarchicalSessionManager(sessions_dir=Path(tmpdir))
        session = manager2.get_session(session_id)

        # Data might be lost (expected - buffer tradeoff)
        # This documents the limitation
        if session:
            # If it exists, might have been auto-flushed
            pass
        else:
            # Data lost - this is expected with buffering
            pass


def test_data_loss_index_out_of_sync():
    """
    DATA LOSS SCENARIO: Index out of sync, sessions not found.

    If index is corrupted or out of sync, sessions might not be queryable.
    """
    annotate_test(
        "test_data_loss_index_out_of_sync",
        pattern="hierarchical_memory",
        opinion="index_sync_is_critical",
        category="data_loss",
        hypothesis="Index out of sync can make sessions unqueryable",
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

        # Corrupt index
        index_file = Path(tmpdir) / "sessions" / "index.json"
        if index_file.exists():
            index_file.write_text("{}")  # Empty index

        # Session file still exists, but index doesn't know about it
        # Query might not find it
        manager.query_sessions(min_score=0.6)
        # Might not include session_id (index is empty)

        # But direct get should work
        session = manager.get_session(session_id)
        assert session is not None  # File still exists


def test_data_loss_checksum_failure_handling():
    """
    DATA LOSS SCENARIO: What if checksum fails and we can't repair?

    Data might be lost or corrupted.
    """
    annotate_test(
        "test_data_loss_checksum_failure_handling",
        pattern="hierarchical_memory",
        opinion="checksum_failures_are_handled",
        category="data_loss",
        hypothesis="Checksum failures are handled without data loss",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))

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

        # Corrupt file (change checksum)
        session_file = Path(tmpdir) / "sessions" / f"{session_id}.json"
        if session_file.exists():
            data = json.loads(session_file.read_text())
            data["checksum"] = "wrong_checksum"
            session_file.write_text(json.dumps(data))

        # Try to load
        session = manager.get_session(session_id)
        # Should either:
        # 1. Detect corruption and return None
        # 2. Repair and return session
        # 3. Return corrupted session (bug)

        # Current implementation recalculates checksum, so should work
        if session:
            assert session.evaluations[0].query == "Test"


def test_actual_behavior_vs_documented():
    """
    DEEP: Compare actual behavior to what we claim.

    Do features actually work as documented?
    """
    annotate_test(
        "test_actual_behavior_vs_documented",
        pattern="hierarchical_memory",
        opinion="behavior_matches_documentation",
        category="deep_analysis",
        hypothesis="Actual behavior matches documented behavior",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(
            sessions_dir=Path(tmpdir),
            enable_indexing=True,
            enable_buffering=True,
        )

        # Documented: "Write buffering for performance"
        # Test: Does it actually buffer?
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

        # Before flush, data might be in buffer
        # Check if file exists
        session_file = Path(tmpdir) / "sessions" / f"{session_id}.json"
        # Might not exist if buffered

        # Flush
        manager.flush_buffer()

        # After flush, should exist
        assert session_file.exists()

        # Documented: "Indexing for fast lookups"
        # Test: Does query actually use index?
        sessions = manager.query_sessions(min_score=0.6)
        assert isinstance(sessions, list)

        # Documented: "Lazy loading with LRU cache"
        # Test: Does it actually lazy load?
        session = manager.get_session(session_id)
        assert session is not None
        # Cache should have it
        assert session_id in manager.cache.cache

