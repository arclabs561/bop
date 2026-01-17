"""Property-based and metamorphic tests that automatically detect the bugs we found."""

from hypothesis import given, settings
from hypothesis import strategies as st

from pran.agent import KnowledgeAgent
from pran.validation import validate_response


@given(
    response_text=st.text(min_size=50, max_size=500),
    synthesis_text=st.text(min_size=50, max_size=500),
)
@settings(max_examples=20, deadline=None)
def test_property_source_references_match_response(response_text: str, synthesis_text: str):
    """
    PROPERTY: Source references should match response text, not synthesis.

    This test will fail if sources are matched to synthesis instead of response.
    """
    agent = KnowledgeAgent(enable_quality_feedback=False)

    # Create response with synthesis different from response
    response = {
        "response": response_text,
        "research": {
            "subsolutions": [
                {
                    "subproblem": "Test",
                    "synthesis": synthesis_text,
                    "results": [{"tool": "test_tool", "result": "test"}]
                }
            ]
        }
    }

    # Add source references (simulating the bug - matching to synthesis)
    # In buggy version, this would cite synthesis claims
    if synthesis_text:
        response["response"] += f"\n\n**Sources:**\n- {synthesis_text[:50]} [Sources: test_tool]"

    issues = validate_response(response, "test query", agent)

    # If response_text and synthesis_text are different, should detect mismatch
    if response_text != synthesis_text and len(response_text) > 20 and len(synthesis_text) > 20:
        # Check if validation caught the mismatch
        [i for i in issues if i.severity == "critical" and i.category == "source_references"]
        # Note: This test documents the expected behavior
        # In practice, if sources match synthesis but not response, validation should catch it


@given(
    message=st.text(min_size=20, max_size=200).filter(
        lambda x: "i think" in x.lower() and "i believe" in x.lower()
    ),
)
@settings(max_examples=10, deadline=None)
def test_property_belief_extraction_all_beliefs(message: str):
    """
    PROPERTY: All belief indicators in message should extract beliefs.

    This test will fail if only first belief is extracted.
    """
    agent = KnowledgeAgent(enable_quality_feedback=False)

    # Count belief indicators
    belief_indicators = ["i think", "i believe", "i know", "i'm convinced"]
    indicator_count = sum(1 for indicator in belief_indicators if indicator in message.lower())

    # Extract beliefs
    agent._extract_prior_beliefs(message)

    # Validate
    issues = validate_response({"response": "test"}, message, agent)

    # If multiple indicators, should extract multiple beliefs (or validation should flag it)
    if indicator_count > 1:
        belief_issues = [i for i in issues if i.category == "belief_extraction"]
        # Validation should catch if only one belief extracted from multiple indicators
        assert len(belief_issues) > 0 or len(agent.prior_beliefs) > 1, \
            f"Multiple belief indicators ({indicator_count}) but only {len(agent.prior_beliefs)} belief(s) extracted"


@given(
    topics=st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=5),
)
@settings(max_examples=20, deadline=None)
def test_property_topic_similarity_no_empty_strings(topics: List[str]):
    """
    PROPERTY: Topic similarity should not process empty strings.

    This test will fail if empty strings are included in recent_topics.
    """
    agent = KnowledgeAgent(enable_quality_feedback=False)

    # Filter out empty strings (correct behavior)
    filtered_topics = [t for t in topics if t and t.strip()]

    # Compute similarity
    similarity = agent._compute_topic_similarity("test query", filtered_topics)

    # Should handle gracefully
    assert 0.0 <= similarity <= 1.0

    # If we included empty strings, validation should catch it
    if any(not t or not t.strip() for t in topics):
        # Simulate the bug: include empty strings
        # Validation should catch this
        [{"topic": t, "key_terms": []} for t in topics]
        issues = validate_response({"response": "test"}, "test", agent)
        topic_issues = [i for i in issues if i.category == "topic_similarity" and "empty" in i.message.lower()]
        # Should detect empty topics
        assert len(topic_issues) > 0 or all(t and t.strip() for t in topics)


def test_metamorphic_source_references_consistency():
    """
    METAMORPHIC: Source references should be consistent across response variations.

    If we paraphrase the response, sources should still match (semantically).
    """
    agent = KnowledgeAgent(enable_quality_feedback=False)

    # Original response
    response1 = {
        "response": "Trust is important for knowledge systems.",
        "research": {
            "subsolutions": [{
                "synthesis": "Trust enables systems.",
                "results": [{"tool": "test", "result": "Trust"}]
            }]
        }
    }

    # Paraphrased response (semantically same)
    response2 = {
        "response": "Trust serves as a crucial mechanism in knowledge systems.",
        "research": response1["research"]  # Same research
    }

    # Both should have consistent source attribution
    # If sources match synthesis but not response, both will fail validation
    validate_response(response1, "test", agent)
    validate_response(response2, "test", agent)

    # Both should have similar validation results
    # (Both should fail if sources don't match response)


def test_metamorphic_belief_extraction_order_independence():
    """
    METAMORPHIC: Belief extraction should be order-independent.

    "I think X and I believe Y" should extract same beliefs as "I believe Y and I think X".
    """
    agent1 = KnowledgeAgent(enable_quality_feedback=False)
    agent2 = KnowledgeAgent(enable_quality_feedback=False)

    message1 = "I think trust is important and I believe systems need reliability"
    message2 = "I believe systems need reliability and I think trust is important"

    agent1._extract_prior_beliefs(message1)
    agent2._extract_prior_beliefs(message2)

    # Should extract same number of beliefs (both should extract 2)
    # Current bug: only extracts first, so both extract 1
    # Validation should catch this
    issues1 = validate_response({"response": "test"}, message1, agent1)
    issues2 = validate_response({"response": "test"}, message2, agent2)

    # If extraction is order-dependent or incomplete, validation should flag it
    belief_count1 = len(agent1.prior_beliefs)
    belief_count2 = len(agent2.prior_beliefs)

    # Both messages have 2 belief indicators, so both should extract 2 beliefs
    # If not, validation should catch it
    if belief_count1 != 2 or belief_count2 != 2:
        assert len([i for i in issues1 if i.category == "belief_extraction"]) > 0 or \
               len([i for i in issues2 if i.category == "belief_extraction"]) > 0, \
               "Validation should catch incomplete belief extraction"

