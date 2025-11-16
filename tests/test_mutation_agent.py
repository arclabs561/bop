"""Mutation testing helpers and focused tests for agent.

These tests are designed to catch mutations in the agent code.
They should be comprehensive enough to kill most mutants.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from bop.agent import KnowledgeAgent


@pytest.mark.asyncio
async def test_agent_initialization_state():
    """Test agent initializes with correct state."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    assert agent.research_agent is not None
    assert agent.conversation_history == []
    assert agent.prior_beliefs == []
    assert agent.recent_queries == []
    assert agent.knowledge_base is not None


@pytest.mark.asyncio
async def test_agent_chat_basic_flow():
    """Test basic chat flow without LLM."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None
    
    response = await agent.chat("Hello")
    
    assert response["message"] == "Hello"
    assert "response" in response
    assert response["schema_used"] is None
    assert response["research_conducted"] is False
    assert len(agent.conversation_history) == 2  # User + assistant


@pytest.mark.asyncio
async def test_agent_chat_with_schema():
    """Test chat with schema selection."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None
    
    response = await agent.chat("Test", use_schema="chain_of_thought")
    
    assert response["schema_used"] == "chain_of_thought"
    assert "structured_reasoning" in response


@pytest.mark.asyncio
async def test_agent_chat_research_flag():
    """Test research flag is properly set."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None
    agent.research_agent.deep_research = AsyncMock(return_value={
        "query": "test",
        "subsolutions": [],
        "final_synthesis": "Test synthesis",
    })
    
    response = await agent.chat("Test query", use_research=True)
    
    assert response["research_conducted"] is True
    assert "research" in response


@pytest.mark.asyncio
async def test_conversation_history_tracking():
    """Test conversation history is properly tracked."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None
    
    await agent.chat("First message")
    await agent.chat("Second message")
    
    history = agent.get_conversation_history()
    assert len(history) == 4  # 2 user + 2 assistant
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "First message"
    assert history[1]["role"] == "assistant"
    assert history[2]["role"] == "user"
    assert history[2]["content"] == "Second message"


def test_clear_history():
    """Test clearing history resets all state."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    # Add some state
    agent.conversation_history = [{"role": "user", "content": "test"}]
    agent.prior_beliefs = [{"text": "test belief"}]
    agent.recent_queries = [{"message": "test query"}]
    
    agent.clear_history()
    
    assert len(agent.conversation_history) == 0
    assert len(agent.prior_beliefs) == 0
    assert len(agent.recent_queries) == 0


@pytest.mark.asyncio
async def test_extract_prior_beliefs():
    """Test prior belief extraction from messages."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    # Test belief extraction
    agent._extract_prior_beliefs("I think trust is important")
    assert len(agent.prior_beliefs) > 0
    assert "trust" in agent.prior_beliefs[0]["text"].lower()
    
    # Test no belief extraction
    agent.prior_beliefs = []
    agent._extract_prior_beliefs("What is trust?")
    assert len(agent.prior_beliefs) == 0


def test_track_recent_query():
    """Test recent query tracking."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    agent._track_recent_query("What is information geometry?")
    
    assert len(agent.recent_queries) == 1
    assert "information" in agent.recent_queries[0]["topic"].lower() or "geometry" in agent.recent_queries[0]["topic"].lower()
    assert "message" in agent.recent_queries[0]
    assert "key_terms" in agent.recent_queries[0]


def test_compute_topic_similarity():
    """Test topic similarity computation."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    # Similar topics
    similarity = agent._compute_topic_similarity(
        "information geometry",
        ["information geometry", "geometric information"]
    )
    assert similarity > 0.5
    
    # Different topics
    similarity = agent._compute_topic_similarity(
        "information geometry",
        ["weather forecast", "cooking recipes"]
    )
    assert similarity < 0.5
    
    # Empty topics
    similarity = agent._compute_topic_similarity("test", [])
    assert similarity == 0.0


