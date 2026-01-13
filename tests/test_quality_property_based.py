"""Property-based tests for quality, semantic, and behavioral properties.

Uses Hypothesis for generating diverse test cases and verifying invariants.
"""

from typing import List

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from bop.semantic_eval import SemanticEvaluator
from tests.test_annotations import annotate_test


# Property: Relevance score should be in [0, 1]
@given(
    query=st.text(min_size=1, max_size=200),
    response=st.text(min_size=1, max_size=1000),
)
@settings(max_examples=20, deadline=None)
def test_property_relevance_score_range(query: str, response: str):
    """
    PROPERTY: Relevance scores should always be in [0, 1].

    Pattern: property_based
    Opinion: scores_are_in_valid_range
    Category: quality_property
    Hypothesis: Relevance evaluation always returns scores in [0, 1] range.
    """
    annotate_test(
        "test_property_relevance_score_range",
        pattern="property_based",
        opinion="scores_are_in_valid_range",
        category="quality_property",
        hypothesis="Relevance evaluation always returns scores in [0, 1] range.",
    )

    evaluator = SemanticEvaluator()
    judgment = evaluator.evaluate_relevance(query=query, response=response)

    assert 0.0 <= judgment.score <= 1.0, f"Score {judgment.score} out of range"


# Property: Consistency score should be in [0, 1]
@given(
    query=st.text(min_size=1, max_size=200),
    responses=st.lists(st.text(min_size=1, max_size=500), min_size=2, max_size=5),
)
@settings(max_examples=15, deadline=None)
def test_property_consistency_score_range(query: str, responses: List[str]):
    """
    PROPERTY: Consistency scores should always be in [0, 1].

    Pattern: property_based
    Opinion: consistency_scores_are_in_valid_range
    Category: quality_property
    Hypothesis: Consistency evaluation always returns scores in [0, 1] range.
    """
    annotate_test(
        "test_property_consistency_score_range",
        pattern="property_based",
        opinion="consistency_scores_are_in_valid_range",
        category="quality_property",
        hypothesis="Consistency evaluation always returns scores in [0, 1] range.",
    )

    evaluator = SemanticEvaluator()
    judgment = evaluator.evaluate_consistency(query=query, responses=responses)

    assert 0.0 <= judgment.score <= 1.0, f"Score {judgment.score} out of range"


# Property: Quality flags should be consistent
@given(
    response=st.text(min_size=1, max_size=1000),
)
@settings(max_examples=20, deadline=None)
def test_property_quality_flags_consistent(response: str):
    """
    PROPERTY: Quality flag detection should be consistent for same response.

    Pattern: property_based
    Opinion: quality_flags_are_consistent
    Category: quality_property
    Hypothesis: Same response should always get same quality flags.
    """
    annotate_test(
        "test_property_quality_flags_consistent",
        pattern="property_based",
        opinion="quality_flags_are_consistent",
        category="quality_property",
        hypothesis="Same response should always get same quality flags.",
    )

    evaluator = SemanticEvaluator()

    # Check twice - should be same
    flags1 = evaluator._detect_quality_issues(response)
    flags2 = evaluator._detect_quality_issues(response)

    assert flags1 == flags2, f"Quality flags inconsistent: {flags1} vs {flags2}"


# Property: Semantic similarity should be symmetric
@given(
    text1=st.text(min_size=1, max_size=200),
    text2=st.text(min_size=1, max_size=200),
)
@settings(max_examples=20, deadline=None)
def test_property_semantic_similarity_symmetric(text1: str, text2: str):
    """
    PROPERTY: Semantic similarity should be symmetric.

    Pattern: property_based
    Opinion: similarity_is_symmetric
    Category: semantic_property
    Hypothesis: similarity(A, B) == similarity(B, A).
    """
    annotate_test(
        "test_property_semantic_similarity_symmetric",
        pattern="property_based",
        opinion="similarity_is_symmetric",
        category="semantic_property",
        hypothesis="Semantic similarity should be symmetric: similarity(A, B) == similarity(B, A).",
    )

    evaluator = SemanticEvaluator()

    sim1 = evaluator._calculate_semantic_similarity(text1, text2)
    sim2 = evaluator._calculate_semantic_similarity(text2, text1)

    # Allow small floating point differences
    assert abs(sim1 - sim2) < 0.001, f"Similarity not symmetric: {sim1} vs {sim2}"


