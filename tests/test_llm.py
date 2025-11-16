"""Tests for LLM service integration."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

pytestmark = pytest.mark.asyncio

from bop.llm import LLMService
from bop.schemas import CHAIN_OF_THOUGHT


async def test_llm_service_initialization():
    """Test LLM service initialization."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        with patch("bop.llm.OpenAIChatModel") as mock_model:
            with patch("bop.llm.Agent") as mock_agent:
                service = LLMService(backend="openai")
                assert service is not None
                assert service.model is not None


async def test_llm_service_missing_api_key():
    """Test LLM service fails gracefully without API key."""
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            LLMService(backend="openai")


async def test_generate_response():
    """Test response generation."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        with patch("bop.llm.OpenAIChatModel"):
            with patch("bop.llm.Agent") as mock_agent_class:
                mock_agent = AsyncMock()
                mock_result = MagicMock()
                mock_result.data = "Test response"
                mock_agent.run = AsyncMock(return_value=mock_result)
                mock_agent_class.return_value = mock_agent

                service = LLMService(backend="openai")
                response = await service.generate_response("Test message")

                assert response == "Test response"
                mock_agent.run.assert_called_once()


async def test_hydrate_schema():
    """Test schema hydration."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        with patch("bop.llm.OpenAIChatModel"):
            with patch("bop.llm.Agent") as mock_agent_class:
                mock_agent = AsyncMock()
                mock_result = MagicMock()
                mock_result.data = {"input_analysis": "test", "steps": ["step1"]}
                mock_agent.run = AsyncMock(return_value=mock_result)
                mock_agent_class.return_value = mock_agent

                service = LLMService(backend="openai")
                hydrated = await service.hydrate_schema(CHAIN_OF_THOUGHT, "Test input")

                assert isinstance(hydrated, dict)
                assert "input_analysis" in hydrated


async def test_decompose_query():
    """Test query decomposition."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        with patch("bop.llm.OpenAIChatModel"):
            with patch("bop.llm.Agent") as mock_agent_class:
                mock_agent = AsyncMock()
                mock_result = MagicMock()
                mock_result.data = ["subproblem1", "subproblem2"]
                mock_agent.run = AsyncMock(return_value=mock_result)
                mock_agent_class.return_value = mock_agent

                service = LLMService(backend="openai")
                from bop.schemas import DECOMPOSE_AND_SYNTHESIZE

                decomposition = await service.decompose_query("Test query", DECOMPOSE_AND_SYNTHESIZE)

                assert isinstance(decomposition, list)
                assert len(decomposition) > 0


async def test_synthesize_tool_results():
    """Test tool result synthesis."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        with patch("bop.llm.OpenAIChatModel"):
            with patch("bop.llm.Agent") as mock_agent_class:
                mock_agent = AsyncMock()
                mock_result = MagicMock()
                mock_result.data = "Synthesized result"
                mock_agent.run = AsyncMock(return_value=mock_result)
                mock_agent_class.return_value = mock_agent

                service = LLMService(backend="openai")
                tool_results = [
                    {"tool": "test", "result": "Result 1"},
                    {"tool": "test2", "result": "Result 2"},
                ]

                synthesis = await service.synthesize_tool_results(tool_results, "Test subproblem")

                assert isinstance(synthesis, str)
                assert len(synthesis) > 0

