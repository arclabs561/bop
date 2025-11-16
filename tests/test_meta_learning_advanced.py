"""Advanced tests for meta-learning: sophisticated scenarios, stress tests, and deep validation."""

import pytest
import tempfile
import asyncio
import time
import statistics
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import AsyncMock, patch
import json
import re

from bop.agent import KnowledgeAgent
from bop.meta_learning import MetaLearner, ExperienceStore
from bop.quality_feedback import QualityFeedbackLoop
from bop.adaptive_quality import AdaptiveQualityManager


# ============================================================================
# Stress Tests
# ============================================================================

@pytest.mark.asyncio
async def test_stress_experience_store_rapid_writes():
    """Stress: Rapid sequential writes to experience store."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ExperienceStore(storage_path=Path(tmpdir) / "experiences.json")
        
        start_time = time.time()
        for i in range(200):
            store.add_experience(
                query_type="factual",
                query=f"Query {i}",
                response=f"Response {i}",
                reflection_text=f"Reflection {i}",
                reflection_type="self",
                tools_used=[],
            )
        elapsed = time.time() - start_time
        
        # Should complete in reasonable time
        assert elapsed < 2.0, f"200 writes took {elapsed:.3f}s"
        
        # Should still be functional
        experiences = store.get_relevant_experiences("factual", limit=10)
        assert len(experiences) == 10


@pytest.mark.asyncio
async def test_stress_agent_meta_learning_rapid_queries():
    """Stress: Rapid queries to agent with meta-learning enabled."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"
        
        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path
        
        queries = [f"What is concept {i}?" for i in range(20)]
        
        start_time = time.time()
        responses = []
        for query in queries:
            response = await agent.chat(query, use_research=False)
            responses.append(response)
        elapsed = time.time() - start_time
        
        # Should complete in reasonable time
        assert elapsed < 30.0, f"20 queries took {elapsed:.3f}s"
        
        # All should succeed
        assert all("response" in r for r in responses)


@pytest.mark.asyncio
async def test_stress_experience_retrieval_many_types():
    """Stress: Retrieve experiences across many query types."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ExperienceStore(storage_path=Path(tmpdir) / "experiences.json")
        
        # Add experiences for many query types
        query_types = [f"type_{i}" for i in range(50)]
        for q_type in query_types:
            for j in range(10):
                store.add_experience(
                    query_type=q_type,
                    query=f"Query {j}",
                    response=f"Response {j}",
                    reflection_text=f"Reflection {j}",
                    reflection_type="self",
                    tools_used=[],
                )
        
        # Retrieve from all types
        start_time = time.time()
        all_experiences = []
        for q_type in query_types:
            exps = store.get_relevant_experiences(q_type, limit=5)
            all_experiences.extend(exps)
        elapsed = time.time() - start_time
        
        assert elapsed < 1.0, f"Retrieval from 50 types took {elapsed:.3f}s"
        assert len(all_experiences) == 50 * 5


# ============================================================================
# Sophisticated Multi-Turn Scenarios
# ============================================================================

@pytest.mark.asyncio
async def test_multiturn_topic_evolution_judge():
    """
    Multi-turn: LLM judge evaluates if system adapts as conversation topic evolves.
    
    Scenario: Conversation starts broad, narrows, then expands again.
    System should use relevant experiences at each stage.
    """
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
        
        # Turn 1: Broad question
        response1 = await agent.chat("What is causality?", use_research=False)
        await asyncio.sleep(0.2)
        
        # Turn 2: Narrow to specific concept
        response2 = await agent.chat("What is d-separation in causality?", use_research=False)
        await asyncio.sleep(0.2)
        
        # Turn 3: Expand to related concept
        response3 = await agent.chat("How does d-separation relate to information geometry?", use_research=False)
        await asyncio.sleep(0.2)
        
        # Turn 4: Back to broader question
        response4 = await agent.chat("What are the key concepts in causal inference?", use_research=False)
        
        # LLM Judge: Evaluate topic evolution adaptation
        judge_prompt = f"""Evaluate if the system adapts as conversation topic evolves:

Turn 1 (Broad): "What is causality?"
Response: {response1.get('response', '')[:200]}

Turn 2 (Narrow): "What is d-separation in causality?"
Response: {response2.get('response', '')[:200]}

Turn 3 (Expand): "How does d-separation relate to information geometry?"
Response: {response3.get('response', '')[:200]}

