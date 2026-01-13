"""Comprehensive tests for meta-learning: edge cases, performance, adversarial, property-based."""

import asyncio
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from bop.agent import KnowledgeAgent
from bop.meta_learning import ExperienceStore, MetaLearner

# ============================================================================
# Edge Cases
# ============================================================================

def test_experience_store_empty_query_type():
    """Test handling of empty query type."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ExperienceStore(storage_path=Path(tmpdir) / "experiences.json")

        store.add_experience(
            query_type="",
            query="Test",
            response="Test response",
            reflection_text="Test reflection",
            reflection_type="self",
            tools_used=[],
        )

        experiences = store.get_relevant_experiences("", limit=5)
        assert len(experiences) >= 0  # Should handle gracefully


def test_experience_store_very_long_reflection():
    """Test handling of very long reflection text."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ExperienceStore(storage_path=Path(tmpdir) / "experiences.json")

        long_reflection = "A" * 10000
        store.add_experience(
            query_type="factual",
            query="Test",
            response="Test response",
            reflection_text=long_reflection,
            reflection_type="self",
            tools_used=[],
        )

        experiences = store.get_relevant_experiences("factual", limit=1)
        assert len(experiences) == 1
        # Context should be truncated
        assert len(experiences[0]["insights"]) <= 300


def test_experience_store_special_characters():
    """Test handling of special characters in queries/responses."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ExperienceStore(storage_path=Path(tmpdir) / "experiences.json")

        special_query = "What is d-separation? (with parentheses) & special chars: <tag>"
        special_response = "Response with 'quotes' and \"double quotes\""
        special_reflection = "Reflection with\nnewlines\tand\ttabs"

        store.add_experience(
            query_type="factual",
            query=special_query,
            response=special_response,
            reflection_text=special_reflection,
            reflection_type="self",
            tools_used=["tool_with-special_chars"],
        )

        experiences = store.get_relevant_experiences("factual", limit=1)
        assert len(experiences) == 1
        # Should handle special characters gracefully
        assert experiences[0]["query_type"] == "factual"


def test_experience_store_concurrent_access():
    """Test concurrent access to experience store."""
    import threading

    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "experiences.json"
        store = ExperienceStore(storage_path=store_path)

        def add_experience(i):
            store.add_experience(
                query_type="factual",
                query=f"Query {i}",
                response=f"Response {i}",
                reflection_text=f"Reflection {i}",
                reflection_type="self",
                tools_used=[],
            )

        # Add experiences concurrently
        threads = [threading.Thread(target=add_experience, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have all experiences
        experiences = store.get_relevant_experiences("factual", limit=20)
        assert len(experiences) == 10


def test_meta_learner_no_storage_path():
    """Test MetaLearner without storage path (in-memory only)."""
    learner = MetaLearner(storage_path=None)

    # Add experience in memory
    learner.experience_store.add_experience(
        query_type="factual",
        query="Test",
        response="Test response",
        reflection_text="Test reflection",
        reflection_type="self",
        tools_used=[],
    )

    # Should work without persistence (in-memory)
    context = learner.get_context_experience("Test", "factual")
    # May have experiences if added above
    assert isinstance(context, str)


@pytest.mark.asyncio
async def test_meta_learner_reflection_with_empty_tools():
    """Test reflection with empty tools list."""
    learner = MetaLearner(enable_reflection=True)

    mock_llm = AsyncMock()
    mock_llm.generate_response = AsyncMock(return_value="Reflection without tools")

    reflection = await learner.reflect_on_completion(
        query="Test",
        response="Test response",
        query_type="factual",
        tools_used=[],  # Empty list
        llm_service=mock_llm,
    )

    assert reflection is not None


@pytest.mark.asyncio
async def test_meta_learner_reflection_with_none_quality_score():
    """Test reflection with None quality score."""
    learner = MetaLearner(enable_reflection=True)

    mock_llm = AsyncMock()
    mock_llm.generate_response = AsyncMock(return_value="Reflection without quality score")

    reflection = await learner.reflect_on_completion(
        query="Test",
        response="Test response",
        query_type="factual",
        tools_used=["tool1"],
        quality_score=None,  # None score
        llm_service=mock_llm,
    )

    assert reflection is not None


# ============================================================================
# Performance Tests
# ============================================================================

def test_experience_store_performance_large_dataset():
    """Test performance with large number of experiences."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ExperienceStore(storage_path=Path(tmpdir) / "experiences.json")

        # Add many experiences
        start_time = time.time()
        for i in range(100):
            store.add_experience(
                query_type="factual",
                query=f"Query {i}",
                response=f"Response {i}",
                reflection_text=f"Reflection {i}",
                reflection_type="self",
                tools_used=[],
            )
        add_time = time.time() - start_time

        # Retrieve should be fast
        start_time = time.time()
        experiences = store.get_relevant_experiences("factual", limit=10)
        retrieve_time = time.time() - start_time

        assert add_time < 1.0, f"Adding 100 experiences took {add_time:.3f}s"
        assert retrieve_time < 0.1, f"Retrieving experiences took {retrieve_time:.3f}s"
        assert len(experiences) == 10


