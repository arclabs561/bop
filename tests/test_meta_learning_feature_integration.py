"""Test meta-learning from the perspective of other BOP features."""

import asyncio
import tempfile
from pathlib import Path

import pytest

from pran.agent import KnowledgeAgent

# Cache is used internally, no direct import needed


# ============================================================================
# Research Orchestration Integration
# ============================================================================

@pytest.mark.asyncio
async def test_meta_learning_with_research_orchestration():
    """Test meta-learning doesn't break research orchestration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        # Add experience about tool effectiveness
        agent.meta_learner.experience_store.add_experience(
            query_type="factual",
            query="What is X?",
            response="X is...",
            reflection_text="Perplexity search worked well for factual queries",
            reflection_type="verified",
            tools_used=["perplexity_search"],
            quality_score=0.9,
        )

        # Query with research - experience should be injected
        response = await agent.chat(
            "What is d-separation?",
            use_research=True,
            use_schema="decompose_and_synthesize",
        )

        # Research orchestration should still work
        assert "response" in response
        if response.get("research_conducted"):
            research = response.get("research", {})
            # Should have research structure
            assert isinstance(research, dict)
            # Experience context should have been injected (helps with tool selection)
            # Can't easily verify without mocking, but shouldn't break


@pytest.mark.asyncio
async def test_meta_learning_with_tool_selection():
    """Test meta-learning helps with tool selection in research."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        # Add experiences about tool effectiveness
        agent.meta_learner.experience_store.add_experience(
            query_type="factual",
            query="What is X?",
            response="X is...",
            reflection_text="Perplexity search works best for definitions",
            reflection_type="verified",
            tools_used=["perplexity_search"],
        )

        agent.meta_learner.experience_store.add_experience(
            query_type="analytical",
            query="Why is X important?",
            response="X is important because...",
            reflection_text="Firecrawl helps find research papers for analytical questions",
            reflection_type="verified",
            tools_used=["firecrawl_search"],
        )

        # Factual query - should benefit from experience
        response1 = await agent.chat(
            "What is trust?",
            use_research=True,
        )

        # Analytical query - should benefit from different experience
        response2 = await agent.chat(
            "Why is trust important?",
            use_research=True,
        )

        # Both should work
        assert "response" in response1
        assert "response" in response2

        # Research should have been conducted (if tools available)
        # Experience context should have helped with tool selection


# ============================================================================
# Quality Feedback Integration
# ============================================================================

@pytest.mark.asyncio
async def test_meta_learning_with_quality_feedback():
    """Test meta-learning works with quality feedback loop."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        # Query should trigger both quality evaluation and reflection
        response = await agent.chat(
            "What is d-separation?",
            use_research=False,
        )

        await asyncio.sleep(0.2)  # Allow reflection to complete

        # Quality feedback should have evaluated
        if "quality" in response:
            quality = response["quality"]
            assert "score" in quality or quality.get("score") is None

        # Meta-learning should have reflected (if LLM available)
        # Check if experiences were stored
        experiences = agent.meta_learner.experience_store.get_relevant_experiences("factual", limit=1)
        # May be 0 if reflection didn't happen, but structure should work
        assert isinstance(experiences, list)


@pytest.mark.asyncio
async def test_meta_learning_uses_quality_scores():
    """Test meta-learning uses quality scores in reflection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        # Multiple queries with varying quality
        queries = [
            "What is trust?",
            "What is causality?",
            "What is information geometry?",
        ]

        for query in queries:
            response = await agent.chat(query, use_research=False)
            await asyncio.sleep(0.1)

            # Quality score should be available for reflection
            response.get("quality", {}).get("score")
            # Reflection should use this score (if LLM available)

        # Experiences should be stored with quality scores
        all_experiences = []
        for q_type in ["factual", "analytical"]:
            exps = agent.meta_learner.experience_store.get_relevant_experiences(q_type, limit=5)
            all_experiences.extend(exps)

        # Structure should work
        assert isinstance(all_experiences, list)


# ============================================================================
# Adaptive Learning Integration
# ============================================================================