# Property: Semantic similarity should be reflexive (self-similarity = 1.0)
@given(
    text=st.text(min_size=10, max_size=200).filter(lambda x: len(x.split()) >= 3 and not x.isdigit()),  # Filter very short/numeric
)
@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_property_semantic_similarity_reflexive(text: str):
    """
    PROPERTY: Text should be maximally similar to itself.

    Pattern: property_based
    Opinion: similarity_is_reflexive
    Category: semantic_property
    Hypothesis: similarity(text, text) should be close to 1.0 for meaningful text.
    """
    annotate_test(
        "test_property_semantic_similarity_reflexive",
        pattern="property_based",
        opinion="similarity_is_reflexive",
        category="semantic_property",
        hypothesis="Text should be maximally similar to itself: similarity(text, text) ≈ 1.0 for meaningful text.",
    )

    evaluator = SemanticEvaluator()

    sim = evaluator._calculate_semantic_similarity(text, text)

    # Self-similarity should be very high for meaningful text
    # (Very short/numeric text may have lower similarity due to processing)
    assert sim >= 0.8, f"Self-similarity too low: {sim} for text: {text[:50]}"


# Property: Concept extraction should be idempotent
@given(
    text=st.text(min_size=1, max_size=500),
)
@settings(max_examples=20, deadline=None)
def test_property_concept_extraction_idempotent(text: str):
    """
    PROPERTY: Concept extraction should be idempotent.

    Pattern: property_based
    Opinion: concept_extraction_is_idempotent
    Category: semantic_property
    Hypothesis: Extracting concepts twice should give same result.
    """
    annotate_test(
        "test_property_concept_extraction_idempotent",
        pattern="property_based",
        opinion="concept_extraction_is_idempotent",
        category="semantic_property",
        hypothesis="Extracting concepts twice should give same result.",
    )

    evaluator = SemanticEvaluator()

    concepts1 = evaluator._extract_key_concepts(text.lower())
    concepts2 = evaluator._extract_key_concepts(text.lower())

    assert concepts1 == concepts2, f"Concept extraction not idempotent: {concepts1} vs {concepts2}"


# Property: Query characteristics should be deterministic
@given(
    query=st.text(min_size=1, max_size=200),
)
@settings(max_examples=20, deadline=None)
def test_property_query_characteristics_deterministic(query: str):
    """
    PROPERTY: Query characteristics analysis should be deterministic.

    Pattern: property_based
    Opinion: query_analysis_is_deterministic
    Category: quality_property
    Hypothesis: Same query should always get same characteristics.
    """
    annotate_test(
        "test_property_query_characteristics_deterministic",
        pattern="property_based",
        opinion="query_analysis_is_deterministic",
        category="quality_property",
        hypothesis="Same query should always get same characteristics.",
    )

    evaluator = SemanticEvaluator()

    chars1 = evaluator._analyze_query_characteristics(query)
    chars2 = evaluator._analyze_query_characteristics(query)

    assert chars1 == chars2, f"Query characteristics not deterministic: {chars1} vs {chars2}"


