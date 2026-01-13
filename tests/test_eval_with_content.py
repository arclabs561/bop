"""Tests for evaluation framework using actual content files."""

from pathlib import Path

import pytest

from bop.agent import KnowledgeAgent
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


def test_load_content(content_dir):
    """Test loading content files."""
    content = load_content(content_dir)
    assert isinstance(content, dict)
    assert len(content) > 0
    # Should have at least shape-of-ideas and reasoning-theory
    assert "shape-of-ideas" in content or "reasoning-theory" in content


def test_eval_with_content_queries(knowledge_base):
    """Test evaluation with queries derived from content."""
    framework = EvaluationFramework()

    # Create test cases based on content
    test_cases = []

    # Extract key concepts from content
    for doc_name, doc_content in knowledge_base.items():
        # Create queries based on document content
        if "trust" in doc_content.lower():
            test_cases.append({
                "input": f"What does {doc_name} say about trust?",
                "expected": {"input_analysis": str, "steps": list, "final_result": str},
                "actual": {
                    "input_analysis": f"Querying {doc_name} about trust",
                    "steps": ["Load document", "Extract trust concepts"],
                    "final_result": "Trust is discussed in the document",
                },
            })

        if "uncertainty" in doc_content.lower():
            test_cases.append({
                "input": f"How does {doc_name} handle uncertainty?",
                "expected": {"input_analysis": str, "steps": list, "final_result": str},
                "actual": {
                    "input_analysis": f"Querying {doc_name} about uncertainty",
                    "steps": ["Load document", "Extract uncertainty concepts"],
                    "final_result": "Uncertainty is discussed in the document",
                },
            })

    if test_cases:
        result = framework.evaluate_schema_usage("chain_of_thought", test_cases)
        assert result.test_name == "schema_chain_of_thought"
        assert result.score >= 0.0


def test_eval_reasoning_coherence_with_content(knowledge_base):
    """Test reasoning coherence evaluation with content-based responses."""
    framework = EvaluationFramework()

    # Generate responses based on content
    responses = []
    for doc_name, doc_content in list(knowledge_base.items())[:3]:
        # Create a response based on document
        response = f"Based on {doc_name}, the key concepts include: {doc_content[:200]}"
        responses.append(response)

    if responses:
        result = framework.evaluate_reasoning_coherence(responses)
        assert result.test_name == "reasoning_coherence"
        assert result.score >= 0.0


def test_eval_dependency_gaps_with_content(knowledge_base):
    """Test dependency gap handling with content-based queries."""
    framework = EvaluationFramework()

    # Create test cases that require bridging concepts
    test_cases = []

    # Find concepts that might need bridging
    all_content = " ".join(knowledge_base.values())

    if "trust" in all_content.lower() and "uncertainty" in all_content.lower():
        test_cases.append({
            "query": "How does trust relate to uncertainty?",
            "intermediate_steps": [
                "Understand trust concept",
                "Understand uncertainty concept",
                "Find relationship",
            ],
            "actual_steps": [
                "Understanding trust",
                "Understanding uncertainty",
                "Relating concepts",
            ],
            "final_answer": "Trust and uncertainty are related through...",
            "actual_answer": "Trust and uncertainty are related concepts that...",
        })

    if test_cases:
        result = framework.evaluate_dependency_gap_handling(test_cases)
        assert result.test_name == "dependency_gap_handling"
        assert result.score >= 0.0


@pytest.mark.asyncio
async def test_agent_with_content_queries(knowledge_base):
    """Test agent with queries derived from content."""
    agent = KnowledgeAgent()
    agent.llm_service = None  # Use fallback

    # Test with queries based on content
    for doc_name in list(knowledge_base.keys())[:2]:
        query = f"What are the main concepts in {doc_name}?"
        response = await agent.chat(query, use_schema="chain_of_thought", use_research=False)

        assert "response" in response
        assert response["message"] == query
        assert response["schema_used"] == "chain_of_thought"


def test_eval_multiple_schemas_with_content(knowledge_base):
    """Test evaluation with multiple schemas using content."""
    framework = EvaluationFramework()

    # Test different schemas with content-based queries
    schemas = ["chain_of_thought", "decompose_and_synthesize", "hypothesize_and_test"]

    for schema_name in schemas:
        test_cases = [
            {
                "input": f"Analyze the concepts in {list(knowledge_base.keys())[0]}",
                "expected": {"input_analysis": str},
                "actual": {
                    "input_analysis": "Analyzing concepts in document",
                },
            }
        ]

        result = framework.evaluate_schema_usage(schema_name, test_cases)
        assert result.test_name == f"schema_{schema_name}"
        assert result.score >= 0.0

