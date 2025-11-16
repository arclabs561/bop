"""Tests for structured orchestrator."""

import pytest
from bop.orchestrator import StructuredOrchestrator, ToolType, ToolSelector
from bop.research import ResearchAgent
from bop.schemas import get_schema


@pytest.mark.asyncio
async def test_orchestrator_initialization():
    """Test orchestrator initialization."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent)
    
    # Verify components are properly initialized
    assert orchestrator.research_agent == research_agent
    assert orchestrator.topology is not None
    assert isinstance(orchestrator.topology.nodes, dict)
    assert isinstance(orchestrator.topology.edges, dict)
    assert orchestrator.tool_selector is not None


@pytest.mark.asyncio
async def test_orchestrator_with_schema():
    """Test orchestrator with schema."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent)
    
    schema = get_schema("chain_of_thought")
    assert schema is not None
    
    # Test with a simple query
    result = await orchestrator.research_with_schema(
        "What is structured reasoning?",
        schema_name="chain_of_thought",
    )
    
    # Verify result structure and content
    assert result["query"] == "What is structured reasoning?"
    assert result["schema_used"] == "chain_of_thought"
    assert isinstance(result["subsolutions"], list)
    assert isinstance(result["final_synthesis"], str)
    assert len(result["final_synthesis"]) > 0  # Should have actual content


@pytest.mark.asyncio
async def test_orchestrator_topology_tracking():
    """Test that orchestrator tracks topology."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent)
    
    result = await orchestrator.research_with_schema(
        "Test query for topology",
        schema_name="chain_of_thought",
    )
    
    # Check topology metrics are included
    assert "topology" in result
    topology = result["topology"]
    assert "betti_numbers" in topology
    assert "euler_characteristic" in topology
    assert "trust_summary" in topology


@pytest.mark.asyncio
async def test_tool_selector():
    """Test tool selection logic."""
    selector = ToolSelector()
    
    # Test deep research query
    tools = selector.select_tools("comprehensive analysis of trust in knowledge graphs")
    assert ToolType.PERPLEXITY_DEEP in tools
    
    # Test reasoning query
    tools = selector.select_tools("why does trust propagate through networks?")
    assert ToolType.PERPLEXITY_REASON in tools
    
    # Test factual query
    tools = selector.select_tools("what is the definition of trust?")
    assert ToolType.PERPLEXITY_SEARCH in tools or ToolType.TAVILY_SEARCH in tools
    
    # Test URL query
    tools = selector.select_tools("scrape http://example.com")
    assert ToolType.FIRECRAWL_SCRAPE in tools


@pytest.mark.asyncio
async def test_orchestrator_preserves_d_separation():
    """Test that orchestrator preserves d-separation."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent, reset_topology_per_query=True)
    
    result = await orchestrator.research_with_schema(
        "Test query",
        schema_name="chain_of_thought",
        preserve_d_separation=True,
    )
    
    assert result["d_separation_preserved"] is True


@pytest.mark.asyncio
async def test_orchestrator_multiple_subproblems():
    """Test orchestrator with multiple subproblems."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent)
    
    # Use decompose_and_synthesize schema which creates multiple subproblems
    result = await orchestrator.research_with_schema(
        "What are the theoretical foundations and recent empirical results in trust modeling?",
        schema_name="decompose_and_synthesize",
    )
    
    assert len(result["subsolutions"]) > 0
    assert len(result["decomposition"]) > 0


@pytest.mark.asyncio
async def test_orchestrator_error_handling():
    """Test orchestrator error handling."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent)
    
    # Test with invalid schema
    result = await orchestrator.research_with_schema(
        "Test query",
        schema_name="nonexistent_schema",
    )
    
    # Should still return a result (fallback behavior)
    assert result is not None


@pytest.mark.asyncio
async def test_topology_aware_tool_selection():
    """Test topology-aware tool selection."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent)
    
    # Add some nodes to topology first
    from bop.context_topology import ContextNode
    node = ContextNode(
        id="test_node",
        content="Test content",
        source="test",
        credibility=0.8,
    )
    orchestrator.topology.add_node(node)
    
    # Test tool selection with topology
    candidate_tools = [ToolType.PERPLEXITY_SEARCH, ToolType.TAVILY_SEARCH]
    selected = orchestrator._topology_aware_tool_selection(
        candidate_tools,
        "test query",
        {"test_node"},
    )
    
    assert len(selected) > 0
    assert all(tool in candidate_tools for tool in selected)