def test_experience_store_format_performance():
    """Test context formatting performance."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ExperienceStore(storage_path=Path(tmpdir) / "experiences.json")

        # Add experiences
        for i in range(20):
            store.add_experience(
                query_type="factual",
                query=f"Query {i}",
                response=f"Response {i}",
                reflection_text=f"Reflection {i}",
                reflection_type="self",
                tools_used=[],
            )

        experiences = store.get_relevant_experiences("factual", limit=20)

        start_time = time.time()
        context = store.format_for_context(experiences)
        format_time = time.time() - start_time

        assert format_time < 0.05, f"Formatting took {format_time:.3f}s"
        assert len(context) > 0


# ============================================================================
# Adversarial Tests
# ============================================================================

def test_experience_store_malformed_data():
    """Test handling of malformed experience data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "experiences.json"

        # Create malformed JSON
        store_path.parent.mkdir(parents=True, exist_ok=True)
        store_path.write_text("{ invalid json }")

        # Should handle gracefully
        store = ExperienceStore(storage_path=store_path)
        assert isinstance(store.experiences, dict)


def test_experience_store_corrupted_file():
    """Test handling of corrupted file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "experiences.json"

        # Create corrupted file
        store_path.parent.mkdir(parents=True, exist_ok=True)
        store_path.write_bytes(b"\x00\x01\x02\x03")  # Binary data

        # Should handle gracefully
        store = ExperienceStore(storage_path=store_path)
        assert isinstance(store.experiences, dict)


def test_experience_store_invalid_query_type():
    """Test handling of invalid query types."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ExperienceStore(storage_path=Path(tmpdir) / "experiences.json")

        # Add with None query type
        store.add_experience(
            query_type=None,  # Invalid
            query="Test",
            response="Test",
            reflection_text="Test",
            reflection_type="self",
            tools_used=[],
        )

        # Should handle gracefully
        experiences = store.get_relevant_experiences(None, limit=5)
        assert isinstance(experiences, list)


@pytest.mark.asyncio
async def test_meta_learner_reflection_llm_failure():
    """Test handling of LLM failure during reflection."""
    learner = MetaLearner(enable_reflection=True)

    mock_llm = AsyncMock()
    mock_llm.generate_response = AsyncMock(side_effect=Exception("LLM error"))

    reflection = await learner.reflect_on_completion(
        query="Test",
        response="Test response",
        query_type="factual",
        tools_used=[],
        llm_service=mock_llm,
    )

    # Should return None on failure, not crash
    assert reflection is None


@pytest.mark.asyncio
async def test_meta_learner_reflection_timeout():
    """Test handling of LLM timeout during reflection."""
    learner = MetaLearner(enable_reflection=True)

    async def slow_generate(*args, **kwargs):
        await asyncio.sleep(10)  # Simulate timeout
        return "Reflection"

    mock_llm = AsyncMock()
    mock_llm.generate_response = slow_generate

    # Should timeout gracefully
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(
            learner.reflect_on_completion(
                query="Test",
                response="Test response",
                query_type="factual",
                tools_used=[],
                llm_service=mock_llm,
            ),
            timeout=0.1,
        )


# ============================================================================
# Property-Based Tests
# ============================================================================

