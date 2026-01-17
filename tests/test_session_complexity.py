"""Tests for sessions with varying complexity levels."""

import tempfile
from pathlib import Path

from pran.session_manager import (
    HierarchicalSessionManager,
)


def test_blank_slate_session():
    """Test completely empty session (blank slate)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))

        # Create blank session
        session_id = manager.create_session()
        session = manager.get_session(session_id)

        assert session is not None
        assert len(session.evaluations) == 0
        assert session.status == "active"
        assert session.context is None
        assert session.user_id is None
        assert len(session.metadata) == 0

        # Statistics should handle empty
        stats = session.get_statistics()
        assert stats["evaluation_count"] == 0
        assert stats["mean_score"] == 0.0

        # Should persist and reload
        manager.flush_buffer()
        manager2 = HierarchicalSessionManager(sessions_dir=Path(tmpdir))
        reloaded = manager2.get_session(session_id)
        assert reloaded is not None
        assert len(reloaded.evaluations) == 0


def test_session_with_single_evaluation():
    """Test session with minimal data (one evaluation)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))

        session_id = manager.create_session()
        manager.add_evaluation(
            query="Simple query",
            response="Simple response",
            response_length=50,
            score=0.7,
            judgment_type="relevance",
            quality_flags=[],
            reasoning="OK",
            metadata={},
        )
        manager.flush_buffer()

        session = manager.get_session(session_id)
        assert len(session.evaluations) == 1
        assert session.evaluations[0].score == 0.7

        stats = session.get_statistics()
        assert stats["evaluation_count"] == 1
        assert stats["mean_score"] == 0.7
        assert stats["min_score"] == 0.7
        assert stats["max_score"] == 0.7


def test_session_with_many_evaluations():
    """Test session with many evaluations (stress test)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))

        session_id = manager.create_session()

        # Add 100 evaluations
        for i in range(100):
            manager.add_evaluation(
                query=f"Query {i}",
                response=f"Response {i}",
                response_length=100 + i,
                score=0.5 + (i % 10) * 0.05,
                judgment_type="relevance",
                quality_flags=[] if i % 5 else ["placeholder"],
                reasoning=f"Reasoning {i}",
                metadata={"iteration": i, "schema": "chain_of_thought"},
            )

        manager.flush_buffer()

        session = manager.get_session(session_id)
        assert len(session.evaluations) == 100

        stats = session.get_statistics()
        assert stats["evaluation_count"] == 100
        assert 0.5 <= stats["mean_score"] <= 1.0

        # Check quality issues
        assert "placeholder" in stats.get("quality_issues", {})
        assert stats["quality_issues"]["placeholder"] == 20  # Every 5th

        # Check schemas used
        assert "chain_of_thought" in stats.get("schemas_used", [])


def test_session_with_very_large_evaluations():
    """Test session with very large evaluation data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))

        session_id = manager.create_session()

        # Add evaluation with very long response
        long_response = "x" * 5000  # 5KB response
        manager.add_evaluation(
            query="Query with long response",
            response=long_response,
            response_length=len(long_response),
            score=0.8,
            judgment_type="relevance",
            quality_flags=[],
            reasoning="Long response",
            metadata={"large": True},
        )

        manager.flush_buffer()

        session = manager.get_session(session_id)
        assert len(session.evaluations) == 1
        # Response should be truncated in storage (1000 chars)
        assert len(session.evaluations[0].response) <= 1000


