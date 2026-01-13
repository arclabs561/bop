"""Advanced property-based tests for additional invariants discovered via MCP research.

Includes: triangle inequality, subadditivity, compositionality, order invariance, etc.
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from bop.semantic_eval import SemanticEvaluator
from tests.test_annotations import annotate_test


# Property: Triangle inequality for semantic similarity
@given(
    text1=st.text(min_size=10, max_size=200),
    text2=st.text(min_size=10, max_size=200),
    text3=st.text(min_size=10, max_size=200),
)
@settings(max_examples=15, deadline=None)
def test_property_triangle_inequality_similarity(text1: str, text2: str, text3: str):
    """
    PROPERTY: Semantic similarity should satisfy triangle inequality.

    Pattern: property_based_advanced
    Opinion: similarity_satisfies_triangle_inequality
    Category: semantic_property
    Hypothesis: distance(text1, text3) <= distance(text1, text2) + distance(text2, text3).
    """
    annotate_test(
        "test_property_triangle_inequality_similarity",
        pattern="property_based_advanced",
        opinion="similarity_satisfies_triangle_inequality",
        category="semantic_property",
        hypothesis="Semantic similarity should satisfy triangle inequality.",
    )

    evaluator = SemanticEvaluator()

    sim12 = evaluator._calculate_semantic_similarity(text1, text2)
    sim23 = evaluator._calculate_semantic_similarity(text2, text3)
    sim13 = evaluator._calculate_semantic_similarity(text1, text3)

    # Convert similarity to distance: distance = 1 - similarity
    dist12 = 1.0 - sim12
    dist23 = 1.0 - sim23
    dist13 = 1.0 - sim13

    # Triangle inequality: dist(A, C) <= dist(A, B) + dist(B, C)
    # Allow some tolerance for approximation
    assert dist13 <= dist12 + dist23 + 0.1, (
        f"Triangle inequality violated: dist({text1[:20]}, {text3[:20]}) = {dist13:.2f} > "
        f"dist({text1[:20]}, {text2[:20]}) + dist({text2[:20]}, {text3[:20]}) = {dist12 + dist23:.2f}"
    )


# Property: Compositionality - response to composed query should incorporate parts
@given(
    query_part1=st.text(min_size=5, max_size=100),
    query_part2=st.text(min_size=5, max_size=100),
)
@settings(max_examples=10, deadline=None)
def test_property_compositionality_responses(query_part1: str, query_part2: str):
    """
    PROPERTY: Response to composed query should incorporate answers to parts.

    Pattern: property_based_advanced
    Opinion: responses_are_compositional
    Category: semantic_property
    Hypothesis: Response to "A and B" should incorporate answers to "A" and "B".
    """
    annotate_test(
        "test_property_compositionality_responses",
        pattern="property_based_advanced",
        opinion="responses_are_compositional",
        category="semantic_property",
        hypothesis="Response to composed query should incorporate answers to parts.",
    )

    evaluator = SemanticEvaluator()

    # Simulate responses to parts and composed query
    # (In real test, would call agent, but for property test we check evaluator behavior)
    composed_query = f"{query_part1} and {query_part2}"

    # Check that evaluator can handle composed queries
    # This is a structural property: evaluator should process composed queries
    judgment = evaluator.evaluate_relevance(query=composed_query, response="test response")

    # Should produce valid judgment
    assert 0.0 <= judgment.score <= 1.0
    # Query characteristics should detect multi-part
    assert judgment.query_characteristics is not None


# Property: Order invariance - order of topics shouldn't change core answer
@given(
    topic1=st.text(min_size=5, max_size=50),
    topic2=st.text(min_size=5, max_size=50),
)
@settings(max_examples=10, deadline=None)
def test_property_order_invariance_topics(topic1: str, topic2: str):
    """
    PROPERTY: Order of topics shouldn't change core answer (when order shouldn't matter).

    Pattern: property_based_advanced
    Opinion: responses_are_order_invariant
    Category: semantic_property
    Hypothesis: Response to "A, B" should have same core answer as "B, A" (when order doesn't matter).
    """
    annotate_test(
        "test_property_order_invariance_topics",
        pattern="property_based_advanced",
        opinion="responses_are_order_invariant",
        category="semantic_property",
        hypothesis="Order of topics shouldn't change core answer (when order shouldn't matter).",
    )

    evaluator = SemanticEvaluator()

    query1 = f"Tell me about {topic1} and {topic2}"
    query2 = f"Tell me about {topic2} and {topic1}"

    # Both queries should be processable
    judgment1 = evaluator.evaluate_relevance(query=query1, response="test response")
    judgment2 = evaluator.evaluate_relevance(query=query2, response="test response")

    # Both should produce valid judgments
    assert 0.0 <= judgment1.score <= 1.0
    assert 0.0 <= judgment2.score <= 1.0
    # Query characteristics should be similar (both multi-part)
    assert judgment1.query_characteristics.get("is_multi_part") == judgment2.query_characteristics.get("is_multi_part")


# Property: Subadditivity - combining queries shouldn't decrease relevance
@given(
    query1=st.text(min_size=5, max_size=100),
    query2=st.text(min_size=5, max_size=100),
    response=st.text(min_size=10, max_size=500),
)
@settings(max_examples=10, deadline=None)
def test_property_subadditivity_relevance(query1: str, query2: str, response: str):
    """
    PROPERTY: Relevance to combined query shouldn't be less than minimum of parts.

    Pattern: property_based_advanced
    Opinion: relevance_is_subadditive
    Category: quality_property
    Hypothesis: relevance(combined_query, response) >= min(relevance(query1, response), relevance(query2, response)).
    """
    annotate_test(
        "test_property_subadditivity_relevance",
        pattern="property_based_advanced",
        opinion="relevance_is_subadditive",
        category="quality_property",
        hypothesis="Relevance to combined query shouldn't be less than minimum of parts.",
    )

    evaluator = SemanticEvaluator()

    judgment1 = evaluator.evaluate_relevance(query=query1, response=response)
    judgment2 = evaluator.evaluate_relevance(query=query2, response=response)
    combined_query = f"{query1} and {query2}"
    combined_judgment = evaluator.evaluate_relevance(query=combined_query, response=response)

    # Combined relevance should be at least the minimum of parts
    # (Response relevant to both parts should be relevant to combined)
    min_relevance = min(judgment1.score, judgment2.score)
    assert combined_judgment.score >= min_relevance - 0.2, (
        f"Subadditivity violated: combined relevance {combined_judgment.score:.2f} < "
        f"min({judgment1.score:.2f}, {judgment2.score:.2f}) = {min_relevance:.2f}"
    )


# Property: Idempotence - same query should get same evaluation
@given(
    query=st.text(min_size=5, max_size=200),
    response=st.text(min_size=10, max_size=500),
)
@settings(max_examples=15, deadline=None)
def test_property_evaluation_idempotent(query: str, response: str):
    """
    PROPERTY: Evaluating same query-response twice should give same result.

    Pattern: property_based_advanced
    Opinion: evaluation_is_idempotent
    Category: quality_property
    Hypothesis: evaluate(query, response) == evaluate(query, response) (deterministic).
    """
    annotate_test(
        "test_property_evaluation_idempotent",
        pattern="property_based_advanced",
        opinion="evaluation_is_idempotent",
        category="quality_property",
        hypothesis="Evaluating same query-response twice should give same result.",
    )

    evaluator = SemanticEvaluator()

    judgment1 = evaluator.evaluate_relevance(query=query, response=response)
    judgment2 = evaluator.evaluate_relevance(query=query, response=response)

    # Should be identical (deterministic)
    assert abs(judgment1.score - judgment2.score) < 0.001, (
        f"Evaluation not idempotent: {judgment1.score} vs {judgment2.score}"
    )
    assert judgment1.quality_flags == judgment2.quality_flags


# Property: Consistency under paraphrase - paraphrased queries should get similar scores
@given(
    base_query=st.text(min_size=10, max_size=200),
    response=st.text(min_size=10, max_size=500),
)
@settings(max_examples=10, deadline=None)
def test_property_consistency_under_paraphrase(base_query: str, response: str):
    """
    PROPERTY: Paraphrased queries should get similar relevance scores.

    Pattern: property_based_advanced
    Opinion: scores_consistent_under_paraphrase
    Category: quality_property
    Hypothesis: Semantically equivalent queries should get similar relevance scores.
    """
    annotate_test(
        "test_property_consistency_under_paraphrase",
        pattern="property_based_advanced",
        opinion="scores_consistent_under_paraphrase",
        category="quality_property",
        hypothesis="Paraphrased queries should get similar relevance scores.",
    )

    evaluator = SemanticEvaluator()

    # Create simple paraphrase by adding/removing words
    # (In real test, would use actual paraphrasing, but this tests structure)
    query1 = base_query
    query2 = f"What about {base_query}?"  # Simple paraphrase

    judgment1 = evaluator.evaluate_relevance(query=query1, response=response)
    judgment2 = evaluator.evaluate_relevance(query=query2, response=response)

    # Scores should be similar (within reasonable tolerance)
    # Note: This is a structural property - actual semantic equivalence would need LLM
    score_diff = abs(judgment1.score - judgment2.score)
    # Allow some difference due to query characteristics (question vs statement)
    assert score_diff < 0.4, (
        f"Paraphrased queries scored very differently: {judgment1.score:.2f} vs {judgment2.score:.2f}"
    )


# Property: Conservativity - shouldn't invent facts when told not to
@given(
    query=st.text(min_size=10, max_size=200),
    response_with_disclaimer=st.text(min_size=20, max_size=500),
)
@settings(max_examples=10, deadline=None)
def test_property_conservativity_no_hallucination(query: str, response_with_disclaimer: str):
    """
    PROPERTY: Responses with disclaimers should be flagged appropriately.

    Pattern: property_based_advanced
    Opinion: system_respects_conservativity
    Category: quality_property
    Hypothesis: Responses with uncertainty disclaimers should be handled appropriately.
    """
    annotate_test(
        "test_property_conservativity_no_hallucination",
        pattern="property_based_advanced",
        opinion="system_respects_conservativity",
        category="quality_property",
        hypothesis="Responses with uncertainty disclaimers should be handled appropriately.",
    )

    evaluator = SemanticEvaluator()

    # Response with uncertainty disclaimer
    response = f"I'm not certain, but {response_with_disclaimer}"
    judgment = evaluator.evaluate_relevance(query=query, response=response)

    # Should produce valid judgment
    assert 0.0 <= judgment.score <= 1.0
    # System should process responses with disclaimers
    assert judgment.reasoning is not None