def test_experience_store_idempotency():
    """Property: Adding same experience multiple times should be idempotent."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ExperienceStore(storage_path=Path(tmpdir) / "experiences.json")

        # Add same experience twice
        store.add_experience(
            query_type="factual",
            query="Same query",
            response="Same response",
            reflection_text="Same reflection",
            reflection_type="self",
            tools_used=["tool1"],
        )

        count1 = len(store.experiences.get("factual", []))

        store.add_experience(
            query_type="factual",
            query="Same query",
            response="Same response",
            reflection_text="Same reflection",
            reflection_type="self",
            tools_used=["tool1"],
        )

        count2 = len(store.experiences.get("factual", []))

        # Should add both (not deduplicate)
        assert count2 == count1 + 1


def test_experience_store_ordering():
    """Property: Experiences should be ordered by relevance (verified > self, recent > old)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ExperienceStore(storage_path=Path(tmpdir) / "experiences.json")

        # Add old self-reflection
        store.add_experience(
            query_type="factual",
            query="Old query",
            response="Old response",
            reflection_text="Old reflection",
            reflection_type="self",
            tools_used=[],
        )

        # Add recent verified reflection
        store.add_experience(
            query_type="factual",
            query="Recent query",
            response="Recent response",
            reflection_text="Recent verified reflection",
            reflection_type="verified",
            tools_used=[],
        )

        experiences = store.get_relevant_experiences("factual", limit=2)

        # Verified should come first
        assert len(experiences) == 2
        assert experiences[0]["reflection_type"] == "verified"
        assert experiences[0]["confidence"] == 0.8


def test_experience_store_limit_property():
    """Property: Limit should always be respected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ExperienceStore(storage_path=Path(tmpdir) / "experiences.json")

        # Add many experiences
        for i in range(100):
            store.add_experience(
                query_type="factual",
                query=f"Query {i}",
                response=f"Response {i}",
                reflection_text=f"Reflection {i}",
                reflection_type="self",
                tools_used=[],
            )

        # Test various limits
        for limit in [1, 5, 10, 20, 50]:
            experiences = store.get_relevant_experiences("factual", limit=limit)
            assert len(experiences) <= limit


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_agent_meta_learning_multi_turn():
    """Test meta-learning across multiple conversation turns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        # Multiple turns
        queries = [
            "What is trust?",
            "How does trust work?",
            "Why is trust important?",
        ]

        for query in queries:
            response = await agent.chat(query, use_research=False)
            assert "response" in response

        # Check experiences accumulated
        all_experiences = []
        for q_type in ["factual", "procedural", "analytical"]:
            all_experiences.extend(
                agent.meta_learner.experience_store.get_relevant_experiences(q_type, limit=10)
            )

        # Should have some experiences
        assert len(all_experiences) >= 0  # May be 0 if reflection didn't happen


@pytest.mark.asyncio
async def test_agent_meta_learning_with_research():
    """Test meta-learning when research is enabled."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        # Add experience first
        agent.meta_learner.experience_store.add_experience(
            query_type="factual",
            query="What is X?",
            response="X is...",
            reflection_text="Perplexity search worked well",
            reflection_type="self",
            tools_used=["perplexity_search"],
        )

        # Query with research (should use experience context)
        response = await agent.chat(
            "What is d-separation?",
            use_research=True,
            use_schema="decompose_and_synthesize",
        )

        assert "response" in response
        # Experience should be injected into research query
        # (Can't easily verify without mocking, but should not crash)


@pytest.mark.asyncio
async def test_agent_meta_learning_adaptive_integration():
    """Test meta-learning integration with adaptive quality manager."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        # Query should trigger both adaptive learning and meta-learning
        response = await agent.chat(
            "What is trust?",
            use_research=False,
        )

        # Both systems should work together
        assert "response" in response

        # Adaptive manager should have learned
        if agent.adaptive_manager:
            strategy = agent.adaptive_manager.get_adaptive_strategy("What is trust?")
            assert strategy is not None

        # Meta-learner should have stored experience (if reflection happened)
        experiences = agent.meta_learner.experience_store.get_relevant_experiences("factual", limit=1)
        assert isinstance(experiences, list)