def test_session_with_mixed_quality_scores():
    """Test session with wide range of quality scores."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))

        session_id = manager.create_session()

        # Add evaluations with varying scores
        scores = [0.1, 0.3, 0.5, 0.7, 0.9, 0.2, 0.4, 0.6, 0.8, 1.0]
        for score in scores:
            manager.add_evaluation(
                query=f"Query with score {score}",
                response=f"Response {score}",
                response_length=100,
                score=score,
                judgment_type="relevance",
                quality_flags=[] if score > 0.5 else ["low_quality"],
                reasoning="",
                metadata={},
            )

        manager.flush_buffer()

        session = manager.get_session(session_id)
        stats = session.get_statistics()

        assert stats["evaluation_count"] == 10
        assert stats["min_score"] == 0.1
        assert stats["max_score"] == 1.0
        assert 0.4 < stats["mean_score"] < 0.6  # Around 0.55

        # Check quality issues
        assert stats["quality_issues"]["low_quality"] == 5


def test_session_with_multiple_schemas():
    """Test session using multiple reasoning schemas."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))

        session_id = manager.create_session()

        schemas = [
            "chain_of_thought",
            "decompose_and_synthesize",
            "hypothesize_and_test",
            "scenario_analysis",
            "iterative_elaboration",
        ]

        for schema in schemas:
            manager.add_evaluation(
                query=f"Query using {schema}",
                response=f"Response with {schema}",
                response_length=100,
                score=0.7,
                judgment_type="relevance",
                quality_flags=[],
                reasoning="",
                metadata={"schema": schema},
            )

        manager.flush_buffer()

        session = manager.get_session(session_id)
        stats = session.get_statistics()

        assert len(stats["schemas_used"]) == 5
        assert all(schema in stats["schemas_used"] for schema in schemas)


def test_session_with_all_judgment_types():
    """Test session with all judgment types."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))

        session_id = manager.create_session()

        judgment_types = ["relevance", "accuracy", "completeness", "consistency"]

        for jtype in judgment_types:
            manager.add_evaluation(
                query="Test query",
                response="Test response",
                response_length=100,
                score=0.7,
                judgment_type=jtype,
                quality_flags=[],
                reasoning="",
                metadata={},
            )

        manager.flush_buffer()

        session = manager.get_session(session_id)
        assert len(session.evaluations) == 4

        # All judgment types should be present
        eval_types = {e.judgment_type for e in session.evaluations}
        assert eval_types == set(judgment_types)


def test_session_with_complex_metadata():
    """Test session with complex nested metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))

        session_id = manager.create_session(metadata={
            "user_preferences": {
                "language": "en",
                "detail_level": "high",
            },
            "context": {
                "domain": "knowledge_structure",
                "subdomain": "trust_uncertainty",
            },
        })

        manager.add_evaluation(
            query="Complex query",
            response="Complex response",
            response_length=100,
            score=0.8,
            judgment_type="relevance",
            quality_flags=[],
            reasoning="",
            metadata={
                "schema": "chain_of_thought",
                "research": True,
                "tools_used": ["perplexity", "firecrawl"],
                "cost": 0.05,
                "latency_ms": 1200,
            },
        )

        manager.flush_buffer()

        session = manager.get_session(session_id)
        assert session.metadata["user_preferences"]["language"] == "en"
        assert session.evaluations[0].metadata["tools_used"] == ["perplexity", "firecrawl"]


def test_session_lifecycle_from_blank_to_complex():
    """Test session evolving from blank to complex."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))

        # Start blank
        session_id = manager.create_session()
        session = manager.get_session(session_id)
        assert len(session.evaluations) == 0
        assert session.status == "active"

        # Add evaluations gradually
        for i in range(10):
            manager.add_evaluation(
                query=f"Query {i}",
                response=f"Response {i}",
                response_length=100,
                score=0.5 + i * 0.05,
                judgment_type="relevance",
                quality_flags=[],
                reasoning="",
                metadata={"step": i},
            )

            # Check intermediate state
            session = manager.get_session(session_id)
            assert len(session.evaluations) == i + 1
            assert session.status == "active"

        # Close session
        manager.close_session(session_id, finalize=True)
        session = manager.get_session(session_id)
        assert session.status == "closed"
        assert session.final_statistics is not None
        assert session.final_statistics["evaluation_count"] == 10


def test_multiple_blank_sessions():
    """Test creating many blank sessions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))

        # Create 50 blank sessions
        session_ids = []
        for i in range(50):
            session_id = manager.create_session(context=f"blank_{i}")
            session_ids.append(session_id)

        manager.flush_buffer()

        # All should be blank
        for session_id in session_ids:
            session = manager.get_session(session_id)
            assert session is not None
            assert len(session.evaluations) == 0
            assert session.status == "active"

        # Aggregate stats
        stats = manager.get_aggregate_statistics()
        assert stats["session_count"] == 50
        assert stats["total_evaluations"] == 0
        assert stats["mean_score"] == 0.0


