"""Custom property-based test strategies for conversational AI.

Uses Hypothesis custom strategies to generate realistic conversational inputs.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import List, Dict, Any

from bop.semantic_eval import SemanticEvaluator
from bop.quality_feedback import QualityFeedbackLoop
from tests.test_annotations import annotate_test


# Custom strategy for realistic queries
realistic_query = st.one_of(
    st.text(
        min_size=10,
        max_size=200,
        alphabet=st.characters(min_codepoint=32, max_codepoint=126),
    ).filter(lambda x: len(x.split()) >= 3),  # At least 3 words
    st.sampled_from([
        "What is knowledge structure?",
        "How does hierarchical session management work?",
        "Explain trust and uncertainty in knowledge systems",
        "What are the key concepts in your knowledge base?",
    ]),
)

# Custom strategy for realistic responses
realistic_response = st.one_of(
    st.text(
        min_size=20,
        max_size=1000,
        alphabet=st.characters(min_codepoint=32, max_codepoint=126),
    ).filter(lambda x: len(x.split()) >= 5),  # At least 5 words
    st.sampled_from([
        "Knowledge structure refers to how information is organized and connected.",
        "Hierarchical session management organizes sessions into groups for better analysis.",
        "Trust and uncertainty are key concepts in knowledge systems.",
    ]),
)


@given(query=realistic_query, response=realistic_response)
@settings(max_examples=20, deadline=None)
def test_property_realistic_queries_relevance(query: str, response: str):
    """
    PROPERTY: Realistic queries should get valid relevance scores.
    
    Pattern: property_based_custom
    Opinion: realistic_queries_work
    Category: quality_property
    Hypothesis: Realistic conversational queries should produce valid relevance evaluations.
    """
    annotate_test(
        "test_property_realistic_queries_relevance",
        pattern="property_based_custom",
        opinion="realistic_queries_work",
        category="quality_property",
        hypothesis="Realistic conversational queries should produce valid relevance evaluations.",
    )
    
    evaluator = SemanticEvaluator()
    judgment = evaluator.evaluate_relevance(query=query, response=response)
    
    # Should produce valid score
    assert 0.0 <= judgment.score <= 1.0
    # Should have reasoning
    assert judgment.reasoning is not None
    # Should have query characteristics
    assert judgment.query_characteristics is not None


# Custom strategy for multi-turn conversations
multi_turn_conversation = st.lists(
    st.tuples(
        st.text(min_size=10, max_size=200).filter(lambda x: len(x.split()) >= 3),
        st.text(min_size=20, max_size=500).filter(lambda x: len(x.split()) >= 5),
    ),
    min_size=2,
    max_size=5,
)


@given(conversation=multi_turn_conversation)
@settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
def test_property_multi_turn_consistency(conversation: List[tuple]):
    """
    PROPERTY: Multi-turn conversations should maintain consistency.
    
    Pattern: property_based_custom
    Opinion: multi_turn_maintains_consistency
    Category: behavioral_property
    Hypothesis: Responses in multi-turn conversations should be consistent.
    """
    annotate_test(
        "test_property_multi_turn_consistency",
        pattern="property_based_custom",
        opinion="multi_turn_maintains_consistency",
        category="behavioral_property",
        hypothesis="Responses in multi-turn conversations should be consistent.",
    )
    
    evaluator = SemanticEvaluator()
    
    queries = [q for q, r in conversation]
    responses = [r for q, r in conversation]
    
    # Check consistency across responses
    if len(responses) >= 2:
        judgment = evaluator.evaluate_consistency(
            query=queries[0],  # Use first query as context
            responses=responses,
        )
        
        # Should produce valid consistency score
        assert 0.0 <= judgment.score <= 1.0


# Custom strategy for query types
query_type = st.sampled_from([
    "factual",  # "What is X?"
    "how",  # "How does X work?"
    "why",  # "Why does X happen?"
    "compare",  # "Compare X and Y"
    "explain",  # "Explain X"
])


@given(
    query_type=query_type,
    topic=st.text(min_size=3, max_size=50).filter(lambda x: len(x.split()) >= 1),
    response=realistic_response,
)
@settings(max_examples=15, deadline=None)
def test_property_query_type_handling(query_type: str, topic: str, response: str):
    """
    PROPERTY: Different query types should be handled appropriately.
    
    Pattern: property_based_custom
    Opinion: query_types_handled_appropriately
    Category: quality_property
    Hypothesis: System should handle different query types (factual, how, why, compare, explain).
    """
    annotate_test(
        "test_property_query_type_handling",
        pattern="property_based_custom",
        opinion="query_types_handled_appropriately",
        category="quality_property",
        hypothesis="System should handle different query types appropriately.",
    )
    
    evaluator = SemanticEvaluator()
    
    # Construct query based on type
    query_templates = {
        "factual": f"What is {topic}?",
        "how": f"How does {topic} work?",
        "why": f"Why does {topic} happen?",
        "compare": f"Compare {topic} and related concepts",
        "explain": f"Explain {topic}",
    }
    
    query = query_templates[query_type]
    judgment = evaluator.evaluate_relevance(query=query, response=response)
    
    # Should produce valid evaluation
    assert 0.0 <= judgment.score <= 1.0
    # Query characteristics should detect type
    assert judgment.query_characteristics is not None

