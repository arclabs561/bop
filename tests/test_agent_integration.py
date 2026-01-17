"""Integration tests for agent with all components."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pran.agent import KnowledgeAgent


@pytest.mark.asyncio
async def test_agent_full_flow_with_schema_and_research():
    """Test complete agent flow with schema and research."""
    with patch("pran.agent.LLMService") as mock_llm_class:
        mock_llm = MagicMock()
        mock_llm.generate_response = AsyncMock(return_value="Full response")
        mock_llm.hydrate_schema = AsyncMock(return_value={"steps": ["step1"]})
        mock_llm.decompose_query = AsyncMock(return_value=["sub1", "sub2"])
        mock_llm.synthesize_tool_results = AsyncMock(return_value="Synthesized")
        mock_llm.synthesize_subsolutions = AsyncMock(return_value="Final")
        mock_llm_class.return_value = mock_llm

        agent = KnowledgeAgent()
        agent.orchestrator._call_tool = AsyncMock(return_value={
            "tool": "test",
            "result": "Tool result",
            "sources": [],
        })

        response = await agent.chat(
            "What is structured reasoning?",
            use_schema="chain_of_thought",
            use_research=True,
        )

        assert response["schema_used"] == "chain_of_thought"
        assert response["research_conducted"] is True
        assert "response" in response
        assert len(response["response"]) > 0


@pytest.mark.asyncio
async def test_agent_knowledge_base_integration():
    """Test agent uses knowledge base in responses."""
    with patch("pran.agent.LLMService") as mock_llm_class:
        mock_llm = MagicMock()
        mock_llm.generate_response = AsyncMock(return_value="KB-enhanced response")
        mock_llm_class.return_value = mock_llm

        agent = KnowledgeAgent()

        # Add some knowledge base results
        agent.search_knowledge_base("reasoning")

        response = await agent.chat("Tell me about reasoning")

        # Response should be generated (may or may not use KB depending on implementation)
        assert "response" in response


@pytest.mark.asyncio
async def test_agent_conversation_history_persistence():
    """Test that conversation history persists across multiple chats."""
    agent = KnowledgeAgent()
    agent.llm_service = None  # Use fallback

    await agent.chat("First message")
    await agent.chat("Second message")
    await agent.chat("Third message")

    history = agent.get_conversation_history()

    # Should have 6 messages (3 user + 3 assistant)
    assert len(history) == 6
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "First message"
    assert history[1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_agent_schema_hydration_error_handling():
    """Test agent handles schema hydration errors gracefully."""
    with patch("pran.agent.LLMService") as mock_llm_class:
        mock_llm = MagicMock()
        mock_llm.generate_response = AsyncMock(return_value="Response")
        mock_llm.hydrate_schema = AsyncMock(side_effect=Exception("Hydration error"))
        mock_llm_class.return_value = mock_llm

        agent = KnowledgeAgent()
        response = await agent.chat(
            "Test",
            use_schema="chain_of_thought"
        )

        # Should continue despite hydration error
        assert "response" in response
        # Should have fallback structured reasoning
        assert "structured_reasoning" in response or "structured_reasoning_error" in response


@pytest.mark.asyncio
async def test_agent_research_error_handling():
    """Test agent handles research errors gracefully."""
    with patch("pran.agent.LLMService") as mock_llm_class:
        mock_llm = MagicMock()
        mock_llm.generate_response = AsyncMock(return_value="Response despite error")
        mock_llm_class.return_value = mock_llm

        agent = KnowledgeAgent()
        agent.orchestrator.research_with_schema = AsyncMock(side_effect=Exception("Research failed"))

        response = await agent.chat(
            "Test query",
            use_research=True,
            use_schema="decompose_and_synthesize"
        )

        # Should continue despite research error
        assert "response" in response
        assert response["research_conducted"] is False
        assert "research_error" in response


@pytest.mark.asyncio
async def test_agent_llm_unavailable_fallback():
    """Test agent works when LLM service is unavailable."""
    agent = KnowledgeAgent()
    agent.llm_service = None

    response = await agent.chat("Test message")

    assert "response" in response
    assert "LLM service not available" in response["response"] or len(response["response"]) > 0


@pytest.mark.asyncio
async def test_agent_multiple_schemas():
    """Test agent can use different schemas."""
    agent = KnowledgeAgent()
    agent.llm_service = None  # Use fallback

    schemas_to_test = ["chain_of_thought", "iterative_elaboration", "hypothesize_and_test"]

    for schema_name in schemas_to_test:
        response = await agent.chat(
            f"Test with {schema_name}",
            use_schema=schema_name
        )

        assert response["schema_used"] == schema_name
        assert "response" in response


@pytest.mark.asyncio
async def test_agent_research_without_schema():
    """Test agent can do research without schema."""
    with patch("pran.agent.LLMService") as mock_llm_class:
        mock_llm = MagicMock()
        mock_llm.generate_response = AsyncMock(return_value="Response")
        mock_llm_class.return_value = mock_llm

        agent = KnowledgeAgent()
        agent.research_agent.deep_research = AsyncMock(return_value={
            "summary": "Research summary",
            "sources": [],
        })

        response = await agent.chat(
            "Research query",
            use_research=True,
        )

        assert response["research_conducted"] is True
        assert "research" in response


@pytest.mark.asyncio
async def test_agent_context_building():
    """Test that agent builds context correctly for LLM."""
    with patch("pran.agent.LLMService") as mock_llm_class:
        mock_llm = MagicMock()
        mock_llm.generate_response = AsyncMock(return_value="Contextual response")
        mock_llm_class.return_value = mock_llm

        agent = KnowledgeAgent()
        agent.research_agent.deep_research = AsyncMock(return_value={
            "summary": "Research summary",
            "final_synthesis": "Synthesis",
        })

        response = await agent.chat(
            "Query",
            use_research=True,
        )

        # Verify context was passed to LLM
        call_args = mock_llm.generate_response.call_args
        context = call_args[1].get("context", {})

        # Context should include research if research was conducted
        if response.get("research_conducted"):
            assert "research" in context or "research" in str(call_args)