def test_mixed_blank_and_complex_sessions():
    """Test mix of blank and complex sessions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))

        # Create some blank sessions
        blank_ids = [manager.create_session() for _ in range(5)]

        # Create some complex sessions
        complex_ids = []
        for i in range(5):
            session_id = manager.create_session()
            for j in range(20):
                manager.add_evaluation(
                    query=f"Query {i}-{j}",
                    response=f"Response {i}-{j}",
                    response_length=100,
                    score=0.7,
                    judgment_type="relevance",
                    quality_flags=[],
                    reasoning="",
                    metadata={},
                )
            complex_ids.append(session_id)

        manager.flush_buffer()

        # Verify blank sessions
        for session_id in blank_ids:
            session = manager.get_session(session_id)
            assert len(session.evaluations) == 0

        # Verify complex sessions
        for session_id in complex_ids:
            session = manager.get_session(session_id)
            assert len(session.evaluations) == 20

        # Aggregate stats
        stats = manager.get_aggregate_statistics()
        assert stats["session_count"] == 10
        assert stats["total_evaluations"] == 100  # 5 * 20


def test_session_with_extreme_scores():
    """Test session with extreme score values."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))

        session_id = manager.create_session()

        # Add evaluations with extreme scores
        extreme_scores = [0.0, 0.0001, 0.9999, 1.0]
        for score in extreme_scores:
            manager.add_evaluation(
                query=f"Query with score {score}",
                response="Response",
                response_length=100,
                score=score,
                judgment_type="relevance",
                quality_flags=[],
                reasoning="",
                metadata={},
            )

        manager.flush_buffer()

        session = manager.get_session(session_id)
        stats = session.get_statistics()

        assert stats["min_score"] == 0.0
        assert stats["max_score"] == 1.0
        assert stats["evaluation_count"] == 4


def test_session_persistence_complexity():
    """Test that complex sessions persist correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create complex session
        manager1 = HierarchicalSessionManager(sessions_dir=Path(tmpdir))
        session_id = manager1.create_session(
            context="complex_test",
            metadata={"complex": True, "nested": {"data": "value"}},
        )

        # Add many evaluations with varied data
        for i in range(50):
            manager1.add_evaluation(
                query=f"Complex query {i}",
                response=f"Complex response {i}",
                response_length=200 + i,
                score=0.5 + (i % 20) * 0.025,
                judgment_type=["relevance", "accuracy", "completeness"][i % 3],
                quality_flags=[] if i % 3 else ["flag1", "flag2"],
                reasoning=f"Complex reasoning {i}",
                metadata={
                    "schema": ["chain_of_thought", "decompose_and_synthesize"][i % 2],
                    "iteration": i,
                    "nested": {"level": i % 10},
                },
            )

        manager1.flush_buffer()

        # Reload in new manager
        manager2 = HierarchicalSessionManager(sessions_dir=Path(tmpdir))
        session = manager2.get_session(session_id)

        assert session is not None
        assert session.context == "complex_test"
        assert len(session.evaluations) == 50
        assert session.metadata["complex"] is True

        # Verify all evaluations persisted
        for i, eval_entry in enumerate(session.evaluations):
            assert eval_entry.query == f"Complex query {i}"
            assert eval_entry.response == f"Complex response {i}"
            assert eval_entry.metadata["iteration"] == i

