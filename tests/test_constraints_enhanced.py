"""Enhanced tests for constraint solver with pseudo-boolean and cardinality constraints."""

import pytest

# Test if PySAT is available
try:
    from pysat.formula import CNF
    from pysat.solvers import Solver
    try:
        from pysat.card import CardEnc
        CARD_AVAILABLE = True
    except ImportError:
        CARD_AVAILABLE = False
    PYSAT_AVAILABLE = True
except ImportError:
    PYSAT_AVAILABLE = False
    CARD_AVAILABLE = False


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
class TestConstraintSolverEnhanced:
    """Test enhanced constraint solver with pseudo-boolean and cardinality constraints."""

    def test_max_tools_cardinality_constraint(self):
        """Test that max_tools constraint is enforced."""
        from pran.constraints import ConstraintSolver, ToolConstraint, ToolType

        solver = ConstraintSolver()
        constraints = [
            ToolConstraint(tool=ToolType.PERPLEXITY_SEARCH, cost=0.1),
            ToolConstraint(tool=ToolType.TAVILY_SEARCH, cost=0.1),
            ToolConstraint(tool=ToolType.FIRECRAWL_SEARCH, cost=0.15),
            ToolConstraint(tool=ToolType.PERPLEXITY_DEEP, cost=0.3),
        ]

        # Test with max_tools = 2
        result = solver.solve(constraints, max_tools=2)
        assert result is not None
        assert len(result) <= 2

        # Test with max_tools = 1
        result = solver.solve(constraints, max_tools=1)
        assert result is not None
        assert len(result) <= 1

    def test_budget_constraint(self):
        """Test that budget constraint is enforced."""
        from pran.constraints import ConstraintSolver, ToolConstraint, ToolType

        solver = ConstraintSolver()
        constraints = [
            ToolConstraint(tool=ToolType.PERPLEXITY_SEARCH, cost=0.1),
            ToolConstraint(tool=ToolType.TAVILY_SEARCH, cost=0.1),
            ToolConstraint(tool=ToolType.FIRECRAWL_SEARCH, cost=0.15),
            ToolConstraint(tool=ToolType.PERPLEXITY_DEEP, cost=0.3),
        ]

        # Test with budget = 0.2 (should only allow low-cost tools)
        result = solver.solve(constraints, budget=0.2)
        assert result is not None
        total_cost = sum(
            next((c.cost for c in constraints if c.tool == t), 1.0)
            for t in result
        )
        assert total_cost <= 0.2

        # Test with budget = 0.5 (should allow more tools)
        result = solver.solve(constraints, budget=0.5)
        assert result is not None
        total_cost = sum(
            next((c.cost for c in constraints if c.tool == t), 1.0)
            for t in result
        )
        assert total_cost <= 0.5

    def test_min_information_constraint(self):
        """Test that min_information constraint is enforced."""
        from pran.constraints import ConstraintSolver, ToolConstraint, ToolType

        solver = ConstraintSolver()
        constraints = [
            ToolConstraint(tool=ToolType.PERPLEXITY_SEARCH, information_gain=0.4, required=True),
            ToolConstraint(tool=ToolType.TAVILY_SEARCH, information_gain=0.4),
            ToolConstraint(tool=ToolType.PERPLEXITY_DEEP, information_gain=0.8),
        ]

        # Test with min_information = 0.3 (should be easy to satisfy)
        result = solver.solve(constraints, min_information=0.3)
        assert result is not None
        assert len(result) > 0
        total_info = sum(
            next((c.information_gain for c in constraints if c.tool == t), 0.0)
            for t in result
        )
        assert total_info >= 0.3

        # Test with min_information = 0.5 (needs at least one high-info tool or multiple)
        result = solver.solve(constraints, min_information=0.5)
        if result is not None:  # May be None if no solution found
            total_info = sum(
                next((c.information_gain for c in constraints if c.tool == t), 0.0)
                for t in result
            )
            assert total_info >= 0.5

    def test_combined_constraints(self):
        """Test combining multiple constraints."""
        from pran.constraints import ConstraintSolver, ToolConstraint, ToolType

        solver = ConstraintSolver()
        constraints = [
            ToolConstraint(tool=ToolType.PERPLEXITY_SEARCH, cost=0.1, information_gain=0.4),
            ToolConstraint(tool=ToolType.TAVILY_SEARCH, cost=0.1, information_gain=0.4),
            ToolConstraint(tool=ToolType.PERPLEXITY_DEEP, cost=0.3, information_gain=0.8),
            ToolConstraint(tool=ToolType.FIRECRAWL_SCRAPE, cost=0.2, information_gain=0.7),
        ]

        # Test with budget, min_information, and max_tools
        result = solver.solve(
            constraints,
            budget=0.4,
            min_information=0.7,
            max_tools=2
        )

        if result is not None:
            assert len(result) <= 2
            total_cost = sum(
                next((c.cost for c in constraints if c.tool == t), 1.0)
                for t in result
            )
            assert total_cost <= 0.4
            total_info = sum(
                next((c.information_gain for c in constraints if c.tool == t), 0.0)
                for t in result
            )
            assert total_info >= 0.7

    def test_impossible_constraints(self):
        """Test that impossible constraints return None."""
        from pran.constraints import ConstraintSolver, ToolConstraint, ToolType

        solver = ConstraintSolver()
        constraints = [
            ToolConstraint(tool=ToolType.PERPLEXITY_SEARCH, cost=0.1, information_gain=0.4),
            ToolConstraint(tool=ToolType.TAVILY_SEARCH, cost=0.1, information_gain=0.4),
        ]

        # Impossible: budget too low
        result = solver.solve(constraints, budget=0.05)
        # May return None or empty list
        if result is not None:
            assert len(result) == 0 or sum(
                next((c.cost for c in constraints if c.tool == t), 1.0)
                for t in result
            ) <= 0.05

        # Impossible: information requirement too high
        result = solver.solve(constraints, min_information=2.0)
        # Should return None or empty
        assert result is None or len(result) == 0

    def test_cardinality_with_dependencies(self):
        """Test cardinality constraint with dependency constraints."""
        from pran.constraints import ConstraintSolver, ToolConstraint, ToolType

        solver = ConstraintSolver()
        constraints = [
            ToolConstraint(
                tool=ToolType.FIRECRAWL_SCRAPE,
                cost=0.2,
                dependencies=[ToolType.FIRECRAWL_SEARCH],
            ),
            ToolConstraint(tool=ToolType.FIRECRAWL_SEARCH, cost=0.15),
            ToolConstraint(tool=ToolType.PERPLEXITY_SEARCH, cost=0.1),
        ]

        # With max_tools=2, if scrape is selected, search must be too
        result = solver.solve(constraints, max_tools=2)
        assert result is not None

        # If scrape is in result, search must be too
        if ToolType.FIRECRAWL_SCRAPE in result:
            assert ToolType.FIRECRAWL_SEARCH in result

    def test_budget_with_conflicts(self):
        """Test budget constraint with conflict constraints."""
        from pran.constraints import ConstraintSolver, ToolConstraint, ToolType

        solver = ConstraintSolver()
        constraints = [
            ToolConstraint(
                tool=ToolType.PERPLEXITY_SEARCH,
                cost=0.1,
                conflicts=[ToolType.TAVILY_SEARCH],
            ),
            ToolConstraint(tool=ToolType.TAVILY_SEARCH, cost=0.1),
            ToolConstraint(tool=ToolType.FIRECRAWL_SEARCH, cost=0.15),
        ]

        # With budget=0.2, can't use both search tools
        result = solver.solve(constraints, budget=0.2)
        assert result is not None

        # Should not have both conflicting tools
        assert not (
            ToolType.PERPLEXITY_SEARCH in result and
            ToolType.TAVILY_SEARCH in result
        )

        # Total cost should be within budget
        total_cost = sum(
            next((c.cost for c in constraints if c.tool == t), 1.0)
            for t in result
        )
        assert total_cost <= 0.2

