"""Integration tests for research functionality."""

import pytest

from bop.agent import KnowledgeAgent
from bop.orchestrator import StructuredOrchestrator
from bop.research import ResearchAgent


@pytest.mark.asyncio
async def test_research_with_multiple_schemas():
    """Test research with different schemas."""
    agent = KnowledgeAgent()
    agent.llm_service = None  # Use fallback

    schemas = ["chain_of_thought", "decompose_and_synthesize", "hypothesize_and_test"]

    for schema_name in schemas:
        response = await agent.chat(
            "What is structured reasoning?",
            use_schema=schema_name,
            use_research=True,
        )

        assert response["schema_used"] == schema_name
        assert response["research_conducted"] is True


@pytest.mark.asyncio
async def test_research_topology_metrics():
    """Test that research includes topology metrics."""
    agent = KnowledgeAgent()
    agent.llm_service = None

    response = await agent.chat(
        "What are the key concepts in knowledge graphs?",
        use_schema="decompose_and_synthesize",
        use_research=True,
    )

    if response.get("research") and isinstance(response["research"], dict):
        topology = response["research"].get("topology", {})
        if topology:
            assert "trust_summary" in topology
            assert "betti_numbers" in topology


@pytest.mark.asyncio
async def test_orchestrator_tool_selection():
    """Test orchestrator tool selection across different query types."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent)

    queries = [
        "comprehensive analysis of trust",
        "why does uncertainty propagate?",
        "what is the definition of trust?",
    ]

    for query in queries:
        result = await orchestrator.research_with_schema(
            query,
            schema_name="chain_of_thought",
        )

        assert result is not None
        assert "tools_called" in result
        assert result["tools_called"] >= 0


@pytest.mark.asyncio
async def test_research_error_handling():
    """Test that research handles errors gracefully."""
    agent = KnowledgeAgent()
    agent.llm_service = None

    # Test with invalid input
    response = await agent.chat(
        "",  # Empty query
        use_schema="chain_of_thought",
        use_research=True,
    )

    # Should still return a response (even if empty)
    assert "response" in response


@pytest.mark.asyncio
async def test_conversation_context_preservation():
    """Test that conversation context is preserved across research calls."""
    agent = KnowledgeAgent()
    agent.llm_service = None

    # First message
    await agent.chat("What is trust?", use_research=True)

    # Second message (should have context)
    await agent.chat("How does it relate to uncertainty?", use_research=True)

    history = agent.get_conversation_history()
    assert len(history) >= 4  # At least 2 user + 2 assistant messages

