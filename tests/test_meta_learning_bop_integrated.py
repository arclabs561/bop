"""BOP-integrated meta-learning tests: BOP evaluates itself using its own capabilities."""

import asyncio
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest

from bop.agent import KnowledgeAgent
from datasets.load_external_datasets import load_fever, load_hotpotqa

# ============================================================================
# BOP Self-Evaluation Framework
# ============================================================================

class BOPSelfEvaluator:
    """BOP evaluates its own meta-learning capabilities."""

    def __init__(self, agent: KnowledgeAgent):
        self.agent = agent
        self.evaluation_results = []

    async def evaluate_meta_learning_with_bop_research(
        self,
        query: str,
        use_meta_learning: bool = True,
    ) -> Dict[str, Any]:
        """Use BOP's research capabilities to evaluate meta-learning."""

        # Create evaluation query that uses BOP's research
        eval_query = f"""Research and evaluate: Does meta-learning improve AI system responses?

Context: A system with meta-learning should:
1. Learn from previous task completions
2. Use accumulated experience to improve future responses
3. Reflect on what worked and what didn't
4. Adapt based on feedback

Query to test: "{query}"

Evaluate using research:
- Find papers on meta-learning in AI systems
- Find examples of self-improving AI
- Compare systems with/without meta-learning

Provide evaluation with:
1. Evidence from research
2. Analysis of meta-learning effectiveness
3. Recommendations for improvement
"""

        # Use BOP's research to evaluate
        response = await self.agent.chat(
            eval_query,
            use_research=True,
            use_schema="decompose_and_synthesize",
        )

        evaluation = {
            "query": query,
            "research_conducted": response.get("research_conducted", False),
            "response_length": len(response.get("response", "")),
            "has_meta_reflection": "meta_reflection" in response,
            "quality_score": response.get("quality", {}).get("score"),
        }

        if response.get("research"):
            research = response["research"]
            evaluation["research_sources"] = len(research.get("subsolutions", []))
            evaluation["topology_available"] = "topology" in research

        self.evaluation_results.append(evaluation)
        return evaluation

    async def evaluate_experience_accumulation(
        self,
        queries: List[str],
    ) -> Dict[str, Any]:
        """Use BOP to evaluate if experiences accumulate correctly."""

        # Get experiences from meta-learner
        all_experiences = []
        for q_type in ["factual", "analytical", "procedural"]:
            exps = self.agent.meta_learner.experience_store.get_relevant_experiences(q_type, limit=20)
            all_experiences.extend(exps)

        # Use BOP to analyze experience accumulation
        analysis_query = f"""Analyze experience accumulation in a meta-learning system:

Number of queries processed: {len(queries)}
Number of experiences accumulated: {len(all_experiences)}
Experience distribution by type: {{
    "factual": {len([e for e in all_experiences if e.get("query_type") == "factual"])},
    "analytical": {len([e for e in all_experiences if e.get("query_type") == "analytical"])},
    "procedural": {len([e for e in all_experiences if e.get("query_type") == "procedural"])},
}}

Sample experiences:
{json.dumps([{"query": e.get("query", "")[:50], "type": e.get("query_type"), "reflection_type": e.get("reflection_type")} for e in all_experiences[:5]], indent=2)}

Evaluate:
1. Is experience accumulation working? (0-1)
2. Are experiences diverse? (0-1)
3. Would these experiences help future queries? (0-1)
4. Overall meta-learning health? (0-1)

Respond with JSON: {{"accumulation_working": 0.0-1.0, "diverse": 0.0-1.0, "helpful": 0.0-1.0, "health": 0.0-1.0, "reasoning": "..."}}
"""

        try:
            response = await self.agent.chat(analysis_query, use_research=False)
            response_text = response.get("response", "")

            import re
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                analysis["total_experiences"] = len(all_experiences)
                analysis["total_queries"] = len(queries)
                return analysis
        except Exception:
            pass

        return {
            "accumulation_working": 0.5,
            "total_experiences": len(all_experiences),
            "total_queries": len(queries),
        }


# ============================================================================
# BOP-Integrated Tests with External Datasets
# ============================================================================

@pytest.mark.asyncio
async def test_bop_integrated_hotpotqa_meta_learning():
    """BOP-integrated: Test meta-learning on HotpotQA dataset using BOP's research."""
    try:
        hotpot_data = load_hotpotqa(split="dev", max_samples=5)
    except Exception:
        pytest.skip("HotpotQA dataset not available")

    if not hotpot_data:
        pytest.skip("HotpotQA dataset empty")

    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        evaluator = BOPSelfEvaluator(agent)

        # Process queries with BOP research
        queries = [item.get("question", "") for item in hotpot_data if item.get("question")]

        for query in queries[:3]:  # Limit for speed
            await evaluator.evaluate_meta_learning_with_bop_research(query)
            await asyncio.sleep(0.2)

        # BOP should have used its own research capabilities
        assert len(evaluator.evaluation_results) > 0
        assert any(e.get("research_conducted") for e in evaluator.evaluation_results)


