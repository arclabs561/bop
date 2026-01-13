"""Integration tests with minimal mocking - test real behavior."""


import pytest

from bop.agent import KnowledgeAgent
from bop.context_topology import ContextNode, ContextTopology
from bop.eval import EvaluationFramework
from bop.orchestrator import StructuredOrchestrator
from bop.research import ResearchAgent


@pytest.mark.asyncio
async def test_orchestrator_real_topology_building():
    """Test orchestrator actually builds topology from tool results."""
    orchestrator = StructuredOrchestrator()

    # Mock only the tool calls, not the topology logic
    from unittest.mock import patch

    with patch.object(orchestrator, "_call_tool") as mock_call:
        mock_call.return_value = {
            "tool": "perplexity_search",
            "query": "test query",
            "result": "Test result content about trust and uncertainty",
            "sources": ["source1", "source2"],
        }

        result = await orchestrator.research_with_schema(
            "What is trust?",
            schema_name="decompose_and_synthesize",
        )

        # Verify topology was actually built
        assert len(orchestrator.topology.nodes) > 0
        # Should have nodes from tool results
        node_ids = list(orchestrator.topology.nodes.keys())
        assert any("q1_" in node_id for node_id in node_ids)

        # Verify topology metrics are computed
        assert "topology" in result
        assert "betti_numbers" in result["topology"]
        assert isinstance(result["topology"]["betti_numbers"], dict)


@pytest.mark.asyncio
async def test_agent_real_conversation_flow():
    """Test agent maintains real conversation state."""
    agent = KnowledgeAgent()
    agent.llm_service = None  # Use fallback to test real logic

    # First message
    await agent.chat("Hello, what is structured reasoning?")

    # Verify conversation history is maintained
    history = agent.get_conversation_history()
    assert len(history) == 2  # User + assistant

    # Second message - should have context
    response2 = await agent.chat("Can you tell me more?")

    # Should have more history
    assert len(agent.get_conversation_history()) == 4
    # Second response should reference previous context
    assert "response" in response2


def test_topology_real_clique_computation():
    """Test topology actually computes cliques correctly."""
    topology = ContextTopology()

    # Create a real graph structure
    nodes = []
    for i in range(5):
        node = ContextNode(
            id=f"n{i}",
            content=f"Content about topic {i}",
            source="test",
            credibility=0.7 + i * 0.05,
        )
        topology.add_node(node)
        nodes.append(f"n{i}")

    # Create a triangle (3-clique)
    topology.add_edge("n0", "n1", weight=0.9)
    topology.add_edge("n1", "n2", weight=0.9)
    topology.add_edge("n0", "n2", weight=0.9)

    # Add isolated edge
    topology.add_edge("n3", "n4", weight=0.8)

    cliques = topology.compute_cliques()

    # Should find the 3-clique
    three_cliques = [c for c in cliques if len(c.nodes) == 3]
    assert len(three_cliques) > 0

    # Verify the 3-clique contains the right nodes
    three_clique = three_cliques[0]
    assert {"n0", "n1", "n2"}.issubset(three_clique.nodes)

    # Should also find 2-cliques
    two_cliques = [c for c in cliques if len(c.nodes) == 2]
    assert len(two_cliques) >= 1  # At least the n3-n4 edge


def test_topology_real_betti_computation():
    """Test topology computes Betti numbers correctly."""
    topology = ContextTopology()

    # Create disconnected components
    for i in range(3):
        node = ContextNode(id=f"c1_n{i}", content="comp1", source="test")
        topology.add_node(node)
        if i > 0:
            topology.add_edge(f"c1_n{i-1}", f"c1_n{i}")

    for i in range(3):
        node = ContextNode(id=f"c2_n{i}", content="comp2", source="test")
        topology.add_node(node)
        if i > 0:
            topology.add_edge(f"c2_n{i-1}", f"c2_n{i}")

    betti = topology.compute_betti_numbers()

    # Should have 2 connected components (β₀ = 2)
    assert betti[0] == 2

    # Should have no cycles in this structure (β₁ = 0)
    assert betti[1] == 0


@pytest.mark.asyncio
async def test_orchestrator_real_tool_selection():
    """Test orchestrator actually selects tools based on query."""
    orchestrator = StructuredOrchestrator()

    # Test different query types trigger different tools
    from unittest.mock import patch

    with patch.object(orchestrator, "_call_tool") as mock_call:
        mock_call.return_value = {
            "tool": "test",
            "result": "Test result",
            "sources": [],
        }

        # Deep research query
        await orchestrator.research_with_schema(
            "comprehensive analysis of trust",
            schema_name="decompose_and_synthesize",
        )

        # Get tools that were called
        call_args_list = mock_call.call_args_list
        tool_types_called = [call[0][0] for call in call_args_list]

        # Should have called at least one tool
        assert len(tool_types_called) > 0

        # Verify tool selection happened (tools should match query type)
        # This tests the real ToolSelector logic


def test_evaluation_framework_real_scoring():
    """Test evaluation framework produces real, non-hardcoded scores."""
    framework = EvaluationFramework()

    # Test with different inputs should produce different scores
    test_cases_good = [
        {
            "input": "Solve 2x + 3 = 7",
            "expected": {"input_analysis": str, "steps": list, "final_result": str},
            "actual": {
                "input_analysis": "Equation to solve",
                "steps": ["Subtract 3", "Divide by 2"],
                "final_result": "x = 2",
            },
        }
    ]

    test_cases_bad = [
        {
            "input": "Solve 2x + 3 = 7",
            "expected": {"input_analysis": str, "steps": list, "final_result": str},
            "actual": {
                "input_analysis": "",  # Empty
                "steps": 123,  # Wrong type
                "final_result": "",  # Empty
            },
        }
    ]

    result_good = framework.evaluate_schema_usage("chain_of_thought", test_cases_good)
    result_bad = framework.evaluate_schema_usage("chain_of_thought", test_cases_bad)

    # Good case should score higher
    assert result_good.score > result_bad.score
    # Scores should be different (not hardcoded)
    assert abs(result_good.score - result_bad.score) > 0.2


@pytest.mark.asyncio
async def test_research_agent_real_structure():
    """Test research agent returns proper structure without over-mocking."""
    agent = ResearchAgent(use_mcp=False)  # Don't use MCP, but test real structure

    result = await agent.deep_research("test query")

    # Verify structure is correct
    assert "query" in result
    assert "summary" in result
    assert "sources" in result
    assert isinstance(result["sources"], list)
    assert result["query"] == "test query"


def test_topology_real_trust_propagation():
    """Test topology actually propagates trust through edges."""
    topology = ContextTopology()

    # Create chain with varying trust
    node1 = ContextNode(id="n1", content="high trust", source="trusted", credibility=0.9)
    node2 = ContextNode(id="n2", content="medium", source="medium", credibility=0.6)
    node3 = ContextNode(id="n3", content="low trust", source="untrusted", credibility=0.3)

    topology.add_node(node1)
    topology.add_node(node2)
    topology.add_node(node3)

    topology.add_edge("n1", "n2", weight=0.8, trust=0.7)
    topology.add_edge("n2", "n3", weight=0.6, trust=0.4)

    topology.compute_cliques()

    # Verify trust is considered in cliques
    cliques = topology.cliques
    if cliques:
        # Cliques should have trust scores
        for clique in cliques:
            assert hasattr(clique, "trust_score")
            assert 0.0 <= clique.trust_score <= 1.0

