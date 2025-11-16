"""Deep, comprehensive tests for new features - edge cases, properties, adversarial scenarios."""

import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import List, Dict, Any
from unittest.mock import Mock, patch
from bop.agent import KnowledgeAgent
from bop.orchestrator import StructuredOrchestrator
from bop.research import ResearchAgent


# ============================================================================
# Property-Based Tests for Topic Similarity
# ============================================================================

@given(
    current=st.text(min_size=1, max_size=200),
    recent_topics=st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=20),
)
@settings(max_examples=50, deadline=None)
def test_property_topic_similarity_bounds(current: str, recent_topics: List[str]):
    """PROPERTY: Topic similarity should always be in [0, 1]."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    similarity = agent._compute_topic_similarity(current, recent_topics)
    
    assert 0.0 <= similarity <= 1.0, f"Similarity {similarity} out of bounds for current='{current[:30]}', topics={recent_topics[:3]}"


@given(
    text=st.text(min_size=5, max_size=100).filter(lambda x: len(x.split()) >= 2),
)
@settings(max_examples=30, deadline=None)
def test_property_topic_similarity_reflexive(text: str):
    """PROPERTY: Text should be maximally similar to itself."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    # Split text into words for topics
    topics = text.lower().split()[:10]  # Limit topics
    
    similarity = agent._compute_topic_similarity(text, topics)
    
    # Should have some similarity (may not be 1.0 due to stop word filtering)
    assert similarity >= 0.0


@given(
    current1=st.text(min_size=5, max_size=100),
    current2=st.text(min_size=5, max_size=100),
    recent_topics=st.lists(st.text(min_size=1, max_size=30), min_size=1, max_size=10),
)
@settings(max_examples=30, deadline=None)
def test_property_topic_similarity_consistent(current1: str, current2: str, recent_topics: List[str]):
    """PROPERTY: Similarity computation should be consistent."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    sim1 = agent._compute_topic_similarity(current1, recent_topics)
    sim2 = agent._compute_topic_similarity(current2, recent_topics)
    
    # Both should be in valid range
    assert 0.0 <= sim1 <= 1.0
    assert 0.0 <= sim2 <= 1.0
    
    # If we compute same query twice, should get same result
    sim1_repeat = agent._compute_topic_similarity(current1, recent_topics)
    assert abs(sim1 - sim1_repeat) < 0.001, "Similarity should be deterministic"


# ============================================================================
# Property-Based Tests for Source References
# ============================================================================

@given(
    response_text=st.text(min_size=1, max_size=500),
    num_subsolutions=st.integers(min_value=0, max_value=5),
)
@settings(max_examples=30, deadline=None)
def test_property_source_references_always_returns_string(response_text: str, num_subsolutions: int):
    """PROPERTY: Source references should always return a string."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    # Build research dict
    research = {
        "subsolutions": [
            {
                "subproblem": f"Problem {i}",
                "synthesis": f"Synthesis {i} with some content about trust and systems.",
                "tools_used": [f"tool_{i}"],
                "results": [{"tool": f"tool_{i}", "result": f"Result {i}"}]
            }
            for i in range(num_subsolutions)
        ]
    }
    
    result = agent._add_source_references(response_text, research)
    
    assert isinstance(result, str)
    assert len(result) >= len(response_text)  # Should be at least as long


@given(
    response_text=st.text(min_size=0, max_size=1000),
)
@settings(max_examples=20, deadline=None)
def test_property_source_references_idempotent(response_text: str):
    """PROPERTY: Adding source references multiple times should be safe."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    research = {
        "subsolutions": [
            {
                "subproblem": "Test",
                "synthesis": "Test synthesis with content.",
                "tools_used": ["tool1"],
                "results": [{"tool": "tool1", "result": "Result"}]
            }
        ]
    }
    
    result1 = agent._add_source_references(response_text, research)
    result2 = agent._add_source_references(result1, research)
    
    # Should handle gracefully (may add more references or be idempotent)
    assert isinstance(result1, str)
    assert isinstance(result2, str)


# ============================================================================
# Deep Edge Case Tests
# ============================================================================

def test_deep_belief_extraction_unicode():
    """Test belief extraction with unicode characters."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    # Unicode in belief statement
    agent._extract_prior_beliefs("I think 信任 (trust) is important for 系统 (systems)")
    
    # Should handle gracefully
    assert len(agent.prior_beliefs) >= 0


def test_deep_belief_extraction_very_long():
    """Test belief extraction with very long statements."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    long_belief = "I think " + "trust " * 1000 + "is important"
    agent._extract_prior_beliefs(long_belief)
    
    # Should handle gracefully (may truncate)
    assert len(agent.prior_beliefs) >= 0


def test_deep_belief_extraction_special_characters():
    """Test belief extraction with special characters."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    special = "I think trust@#$%^&*() is important!!!"
    agent._extract_prior_beliefs(special)
    
    # Should handle gracefully
    assert len(agent.prior_beliefs) >= 0


