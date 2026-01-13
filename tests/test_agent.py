"""Tests for knowledge agent."""


import pytest

from bop.agent import KnowledgeAgent


def test_agent_initialization():
    """Test agent initialization."""
    agent = KnowledgeAgent()
    assert agent is not None
    assert agent.research_agent is not None


@pytest.mark.asyncio
async def test_agent_chat():
    """Test basic chat functionality."""
    agent = KnowledgeAgent()
    agent.llm_service = None  # Use fallback
    response = await agent.chat("Hello")
    assert "response" in response
    assert response["message"] == "Hello"


@pytest.mark.asyncio
async def test_agent_with_schema():
    """Test chat with structured schema."""
    agent = KnowledgeAgent()
    agent.llm_service = None  # Use fallback
    response = await agent.chat("Solve 2x + 3 = 7", use_schema="chain_of_thought")
    assert response["schema_used"] == "chain_of_thought"


def test_search_knowledge_base():
    """Test searching knowledge base."""
    agent = KnowledgeAgent()
    # This will work if content files exist
    results = agent.search_knowledge_base("knowledge")
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_conversation_history():
    """Test conversation history tracking."""
    agent = KnowledgeAgent()
    agent.llm_service = None  # Use fallback
    await agent.chat("Hello")
    history = agent.get_conversation_history()
    assert len(history) == 2  # User message + assistant response


@pytest.mark.asyncio
async def test_clear_history():
    """Test clearing conversation history."""
    agent = KnowledgeAgent()
    agent.llm_service = None  # Use fallback
    await agent.chat("Hello")
    agent.clear_history()
    assert len(agent.get_conversation_history()) == 0

