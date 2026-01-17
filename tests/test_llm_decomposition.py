"""Tests for LLM-based query decomposition."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pran.llm import LLMService
from pran.schemas import get_schema


@pytest.mark.asyncio
async def test_decompose_query_decompose_and_synthesize():
    """Test decomposition for decompose_and_synthesize schema."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        with patch("pran.llm.OpenAIModel"):
            with patch("pran.llm.Agent"):
                service = LLMService()

                # Mock the agent to return structured subproblems
                with patch.object(service, 'agent') as mock_agent:
                    mock_result = MagicMock()
                    mock_result.data = [
                        "Theoretical foundation of trust and uncertainty",
                        "Recent empirical studies on trust",
                        "Alternative perspectives on uncertainty",
                        "Practical applications",
                    ]
                    mock_agent.run = AsyncMock(return_value=mock_result)

                    schema = get_schema("decompose_and_synthesize")
                    if not schema:
                        pytest.skip("decompose_and_synthesize schema not found")

                    result = await service.decompose_query(
                        "What is the relationship between trust and uncertainty?",
                        schema
                    )

                    assert isinstance(result, list)
                    assert len(result) > 0
                    assert all(isinstance(sub, str) for sub in result)


@pytest.mark.asyncio
async def test_decompose_query_other_schema():
    """Test decomposition for other schemas."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        with patch("pran.llm.OpenAIChatModel"):
            with patch("pran.llm.Agent"):
                service = LLMService(backend="openai")

                with patch.object(service, 'agent') as mock_agent:
                    mock_result = MagicMock()
                    mock_result.data = [
                        "Understanding the problem",
                        "Analyzing components",
                    ]
                    mock_agent.run = AsyncMock(return_value=mock_result)

                    schema = get_schema("chain_of_thought")
                    if not schema:
                        pytest.skip("chain_of_thought schema not found")

                    result = await service.decompose_query("Test query", schema)

                    assert isinstance(result, list)
                    assert len(result) > 0


@pytest.mark.asyncio
async def test_decompose_query_fallback():
    """Test that decomposition falls back if LLM fails."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        with patch("pran.llm.OpenAIChatModel"):
            with patch("pran.llm.Agent"):
                service = LLMService(backend="openai")

                # Mock agent to raise exception
                with patch.object(service, 'agent') as mock_agent:
                    mock_agent.run = AsyncMock(side_effect=Exception("LLM error"))

                    schema = get_schema("chain_of_thought")
                    if not schema:
                        pytest.skip("chain_of_thought schema not found")

                    result = await service.decompose_query("Test query", schema)

                    # Should fallback to single query
                    assert isinstance(result, list)
                    assert len(result) == 1
                    assert result[0] == "Test query"


@pytest.mark.asyncio
async def test_decompose_query_invalid_response():
    """Test handling of invalid LLM response."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        with patch("pran.llm.OpenAIChatModel"):
            with patch("pran.llm.Agent"):
                service = LLMService(backend="openai")

                with patch.object(service, 'agent') as mock_agent:
                    # Return non-list response
                    mock_result = MagicMock()
                    mock_result.data = "Not a list"
                    mock_agent.run = AsyncMock(return_value=mock_result)

                    schema = get_schema("chain_of_thought")
                    if not schema:
                        pytest.skip("chain_of_thought schema not found")

                    result = await service.decompose_query("Test query", schema)

                    # Should fallback
                    assert isinstance(result, list)
                    assert len(result) == 1


@pytest.mark.asyncio
async def test_decompose_query_empty_response():
    """Test handling of empty LLM response."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        with patch("pran.llm.OpenAIChatModel"):
            with patch("pran.llm.Agent"):
                service = LLMService(backend="openai")

                with patch.object(service, 'agent') as mock_agent:
                    mock_result = MagicMock()
                    mock_result.data = []
                    mock_agent.run = AsyncMock(return_value=mock_result)

                    schema = get_schema("chain_of_thought")
                    if not schema:
                        pytest.skip("chain_of_thought schema not found")

                    result = await service.decompose_query("Test query", schema)

                    # Should fallback
                    assert isinstance(result, list)
                    assert len(result) == 1


@pytest.mark.asyncio
async def test_decompose_query_without_llm_service():
    """Test orchestrator decomposition without LLM service."""
    from pran.orchestrator import StructuredOrchestrator
    from pran.schemas import get_schema

    orchestrator = StructuredOrchestrator()
    orchestrator.llm_service = None  # No LLM service

    schema = get_schema("decompose_and_synthesize")
    if not schema:
        pytest.skip("decompose_and_synthesize schema not found")

    result = await orchestrator._decompose_query(
        "Test query",
        schema
    )

    # Should use fallback
    assert isinstance(result, list)
    assert len(result) > 0
    # Should have heuristic subproblems for decompose_and_synthesize
    if schema.name == "decompose_and_synthesize":
        assert len(result) == 3


@pytest.mark.asyncio
async def test_decompose_query_with_llm_service():
    """Test orchestrator decomposition with LLM service."""
    from pran.orchestrator import StructuredOrchestrator
    from pran.schemas import get_schema

    orchestrator = StructuredOrchestrator()

    # Mock LLM service
    mock_llm = MagicMock()
    mock_llm.decompose_query = AsyncMock(return_value=[
        "Subproblem 1",
        "Subproblem 2",
        "Subproblem 3",
    ])
    orchestrator.llm_service = mock_llm

    schema = get_schema("decompose_and_synthesize")
    if not schema:
        pytest.skip("decompose_and_synthesize schema not found")

    result = await orchestrator._decompose_query(
        "Test query",
        schema
    )

    # Should use LLM decomposition
    assert isinstance(result, list)
    assert len(result) == 3
    assert result[0] == "Subproblem 1"
    mock_llm.decompose_query.assert_called_once()


@pytest.mark.asyncio
async def test_decompose_query_llm_error_fallback():
    """Test that orchestrator falls back when LLM decomposition fails."""
    from pran.orchestrator import StructuredOrchestrator
    from pran.schemas import get_schema

    orchestrator = StructuredOrchestrator()

    # Mock LLM service to raise error
    mock_llm = MagicMock()
    mock_llm.decompose_query = AsyncMock(side_effect=Exception("LLM error"))
    orchestrator.llm_service = mock_llm

    schema = get_schema("decompose_and_synthesize")
    if not schema:
        pytest.skip("decompose_and_synthesize schema not found")

    result = await orchestrator._decompose_query(
        "Test query",
        schema
    )

    # Should fallback to heuristics
    assert isinstance(result, list)
    assert len(result) > 0
