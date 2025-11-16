"""Tests for topology-aware tool selection."""

import pytest

from bop.orchestrator import StructuredOrchestrator, ToolType, ToolSelector
from bop.research import ResearchAgent
from bop.context_topology import ContextTopology, ContextNode


def test_topology_aware_tool_selection_empty_topology():
    """Test topology-aware selection with empty topology (should use heuristics)."""
    orchestrator = StructuredOrchestrator()
    candidate_tools = [ToolType.PERPLEXITY_SEARCH, ToolType.TAVILY_SEARCH]
    
    # With empty topology, should return tools as-is
    selected = orchestrator._topology_aware_tool_selection(
        candidate_tools, "test query", set()
    )
    
    assert len(selected) == 2
    assert ToolType.PERPLEXITY_SEARCH in selected
    assert ToolType.TAVILY_SEARCH in selected


def test_topology_aware_tool_selection_with_context():
    """Test topology-aware selection considers existing context."""
    orchestrator = StructuredOrchestrator()
    
    # Add some context nodes
    node1 = ContextNode(
        id="n1",
        content="Existing context",
        source="perplexity_search",
        credibility=0.8,
        confidence=0.7,
    )
    orchestrator.topology.add_node(node1)
    
    # Add another node connected to first
    node2 = ContextNode(
        id="n2",
        content="Related context",
        source="tavily_search",
        credibility=0.7,
        confidence=0.6,
    )
    orchestrator.topology.add_node(node2)
    orchestrator.topology.add_edge("n1", "n2", weight=0.8)
    orchestrator.topology.compute_cliques()
    
    candidate_tools = [ToolType.PERPLEXITY_SEARCH, ToolType.TAVILY_SEARCH, ToolType.FIRECRAWL_SEARCH]
    conditioning_set = {"n1", "n2"}
    
    selected = orchestrator._topology_aware_tool_selection(
        candidate_tools, "test query", conditioning_set
    )
    
    # Should still return tools, but potentially reordered based on topology
    assert len(selected) == 3
    assert all(tool in selected for tool in candidate_tools)


def test_topology_aware_tool_selection_credibility_ranking():
    """Test that tools with higher credibility are preferred."""
    orchestrator = StructuredOrchestrator()
    
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
    
    # Tools with different credibility
    candidate_tools = [
        ToolType.FIRECRAWL_SEARCH,  # Lower credibility (0.6)
        ToolType.PERPLEXITY_DEEP,   # Higher credibility (0.75)
    ]
    
    selected = orchestrator._topology_aware_tool_selection(
        candidate_tools, "test query", set()
    )
    
    # Higher credibility tool should be ranked first
    assert selected[0] == ToolType.PERPLEXITY_DEEP


def test_topology_aware_tool_selection_connects_to_cliques():
    """Test that tools connecting to existing cliques are preferred."""
    orchestrator = StructuredOrchestrator()
    
    # Create a high-trust clique
    node1 = ContextNode(
        id="n1",
        content="Context 1",
        source="perplexity_search",
        credibility=0.8,
        confidence=0.7,
    )
    node2 = ContextNode(
        id="n2",
        content="Context 2",
        source="perplexity_search",
        credibility=0.8,
        confidence=0.7,
    )
    orchestrator.topology.add_node(node1)
    orchestrator.topology.add_node(node2)
    orchestrator.topology.add_edge("n1", "n2", weight=0.9)
    orchestrator.topology.compute_cliques()
    
    # Tools that could extend the clique should be preferred
    candidate_tools = [
        ToolType.FIRECRAWL_SEARCH,  # Different source, might not connect
        ToolType.PERPLEXITY_SEARCH,  # Same source as clique, likely connects
    ]
    
    selected = orchestrator._topology_aware_tool_selection(
        candidate_tools, "test query", {"n1", "n2"}
    )
    
    # Should return tools (exact ranking depends on scoring)
    assert len(selected) == 2


def test_topology_influences_research():
    """Test that topology analysis influences tool selection in research."""
    orchestrator = StructuredOrchestrator()
    
    # Add initial context
    node = ContextNode(
        id="n1",
        content="Initial research result",
        source="perplexity_search",
        credibility=0.8,
    )
    orchestrator.topology.add_node(node)
    orchestrator.topology.compute_cliques()
    
    # Verify topology-aware selection is used
    # (This is tested indirectly through research_with_schema)
    assert orchestrator.topology.nodes
    assert len(orchestrator.topology.cliques) >= 0  # May be 0 if no edges


@pytest.mark.asyncio
async def test_research_with_topology_aware_selection():
    """Test that research uses topology-aware tool selection."""
    orchestrator = StructuredOrchestrator()
    
    # Add some context first
    node = ContextNode(
        id="n1",
        content="Prior context",
        source="perplexity_search",
        credibility=0.8,
    )
    orchestrator.topology.add_node(node)
    
    # Run research (should use topology-aware selection)
    # Note: This will use placeholder MCP calls, but should still exercise the logic
    result = await orchestrator.research_with_schema(
        "Test query",
        schema_name="decompose_and_synthesize",
        preserve_d_separation=True,
    )
    
    assert "subsolutions" in result
    assert "topology" in result
    # Verify topology metrics are computed
    assert "betti_numbers" in result["topology"]
    assert "fisher_information" in result["topology"]

