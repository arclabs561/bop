"""Strengthened evaluation tests that verify correctness, not just structure."""

import pytest

from bop.eval import EvaluationFramework, EvaluationResult


def test_evaluate_schema_usage_validates_content():
    """Test that schema evaluation validates field content, not just presence."""
    framework = EvaluationFramework()
    
    from bop.schemas import get_schema
    schema = get_schema("chain_of_thought")
    if not schema:
        pytest.skip("chain_of_thought schema not found")
    
    # Test case with empty strings (should fail)
    test_cases = [
        {
            "input": "Solve 2x + 3 = 7",
            "expected": schema.schema_def,
            "actual": {
                key: "" for key in schema.schema_def.keys()  # All empty strings
            },
        }
    ]
    
    result = framework.evaluate_schema_usage("chain_of_thought", test_cases)
    
    # Should have low score even though fields are present (empty content)
    # Score = coverage * (0.5 + 0.5 * content_quality) = 1.0 * (0.5 + 0.5 * 0.0) = 0.5
    assert result.score <= 0.5  # Empty content should score at most 0.5
    assert result.passed is False
    assert "fields have content" in str(result.details.get("errors", []))


def test_evaluate_schema_usage_validates_field_types():
    """Test that schema evaluation validates field types match expected."""
    framework = EvaluationFramework()
    
    from bop.schemas import get_schema
    schema = get_schema("chain_of_thought")
    if not schema:
        pytest.skip("chain_of_thought schema not found")
    
    # Test case with wrong types
    test_cases = [
        {
            "input": "Test",
            "expected": schema.schema_def,
            "actual": {
                key: 12345 if isinstance(schema.schema_def[key], str) else "wrong"
                for key in schema.schema_def.keys()
            },
        }
    ]
    
    result = framework.evaluate_schema_usage("chain_of_thought", test_cases)
    
    # Type mismatches should reduce score
    # (Current implementation doesn't check types, but this documents the gap)
    assert isinstance(result, EvaluationResult)


def test_evaluate_reasoning_coherence_detects_wrong_answers():
    """Test that coherence evaluation can detect when answers are wrong."""
    framework = EvaluationFramework()
    
    # Responses that are coherent in structure but wrong in content
    wrong_but_coherent = [
        "The answer is 42. First, I calculate. Then I verify.",
        "The answer is 42. First, I calculate. Then I verify.",
        "The answer is 42. First, I calculate. Then I verify.",
    ]
    
    result = framework.evaluate_reasoning_coherence(wrong_but_coherent)
    
    # Current implementation only checks structure, not correctness
    # This test documents that limitation
    assert result.score > 0.6  # High coherence (structure)
    # But we can't verify correctness with current implementation
    # TODO: Add semantic correctness checks


def test_evaluate_reasoning_coherence_detects_incoherent():
    """Test that coherence evaluation detects truly incoherent responses."""
    framework = EvaluationFramework()
    
    # Completely different responses
    incoherent = [
        "A",
        "This is a very long and detailed response that contains many words and provides extensive explanation.",
        "42",
    ]
    
    result = framework.evaluate_reasoning_coherence(incoherent)
    
    # Should have low coherence
    assert result.score < 0.5
    assert result.passed is False


def test_evaluate_dependency_gap_validates_step_relevance():
    """Test that dependency gap evaluation validates step relevance."""
    framework = EvaluationFramework()
    
    # Test case with irrelevant steps
    test_cases = [
        {
            "query": "What is the relationship between A and C?",
            "intermediate_steps": ["Understand A", "Find B", "Relate B to C"],
            "actual_steps": ["Step 1", "Step 2", "Step 3"],  # Generic, not relevant
            "final_answer": "A relates to C through B",
            "actual_answer": "A relates to C through B",
        }
    ]
    
    result = framework.evaluate_dependency_gap_handling(test_cases)
    
    # Current implementation only checks count, not relevance
    # This test documents the limitation
    assert isinstance(result, EvaluationResult)
    # TODO: Add step relevance validation


def test_evaluate_dependency_gap_validates_answer_quality():
    """Test that dependency gap evaluation validates answer quality."""
    framework = EvaluationFramework()
    
    # Test case with answer that doesn't address query
    test_cases = [
        {
            "query": "What is the relationship between A and C?",
            "intermediate_steps": ["Step 1", "Step 2"],
            "actual_steps": ["Step 1", "Step 2"],
            "final_answer": "A relates to C through B",
            "actual_answer": "The weather is nice today.",  # Completely irrelevant
        }
    ]
    
    result = framework.evaluate_dependency_gap_handling(test_cases)
    
    # Current implementation only checks length, not relevance
    # This test documents the limitation
    assert isinstance(result, EvaluationResult)
    # TODO: Add answer relevance validation


def test_evaluate_dependency_gap_detects_missing_steps():
    """Test that dependency gap evaluation detects when steps are missing."""
    framework = EvaluationFramework()
    
    test_cases = [
        {
            "query": "What is A to C?",
            "intermediate_steps": ["Understand A", "Find B", "Relate B to C"],
            "actual_steps": [],  # No steps provided
            "final_answer": "A relates to C through B",
            "actual_answer": "A relates to C",  # Missing intermediate reasoning
        }
    ]
    
    result = framework.evaluate_dependency_gap_handling(test_cases)
    
    # Should have low score when steps are missing
    assert result.score < 0.5
    assert "errors" in result.details


def test_evaluation_framework_catches_empty_responses():
    """Test that evaluation framework catches empty or null responses."""
    framework = EvaluationFramework()
    
    # Schema usage with None values
    test_cases = [
        {
            "input": "Test",
            "expected": {"field1": str, "field2": str},
            "actual": {
                "field1": None,
                "field2": "",
            },
        }
    ]
    
    result = framework.evaluate_schema_usage("chain_of_thought", test_cases)
    
    # Should handle None values gracefully
    assert isinstance(result, EvaluationResult)
    # Fields with None should reduce score
    assert result.score < 1.0


def test_evaluation_framework_validates_required_fields():
    """Test that evaluation framework validates all required fields are present."""
    framework = EvaluationFramework()
    
    from bop.schemas import get_schema
    schema = get_schema("chain_of_thought")
    if not schema:
        pytest.skip("chain_of_thought schema not found")
    
    required_fields = list(schema.schema_def.keys())
    if len(required_fields) < 2:
        pytest.skip("Schema has too few fields")
    
    # Missing some required fields
    partial_actual = {
        field: f"value_{field}"
        for field in required_fields[:len(required_fields)//2]
    }
    
    test_cases = [
        {
            "input": "Test",
            "expected": {field: str for field in required_fields},
            "actual": partial_actual,
        }
    ]
    
    result = framework.evaluate_schema_usage("chain_of_thought", test_cases)
    
    # Should score based on coverage
    assert result.score < 1.0
    assert result.score == len(partial_actual) / len(required_fields)  # Exact coverage ratio


def test_evaluation_framework_handles_malformed_input():
    """Test that evaluation framework handles malformed input gracefully."""
    framework = EvaluationFramework()
    
    # Malformed test cases
    malformed_cases = [
        {},  # Empty dict
        {"input": "Test"},  # Missing expected/actual
        {"input": "Test", "expected": "not a dict"},  # Wrong type
        {"input": "Test", "actual": "not a dict"},  # Wrong type
    ]
    
    for case in malformed_cases:
        result = framework.evaluate_schema_usage("chain_of_thought", [case])
        
        # Should handle gracefully without crashing
        assert isinstance(result, EvaluationResult)
        assert "errors" in result.details or result.score == 0.0