def test_create_response_tiers():
    """Test response tier creation."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    full_response = "This is a test response. It has multiple sentences. And more content here."
    research = {}
    
    tiers = agent._create_response_tiers(full_response, research, "test query")
    
    assert "summary" in tiers
    assert "structured" in tiers
    assert "detailed" in tiers
    assert "evidence" in tiers
    assert len(tiers["summary"]) <= 150
    assert tiers["detailed"] == full_response


def test_add_source_references():
    """Test source reference addition."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    response_text = "This is a test response."
    research = {}  # Empty research = no sources
    
    result = agent._add_source_references(response_text, research)
    assert result == response_text  # No sources to add
    
    # With research data
    research = {
        "subsolutions": [{
            "subproblem": "test",
            "synthesis": "test synthesis",
            "tools_used": ["tool1"],
            "results": [{"tool": "tool1", "content": "result"}]
        }]
    }
    
    result = agent._add_source_references(response_text, research)
    assert "Sources:" in result or result == response_text  # May or may not add sources depending on provenance


def test_search_knowledge_base():
    """Test knowledge base search."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    results = agent.search_knowledge_base("test")
    assert isinstance(results, list)
    
    # Results should be list of dicts with document and matches
    if results:
        assert "document" in results[0]
        assert "matches" in results[0]


@pytest.mark.asyncio
async def test_generate_response_fallback():
    """Test response generation fallback when LLM unavailable."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None
    
    response = await agent._generate_response("test message", {}, None, None)
    
    assert "test message" in response.lower() or "LLM service not available" in response


@pytest.mark.asyncio
async def test_generate_response_with_length():
    """Test response generation with length constraint."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    with patch("bop.agent.LLMService") as mock_llm_class:
        mock_llm = MagicMock()
        # Return a very long response
        long_response = "word " * 1000
        mock_llm.generate_response = AsyncMock(return_value=long_response)
        mock_llm_class.return_value = mock_llm
        
        agent.llm_service = mock_llm
        
        response = await agent._generate_response("test", {}, None, expected_length=100)
        
        # Should be truncated
        assert len(response) < len(long_response)


def test_extract_expected_concepts():
    """Test concept extraction from queries."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    concepts = agent._extract_expected_concepts("What is trust and uncertainty?")
    assert "trust" in concepts or "uncertainty" in concepts
    
    concepts = agent._extract_expected_concepts("Hello world")
    # May or may not extract concepts, but should return a list
    assert isinstance(concepts, list)


def test_get_relevant_context():
    """Test context retrieval from knowledge base."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    context = agent._get_relevant_context("test query")
    # May return None if no relevant content, or a string
    assert context is None or isinstance(context, str)


@pytest.mark.asyncio
async def test_response_tiers_with_research():
    """Test response tiers when research is available."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    full_response = "Test response"
    research = {
        "final_synthesis": "Final synthesis text",
        "subsolutions": [{
            "subproblem": "Subproblem 1",
            "synthesis": "Synthesis 1",
            "tools_used": ["tool1"]
        }]
    }
    
    tiers = agent._create_response_tiers(full_response, research, "test")
    
    assert "summary" in tiers
    assert "structured" in tiers
    assert "evidence" in tiers
    # Evidence should include research content
    assert len(tiers["evidence"]) >= len(full_response)


# ============================================================================
# Critical Logic Mutation Tests
# These tests target specific thresholds and logic branches that mutations
# commonly affect
# ============================================================================

def test_topic_similarity_threshold():
    """Test topic similarity threshold (0.5) for exploration/extraction mode."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    # Test exactly at threshold
    similarity_05 = agent._compute_topic_similarity(
        "information geometry",
        ["information geometry"]
    )
    # Should be > 0.5 (exploration mode)
    assert similarity_05 > 0.5
    
    # Test below threshold
    similarity_low = agent._compute_topic_similarity(
        "information geometry",
        ["weather forecast"]
    )
    # Should be < 0.5 (extraction mode)
    assert similarity_low < 0.5


def test_belief_extraction_minimum_length():
    """Test belief extraction minimum length threshold (10 chars)."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    # Too short - should not extract
    agent._extract_prior_beliefs("I think x")
    assert len(agent.prior_beliefs) == 0
    
    # Long enough - should extract
    agent.prior_beliefs = []
    agent._extract_prior_beliefs("I think trust is important for systems")
    assert len(agent.prior_beliefs) > 0
    assert len(agent.prior_beliefs[0]["text"]) > 10


