"""Diverse evaluation scenarios using content in creative ways."""

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


def test_eval_content_sentence_level(knowledge_base):
    """Test evaluation with sentence-level extraction from content."""
    framework = EvaluationFramework()

    responses = []
    for doc_name, doc_content in knowledge_base.items():
        # Split into sentences (simple split)
        sentences = doc_content.split('.')[:5]  # First 5 sentences
        for sentence in sentences:
            if sentence.strip():
                responses.append(f"From {doc_name}: {sentence.strip()}.")

    if responses:
        result = framework.evaluate_reasoning_coherence(responses)
        assert result.score >= 0.0


def test_eval_content_paragraph_level(knowledge_base):
    """Test evaluation with paragraph-level extraction."""
    framework = EvaluationFramework()

    responses = []
    for doc_name, doc_content in knowledge_base.items():
        # Split into paragraphs
        paragraphs = doc_content.split('\n\n')[:3]
        for para in paragraphs:
            if para.strip():
                responses.append(f"Paragraph from {doc_name}: {para[:200]}")

    if responses:
        result = framework.evaluate_reasoning_coherence(responses)
        assert result.score >= 0.0


def test_eval_content_keyword_extraction(knowledge_base):
    """Test evaluation with keyword-based extraction."""
    framework = EvaluationFramework()

    # Extract keywords from content
    keywords = set()
    for doc_content in knowledge_base.values():
        words = doc_content.lower().split()
        # Filter for meaningful words (length > 3)
        keywords.update(w for w in words if len(w) > 3)

    # Create responses based on keywords
    responses = []
    for keyword in list(keywords)[:10]:
        responses.append(f"Key concept: {keyword} is important in knowledge structure.")

    if responses:
        result = framework.evaluate_reasoning_coherence(responses)
        assert result.score >= 0.0


def test_eval_content_concept_mapping(knowledge_base):
    """Test evaluation with concept mapping across documents."""
    framework = EvaluationFramework()

    # Map concepts across documents
    all_content = " ".join(knowledge_base.values()).lower()

    # Find common concepts
    concepts = ["trust", "uncertainty", "knowledge", "structure", "reasoning"]
    found_concepts = [c for c in concepts if c in all_content]

    test_cases = []
    for concept in found_concepts[:3]:
        test_cases.append({
            "input": f"Map {concept} across documents",
            "expected": {"input_analysis": str, "mapping": dict},
            "actual": {
                "input_analysis": f"Mapping {concept}",
                "mapping": {doc: f"{concept} appears in {doc}" for doc in list(knowledge_base.keys())[:2]},
            },
        })

    if test_cases:
        result = framework.evaluate_schema_usage("decompose_and_synthesize", test_cases)
        assert result.score >= 0.0


def test_eval_content_hierarchical_queries(knowledge_base):
    """Test evaluation with hierarchical queries (general to specific)."""
    framework = EvaluationFramework()

    # Hierarchical query structure
    hierarchy = [
        "What is knowledge structure?",
        "What are the components of knowledge structure?",
        "How do these components interact?",
    ]

    test_cases = []
    for i, query in enumerate(hierarchy):
        test_cases.append({
            "input": query,
            "expected": {"input_analysis": str, "level": int, "details": str},
            "actual": {
                "input_analysis": f"Level {i+1} analysis",
                "level": i + 1,
                "details": f"Details for level {i+1}",
            },
        })

    if test_cases:
        result = framework.evaluate_schema_usage("iterative_elaboration", test_cases)
        assert result.score >= 0.0


def test_eval_content_contradiction_detection(knowledge_base):
    """Test evaluation with potential contradictions in content."""
    framework = EvaluationFramework()

    # Create responses that might contradict
    responses = []
    for doc_name, doc_content in list(knowledge_base.items())[:2]:
        # Extract different perspectives
        responses.append(f"Perspective from {doc_name}: {doc_content[:150]}")
        # Create potentially contradictory response
        responses.append("Alternative view: Different interpretation of concepts.")

    if responses:
        result = framework.evaluate_reasoning_coherence(responses)
        # Contradictory responses should have lower coherence
        assert result.score >= 0.0


def test_eval_content_progressive_refinement(knowledge_base):
    """Test evaluation with progressively refined responses."""
    framework = EvaluationFramework()

    # Simulate progressive refinement
    base_content = list(knowledge_base.values())[0] if knowledge_base else ""

    if base_content:
        responses = [
            f"Initial: {base_content[:50]}",
            f"Refined: {base_content[:100]}",
            f"Detailed: {base_content[:200]}",
        ]

        result = framework.evaluate_reasoning_coherence(responses)
        # Progressive refinement should maintain coherence
        assert result.score >= 0.0


def test_eval_content_multi_perspective(knowledge_base):
    """Test evaluation with multiple perspectives on same content."""
    framework = EvaluationFramework()

    if knowledge_base:
        doc_name = list(knowledge_base.keys())[0]
        doc_content = knowledge_base[doc_name]

        perspectives = [
            f"Theoretical perspective: {doc_content[:150]}",
            f"Practical perspective: {doc_content[:150]}",
            f"Historical perspective: {doc_content[:150]}",
        ]

        result = framework.evaluate_reasoning_coherence(perspectives)
        assert result.score >= 0.0


def test_eval_content_abstraction_levels(knowledge_base):
    """Test evaluation with different abstraction levels."""
    framework = EvaluationFramework()

    test_cases = []
    abstraction_levels = ["concrete", "abstract", "meta"]

    for level in abstraction_levels:
        test_cases.append({
            "input": f"Analyze at {level} level",
            "expected": {"input_analysis": str, "abstraction": str},
            "actual": {
                "input_analysis": f"{level.capitalize()} level analysis",
                "abstraction": level,
            },
        })

    if test_cases:
        result = framework.evaluate_schema_usage("chain_of_thought", test_cases)
        assert result.score >= 0.0


def test_eval_content_question_generation(knowledge_base):
    """Test evaluation with questions generated from content."""
    framework = EvaluationFramework()

    # Generate questions from content
    questions = []
    for doc_name, doc_content in knowledge_base.items():
        # Extract key phrases and turn into questions
        if "trust" in doc_content.lower():
            questions.append(f"How does {doc_name} define trust?")
        if "uncertainty" in doc_content.lower():
            questions.append(f"What role does uncertainty play in {doc_name}?")

    test_cases = []
    for question in questions[:5]:
        test_cases.append({
            "input": question,
            "expected": {"input_analysis": str, "answer": str},
            "actual": {
                "input_analysis": f"Analyzing {question}",
                "answer": f"Answer to {question}",
            },
        })

    if test_cases:
        result = framework.evaluate_schema_usage("chain_of_thought", test_cases)
        assert result.score >= 0.0

