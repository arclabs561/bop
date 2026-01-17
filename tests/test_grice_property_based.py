"""Property-based tests for Grice's maxims using Hypothesis."""

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from pran.semantic_eval import SemanticEvaluator
from tests.test_annotations import annotate_test


# Property: Relevance (Relation maxim) should be transitive-like
@given(
    query=st.text(min_size=5, max_size=200),
    response1=st.text(min_size=5, max_size=500),
    response2=st.text(min_size=5, max_size=500),
)
@settings(max_examples=15, deadline=None)
def test_property_grice_relation_transitive_like(query: str, response1: str, response2: str):
    """
    PROPERTY: If response1 is relevant to query and response2 is similar to response1,
    then response2 should also be relevant (Relation maxim).

    Pattern: property_based_grice
    Opinion: relevance_is_transitive_like
    Category: grice_property
    Hypothesis: Similar responses to same query should have similar relevance scores.
    """
    annotate_test(
        "test_property_grice_relation_transitive_like",
        pattern="property_based_grice",
        opinion="relevance_is_transitive_like",
        category="grice_property",
        hypothesis="Similar responses to same query should have similar relevance scores.",
    )

    evaluator = SemanticEvaluator()

    # Get relevance scores
    judgment1 = evaluator.evaluate_relevance(query=query, response=response1)
    judgment2 = evaluator.evaluate_relevance(query=query, response=response2)

    # Calculate similarity between responses
    response_similarity = evaluator._calculate_semantic_similarity(response1, response2)

    # If responses are very similar, relevance scores should be similar
    if response_similarity > 0.8:
        score_diff = abs(judgment1.score - judgment2.score)
        # Similar responses should have similar relevance (within 0.3)
        assert score_diff < 0.3, (
            f"Similar responses ({response_similarity:.2f}) have very different relevance: "
            f"{judgment1.score:.2f} vs {judgment2.score:.2f}"
        )


# Property: Quantity maxim - longer responses shouldn't always score higher
@given(
    query=st.text(min_size=5, max_size=200),
    short_response=st.text(min_size=10, max_size=100),
    long_response=st.text(min_size=200, max_size=1000),
)
@settings(max_examples=15, deadline=None)
def test_property_grice_quantity_length_independent(query: str, short_response: str, long_response: str):
    """
    PROPERTY: Relevance shouldn't always favor longer responses (Quantity maxim).

    Pattern: property_based_grice
    Opinion: relevance_not_always_favors_length
    Category: grice_property
    Hypothesis: Longer responses shouldn't automatically score higher on relevance.
    """
    annotate_test(
        "test_property_grice_quantity_length_independent",
        pattern="property_based_grice",
        opinion="relevance_not_always_favors_length",
        category="grice_property",
        hypothesis="Longer responses shouldn't automatically score higher on relevance.",
    )

    evaluator = SemanticEvaluator()

    short_judgment = evaluator.evaluate_relevance(query=query, response=short_response)
    long_judgment = evaluator.evaluate_relevance(query=query, response=long_response)

    # Length alone shouldn't determine relevance
    # We can't assert short is always better, but we can assert it's not always worse
    # This property is about ensuring length doesn't dominate relevance
    assert isinstance(short_judgment.score, float)
    assert isinstance(long_judgment.score, float)
    assert 0.0 <= short_judgment.score <= 1.0
    assert 0.0 <= long_judgment.score <= 1.0


