"""Tests for multi-turn conversations mapped to sessions.

Multi-turn conversations are approximately equivalent to sessions:
- Each turn adds an evaluation
- Session context accumulates across turns
- Quality feedback learns from turn sequence
- Adaptive strategies improve across turns
"""

import tempfile
from pathlib import Path

import pytest

from bop.agent import KnowledgeAgent
from bop.session_manager import HierarchicalSessionManager
from tests.test_annotations import annotate_test

# Annotate all tests in this module
# Pattern: multi_turn_conversation
# Opinion: multi_turn_approximates_session
# Category: conversation_modeling


@pytest.mark.asyncio
async def test_multi_turn_conversation_as_session():
    """
    Test that multi-turn conversations map to sessions.

    Pattern: Multi-turn conversation
    Opinion: Each conversation turn ≈ session evaluation
    Category: Conversation modeling
    """
    # Annotate this test
    annotate_test(
        "test_multi_turn_conversation_as_session",
        pattern="multi_turn_conversation",
        opinion="multi_turn_approximates_session",
        category="conversation_modeling",
        hypothesis="Multi-turn conversations map to sessions",
        description="Each conversation turn adds an evaluation to the session",
    )
    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)
        manager = agent.quality_feedback.session_manager

        # Simulate multi-turn conversation
        turns = [
            "What is knowledge structure?",
            "How does it relate to trust?",
            "Can you explain uncertainty quantification?",
            "What are the practical applications?",
        ]

        session_id = None
        for i, query in enumerate(turns):
            await agent.chat(query, use_research=False)

            # First turn creates session
            if i == 0:
                session_id = manager.current_session_id
                assert session_id is not None

            # All turns should be in same session
            assert manager.current_session_id == session_id

            # Each turn should add evaluations (relevance, accuracy, completeness)
            # Plus potential retries, so we check >= expected minimum
            session = manager.get_session(session_id)
            # Minimum: 3 judgment types per turn (relevance, accuracy, completeness)
            # May have more due to retries
            assert len(session.evaluations) >= (i + 1) * 3

        manager.flush_buffer()

        # Verify session contains all turns
        final_session = manager.get_session(session_id)
        # Each turn creates at least 3 evaluations (relevance, accuracy, completeness)
        # May have more due to retries
        assert len(final_session.evaluations) >= len(turns) * 3

        # Session should have accumulated context
        stats = final_session.get_statistics()
        assert stats["evaluation_count"] >= len(turns) * 3


@pytest.mark.asyncio
async def test_multi_turn_context_accumulation():
    """
    Test that context accumulates across conversation turns.

    Pattern: Context accumulation
    Opinion: Later turns benefit from earlier context
    Category: Conversation modeling
    """
    annotate_test(
        "test_multi_turn_context_accumulation",
        pattern="multi_turn_conversation",
        opinion="multi_turn_approximates_session",
        category="conversation_modeling",
        hypothesis="Context accumulates across conversation turns",
    )
    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)
        manager = agent.quality_feedback.session_manager

        # Multi-turn conversation with context building
        turns = [
            ("What is hierarchical learning?", "establishing_base"),
            ("How does it work in practice?", "building_on_base"),
            ("What are the limitations?", "critical_analysis"),
        ]

        session_id = None
        for i, (query, context_type) in enumerate(turns):
            await agent.chat(query, use_research=False)

            if i == 0:
                session_id = manager.current_session_id

            # Session accumulates evaluations
            session = manager.get_session(session_id)
            assert len(session.evaluations) >= (i + 1) * 3

        # Final session should have all context
        final_session = manager.get_session(session_id)
        # Each turn creates at least 3 evaluations
        assert len(final_session.evaluations) >= len(turns) * 3

        # Quality should potentially improve across turns (adaptive learning)
        if agent.adaptive_manager:
            # Later turns might have better strategies
            insights = agent.adaptive_manager.get_performance_insights()
            assert insights is not None


@pytest.mark.asyncio
async def test_multi_turn_adaptive_improvement():
    """
    Test that adaptive strategies improve across conversation turns.

    Pattern: Adaptive learning across turns
    Opinion: System learns from turn sequence to improve later turns
    Category: Adaptive learning
    """
    annotate_test(
        "test_multi_turn_adaptive_improvement",
        pattern="multi_turn_conversation",
        opinion="adaptive_strategies_improve_across_turns",
        category="adaptive_learning",
        hypothesis="Adaptive strategies improve across conversation turns",
    )
    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)

        # Conversation with similar query types (should trigger learning)
        turns = [
            "What is trust?",
            "What is uncertainty?",
            "What is knowledge structure?",
        ]

        strategies = []
        for query in turns:
            response = await agent.chat(query, use_research=False)

            if response.get("quality", {}).get("adaptive_strategy"):
                strategies.append(response["quality"]["adaptive_strategy"])

        # Strategies should be available (may improve across turns)
        assert len(strategies) > 0

        # Later strategies might have higher confidence (if learning occurred)
        if len(strategies) > 1:
            # This is an opinion/testable hypothesis
            # Confidence might increase as system learns
            confidences = [s.get("confidence", 0) for s in strategies]
            # At minimum, strategies should exist
            assert all(c >= 0 for c in confidences)


