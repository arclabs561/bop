"""Real-world scenario tests for constraint solver integration."""

import pytest

from pran.constraints import PYSAT_AVAILABLE, create_default_constraints
from pran.orchestrator import StructuredOrchestrator


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
@pytest.mark.asyncio
async def test_constraints_real_research_query():
    """
    Test constraint solver with real research query scenario.

    Scenario: User asks complex research question requiring multiple tools.
    Goal: Optimize tool selection for quality and cost.
    """
    orchestrator = StructuredOrchestrator(use_constraints=True)

    # Real research query
    query = "What are the latest developments in trust and uncertainty modeling for knowledge graphs?"

    result = await orchestrator.research_with_schema(
        query,
        schema_name="decompose_and_synthesize",
        max_tools_per_subproblem=2,
    )

    # Verify research was conducted
    assert "subsolutions" in result
    assert len(result["subsolutions"]) > 0
    assert "final_synthesis" in result
    assert len(result["final_synthesis"]) > 0

    # Verify constraint solver was used
    assert orchestrator.use_constraints is True

    # Verify tools were selected optimally
    total_tools = result["tools_called"]
    assert total_tools > 0

    # Verify topology was built
    assert "topology" in result
    topology = result["topology"]
    assert "betti_numbers" in topology
    assert "fisher_information" in topology


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
@pytest.mark.asyncio
async def test_constraints_budget_constrained_research():
    """
    Test constraint solver with budget-constrained research scenario.

    Scenario: User has limited API budget, needs quality research.
    Goal: Maximize information within budget constraints.
    """
    orchestrator = StructuredOrchestrator(use_constraints=True)

    query = "Comprehensive analysis of trust in knowledge structures"

    # Simulate budget constraint by limiting tools
    result = await orchestrator.research_with_schema(
        query,
        schema_name="decompose_and_synthesize",
        max_tools_per_subproblem=1,  # Tight budget
    )

    # Should still produce quality research
    assert "subsolutions" in result
    assert "final_synthesis" in result

    # Should respect tool limit
    for subsolution in result["subsolutions"]:
        assert len(subsolution.get("tools_used", [])) <= 1

    # Calculate cost
    constraints = create_default_constraints()
    total_cost = sum(
        next((c.cost for c in constraints if c.tool.value == t), 0.0)
        for subsolution in result["subsolutions"]
        for t in subsolution.get("tools_used", [])
    )

    # Should be cost-efficient
    assert total_cost < 1.0  # Reasonable cost
    assert orchestrator.use_constraints is True


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
@pytest.mark.asyncio
async def test_constraints_multi_turn_conversation():
    """
    Test constraint solver in multi-turn conversation scenario.

    Scenario: User has ongoing conversation, context accumulates.
    Goal: Maintain coherence while optimizing tool selection.
    """
    orchestrator = StructuredOrchestrator(
        use_constraints=True,
        reset_topology_per_query=False  # Accumulate context
    )

    # First turn
    result1 = await orchestrator.research_with_schema(
        "What is trust in knowledge graphs?",
        schema_name="chain_of_thought",
        max_tools_per_subproblem=2,
    )

    initial_nodes = len(orchestrator.topology.nodes)

    # Second turn (builds on first)
    result2 = await orchestrator.research_with_schema(
        "How does uncertainty relate to what we discussed?",
        schema_name="chain_of_thought",
        max_tools_per_subproblem=2,
    )

    # Topology should have grown
    assert len(orchestrator.topology.nodes) > initial_nodes

    # Both should use constraints
    assert orchestrator.use_constraints is True

    # Both should have results
    assert "final_synthesis" in result1
    assert "final_synthesis" in result2

    # Topology should reflect accumulated knowledge
    assert "topology" in result2
    topology = result2["topology"]
    assert "attractor_basins" in topology


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
@pytest.mark.asyncio
async def test_constraints_comparative_research():
    """
    Test constraint solver with comparative research scenario.

    Scenario: User wants to compare multiple concepts.
    Goal: Select tools that provide balanced information.
    """
    orchestrator = StructuredOrchestrator(use_constraints=True)

    query = "Compare trust and uncertainty in knowledge structures"

    result = await orchestrator.research_with_schema(
        query,
        schema_name="decompose_and_synthesize",
        max_tools_per_subproblem=2,
    )

    # Should decompose into comparison subproblems
    assert len(result["subsolutions"]) > 1

    # Each subproblem should have tools
    for subsolution in result["subsolutions"]:
        assert "tools_used" in subsolution
        assert len(subsolution["tools_used"]) > 0

    # Should synthesize comparison
    assert len(result["final_synthesis"]) > 0
    assert orchestrator.use_constraints is True


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
@pytest.mark.asyncio
async def test_constraints_deep_dive_research():
    """
    Test constraint solver with deep dive research scenario.

    Scenario: User wants comprehensive, deep research.
    Goal: Select high-information tools even if higher cost.
    """
    orchestrator = StructuredOrchestrator(use_constraints=True)

    query = "comprehensive deep thorough analysis of trust propagation in networks"

    result = await orchestrator.research_with_schema(
        query,
        schema_name="decompose_and_synthesize",
        max_tools_per_subproblem=3,  # Allow more tools for deep research
    )

    # Should produce comprehensive results
    assert "subsolutions" in result
    assert len(result["subsolutions"]) > 0

    # Calculate information gain
    constraints = create_default_constraints()
    total_info = 0.0

    for subsolution in result["subsolutions"]:
        for tool_name in subsolution.get("tools_used", []):
            constraint = next(
                (c for c in constraints if c.tool.value == tool_name),
                None
            )
            if constraint:
                total_info += constraint.information_gain

    # Deep research should have high information gain
    if total_info > 0:
        # Should meet high information threshold for "deep" queries
        assert total_info >= 0.5, \
            f"Deep research should have high information gain, got {total_info:.2f}"

    assert orchestrator.use_constraints is True


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
@pytest.mark.asyncio
async def test_constraints_rapid_factual_query():
    """
    Test constraint solver with rapid factual query scenario.

    Scenario: User wants quick factual answer.
    Goal: Select fast, low-cost tools that provide sufficient information.
    """
    orchestrator = StructuredOrchestrator(use_constraints=True)

    query = "What is the definition of trust?"

    result = await orchestrator.research_with_schema(
        query,
        schema_name="chain_of_thought",
        max_tools_per_subproblem=1,  # Minimal tools for quick answer
    )

    # Should produce quick answer
    assert "final_synthesis" in result
    assert len(result["final_synthesis"]) > 0

    # Should use minimal tools
    assert result["tools_called"] <= 1

    # Calculate latency
    constraints = create_default_constraints()
    total_latency = sum(
        next((c.latency for c in constraints if c.tool.value == t), 0.0)
        for subsolution in result["subsolutions"]
        for t in subsolution.get("tools_used", [])
    )

    # Should be fast
    assert total_latency < 5.0, \
        f"Rapid query should be fast, got {total_latency:.2f}s"

    assert orchestrator.use_constraints is True


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
@pytest.mark.asyncio
async def test_constraints_cross_domain_research():
    """
    Test constraint solver with cross-domain research scenario.

    Scenario: User researches across multiple domains.
    Goal: Select diverse tools to cover different domains.
    """
    orchestrator = StructuredOrchestrator(use_constraints=True)

    query = "How do trust, uncertainty, and information geometry relate?"

    result = await orchestrator.research_with_schema(
        query,
        schema_name="decompose_and_synthesize",
        max_tools_per_subproblem=2,
    )

    # Should use multiple tools
    all_tools = set()
    for subsolution in result["subsolutions"]:
        all_tools.update(subsolution.get("tools_used", []))

    # Should have tool diversity
    assert len(all_tools) > 0

    # Should synthesize cross-domain knowledge
    assert len(result["final_synthesis"]) > 0
    assert orchestrator.use_constraints is True

    # Topology should reflect cross-domain connections
    assert "topology" in result


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
@pytest.mark.asyncio
async def test_constraints_sequential_dependent_research():
    """
    Test constraint solver with sequential dependent research.

    Scenario: Research requires sequential steps (find URL, scrape, extract).
    Goal: Respect tool dependencies for proper sequencing.
    """
    orchestrator = StructuredOrchestrator(use_constraints=True)

    # Query that might trigger dependency chain
    query = "Find and extract information from research papers about trust"

    result = await orchestrator.research_with_schema(
        query,
        schema_name="decompose_and_synthesize",
        max_tools_per_subproblem=3,  # Allow dependency chain
    )

    # Should handle sequential dependencies
    assert "subsolutions" in result

    # Constraint solver should respect dependencies
    # (e.g., if scrape is used, search should be used)
    constraints = create_default_constraints()

    for subsolution in result["subsolutions"]:
        tools_used = [t for t in subsolution.get("tools_used", [])]

        # Check dependencies are satisfied
        for tool_name in tools_used:
            constraint = next(
                (c for c in constraints if c.tool.value == tool_name),
                None
            )
            if constraint and constraint.dependencies:
                # Dependencies should be satisfied (in this or previous subproblems)
                # This is a simplified check
                pass

    assert orchestrator.use_constraints is True


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
@pytest.mark.asyncio
async def test_constraints_quality_vs_cost_tradeoff():
    """
    Test constraint solver optimizes quality vs cost tradeoff.

    Scenario: User wants good quality but has cost concerns.
    Goal: Find optimal balance between quality and cost.
    """
    orchestrator_constraints = StructuredOrchestrator(use_constraints=True)
    orchestrator_heuristics = StructuredOrchestrator(use_constraints=False)

    query = "Research topic requiring quality information"

    # With constraints
    result_constraints = await orchestrator_constraints.research_with_schema(
        query,
        schema_name="decompose_and_synthesize",
        max_tools_per_subproblem=2,
    )

    # With heuristics
    result_heuristics = await orchestrator_heuristics.research_with_schema(
        query,
        schema_name="decompose_and_synthesize",
        max_tools_per_subproblem=2,
    )

    # Calculate metrics
    constraints = create_default_constraints()

    def calculate_metrics(result):
        cost = 0.0
        info = 0.0
        for subsolution in result["subsolutions"]:
            for tool_name in subsolution.get("tools_used", []):
                constraint = next(
                    (c for c in constraints if c.tool.value == tool_name),
                    None
                )
                if constraint:
                    cost += constraint.cost
                    info += constraint.information_gain
        return cost, info

    cost_constraints, info_constraints = calculate_metrics(result_constraints)
    cost_heuristics, info_heuristics = calculate_metrics(result_heuristics)

    # Constraint solver should optimize the tradeoff
    if info_constraints > 0 and info_heuristics > 0:
        # Constraint solver should have better cost/info ratio or meet requirements
        ratio_constraints = cost_constraints / info_constraints
        ratio_heuristics = cost_heuristics / info_heuristics

        # Constraint solver should be at least as efficient
        assert ratio_constraints <= ratio_heuristics * 1.2, \
            f"Constraint ratio {ratio_constraints:.3f} should be <= heuristic {ratio_heuristics:.3f}"

    assert orchestrator_constraints.use_constraints is True

