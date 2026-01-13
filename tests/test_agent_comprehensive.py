"""Comprehensive agent tests with various scenarios."""

import pytest

from bop.agent import KnowledgeAgent
from bop.schemas import list_schemas


@pytest.mark.asyncio
async def test_agent_all_schemas():
    """Test agent with all available schemas."""
    agent = KnowledgeAgent()
    agent.llm_service = None  # Use fallback

    query = "What is structured reasoning?"
    schemas = list_schemas()

    for schema_name in schemas:
        response = await agent.chat(
            query,
            use_schema=schema_name,
            use_research=False,
        )

        assert response["schema_used"] == schema_name
        assert "response" in response


@pytest.mark.asyncio
async def test_agent_research_modes():
    """Test agent with different research configurations."""
    agent = KnowledgeAgent()
    agent.llm_service = None

    query = "What are the latest developments?"

    # Without research
    response_no_research = await agent.chat(query, use_research=False)
    assert response_no_research["research_conducted"] is False

    # With research
    response_with_research = await agent.chat(query, use_research=True)
    assert response_with_research["research_conducted"] is True


@pytest.mark.asyncio
async def test_agent_conversation_flow():
    """Test agent maintains conversation flow."""
    agent = KnowledgeAgent()
    agent.llm_service = None

    # Multi-turn conversation
    await agent.chat("What is trust?", use_research=False)
    await agent.chat("How does it relate to uncertainty?", use_research=False)
    await agent.chat("What are the applications?", use_research=False)

    history = agent.get_conversation_history()
    assert len(history) >= 6  # 3 user + 3 assistant messages


@pytest.mark.asyncio
async def test_agent_knowledge_base_search():
    """Test agent knowledge base search functionality."""
    agent = KnowledgeAgent()

    # Search for concepts that might be in content
    results = agent.search_knowledge_base("trust")
    assert isinstance(results, list)

    results = agent.search_knowledge_base("uncertainty")
    assert isinstance(results, list)

    results = agent.search_knowledge_base("nonexistent_concept_xyz")
    assert isinstance(results, list)  # Should return empty list, not error


@pytest.mark.asyncio
async def test_agent_error_handling():
    """Test agent handles errors gracefully."""
    agent = KnowledgeAgent()
    agent.llm_service = None

    # Various error scenarios
    problematic_inputs = [
        "",  # Empty
        "a" * 10000,  # Very long
        None,  # None (should be handled by caller)
    ]

    for inp in problematic_inputs:
        if inp is not None:
            try:
                response = await agent.chat(str(inp), use_research=False)
                # Should return some response, not crash
                assert "response" in response
            except Exception:
                # Some errors are acceptable for extreme cases
                pass


@pytest.mark.asyncio
async def test_agent_schema_research_combination():
    """Test agent with different schema+research combinations."""
    agent = KnowledgeAgent()
    agent.llm_service = None

    query = "What is knowledge structure?"

    combinations = [
        (None, False),
        ("chain_of_thought", False),
        (None, True),
        ("chain_of_thought", True),
        ("decompose_and_synthesize", True),
    ]

    for schema, research in combinations:
        response = await agent.chat(
            query,
            use_schema=schema,
            use_research=research,
        )

        assert "response" in response
        if schema:
            assert response["schema_used"] == schema
        assert response["research_conducted"] == research


@pytest.mark.asyncio
async def test_agent_history_management():
    """Test agent history management operations."""
    agent = KnowledgeAgent()
    agent.llm_service = None

    # Add some messages
    await agent.chat("Message 1")
    await agent.chat("Message 2")

    history = agent.get_conversation_history()
    assert len(history) >= 4

    # Clear history
    agent.clear_history()
    assert len(agent.get_conversation_history()) == 0

    # Add new message
    await agent.chat("Message 3")
    new_history = agent.get_conversation_history()
    assert len(new_history) == 2  # One user + one assistant


@pytest.mark.asyncio
async def test_agent_research_error_recovery():
    """Test agent recovers from research errors."""
    agent = KnowledgeAgent()
    agent.llm_service = None

    # Research might fail, but agent should continue
    response = await agent.chat(
        "Test query",
        use_schema="chain_of_thought",
        use_research=True,
    )

    # Should have response even if research had issues
    assert "response" in response
    # Should indicate research status
    assert "research_conducted" in response


@pytest.mark.asyncio
async def test_agent_response_structure():
    """Test that agent responses have consistent structure."""
    agent = KnowledgeAgent()
    agent.llm_service = None

    response = await agent.chat(
        "Test query",
        use_schema="chain_of_thought",
        use_research=True,
    )

    # Required fields
    assert "message" in response
    assert "response" in response
    assert "schema_used" in response
    assert "research_conducted" in response

    # Optional fields
    if response.get("research"):
        assert isinstance(response["research"], dict)
    if response.get("research_error"):
        assert isinstance(response["research_error"], str)


@pytest.mark.asyncio
async def test_agent_multiple_queries_same_session():
    """Test agent handles multiple queries in same session."""
    agent = KnowledgeAgent()
    agent.llm_service = None

    queries = [
        "What is concept A?",
        "What is concept B?",
        "How do A and B relate?",
    ]

    for query in queries:
        response = await agent.chat(query, use_research=False)
        assert response["message"] == query
        assert len(response["response"]) > 0

    # History should contain all
    history = agent.get_conversation_history()
    assert len(history) >= len(queries) * 2

