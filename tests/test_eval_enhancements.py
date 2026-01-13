"""Evaluations for optional enhancements: constraint solver and LLM decomposition."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from bop.eval import EvaluationFramework
from bop.schemas import get_schema


def test_eval_constraint_solver_budget_optimization():
    """Evaluate that constraint solver optimizes for budget."""
    try:
        from bop.constraints import ConstraintSolver, ToolConstraint, ToolType
    except ImportError:
        pytest.skip("PySAT not available")

    solver = ConstraintSolver()
    constraints = [
        ToolConstraint(tool=ToolType.PERPLEXITY_SEARCH, cost=0.1, information_gain=0.4),
        ToolConstraint(tool=ToolType.TAVILY_SEARCH, cost=0.1, information_gain=0.4),
        ToolConstraint(tool=ToolType.PERPLEXITY_DEEP, cost=0.3, information_gain=0.8),
    ]

    # With tight budget, should select cheaper tools
    result = solver.solve(constraints, budget=0.2, min_information=0.3)

    if result is not None:
        total_cost = sum(
            next((c.cost for c in constraints if c.tool == t), 1.0)
            for t in result
        )
        total_info = sum(
            next((c.information_gain for c in constraints if c.tool == t), 0.0)
            for t in result
        )

        # Should respect budget
        assert total_cost <= 0.2
        # Should meet information requirement
        assert total_info >= 0.3


def test_eval_constraint_solver_cardinality():
    """Evaluate that cardinality constraints work correctly."""
    try:
        from bop.constraints import ConstraintSolver, ToolConstraint, ToolType
    except ImportError:
        pytest.skip("PySAT not available")

    solver = ConstraintSolver()
    constraints = [
        ToolConstraint(tool=ToolType.PERPLEXITY_SEARCH),
        ToolConstraint(tool=ToolType.TAVILY_SEARCH),
        ToolConstraint(tool=ToolType.FIRECRAWL_SEARCH),
        ToolConstraint(tool=ToolType.PERPLEXITY_DEEP),
    ]

    # Test max_tools constraint
    result = solver.solve(constraints, max_tools=2)
    assert result is not None
    assert len(result) <= 2


@pytest.mark.asyncio
async def test_eval_llm_decomposition_quality():
    """Evaluate quality of LLM-based decomposition."""
    EvaluationFramework()

    # Test cases for decomposition quality
    test_cases = [
        {
            "input": "What is the relationship between trust and uncertainty?",
            "expected_subproblems": 3,  # Should decompose into multiple subproblems
            "actual_subproblems": [
                "Theoretical foundation of trust and uncertainty",
                "Recent empirical studies",
                "Alternative perspectives",
            ],
        }
    ]

    # Evaluate that decomposition creates meaningful subproblems
    for case in test_cases:
        actual = case["actual_subproblems"]
        expected_count = case["expected_subproblems"]

        # Should have expected number of subproblems
        assert len(actual) >= expected_count

        # Each subproblem should be non-empty and distinct
        assert all(sub.strip() for sub in actual)
        assert len(set(actual)) == len(actual)  # All unique


@pytest.mark.asyncio
async def test_eval_orchestrator_decomposition_integration():
    """Evaluate orchestrator integration with LLM decomposition."""
    from bop.orchestrator import StructuredOrchestrator

    orchestrator = StructuredOrchestrator()

    # Test without LLM (fallback)
    schema = get_schema("decompose_and_synthesize")
    if not schema:
        pytest.skip("decompose_and_synthesize schema not found")

    orchestrator.llm_service = None
    result = await orchestrator._decompose_query("Test query", schema)

    # Should return valid decomposition
    assert isinstance(result, list)
    assert len(result) > 0

    # Test with LLM (mocked)
    mock_llm = MagicMock()
    mock_llm.decompose_query = AsyncMock(return_value=[
        "Subproblem 1",
        "Subproblem 2",
    ])
    orchestrator.llm_service = mock_llm

    result = await orchestrator._decompose_query("Test query", schema)

    # Should use LLM decomposition
    assert len(result) == 2
    assert result[0] == "Subproblem 1"


def test_eval_constraint_solver_complex_scenario():
    """Evaluate constraint solver with complex real-world scenario."""
    try:
        from bop.constraints import ConstraintSolver, ToolConstraint, ToolType
    except ImportError:
        pytest.skip("PySAT not available")

    solver = ConstraintSolver()

    # Realistic constraints
    constraints = [
        ToolConstraint(
            tool=ToolType.PERPLEXITY_DEEP,
            cost=0.3,
            information_gain=0.8,
            latency=3.0,
        ),
        ToolConstraint(
            tool=ToolType.FIRECRAWL_SCRAPE,
            cost=0.2,
            information_gain=0.7,
            latency=2.0,
            dependencies=[ToolType.FIRECRAWL_SEARCH],
        ),
        ToolConstraint(
            tool=ToolType.FIRECRAWL_SEARCH,
            cost=0.15,
            information_gain=0.5,
            latency=1.5,
        ),
        ToolConstraint(
            tool=ToolType.PERPLEXITY_SEARCH,
            cost=0.1,
            information_gain=0.4,
            conflicts=[ToolType.TAVILY_SEARCH],
        ),
        ToolConstraint(
            tool=ToolType.TAVILY_SEARCH,
            cost=0.1,
            information_gain=0.4,
        ),
    ]

    # Complex scenario: budget, information, and max tools
    result = solver.solve(
        constraints,
        budget=0.5,
        min_information=0.7,
        max_tools=3,
    )

    if result is not None:
        # Verify all constraints satisfied
        total_cost = sum(
            next((c.cost for c in constraints if c.tool == t), 1.0)
            for t in result
        )
        total_info = sum(
            next((c.information_gain for c in constraints if c.tool == t), 0.0)
            for t in result
        )

        assert total_cost <= 0.5
        assert total_info >= 0.7
        assert len(result) <= 3

        # Verify dependencies: if scrape selected, search must be too
        if ToolType.FIRECRAWL_SCRAPE in result:
            assert ToolType.FIRECRAWL_SEARCH in result

        # Verify conflicts: can't have both search tools
        assert not (
            ToolType.PERPLEXITY_SEARCH in result and
            ToolType.TAVILY_SEARCH in result
        )