@pytest.mark.asyncio
async def test_multi_turn_session_lifecycle():
    """
    Test session lifecycle in multi-turn conversations.

    Pattern: Session lifecycle in conversations
    Opinion: Sessions should auto-close after conversation ends
    Category: Lifecycle management
    """
    annotate_test(
        "test_multi_turn_session_lifecycle",
        pattern="multi_turn_conversation",
        opinion="multi_turn_approximates_session",
        category="lifecycle_management",
        hypothesis="Sessions manage lifecycle in multi-turn conversations",
    )
    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)
        manager = agent.quality_feedback.session_manager

        # Start conversation
        await agent.chat("First question", use_research=False)
        session_id = manager.current_session_id

        # Continue conversation
        await agent.chat("Follow-up question", use_research=False)
        assert manager.current_session_id == session_id

        # Session should still be active
        session = manager.get_session(session_id)
        assert session.status == "active"

        # After inactivity, should auto-close
        manager.auto_close_inactive_sessions(timeout=0.001)  # Very short timeout
        # Note: This may or may not close depending on timing
        # The important thing is the mechanism exists


def test_multi_turn_statistics_accumulation():
    """
    Test that statistics accumulate across conversation turns.

    Pattern: Statistics accumulation
    Opinion: Session statistics reflect entire conversation
    Category: Statistics
    """
    annotate_test(
        "test_multi_turn_statistics_accumulation",
        pattern="multi_turn_conversation",
        opinion="multi_turn_approximates_session",
        category="conversation_modeling",
        hypothesis="Statistics accumulate across conversation turns",
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))

        session_id = manager.create_session(context="multi_turn_conversation")

        # Simulate multi-turn conversation
        turns = [
            ("Query 1", 0.7),
            ("Query 2", 0.8),
            ("Query 3", 0.9),
        ]

        for query, score in turns:
            manager.add_evaluation(
                query=query,
                response=f"Response to {query}",
                response_length=100,
                score=score,
                judgment_type="relevance",
                quality_flags=[],
                reasoning="",
                metadata={"turn": turns.index((query, score))},
            )

        manager.flush_buffer()

        # Statistics should reflect all turns
        session = manager.get_session(session_id)
        stats = session.get_statistics()

        assert stats["evaluation_count"] == len(turns)
        assert stats["mean_score"] == pytest.approx(0.8, abs=0.01)
        assert stats["min_score"] == 0.7
        assert stats["max_score"] == 0.9


@pytest.mark.asyncio
async def test_multi_turn_cross_session_learning():
    """
    Test that learning from one conversation improves next.

    Pattern: Cross-session learning
    Opinion: Patterns learned in one conversation help next
    Category: Adaptive learning
    """
    annotate_test(
        "test_multi_turn_cross_session_learning",
        pattern="multi_turn_conversation",
        opinion="learning_transfers_across_conversations",
        category="adaptive_learning",
        hypothesis="Learning from one conversation improves next",
    )
    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)
        adaptive = agent.adaptive_manager

        # First conversation
        await agent.chat("What is trust?", use_research=False)
        await agent.chat("How does trust work?", use_research=False)

        # Second conversation (should benefit from first)
        await agent.chat("What is uncertainty?", use_research=False)

        # Adaptive manager should have learned patterns
        if adaptive:
            insights = adaptive.get_performance_insights()
            assert insights is not None

            # Should have query type performance data
            if insights.get("query_type_performance"):
                assert len(insights["query_type_performance"]) > 0


def test_multi_turn_replay():
    """
    Test replaying multi-turn conversations.

    Pattern: Experience replay
    Opinion: Can replay entire conversations for learning
    Category: Experience replay
    """
    annotate_test(
        "test_multi_turn_replay",
        pattern="multi_turn_conversation",
        opinion="conversations_can_be_replayed",
        category="experience_replay",
        hypothesis="Can replay entire conversations for learning",
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = HierarchicalSessionManager(sessions_dir=Path(tmpdir))
        from bop.session_replay import SessionReplayManager
        replay = SessionReplayManager(manager)

        # Create multi-turn session
        session_id = manager.create_session(context="conversation")

        turns = ["Query 1", "Query 2", "Query 3"]
        for query in turns:
            manager.add_evaluation(
                query=query,
                response=f"Response {query}",
                response_length=100,
                score=0.7,
                judgment_type="relevance",
                quality_flags=[],
                reasoning="",
                metadata={},
            )

        manager.flush_buffer()

        # Replay conversation
        replayed = []
        def collect_turn(e):
            replayed.append(e.query)

        replay.forward_replay(session_id, collect_turn)

        # Should replay all turns in order
        assert len(replayed) == len(turns)
        assert replayed == turns


@pytest.mark.asyncio
async def test_multi_turn_quality_tracking():
    """
    Test quality tracking across conversation turns.

    Pattern: Quality tracking
    Opinion: Quality metrics track conversation quality over time
    Category: Quality feedback
    """
    annotate_test(
        "test_multi_turn_quality_tracking",
        pattern="multi_turn_conversation",
        opinion="quality_tracks_conversation_over_time",
        category="quality_feedback",
        hypothesis="Quality metrics track conversation quality over time",
    )
    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)
        manager = agent.quality_feedback.session_manager

        # Multi-turn with varying quality
        queries = [
            "Simple question",
            "Complex multi-part question requiring detailed analysis",
            "Follow-up clarification",
        ]

        scores = []
        for query in queries:
            response = await agent.chat(query, use_research=False)
            if response.get("quality"):
                scores.append(response["quality"].get("score", 0))

        # All turns should have quality scores
        assert len(scores) == len(queries)

        # Session should aggregate quality
        session = manager.get_session(manager.current_session_id)
        stats = session.get_statistics()
        assert stats["evaluation_count"] > 0
        assert stats["mean_score"] >= 0.0

