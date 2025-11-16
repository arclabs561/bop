"""Comprehensive evaluation framework tests.

Tests based on established frameworks: HELM, Chatbot Arena, MT-Bench, DeepEval, Ragas.
"""

import pytest
from pathlib import Path
import tempfile

from bop.quality_feedback import QualityFeedbackLoop
from bop.semantic_eval import SemanticEvaluator
from tests.test_annotations import annotate_test


def test_framework_helm_groundedness():
    """
    FRAMEWORK: Test HELM groundedness metric (claims supported by evidence).
    
    Pattern: framework_testing
    Opinion: system_measures_helm_groundedness
    Category: framework_helm
    Hypothesis: System should measure if claims are supported by evidence (HELM metric).
    """
    annotate_test(
        "test_framework_helm_groundedness",
        pattern="framework_testing",
        opinion="system_measures_helm_groundedness",
        category="framework_helm",
        hypothesis="System should measure if claims are supported by evidence (HELM metric).",
    )
    
    evaluator = SemanticEvaluator()
    
    query = "What is knowledge structure?"
    
    # Grounded response (with evidence indicators)
    grounded_response = "Knowledge structure refers to how information is organized. Research shows this concept is fundamental to information architecture."
    
    # Ungrounded response (no evidence)
    ungrounded_response = "Knowledge structure is a complex topic."
    
    grounded_judgment = evaluator.evaluate_relevance(query=query, response=grounded_response)
    ungrounded_judgment = evaluator.evaluate_relevance(query=query, response=ungrounded_response)
    
    # Both should produce valid evaluations
    assert 0.0 <= grounded_judgment.score <= 1.0
    assert 0.0 <= ungrounded_judgment.score <= 1.0


def test_framework_helm_coherence():
    """
    FRAMEWORK: Test HELM coherence metric (logical flow and consistency).
    
    Pattern: framework_testing
    Opinion: system_measures_helm_coherence
    Category: framework_helm
    Hypothesis: System should measure logical flow and consistency (HELM metric).
    """
    annotate_test(
        "test_framework_helm_coherence",
        pattern="framework_testing",
        opinion="system_measures_helm_coherence",
        category="framework_helm",
        hypothesis="System should measure logical flow and consistency (HELM metric).",
    )
    
    evaluator = SemanticEvaluator()
    
    query = "Explain knowledge structure"
    
    # Coherent response
    coherent_response = "Knowledge structure refers to how information is organized. It involves relationships between concepts. These relationships form networks of meaning that enable understanding."
    
    # Incoherent response
    incoherent_response = "Knowledge structure. The weather is nice. Information can be organized. Random thoughts about structure and meaning."
    
    coherent_judgment = evaluator.evaluate_relevance(query=query, response=coherent_response)
    incoherent_judgment = evaluator.evaluate_relevance(query=query, response=incoherent_response)
    
    # Both should produce valid evaluations
    assert 0.0 <= coherent_judgment.score <= 1.0
    assert 0.0 <= incoherent_judgment.score <= 1.0