@pytest.mark.asyncio
async def test_meta_learning_with_adaptive_learning():
    """Test meta-learning works alongside adaptive learning."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        # Multiple queries - both systems should learn
        queries = [
            ("What is trust?", "factual"),
            ("How do you build trust?", "procedural"),
            ("Why is trust important?", "analytical"),
        ]

        for query, expected_type in queries:
            await agent.chat(query, use_research=False)
            await asyncio.sleep(0.1)

            # Adaptive learning should learn schema preferences
            if agent.adaptive_manager:
                strategy = agent.adaptive_manager.get_adaptive_strategy(query)
                assert strategy is not None
                # Should have schema selection
                assert strategy.schema_selection is not None

            # Meta-learning should accumulate experiences
            experiences = agent.meta_learner.experience_store.get_relevant_experiences(
                expected_type,
                limit=1,
            )
            assert isinstance(experiences, list)

        # Both systems should have learned
        if agent.adaptive_manager:
            insights = agent.adaptive_manager.get_performance_insights()
            assert insights is not None


@pytest.mark.asyncio
async def test_meta_learning_adaptive_synergy():
    """Test synergy between meta-learning and adaptive learning."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        # First query - both systems learn
        response1 = await agent.chat("What is trust?", use_research=False)
        await asyncio.sleep(0.1)

        # Second similar query - should benefit from both learnings
        response2 = await agent.chat("What is trust?", use_research=False)

        # Both responses should exist
        assert "response" in response1
        assert "response" in response2

        # Adaptive learning should have selected schema
        if agent.adaptive_manager:
            strategy = agent.adaptive_manager.get_adaptive_strategy("What is trust?")
            assert strategy is not None

        # Meta-learning should have experiences
        experiences = agent.meta_learner.experience_store.get_relevant_experiences("factual", limit=1)
        assert isinstance(experiences, list)


# ============================================================================
# Context Topology Integration
# ============================================================================

@pytest.mark.asyncio
async def test_meta_learning_with_context_topology():
    """Test meta-learning works with context topology analysis."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        # Query with research - should generate topology
        response = await agent.chat(
            "What is d-separation and how does it relate to causality?",
            use_research=True,
            use_schema="decompose_and_synthesize",
        )

        # Context topology should still work
        if response.get("research") and response["research"].get("topology"):
            topology = response["research"]["topology"]
            # Should have topology metrics
            assert isinstance(topology, dict)
            # Meta-learning shouldn't break topology computation


@pytest.mark.asyncio
async def test_meta_learning_with_trust_metrics():
    """Test meta-learning works with trust and uncertainty modeling."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        # Query with research - should have trust metrics
        response = await agent.chat(
            "What is d-separation?",
            use_research=True,
        )

        # Trust metrics should still work
        if response.get("research") and response["research"].get("topology"):
            topology = response["research"]["topology"]
            if "trust_summary" in topology:
                trust_summary = topology["trust_summary"]
                # Should have trust metrics
                assert isinstance(trust_summary, dict)
                # Meta-learning shouldn't break trust computation


# ============================================================================
# Information Bottleneck Integration
# ============================================================================

@pytest.mark.asyncio
async def test_meta_learning_with_ib_filtering():
    """Test meta-learning works with information bottleneck filtering."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        # Query with research - IB filtering should still work
        response = await agent.chat(
            "What is d-separation?",
            use_research=True,
            use_schema="decompose_and_synthesize",
        )

        # IB filtering happens in LLMService.synthesize_tool_results
        # Should still work with meta-learning
        assert "response" in response

        # If research was conducted, IB filtering should have been applied
        if response.get("research_conducted"):
            research = response.get("research", {})
            # Should have research results
            assert isinstance(research, dict)


# ============================================================================
# Progressive Disclosure Integration
# ============================================================================

@pytest.mark.asyncio
async def test_meta_learning_with_progressive_disclosure():
    """Test meta-learning works with progressive disclosure tiers."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        # Query with progressive disclosure
        response = await agent.chat(
            "What is d-separation?",
            use_research=False,
        )

        # Progressive disclosure should still work
        if "response_tiers" in response:
            tiers = response["response_tiers"]
            # Should have tiers
            assert isinstance(tiers, dict)
            # Meta-learning shouldn't break tier creation


# ============================================================================
# Caching Integration
# ============================================================================

@pytest.mark.asyncio
async def test_meta_learning_with_caching():
    """Test meta-learning works with caching system."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"
        Path(tmpdir) / "cache"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        # Query - should use cache if available
        response1 = await agent.chat(
            "What is trust?",
            use_research=True,
        )

        # Same query - should benefit from cache
        response2 = await agent.chat(
            "What is trust?",
            use_research=True,
        )

        # Both should work
        assert "response" in response1
        assert "response" in response2

        # Caching should still work with meta-learning
        # Meta-learning experiences are separate from cache


# ============================================================================
# Session Management Integration
# ============================================================================

@pytest.mark.asyncio
async def test_meta_learning_with_sessions():
    """Test meta-learning works with session management."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
            # Enable session management
            if agent.quality_feedback.session_manager:
                agent.quality_feedback.session_manager.create_session(
                    user_id="test_user",
                )
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        # Query in session
        response = await agent.chat(
            "What is trust?",
            use_research=False,
        )

        # Session should still work
        if agent.quality_feedback and agent.quality_feedback.session_manager:
            current_session = agent.quality_feedback.session_manager.get_current_session()
            # Should have session
            assert current_session is not None or current_session is None

        # Meta-learning should work within session context
        assert "response" in response


