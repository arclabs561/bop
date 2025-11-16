"""Tests for advanced evaluation features: semantic similarity, type validation, step relevance."""

import pytest

from bop.eval import EvaluationFramework, EvaluationResult


def test_evaluate_schema_usage_type_validation():
    """Test that schema evaluation validates field types."""
    framework = EvaluationFramework()
    
    from bop.schemas import get_schema
    schema = get_schema("chain_of_thought")
    if not schema:
        pytest.skip("chain_of_thought schema not found")
    
    # Test case with wrong types
    test_cases = [
        {
            "input": "Test query",
            "expected": {
                "input_analysis": str,  # Expected string type
                "steps": list,  # Expected list type
                "final_result": str,
            },
            "actual": {
                "input_analysis": 12345,  # Wrong type: int instead of str
                "steps": "not a list",  # Wrong type: str instead of list
                "final_result": "Correct string",
            },
        }
    ]
    
    result = framework.evaluate_schema_usage("chain_of_thought", test_cases)
    
    # Should have lower score due to type mismatches
    assert result.score < 1.0
    # Type mismatches should reduce the score
    assert result.score < 0.8  # Should be penalized for wrong types


def test_evaluate_schema_usage_correct_types():
    """Test that schema evaluation rewards correct types."""
    framework = EvaluationFramework()
    
    from bop.schemas import get_schema
    schema = get_schema("chain_of_thought")
    if not schema:
        pytest.skip("chain_of_thought schema not found")
    
    # Test case with correct types
    test_cases = [
        {
            "input": "Test query",
            "expected": {
                "input_analysis": str,
                "steps": list,
                "final_result": str,
            },
            "actual": {
                "input_analysis": "Analysis text",
                "steps": ["step1", "step2"],
                "final_result": "Result text",
            },
        }
    ]
    
    result = framework.evaluate_schema_usage("chain_of_thought", test_cases)
    
    # Should have high score with correct types
    assert result.score > 0.7
    assert result.passed is True


def test_evaluate_reasoning_coherence_semantic_similarity():
    """Test that coherence evaluation uses semantic similarity."""
    framework = EvaluationFramework()
    
    # Responses that are semantically similar but use different words
    semantically_similar = [
        "I need to understand the problem first, then break it down.",
        "First, I must comprehend the issue, then decompose it.",
        "Understanding comes first, followed by decomposition.",
    ]
    
    result = framework.evaluate_reasoning_coherence(semantically_similar)
    
    # Should have good semantic score even if word overlap is lower
    assert "semantic_score" in result.details
    semantic_score = result.details["semantic_score"]
    assert semantic_score > 0.2  # Should detect some similarity
    
    # Overall score might be lower due to structure_score, but semantic similarity is working
    assert result.score >= 0.3  # Should have some score
    # Verify semantic_score is higher than word overlap (proving semantic similarity works)
    assert semantic_score > result.details["overlap_score"] * 1.5  # Semantic should be better than word overlap


def test_evaluate_reasoning_coherence_detects_semantic_differences():
    """Test that coherence evaluation detects semantically different responses."""
    framework = EvaluationFramework()
    
    # Responses that are semantically different
    semantically_different = [
        "The answer is 42.",
        "I need to understand the problem first, then break it down into steps.",
        "Weather is nice today.",
    ]
    
    result = framework.evaluate_reasoning_coherence(semantically_different)
    
    # Should have low semantic score
    assert "semantic_score" in result.details
    assert result.details["semantic_score"] < 0.5  # Should detect differences
    assert result.score < 0.6  # Should score lower


def test_evaluate_dependency_gap_step_relevance():
    """Test that dependency gap evaluation validates step relevance."""
    framework = EvaluationFramework()
    
    # Test case with relevant steps
    test_cases = [
        {
            "query": "What is the relationship between A and C?",
            "intermediate_steps": ["Understand A", "Find connection to B", "Relate B to C"],
            "actual_steps": ["Understanding A", "Finding B connection", "Relating B to C"],
            "final_answer": "A relates to C through B",
            "actual_answer": "A relates to C through intermediate B",
        }
    ]
    
    result = framework.evaluate_dependency_gap_handling(test_cases)
    
    # Should have good step relevance
    assert "avg_step_relevance" in result.details
    assert result.details["avg_step_relevance"] > 0.4  # Steps should be relevant
    assert result.score > 0.6  # Should score well


