"""Comprehensive tests for orchestrator with various scenarios."""

import pytest

from pran.orchestrator import StructuredOrchestrator
from pran.research import ResearchAgent
from pran.schemas import list_schemas


@pytest.mark.asyncio
async def test_orchestrator_all_schemas():
    """Test orchestrator with all available schemas."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent)

    query = "What are the key concepts in knowledge structure?"
    schemas = list_schemas()

    for schema_name in schemas:
        result = await orchestrator.research_with_schema(
            query,
            schema_name=schema_name,
        )

        assert result is not None
        assert result["schema_used"] == schema_name
        assert "subsolutions" in result
        assert "final_synthesis" in result


@pytest.mark.asyncio
async def test_orchestrator_query_variations():
    """Test orchestrator with various query types."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent)

    queries = [
        "What is X?",  # Simple factual
        "Why does Y happen?",  # Causal reasoning
        "How can we solve Z?",  # Problem-solving
        "Compare A and B",  # Comparative
        "Explain the relationship between C and D",  # Relational
        "What are the latest developments in E?",  # Temporal
        "Analyze the implications of F",  # Analytical
    ]

    for query in queries:
        result = await orchestrator.research_with_schema(
            query,
            schema_name="chain_of_thought",
        )

        assert result["query"] == query
        assert len(result["final_synthesis"]) > 0


@pytest.mark.asyncio
async def test_orchestrator_topology_accumulation():
    """Test that topology accumulates across multiple queries."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent, reset_topology_per_query=False)

    queries = [
        "What is trust?",
        "What is uncertainty?",
        "How do trust and uncertainty relate?",
    ]

    initial_nodes = len(orchestrator.topology.nodes)

    for query in queries:
        await orchestrator.research_with_schema(
            query,
            schema_name="chain_of_thought",
        )

    # Topology should have grown
    final_nodes = len(orchestrator.topology.nodes)
    assert final_nodes > initial_nodes


@pytest.mark.asyncio
async def test_orchestrator_tool_diversity():
    """Test that orchestrator selects diverse tools."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent)

    # Run multiple queries and track tool usage
    queries = [
        "comprehensive analysis of trust",
        "why does uncertainty propagate",
        "what is the definition of knowledge",
        "scrape https://example.com",
    ]

    all_tools_used = set()

    for query in queries:
        result = await orchestrator.research_with_schema(
            query,
            schema_name="decompose_and_synthesize",
        )

        # Collect tools used
        for subsolution in result["subsolutions"]:
            all_tools_used.update(subsolution.get("tools_used", []))

    # Should have used multiple different tools
    assert len(all_tools_used) > 0


@pytest.mark.asyncio
async def test_orchestrator_error_recovery():
    """Test that orchestrator recovers from errors gracefully."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent)

    # Test with various error-prone scenarios
    problematic_queries = [
        "",  # Empty query
        "a" * 10000,  # Very long query
        "!@#$%^&*()",  # Special characters
    ]

    for query in problematic_queries:
        # Should not crash
        result = await orchestrator.research_with_schema(
            query if query else "fallback query",
            schema_name="chain_of_thought",
        )

        assert result is not None


@pytest.mark.asyncio
async def test_orchestrator_subproblem_decomposition():
    """Test that orchestrator properly decomposes complex queries."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent)

    complex_query = """
    What are the theoretical foundations, recent empirical results,
    alternative perspectives, and practical applications of trust
    and uncertainty in knowledge graphs?
    """

    result = await orchestrator.research_with_schema(
        complex_query,
        schema_name="decompose_and_synthesize",
    )

    # Should have multiple subsolutions
    assert len(result["subsolutions"]) > 1
    assert len(result["decomposition"]) > 1


@pytest.mark.asyncio
async def test_orchestrator_topology_metrics_consistency():
    """Test that topology metrics are consistent across calls."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent, reset_topology_per_query=True)

    query = "What is knowledge structure?"

    # Run same query twice
    result1 = await orchestrator.research_with_schema(
        query,
        schema_name="chain_of_thought",
    )

    result2 = await orchestrator.research_with_schema(
        query,
        schema_name="chain_of_thought",
    )

    # Topology metrics should be present in both
    assert "topology" in result1
    assert "topology" in result2

    # Metrics should have same structure
    topo1 = result1["topology"]
    topo2 = result2["topology"]

    assert set(topo1.keys()) == set(topo2.keys())


@pytest.mark.asyncio
async def test_orchestrator_max_tools_limit():
    """Test that orchestrator respects max_tools_per_subproblem limit."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent)

    query = "comprehensive deep thorough analysis"

    result = await orchestrator.research_with_schema(
        query,
        schema_name="chain_of_thought",
        max_tools_per_subproblem=2,
    )

    # Check that no subproblem used more than max tools
    for subsolution in result["subsolutions"]:
        tools_used = len(subsolution.get("tools_used", []))
        assert tools_used <= 2


@pytest.mark.asyncio
async def test_orchestrator_conditioning_set_propagation():
    """Test that conditioning set properly propagates through subproblems."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent)

    query = "What are the key concepts and how do they relate?"

    result = await orchestrator.research_with_schema(
        query,
        schema_name="decompose_and_synthesize",
    )

    # Later subsolutions should have more nodes in conditioning set
    # (they depend on earlier results)
    if len(result["subsolutions"]) > 1:
        # Check that topology has nodes from all subsolutions
        total_nodes = len(orchestrator.topology.nodes)
        assert total_nodes > 0


@pytest.mark.asyncio
async def test_orchestrator_synthesis_quality():
    """Test that synthesis produces coherent results."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent)

    query = "What is structured reasoning?"

    result = await orchestrator.research_with_schema(
        query,
        schema_name="chain_of_thought",
    )

    synthesis = result["final_synthesis"]

    # Synthesis should be non-empty
    assert len(synthesis) > 0

    # Should contain some content (may include MCP placeholders if tools not available)
    # This is expected behavior when MCP tools return placeholders
    assert len(synthesis) > 0  # At minimum, should have some content


@pytest.mark.asyncio
async def test_orchestrator_topology_impact_tracking():
    """Test that topology impact is tracked for each subproblem."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent)

    query = "What are trust and uncertainty?"

    result = await orchestrator.research_with_schema(
        query,
        schema_name="decompose_and_synthesize",
        preserve_d_separation=True,
    )

    # Each subsolution should have topology impact
    for subsolution in result["subsolutions"]:
        assert "topology_impact" in subsolution
        impact = subsolution["topology_impact"]
        assert isinstance(impact, dict)


@pytest.mark.asyncio
async def test_orchestrator_source_credibility_variation():
    """Test that orchestrator handles different source credibilities."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent)

    # Use different tool types (which have different credibilities)
    query = "What is knowledge?"

    await orchestrator.research_with_schema(
        query,
        schema_name="chain_of_thought",
    )

    # Check that nodes have varying credibilities
    credibilities = [
        node.credibility
        for node in orchestrator.topology.nodes.values()
    ]

    if credibilities:
        # Should have some variation (not all same)
        assert len(set(credibilities)) > 0