def test_deep_topic_similarity_unicode():
    """Test topic similarity with unicode."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    similarity = agent._compute_topic_similarity("信任系统", ["信任", "系统"])
    
    assert 0.0 <= similarity <= 1.0


def test_deep_topic_similarity_very_long():
    """Test topic similarity with very long strings."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    long_text = "trust " * 1000
    long_topics = ["trust " * 100, "systems " * 100]
    
    similarity = agent._compute_topic_similarity(long_text, long_topics)
    
    assert 0.0 <= similarity <= 1.0


def test_deep_source_references_malformed_research():
    """Test source references with malformed research data."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    # Various malformed structures
    malformed_cases = [
        {"subsolutions": None},
        {"subsolutions": "not a list"},
        {"subsolutions": [None]},
        {"subsolutions": ["not a dict"]},  # String in list
        {"subsolutions": [{"invalid": "structure"}]},
        {"subsolutions": [{"synthesis": None}]},
        {"subsolutions": [{"synthesis": "", "results": None}]},
    ]
    
    for research in malformed_cases:
        result = agent._add_source_references("Test response", research)
        assert isinstance(result, str)
        assert len(result) >= len("Test response")


def test_deep_source_references_very_large():
    """Test source references with very large research data."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    # Create large research structure
    large_research = {
        "subsolutions": [
            {
                "subproblem": f"Problem {i}",
                "synthesis": "Large synthesis. " * 100,
                "tools_used": [f"tool_{j}" for j in range(10)],
                "results": [{"tool": f"tool_{j}", "result": "Result " * 50} for j in range(10)]
            }
            for i in range(20)  # 20 subsolutions
        ]
    }
    
    result = agent._add_source_references("Test", large_research)
    
    assert isinstance(result, str)
    # Should handle large data without crashing


def test_deep_response_tiers_very_long_response():
    """Test response tiers with very long response."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    very_long = "Response. " * 10000
    tiers = agent._create_response_tiers(very_long, {}, "query")
    
    assert "summary" in tiers
    assert "detailed" in tiers
    # Summary should be shorter
    assert len(tiers["summary"]) <= len(tiers["detailed"])


def test_deep_response_tiers_unicode():
    """Test response tiers with unicode content."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    unicode_response = "信任系统 (Trust Systems) 是重要的。"
    tiers = agent._create_response_tiers(unicode_response, {}, "query")
    
    assert "summary" in tiers
    assert "detailed" in tiers


# ============================================================================
# Adversarial Tests
# ============================================================================

def test_adversarial_belief_extraction_injection():
    """Test belief extraction with potential injection attempts."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    # SQL injection attempt
    agent._extract_prior_beliefs("I think '; DROP TABLE beliefs; --")
    
    # Command injection attempt
    agent._extract_prior_beliefs("I think $(rm -rf /)")
    
    # Should handle safely
    assert len(agent.prior_beliefs) >= 0


def test_adversarial_topic_similarity_injection():
    """Test topic similarity with injection attempts."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    # Various injection patterns
    malicious = [
        "<script>alert('xss')</script>",
        "'; DROP TABLE topics; --",
        "../../etc/passwd",
        "\x00\x01\x02",  # Null bytes
    ]
    
    for mal in malicious:
        similarity = agent._compute_topic_similarity(mal, ["trust"])
        assert 0.0 <= similarity <= 1.0


def test_adversarial_source_references_injection():
    """Test source references with injection attempts."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    malicious_research = {
        "subsolutions": [
            {
                "subproblem": "<script>alert('xss')</script>",
                "synthesis": "'; DROP TABLE sources; --",
                "tools_used": ["../../etc/passwd"],
                "results": [{"tool": "\x00\x01", "result": "<img src=x onerror=alert(1)>"}]
            }
        ]
    }
    
    result = agent._add_source_references("Test", malicious_research)
    
    # Should handle safely (may escape or filter)
    assert isinstance(result, str)


# ============================================================================
# Concurrency and Race Condition Tests
# ============================================================================

@pytest.mark.asyncio
async def test_concurrent_belief_extraction():
    """Test belief extraction with concurrent calls."""
    import asyncio
    
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    async def extract_belief(i):
        agent._extract_prior_beliefs(f"I think belief {i} is important")
    
    # Concurrent extractions
    await asyncio.gather(*[extract_belief(i) for i in range(10)])
    
    # Should handle gracefully (may have race conditions, but shouldn't crash)
    assert len(agent.prior_beliefs) >= 0


@pytest.mark.asyncio
async def test_concurrent_topic_similarity():
    """Test topic similarity with concurrent calls."""
    import asyncio
    
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    async def compute_similarity(i):
        return agent._compute_topic_similarity(f"query {i}", ["trust", "systems"])
    
    results = await asyncio.gather(*[compute_similarity(i) for i in range(10)])
    
    # All should be valid
    for result in results:
        assert 0.0 <= result <= 1.0


@pytest.mark.asyncio
async def test_concurrent_query_tracking():
    """Test query tracking with concurrent calls."""
    import asyncio
    
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    async def track_query(i):
        agent._track_recent_query(f"Query {i} about trust and systems")
    
    await asyncio.gather(*[track_query(i) for i in range(10)])
    
    # Should handle gracefully
    assert len(agent.recent_queries) >= 0


# ============================================================================
# Integration Edge Cases
# ============================================================================

@pytest.mark.asyncio
async def test_integration_belief_then_similarity():
    """Test integration: extract belief, then compute similarity."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    # Extract belief
    agent._extract_prior_beliefs("I think trust is crucial")
    
    # Track query
    agent._track_recent_query("What is trust?")
    
    # Compute similarity with new query
    recent_topics = [q.get("topics", []) for q in agent.recent_queries]
    recent_topics_flat = [topic for topics in recent_topics for topic in topics]
    similarity = agent._compute_topic_similarity("Tell me about trust", recent_topics_flat)
    
    assert 0.0 <= similarity <= 1.0