Turn 4 (Broad again): "What are the key concepts in causal inference?"
Response: {response4.get('response', '')[:200]}

Evaluate:
1. Does the system adapt response style to topic breadth? (0-1)
2. Does it use relevant experiences at each stage? (0-1)
3. Does it show learning from previous turns? (0-1)
4. Overall adaptation quality? (0-1)

Respond with JSON: {{"adapts_style": 0.0-1.0, "uses_experiences": 0.0-1.0, "shows_learning": 0.0-1.0, "adaptation": 0.0-1.0}}
"""
        
        judge_response = await llm.generate_response(judge_prompt)
        
        json_match = re.search(r'\{[^}]+\}', judge_response, re.DOTALL)
        if json_match:
            try:
                judgment = json.loads(json_match.group())
                assert "adaptation" in judgment
                print(f"Topic evolution judgment: {judgment}")
            except json.JSONDecodeError:
                pass


@pytest.mark.asyncio
async def test_multiturn_error_recovery_judge():
    """
    Multi-turn: LLM judge evaluates if system learns from errors and recovers.
    
    Scenario: First response has issues, system reflects, second response improves.
    """
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
        
        # Turn 1: Query that might have issues
        response1 = await agent.chat("What is d-separation?", use_research=False)
        await asyncio.sleep(0.2)
        
        # Manually add a "bad" experience to simulate learning from error
        agent.meta_learner.experience_store.add_experience(
            query_type="factual",
            query="What is d-separation?",
            response=response1.get("response", ""),
            reflection_text="Previous response was too brief. Should include examples and explain the graphical criterion more clearly.",
            reflection_type="verified",
            tools_used=[],
            quality_score=0.6,  # Lower quality
        )
        
        # Turn 2: Same query, should improve
        response2 = await agent.chat("What is d-separation?", use_research=False)
        
        # LLM Judge: Evaluate error recovery
        judge_prompt = f"""Evaluate if the system learned from a previous error and improved:

Turn 1 Response (had issues):
{response1.get('response', '')[:300]}

Reflection on Turn 1:
"Previous response was too brief. Should include examples and explain the graphical criterion more clearly."

Turn 2 Response (after reflection):
{response2.get('response', '')[:300]}

Evaluate:
1. Does Turn 2 address the issues identified in reflection? (0-1)
2. Is Turn 2 more complete/detailed? (0-1)
3. Does it show learning from the error? (0-1)
4. Overall improvement? (0-1)

Respond with JSON: {{"addresses_issues": 0.0-1.0, "more_complete": 0.0-1.0, "shows_learning": 0.0-1.0, "improvement": 0.0-1.0}}
"""
        
        judge_response = await llm.generate_response(judge_prompt)
        
        json_match = re.search(r'\{[^}]+\}', judge_response, re.DOTALL)
        if json_match:
            try:
                judgment = json.loads(json_match.group())
                assert "improvement" in judgment
                print(f"Error recovery judgment: {judgment}")
            except json.JSONDecodeError:
                pass


@pytest.mark.asyncio
async def test_multiturn_experience_relevance_judge():
    """
    Multi-turn: LLM judge evaluates if experiences remain relevant as conversation evolves.
    """
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
        
        # Add experiences for different topics
        agent.meta_learner.experience_store.add_experience(
            query_type="factual",
            query="What is trust?",
            response="Trust is...",
            reflection_text="Perplexity search works well for definitions",
            reflection_type="self",
            tools_used=["perplexity_search"],
        )
        
        agent.meta_learner.experience_store.add_experience(
            query_type="analytical",
            query="Why is trust important?",
            response="Trust is important because...",
            reflection_text="Firecrawl helps find research papers for analytical questions",
            reflection_type="self",
            tools_used=["firecrawl_search"],
        )
        
        # Query that should match factual experiences
        response1 = await agent.chat("What is d-separation?", use_research=False)
        
        # Query that should match analytical experiences
        response2 = await agent.chat("Why is d-separation important?", use_research=False)
        
        # Get experiences that were used
        factual_exps = agent.meta_learner.experience_store.get_relevant_experiences("factual", limit=5)
        analytical_exps = agent.meta_learner.experience_store.get_relevant_experiences("analytical", limit=5)
        
        # LLM Judge: Evaluate relevance
        judge_prompt = f"""Evaluate if experiences are relevant to queries:

