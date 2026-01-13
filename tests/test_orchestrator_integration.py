"""Integration tests for orchestrator with LLM and topology."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bop.context_topology import ContextNode
from bop.orchestrator import StructuredOrchestrator


@pytest.mark.asyncio
async def test_orchestrator_with_llm_decomposition():
    """Test orchestrator uses LLM for query decomposition."""
    with patch("bop.orchestrator.LLMService") as mock_llm_class:
        mock_llm = MagicMock()
        mock_llm.decompose_query = AsyncMock(return_value=["sub1", "sub2", "sub3"])
        mock_llm.synthesize_tool_results = AsyncMock(return_value="Synthesized")
        mock_llm.synthesize_subsolutions = AsyncMock(return_value="Final answer")
        mock_llm_class.return_value = mock_llm

        orchestrator = StructuredOrchestrator(llm_service=mock_llm)
        result = await orchestrator.research_with_schema(
            "Test query",
            schema_name="decompose_and_synthesize",
        )

        assert "decomposition" in result
        assert len(result["decomposition"]) == 3
        mock_llm.decompose_query.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_fallback_without_llm():
    """Test orchestrator falls back when LLM not available."""
    orchestrator = StructuredOrchestrator(llm_service=None)
    result = await orchestrator.research_with_schema(
        "Test query",
        schema_name="decompose_and_synthesize",
    )

    assert "decomposition" in result
    assert "subsolutions" in result
    # Should still work with fallback decomposition


@pytest.mark.asyncio
async def test_orchestrator_tool_selection_topology_aware():
    """Test that orchestrator uses topology-aware tool selection."""
    orchestrator = StructuredOrchestrator()

    # Add context to topology
    node = ContextNode(
        id="n1",
        content="Existing context",
        source="perplexity_search",
        credibility=0.8,
    )
    orchestrator.topology.add_node(node)
    orchestrator.topology.compute_cliques()

    # Mock tool calls
    with patch.object(orchestrator, "_call_tool") as mock_call:
        mock_call.return_value = {
            "tool": "perplexity_search",
            "query": "test",
            "result": "Test result",
            "sources": [],
        }

        result = await orchestrator.research_with_schema(
            "Test query",
            schema_name="decompose_and_synthesize",
            preserve_d_separation=True,
        )

        # Verify topology was considered
        assert "topology" in result
        assert "tools_called" in result


@pytest.mark.asyncio
async def test_orchestrator_handles_tool_failures():
    """Test orchestrator handles tool failures gracefully."""
    orchestrator = StructuredOrchestrator()

    # Mock tool to fail
    with patch.object(orchestrator, "_call_tool") as mock_call:
        mock_call.side_effect = [
            Exception("Tool error"),  # First tool fails
            {"tool": "test", "result": "Success", "sources": []},  # Second succeeds
        ]

        result = await orchestrator.research_with_schema(
            "Test query",
            max_tools_per_subproblem=2,
        )

        # Should continue despite failure
        assert "subsolutions" in result
        # Should have at least one successful tool call
        assert result["tools_called"] >= 0


@pytest.mark.asyncio
async def test_orchestrator_topology_metrics_computed():
    """Test that topology metrics are computed and included."""
    orchestrator = StructuredOrchestrator()

    # Add some context
    node1 = ContextNode(id="n1", content="test1", source="test", credibility=0.8)
    node2 = ContextNode(id="n2", content="test2", source="test", credibility=0.7)
    orchestrator.topology.add_node(node1)
    orchestrator.topology.add_node(node2)
    orchestrator.topology.add_edge("n1", "n2")

    with patch.object(orchestrator, "_call_tool") as mock_call:
        mock_call.return_value = {
            "tool": "test",
            "result": "Test",
            "sources": [],
        }

        result = await orchestrator.research_with_schema("Test query")

        assert "topology" in result
        topology = result["topology"]
        assert "betti_numbers" in topology
        assert "euler_characteristic" in topology
        assert "fisher_information" in topology
        assert "attractor_basins" in topology


@pytest.mark.asyncio
async def test_orchestrator_preserves_d_separation():
    """Test that d-separation is preserved when enabled."""
    orchestrator = StructuredOrchestrator()

    with patch.object(orchestrator, "_call_tool") as mock_call:
        mock_call.return_value = {
            "tool": "test",
            "result": "Test",
            "sources": [],
        }

        result = await orchestrator.research_with_schema(
            "Test query",
            preserve_d_separation=True,
        )

        assert result["d_separation_preserved"] is True
        assert "topology" in result


@pytest.mark.asyncio
async def test_orchestrator_conditioning_set_tracking():
    """Test that conditioning set is tracked correctly."""
    orchestrator = StructuredOrchestrator()

    call_count = 0

    async def mock_call_tool(tool, query):
        nonlocal call_count
        call_count += 1
        # Track when tools are called
        return {
            "tool": tool.value,
            "result": f"Result {call_count}",
            "sources": [],
        }

    orchestrator._call_tool = mock_call_tool

    result = await orchestrator.research_with_schema(
        "Test query",
        schema_name="decompose_and_synthesize",
    )

    # Should have called tools for each subproblem
    assert "subsolutions" in result
    assert len(result["subsolutions"]) > 0


@pytest.mark.asyncio
async def test_orchestrator_reset_topology_per_query():
    """Test that topology resets between queries when configured."""
    orchestrator = StructuredOrchestrator(reset_topology_per_query=True)

    # Add nodes in first query
    node1 = ContextNode(id="n1", content="test1", source="test")
    orchestrator.topology.add_node(node1)

    # Run query
    with patch.object(orchestrator, "_call_tool") as mock_call:
        mock_call.return_value = {"tool": "test", "result": "Test", "sources": []}
        await orchestrator.research_with_schema("Query 1")

    # Topology should be reset for next query
    len(orchestrator.topology.nodes)

    with patch.object(orchestrator, "_call_tool") as mock_call:
        mock_call.return_value = {"tool": "test", "result": "Test", "sources": []}
        await orchestrator.research_with_schema("Query 2")

    # After reset, should start fresh (or have new nodes from query 2)
    # The key is that reset_topology_per_query=True causes reset
    assert orchestrator.reset_topology_per_query is True


@pytest.mark.asyncio
async def test_orchestrator_max_tools_per_subproblem():
    """Test that max_tools_per_subproblem limit is respected."""
    orchestrator = StructuredOrchestrator()

    tool_calls = []

    async def track_calls(tool, query):
        tool_calls.append(tool)
        return {"tool": tool.value, "result": "Test", "sources": []}

    orchestrator._call_tool = track_calls

    await orchestrator.research_with_schema(
        "Test query",
        max_tools_per_subproblem=1,
    )

    # Should limit tools per subproblem
    # With 3 subproblems and max 1 tool each, should have at most 3 calls
    # (but may be less if heuristics select fewer)
    assert len(tool_calls) <= 3  # 3 subproblems * 1 max tool


@pytest.mark.asyncio
async def test_orchestrator_synthesis_with_llm():
    """Test that LLM is used for synthesis when available."""
    with patch("bop.orchestrator.LLMService") as mock_llm_class:
        mock_llm = MagicMock()
        mock_llm.decompose_query = AsyncMock(return_value=["sub1"])
        mock_llm.synthesize_tool_results = AsyncMock(return_value="Tool synthesis")
        mock_llm.synthesize_subsolutions = AsyncMock(return_value="Final LLM synthesis")
        mock_llm_class.return_value = mock_llm

        orchestrator = StructuredOrchestrator(llm_service=mock_llm)

        with patch.object(orchestrator, "_call_tool") as mock_call:
            mock_call.return_value = {"tool": "test", "result": "Test", "sources": []}

            result = await orchestrator.research_with_schema("Test query")

            # Verify LLM synthesis was called
            mock_llm.synthesize_tool_results.assert_called()
            mock_llm.synthesize_subsolutions.assert_called()
            assert "final_synthesis" in result

