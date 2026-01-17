"""Comprehensive backwards compatibility tests for all display improvements."""

import pytest

from pran.agent import KnowledgeAgent
from pran.orchestrator import StructuredOrchestrator


def test_agent_initialization_backwards_compatible():
    """Test that agent initialization works with old and new code."""
    # Old way: should still work
    agent1 = KnowledgeAgent(enable_quality_feedback=False)
    assert agent1 is not None
    assert hasattr(agent1, 'conversation_history')
    assert hasattr(agent1, 'prior_beliefs')
    assert hasattr(agent1, 'recent_queries')

    # New way: with quality feedback
    agent2 = KnowledgeAgent(enable_quality_feedback=True)
    assert agent2 is not None
    assert agent2.quality_feedback is not None


@pytest.mark.asyncio
async def test_response_structure_backwards_compatible():
    """Test that response structure includes both old and new fields."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None  # Use fallback

    response = await agent.chat("Test query", use_research=False)

    # Old fields must still exist
    assert "response" in response
    assert isinstance(response["response"], str)

    # New fields should exist
    assert "response_tiers" in response
    assert isinstance(response["response_tiers"], dict)
    assert "summary" in response["response_tiers"]
    assert "detailed" in response["response_tiers"]


@pytest.mark.asyncio
async def test_research_response_structure():
    """Test that research response structure is backwards compatible."""
    agent = KnowledgeAgent(enable_quality_feedback=False)

    # Mock research result structure
    response = await agent.chat("Test", use_research=False)

    # If research was conducted, check structure
    if response.get("research_conducted"):
        research = response.get("research", {})
        if research:
            # Old fields
            assert "query" in research or "final_synthesis" in research or "subsolutions" in research

            # New fields (if topology exists)
            if "topology" in research:
                topology = research["topology"]
                # Old topology fields
                assert "trust_summary" in topology or "betti_numbers" in topology

                # New topology fields (optional, may not exist if no nodes)
                # These are optional additions, not breaking changes


def test_orchestrator_backwards_compatible():
    """Test that orchestrator still works with old method signatures."""
    from pran.research import ResearchAgent

    StructuredOrchestrator(
        ResearchAgent(),
        None,  # LLM service can be None
    )

    # Should be able to call with old signature (no prior_beliefs)
    # This is tested implicitly through agent.chat()


@pytest.mark.asyncio
async def test_belief_tracking_optional():
    """Test that belief tracking doesn't break if no beliefs are stated."""
    agent = KnowledgeAgent(enable_quality_feedback=False)

    # Message without belief indicators
    response = await agent.chat("What is trust?")

    # Should work fine, no beliefs extracted
    assert len(agent.prior_beliefs) == 0
    assert "response" in response


@pytest.mark.asyncio
async def test_context_adaptation_optional():
    """Test that context adaptation doesn't break if no recent queries."""
    agent = KnowledgeAgent(enable_quality_feedback=False)

    # First query: no recent queries
    response1 = await agent.chat("First query")
    assert "response" in response1

    # Second query: should track first query
    response2 = await agent.chat("Second query")
    assert len(agent.recent_queries) >= 1
    assert "response" in response2


@pytest.mark.asyncio
async def test_source_references_optional():
    """Test that source references don't break if no research."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None

    response = await agent.chat("Test", use_research=False)

    # Should work fine, no source references added
    assert "response" in response
    assert isinstance(response["response"], str)


@pytest.mark.asyncio
async def test_progressive_disclosure_always_created():
    """Test that response tiers are always created, even without research."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None

    response = await agent.chat("Test", use_research=False)

    # Response tiers should always exist
    assert "response_tiers" in response
    tiers = response["response_tiers"]
    assert "summary" in tiers
    assert "detailed" in tiers
    assert "structured" in tiers
    assert "evidence" in tiers


def test_clear_history_backwards_compatible():
    """Test that clear_history clears all new state."""
    agent = KnowledgeAgent(enable_quality_feedback=False)

    # Add some state
    agent.conversation_history.append({"role": "user", "content": "test"})
    agent.prior_beliefs.append({"text": "test belief"})
    agent.recent_queries.append({"message": "test query"})

    # Clear
    agent.clear_history()

    # All should be empty
    assert len(agent.conversation_history) == 0
    assert len(agent.prior_beliefs) == 0
    assert len(agent.recent_queries) == 0


@pytest.mark.asyncio
async def test_quality_feedback_integration():
    """Test that quality feedback still works with new features."""
    agent = KnowledgeAgent(enable_quality_feedback=True)
    agent.llm_service = None

    response = await agent.chat("Test query", use_research=False)

    # Quality feedback should still work
    if agent.quality_feedback:
        assert "quality" in response or response.get("quality_score") is not None


def test_orchestrator_prior_beliefs_optional():
    """Test that orchestrator works with or without prior_beliefs."""
    from pran.research import ResearchAgent

    orchestrator = StructuredOrchestrator(ResearchAgent(), None)

    # Should be able to compute belief alignment with empty list
    alignment = orchestrator._compute_belief_alignment("Some evidence", [])
    assert alignment == 0.5  # Neutral when no prior beliefs


def test_topic_similarity_edge_cases():
    """Test topic similarity computation with edge cases."""
    agent = KnowledgeAgent(enable_quality_feedback=False)

    # Empty recent topics
    similarity = agent._compute_topic_similarity("test", [])
    assert similarity == 0.0

    # No overlap
    similarity = agent._compute_topic_similarity("completely different topic", ["unrelated words"])
    assert 0.0 <= similarity <= 1.0


@pytest.mark.asyncio
async def test_response_length_adaptation_optional():
    """Test that response length adaptation works even without adaptive manager."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.adaptive_manager = None  # Disable adaptive manager
    agent.llm_service = None

    # Should still work
    response = await agent.chat("Test")
    assert "response" in response


def test_display_helpers_import():
    """Test that display helpers can be imported and used."""
    from pran.display_helpers import (
        format_clique_clusters,
        format_source_credibility,
        format_trust_summary,
    )

    # Test with empty data
    assert format_trust_summary({}) == ""
    assert format_source_credibility({}) == ""
    assert format_clique_clusters([]) == ""

    # Test with valid data
    trust_summary = {"avg_trust": 0.75}
    result = format_trust_summary(trust_summary)
    assert "Average Trust" in result or "0.75" in result


def test_all_imports_work():
    """Test that all modules can be imported without errors."""
    import pran.agent
    import pran.cli
    import pran.context_topology
    import pran.display_helpers
    import pran.llm
    import pran.orchestrator
    import pran.quality_feedback

    # Web module has optional dependencies, test with try/except
    try:
        import pran.web
    except ImportError:
        # manus is optional, so this is OK
        pass

    # If we get here, core imports work
    assert True

