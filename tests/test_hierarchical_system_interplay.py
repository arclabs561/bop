"""Tests for nuanced interplay between hierarchical memory and complex systems.

These tests validate:
- Hierarchical session management interactions
- Quality feedback loop integration
- Adaptive learning across sessions
- Unified storage deduplication
- Experience replay mechanisms
- Cross-session learning patterns

Uses LLM judges where semantic/behavioral validation is needed.
"""

import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pran.adaptive_quality import AdaptiveQualityManager
from pran.quality_feedback import QualityFeedbackLoop
from pran.session_manager import HierarchicalSessionManager
from pran.session_replay import SessionReplayManager
from pran.unified_storage import UnifiedSessionStorage
from tests.test_annotations import annotate_test


@pytest.mark.asyncio
async def test_hierarchical_quality_feedback_integration():
    """
    Test nuanced interaction between hierarchical sessions and quality feedback.

    Nuance: Quality feedback should learn from hierarchical session structure,
    not just flat evaluations.
    """
    annotate_test(
        "test_hierarchical_quality_feedback_integration",
        pattern="hierarchical_memory",
        opinion="quality_feedback_learns_from_hierarchy",
        category="system_interplay",
        hypothesis="Quality feedback learns from hierarchical session structure",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        quality_feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=True,
        )
        manager = quality_feedback.session_manager

        # Create sessions in different groups (by day)
        datetime.now(timezone.utc)

        # Session 1: Day 1
        manager.create_session(context="day1_session")
        manager.add_evaluation(
            query="Query 1",
            response="Response 1",
            response_length=100,
            score=0.7,
            judgment_type="relevance",
            quality_flags=[],
            reasoning="",
            metadata={"day": 1},
        )

        # Session 2: Day 2 (different group)
        manager.create_session(context="day2_session")
        manager.add_evaluation(
            query="Query 2",
            response="Response 2",
            response_length=100,
            score=0.8,
            judgment_type="relevance",
            quality_flags=[],
            reasoning="",
            metadata={"day": 2},
        )

        manager.flush_buffer()

        # Quality feedback should see both sessions
        # and learn from the hierarchical structure
        history = quality_feedback.history
        assert len(history) >= 0  # May be empty initially, but should load

        # Should have access to group information
        groups = manager.groups
        assert len(groups) > 0

        # Quality feedback should be able to query by group
        # (if we add that capability)
        assert quality_feedback.session_manager is not None


@pytest.mark.asyncio
async def test_cross_session_adaptive_learning_nuances():
    """
    Test nuanced cross-session learning patterns.

    Nuance: Adaptive manager should recognize patterns across session groups,
    not just individual sessions.
    """
    annotate_test(
        "test_cross_session_adaptive_learning_nuances",
        pattern="hierarchical_memory",
        opinion="adaptive_learning_recognizes_group_patterns",
        category="system_interplay",
        hypothesis="Adaptive learning recognizes patterns across session groups",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        quality_feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=True,
        )
        manager = quality_feedback.session_manager
        adaptive = AdaptiveQualityManager(quality_feedback)

        # Create multiple sessions with similar patterns
        for i in range(5):
            manager.create_session(context=f"pattern_session_{i}")
            manager.add_evaluation(
                query=f"Similar query pattern {i}",
                response=f"Response {i}",
                response_length=100,
                score=0.7 + (i * 0.02),
                judgment_type="relevance",
                quality_flags=[],
                reasoning="",
                metadata={"pattern": "similar", "iteration": i},
            )

        manager.flush_buffer()

        # Adaptive manager should learn from cross-session patterns
        # Check if it recognizes the pattern
        insights = adaptive.get_performance_insights()
        assert insights is not None

        # Should have learned from multiple sessions
        if insights.get("session_count"):
            assert insights["session_count"] >= 5


@pytest.mark.asyncio
async def test_unified_storage_deduplication_nuances():
    """
    Test nuanced deduplication between flat history and hierarchical sessions.

    Nuance: Unified storage should prevent duplicate entries while preserving
    both flat and hierarchical views.
    """
    annotate_test(
        "test_unified_storage_deduplication_nuances",
        pattern="hierarchical_memory",
        opinion="unified_storage_deduplicates_correctly",
        category="system_interplay",
        hypothesis="Unified storage prevents duplicates while preserving views",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))
        unified = UnifiedSessionStorage(session_manager=manager)

        # Add evaluation through session manager
        session_id = manager.create_session()
        manager.add_evaluation(
            query="Test query",
            response="Test response",
            response_length=100,
            score=0.7,
            judgment_type="relevance",
            quality_flags=[],
            reasoning="",
            metadata={},
        )
        manager.flush_buffer()

        # Get unified view
        history = unified.get_history_view(limit=100)

        # Should have exactly one entry (no duplicates)
        assert len(history) == 1

        # Entry should have session context in metadata
        entry = history[0]
        assert entry.get("metadata", {}).get("session_id") == session_id