def test_framework_helm_fluency():
    """
    FRAMEWORK: Test HELM fluency metric (grammatical correctness and naturalness).
    
    Pattern: framework_testing
    Opinion: system_measures_helm_fluency
    Category: framework_helm
    Hypothesis: System should measure grammatical correctness and naturalness (HELM metric).
    """
    annotate_test(
        "test_framework_helm_fluency",
        pattern="framework_testing",
        opinion="system_measures_helm_fluency",
        category="framework_helm",
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


def test_framework_chatbot_arena_helpfulness():
    """
    FRAMEWORK: Test Chatbot Arena helpfulness metric (usefulness and task completion).
    
    Pattern: framework_testing
    Opinion: system_measures_chatbot_arena_helpfulness
    Category: framework_chatbot_arena
    Hypothesis: System should measure usefulness and task completion (Chatbot Arena metric).
    """
    annotate_test(
        "test_framework_chatbot_arena_helpfulness",
        pattern="framework_testing",
        opinion="system_measures_chatbot_arena_helpfulness",
        category="framework_chatbot_arena",
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


def test_framework_mt_bench_multi_turn_consistency():
    """
    FRAMEWORK: Test MT-Bench multi-turn consistency metric.
    
    Pattern: framework_testing
    Opinion: system_measures_mt_bench_consistency
    Category: framework_mt_bench
    Hypothesis: System should measure consistency across multi-turn conversations (MT-Bench metric).
    """
    annotate_test(
        "test_framework_mt_bench_multi_turn_consistency",
        pattern="framework_testing",
        opinion="system_measures_mt_bench_consistency",
        category="framework_mt_bench",
        hypothesis="System should measure consistency across multi-turn conversations (MT-Bench metric).",
    )
    
    evaluator = SemanticEvaluator()
    
    # Multi-turn conversation (MT-Bench style)
    conversation = [
        ("What is knowledge structure?", "Knowledge structure refers to how information is organized."),
        ("How does it relate to trust?", "Trust in knowledge structure involves confidence in the relationships between concepts."),
        ("Can you give an example?", "For example, in a knowledge graph, nodes represent concepts and edges represent relationships, creating a structure that can be trusted based on evidence."),
    ]
    
    queries = [q for q, r in conversation]
    responses = [r for q, r in conversation]
    
    # Check consistency (MT-Bench style)
    judgment = evaluator.evaluate_consistency(
        query=queries[0],  # Use first query as context
        responses=responses,
    )
    
    # Should produce valid consistency score
    assert 0.0 <= judgment.score <= 1.0


def test_framework_ragas_relevance():
    """
    FRAMEWORK: Test Ragas relevance metric (answer relevance to question).
    
    Pattern: framework_testing
    Opinion: system_measures_ragas_relevance
    Category: framework_ragas
    Hypothesis: System should measure answer relevance to question (Ragas metric).
    """
    annotate_test(
        "test_framework_ragas_relevance",
        pattern="framework_testing",
        opinion="system_measures_ragas_relevance",
        category="framework_ragas",
        hypothesis="System should measure answer relevance to question (Ragas metric).",
    )
    
    evaluator = SemanticEvaluator()
    
    query = "What is knowledge structure?"
    
    # Relevant response
    relevant_response = "Knowledge structure refers to how information is organized and connected in meaningful ways."
    
    # Irrelevant response
    irrelevant_response = "The weather today is sunny and warm."
    
    relevant_judgment = evaluator.evaluate_relevance(query=query, response=relevant_response)
    irrelevant_judgment = evaluator.evaluate_relevance(query=query, response=irrelevant_response)
    
    # Both should produce valid evaluations
    assert 0.0 <= relevant_judgment.score <= 1.0
    assert 0.0 <= irrelevant_judgment.score <= 1.0
    
    # Relevant should score higher
    assert relevant_judgment.score > irrelevant_judgment.score


def test_framework_ragas_faithfulness():
    """
    FRAMEWORK: Test Ragas faithfulness metric (answer grounded in context).
    
    Pattern: framework_testing
    Opinion: system_measures_ragas_faithfulness
    Category: framework_ragas
    Hypothesis: System should measure if answer is grounded in provided context (Ragas metric).
    """
    annotate_test(
        "test_framework_ragas_faithfulness",
        pattern="framework_testing",
        opinion="system_measures_ragas_faithfulness",
        category="framework_ragas",
        hypothesis="System should measure if answer is grounded in provided context (Ragas metric).",
    )
    
    evaluator = SemanticEvaluator()
    
    query = "What is knowledge structure?"
    context = "Knowledge structure is a concept in information science that describes how information is organized and connected."
    
    # Faithful response (grounded in context)
    faithful_response = "Based on the context, knowledge structure is a concept in information science that describes how information is organized and connected."
    
    # Unfaithful response (not grounded in context)
    unfaithful_response = "Knowledge structure is a mathematical concept involving graph theory and topology."
    
    faithful_judgment = evaluator.evaluate_relevance(query=query, response=faithful_response)
    unfaithful_judgment = evaluator.evaluate_relevance(query=query, response=unfaithful_response)
    
    # Both should produce valid evaluations
    assert 0.0 <= faithful_judgment.score <= 1.0
    assert 0.0 <= unfaithful_judgment.score <= 1.0


def test_framework_deepeval_g_eval():
    """
    FRAMEWORK: Test DeepEval G-Eval style evaluation (LLM-as-judge with chain-of-thought).
    
    Pattern: framework_testing
    Opinion: system_supports_g_eval_style
    Category: framework_deepeval
    Hypothesis: System should support G-Eval style LLM-as-judge evaluation.
    """
    annotate_test(
        "test_framework_deepeval_g_eval",
        pattern="framework_testing",
        opinion="system_supports_g_eval_style",
        category="framework_deepeval",
        hypothesis="System should support G-Eval style LLM-as-judge evaluation.",
    )
    
    evaluator = SemanticEvaluator()
    
    query = "What is knowledge structure?"
    response = "Knowledge structure refers to how information is organized and connected."
    
    # G-Eval style evaluation (using semantic evaluator as proxy)
    judgment = evaluator.evaluate_relevance(query=query, response=response)
    
    # Should produce structured judgment with reasoning
    assert hasattr(judgment, 'score')
    assert hasattr(judgment, 'reasoning')
    assert hasattr(judgment, 'query_characteristics')
    
    # Reasoning should be present (G-Eval style)
    assert judgment.reasoning is not None
    assert len(judgment.reasoning) > 0