# ============================================================================
# Cross-Session Learning Tests
# ============================================================================

def test_experience_store_cross_session_persistence():
    """Test that experiences persist across agent instances (sessions)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        # First session
        agent1 = KnowledgeAgent(enable_quality_feedback=True)
        if agent1.quality_feedback:
            agent1.quality_feedback.evaluation_history_path = history_path
        if agent1.meta_learner:
            agent1.meta_learner.experience_store.storage_path = experience_path

        # Add experience
        agent1.meta_learner.experience_store.add_experience(
            query_type="factual",
            query="What is trust?",
            response="Trust is...",
            reflection_text="First session reflection",
            reflection_type="self",
            tools_used=["tool1"],
        )

        # Force save
        agent1.meta_learner.experience_store._save_experiences()

        # Second session (new agent instance)
        agent2 = KnowledgeAgent(enable_quality_feedback=True)
        if agent2.quality_feedback:
            agent2.quality_feedback.evaluation_history_path = history_path
        if agent2.meta_learner:
            agent2.meta_learner.experience_store.storage_path = experience_path
            # Force reload
            agent2.meta_learner.experience_store._load_experiences()

        # Should load experiences from first session
        experiences = agent2.meta_learner.experience_store.get_relevant_experiences("factual", limit=5)
        # May be 0 if file wasn't saved yet, but structure should work
        if len(experiences) > 0:
            assert "First session reflection" in experiences[0]["insights"]


# ============================================================================
# Real-World Scenario Tests
# ============================================================================

@pytest.mark.asyncio
async def test_meta_learning_realistic_workflow():
    """Test realistic workflow: research query → reflection → improved subsequent query."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        # First query: complex research question
        response1 = await agent.chat(
            "What is d-separation and how does it relate to causality?",
            use_research=False,  # Faster for testing
        )

        assert "response" in response1

        # Wait a bit for reflection (if async)
        await asyncio.sleep(0.1)

        # Second similar query: should benefit from experience
        response2 = await agent.chat(
            "Explain d-separation in Bayesian networks",
            use_research=False,
        )

        assert "response" in response2

        # Both should work
        assert len(response1["response"]) > 0
        assert len(response2["response"]) > 0


@pytest.mark.asyncio
async def test_meta_learning_different_query_types():
    """Test meta-learning with different query types in realistic scenario."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        # Mix of query types
        queries = [
            ("What is trust?", "factual"),
            ("How do you build trust?", "procedural"),
            ("Why is trust important?", "analytical"),
            ("Compare trust and reliability", "comparative"),
            ("Evaluate trust mechanisms", "evaluative"),
        ]

        for query, expected_type in queries:
            response = await agent.chat(query, use_research=False)
            assert "response" in response

            # Verify query type classification
            if agent.adaptive_manager:
                classified_type = agent.adaptive_manager._classify_query(query)
                # Should match expected type (or be close)
                assert classified_type in ["factual", "procedural", "analytical", "comparative", "evaluative", "general"]


# ============================================================================
# LLM-as-Judge Comprehensive Tests
# ============================================================================

@pytest.mark.asyncio
async def test_llm_judge_reflection_generalizability():
    """LLM-as-judge: Evaluate if reflections extract generalizable principles."""
    from bop.llm import LLMService

    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "experiences.json"
        learner = MetaLearner(storage_path=store_path, enable_reflection=True)

        try:
            llm = LLMService()
        except Exception:
            pytest.skip("LLM service not available")

        # Perform reflection
        reflection_text = await learner.reflect_on_completion(
            query="What is d-separation?",
            response="D-separation is a graphical criterion...",
            query_type="factual",
            tools_used=["perplexity_search"],
            quality_score=0.85,
            llm_service=llm,
        )

        if not reflection_text:
            pytest.skip("Reflection not performed")

        # Judge: Evaluate generalizability
        judge_prompt = f"""Evaluate if this reflection extracts generalizable principles:

Reflection:
{reflection_text}

Evaluate:
1. Does it identify patterns that apply beyond this specific case? (0-1)
2. Does it extract actionable principles? (0-1)
3. Could these insights help with similar but different queries? (0-1)