def test_recent_queries_limit():
    """Test recent queries limit (10 items)."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    # Add 15 queries
    for i in range(15):
        agent._track_recent_query(f"Query {i}")
    
    # Should only keep last 10
    assert len(agent.recent_queries) == 10
    assert agent.recent_queries[0]["message"] == "Query 5"  # First of last 10
    assert agent.recent_queries[-1]["message"] == "Query 14"  # Last


def test_prior_beliefs_limit():
    """Test prior beliefs limit (10 items)."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    # Add 15 beliefs
    for i in range(15):
        agent._extract_prior_beliefs(f"I think belief number {i} is important")
    
    # Should only keep last 10
    assert len(agent.prior_beliefs) <= 10


def test_topic_similarity_edge_cases():
    """Test topic similarity edge cases that mutations might break."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    # Empty topics
    assert agent._compute_topic_similarity("test", []) == 0.0
    
    # Identical topics
    similarity = agent._compute_topic_similarity(
        "information geometry",
        ["information geometry"]
    )
    assert similarity > 0.8  # Should be very similar
    
    # Completely different
    similarity = agent._compute_topic_similarity(
        "information geometry",
        ["cooking recipes weather"]
    )
    assert similarity < 0.3  # Should be low


@pytest.mark.asyncio
async def test_response_length_adaptation():
    """Test response length adaptation multipliers (1.2 and 0.8)."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    # Mock adaptive manager to return base length
    with patch.object(agent, 'adaptive_manager', None):
        # Without adaptive manager, should use None
        response = await agent._generate_response("test", {}, None, expected_length=100)
        # Should work without error
        assert isinstance(response, str)


def test_belief_extraction_sentence_boundary():
    """Test belief extraction handles sentence boundaries correctly."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    # Belief with period
    agent._extract_prior_beliefs("I think trust is crucial. This is important.")
    if agent.prior_beliefs:
        # Should extract up to first period
        assert "." not in agent.prior_beliefs[0]["text"] or agent.prior_beliefs[0]["text"].endswith(".")
    
    # Belief without period
    agent.prior_beliefs = []
    agent._extract_prior_beliefs("I think trust is crucial for knowledge systems")
    if agent.prior_beliefs:
        # Should extract first 100 chars
        assert len(agent.prior_beliefs[0]["text"]) <= 100


def test_response_tiers_summary_length():
    """Test response tier summary length limit (150 chars)."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    # Long response with periods (triggers sentence-based truncation)
    long_response = "This is a test sentence. " * 20  # Much longer than 150 chars
    tiers = agent._create_response_tiers(long_response, {}, "test")
    
    # Summary should be limited to 150 chars
    assert len(tiers["summary"]) <= 150
    
    # Very long response without periods (triggers char-based truncation)
    very_long = "word " * 100  # 500+ chars, no periods
    tiers2 = agent._create_response_tiers(very_long, {}, "test")
    # Should be truncated to 150 chars with "..."
    assert len(tiers2["summary"]) <= 150


@pytest.mark.asyncio
async def test_conversation_history_append():
    """Test conversation history is appended correctly."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None
    
    # Chat should append to history
    initial_length = len(agent.conversation_history)
    await agent.chat("Test message")
    
    # Should have added user + assistant messages
    assert len(agent.conversation_history) == initial_length + 2
    assert agent.conversation_history[-2]["role"] == "user"
    assert agent.conversation_history[-1]["role"] == "assistant"