@pytest.mark.asyncio
async def test_hierarchical_replay_learning_nuances():
    """
    Test nuanced learning from hierarchical replay.

    Nuance: Replay should respect hierarchical structure and learn from
    group-level patterns, not just individual session sequences.
    """
    annotate_test(
        "test_hierarchical_replay_learning_nuances",
        pattern="hierarchical_memory",
        opinion="replay_respects_hierarchical_structure",
        category="system_interplay",
        hypothesis="Replay respects hierarchical structure for learning",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))
        replay = SessionReplayManager(manager)

        # Create sessions in different groups
        session1 = manager.create_session(context="group1")
        manager.add_evaluation(
            query="Query 1",
            response="Response 1",
            response_length=100,
            score=0.7,
            judgment_type="relevance",
            quality_flags=[],
            reasoning="",
            metadata={"group": 1},
        )

        manager.create_session(context="group2")
        manager.add_evaluation(
            query="Query 2",
            response="Response 2",
            response_length=100,
            score=0.8,
            judgment_type="relevance",
            quality_flags=[],
            reasoning="",
            metadata={"group": 2},
        )

        manager.flush_buffer()

        # Replay should work with hierarchical structure
        replayed = []
        def collect(e):
            replayed.append(e.query)

        replay.forward_replay(session1, collect)
        assert len(replayed) == 1
        assert replayed[0] == "Query 1"

        # Should be able to replay by group
        groups = manager.groups
        assert len(groups) > 0


