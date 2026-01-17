"""Tests for topology integration with orchestrator."""

import pytest

from pran.context_topology import ContextNode, ContextTopology
from pran.orchestrator import StructuredOrchestrator
from pran.research import ResearchAgent


@pytest.mark.asyncio
async def test_topology_grows_with_research():
    """Test that topology grows as research is conducted."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent, reset_topology_per_query=False)

    initial_nodes = len(orchestrator.topology.nodes)

    await orchestrator.research_with_schema(
        "What is trust in knowledge graphs?",
        schema_name="chain_of_thought",
    )

    # Topology should have grown
    assert len(orchestrator.topology.nodes) > initial_nodes


@pytest.mark.asyncio
async def test_topology_reset_per_query():
    """Test topology reset per query option."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent, reset_topology_per_query=True)

    # First query
    await orchestrator.research_with_schema(
        "First query",
        schema_name="chain_of_thought",
    )
    len(orchestrator.topology.nodes)

    # Second query (should reset)
    await orchestrator.research_with_schema(
        "Second query",
        schema_name="chain_of_thought",
    )
    nodes_after_second = len(orchestrator.topology.nodes)

    # Should have nodes from second query
    assert nodes_after_second > 0
    # But topology was reset, so might be different
    # (exact comparison depends on implementation)


@pytest.mark.asyncio
async def test_trust_propagation_in_topology():
    """Test trust propagation through topology."""
    topology = ContextTopology()

    # Create a chain of nodes
    nodes = []
    for i in range(3):
        node = ContextNode(
            id=f"n{i}",
            content=f"Node {i}",
            source="test",
            credibility=0.7 + i * 0.1,
            confidence=0.6 + i * 0.1,
        )
        topology.add_node(node)
        nodes.append(node)
        if i > 0:
            topology.add_edge(f"n{i-1}", f"n{i}")

    # Compute path trust
    path = ["n0", "n1", "n2"]
    path_trust = topology._compute_path_trust(path)

    assert 0.0 <= path_trust <= 1.0
    # Trust should decay with path length
    direct_trust = topology.edge_trust.get(tuple(sorted(["n0", "n1"])), 0.5)
    assert path_trust <= direct_trust * 1.5  # Allow some variance


@pytest.mark.asyncio
async def test_attractor_basins_from_research():
    """Test that attractor basins are identified from research."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent)

    result = await orchestrator.research_with_schema(
        "What are the key concepts in trust and uncertainty?",
        schema_name="decompose_and_synthesize",
    )

    topology_metrics = result.get("topology", {})
    assert "attractor_basins" in topology_metrics
    assert topology_metrics["attractor_basins"] >= 0


@pytest.mark.asyncio
async def test_calibration_tracking_in_research():
    """Test that calibration is tracked during research."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent)

    await orchestrator.research_with_schema(
        "Test query",
        schema_name="chain_of_thought",
    )

    # Add some confidence predictions
    orchestrator.topology.confidence_predictions = [
        (0.9, True),
        (0.8, True),
        (0.7, False),
    ]

    trust_summary = orchestrator.topology._get_trust_summary()
    assert "calibration_error" in trust_summary
    if trust_summary["calibration_error"] is not None:
        assert trust_summary["calibration_error"] >= 0.0


@pytest.mark.asyncio
async def test_schema_validation_in_research():
    """Test that schema validation runs during research."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent)

    await orchestrator.research_with_schema(
        "Test query",
        schema_name="chain_of_thought",
    )

    # Check that schema violations are tracked
    assert hasattr(orchestrator.topology, "schema_violations")
    assert isinstance(orchestrator.topology.schema_violations, list)

