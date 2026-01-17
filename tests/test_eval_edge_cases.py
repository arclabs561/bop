"""Edge case tests for evaluation framework."""

import pytest

from pran.eval import EvaluationFramework, EvaluationResult


def test_evaluate_schema_usage_partial_coverage():
    """Test schema evaluation with partial field coverage."""
    framework = EvaluationFramework()

    # Get actual schema to test with real fields
    from pran.schemas import get_schema
    schema = get_schema("chain_of_thought")
    if not schema:
        pytest.skip("chain_of_thought schema not found")

    # Create test case with partial coverage of actual schema fields
    schema_fields = list(schema.schema_def.keys())
    if len(schema_fields) < 2:
        pytest.skip("Schema has too few fields to test partial coverage")

    # Include some fields, exclude others
    partial_actual = {field: f"value_{field}" for field in schema_fields[:len(schema_fields)//2]}

    test_cases = [
        {
            "input": "Test query",
            "expected": {field: str for field in schema_fields},  # All fields expected
            "actual": partial_actual,  # Only partial fields
        }
    ]

    result = framework.evaluate_schema_usage("chain_of_thought", test_cases)

    assert result.score < 1.0  # Should be less than perfect
    assert result.score >= 0.0  # Should be non-negative (may be 0 if no fields match)
    # With partial coverage, should have some score if fields match
    if len(partial_actual) > 0:
        assert result.score > 0.0 or "errors" in result.details


def test_evaluate_schema_usage_invalid_format():
    """Test schema evaluation handles invalid test case format."""
    framework = EvaluationFramework()

    test_cases = [
        {
            "input": "Test",
            "expected": "Not a dict",  # Invalid
            "actual": {"field1": "value1"},
        }
    ]

    result = framework.evaluate_schema_usage("chain_of_thought", test_cases)

    # Should handle gracefully
    assert isinstance(result, EvaluationResult)
    assert "errors" in result.details or result.score == 0.0


def test_evaluate_reasoning_coherence_very_different():
    """Test coherence evaluation with very different responses."""
    framework = EvaluationFramework()

    responses = [
        "Short answer.",
        "This is a much longer and more detailed response that contains many more words and provides extensive explanation of the topic at hand with multiple sentences and comprehensive coverage.",
        "Another response.",
    ]

    result = framework.evaluate_reasoning_coherence(responses)

    # Very different lengths should lower coherence
    assert isinstance(result, EvaluationResult)
    assert 0.0 <= result.score <= 1.0
    # High variance should reduce score
    assert result.score < 1.0


def test_evaluate_reasoning_coherence_identical():
    """Test coherence with nearly identical responses."""
    framework = EvaluationFramework()

    responses = [
        "First, I need to understand the problem. Then I'll break it down into steps.",
        "First, I need to understand the problem. Then I'll break it down into steps.",
        "First, I need to understand the problem. Then I'll break it down into steps.",
    ]

    result = framework.evaluate_reasoning_coherence(responses)

    # Identical responses should have high coherence
    assert result.score >= 0.7  # Should be quite high (>= instead of >)


def test_evaluate_dependency_gap_no_steps():
    """Test dependency gap evaluation when no intermediate steps provided."""
    framework = EvaluationFramework()

    test_cases = [
        {
            "query": "What is A to C?",
            "intermediate_steps": ["Step 1", "Step 2"],
            "actual_steps": [],  # No steps provided
            "final_answer": "A relates to C",
            "actual_answer": "A relates to C",
        }
    ]

    result = framework.evaluate_dependency_gap_handling(test_cases)

    # Should penalize missing steps
    assert result.score < 1.0
    assert "errors" in result.details


def test_evaluate_dependency_gap_short_answer():
    """Test dependency gap evaluation with very short answer."""
    framework = EvaluationFramework()

    test_cases = [
        {
            "query": "What is the relationship between A and C?",
            "intermediate_steps": ["Step 1"],
            "actual_steps": ["Step 1"],
            "final_answer": "A relates to C through B",
            "actual_answer": "Yes",  # Too short
        }
    ]

    result = framework.evaluate_dependency_gap_handling(test_cases)

    # Short answer should reduce score
    assert result.score < 1.0


def test_evaluate_dependency_gap_excellent():
    """Test dependency gap evaluation with excellent response."""
    framework = EvaluationFramework()

    test_cases = [
        {
            "query": "What is A to C?",
            "intermediate_steps": ["Understand A", "Find B", "Relate B to C"],
            "actual_steps": ["Understanding A", "Finding B connection", "Relating B to C"],
            "final_answer": "A relates to C through B",
            "actual_answer": "A relates to C through intermediate B, which serves as a bridge connecting the two concepts with detailed explanation.",
        }
    ]

    result = framework.evaluate_dependency_gap_handling(test_cases)

    # Excellent response should score well
    assert result.score >= 0.7
    assert result.passed is True


def test_run_evaluations_all_pass():
    """Test running evaluations when all tests pass."""
    framework = EvaluationFramework()
    results = framework.run_evaluations()

    # Should return results for all evaluation types
    assert "schema_chain_of_thought" in results
    assert "reasoning_coherence" in results
    assert "dependency_gap_handling" in results

    # All should have scores
    for test_name, result in results.items():
        assert "score" in result
        assert "passed" in result
        assert isinstance(result["score"], (int, float))
        assert isinstance(result["passed"], bool)


def test_evaluation_result_serialization():
    """Test that evaluation results can be serialized."""
    framework = EvaluationFramework()
    results = framework.run_evaluations()

    # Should be JSON-serializable
    import json
    json_str = json.dumps(results)
    parsed = json.loads(json_str)

    assert isinstance(parsed, dict)
    assert len(parsed) == len(results)


def test_evaluate_schema_usage_missing_schema():
    """Test schema evaluation when schema doesn't exist."""
    framework = EvaluationFramework()

    test_cases = [{"input": "Test", "expected": {}, "actual": {}}]
    result = framework.evaluate_schema_usage("nonexistent_schema", test_cases)

    # Should handle missing schema gracefully
    assert isinstance(result, EvaluationResult)
    assert "errors" in result.details or result.score == 0.0

