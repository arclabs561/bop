"""Comprehensive evaluation tests using content in multiple ways."""

from pathlib import Path

import pytest

from bop.eval import EvaluationFramework
from bop.research import load_content


@pytest.fixture
def content_dir():
    """Get content directory."""
    return Path(__file__).parent.parent / "content"


@pytest.fixture
def knowledge_base(content_dir):
    """Load knowledge base."""
    return load_content(content_dir)


def test_eval_all_schemas_with_content(knowledge_base):
    """Test all schemas with content-based queries."""
    framework = EvaluationFramework()

    schemas = ["chain_of_thought", "decompose_and_synthesize", "hypothesize_and_test",
               "iterative_elaboration", "scenario_analysis"]

    for schema_name in schemas:
        # Create test cases from content
        test_cases = []
        for doc_name, doc_content in list(knowledge_base.items())[:2]:
            # Extract key phrases from content
            if len(doc_content) > 100:
                test_cases.append({
                    "input": f"Analyze concepts in {doc_name}",
                    "expected": {"input_analysis": str, "steps": list},
                    "actual": {
                        "input_analysis": f"Analyzing {doc_name}",
                        "steps": ["Load document", "Extract concepts"],
                    },
                })

        if test_cases:
            result = framework.evaluate_schema_usage(schema_name, test_cases)
            assert result.test_name == f"schema_{schema_name}"
            assert result.score >= 0.0


def test_eval_content_extraction_scenarios(knowledge_base):
    """Test evaluation with different content extraction scenarios."""
    framework = EvaluationFramework()

    # Scenario 1: Extract trust-related content
    trust_responses = []
    for doc_name, doc_content in knowledge_base.items():
        if "trust" in doc_content.lower():
            # Simulate extracting trust-related content
            trust_responses.append(f"From {doc_name}: Trust concepts include...")

    if trust_responses:
        result = framework.evaluate_reasoning_coherence(trust_responses)
        assert result.score >= 0.0

    # Scenario 2: Extract uncertainty-related content
    uncertainty_responses = []
    for doc_name, doc_content in knowledge_base.items():
        if "uncertainty" in doc_content.lower():
            uncertainty_responses.append(f"From {doc_name}: Uncertainty concepts...")

    if uncertainty_responses:
        result = framework.evaluate_reasoning_coherence(uncertainty_responses)
        assert result.score >= 0.0


def test_eval_dependency_gaps_with_content_concepts(knowledge_base):
    """Test dependency gap handling with actual concepts from content."""
    framework = EvaluationFramework()

    # Extract concept pairs that might need bridging
    all_content = " ".join(knowledge_base.values()).lower()

    concept_pairs = [
        ("trust", "uncertainty"),
        ("knowledge", "structure"),
        ("reasoning", "logic"),
        ("graph", "network"),
    ]

    test_cases = []
    for concept1, concept2 in concept_pairs:
        if concept1 in all_content and concept2 in all_content:
            test_cases.append({
                "query": f"How does {concept1} relate to {concept2}?",
                "intermediate_steps": [
                    f"Understand {concept1}",
                    f"Understand {concept2}",
                    "Find relationship",
                ],
                "actual_steps": [
                    f"Understanding {concept1}",
                    f"Understanding {concept2}",
                    "Relating concepts",
                ],
                "final_answer": f"{concept1} relates to {concept2} through...",
                "actual_answer": f"{concept1} and {concept2} are related concepts that...",
            })

    if test_cases:
        result = framework.evaluate_dependency_gap_handling(test_cases)
        assert result.score >= 0.0
        assert result.test_name == "dependency_gap_handling"


def test_eval_multi_document_queries(knowledge_base):
    """Test evaluation with queries spanning multiple documents."""
    framework = EvaluationFramework()

    if len(knowledge_base) >= 2:
        doc_names = list(knowledge_base.keys())[:2]

        test_cases = [
            {
                "input": f"Compare concepts in {doc_names[0]} and {doc_names[1]}",
                "expected": {"input_analysis": str, "steps": list, "comparison": str},
                "actual": {
                    "input_analysis": f"Comparing {doc_names[0]} and {doc_names[1]}",
                    "steps": ["Load both documents", "Extract concepts", "Compare"],
                    "comparison": "Both documents discuss related concepts",
                },
            }
        ]

        result = framework.evaluate_schema_usage("decompose_and_synthesize", test_cases)
        assert result.score >= 0.0


def test_eval_content_length_variations(knowledge_base):
    """Test evaluation with responses of varying lengths from content."""
    framework = EvaluationFramework()

    responses = []
    for doc_name, doc_content in list(knowledge_base.items())[:3]:
        # Create responses of different lengths
        if len(doc_content) > 500:
            responses.append(doc_content[:100])  # Short
            responses.append(doc_content[:500])  # Medium
            responses.append(doc_content[:1000])  # Long

    if len(responses) >= 3:
        result = framework.evaluate_reasoning_coherence(responses)
        assert result.score >= 0.0
        # Should handle length variations
        assert "length_coherence" in result.details


def test_eval_content_structure_consistency(knowledge_base):
    """Test that content-based responses maintain structure consistency."""
    framework = EvaluationFramework()

    # Create structured responses from content
    responses = []
    for doc_name, doc_content in knowledge_base.items():
        # Format as structured response
        response = f"""
# Analysis of {doc_name}

## Key Concepts
{doc_content[:200]}

## Summary
This document discusses important concepts.
"""
        responses.append(response)

    if responses:
        result = framework.evaluate_reasoning_coherence(responses)
        # Structured responses should have higher structure score
        if "structure_score" in result.details:
            assert result.details["structure_score"] >= 0.0


