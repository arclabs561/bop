"""Stress tests for session manager with extreme scenarios."""

import pytest
import tempfile
from pathlib import Path
import time

from bop.session_manager import HierarchicalSessionManager


def test_rapid_session_creation():
    """Test creating many sessions rapidly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))
        
        # Create 100 sessions rapidly
        start = time.time()
        session_ids = [manager.create_session() for _ in range(100)]
        creation_time = time.time() - start
        
        manager.flush_buffer()
        
        # All should exist
        assert len(session_ids) == 100
        for session_id in session_ids:
            session = manager.get_session(session_id)
            assert session is not None
        
        # Should be reasonably fast
        assert creation_time < 5.0  # Should complete in under 5 seconds
        
        print(f"Created 100 sessions in {creation_time:.3f}s")


def test_rapid_evaluation_addition():
    """Test adding many evaluations rapidly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))
        
        session_id = manager.create_session()
        
        # Add 500 evaluations rapidly
        start = time.time()
        for i in range(500):
            manager.add_evaluation(
                query=f"Query {i}",
                response=f"Response {i}",
                response_length=100,
                score=0.7,
                judgment_type="relevance",
                quality_flags=[],
                reasoning="",
                metadata={},
            )
        add_time = time.time() - start
        
        flush_start = time.time()
        manager.flush_buffer()
        flush_time = time.time() - flush_start
        
        session = manager.get_session(session_id)
        assert len(session.evaluations) == 500
        
        print(f"Added 500 evaluations in {add_time:.3f}s, flushed in {flush_time:.3f}s")


def test_concurrent_session_operations():
    """Test concurrent operations on different sessions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))
        
        # Create 10 sessions
        session_ids = [manager.create_session() for _ in range(10)]
        
        # Add evaluations to each session
        for session_id in session_ids:
            for i in range(10):
                manager.add_evaluation(
                    query=f"Query {i}",
                    response=f"Response {i}",
                    response_length=100,
                    score=0.7,
                    judgment_type="relevance",
                    quality_flags=[],
                    reasoning="",
                    metadata={},
                    session_id=session_id,
                )
        
        manager.flush_buffer()
        
        # All sessions should have 10 evaluations
        for session_id in session_ids:
            session = manager.get_session(session_id)
            assert len(session.evaluations) == 10


def test_buffer_under_heavy_load():
    """Test buffer behavior under heavy load."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(
            sessions_dir=Path(tmpdir),
            batch_size=20,
            flush_interval=1.0,
        )
        
        # Create session and add many evaluations
        session_id = manager.create_session()
        
        for i in range(100):
            manager.add_evaluation(
                query=f"Query {i}",
                response=f"Response {i}",
                response_length=100,
                score=0.7,
                judgment_type="relevance",
                quality_flags=[],
                reasoning="",
                metadata={},
            )
            
            # Check buffer size periodically
            if i % 10 == 0:
                buffer_size = len(manager.write_buffer._buffer) if manager.write_buffer else 0
                assert buffer_size <= manager.write_buffer.batch_size if manager.write_buffer else True
        
        # Final flush
        manager.flush_buffer()
        
        session = manager.get_session(session_id)
        assert len(session.evaluations) == 100


def test_cache_eviction_under_load():
    """Test cache eviction when many sessions are accessed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(
            sessions_dir=Path(tmpdir),
            cache_size=10,  # Small cache
        )
        
        # Create more sessions than cache size
        session_ids = [manager.create_session() for _ in range(20)]
        manager.flush_buffer()
        
        # Access all sessions (should trigger evictions)
        for session_id in session_ids:
            session = manager.get_session(session_id)
            assert session is not None
        
        # Cache should not exceed max size
        assert len(manager.cache.cache) <= manager.cache.maxsize


def test_index_performance_with_many_sessions():
    """Test index query performance with many sessions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(
            sessions_dir=Path(tmpdir),
            enable_indexing=True,
        )
        
        # Create 200 sessions with varied scores
        for i in range(200):
            session_id = manager.create_session()
            manager.add_evaluation(
                query="Test",
                response="Test",
                response_length=100,
                score=i / 200.0,  # Scores from 0.0 to 0.995
                judgment_type="relevance",
                quality_flags=[],
                reasoning="",
                metadata={},
            )
        
        manager.flush_buffer()
        
        # Test index queries
        import time
        
        start = time.time()
        high_score = manager.query_sessions(min_score=0.9)
        query_time = time.time() - start
        
        assert len(high_score) > 0
        assert query_time < 0.1  # Should be very fast
        
        print(f"Index query on 200 sessions took {query_time:.6f}s")


def test_large_metadata_persistence():
    """Test persistence of sessions with large metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))
        
        # Create session with large metadata
        large_metadata = {
            "data": "x" * 10000,  # 10KB of metadata
            "nested": {
                "level1": {
                    "level2": {
                        "level3": {"data": "deep nesting"}
                    }
                }
            },
            "array": list(range(1000)),
        }
        
        session_id = manager.create_session(metadata=large_metadata)
        manager.flush_buffer()
        
        # Reload
        session = manager.get_session(session_id)
        assert session.metadata["data"] == "x" * 10000
        assert session.metadata["nested"]["level1"]["level2"]["level3"]["data"] == "deep nesting"
        assert len(session.metadata["array"]) == 1000