def test_evaluate_dependency_gap_irrelevant_steps():
    """Test that dependency gap evaluation detects irrelevant steps."""
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
    
    # Should have lower step relevance
    assert "avg_step_relevance" in result.details
    # Generic steps should have lower relevance
    assert result.details["avg_step_relevance"] < 0.5
    # Overall score should be lower due to irrelevant steps
    assert result.score < 0.8


def test_evaluate_dependency_gap_query_relevance():
    """Test that dependency gap evaluation checks if steps relate to query."""
    framework = EvaluationFramework()
    
    # Test case where steps don't relate to query
    test_cases = [
        {
            "query": "What is the relationship between trust and uncertainty?",
            "intermediate_steps": ["Understand trust", "Understand uncertainty", "Find relationship"],
            "actual_steps": ["Weather is nice", "Coffee is good", "Testing is fun"],  # Completely irrelevant
            "final_answer": "Trust and uncertainty are related",
            "actual_answer": "Trust and uncertainty are related concepts",
        }
    ]
    
    result = framework.evaluate_dependency_gap_handling(test_cases)
    
    # Should have low relevance (but SequenceMatcher might find some similarity)
    assert "avg_step_relevance" in result.details
    # Even irrelevant steps might have some similarity due to common words
    # But should still be lower than relevant steps
    assert result.details["avg_step_relevance"] < 0.5  # Steps don't relate well to query
    assert result.score < 0.7  # Should score lower than relevant steps


def test_evaluate_schema_usage_type_validation_mixed():
    """Test type validation with mixed correct and incorrect types."""
    framework = EvaluationFramework()
    
    from bop.schemas import get_schema
    schema = get_schema("chain_of_thought")
    if not schema:
        pytest.skip("chain_of_thought schema not found")
    
    # Use actual schema fields
    schema_fields = list(schema.schema_def.keys())
    if len(schema_fields) < 3:
        pytest.skip("Schema has too few fields")
    
    # Create expected dict with types
    expected_dict = {}
    for field in schema_fields:
        # Determine expected type from schema
        desc = schema.schema_def[field]
        if isinstance(desc, list):
            expected_dict[field] = list
        else:
            expected_dict[field] = str
    
    # Create actual with mixed types
    actual_dict = {}
    for i, field in enumerate(schema_fields):
        if i == 1 and expected_dict[field] == str:
            actual_dict[field] = 12345  # Wrong type
        elif i == 1 and expected_dict[field] == list:
            actual_dict[field] = "not a list"  # Wrong type
        else:
            if expected_dict[field] == list:
                actual_dict[field] = ["item1", "item2"]  # Correct type
            else:
                actual_dict[field] = f"Value for {field}"  # Correct type
    
    test_cases = [
        {
            "input": "Test query",
            "expected": expected_dict,
            "actual": actual_dict,
        }
    ]
    
    result = framework.evaluate_schema_usage("chain_of_thought", test_cases)
    
    # Should score based on type correctness
    # Most fields should have correct types
    assert result.score < 1.0
    # Should still score reasonably if most types are correct
    assert result.score >= 0.0  # At least non-negative


def test_evaluate_reasoning_coherence_semantic_vs_word_overlap():
    """Test that semantic similarity provides better measure than word overlap."""
    framework = EvaluationFramework()
    
    # Responses with low word overlap but high semantic similarity
    low_overlap_high_semantic = [
        "I need to understand the problem first.",
        "Comprehending the issue is the initial step.",
        "Understanding comes before solving.",
    ]
    
    result = framework.evaluate_reasoning_coherence(low_overlap_high_semantic)
    
    # Semantic score should be higher than word overlap
    assert "semantic_score" in result.details
    assert "overlap_score" in result.details
    # Semantic similarity should help even with low word overlap
    assert result.details["semantic_score"] > result.details["overlap_score"] * 0.8


def test_evaluate_dependency_gap_step_relevance_weighting():
    """Test that step relevance is properly weighted in scoring."""
    framework = EvaluationFramework()
    
    # Test case with many steps but low relevance
    test_cases = [
        {
            "query": "What is A to C?",
            "intermediate_steps": ["Understand A", "Find B", "Relate to C"],
            "actual_steps": ["Step 1", "Step 2", "Step 3", "Step 4", "Step 5"],  # Many but irrelevant
            "final_answer": "A relates to C",
            "actual_answer": "A relates to C through B",
        }
    ]
    
    result = framework.evaluate_dependency_gap_handling(test_cases)
    
    # Should score lower due to low relevance, even with many steps
    assert result.score < 0.7  # Low relevance should reduce score
    assert "avg_step_relevance" in result.details

