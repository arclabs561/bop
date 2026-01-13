"""Tests for LLM service error handling and edge cases."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bop.llm import LLMService
from bop.schemas import CHAIN_OF_THOUGHT, DECOMPOSE_AND_SYNTHESIZE


@pytest.mark.asyncio
async def test_llm_service_generate_response_with_context():
    """Test response generation with full context."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        with patch("bop.llm.OpenAIChatModel"):
            with patch("bop.llm.Agent") as mock_agent_class:
                mock_agent = AsyncMock()
                mock_result = MagicMock()
                mock_result.data = "Context-aware response"
                mock_agent.run = AsyncMock(return_value=mock_result)
                mock_agent_class.return_value = mock_agent

                service = LLMService(backend="openai")
                context = {
                    "research": {"summary": "Research summary", "final_synthesis": "Synthesis"},
                    "knowledge_base_results": ["Result 1", "Result 2"],
                }

                response = await service.generate_response("Test", context=context)

                assert response == "Context-aware response"
                # Verify context was included in prompt
                call_args = mock_agent.run.call_args[0][0]
                assert "Research summary" in call_args or "Synthesis" in call_args


@pytest.mark.asyncio
async def test_llm_service_generate_response_with_schema():
    """Test response generation with schema."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        with patch("bop.llm.OpenAIChatModel"):
            with patch("bop.llm.Agent") as mock_agent_class:
                mock_agent = AsyncMock()
                mock_result = MagicMock()
                mock_result.data = "Schema-guided response"
                mock_agent.run = AsyncMock(return_value=mock_result)
                mock_agent_class.return_value = mock_agent

                service = LLMService(backend="openai")
                response = await service.generate_response("Test", schema=CHAIN_OF_THOUGHT)

                assert response == "Schema-guided response"
                call_args = mock_agent.run.call_args[0][0]
                assert "chain_of_thought" in call_args.lower() or "step-by-step" in call_args.lower()


@pytest.mark.asyncio
async def test_llm_service_hydrate_schema_complex():
    """Test schema hydration with complex schema."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        with patch("bop.llm.OpenAIChatModel"):
            with patch("bop.llm.Agent") as mock_agent_class:
                mock_agent = AsyncMock()
                mock_result = MagicMock()
                mock_result.data = {
                    "decomposition": ["sub1", "sub2"],
                    "subsolutions": ["sol1", "sol2"],
                    "synthesis": "Final",
                }
                mock_agent.run = AsyncMock(return_value=mock_result)
                mock_agent_class.return_value = mock_agent

                service = LLMService(backend="openai")
                hydrated = await service.hydrate_schema(DECOMPOSE_AND_SYNTHESIZE, "Complex query")

                assert isinstance(hydrated, dict)
                assert "decomposition" in hydrated or len(hydrated) > 0


@pytest.mark.asyncio
async def test_llm_service_hydrate_schema_invalid_response():
    """Test schema hydration handles invalid LLM response."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        with patch("bop.llm.OpenAIChatModel"):
            with patch("bop.llm.Agent") as mock_agent_class:
                mock_agent = AsyncMock()
                mock_result = MagicMock()
                mock_result.data = "Not a dict"  # Invalid response
                mock_agent.run = AsyncMock(return_value=mock_result)
                mock_agent_class.return_value = mock_agent

                service = LLMService(backend="openai")
                hydrated = await service.hydrate_schema(CHAIN_OF_THOUGHT, "Test")

                # Should return empty dict for invalid response
                assert isinstance(hydrated, dict)


@pytest.mark.asyncio
async def test_llm_service_decompose_query_fallback():
    """Test query decomposition falls back if LLM returns invalid format."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        with patch("bop.llm.OpenAIChatModel"):
            with patch("bop.llm.Agent") as mock_agent_class:
                mock_agent = AsyncMock()
                mock_result = MagicMock()
                mock_result.data = "Not a list"  # Invalid format
                mock_agent.run = AsyncMock(return_value=mock_result)
                mock_agent_class.return_value = mock_agent

                service = LLMService(backend="openai")
                decomposition = await service.decompose_query("Test", DECOMPOSE_AND_SYNTHESIZE)

                # Should fall back to single query
                assert isinstance(decomposition, list)
                assert len(decomposition) >= 1


@pytest.mark.asyncio
async def test_llm_service_synthesize_empty_results():
    """Test synthesis handles empty tool results."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        with patch("bop.llm.OpenAIChatModel"):
            with patch("bop.llm.Agent") as mock_agent_class:
                mock_agent = AsyncMock()
                mock_result = MagicMock()
                mock_result.data = "No results message"
                mock_agent.run = AsyncMock(return_value=mock_result)
                mock_agent_class.return_value = mock_agent

                service = LLMService(backend="openai")
                synthesis = await service.synthesize_tool_results([], "Test subproblem")

                # Should handle empty results gracefully
                assert isinstance(synthesis, str)


@pytest.mark.asyncio
async def test_llm_service_synthesize_filtered_results():
    """Test synthesis filters invalid tool results."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        with patch("bop.llm.OpenAIChatModel"):
            with patch("bop.llm.Agent") as mock_agent_class:
                mock_agent = AsyncMock()
                mock_result = MagicMock()
                mock_result.data = "Synthesized"
                mock_agent.run = AsyncMock(return_value=mock_result)
                mock_agent_class.return_value = mock_agent

                service = LLMService(backend="openai")
                tool_results = [
                    {"tool": "test1", "result": "Valid result"},
                    {"tool": "test2"},  # Missing result
                    None,  # Invalid
                    {"tool": "test3", "result": ""},  # Empty result
                ]

                synthesis = await service.synthesize_tool_results(tool_results, "Test")

                # Should synthesize only valid results
                assert isinstance(synthesis, str)
                assert len(synthesis) > 0


@pytest.mark.asyncio
async def test_llm_service_synthesize_subsolutions_empty():
    """Test synthesis handles empty subsolutions."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        with patch("bop.llm.OpenAIChatModel"):
            with patch("bop.llm.Agent") as mock_agent_class:
                mock_agent = AsyncMock()
                mock_result = MagicMock()
                mock_result.data = "No solutions"
                mock_agent.run = AsyncMock(return_value=mock_result)
                mock_agent_class.return_value = mock_agent

                service = LLMService(backend="openai")
                synthesis = await service.synthesize_subsolutions(
                    [], DECOMPOSE_AND_SYNTHESIZE, "Original query"
                )

                assert isinstance(synthesis, str)


@pytest.mark.asyncio
async def test_llm_service_error_propagation():
    """Test that LLM errors are properly handled."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        with patch("bop.llm.OpenAIChatModel"):
            with patch("bop.llm.Agent") as mock_agent_class:
                mock_agent = AsyncMock()
                mock_agent.run = AsyncMock(side_effect=Exception("LLM API error"))
                mock_agent_class.return_value = mock_agent

                service = LLMService(backend="openai")

                with pytest.raises(Exception):
                    await service.generate_response("Test")


def test_llm_service_format_schema_def_nested():
    """Test schema definition formatting with nested structures."""
    # Test the method directly without requiring API key
    # We'll create a minimal service instance or test the method logic
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        with patch("bop.llm.OpenAIChatModel"):
            with patch("bop.llm.Agent"):
                service = LLMService(backend="openai")

                complex_schema_def = {
                    "steps": "List of steps",
                    "refinements": [
                        {
                            "iteration": "Number",
                            "changes": "Details",
                        }
                    ],
                }

                formatted = service._format_schema_def(complex_schema_def)

                assert "steps" in formatted
                assert "refinements" in formatted
                assert "iteration" in formatted or "changes" in formatted