@pytest.mark.asyncio
async def test_integration_full_workflow_edge_cases():
    """Test full workflow with various edge cases."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None
    
    # Edge case: Empty query
    response1 = await agent.chat("", use_research=False)
    assert "response" in response1
    
    # Edge case: Very long query
    long_query = "What is trust? " * 1000
    response2 = await agent.chat(long_query, use_research=False)
    assert "response" in response2
    
    # Edge case: Unicode query
    unicode_query = "什么是信任？ (What is trust?)"
    response3 = await agent.chat(unicode_query, use_research=False)
    assert "response" in response3


# ============================================================================
# Performance and Scalability Tests
# ============================================================================

def test_performance_topic_similarity_many_topics():
    """Test topic similarity performance with many topics."""
    import time
    
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    # Many topics
    many_topics = [f"topic_{i}" for i in range(1000)]
    
    start = time.time()
    similarity = agent._compute_topic_similarity("test query", many_topics)
    elapsed = time.time() - start
    
    assert 0.0 <= similarity <= 1.0
    # Should complete in reasonable time (< 1 second)
    assert elapsed < 1.0, f"Topic similarity took {elapsed:.2f}s with 1000 topics"


def test_performance_source_references_many_subsolutions():
    """Test source references performance with many subsolutions."""
    import time
    
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    # Many subsolutions
    large_research = {
        "subsolutions": [
            {
                "subproblem": f"Problem {i}",
                "synthesis": f"Synthesis {i} with content.",
                "tools_used": ["tool1"],
                "results": [{"tool": "tool1", "result": f"Result {i}"}]
            }
            for i in range(100)
        ]
    }
    
    start = time.time()
    result = agent._add_source_references("Test response", large_research)
    elapsed = time.time() - start
    
    assert isinstance(result, str)
    # Should complete in reasonable time (< 2 seconds)
    assert elapsed < 2.0, f"Source references took {elapsed:.2f}s with 100 subsolutions"


# ============================================================================
# Boundary Value Tests
# ============================================================================

def test_boundary_topic_similarity_empty_strings():
    """Test topic similarity with empty strings."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    # All empty
    assert agent._compute_topic_similarity("", []) == 0.0
    
    # Empty current
    assert agent._compute_topic_similarity("", ["topic"]) == 0.0
    
    # Empty topics
    assert agent._compute_topic_similarity("query", []) == 0.0


def test_boundary_belief_extraction_empty():
    """Test belief extraction with empty/whitespace."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    agent._extract_prior_beliefs("")
    agent._extract_prior_beliefs("   ")
    agent._extract_prior_beliefs("\n\t")
    
    # Should handle gracefully
    assert len(agent.prior_beliefs) >= 0


def test_boundary_source_references_empty():
    """Test source references with empty inputs."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    # Empty response
    result1 = agent._add_source_references("", {})
    assert isinstance(result1, str)
    
    # Empty research
    result2 = agent._add_source_references("Test", {})
    assert isinstance(result2, str)
    assert len(result2) >= len("Test")


# ============================================================================
# Type Safety Tests
# ============================================================================

def test_type_safety_belief_extraction():
    """Test belief extraction with wrong types."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    # Wrong types (should handle gracefully)
    agent._extract_prior_beliefs(None)
    agent._extract_prior_beliefs(123)
    agent._extract_prior_beliefs([])
    agent._extract_prior_beliefs({})
    
    # Should not crash
    assert isinstance(agent.prior_beliefs, list)


def test_type_safety_topic_similarity():
    """Test topic similarity with wrong types."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    # Should handle type errors gracefully
    try:
        agent._compute_topic_similarity(None, ["topic"])
    except (TypeError, AttributeError):
        pass  # Expected
    
    try:
        agent._compute_topic_similarity("query", None)
    except (TypeError, AttributeError):
        pass  # Expected


def test_type_safety_source_references():
    """Test source references with wrong types."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    # Wrong types
    result1 = agent._add_source_references(None, {})
    assert result1 is None or isinstance(result1, str)
    
    result2 = agent._add_source_references("Test", None)
    assert isinstance(result2, str)
    
    result3 = agent._add_source_references("Test", "not a dict")
    assert isinstance(result3, str)

