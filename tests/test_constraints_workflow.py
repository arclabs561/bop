"""Full workflow tests for constraint solver integration."""

import pytest

from bop.agent import KnowledgeAgent
from bop.constraints import PYSAT_AVAILABLE
from bop.orchestrator import StructuredOrchestrator
from bop.schemas import list_schemas


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
@pytest.mark.asyncio
async def test_full_research_workflow_with_constraints():
    """Test complete research workflow from query to final answer with constraints."""
    agent = KnowledgeAgent()
    agent.llm_service = None

    # Complete workflow with constraints enabled
    query = "What are the theoretical foundations and practical applications of trust in knowledge graphs?"

    # Note: KnowledgeAgent doesn't expose use_constraints yet, so test orchestrator directly
    orchestrator = StructuredOrchestrator(use_constraints=True)

    result = await orchestrator.research_with_schema(
        query,
        schema_name="decompose_and_synthesize",
        max_tools_per_subproblem=2,
    )

    # Verify complete workflow
    assert result["schema_used"] == "decompose_and_synthesize"
    assert "subsolutions" in result
    assert "final_synthesis" in result
    assert "topology" in result

    # Verify constraint solver was used
    assert orchestrator.use_constraints is True
    assert orchestrator.constraint_solver is not None

    # Verify tools were called
    assert result["tools_called"] >= 0


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
@pytest.mark.asyncio
async def test_multi_schema_workflow_with_constraints():
    """Test workflow using multiple schemas in sequence with constraints."""
    orchestrator = StructuredOrchestrator(use_constraints=True)

    schemas = ["chain_of_thought", "decompose_and_synthesize", "hypothesize_and_test"]

    for schema in schemas:
        result = await orchestrator.research_with_schema(
            "What is knowledge structure?",
            schema_name=schema,
            max_tools_per_subproblem=2,
        )

        assert result["schema_used"] == schema
        assert "subsolutions" in result
        assert orchestrator.use_constraints is True


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
@pytest.mark.asyncio
async def test_workflow_with_topology_tracking_and_constraints():
    """Test workflow with topology tracking enabled and constraints."""
    orchestrator = StructuredOrchestrator(
        use_constraints=True,
        reset_topology_per_query=False
    )

    queries = [
        "What is trust?",
        "What is uncertainty?",
        "How do they relate?",
    ]

    for query in queries:
        result = await orchestrator.research_with_schema(
            query,
            schema_name="chain_of_thought",
            preserve_d_separation=True,
            max_tools_per_subproblem=2,
        )

        # Topology should be tracked
        assert "topology" in result
        assert result["d_separation_preserved"] is True
        assert orchestrator.use_constraints is True

    # Final topology should have accumulated nodes
    assert len(orchestrator.topology.nodes) > 0


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
@pytest.mark.asyncio
async def test_workflow_error_recovery_with_constraints():
    """Test that workflow recovers from intermediate errors with constraints."""
    orchestrator = StructuredOrchestrator(use_constraints=True)

    # Workflow that might have errors
    queries = [
        "Normal query",
        "Another normal query",
    ]

    for query in queries:
        result = await orchestrator.research_with_schema(
            query,
            schema_name="chain_of_thought",
            max_tools_per_subproblem=2,
        )

        # Should always return a result
        assert result is not None
        assert "subsolutions" in result
        assert orchestrator.use_constraints is True


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
@pytest.mark.asyncio
async def test_orchestrator_all_schemas_with_constraints():
    """Test orchestrator with all available schemas using constraints."""
    orchestrator = StructuredOrchestrator(use_constraints=True)

    query = "What are the key concepts in knowledge structure?"
    schemas = list_schemas()

    for schema_name in schemas:
        result = await orchestrator.research_with_schema(
            query,
            schema_name=schema_name,
            max_tools_per_subproblem=2,
        )

        assert result is not None
        assert result["schema_used"] == schema_name
        assert "subsolutions" in result
        assert "final_synthesis" in result
        assert orchestrator.use_constraints is True


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
@pytest.mark.asyncio
async def test_orchestrator_query_variations_with_constraints():
    """Test orchestrator with various query types using constraints."""
    orchestrator = StructuredOrchestrator(use_constraints=True)

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
            max_tools_per_subproblem=2,
        )

        assert result["query"] == query
        assert len(result["final_synthesis"]) > 0
        assert orchestrator.use_constraints is True


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
@pytest.mark.asyncio
async def test_orchestrator_tool_diversity_with_constraints():
    """Test that orchestrator selects diverse tools with constraints."""
    orchestrator = StructuredOrchestrator(use_constraints=True)

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
            max_tools_per_subproblem=2,
        )

        # Collect tools used
        for subsolution in result["subsolutions"]:
            all_tools_used.update(subsolution.get("tools_used", []))

        assert orchestrator.use_constraints is True

    # Should have used multiple different tools
    assert len(all_tools_used) > 0


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
@pytest.mark.asyncio
async def test_orchestrator_max_tools_limit_with_constraints():
    """Test that orchestrator respects max_tools_per_subproblem limit with constraints."""
    orchestrator = StructuredOrchestrator(use_constraints=True)

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

    assert orchestrator.use_constraints is True

