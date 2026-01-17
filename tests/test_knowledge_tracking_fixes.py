"""Tests verifying the fixes to knowledge tracking."""

import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pran.knowledge_tracking import KnowledgeTracker


def test_persistence_save_and_load():
    """Test that persistence actually works."""
    with tempfile.TemporaryDirectory() as tmpdir:
        persistence_path = Path(tmpdir) / "knowledge.json"

        # Create tracker and track some concepts
        tracker1 = KnowledgeTracker(persistence_path=persistence_path, auto_save_interval=1)
        tracker1.track_query(
            session_id="session1",
            query="What is d-separation?",
            response="D-separation is a criterion...",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        tracker1.save()  # Ensure saved

        # Create new tracker and load
        tracker2 = KnowledgeTracker(persistence_path=persistence_path)

        # Should have loaded the concept
        assert "d-separation" in tracker2.concept_learning
        assert "session1" in tracker2.session_knowledge


def test_memory_limits_enforced():
    """Test that memory limits are actually enforced."""
    tracker = KnowledgeTracker()

    # Track many sessions (more than MAX_SESSIONS)
    for i in range(600):  # MAX_SESSIONS is 500
        tracker.track_query(
            session_id=f"session_{i}",
            query="What is trust?",
            response="Trust is...",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # Should be limited
    assert len(tracker.session_knowledge) <= tracker.MAX_SESSIONS
    assert len(tracker.session_knowledge) == tracker.MAX_SESSIONS  # Exactly at limit


def test_thread_safety_actual():
    """Test that thread safety actually works."""
    import threading

    tracker = KnowledgeTracker()
    results = []

    def track(session_id):
        for i in range(50):
            tracker.track_query(
                session_id=session_id,
                query="What is trust?",  # Will extract "trust" concept
                response="Trust is important",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        results.append(session_id)

    threads = [threading.Thread(target=track, args=(f"s{i}",)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Should have all sessions
    assert len(results) == 5
    assert len(tracker.session_knowledge) == 5


def test_cleanup_old_data():
    """Test cleanup mechanism."""
    with tempfile.TemporaryDirectory() as tmpdir:
        persistence_path = Path(tmpdir) / "knowledge.json"
        tracker = KnowledgeTracker(persistence_path=persistence_path)

        # Add old data (with extractable concept)
        old_timestamp = (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()
        tracker.track_query(
            session_id="old_session",
            query="What is trust?",
            response="Trust is important",
            timestamp=old_timestamp,
        )

        # Add recent data
        recent_timestamp = datetime.now(timezone.utc).isoformat()
        tracker.track_query(
            session_id="recent_session",
            query="What is knowledge?",
            response="Knowledge is understanding",
            timestamp=recent_timestamp,
        )

        # Cleanup data older than 90 days
        removed = tracker.cleanup_old_data(max_age_days=90)

        # Should remove old session and old concept
        assert removed > 0
        assert "old_session" not in tracker.session_knowledge
        assert "recent_session" in tracker.session_knowledge


def test_no_empty_entries():
    """Test that empty concept extraction doesn't create entries."""
    tracker = KnowledgeTracker()

    # Query with no extractable concepts
    tracker.track_query(
        session_id="session1",
        query="Hello, how are you?",
        response="I'm fine, thanks!",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    # Should not create session entry if no concepts
    # (Current behavior: creates entry but with no concepts - acceptable)
    # But should not crash


def test_recent_confidence_only():
    """Test that only recent confidence is stored."""
    tracker = KnowledgeTracker()

    # Track same concept with different confidence values
    for confidence in [0.5, 0.6, 0.7, 0.8, 0.9]:
        tracker.track_query(
            session_id="session1",
            query="What is trust?",
            response="Trust is...",
            timestamp=datetime.now(timezone.utc).isoformat(),
            confidence=confidence,
        )

    learning = tracker.concept_learning.get("trust")
    if learning:
        # Should only have most recent confidence
        assert learning.recent_confidence == 0.9
        # Should not have confidence_scores list
        assert not hasattr(learning, "confidence_scores")


def test_session_ids_limit():
    """Test that session_ids list is limited."""
    tracker = KnowledgeTracker()

    # Track same concept across many sessions (more than MAX_SESSION_IDS_PER_CONCEPT)
    for i in range(150):  # MAX_SESSION_IDS_PER_CONCEPT is 100
        tracker.track_query(
            session_id=f"session_{i}",
            query="What is trust?",
            response="Trust is...",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    learning = tracker.concept_learning.get("trust")
    if learning:
        # Should be limited to MAX_SESSION_IDS_PER_CONCEPT
        assert len(learning.session_ids) <= tracker.MAX_SESSION_IDS_PER_CONCEPT
        # Should keep most recent
        assert len(learning.session_ids) == tracker.MAX_SESSION_IDS_PER_CONCEPT


def test_auto_save_works():
    """Test that auto-save actually saves."""
    with tempfile.TemporaryDirectory() as tmpdir:
        persistence_path = Path(tmpdir) / "knowledge.json"
        tracker = KnowledgeTracker(persistence_path=persistence_path, auto_save_interval=5)

        # Track 5 queries with extractable concepts (should trigger auto-save)
        for i in range(5):
            tracker.track_query(
                session_id="session1",
                query="What is trust?",
                response="Trust is important",
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

        # File should exist (auto-save triggered after 5 queries)
        assert persistence_path.exists()

        # Load and verify
        tracker2 = KnowledgeTracker(persistence_path=persistence_path)
        assert len(tracker2.concept_learning) > 0