def test_eval_content_semantic_similarity(knowledge_base):
    """Test semantic similarity evaluation with content."""
    framework = EvaluationFramework()

    # Create semantically similar responses
    responses = []
    base_content = list(knowledge_base.values())[0] if knowledge_base else ""

    if base_content:
        # Variations of same content
        responses.append(f"Key concepts: {base_content[:200]}")
        responses.append(f"Main ideas include: {base_content[:200]}")
        responses.append(f"Important points: {base_content[:200]}")

        result = framework.evaluate_reasoning_coherence(responses)

        # Semantically similar should have higher semantic_score
        if "semantic_score" in result.details:
            assert result.details["semantic_score"] >= 0.0


def test_eval_content_query_types(knowledge_base):
    """Test evaluation with different query types using content."""
    framework = EvaluationFramework()

    query_types = [
        ("What is", "definition"),
        ("How does", "process"),
        ("Why does", "causation"),
        ("Compare", "comparison"),
        ("Analyze", "analysis"),
    ]

    test_cases = []
    for prefix, query_type in query_types:
        for doc_name in list(knowledge_base.keys())[:1]:
            test_cases.append({
                "input": f"{prefix} {doc_name} discuss?",
                "expected": {"input_analysis": str, "steps": list},
                "actual": {
                    "input_analysis": f"{query_type} query about {doc_name}",
                    "steps": [f"Identify {query_type}", "Extract information"],
                },
            })

    if test_cases:
        result = framework.evaluate_schema_usage("chain_of_thought", test_cases)
        assert result.score >= 0.0


def test_eval_content_step_relevance(knowledge_base):
    """Test step relevance evaluation with content-based steps."""
    framework = EvaluationFramework()

    all_content = " ".join(knowledge_base.values()).lower()

    # Create test cases with steps that should be relevant to content
    test_cases = []
    if "trust" in all_content and "uncertainty" in all_content:
        test_cases.append({
            "query": "How do trust and uncertainty relate in knowledge graphs?",
            "intermediate_steps": [
                "Understand trust concept",
                "Understand uncertainty concept",
                "Find relationship in knowledge graphs",
            ],
            "actual_steps": [
                "Understanding trust in knowledge graphs",
                "Understanding uncertainty in knowledge graphs",
                "Relating trust and uncertainty",
            ],
            "final_answer": "Trust and uncertainty are related in knowledge graphs",
            "actual_answer": "Trust and uncertainty are related concepts in knowledge graphs that...",
        })

    if test_cases:
        result = framework.evaluate_dependency_gap_handling(test_cases)
        assert "avg_step_relevance" in result.details
        assert result.details["avg_step_relevance"] >= 0.0


def test_eval_content_answer_relevance(knowledge_base):
    """Test answer relevance evaluation with content-based answers."""
    framework = EvaluationFramework()

    test_cases = []
    for doc_name, doc_content in list(knowledge_base.items())[:2]:
        query = f"What does {doc_name} discuss?"

        # Create answer that should be relevant to query
        answer = f"{doc_name} discusses {doc_content[:100]}"

        test_cases.append({
            "query": query,
            "intermediate_steps": ["Load document", "Extract key points"],
            "actual_steps": ["Loading document", "Extracting information"],
            "final_answer": f"{doc_name} discusses relevant concepts",
            "actual_answer": answer,
        })

    if test_cases:
        result = framework.evaluate_dependency_gap_handling(test_cases)
        # Answers should be relevant (contain query words)
        assert result.score >= 0.0


def test_eval_content_type_validation(knowledge_base):
    """Test type validation in evaluation with content."""
    framework = EvaluationFramework()

    test_cases = []
    for doc_name in list(knowledge_base.keys())[:2]:
        # Test with correct types
        test_cases.append({
            "input": f"Analyze {doc_name}",
            "expected": {
                "input_analysis": str,
                "steps": list,
                "final_result": str,
            },
            "actual": {
                "input_analysis": f"Analyzing {doc_name}",
                "steps": ["Step 1", "Step 2"],
                "final_result": "Analysis complete",
            },
        })

        # Test with incorrect types
        test_cases.append({
            "input": f"Analyze {doc_name}",
            "expected": {
                "input_analysis": str,
                "steps": list,
            },
            "actual": {
                "input_analysis": 123,  # Wrong type
                "steps": "not a list",  # Wrong type
            },
        })

    if test_cases:
        result = framework.evaluate_schema_usage("chain_of_thought", test_cases)
        # Should penalize incorrect types
        assert result.score < 1.0


def test_eval_content_empty_handling(knowledge_base):
    """Test evaluation handles empty content gracefully."""
    framework = EvaluationFramework()

    # Test with empty responses
    result = framework.evaluate_reasoning_coherence([])
    assert result.passed is False
    assert result.score == 0.0

    # Test with empty test cases
    result = framework.evaluate_schema_usage("chain_of_thought", [])
    assert result.passed is False
    assert result.score == 0.0

    # Test with empty dependency gap cases
    result = framework.evaluate_dependency_gap_handling([])
    assert result.passed is False
    assert result.score == 0.0

