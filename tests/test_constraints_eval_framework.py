"""Evaluation framework integration for constraint solver."""

import pytest
from bop.eval import EvaluationFramework, EvaluationResult
from bop.constraints import ConstraintSolver, create_default_constraints, ToolType, PYSAT_AVAILABLE


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
def test_eval_constraint_solver_using_framework():
    """Evaluate constraint solver using EvaluationFramework."""
    framework = EvaluationFramework()
    
    # Create test cases for constraint solver
    test_cases = []
    
    solver = ConstraintSolver()
    constraints = create_default_constraints()
    
    # Test case 1: Budget optimization
    result1 = solver.solve_optimal(
        constraints=constraints,
        objective="min_cost",
        budget=0.2,
        min_information=0.5,
        max_tools=2,
    )
    
    if result1:
        total_cost = sum(
            next((c.cost for c in constraints if c.tool == t), 1.0)
            for t in result1
        )
        total_info = sum(
            next((c.information_gain for c in constraints if c.tool == t), 0.0)
            for t in result1
        )
        
        test_cases.append({
            "input": "Budget optimization scenario",
            "expected": {
                "budget_respected": True,
                "information_met": True,
                "max_tools_respected": True,
            },
            "actual": {
                "budget_respected": total_cost <= 0.2,
                "information_met": total_info >= 0.5,
                "max_tools_respected": len(result1) <= 2,
            },
        })
    
    # Test case 2: Information optimization
    result2 = solver.solve_optimal(
        constraints=constraints,
        objective="max_information",
        min_information=0.5,
        max_tools=2,
    )
    
    if result2:
        total_info = sum(
            next((c.information_gain for c in constraints if c.tool == t), 0.0)
            for t in result2
        )
        
        test_cases.append({
            "input": "Information optimization scenario",
            "expected": {
                "information_met": True,
                "max_tools_respected": True,
            },
            "actual": {
                "information_met": total_info >= 0.5,
                "max_tools_respected": len(result2) <= 2,
            },
        })
    
    if test_cases:
        # Evaluate using framework
        result = framework.evaluate_schema_usage("constraint_solver", test_cases)
        
        assert isinstance(result, EvaluationResult)
        assert result.test_name == "schema_constraint_solver"
        assert result.score >= 0.0
        assert "test_cases" in result.details


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
def test_eval_constraint_solver_quality_scoring():
    """Evaluate constraint solver quality with proper scoring."""
    framework = EvaluationFramework()
    
    solver = ConstraintSolver()
    constraints = create_default_constraints()
    
    # Test multiple scenarios and collect results
    scenarios = [
        {
            "name": "budget_constraint",
            "params": {"budget": 0.2, "min_information": 0.5, "max_tools": 2},
            "expected": {"cost": 0.2, "info": 0.5, "tools": 2},
        },
        {
            "name": "information_requirement",
            "params": {"min_information": 0.7, "max_tools": 3},
            "expected": {"info": 0.7, "tools": 3},
        },
        {
            "name": "max_tools_limit",
            "params": {"max_tools": 1, "min_information": 0.3},
            "expected": {"tools": 1, "info": 0.3},
        },
    ]
    
    test_cases = []
    for scenario in scenarios:
        result = solver.solve_optimal(
            constraints=constraints,
            objective="min_cost",
            **scenario["params"]
        )
        
        if result:
            actual = {}
            expected = scenario["expected"]
            
            if "cost" in expected:
                total_cost = sum(
                    next((c.cost for c in constraints if c.tool == t), 1.0)
                    for t in result
                )
                actual["cost"] = total_cost
                actual["cost_ok"] = total_cost <= expected["cost"]
            
            if "info" in expected:
                total_info = sum(
                    next((c.information_gain for c in constraints if c.tool == t), 0.0)
                    for t in result
                )
                actual["info"] = total_info
                actual["info_ok"] = total_info >= expected["info"]
            
            if "tools" in expected:
                actual["tools"] = len(result)
                actual["tools_ok"] = len(result) <= expected["tools"]
            
            test_cases.append({
                "input": scenario["name"],
                "expected": expected,
                "actual": actual,
            })
    
    if test_cases:
        # Use a real schema for evaluation, or evaluate directly
        # Since constraint solver doesn't have a schema, evaluate constraints directly
        passed_count = sum(
            1 for case in test_cases
            if case["actual"].get("cost_ok", True) and 
               case["actual"].get("info_ok", True) and
               case["actual"].get("tools_ok", True)
        )
        
        # Should have passed all constraint checks
        assert passed_count == len(test_cases), \
            f"Expected all {len(test_cases)} test cases to pass constraints, but {passed_count} passed"


@pytest.mark.skipif(not PYSAT_AVAILABLE, reason="PySAT not available")
def test_eval_constraint_solver_comparison():
    """Evaluate constraint solver vs heuristic selection."""
    framework = EvaluationFramework()
    
    from bop.orchestrator import StructuredOrchestrator
    from bop.constraints import create_default_constraints
    
    query = "Research topic"
    constraints = create_default_constraints()
    
    # Constraint-based selection
    orchestrator_constraints = StructuredOrchestrator(use_constraints=True)
    tools_constraints = orchestrator_constraints._select_tools_with_constraints(
        query, max_tools=2, min_information=0.5
    )
    
    # Heuristic-based selection
    orchestrator_heuristics = StructuredOrchestrator(use_constraints=False)
    tools_heuristics = orchestrator_heuristics.tool_selector.select_tools(query)
    tools_heuristics = tools_heuristics[:2]
    
    # Calculate metrics for comparison
    test_cases = []
    
    if tools_constraints:
        cost_constraints = sum(
            next((c.cost for c in constraints if c.tool == t), 1.0)
            for t in tools_constraints
        )
        info_constraints = sum(
            next((c.information_gain for c in constraints if c.tool == t), 0.0)
            for t in tools_constraints
        )
        
        if tools_heuristics:
            cost_heuristics = sum(
                next((c.cost for c in constraints if c.tool == t), 1.0)
                for t in tools_heuristics
            )
            info_heuristics = sum(
                next((c.information_gain for c in constraints if c.tool == t), 0.0)
                for t in tools_heuristics
            )
            
            test_cases.append({
                "input": "Tool selection comparison",
                "expected": {
                    "constraint_cost_optimized": True,
                    "constraint_info_met": True,
                },
                "actual": {
                    "constraint_cost_optimized": cost_constraints <= cost_heuristics * 1.2,
                    "constraint_info_met": info_constraints >= 0.5,
                    "heuristic_info_met": info_heuristics >= 0.0,
                },
            })
    
    if test_cases:
        result = framework.evaluate_schema_usage("constraint_vs_heuristic", test_cases)
        
        assert isinstance(result, EvaluationResult)
        assert result.score >= 0.0