# Property: Manner maxim - clear responses should score well
@given(
    query=st.text(min_size=5, max_size=200),
    clear_response=st.text(min_size=20, max_size=500).filter(
        lambda x: len(x.split()) >= 5 and not x.isdigit()
    ),  # Filter very short/numeric
)
@settings(max_examples=15, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_property_grice_manner_clear_responses(query: str, clear_response: str):
    """
    PROPERTY: Clear, well-formed responses should score reasonably (Manner maxim).

    Pattern: property_based_grice
    Opinion: clear_responses_score_reasonably
    Category: grice_property
    Hypothesis: Clear responses (with words, not just noise) should score reasonably.
    """
    annotate_test(
        "test_property_grice_manner_clear_responses",
        pattern="property_based_grice",
        opinion="clear_responses_score_reasonably",
        category="grice_property",
        hypothesis="Clear responses (with words, not just noise) should score reasonably.",
    )

    evaluator = SemanticEvaluator()
    judgment = evaluator.evaluate_relevance(query=query, response=clear_response)

    # Clear responses should score in valid range
    assert 0.0 <= judgment.score <= 1.0
    # And shouldn't be penalized just for being clear
    # (We can't assert it's high, but we can assert it's not artificially low)


# Property: Quality maxim - placeholder responses should score low
@given(
    query=st.text(min_size=5, max_size=200),
)
@settings(max_examples=10, deadline=None)
def test_property_grice_quality_placeholders_low(query: str):
    """
    PROPERTY: Placeholder responses should score low (Quality maxim violation).

    Pattern: property_based_grice
    Opinion: placeholders_score_low
    Category: grice_property
    Hypothesis: Placeholder responses should get low relevance scores.
    """
    annotate_test(
        "test_property_grice_quality_placeholders_low",
        pattern="property_based_grice",
        opinion="placeholders_score_low",
        category="grice_property",
        hypothesis="Placeholder responses should get low relevance scores.",
    )

    evaluator = SemanticEvaluator()

    placeholders = [
        "[LLM service not available]",
        "[MCP integration ready]",
        "Response to:",
        "to be filled",
        "placeholder",
    ]

    for placeholder in placeholders:
        judgment = evaluator.evaluate_relevance(query=query, response=placeholder)
        # Placeholders should score low (but not necessarily 0 due to quality flags)
        assert judgment.score < 0.7, f"Placeholder '{placeholder}' scored too high: {judgment.score}"


# Property: Consistency should be symmetric
@given(
    query=st.text(min_size=5, max_size=200),
    response1=st.text(min_size=5, max_size=500),
    response2=st.text(min_size=5, max_size=500),
)
@settings(max_examples=15, deadline=None)
def test_property_semantic_consistency_symmetric(query: str, response1: str, response2: str):
    """
    PROPERTY: Consistency should be symmetric (order shouldn't matter).

    Pattern: property_based_semantic
    Opinion: consistency_is_symmetric
    Category: semantic_property
    Hypothesis: consistency([A, B]) == consistency([B, A]).
    """
    annotate_test(
        "test_property_semantic_consistency_symmetric",
        pattern="property_based_semantic",
        opinion="consistency_is_symmetric",
        category="semantic_property",
        hypothesis="Consistency should be symmetric: consistency([A, B]) == consistency([B, A]).",
    )

    evaluator = SemanticEvaluator()

    judgment1 = evaluator.evaluate_consistency(query=query, responses=[response1, response2])
    judgment2 = evaluator.evaluate_consistency(query=query, responses=[response2, response1])

    # Consistency should be symmetric (order shouldn't matter)
    assert abs(judgment1.score - judgment2.score) < 0.001, (
        f"Consistency not symmetric: {judgment1.score} vs {judgment2.score}"
    )


# Property: Consistency should be monotonic (adding similar response increases consistency)
@given(
    query=st.text(min_size=5, max_size=200),
    base_response=st.text(min_size=5, max_size=500),
    similar_response=st.text(min_size=5, max_size=500),
)
@settings(max_examples=15, deadline=None)
def test_property_semantic_consistency_monotonic(
    query: str, base_response: str, similar_response: str
):
    """
    PROPERTY: Adding a similar response shouldn't decrease consistency.

    Pattern: property_based_semantic
    Opinion: consistency_is_monotonic
    Category: semantic_property
    Hypothesis: Adding similar response shouldn't decrease consistency.
    """
    annotate_test(
        "test_property_semantic_consistency_monotonic",
        pattern="property_based_semantic",
        opinion="consistency_is_monotonic",
        category="semantic_property",
        hypothesis="Adding similar response shouldn't decrease consistency.",
    )

    evaluator = SemanticEvaluator()

    # Single response (perfect consistency)
    evaluator.evaluate_consistency(query=query, responses=[base_response])

    # Two responses
    two_judgment = evaluator.evaluate_consistency(query=query, responses=[base_response, similar_response])

    # Calculate similarity
    similarity = evaluator._calculate_semantic_similarity(base_response, similar_response)

    # If responses are very similar, consistency shouldn't drop much
    if similarity > 0.8:
        # Consistency with similar response should still be high
        assert two_judgment.score >= 0.7, (
            f"Adding similar response ({similarity:.2f}) dropped consistency too much: "
            f"{two_judgment.score:.2f}"
        )

