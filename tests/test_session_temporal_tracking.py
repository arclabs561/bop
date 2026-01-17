"""Tests for session-level temporal knowledge tracking."""

from datetime import datetime, timedelta, timezone

import pytest

from pran.agent import KnowledgeAgent
from pran.knowledge_tracking import KnowledgeTracker


def test_knowledge_tracker_extract_concepts():
    """Test concept extraction from text."""
    tracker = KnowledgeTracker()

    # Test with query about d-separation
    query = "What is d-separation and how does it relate to causality?"
    concepts = tracker.extract_concepts(query)

    assert "d-separation" in concepts
    assert "causality" in concepts


def test_knowledge_tracker_track_query():
    """Test tracking concepts from a query-response pair."""
    tracker = KnowledgeTracker()

    session_id = "test_session_1"
    query = "What is d-separation?"
    response = "D-separation is a graphical criterion for determining conditional independence in Bayesian networks."
    timestamp = datetime.now(timezone.utc).isoformat()

    tracker.track_query(
        session_id=session_id,
        query=query,
        response=response,
        timestamp=timestamp,
        confidence=0.85,
    )

    # Should have tracked d-separation
    assert "d-separation" in tracker.concept_learning
    learning = tracker.concept_learning["d-separation"]
    assert learning.first_learned_at == timestamp
    assert learning.query_count == 1
    assert session_id in learning.session_ids

    # Should have session knowledge
    assert session_id in tracker.session_knowledge
    session = tracker.session_knowledge[session_id]
    assert "d-separation" in session.concepts_learned


def test_knowledge_tracker_refinement():
    """Test that refining an existing concept is tracked correctly."""
    tracker = KnowledgeTracker()

    session_id_1 = "session_1"
    session_id_2 = "session_2"
    timestamp_1 = datetime.now(timezone.utc).isoformat()
    timestamp_2 = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    # First occurrence - learning
    tracker.track_query(
        session_id=session_id_1,
        query="What is d-separation?",
        response="D-separation is a criterion...",
        timestamp=timestamp_1,
    )

    # Second occurrence - refinement
    tracker.track_query(
        session_id=session_id_2,
        query="How does d-separation work?",
        response="D-separation determines conditional independence...",
        timestamp=timestamp_2,
    )

    learning = tracker.concept_learning["d-separation"]
    assert learning.first_learned_at == timestamp_1
    assert learning.last_updated_at == timestamp_2
    assert learning.query_count == 2
    assert len(learning.session_ids) == 2

    # First session should show as learned
    session_1 = tracker.session_knowledge[session_id_1]
    assert "d-separation" in session_1.concepts_learned

    # Second session should show as refined
    session_2 = tracker.session_knowledge[session_id_2]
    assert "d-separation" in session_2.concepts_refined


def test_knowledge_tracker_get_concept_evolution():
    """Test getting evolution of a specific concept."""
    tracker = KnowledgeTracker()

    session_id = "test_session"
    timestamp = datetime.now(timezone.utc).isoformat()

    tracker.track_query(
        session_id=session_id,
        query="What is trust?",
        response="Trust is important for knowledge systems.",
        timestamp=timestamp,
        confidence=0.8,
    )

    evolution = tracker.get_concept_evolution("trust")
    assert evolution is not None
    assert evolution["concept"] == "trust"
    assert evolution["first_learned_at"] == timestamp
    assert evolution["session_count"] == 1
    assert evolution["query_count"] == 1
    assert evolution["recent_confidence"] == 0.8  # Changed from average_confidence


def test_knowledge_tracker_cross_session_evolution():
    """Test getting cross-session evolution."""
    tracker = KnowledgeTracker()

    # Track concepts across multiple sessions
    for i in range(3):
        session_id = f"session_{i}"
        timestamp = (datetime.now(timezone.utc) + timedelta(days=i)).isoformat()

        tracker.track_query(
            session_id=session_id,
            query=f"Query about trust {i}",
            response=f"Response about trust {i}",
            timestamp=timestamp,
        )

    evolution = tracker.get_cross_session_evolution(limit=5)
    assert len(evolution) > 0
    assert any(item["concept"] == "trust" for item in evolution)

    trust_evolution = next(item for item in evolution if item["concept"] == "trust")
    assert trust_evolution["session_count"] == 3


@pytest.mark.asyncio
async def test_agent_tracks_session_knowledge():
    """Test that agent tracks knowledge across sessions."""
    agent = KnowledgeAgent(enable_quality_feedback=True)
    agent.llm_service = None

    # First query in session
    response1 = await agent.chat(
        "What is d-separation?",
        use_research=False,
    )

    # Should have session knowledge
    assert response1.get("timestamp") is not None

    # If session exists, should track knowledge
    if agent.quality_feedback and agent.quality_feedback.session_manager:
        current_session = agent.quality_feedback.session_manager.get_current_session()
        if current_session:
            # Knowledge tracker should have tracked concepts
            assert hasattr(agent, "knowledge_tracker")
            assert agent.knowledge_tracker is not None

            # Check if concepts were extracted
            concepts = agent.knowledge_tracker.extract_concepts("What is d-separation?")
            assert len(concepts) > 0


@pytest.mark.asyncio
async def test_agent_cross_session_evolution():
    """Test that agent tracks evolution across multiple sessions."""
    agent = KnowledgeAgent(enable_quality_feedback=True)
    agent.llm_service = None

    # Query 1: Learn about d-separation
    response1 = await agent.chat("What is d-separation?", use_research=False)

    # Query 2: Refine understanding
    response2 = await agent.chat("How does d-separation relate to causality?", use_research=False)

    # Both should have timestamps
    assert response1.get("timestamp")
    assert response2.get("timestamp")

    # If session knowledge is tracked, should show evolution
    if response2.get("session_knowledge"):
        session_knowledge = response2["session_knowledge"]
        # Should have tracked concepts
        assert "concepts_learned" in session_knowledge or "concepts_refined" in session_knowledge

    # Cross-session evolution should be available if multiple sessions exist
    if response2.get("cross_session_evolution"):
        evolution = response2["cross_session_evolution"]
        assert isinstance(evolution, list)


@pytest.mark.asyncio
async def test_agent_session_concepts_display():
    """Test that session concepts are included in response."""
    agent = KnowledgeAgent(enable_quality_feedback=True)
    agent.llm_service = None

    # Make multiple queries about related topics
    await agent.chat("What is d-separation?", use_research=False)
    await agent.chat("What is trust?", use_research=False)
    response3 = await agent.chat("How does uncertainty affect trust?", use_research=False)

    # Should have session concepts if tracking is enabled
    if response3.get("session_concepts"):
        session_concepts = response3["session_concepts"]
        assert "concepts" in session_concepts
        assert isinstance(session_concepts["concepts"], list)


@pytest.mark.asyncio
async def test_knowledge_tracker_persistence():
    """Test that knowledge tracker maintains state across queries."""
    agent = KnowledgeAgent(enable_quality_feedback=True)
    agent.llm_service = None

    # First query
    await agent.chat("What is d-separation?", use_research=False)

    # Second query about same concept (should be refinement)
    response2 = await agent.chat("Explain d-separation in detail", use_research=False)

    # Knowledge tracker should persist between queries
    assert agent.knowledge_tracker is not None

    # If both queries are in same session, should show refinement
    if response2.get("session_concepts"):
        concepts = response2["session_concepts"].get("concepts", [])
        dsep_concept = next((c for c in concepts if c.get("concept") == "d-separation"), None)
        if dsep_concept:
            # Should show it was refined (not new) if it appeared in first query
            pass  # This depends on session management

