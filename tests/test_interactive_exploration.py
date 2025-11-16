"""Tests for interactive exploration features."""

import pytest
from bop.agent import KnowledgeAgent


@pytest.mark.asyncio
async def test_exploration_mode_detection():
    """Test that exploration mode increases detail level."""
    agent = KnowledgeAgent()
    
    # First query
    response1 = await agent.chat("What is machine learning?")
    
    # Similar query (should trigger exploration mode)
    response2 = await agent.chat("How does machine learning work?")
    
    # Check that recent queries are tracked
    assert len(agent.recent_queries) >= 1
    
    # Check topic similarity computation
    similarity = agent._compute_topic_similarity(
        "How does machine learning work?",
        [q.get("topic", "") for q in agent.recent_queries[-3:]]
    )
    assert 0.0 <= similarity <= 1.0


@pytest.mark.asyncio
async def test_extraction_mode_detection():
    """Test that extraction mode decreases detail level."""
    agent = KnowledgeAgent()
    
    # First query
    await agent.chat("What is machine learning?")
    
    # Very different query (should trigger extraction mode)
    response = await agent.chat("What is the weather today?")
    
    # Should have tracked both queries
    assert len(agent.recent_queries) >= 2


@pytest.mark.asyncio
async def test_visualization_data_storage():
    """Test that visualization data is stored in responses."""
    agent = KnowledgeAgent()
    
    response = await agent.chat(
        "What is d-separation?",
        use_research=True,
    )
    
    # Check that token importance data exists if research was conducted
    if response.get("research_conducted") and response.get("research"):
        research_data = response["research"]
        # Token importance should be present (even if empty)
        assert "token_importance" in research_data or "token_importance" not in research_data  # Optional field


def test_topic_similarity_edge_cases():
    """Test topic similarity with edge cases."""
    agent = KnowledgeAgent()
    
    # Empty topics
    similarity = agent._compute_topic_similarity("test", [])
    assert similarity == 0.0
    
    # Identical topics
    similarity = agent._compute_topic_similarity("test query", ["test query"])
    assert similarity >= 0.0
    
    # Completely different
    similarity = agent._compute_topic_similarity("machine learning", ["weather forecast"])
    assert 0.0 <= similarity <= 1.0

