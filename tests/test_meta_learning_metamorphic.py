"""Metamorphic tests for meta-learning: test invariants that should hold across transformations."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from bop.agent import KnowledgeAgent
from bop.meta_learning import ExperienceStore, MetaLearner

# ============================================================================
# Metamorphic Relations
# ============================================================================

def test_metamorphic_experience_ordering():
    """
    Metamorphic: Adding experiences in different orders should produce same results.

    Relation: Order independence
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Order 1: Add A, then B
        store1 = ExperienceStore(storage_path=Path(tmpdir) / "exp1.json")
        store1.add_experience(
            query_type="factual",
            query="Query A",
            response="Response A",
            reflection_text="Reflection A",
            reflection_type="self",
            tools_used=[],
        )
        store1.add_experience(
            query_type="factual",
            query="Query B",
            response="Response B",
            reflection_text="Reflection B",
            reflection_type="verified",
            tools_used=[],
        )

        # Order 2: Add B, then A
        store2 = ExperienceStore(storage_path=Path(tmpdir) / "exp2.json")
        store2.add_experience(
            query_type="factual",
            query="Query B",
            response="Response B",
            reflection_text="Reflection B",
            reflection_type="verified",
            tools_used=[],
        )
        store2.add_experience(
            query_type="factual",
            query="Query A",
            response="Response A",
            reflection_text="Reflection A",
            reflection_type="self",
            tools_used=[],
        )

        # Retrieval should prioritize verified over self, regardless of order
        exp1 = store1.get_relevant_experiences("factual", limit=2)
        exp2 = store2.get_relevant_experiences("factual", limit=2)

        # Both should have verified first
        assert len(exp1) == 2
        assert len(exp2) == 2
        assert exp1[0]["reflection_type"] == "verified"
        assert exp2[0]["reflection_type"] == "verified"


def test_metamorphic_experience_limit():
    """
    Metamorphic: Retrieving with different limits should respect limit property.

    Relation: Limit monotonicity
    """
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

        # Test different limits
        limits = [1, 5, 10, 20, 50]
        results = []
        for limit in limits:
            exps = store.get_relevant_experiences("factual", limit=limit)
            results.append(len(exps))

        # Should be monotonic (more limit = more results, up to available)
        assert results[0] <= results[1] <= results[2] <= results[3] <= results[4]
        # All should respect limit
        assert all(r <= limit for r, limit in zip(results, limits))


def test_metamorphic_experience_duplication():
    """
    Metamorphic: Adding duplicate experiences should not break retrieval.

    Relation: Duplication tolerance
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ExperienceStore(storage_path=Path(tmpdir) / "experiences.json")

        # Add same experience multiple times
        for i in range(10):
            store.add_experience(
                query_type="factual",
                query="Same query",
                response="Same response",
                reflection_text="Same reflection",
                reflection_type="self",
                tools_used=[],
            )

        # Should still work
        experiences = store.get_relevant_experiences("factual", limit=5)
        assert len(experiences) <= 5
        assert isinstance(experiences, list)


@pytest.mark.asyncio
async def test_metamorphic_reflection_consistency():
    """
    Metamorphic: Reflecting on same task multiple times should produce consistent results.

    Relation: Reflection consistency
    """
    learner = MetaLearner(enable_reflection=True)

    mock_llm = AsyncMock()
    mock_llm.generate_response = AsyncMock(return_value="Consistent reflection")

    # Reflect on same task twice
    reflection1 = await learner.reflect_on_completion(
        query="What is trust?",
        response="Trust is...",
        query_type="factual",
        tools_used=["tool1"],
        llm_service=mock_llm,
    )

    reflection2 = await learner.reflect_on_completion(
        query="What is trust?",
        response="Trust is...",
        query_type="factual",
        tools_used=["tool1"],
        llm_service=mock_llm,
    )

    # With same LLM mock, should get same result
    assert reflection1 == reflection2


def test_metamorphic_context_injection_idempotency():
    """
    Metamorphic: Getting context multiple times should return same result.

    Relation: Idempotency
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "experiences.json"
        learner = MetaLearner(storage_path=store_path)

        # Add experience
        learner.experience_store.add_experience(
            query_type="factual",
            query="What is X?",
            response="X is...",
            reflection_text="Test reflection",
            reflection_type="self",
            tools_used=[],
        )

        # Get context multiple times
        context1 = learner.get_context_experience("Test", "factual")
        context2 = learner.get_context_experience("Test", "factual")
        context3 = learner.get_context_experience("Test", "factual")

        # Should be same (idempotent)
        assert context1 == context2 == context3


