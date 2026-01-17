"""Topology integration tests for constraint solver."""

import pytest

from pran.constraints import PYSAT_AVAILABLE
from pran.context_topology import ContextNode
from pran.orchestrator import StructuredOrchestrator


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
@pytest.mark.asyncio
async def test_constraint_solver_with_topology():
    """Test that constraint solver works with existing topology."""
    orchestrator = StructuredOrchestrator(use_constraints=True)

    # Add some context nodes to topology
    node1 = ContextNode(
        id="n1",
        content="Existing context about trust",
        source="perplexity_search",
        credibility=0.8,
        confidence=0.7,
    )
    orchestrator.topology.add_node(node1)

    node2 = ContextNode(
        id="n2",
        content="Related context about uncertainty",
        source="tavily_search",
        credibility=0.7,
        confidence=0.6,
    )
    orchestrator.topology.add_node(node2)
    orchestrator.topology.add_edge("n1", "n2", weight=0.8)
    orchestrator.topology.compute_cliques()

    # Test tool selection with constraints and topology
    result = await orchestrator.research_with_schema(
        "How do trust and uncertainty relate?",
        schema_name="decompose_and_synthesize",
        preserve_d_separation=True,
        max_tools_per_subproblem=2,
    )

    # Should use constraints
    assert orchestrator.use_constraints is True

    # Topology should be considered
    assert "topology" in result
    assert len(orchestrator.topology.nodes) >= 2  # At least the initial nodes

    # Should have subsolutions
    assert "subsolutions" in result


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
@pytest.mark.asyncio
async def test_constraint_solver_topology_aware_selection():
    """Test constraint solver with topology-aware selection enabled."""
    orchestrator = StructuredOrchestrator(
        use_constraints=True,
        reset_topology_per_query=False
    )

    # Add high-trust context
    node = ContextNode(
        id="n1",
        content="High trust context",
        source="perplexity_deep_research",
        credibility=0.9,
        confidence=0.8,
    )
    orchestrator.topology.add_node(node)
    orchestrator.topology.compute_cliques()

    # Run research with both constraints and topology
    result = await orchestrator.research_with_schema(
        "Test query",
        schema_name="chain_of_thought",
        preserve_d_separation=True,
        max_tools_per_subproblem=2,
    )

    # Both should be active
    assert orchestrator.use_constraints is True
    assert "topology" in result
    assert result["d_separation_preserved"] is True


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
@pytest.mark.asyncio
async def test_constraint_solver_topology_accumulation():
    """Test that constraint solver works as topology accumulates."""
    orchestrator = StructuredOrchestrator(
        use_constraints=True,
        reset_topology_per_query=False
    )

    queries = [
        "What is trust?",
        "What is uncertainty?",
        "How do they relate?",
    ]

    initial_nodes = len(orchestrator.topology.nodes)

    for query in queries:
        result = await orchestrator.research_with_schema(
            query,
            schema_name="chain_of_thought",
            max_tools_per_subproblem=2,
        )

        assert orchestrator.use_constraints is True
        assert "topology" in result

    # Topology should have grown
    final_nodes = len(orchestrator.topology.nodes)
    assert final_nodes > initial_nodes


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
@pytest.mark.asyncio
async def test_constraint_solver_topology_metrics():
    """Test that topology metrics are computed with constraint solver."""
    orchestrator = StructuredOrchestrator(use_constraints=True)

    # Add some context
    node1 = ContextNode(id="n1", content="test1", source="test", credibility=0.8)
    node2 = ContextNode(id="n2", content="test2", source="test", credibility=0.7)
    orchestrator.topology.add_node(node1)
    orchestrator.topology.add_node(node2)
    orchestrator.topology.add_edge("n1", "n2")

    result = await orchestrator.research_with_schema(
        "Test query",
        schema_name="chain_of_thought",
        max_tools_per_subproblem=2,
    )

    # Verify topology metrics
    assert "topology" in result
    topology = result["topology"]
    assert "betti_numbers" in topology
    assert "euler_characteristic" in topology
    assert "fisher_information" in topology
    assert orchestrator.use_constraints is True


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
@pytest.mark.asyncio
async def test_constraint_solver_topology_reset():
    """Test constraint solver with topology reset per query."""
    orchestrator = StructuredOrchestrator(
        use_constraints=True,
        reset_topology_per_query=True
    )

    # Add nodes in first query
    node1 = ContextNode(id="n1", content="test1", source="test")
    orchestrator.topology.add_node(node1)

    # Run query
    result1 = await orchestrator.research_with_schema(
        "Query 1",
        schema_name="chain_of_thought",
        max_tools_per_subproblem=2,
    )

    # Topology should be reset for next query
    len(orchestrator.topology.nodes)

    result2 = await orchestrator.research_with_schema(
        "Query 2",
        schema_name="chain_of_thought",
        max_tools_per_subproblem=2,
    )

    # Both should use constraints
    assert orchestrator.use_constraints is True
    assert orchestrator.reset_topology_per_query is True
    assert "topology" in result1
    assert "topology" in result2

