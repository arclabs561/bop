"""Tests for real evaluation framework (not placeholders)."""


from pran.eval import EvaluationFramework, EvaluationResult


def test_evaluate_schema_usage_real():
    """Test real schema usage evaluation."""
    framework = EvaluationFramework()

    test_cases = [
        {
            "input": "Solve 2x + 3 = 7",
            "expected": {"input_analysis": str, "steps": list, "final_result": str},
            "actual": {
                "input_analysis": "Equation to solve: 2x + 3 = 7",
                "steps": ["Subtract 3 from both sides", "Divide both sides by 2"],
                "final_result": "x = 2",
            },
        },
        {
            "input": "What is 5 + 3?",
            "expected": {"input_analysis": str, "steps": list, "final_result": str},
            "actual": {
                "input_analysis": "Simple addition",
                "steps": ["Add 5 and 3"],
                "final_result": "8",
            },
        },
    ]

    result = framework.evaluate_schema_usage("chain_of_thought", test_cases)

    assert isinstance(result, EvaluationResult)
    assert result.test_name == "schema_chain_of_thought"
    assert result.score > 0.0
    assert "test_cases" in result.details
    assert result.details["test_cases"] == 2


def test_evaluate_schema_usage_empty():
    """Test schema usage evaluation with empty test cases."""
    framework = EvaluationFramework()
    result = framework.evaluate_schema_usage("chain_of_thought", [])

    assert isinstance(result, EvaluationResult)
    assert result.passed is False
    assert result.score == 0.0
    assert "error" in result.details


def test_evaluate_reasoning_coherence_real():
    """Test real reasoning coherence evaluation."""
    framework = EvaluationFramework()

    responses = [
        "First, I need to understand the problem. Then I'll break it down into steps.",
        "Let me analyze this step by step. First, identify the key components.",
        "I'll solve this systematically. Step 1: Understand the requirements.",
    ]

    result = framework.evaluate_reasoning_coherence(responses)

    assert isinstance(result, EvaluationResult)
    assert result.test_name == "reasoning_coherence"
    assert result.score > 0.0
    assert "responses_evaluated" in result.details
    assert result.details["responses_evaluated"] == 3
    assert "length_coherence" in result.details
    assert "overlap_score" in result.details
    assert "structure_score" in result.details


def test_evaluate_reasoning_coherence_empty():
    """Test reasoning coherence with empty responses."""
    framework = EvaluationFramework()
    result = framework.evaluate_reasoning_coherence([])

    assert isinstance(result, EvaluationResult)
    assert result.passed is False
    assert result.score == 0.0


def test_evaluate_dependency_gap_handling_real():
    """Test real dependency gap handling evaluation."""
    framework = EvaluationFramework()

    test_cases = [
        {
            "query": "What is the relationship between A and C?",
            "intermediate_steps": ["Understand A", "Find connection to B", "Relate B to C"],
            "actual_steps": ["Understanding A", "Finding B connection", "Relating to C"],
            "final_answer": "A relates to C through B",
            "actual_answer": "A relates to C through intermediate B, which connects them.",
        }
    ]

    result = framework.evaluate_dependency_gap_handling(test_cases)

    assert isinstance(result, EvaluationResult)
    assert result.test_name == "dependency_gap_handling"
    assert result.score > 0.0
    assert "test_cases" in result.details


def test_evaluate_dependency_gap_handling_empty():
    """Test dependency gap handling with empty test cases."""
    framework = EvaluationFramework()
    result = framework.evaluate_dependency_gap_handling([])

    assert isinstance(result, EvaluationResult)
    assert result.passed is False
    assert result.score == 0.0


def test_run_evaluations():
    """Test running all evaluations."""
    framework = EvaluationFramework()
    results = framework.run_evaluations()

    assert isinstance(results, dict)
    assert len(results) > 0
    assert "schema_chain_of_thought" in results
    assert "reasoning_coherence" in results
    assert "dependency_gap_handling" in results

    # Check that results have real scores (not hardcoded)
    for test_name, result in results.items():
        assert "score" in result
        assert "passed" in result
        assert "details" in result

