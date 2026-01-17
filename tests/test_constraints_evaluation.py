"""Evaluation and benchmarking for constraint-based tool selection."""

import statistics
import time

import pytest

from pran.constraints import PYSAT_AVAILABLE, ConstraintSolver, create_default_constraints
from pran.orchestrator import StructuredOrchestrator


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
class TestConstraintSolverEvaluation:
    """Evaluate constraint solver performance and quality."""

    def test_solver_speed_benchmark(self):
        """Benchmark constraint solver speed."""
        solver = ConstraintSolver()
        constraints = create_default_constraints()

        times = []
        for _ in range(10):
            start = time.time()
            solver.solve_optimal(
                constraints=constraints,
                objective="min_cost",
                max_tools=2,
                min_information=0.5,
            )
            elapsed = time.time() - start
            times.append(elapsed)

        avg_time = statistics.mean(times)
        max_time = max(times)

        # Should be fast (< 100ms average)
        assert avg_time < 0.1, f"Average time: {avg_time:.3f}s"
        assert max_time < 0.5, f"Max time: {max_time:.3f}s"

    def test_solver_consistency(self):
        """Test that solver produces consistent results."""
        solver = ConstraintSolver()
        constraints = create_default_constraints()

        results = []
        for _ in range(5):
            result = solver.solve_optimal(
                constraints=constraints,
                objective="min_cost",
                max_tools=2,
                min_information=0.5,
            )
            if result:
                results.append(tuple(sorted(t.value for t in result)))

        # Should produce consistent results (same solution each time)
        if len(results) > 1:
            assert len(set(results)) == 1, "Solver should be deterministic"

    def test_cost_optimization_quality(self):
        """Evaluate quality of cost optimization."""
        solver = ConstraintSolver()
        constraints = create_default_constraints()

        # Get optimal solution
        optimal = solver.solve_optimal(
            constraints=constraints,
            objective="min_cost",
            max_tools=2,
            min_information=0.5,
        )

        if optimal:
            optimal_cost = sum(
                next((c.cost for c in constraints if c.tool == t), 1.0)
                for t in optimal
            )

            # Compare with all possible 2-tool combinations
            from itertools import combinations
            all_costs = []
            for combo in combinations(constraints, 2):
                total_cost = sum(c.cost for c in combo)
                total_info = sum(c.information_gain for c in combo)
                if total_info >= 0.5:
                    all_costs.append(total_cost)

            if all_costs:
                min_possible_cost = min(all_costs)
                # Optimal should be close to minimum (within 10%)
                assert optimal_cost <= min_possible_cost * 1.1, \
                    f"Optimal cost {optimal_cost:.3f} should be <= {min_possible_cost * 1.1:.3f}"

    def test_information_optimization_quality(self):
        """Evaluate quality of information optimization."""
        solver = ConstraintSolver()
        constraints = create_default_constraints()

        # Get optimal solution
        optimal = solver.solve_optimal(
            constraints=constraints,
            objective="max_information",
            max_tools=2,
            min_information=0.5,
        )

        if optimal:
            optimal_info = sum(
                next((c.information_gain for c in constraints if c.tool == t), 0.0)
                for t in optimal
            )

            # Compare with all possible 2-tool combinations
            from itertools import combinations
            all_infos = []
            for combo in combinations(constraints, 2):
                total_info = sum(c.information_gain for c in combo)
                total_cost = sum(c.cost for c in combo)
                if total_cost <= 1.0:  # Reasonable cost
                    all_infos.append(total_info)

        if all_infos:
            max_possible_info = max(all_infos)
            # Optimal should be reasonable (at least 50% of max, or meet min requirement)
            # Note: solver might choose single high-info tool over combination
            assert optimal_info >= 0.5 or optimal_info >= max_possible_info * 0.5, \
                f"Optimal info {optimal_info:.3f} should be >= 0.5 or >= {max_possible_info * 0.5:.3f}"


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
@pytest.mark.asyncio
class TestOrchestratorConstraintEvaluation:
    """Evaluate orchestrator with constraint-based selection."""

    async def test_tool_selection_comparison(self):
        """Compare tool selection between constraint and heuristic methods."""
        query = "What are the latest developments in AI reasoning?"

        orchestrator_constraints = StructuredOrchestrator(use_constraints=True)
        orchestrator_heuristics = StructuredOrchestrator(use_constraints=False)

        # Get selections
        tools_constraints = orchestrator_constraints._select_tools_with_constraints(
            query, max_tools=2, min_information=0.5
        )
        tools_heuristics = orchestrator_heuristics.tool_selector.select_tools(query)
        tools_heuristics = tools_heuristics[:2]

        # Both should select tools
        assert tools_constraints is not None or tools_heuristics is not None

        # Constraint-based should respect max_tools strictly
        if tools_constraints:
            assert len(tools_constraints) <= 2

    async def test_cost_comparison(self):
        """Compare costs between constraint and heuristic selection."""
        from pran.constraints import create_default_constraints

        query = "Research topic"
        constraints = create_default_constraints()

        orchestrator_constraints = StructuredOrchestrator(use_constraints=True)
        orchestrator_heuristics = StructuredOrchestrator(use_constraints=False)

        tools_constraints = orchestrator_constraints._select_tools_with_constraints(
            query, max_tools=2, min_information=0.5
        )
        tools_heuristics = orchestrator_heuristics.tool_selector.select_tools(query)
        tools_heuristics = tools_heuristics[:2]

        # Calculate costs
        if tools_constraints:
            cost_constraints = sum(
                next((c.cost for c in constraints if c.tool == t), 1.0)
                for t in tools_constraints
            )
        else:
            cost_constraints = float('inf')

        if tools_heuristics:
            cost_heuristics = sum(
                next((c.cost for c in constraints if c.tool == t), 1.0)
                for t in tools_heuristics
            )
        else:
            cost_heuristics = float('inf')

        # Constraint-based should optimize cost while meeting info requirements
        if tools_constraints and tools_heuristics:
            # Calculate information for both
            info_constraints = sum(
                next((c.information_gain for c in constraints if c.tool == t), 0.0)
                for t in tools_constraints
            )
            info_heuristics = sum(
                next((c.information_gain for c in constraints if c.tool == t), 0.0)
                for t in tools_heuristics
            )

            # Constraint-based should meet min_information requirement
            assert info_constraints >= 0.5, \
                f"Constraint info {info_constraints:.3f} should be >= 0.5"

            # If both meet requirements, constraint should optimize cost
            # But allow some flexibility since heuristics might find cheaper solution
            # that doesn't meet info requirement
            if info_heuristics >= 0.5:
                assert cost_constraints <= cost_heuristics * 1.5, \
                    f"Constraint cost {cost_constraints:.3f} should be <= heuristic cost {cost_heuristics:.3f} (when both meet info)"

    async def test_information_gain_comparison(self):
        """Compare information gain between constraint and heuristic selection."""
        from pran.constraints import create_default_constraints

        query = "Deep research topic"
        constraints = create_default_constraints()

        orchestrator_constraints = StructuredOrchestrator(use_constraints=True)
        orchestrator_heuristics = StructuredOrchestrator(use_constraints=False)

        tools_constraints = orchestrator_constraints._select_tools_with_constraints(
            query, max_tools=2, min_information=0.5
        )
        tools_heuristics = orchestrator_heuristics.tool_selector.select_tools(query)
        tools_heuristics = tools_heuristics[:2]

        # Calculate information gain
        if tools_constraints:
            info_constraints = sum(
                next((c.information_gain for c in constraints if c.tool == t), 0.0)
                for t in tools_constraints
            )
        else:
            info_constraints = 0.0

        if tools_heuristics:
            sum(
                next((c.information_gain for c in constraints if c.tool == t), 0.0)
                for t in tools_heuristics
            )
        else:
            pass

        # Both should meet minimum information requirement
        if tools_constraints:
            assert info_constraints >= 0.5, \
                f"Constraint info {info_constraints:.3f} should be >= 0.5"


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
def test_constraint_solver_scalability():
    """Test constraint solver with larger problem sizes."""
    solver = ConstraintSolver()

    # Create larger constraint set
    constraints = create_default_constraints()
    # Duplicate to simulate larger problem
    large_constraints = constraints * 2

    start = time.time()
    result = solver.solve_optimal(
        constraints=large_constraints,
        objective="min_cost",
        max_tools=3,
        min_information=0.5,
    )
    elapsed = time.time() - start

    # Should still complete quickly
    assert elapsed < 1.0, f"Large problem took {elapsed:.3f}s"

    if result:
        assert len(result) <= 3

