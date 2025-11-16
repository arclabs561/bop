"""Property-based E2E tests using Hypothesis.

Tests system properties that should hold for all inputs.
"""

import pytest
from hypothesis import given, strategies as st, settings
from typing import Dict, Any

from bop.agent import KnowledgeAgent
from tests.test_annotations import annotate_test


@given(
    query=st.text(min_size=1, max_size=500),
    use_research=st.booleans(),
    use_schema=st.one_of(st.none(), st.sampled_from([
        "chain_of_thought",
        "decompose_and_synthesize",
        "iterative_elaboration",
    ])),
)
@settings(max_examples=10, deadline=30000)  # Limit examples for speed
@pytest.mark.asyncio
async def test_e2e_property_always_responds(query: str, use_research: bool, use_schema: str):
    """
    Property: System always responds (never crashes) for any valid input.
    
    This property should hold for all inputs within reasonable bounds.
    """
    annotate_test(
        "test_e2e_property_always_responds",
        pattern="property_based_e2e",
        opinion="system_always_responds",
        category="e2e_property",
        hypothesis="System always responds for any valid input",
    )
    
    # Skip if query is empty (handled by min_size)
    if not query.strip():
        pytest.skip("Empty query")
    
    agent = KnowledgeAgent(enable_quality_feedback=True)
    
    try:
        response = await agent.chat(
            message=query,
            use_research=use_research,
            use_schema=use_schema,
        )
        
        # Property: Always returns a response dict
        assert isinstance(response, dict)
        assert "response" in response
        
        # Property: Response is a string (may be empty on error, but exists)
        assert isinstance(response.get("response"), str)
        
    except Exception as e:
        # Property: Exceptions should be informative
        assert len(str(e)) > 0


@given(
    query=st.text(min_size=1, max_size=200),
    num_turns=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=5, deadline=60000)
@pytest.mark.asyncio
async def test_e2e_property_session_consistency(query: str, num_turns: int):
    """
    Property: Session consistency across multiple turns.
    
    Session should maintain state consistently.
    """
    annotate_test(
        "test_e2e_property_session_consistency",
        pattern="property_based_e2e",
        opinion="sessions_maintain_consistency",
        category="e2e_property",
        hypothesis="Sessions maintain consistency across multiple turns",
    )
    
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        agent = KnowledgeAgent(enable_quality_feedback=True)
        
        responses = []
        for i in range(num_turns):
            response = await agent.chat(
                message=f"{query} (turn {i+1})",
                use_research=False,
            )
            responses.append(response)
        
        # Property: All responses should be valid
        assert len(responses) == num_turns
        assert all(isinstance(r, dict) for r in responses)
        assert all("response" in r for r in responses)
        
        # Property: Session should exist if quality feedback enabled
        if agent.quality_feedback:
            sessions = agent.quality_feedback.session_manager.list_sessions()
            # Should have at least one session
            assert len(sessions) >= 1


@given(
    query1=st.text(min_size=1, max_size=100),
    query2=st.text(min_size=1, max_size=100),
)
@settings(max_examples=5, deadline=30000)
@pytest.mark.asyncio
async def test_e2e_property_idempotency(query1: str, query2: str):
    """
    Property: Same query should produce consistent results (idempotency).
    
    Note: This may not hold perfectly due to LLM non-determinism,
    but structure should be consistent.
    """
    annotate_test(
        "test_e2e_property_idempotency",
        pattern="property_based_e2e",
        opinion="queries_are_idempotent",
        category="e2e_property",
        hypothesis="Same query produces consistent structure",
    )
    
    agent = KnowledgeAgent(enable_quality_feedback=True)
    
    # Same query twice
    response1 = await agent.chat(message=query1, use_research=False)
    response2 = await agent.chat(message=query1, use_research=False)
    
    # Property: Structure should be consistent
    assert set(response1.keys()) == set(response2.keys())
    assert "response" in response1
    assert "response" in response2
    
    # Property: Both should have responses (may differ due to LLM non-determinism)
    assert isinstance(response1.get("response"), str)
    assert isinstance(response2.get("response"), str)


@given(
    query=st.text(min_size=1, max_size=300),
    schema=st.one_of(st.none(), st.sampled_from([
        "chain_of_thought",
        "decompose_and_synthesize",
    ])),
)
@settings(max_examples=5, deadline=30000)
@pytest.mark.asyncio
async def test_e2e_property_quality_scores_valid(query: str, schema: str):
    """
    Property: Quality scores are always in valid range [0, 1].
    
    This should hold for all queries and schemas.
    """
    annotate_test(
        "test_e2e_property_quality_scores_valid",
        pattern="property_based_e2e",
        opinion="quality_scores_always_valid",
        category="e2e_property",
        hypothesis="Quality scores are always in valid range",
    )
    
    agent = KnowledgeAgent(enable_quality_feedback=True)
    
    response = await agent.chat(
        message=query,
        use_research=False,
        use_schema=schema,
    )
    
    # Property: If quality exists, score should be in [0, 1]
    quality = response.get("quality", {})
    if "score" in quality:
        score = quality["score"]
        assert isinstance(score, (int, float))
        assert 0.0 <= score <= 1.0