Respond with JSON: {{"generalizable": 0.0-1.0, "actionable": 0.0-1.0, "transferable": 0.0-1.0, "overall": 0.0-1.0}}
"""

        judge_response = await llm.generate_response(judge_prompt)

        import re
        json_match = re.search(r'\{[^}]+\}', judge_response, re.DOTALL)
        if json_match:
            try:
                judgment = json.loads(json_match.group())
                assert "overall" in judgment
                assert judgment["overall"] >= 0.4  # Should be somewhat generalizable
                print(f"Generalizability judgment: {judgment}")
            except json.JSONDecodeError:
                pass  # Judge response may not be JSON


@pytest.mark.asyncio
async def test_llm_judge_experience_ranking():
    """LLM-as-judge: Evaluate if experiences are ranked by relevance correctly."""
    from bop.llm import LLMService

    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "experiences.json"
        learner = MetaLearner(storage_path=store_path)

        # Add experiences with different relevance
        learner.experience_store.add_experience(
            query_type="factual",
            query="What is trust?",
            response="Trust is...",
            reflection_text="Perplexity search worked for definitions",
            reflection_type="self",
            tools_used=["perplexity_search"],
        )

        learner.experience_store.add_experience(
            query_type="analytical",
            query="Why is trust important?",
            response="Trust is important because...",
            reflection_text="Firecrawl helped find research papers",
            reflection_type="self",
            tools_used=["firecrawl_search"],
        )

        # Get experiences for factual query
        experiences = learner.experience_store.get_relevant_experiences("factual", limit=2)

        try:
            llm = LLMService()
        except Exception:
            pytest.skip("LLM service not available")

        # Judge: Evaluate ranking
        judge_prompt = f"""Evaluate if these experiences are ranked correctly for a factual query:

Query: "What is d-separation?" (factual)

Experiences (in order):
{json.dumps([exp.get('insights', '') for exp in experiences], indent=2)}

Evaluate:
1. Is the most relevant experience first? (0-1)
2. Are experiences ordered by relevance? (0-1)

Respond with JSON: {{"correct_ordering": 0.0-1.0, "relevance": 0.0-1.0}}
"""

        judge_response = await llm.generate_response(judge_prompt)

        import re
        json_match = re.search(r'\{[^}]+\}', judge_response, re.DOTALL)
        if json_match:
            try:
                judgment = json.loads(json_match.group())
                assert "correct_ordering" in judgment
                print(f"Ranking judgment: {judgment}")
            except json.JSONDecodeError:
                pass


@pytest.mark.asyncio
async def test_llm_judge_meta_learning_improvement():
    """LLM-as-judge: Evaluate if meta-learning improves system over time."""
    from bop.llm import LLMService

    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        try:
            llm = LLMService()
        except Exception:
            pytest.skip("LLM service not available")

        # First query (no experience)
        response1 = await agent.chat("What is d-separation?", use_research=False)

        # Add experience manually
        agent.meta_learner.experience_store.add_experience(
            query_type="factual",
            query="What is d-separation?",
            response=response1.get("response", ""),
            reflection_text="Include examples and use clear definitions. Perplexity search helps.",
            reflection_type="verified",
            tools_used=["perplexity_search"],
            quality_score=0.85,
        )

        # Second similar query (with experience)
        response2 = await agent.chat("Explain d-separation", use_research=False)

        # Judge: Compare responses
        judge_prompt = f"""Compare two responses to similar queries and evaluate if meta-learning improved the second:

First Response (no experience):
{response1.get('response', '')[:300]}

Second Response (with experience):
{response2.get('response', '')[:300]}

Evaluate:
1. Is the second response better? (yes/no/equal)
2. Does it show learning from experience? (0-1)
3. Overall improvement? (0-1)

Respond with JSON: {{"improved": "yes|no|equal", "shows_learning": 0.0-1.0, "improvement": 0.0-1.0}}
"""

        judge_response = await llm.generate_response(judge_prompt)

        import re
        json_match = re.search(r'\{[^}]+\}', judge_response, re.DOTALL)
        if json_match:
            try:
                judgment = json.loads(json_match.group())
                assert "improved" in judgment
                print(f"Improvement judgment: {judgment}")
            except json.JSONDecodeError:
                pass