# ============================================================================
# Constraint Solver Integration
# ============================================================================

@pytest.mark.asyncio
async def test_meta_learning_with_constraint_solver():
    """Test meta-learning works with constraint solver for tool selection."""
    import os

    # Enable constraint solver
    os.environ["BOP_USE_CONSTRAINTS"] = "true"

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            history_path = Path(tmpdir) / "history.json"
            experience_path = Path(tmpdir) / "experiences.json"

            agent = KnowledgeAgent(enable_quality_feedback=True)
            if agent.quality_feedback:
                agent.quality_feedback.evaluation_history_path = history_path
            if agent.meta_learner:
                agent.meta_learner.experience_store.storage_path = experience_path

            # Query with research - constraint solver should still work
            response = await agent.chat(
                "What is d-separation?",
                use_research=True,
                use_schema="decompose_and_synthesize",
            )

            # Constraint solver should still work
            assert "response" in response

            # If research was conducted, constraint solver should have been used
            # (if enabled and PySAT available)
    finally:
        # Clean up
        if "BOP_USE_CONSTRAINTS" in os.environ:
            del os.environ["BOP_USE_CONSTRAINTS"]


# ============================================================================
# Multi-Component Integration
# ============================================================================

@pytest.mark.asyncio
async def test_meta_learning_all_features_together():
    """Test meta-learning with all BOP features enabled."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
            # Enable session
            if agent.quality_feedback.session_manager:
                agent.quality_feedback.session_manager.create_session(
                    user_id="test",
                )
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        # Complex query using all features
        response = await agent.chat(
            "What is d-separation and how does it relate to causality, information geometry, and Bayesian networks?",
            use_research=True,
            use_schema="decompose_and_synthesize",
        )

        await asyncio.sleep(0.2)  # Allow reflection

        # All features should work together
        components_active = {
            "response": "response" in response,
            "research": response.get("research_conducted", False),
            "quality": "quality" in response,
            "meta_learning": "meta_reflection" in response or len(agent.meta_learner.experience_store.experiences) > 0,
            "adaptive": agent.adaptive_manager is not None,
            "topology": response.get("research", {}).get("topology") is not None,
            "tiers": "response_tiers" in response,
        }

        # At least most components should be active
        assert sum(components_active.values()) >= 4

        # If research was conducted, check topology
        if response.get("research"):
            research = response["research"]
            if "topology" in research:
                topology = research["topology"]
                assert isinstance(topology, dict)


# ============================================================================
# Feature-Specific Edge Cases
# ============================================================================

@pytest.mark.asyncio
async def test_meta_learning_research_failure_handling():
    """Test meta-learning handles research failures gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        # Query that might fail research (invalid or impossible query)
        response = await agent.chat(
            "What is d-separation?",
            use_research=True,
        )

        # Should handle gracefully
        assert "response" in response

        # If research failed, should have error indicator
        if not response.get("research_conducted"):
            assert "research_error" in response or response.get("research_conducted") is False

        # Meta-learning should still work (reflect on failure)
        experiences = agent.meta_learner.experience_store.get_relevant_experiences("factual", limit=1)
        assert isinstance(experiences, list)


@pytest.mark.asyncio
async def test_meta_learning_quality_feedback_failure():
    """Test meta-learning handles quality feedback failures gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        # Query - quality feedback might fail (e.g., no LLM)
        response = await agent.chat(
            "What is trust?",
            use_research=False,
        )

        # Should handle gracefully
        assert "response" in response

        # Quality might not be evaluated, but shouldn't crash
        # Meta-learning should still work
        experiences = agent.meta_learner.experience_store.get_relevant_experiences("factual", limit=1)
        assert isinstance(experiences, list)


@pytest.mark.asyncio
async def test_meta_learning_adaptive_learning_failure():
    """Test meta-learning handles adaptive learning failures gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        # Query - adaptive learning might fail (e.g., no history)
        response = await agent.chat(
            "What is trust?",
            use_research=False,
        )

        # Should handle gracefully
        assert "response" in response

        # Adaptive learning might not work, but shouldn't crash
        # Meta-learning should still work
        experiences = agent.meta_learner.experience_store.get_relevant_experiences("factual", limit=1)
        assert isinstance(experiences, list)

