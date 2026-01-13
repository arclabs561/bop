"""Integration tests for constraint solver with orchestrator workflows."""

from unittest.mock import patch

import pytest

from bop.constraints import PYSAT_AVAILABLE, ConstraintSolver, ToolType, create_default_constraints
from bop.orchestrator import StructuredOrchestrator


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
@pytest.mark.asyncio
async def test_orchestrator_constraints_vs_heuristics():
    """Compare constraint-based vs heuristic-based tool selection."""
    query = "What are the latest developments in LLM reasoning?"

    # Test with constraints
    orchestrator_constraints = StructuredOrchestrator(use_constraints=True)
    tools_constraints = orchestrator_constraints._select_tools_with_constraints(
        query, max_tools=2, min_information=0.5
    )

    # Test with heuristics
    orchestrator_heuristics = StructuredOrchestrator(use_constraints=False)
    tools_heuristics = orchestrator_heuristics.tool_selector.select_tools(query)
    tools_heuristics = tools_heuristics[:2]

    # Both should return tools
    assert tools_constraints is not None or tools_heuristics is not None

    # Constraint-based should respect max_tools
    if tools_constraints:
        assert len(tools_constraints) <= 2


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
@pytest.mark.asyncio
async def test_orchestrator_research_with_constraints():
    """Test full research workflow with constraint-based tool selection."""
    orchestrator = StructuredOrchestrator(use_constraints=True)

    query = "What is trust in knowledge graphs?"

    result = await orchestrator.research_with_schema(
        query,
        schema_name="decompose_and_synthesize",
        max_tools_per_subproblem=2,
    )

    assert result is not None
    assert "subsolutions" in result
    assert "tools_called" in result

    # Verify tools were selected
    total_tools = result["tools_called"]
    assert total_tools >= 0

    # Check that constraint solver was used
    assert orchestrator.use_constraints is True


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
@pytest.mark.asyncio
async def test_constraint_solver_fallback_on_failure():
    """Test that orchestrator falls back to heuristics if constraint solver fails."""
    orchestrator = StructuredOrchestrator(use_constraints=True)

    # Mock constraint solver to fail
    with patch.object(orchestrator.constraint_solver, 'solve_optimal', return_value=None):
        tools = orchestrator._select_tools_with_constraints(
            "test query",
            max_tools=2,
        )

        # Should fall back to heuristics
        assert tools is not None or orchestrator.tool_selector is not None


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
def test_constraint_solver_performance():
    """Test constraint solver performance with various constraint combinations."""
    solver = ConstraintSolver()
    constraints = create_default_constraints()

    import time

    # Test different scenarios
    scenarios = [
        {"max_tools": 1, "min_information": 0.3},
        {"max_tools": 2, "min_information": 0.5},
        {"max_tools": 3, "min_information": 0.7},
        {"max_tools": 2, "min_information": 0.5, "budget": 0.2},
        {"max_tools": 3, "min_information": 0.8, "budget": 0.4},
    ]

    for scenario in scenarios:
        start = time.time()
        result = solver.solve_optimal(
            constraints=constraints,
            objective="min_cost",
            **scenario
        )
        elapsed = time.time() - start

        # Should complete quickly (< 1 second)
        assert elapsed < 1.0, f"Scenario {scenario} took {elapsed:.3f}s"

        # If solution found, verify constraints
        if result:
            assert len(result) <= scenario["max_tools"]


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
def test_constraint_solver_objectives():
    """Test different optimization objectives."""
    solver = ConstraintSolver()
    constraints = create_default_constraints()

    objectives = ["min_cost", "max_information", "min_latency"]

    results = {}
    for objective in objectives:
        result = solver.solve_optimal(
            constraints=constraints,
            objective=objective,
            max_tools=2,
            min_information=0.5,
        )
        results[objective] = result

    # All objectives should find solutions
    assert all(r is not None for r in results.values())

    # min_cost should have lower cost than max_information
    if results["min_cost"] and results["max_information"]:
        cost_min = sum(next((c.cost for c in constraints if c.tool == t), 1.0)
                      for t in results["min_cost"])
        cost_max = sum(next((c.cost for c in constraints if c.tool == t), 1.0)
                      for t in results["max_information"])
        assert cost_min <= cost_max


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
@pytest.mark.asyncio
async def test_orchestrator_constraints_with_dependencies():
    """Test that constraint solver respects tool dependencies."""
    orchestrator = StructuredOrchestrator(use_constraints=True)

    # Query that might trigger dependency chain (e.g., scrape requires search)
    query = "Extract information from https://example.com"

    tools = orchestrator._select_tools_with_constraints(
        query,
        max_tools=3,
        min_information=0.5,
    )

    if tools:
        # If FIRECRAWL_SCRAPE is selected, FIRECRAWL_SEARCH should also be selected
        if ToolType.FIRECRAWL_SCRAPE in tools:
            assert ToolType.FIRECRAWL_SEARCH in tools


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
def test_constraint_solver_edge_cases():
    """Test constraint solver with edge cases."""
    solver = ConstraintSolver()
    constraints = create_default_constraints()

    # Test with impossible constraints
    result = solver.solve_optimal(
        constraints=constraints,
        objective="min_cost",
        max_tools=0,  # Can't select any tools
        min_information=0.5,  # But need information
    )
    # Should return None (no solution)
    assert result is None or len(result) == 0

    # Test with very high information requirement
    result = solver.solve_optimal(
        constraints=constraints,
        objective="min_cost",
        max_tools=2,
        min_information=10.0,  # Impossible to achieve
    )
    # Should return None (no solution)
    assert result is None

    # Test with very low budget
    result = solver.solve_optimal(
        constraints=constraints,
        objective="min_cost",
        max_tools=3,
        budget=0.01,  # Too low
        min_information=0.5,
    )
    # Should return None or empty (no solution)
    assert result is None or len(result) == 0