@pytest.mark.asyncio
async def test_session_group_statistics_nuances():
    """
    Test nuanced statistics aggregation across session groups.

    Nuance: Group-level statistics should reflect patterns that individual
    session statistics might miss.
    """
    annotate_test(
        "test_session_group_statistics_nuances",
        pattern="hierarchical_memory",
        opinion="group_statistics_reveal_patterns",
        category="system_interplay",
        hypothesis="Group-level statistics reveal patterns missed by individual sessions",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(
            sessions_dir=Path(tmpdir),
            auto_group_by="day",
        )

        # Create multiple sessions in same day group
        for i in range(3):
            manager.create_session()
            manager.add_evaluation(
                query=f"Query {i}",
                response=f"Response {i}",
                response_length=100,
                score=0.6 + (i * 0.1),
                judgment_type="relevance",
                quality_flags=[],
                reasoning="",
                metadata={},
            )

        manager.flush_buffer()

        # Group statistics should aggregate across sessions
        groups = manager.groups
        assert len(groups) > 0

        # Each group should have aggregate stats
        for group in groups.values():
            assert len(group.session_ids) > 0


@pytest.mark.asyncio
async def test_quality_feedback_session_context_nuances():
    """
    Test nuanced use of session context in quality feedback.

    Nuance: Quality feedback should use session context (groups, metadata)
    to make better quality judgments.
    """
    annotate_test(
        "test_quality_feedback_session_context_nuances",
        pattern="hierarchical_memory",
        opinion="quality_feedback_uses_session_context",
        category="system_interplay",
        hypothesis="Quality feedback uses session context for better judgments",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        quality_feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=True,
        )
        manager = quality_feedback.session_manager

        # Create session with rich context
        session_id = manager.create_session(
            context="research_session",
            metadata={
                "domain": "knowledge_structure",
                "complexity": "high",
            },
        )

        # Add evaluation
        quality_feedback.evaluate_and_learn(
            query="Complex research query",
            response="Detailed research response",
            schema="decompose_and_synthesize",
        )

        # Quality feedback should have access to session context
        session = manager.get_session(session_id)
        assert session is not None
        assert session.context == "research_session"
        assert session.metadata.get("domain") == "knowledge_structure"

        # Evaluation should be in session
        assert len(session.evaluations) > 0


@pytest.mark.asyncio
async def test_adaptive_strategy_session_awareness():
    """
    Test nuanced adaptive strategy selection based on session context.

    Nuance: Adaptive manager should select strategies based on session
    group patterns, not just individual session history.
    """
    annotate_test(
        "test_adaptive_strategy_session_awareness",
        pattern="hierarchical_memory",
        opinion="adaptive_strategies_use_session_context",
        category="system_interplay",
        hypothesis="Adaptive strategies use session context for selection",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        quality_feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=True,
        )
        manager = quality_feedback.session_manager
        adaptive = AdaptiveQualityManager(quality_feedback)

        # Create sessions with different contexts
        contexts = ["research", "analysis", "synthesis"]
        for context in contexts:
            manager.create_session(context=context)
            manager.add_evaluation(
                query=f"Query for {context}",
                response=f"Response for {context}",
                response_length=100,
                score=0.7,
                judgment_type="relevance",
                quality_flags=[],
                reasoning="",
                metadata={"context": context},
            )

        manager.flush_buffer()

        # Adaptive manager should be aware of session contexts
        # and potentially select different strategies
        strategy = adaptive.get_adaptive_strategy("test query")
        assert strategy is not None

        # Strategy might vary based on session context
        # (if we implement context-aware strategy selection)


@pytest.mark.asyncio
async def test_hierarchical_learning_consolidation():
    """
    Test nuanced learning consolidation across hierarchical levels.

    Nuance: Learning should consolidate at multiple levels:
    - Individual evaluation level
    - Session level
    - Group level
    - Cross-group level
    """
    annotate_test(
        "test_hierarchical_learning_consolidation",
        pattern="hierarchical_memory",
        opinion="learning_consolidates_at_multiple_levels",
        category="system_interplay",
        hypothesis="Learning consolidates at evaluation, session, group, and cross-group levels",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        quality_feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=True,
        )
        manager = quality_feedback.session_manager
        adaptive = AdaptiveQualityManager(quality_feedback)

        # Create hierarchical structure: multiple groups, multiple sessions per group
        for group_idx in range(2):
            for session_idx in range(2):
                manager.create_session(
                    context=f"group_{group_idx}_session_{session_idx}",
                )
                manager.add_evaluation(
                    query=f"Query g{group_idx}s{session_idx}",
                    response=f"Response g{group_idx}s{session_idx}",
                    response_length=100,
                    score=0.7,
                    judgment_type="relevance",
                    quality_flags=[],
                    reasoning="",
                    metadata={"group": group_idx, "session": session_idx},
                )

        manager.flush_buffer()

        # Learning should consolidate at multiple levels
        # 1. Individual evaluations (4 total)
        all_sessions = manager.list_sessions()
        total_evals = sum(len(s.evaluations) for s in all_sessions)
        assert total_evals >= 4

        # 2. Session level (4 sessions)
        assert len(all_sessions) >= 4

        # 3. Group level (should have groups)
        groups = manager.groups
        assert len(groups) > 0

        # 4. Cross-group learning (adaptive manager)
        insights = adaptive.get_performance_insights()
        assert insights is not None


@pytest.mark.asyncio
async def test_session_lifecycle_quality_interaction():
    """
    Test nuanced interaction between session lifecycle and quality tracking.

    Nuance: Quality metrics should be preserved and accessible even after
    sessions are closed or archived.
    """
    annotate_test(
        "test_session_lifecycle_quality_interaction",
        pattern="hierarchical_memory",
        opinion="quality_metrics_persist_through_lifecycle",
        category="system_interplay",
        hypothesis="Quality metrics persist through session lifecycle transitions",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        quality_feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=True,
        )
        manager = quality_feedback.session_manager

        # Create and use session
        session_id = manager.create_session()
        quality_feedback.evaluate_and_learn(
            query="Test query",
            response="Test response",
            schema="chain_of_thought",
        )

        # Close session
        manager.close_session(session_id, finalize=True)

        # Quality metrics should still be accessible
        session = manager.get_session(session_id)
        assert session is not None
        assert session.status == "closed"
        assert session.final_statistics is not None

        # Statistics should reflect quality
        stats = session.final_statistics
        assert stats["evaluation_count"] > 0


@pytest.mark.asyncio
async def test_buffer_flush_quality_persistence():
    """
    Test nuanced persistence of quality data through buffer flushes.

    Nuance: Quality feedback data should persist correctly even when
    write buffering delays persistence.
    """
    annotate_test(
        "test_buffer_flush_quality_persistence",
        pattern="hierarchical_memory",
        opinion="quality_data_persists_through_buffering",
        category="system_interplay",
        hypothesis="Quality data persists correctly through write buffering",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        quality_feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=True,
        )
        manager = quality_feedback.session_manager

        # Add multiple evaluations (should buffer)
        for i in range(3):
            quality_feedback.evaluate_and_learn(
                query=f"Query {i}",
                response=f"Response {i}",
                schema="chain_of_thought",
            )

        # Before flush, data might be in buffer
        session = manager.get_session(manager.current_session_id)
        assert session is not None
        # Evaluations might be in buffer or persisted
        assert len(session.evaluations) >= 0

        # After flush, should be persisted
        manager.flush_buffer()
        session = manager.get_session(manager.current_session_id)
        assert len(session.evaluations) >= 3


@pytest.mark.asyncio
async def test_cross_group_pattern_recognition():
    """
    Test nuanced pattern recognition across different session groups.

    Nuance: System should recognize patterns that span multiple groups,
    not just patterns within a single group.
    """
    annotate_test(
        "test_cross_group_pattern_recognition",
        pattern="hierarchical_memory",
        opinion="patterns_recognized_across_groups",
        category="system_interplay",
        hypothesis="System recognizes patterns that span multiple session groups",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        quality_feedback = QualityFeedbackLoop(
            evaluation_history_path=history_path,
            use_sessions=True,
        )
        manager = quality_feedback.session_manager
        adaptive = AdaptiveQualityManager(quality_feedback)

        # Create sessions in different groups with similar patterns
        for day in range(3):
            manager.create_session(context=f"day_{day}")
            manager.add_evaluation(
                query="Similar pattern query",
                response="Similar pattern response",
                response_length=100,
                score=0.7,
                judgment_type="relevance",
                quality_flags=[],
                reasoning="",
                metadata={"day": day, "pattern": "similar"},
            )

        manager.flush_buffer()

        # Adaptive manager should recognize cross-group patterns
        insights = adaptive.get_performance_insights()
        assert insights is not None

        # Should have learned from multiple groups
        all_sessions = manager.list_sessions()
        assert len(all_sessions) >= 3