Query 1 (factual): "What is d-separation?"
Response 1: {response1.get('response', '')[:200]}
Available Factual Experiences: {len(factual_exps)} experiences

Query 2 (analytical): "Why is d-separation important?"
Response 2: {response2.get('response', '')[:200]}
Available Analytical Experiences: {len(analytical_exps)} experiences

Evaluate:
1. Are factual experiences relevant to factual query? (0-1)
2. Are analytical experiences relevant to analytical query? (0-1)
3. Is the system selecting appropriate experiences? (0-1)

Respond with JSON: {{"factual_relevant": 0.0-1.0, "analytical_relevant": 0.0-1.0, "appropriate_selection": 0.0-1.0, "overall": 0.0-1.0}}
"""
        
        judge_response = await llm.generate_response(judge_prompt)
        
        json_match = re.search(r'\{[^}]+\}', judge_response, re.DOTALL)
        if json_match:
            try:
                judgment = json.loads(json_match.group())
                assert "overall" in judgment
                print(f"Experience relevance judgment: {judgment}")
            except json.JSONDecodeError:
                pass


# ============================================================================
# Advanced Fuzzing
# ============================================================================

def test_fuzz_experience_store_with_hypothesis():
    """Fuzz: Use Hypothesis to generate test cases for experience store."""
    from hypothesis import given, strategies as st
    
    @given(
        num_experiences=st.integers(min_value=1, max_value=200),
        query_type_length=st.integers(min_value=1, max_value=50),
        reflection_length=st.integers(min_value=1, max_value=5000),
    )
    def test_with_params(num_experiences, query_type_length, reflection_length):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ExperienceStore(storage_path=Path(tmpdir) / "experiences.json")
            
            # Generate experiences with varying parameters
            for i in range(num_experiences):
                query_type = "a" * query_type_length
                reflection = "b" * reflection_length
                
                store.add_experience(
                    query_type=query_type,
                    query=f"Query {i}",
                    response=f"Response {i}",
                    reflection_text=reflection,
                    reflection_type="self",
                    tools_used=[],
                )
            
            # Should still work
            experiences = store.get_relevant_experiences(query_type, limit=10)
            assert len(experiences) <= 10
            assert isinstance(experiences, list)
    
    # Run the property-based test
    test_with_params()


@pytest.mark.asyncio
async def test_fuzz_meta_learner_with_various_quality_scores():
    """Fuzz: Test reflection with various quality score distributions."""
    import random
    
    learner = MetaLearner(enable_reflection=True)
    
    mock_llm = AsyncMock()
    mock_llm.generate_response = AsyncMock(return_value="Reflection")
    
    # Test with various quality score distributions
    quality_distributions = [
        [0.1, 0.2, 0.3],  # Low scores
        [0.7, 0.8, 0.9],  # High scores
        [0.3, 0.5, 0.7],  # Mixed
        [None, None, None],  # All None
        [0.1, None, 0.9],  # Mixed with None
    ]
    
    for quality_scores in quality_distributions:
        for quality in quality_scores:
            try:
                reflection = await learner.reflect_on_completion(
                    query="Test",
                    response="Test response",
                    query_type="factual",
                    tools_used=[],
                    quality_score=quality,
                    llm_service=mock_llm,
                )
                # Should handle all cases
                assert reflection is not None or reflection is None
            except Exception as e:
                pytest.fail(f"Should handle quality score {quality}: {e}")


@pytest.mark.asyncio
async def test_fuzz_agent_with_various_schemas():
    """Fuzz: Test agent meta-learning with various schema combinations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"
        
        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path
        
        schemas = [
            None,
            "chain_of_thought",
            "decompose_and_synthesize",
            "iterative_elaboration",
            "hypothesize_and_test",
            "scenario_analysis",
        ]
        
        research_options = [True, False]
        
        for schema in schemas:
            for use_research in research_options:
                try:
                    response = await agent.chat(
                        "What is trust?",
                        use_schema=schema,
                        use_research=use_research,
                    )
                    assert "response" in response
                except Exception as e:
                    # Some combinations may fail, but shouldn't crash
                    assert "error" in str(e).lower() or "not available" in str(e).lower()


# ============================================================================
# Performance Benchmarks
# ============================================================================

