"""Metamorphic testing properties for conversational AI.

Metamorphic testing: Test that transformations preserve properties.
"""

import pytest
from hypothesis import given, strategies as st, settings
from typing import List, Dict, Any

from bop.semantic_eval import SemanticEvaluator
from tests.test_annotations import annotate_test


# Metamorphic property: Adding context shouldn't decrease relevance
@given(
    query=st.text(min_size=10, max_size=200),
    response=st.text(min_size=20, max_size=500),
    context=st.text(min_size=5, max_size=100),
)
@settings(max_examples=15, deadline=None)
def test_metamorphic_adding_context_preserves_relevance(query: str, response: str, context: str):
    """
    METAMORPHIC: Adding context to query shouldn't decrease relevance.
    
    Pattern: metamorphic_testing
    Opinion: context_preserves_relevance
    Category: quality_metamorphic
    Hypothesis: Adding context to query shouldn't decrease relevance score.
    """
    annotate_test(
        "test_metamorphic_adding_context_preserves_relevance",
        pattern="metamorphic_testing",
        opinion="context_preserves_relevance",
        category="quality_metamorphic",
        hypothesis="Adding context to query shouldn't decrease relevance score.",
    )
    
    evaluator = SemanticEvaluator()
    
    # Original query
    original_judgment = evaluator.evaluate_relevance(query=query, response=response)
    
    # Query with added context
    contextual_query = f"{query} (context: {context})"
    contextual_judgment = evaluator.evaluate_relevance(query=contextual_query, response=response)
    
    # Adding context shouldn't dramatically decrease relevance
    # (It might increase or stay similar, but shouldn't drop significantly)
    assert contextual_judgment.score >= original_judgment.score - 0.3, (
        f"Adding context decreased relevance too much: {original_judgment.score:.2f} -> {contextual_judgment.score:.2f}"
    )


# Metamorphic property: Capitalization shouldn't affect evaluation
@given(
    query=st.text(min_size=10, max_size=200),
    response=st.text(min_size=20, max_size=500),
)
@settings(max_examples=15, deadline=None)
def test_metamorphic_case_insensitivity(query: str, response: str):
    """
    METAMORPHIC: Case changes shouldn't significantly affect evaluation.
    
    Pattern: metamorphic_testing
    Opinion: evaluation_is_case_insensitive
    Category: quality_metamorphic
    Hypothesis: Changing case shouldn't significantly change relevance score.
    """
    annotate_test(
        "test_metamorphic_case_insensitivity",
        pattern="metamorphic_testing",
        opinion="evaluation_is_case_insensitive",
        category="quality_metamorphic",
        hypothesis="Changing case shouldn't significantly change relevance score.",
    )
    
    evaluator = SemanticEvaluator()
    
    original_judgment = evaluator.evaluate_relevance(query=query, response=response)
    upper_judgment = evaluator.evaluate_relevance(query=query.upper(), response=response.upper())
    
    # Case changes shouldn't dramatically affect scores
    # (Some difference is OK due to concept extraction, but shouldn't be huge)
    score_diff = abs(original_judgment.score - upper_judgment.score)
    assert score_diff < 0.3, (
        f"Case change affected score too much: {original_judgment.score:.2f} vs {upper_judgment.score:.2f}"
    )


# Metamorphic property: Whitespace normalization shouldn't affect evaluation
@given(
    query=st.text(min_size=10, max_size=200),
    response=st.text(min_size=20, max_size=500),
)
@settings(max_examples=15, deadline=None)
def test_metamorphic_whitespace_normalization(query: str, response: str):
    """
    METAMORPHIC: Whitespace normalization shouldn't affect evaluation.
    
    Pattern: metamorphic_testing
    Opinion: evaluation_normalizes_whitespace
    Category: quality_metamorphic
    Hypothesis: Normalizing whitespace shouldn't significantly change scores.
    """
    annotate_test(
        "test_metamorphic_whitespace_normalization",
        pattern="metamorphic_testing",
        opinion="evaluation_normalizes_whitespace",
        category="quality_metamorphic",
        hypothesis="Normalizing whitespace shouldn't significantly change scores.",
    )
    
    evaluator = SemanticEvaluator()
    
    original_judgment = evaluator.evaluate_relevance(query=query, response=response)
    
    # Normalize whitespace (multiple spaces -> single space)
    import re
    normalized_query = re.sub(r'\s+', ' ', query.strip())
    normalized_response = re.sub(r'\s+', ' ', response.strip())
    
    normalized_judgment = evaluator.evaluate_relevance(query=normalized_query, response=normalized_response)
    
    # Whitespace normalization shouldn't dramatically affect scores
    score_diff = abs(original_judgment.score - normalized_judgment.score)
    assert score_diff < 0.2, (
        f"Whitespace normalization affected score: {original_judgment.score:.2f} vs {normalized_judgment.score:.2f}"
    )


# Metamorphic property: Response expansion shouldn't decrease completeness
@given(
    query=st.text(min_size=10, max_size=200),
    base_response=st.text(min_size=20, max_size=300),
    additional_info=st.text(min_size=10, max_size=200),
)
@settings(max_examples=10, deadline=None)
def test_metamorphic_response_expansion_preserves_completeness(
    query: str, base_response: str, additional_info: str
):
    """
    METAMORPHIC: Expanding response shouldn't decrease completeness.
    
    Pattern: metamorphic_testing
    Opinion: expansion_preserves_completeness
    Category: quality_metamorphic
    Hypothesis: Adding information to response shouldn't decrease completeness score.
    """
    annotate_test(
        "test_metamorphic_response_expansion_preserves_completeness",
        pattern="metamorphic_testing",
        opinion="expansion_preserves_completeness",
        category="quality_metamorphic",
        hypothesis="Adding information to response shouldn't decrease completeness score.",
    )
    
    evaluator = SemanticEvaluator()
    context = "test context for completeness evaluation"
    
    base_judgment = evaluator.evaluate_completeness(
        query=query,
        response=base_response,
        content_context=context,
    )
    
    expanded_response = f"{base_response} {additional_info}"
    expanded_judgment = evaluator.evaluate_completeness(
        query=query,
        response=expanded_response,
        content_context=context,
    )
    
    # Expanding response shouldn't decrease completeness
    # (It might increase or stay similar, but shouldn't drop)
    assert expanded_judgment.score >= base_judgment.score - 0.2, (
        f"Expanding response decreased completeness: {base_judgment.score:.2f} -> {expanded_judgment.score:.2f}"
    )