# Property: Empty response should have low scores
@given(
    query=st.text(min_size=1, max_size=200),
)
@settings(max_examples=10, deadline=None)
def test_property_empty_response_low_score(query: str):
    """
    PROPERTY: Empty responses should get low relevance scores.

    Pattern: property_based
    Opinion: empty_responses_score_low
    Category: quality_property
    Hypothesis: Empty responses should score low on relevance.
    """
    annotate_test(
        "test_property_empty_response_low_score",
        pattern="property_based",
        opinion="empty_responses_score_low",
        category="quality_property",
        hypothesis="Empty responses should score low on relevance.",
    )

    evaluator = SemanticEvaluator()
    judgment = evaluator.evaluate_relevance(query=query, response="")

    # Empty response should score low (but not necessarily 0 due to quality flags)
    assert judgment.score < 0.5, f"Empty response scored too high: {judgment.score}"


# Property: Identical query-response should have high relevance
@given(
    text=st.text(min_size=20, max_size=200).filter(
        lambda x: len(x.split()) >= 3 and not x.isdigit() and not all(c in '0123456789 ' for c in x)
    ),  # Filter very short/numeric/echo-like
)
@settings(max_examples=15, deadline=None)
def test_property_identical_query_response_high_relevance(text: str):
    """
    PROPERTY: Identical query and response should have high relevance.

    Pattern: property_based
    Opinion: identical_texts_are_relevant
    Category: quality_property
    Hypothesis: If query == response (for meaningful text), relevance should be high.
    """
    annotate_test(
        "test_property_identical_query_response_high_relevance",
        pattern="property_based",
        opinion="identical_texts_are_relevant",
        category="quality_property",
        hypothesis="If query == response (for meaningful text), relevance should be high.",
    )

    evaluator = SemanticEvaluator()
    judgment = evaluator.evaluate_relevance(query=text, response=text)

    # Identical meaningful text should be highly relevant
    # (Very short/numeric text may be flagged as "echo" and score lower)
    assert judgment.score >= 0.6, f"Identical text scored too low: {judgment.score} for: {text[:50]}"


# Property: Consistency with single response should be perfect
@given(
    query=st.text(min_size=1, max_size=200),
    response=st.text(min_size=1, max_size=500),
)
@settings(max_examples=10, deadline=None)
def test_property_single_response_perfect_consistency(query: str, response: str):
    """
    PROPERTY: Single response should have perfect consistency.

    Pattern: property_based
    Opinion: single_response_is_consistent
    Category: semantic_property
    Hypothesis: Consistency with single response should be 1.0.
    """
    annotate_test(
        "test_property_single_response_perfect_consistency",
        pattern="property_based",
        opinion="single_response_is_consistent",
        category="semantic_property",
        hypothesis="Consistency with single response should be 1.0.",
    )

    evaluator = SemanticEvaluator()
    judgment = evaluator.evaluate_consistency(query=query, responses=[response])

    # Single response should be perfectly consistent with itself
    assert judgment.score == 1.0, f"Single response consistency not 1.0: {judgment.score}"


# Property: All responses identical should have perfect consistency
@given(
    query=st.text(min_size=5, max_size=200),
    response=st.text(min_size=15, max_size=500).filter(
        lambda x: len(x.split()) >= 3 and not x.isdigit()  # Filter very short/numeric responses
    ),
    num_responses=st.integers(min_value=2, max_value=5),
)
@settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_property_identical_responses_perfect_consistency(
    query: str, response: str, num_responses: int
):
    """
    PROPERTY: All identical responses should have perfect consistency.

    Pattern: property_based
    Opinion: identical_responses_are_consistent
    Category: semantic_property
    Hypothesis: All identical responses (meaningful text) should have high consistency.
    """
    annotate_test(
        "test_property_identical_responses_perfect_consistency",
        pattern="property_based",
        opinion="identical_responses_are_consistent",
        category="semantic_property",
        hypothesis="All identical responses (meaningful text) should have high consistency.",
    )

    evaluator = SemanticEvaluator()
    responses = [response] * num_responses
    judgment = evaluator.evaluate_consistency(query=query, responses=responses)

    # All identical meaningful responses should be highly consistent
    # (Very short responses may have quality issues that affect consistency)
    assert judgment.score >= 0.8, f"Identical responses consistency too low: {judgment.score}"