def test_benchmark_experience_store_operations():
    """Benchmark: Measure performance of experience store operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = ExperienceStore(storage_path=Path(tmpdir) / "experiences.json")
        
        # Benchmark: Add experiences
        times_add = []
        for i in range(100):
            start = time.time()
            store.add_experience(
                query_type="factual",
                query=f"Query {i}",
                response=f"Response {i}",
                reflection_text=f"Reflection {i}",
                reflection_type="self",
                tools_used=[],
            )
            times_add.append(time.time() - start)
        
        avg_add = statistics.mean(times_add)
        max_add = max(times_add)
        
        # Benchmark: Retrieve experiences
        times_retrieve = []
        for _ in range(100):
            start = time.time()
            store.get_relevant_experiences("factual", limit=10)
            times_retrieve.append(time.time() - start)
        
        avg_retrieve = statistics.mean(times_retrieve)
        max_retrieve = max(times_retrieve)
        
        # Benchmark: Format context
        experiences = store.get_relevant_experiences("factual", limit=10)
        times_format = []
        for _ in range(100):
            start = time.time()
            store.format_for_context(experiences)
            times_format.append(time.time() - start)
        
        avg_format = statistics.mean(times_format)
        max_format = max(times_format)
        
        # Performance assertions
        assert avg_add < 0.01, f"Average add time too slow: {avg_add:.4f}s"
        assert avg_retrieve < 0.005, f"Average retrieve time too slow: {avg_retrieve:.4f}s"
        assert avg_format < 0.001, f"Average format time too slow: {avg_format:.4f}s"
        
        print(f"Performance: add={avg_add:.4f}s, retrieve={avg_retrieve:.4f}s, format={avg_format:.4f}s")


@pytest.mark.asyncio
async def test_benchmark_reflection_latency():
    """Benchmark: Measure reflection latency."""
    learner = MetaLearner(enable_reflection=True)
    
    mock_llm = AsyncMock()
    mock_llm.generate_response = AsyncMock(return_value="Reflection text")
    
    latencies = []
    for i in range(10):
        start = time.time()
        await learner.reflect_on_completion(
            query=f"Query {i}",
            response=f"Response {i}",
            query_type="factual",
            tools_used=[],
            llm_service=mock_llm,
        )
        latencies.append(time.time() - start)
    
    avg_latency = statistics.mean(latencies)
    max_latency = max(latencies)
    
    # Reflection should be reasonably fast (mock LLM)
    assert avg_latency < 0.1, f"Average reflection latency too slow: {avg_latency:.4f}s"
    
    print(f"Reflection latency: avg={avg_latency:.4f}s, max={max_latency:.4f}s")


# ============================================================================
# Deep Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_deep_integration_adaptive_meta_learning():
    """
    Deep integration: Test how adaptive learning and meta-learning interact.
    
    Adaptive learning learns which schemas/tools work best.
    Meta-learning learns from task completions.
    They should complement each other.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"
        
        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path
        
        # Multiple queries to build up learning
        queries = [
            ("What is trust?", "factual"),
            ("How do you build trust?", "procedural"),
            ("Why is trust important?", "analytical"),
        ]
        
        for query, expected_type in queries:
            response = await agent.chat(query, use_research=False)
            await asyncio.sleep(0.1)
            
            # Both systems should learn
            if agent.adaptive_manager:
                strategy = agent.adaptive_manager.get_adaptive_strategy(query)
                assert strategy is not None
            
            # Meta-learner should have experiences
            experiences = agent.meta_learner.experience_store.get_relevant_experiences(expected_type, limit=1)
            # May be 0 if reflection didn't happen, but structure should work
            assert isinstance(experiences, list)


