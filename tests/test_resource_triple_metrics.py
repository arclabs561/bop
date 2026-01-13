"""Tests for resource triple and degradation triple metrics."""

import pytest

from bop.orchestrator import StructuredOrchestrator
from bop.research import ResearchAgent


@pytest.mark.asyncio
async def test_resource_triple_tracking():
    """Test that resource triple metrics are tracked."""
    orchestrator = StructuredOrchestrator(
        research_agent=ResearchAgent(use_mcp=False),
    )

    # Mock a simple research result
    result = await orchestrator.research_with_schema(
        "What is d-separation?",
        schema_name="decompose_and_synthesize",
    )

    assert "resource_triple" in result
    assert "depth" in result["resource_triple"]
    assert "width" in result["resource_triple"]
    assert "coordination" in result["resource_triple"]
    assert "total_tokens" in result["resource_triple"]

    # Verify metrics are non-negative
    assert result["resource_triple"]["depth"] >= 0
    assert result["resource_triple"]["width"] >= 0
    assert result["resource_triple"]["coordination"] >= 0
    assert result["resource_triple"]["total_tokens"] >= 0


@pytest.mark.asyncio
async def test_degradation_triple_tracking():
    """Test that degradation triple metrics are tracked."""
    orchestrator = StructuredOrchestrator(
        research_agent=ResearchAgent(use_mcp=False),
    )

    result = await orchestrator.research_with_schema(
        "What is d-separation?",
        schema_name="decompose_and_synthesize",
    )

    assert "degradation_triple" in result
    assert "noise" in result["degradation_triple"]
    assert "loss" in result["degradation_triple"]
    assert "waste" in result["degradation_triple"]

    # Verify metrics are in valid range [0, 1]
    assert 0.0 <= result["degradation_triple"]["noise"] <= 1.0
    assert 0.0 <= result["degradation_triple"]["loss"] <= 1.0
    assert 0.0 <= result["degradation_triple"]["waste"] <= 1.0


@pytest.mark.asyncio
async def test_resource_triple_depth_matches_subsolutions():
    """Test that resource triple depth matches number of subsolutions."""
    orchestrator = StructuredOrchestrator(
        research_agent=ResearchAgent(use_mcp=False),
    )

    result = await orchestrator.research_with_schema(
        "What is d-separation?",
        schema_name="decompose_and_synthesize",
    )

    num_subsolutions = len(result.get("subsolutions", []))
    depth = result["resource_triple"]["depth"]

    assert depth == num_subsolutions


@pytest.mark.asyncio
async def test_resource_triple_width_matches_tools():
    """Test that resource triple width matches total tools used."""
    orchestrator = StructuredOrchestrator(
        research_agent=ResearchAgent(use_mcp=False),
    )

    result = await orchestrator.research_with_schema(
        "What is d-separation?",
        schema_name="decompose_and_synthesize",
    )

    tools_called = result.get("tools_called", 0)
    width = result["resource_triple"]["width"]

    assert width == tools_called


@pytest.mark.asyncio
async def test_logical_depth_in_topology():
    """Test that logical depth is computed and included in topology."""
    orchestrator = StructuredOrchestrator(
        research_agent=ResearchAgent(use_mcp=False),
    )

    result = await orchestrator.research_with_schema(
        "What is d-separation?",
        schema_name="decompose_and_synthesize",
    )

    topology = result.get("topology", {})
    assert "logical_depths" in topology
    assert "avg_logical_depth" in topology

    # Verify logical depths are in valid range
    logical_depths = topology["logical_depths"]
    if logical_depths:
        for node_id, depth in logical_depths.items():
            assert 0.0 <= depth <= 1.0

    avg_depth = topology["avg_logical_depth"]
    assert 0.0 <= avg_depth <= 1.0