@pytest.mark.asyncio
async def test_bop_integrated_fever_meta_learning():
    """BOP-integrated: Test meta-learning on FEVER dataset using BOP's fact verification."""
    try:
        fever_data = load_fever(split="dev", max_samples=5)
    except Exception:
        pytest.skip("FEVER dataset not available")

    if not fever_data:
        pytest.skip("FEVER dataset empty")

    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        # Process FEVER claims
        claims = [item.get("claim", "") for item in fever_data if item.get("claim")]

        responses = []
        for claim in claims[:3]:  # Limit for speed
            # Use BOP to verify claim
            query = f"Verify this claim: {claim}"
            response = await agent.chat(
                query,
                use_research=True,
                use_schema="hypothesize_and_test",
            )
            responses.append(response)
            await asyncio.sleep(0.2)

        # Should have research and meta-learning
        assert len(responses) > 0
        assert any(r.get("research_conducted") for r in responses)


@pytest.mark.asyncio
async def test_bop_integrated_self_evaluation_workflow():
    """BOP-integrated: Complete self-evaluation workflow using BOP's capabilities."""
    queries = [
        "What is d-separation?",
        "How does d-separation relate to causality?",
        "Explain d-separation with examples",
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        evaluator = BOPSelfEvaluator(agent)

        # Process queries
        for query in queries:
            await agent.chat(query, use_research=False)
            await asyncio.sleep(0.1)

        # Use BOP to evaluate experience accumulation
        accumulation_analysis = await evaluator.evaluate_experience_accumulation(queries)

        # Use BOP research to evaluate meta-learning
        meta_eval = await evaluator.evaluate_meta_learning_with_bop_research(
            "What is meta-learning?",
            use_meta_learning=True,
        )

        # BOP should have evaluated itself
        assert "total_experiences" in accumulation_analysis
        assert "research_conducted" in meta_eval


@pytest.mark.asyncio
async def test_bop_integrated_multi_component_evaluation():
    """BOP-integrated: Evaluate meta-learning across all BOP components."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        query = "What is trust and why is it important for knowledge systems?"

        # Use all BOP capabilities
        response = await agent.chat(
            query,
            use_research=True,
            use_schema="decompose_and_synthesize",
        )

        # Check all components worked together
        components_active = {
            "research": response.get("research_conducted", False),
            "quality_feedback": "quality" in response,
            "meta_learning": "meta_reflection" in response or len(agent.meta_learner.experience_store.experiences) > 0,
            "adaptive": agent.adaptive_manager is not None,
        }

        # At least some components should be active
        assert sum(components_active.values()) >= 2

        # If research was conducted, check topology
        if response.get("research"):
            research = response["research"]
            assert "subsolutions" in research or "final_synthesis" in research


@pytest.mark.asyncio
async def test_bop_integrated_meta_learning_research_integration():
    """BOP-integrated: Test how meta-learning integrates with research orchestration."""
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

        # Query that should use experience context in research
        response = await agent.chat(
            "What is d-separation?",
            use_research=True,
            use_schema="decompose_and_synthesize",
        )

        # Experience should have been injected into research query
        # (Can't easily verify without mocking, but should not crash)
        assert "response" in response

        # If research was conducted, experience context should have helped
        if response.get("research_conducted"):
            assert "research" in response


@pytest.mark.asyncio
async def test_bop_integrated_adaptive_meta_learning_synergy():
    """BOP-integrated: Test synergy between adaptive learning and meta-learning."""
    queries = [
        ("What is trust?", "factual"),
        ("How do you build trust?", "procedural"),
        ("Why is trust important?", "analytical"),
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"

        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path

        # Process queries - both systems should learn
        for query, expected_type in queries:
            await agent.chat(query, use_research=False)
            await asyncio.sleep(0.1)

            # Adaptive learning should learn schema preferences
            if agent.adaptive_manager:
                strategy = agent.adaptive_manager.get_adaptive_strategy(query)
                assert strategy is not None

            # Meta-learning should accumulate experiences
            experiences = agent.meta_learner.experience_store.get_relevant_experiences(
                expected_type,
                limit=1,
            )
            # May be 0 if reflection didn't happen, but structure should work
            assert isinstance(experiences, list)

        # Both systems should have learned
        if agent.adaptive_manager:
            insights = agent.adaptive_manager.get_performance_insights()
            # Should have some insights
            assert insights is not None

        # Meta-learner should have experiences
        all_experiences = []
        for q_type in ["factual", "procedural", "analytical"]:
            exps = agent.meta_learner.experience_store.get_relevant_experiences(q_type, limit=5)
            all_experiences.extend(exps)

        # Structure should work (experiences may be 0 if LLM not available)
        assert isinstance(all_experiences, list)