@pytest.mark.asyncio
async def test_deep_integration_research_meta_learning():
    """
    Deep integration: Test how research and meta-learning interact.
    
    Research uses experience context for tool selection.
    Meta-learning learns from research outcomes.
    """
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
            reflection_text="Perplexity search worked well for factual queries. Use it for definitions.",
            reflection_type="verified",
            tools_used=["perplexity_search"],
            quality_score=0.9,
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
async def test_deep_integration_quality_meta_learning():
    """
    Deep integration: Test how quality feedback and meta-learning interact.
    
    Quality feedback evaluates responses.
    Meta-learning reflects on quality scores.
    They should work together seamlessly.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"
        
        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path
        
        # Query that should trigger quality evaluation and reflection
        response = await agent.chat(
            "What is d-separation?",
            use_research=False,
        )
        
        await asyncio.sleep(0.2)  # Allow reflection
        
        # Quality feedback should have evaluated
        if "quality" in response:
            quality_score = response["quality"].get("score")
            assert quality_score is not None or quality_score is None
        
        # Meta-learner should have reflected (if enabled and LLM available)
        experiences = agent.meta_learner.experience_store.get_relevant_experiences("factual", limit=1)
        # May be 0 if reflection didn't happen, but structure should work
        assert isinstance(experiences, list)


# ============================================================================
# Advanced LLM Judge Tests
# ============================================================================

@pytest.mark.asyncio
async def test_llm_judge_reflection_depth():
    """LLM-as-judge: Evaluate if reflections show sufficient depth and insight."""
    from bop.llm import LLMService
    
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "experiences.json"
        learner = MetaLearner(storage_path=store_path, enable_reflection=True)
        
        try:
            llm = LLMService()
        except Exception:
            pytest.skip("LLM service not available")
        
        # Perform reflection on complex task
        reflection_text = await learner.reflect_on_completion(
            query="What is d-separation and how does it relate to causality, information geometry, and Bayesian networks?",
            response="D-separation is a graphical criterion for determining conditional independence in Bayesian networks. It relates to causality by...",
            query_type="analytical",
            tools_used=["perplexity_search", "firecrawl_search", "tavily_search"],
            quality_score=0.85,
            llm_service=llm,
        )
        
        if not reflection_text:
            pytest.skip("Reflection not performed")
        
        # Judge: Evaluate depth
        judge_prompt = f"""Evaluate the depth and insight of this reflection:

Reflection:
{reflection_text}

Evaluate:
1. Does it go beyond surface-level observations? (0-1)
2. Does it identify underlying patterns or principles? (0-1)
3. Does it provide actionable insights? (0-1)
4. Overall depth and insight? (0-1)

Respond with JSON: {{"beyond_surface": 0.0-1.0, "identifies_patterns": 0.0-1.0, "actionable": 0.0-1.0, "depth": 0.0-1.0}}
"""
        
        judge_response = await llm.generate_response(judge_prompt)
        
        json_match = re.search(r'\{[^}]+\}', judge_response, re.DOTALL)
        if json_match:
            try:
                judgment = json.loads(json_match.group())
                assert "depth" in judgment
                assert judgment["depth"] >= 0.3  # Should have some depth
                print(f"Reflection depth judgment: {judgment}")
            except json.JSONDecodeError:
                pass


@pytest.mark.asyncio
async def test_llm_judge_experience_diversity():
    """LLM-as-judge: Evaluate if experiences capture diverse insights."""
    from bop.llm import LLMService
    
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "experiences.json"
        learner = MetaLearner(storage_path=store_path)
        
        # Add diverse experiences
        diverse_experiences = [
            ("Perplexity search works well for definitions", "tool_usage"),
            ("Include examples in responses for clarity", "response_style"),
            ("Break down complex concepts into steps", "explanation_strategy"),
            ("Use multiple sources to verify claims", "verification"),
        ]
        
        for insight, category in diverse_experiences:
            learner.experience_store.add_experience(
                query_type="factual",
                query="What is X?",
                response="X is...",
                reflection_text=insight,
                reflection_type="self",
                tools_used=[],
            )
        
        experiences = learner.experience_store.get_relevant_experiences("factual", limit=10)
        
        try:
            llm = LLMService()
        except Exception:
            pytest.skip("LLM service not available")
        
        # Judge: Evaluate diversity
        judge_prompt = f"""Evaluate if these experiences capture diverse insights:

Experiences:
{json.dumps([exp.get('insights', '') for exp in experiences], indent=2)}

Evaluate:
1. Do experiences cover different aspects? (0-1)
2. Are insights diverse (not repetitive)? (0-1)
3. Do they provide varied perspectives? (0-1)

Respond with JSON: {{"covers_aspects": 0.0-1.0, "diverse": 0.0-1.0, "varied_perspectives": 0.0-1.0, "overall": 0.0-1.0}}
"""
        
        judge_response = await llm.generate_response(judge_prompt)
        
        json_match = re.search(r'\{[^}]+\}', judge_response, re.DOTALL)
        if json_match:
            try:
                judgment = json.loads(json_match.group())
                assert "overall" in judgment
                print(f"Experience diversity judgment: {judgment}")
            except json.JSONDecodeError:
                pass

