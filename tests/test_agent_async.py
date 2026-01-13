"""Tests for async agent functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = pytest.mark.asyncio

from bop.agent import KnowledgeAgent


async def test_agent_chat_async():
    """Test async chat functionality."""
    with patch("bop.agent.LLMService") as mock_llm_class:
        mock_llm = MagicMock()
        mock_llm.generate_response = AsyncMock(return_value="Test response")
        mock_llm.hydrate_schema = AsyncMock(return_value={})
        mock_llm_class.return_value = mock_llm

        agent = KnowledgeAgent()
        response = await agent.chat("Hello")

        assert "response" in response
        assert response["response"] == "Test response"
        assert response["message"] == "Hello"


async def test_agent_chat_with_schema():
    """Test chat with schema."""
    with patch("bop.agent.LLMService") as mock_llm_class:
        mock_llm = MagicMock()
        mock_llm.generate_response = AsyncMock(return_value="Schema response")
        mock_llm.hydrate_schema = AsyncMock(return_value={"steps": ["step1"]})
        mock_llm_class.return_value = mock_llm

        agent = KnowledgeAgent()
        response = await agent.chat("Solve 2x + 3 = 7", use_schema="chain_of_thought")

        assert response["schema_used"] == "chain_of_thought"
        assert "structured_reasoning" in response


async def test_agent_chat_with_research():
    """Test chat with research."""
    with patch("bop.agent.LLMService") as mock_llm_class:
        mock_llm = MagicMock()
        mock_llm.generate_response = AsyncMock(return_value="Research response")
        mock_llm_class.return_value = mock_llm

        agent = KnowledgeAgent()
        agent.orchestrator.research_with_schema = AsyncMock(
            return_value={"summary": "Research summary"}
        )

        response = await agent.chat(
            "What is structured reasoning?", use_research=True, use_schema="decompose_and_synthesize"
        )

        assert response["research_conducted"] is True
        assert "research" in response


async def test_agent_chat_no_llm():
    """Test chat without LLM service."""
    agent = KnowledgeAgent()
    agent.llm_service = None

    response = await agent.chat("Hello")

    assert "response" in response
    assert "LLM service not available" in response["response"]


async def test_agent_chat_error_handling():
    """Test error handling in chat."""
    with patch("bop.agent.LLMService") as mock_llm_class:
        mock_llm = MagicMock()
        mock_llm.generate_response = AsyncMock(side_effect=Exception("LLM error"))
        mock_llm_class.return_value = mock_llm

        agent = KnowledgeAgent()
        response = await agent.chat("Hello")

        assert "response" in response
        assert "LLM Error" in response["response"]

