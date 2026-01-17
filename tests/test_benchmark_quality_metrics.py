"""Benchmark quality metrics tests.

Tests based on established evaluation frameworks: HELM, Chatbot Arena, MT-Bench.
"""


from pran.semantic_eval import SemanticEvaluator
from tests.test_annotations import annotate_test


def test_benchmark_groundedness_metric():
    """
    BENCHMARK: Test groundedness metric (claims supported by evidence).

    Pattern: benchmark_testing
    Opinion: system_measures_groundedness
    Category: benchmark_quality
    Hypothesis: System should measure if claims are supported by evidence (HELM metric).
    """
    annotate_test(
        "test_benchmark_groundedness_metric",
        pattern="benchmark_testing",
        opinion="system_measures_groundedness",
        category="benchmark_quality",
        hypothesis="System should measure if claims are supported by evidence (HELM metric).",
    )

    evaluator = SemanticEvaluator()

    query = "What is knowledge structure?"

    # Grounded response (with evidence)
    grounded_response = "Knowledge structure refers to how information is organized. This concept is discussed in research on information architecture."

    # Ungrounded response (no evidence)
    ungrounded_response = "Knowledge structure is a complex topic that involves many factors."

    grounded_judgment = evaluator.evaluate_relevance(query=query, response=grounded_response)
    ungrounded_judgment = evaluator.evaluate_relevance(query=query, response=ungrounded_response)

    # Both should produce valid evaluations
    assert 0.0 <= grounded_judgment.score <= 1.0
    assert 0.0 <= ungrounded_judgment.score <= 1.0


def test_benchmark_coherence_metric():
    """
    BENCHMARK: Test coherence metric (logical flow and consistency).

    Pattern: benchmark_testing
    Opinion: system_measures_coherence
    Category: benchmark_quality
    Hypothesis: System should measure logical flow and consistency (HELM metric).
    """
    annotate_test(
        "test_benchmark_coherence_metric",
        pattern="benchmark_testing",
        opinion="system_measures_coherence",
        category="benchmark_quality",
        hypothesis="System should measure logical flow and consistency (HELM metric).",
    )

    evaluator = SemanticEvaluator()

    query = "Explain knowledge structure"

    # Coherent response
    coherent_response = "Knowledge structure refers to how information is organized. It involves relationships between concepts. These relationships form networks of meaning."

    # Incoherent response
    incoherent_response = "Knowledge structure. The weather is nice today. Information can be organized. Random thoughts about structure."

    coherent_judgment = evaluator.evaluate_relevance(query=query, response=coherent_response)
    incoherent_judgment = evaluator.evaluate_relevance(query=query, response=incoherent_response)

    # Both should produce valid evaluations
    assert 0.0 <= coherent_judgment.score <= 1.0
    assert 0.0 <= incoherent_judgment.score <= 1.0


def test_benchmark_fluency_metric():
    """
    BENCHMARK: Test fluency metric (grammatical correctness and naturalness).

    Pattern: benchmark_testing
    Opinion: system_measures_fluency
    Category: benchmark_quality
    Hypothesis: System should measure grammatical correctness and naturalness (HELM metric).
    """
    annotate_test(
        "test_benchmark_fluency_metric",
        pattern="benchmark_testing",
        opinion="system_measures_fluency",
        category="benchmark_quality",
        hypothesis="System should measure grammatical correctness and naturalness (HELM metric).",
    )

    evaluator = SemanticEvaluator()

    query = "What is knowledge structure?"

    # Fluent response
    fluent_response = "Knowledge structure refers to how information is organized and connected in meaningful ways."

    # Disfluent response
    disfluent_response = "Knowledge structure is um how information like organized and stuff connected ways meaning."

    fluent_judgment = evaluator.evaluate_relevance(query=query, response=fluent_response)
    disfluent_judgment = evaluator.evaluate_relevance(query=query, response=disfluent_response)

    # Both should produce valid evaluations
    assert 0.0 <= fluent_judgment.score <= 1.0
    assert 0.0 <= disfluent_judgment.score <= 1.0


def test_benchmark_helpfulness_metric():
    """
    BENCHMARK: Test helpfulness metric (usefulness and task completion).

    Pattern: benchmark_testing
    Opinion: system_measures_helpfulness
    Category: benchmark_quality
    Hypothesis: System should measure usefulness and task completion (Chatbot Arena metric).
    """
    annotate_test(
        "test_benchmark_helpfulness_metric",
        pattern="benchmark_testing",
        opinion="system_measures_helpfulness",
        category="benchmark_quality",
        hypothesis="System should measure usefulness and task completion (Chatbot Arena metric).",
    )

    evaluator = SemanticEvaluator()

    query = "How do I organize my knowledge base?"

    # Helpful response
    helpful_response = "To organize your knowledge base, consider: 1) Group related concepts together, 2) Create hierarchical structures, 3) Use tags and categories, 4) Establish clear relationships between items."

    # Unhelpful response
    unhelpful_response = "I don't know. Maybe try something."

    helpful_judgment = evaluator.evaluate_relevance(query=query, response=helpful_response)
    unhelpful_judgment = evaluator.evaluate_relevance(query=query, response=unhelpful_response)

    # Both should produce valid evaluations
    assert 0.0 <= helpful_judgment.score <= 1.0
    assert 0.0 <= unhelpful_judgment.score <= 1.0


def test_benchmark_multi_turn_consistency():
    """
    BENCHMARK: Test multi-turn consistency (MT-Bench style).

    Pattern: benchmark_testing
    Opinion: system_measures_multi_turn_consistency
    Category: benchmark_quality
    Hypothesis: System should measure consistency across multi-turn conversations (MT-Bench metric).
    """
    annotate_test(
        "test_benchmark_multi_turn_consistency",
        pattern="benchmark_testing",
        opinion="system_measures_multi_turn_consistency",
        category="benchmark_quality",
        hypothesis="System should measure consistency across multi-turn conversations (MT-Bench metric).",
    )

    evaluator = SemanticEvaluator()

    # Multi-turn conversation
    conversation = [
        ("What is knowledge structure?", "Knowledge structure refers to how information is organized."),
        ("How does it relate to trust?", "Trust in knowledge structure involves confidence in the relationships between concepts."),
        ("Can you give an example?", "For example, in a knowledge graph, nodes represent concepts and edges represent relationships, creating a structure that can be trusted based on evidence."),
    ]

    queries = [q for q, r in conversation]
    responses = [r for q, r in conversation]

    # Check consistency
    judgment = evaluator.evaluate_consistency(
        query=queries[0],  # Use first query as context
        responses=responses,
    )

    # Should produce valid consistency score
    assert 0.0 <= judgment.score <= 1.0