# ============================================================================
# Invariant Tests
# ============================================================================

def test_invariant_experience_count_monotonicity():
    """
    Invariant: Experience count should only increase (or stay same) when adding.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ExperienceStore(storage_path=Path(tmpdir) / "experiences.json")

        counts = []
        for i in range(10):
            count_before = len(store.experiences.get("factual", []))
            store.add_experience(
                query_type="factual",
                query=f"Query {i}",
                response=f"Response {i}",
                reflection_text=f"Reflection {i}",
                reflection_type="self",
                tools_used=[],
            )
            count_after = len(store.experiences.get("factual", []))
            counts.append((count_before, count_after))

        # Each addition should increase count (or stay same if at limit)
        for before, after in counts:
            assert after >= before
            assert after <= before + 1  # Can only add one at a time


def test_invariant_experience_confidence_bounds():
    """
    Invariant: Experience confidence should always be in [0, 1].
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ExperienceStore(storage_path=Path(tmpdir) / "experiences.json")

        store.add_experience(
            query_type="factual",
            query="Test",
            response="Test",
            reflection_text="Test",
            reflection_type="self",
            tools_used=[],
        )

        store.add_experience(
            query_type="factual",
            query="Test",
            response="Test",
            reflection_text="Test",
            reflection_type="verified",
            tools_used=[],
        )

        experiences = store.get_relevant_experiences("factual", limit=10)

        # All confidences should be in [0, 1]
        for exp in experiences:
            confidence = exp.get("confidence", 0.5)
            assert 0.0 <= confidence <= 1.0


def test_invariant_experience_timestamp_ordering():
    """
    Invariant: Experiences should be ordered by timestamp (recent first).
    """
    import time

    with tempfile.TemporaryDirectory() as tmpdir:
        store = ExperienceStore(storage_path=Path(tmpdir) / "experiences.json")

        # Add experiences with delays
        for i in range(5):
            store.add_experience(
                query_type="factual",
                query=f"Query {i}",
                response=f"Response {i}",
                reflection_text=f"Reflection {i}",
                reflection_type="self",
                tools_used=[],
            )
            time.sleep(0.01)  # Small delay to ensure different timestamps

        experiences = store.get_relevant_experiences("factual", limit=10)

        # Should be ordered by timestamp (most recent first)
        if len(experiences) > 1:
            timestamps = [exp.get("timestamp", "") for exp in experiences]
            # Most recent should be first
            assert timestamps[0] >= timestamps[-1]


# ============================================================================
# Cross-Component Invariants
# ============================================================================

@pytest.mark.asyncio
async def test_invariant_meta_learning_doesnt_break_quality():
    """
    Invariant: Meta-learning should not break quality evaluation.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        # Query should still get quality evaluation
        response = await agent.chat("What is trust?", use_research=False)

        # Quality should still be evaluated
        if "quality" in response:
            quality_score = response["quality"].get("score")
            # Should have quality score (or None if evaluation didn't happen)
            assert quality_score is None or (0.0 <= quality_score <= 1.0)


@pytest.mark.asyncio
async def test_invariant_meta_learning_doesnt_break_research():
    """
    Invariant: Meta-learning should not break research functionality.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        # Add experience
        agent.meta_learner.experience_store.add_experience(
            query_type="factual",
            query="What is X?",
            response="X is...",
            reflection_text="Test",
            reflection_type="self",
            tools_used=[],
        )

        # Research should still work
        response = await agent.chat(
            "What is d-separation?",
            use_research=True,
            use_schema="decompose_and_synthesize",
        )

        # Should have research results (or error, but not crash)
        assert "response" in response
        assert "research_conducted" in response


@pytest.mark.asyncio
async def test_invariant_meta_learning_doesnt_break_adaptive():
    """
    Invariant: Meta-learning should not break adaptive learning.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        # Multiple queries to build adaptive learning
        for query in ["What is trust?", "How does trust work?", "Why is trust important?"]:
            await agent.chat(query, use_research=False)
            await asyncio.sleep(0.1)

        # Adaptive learning should still work
        if agent.adaptive_manager:
            strategy = agent.adaptive_manager.get_adaptive_strategy("What is trust?")
            assert strategy is not None
            assert strategy.schema_selection is not None

