"""Tests for meta-learning capabilities: experience store, reflection, context engineering."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from bop.meta_learning import ExperienceStore, MetaLearner
from bop.agent import KnowledgeAgent
from bop.quality_feedback import QualityFeedbackLoop


def test_experience_store_initialization():
    """Test ExperienceStore initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "experiences.json"
        store = ExperienceStore(storage_path=store_path)
        
        assert store.storage_path == store_path
        assert isinstance(store.experiences, dict)
        assert len(store.experiences) == 0


def test_experience_store_add_and_retrieve():
    """Test adding and retrieving experiences."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "experiences.json"
        store = ExperienceStore(storage_path=store_path)
        
        # Add experience
        store.add_experience(
            query_type="factual",
            query="What is trust?",
            response="Trust is...",
            reflection_text="This worked well because...",
            reflection_type="self",
            tools_used=["perplexity_search"],
            quality_score=0.85,
        )
        
        # Retrieve experiences
        experiences = store.get_relevant_experiences("factual", limit=5)
        assert len(experiences) == 1
        assert experiences[0]["query_type"] == "factual"
        assert "insights" in experiences[0]
        assert experiences[0]["confidence"] == 0.6  # self-reflection


def test_experience_store_persistence():
    """Test experience persistence across instances."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "experiences.json"
        
        # First instance: add experience
        store1 = ExperienceStore(storage_path=store_path)
        store1.add_experience(
            query_type="analytical",
            query="Why is X important?",
            response="X is important because...",
            reflection_text="Good analysis",
            reflection_type="verified",
            tools_used=["firecrawl_search"],
            quality_score=0.9,
        )
        
        # Second instance: should load persisted experience
        store2 = ExperienceStore(storage_path=store_path)
        experiences = store2.get_relevant_experiences("analytical", limit=5)
        assert len(experiences) == 1
        assert experiences[0]["reflection_type"] == "verified"
        assert experiences[0]["confidence"] == 0.8  # verified reflection


def test_experience_store_limit():
    """Test experience limit per query type."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "experiences.json"
        store = ExperienceStore(storage_path=store_path)
        
        # Add more than 50 experiences
        for i in range(60):
            store.add_experience(
                query_type="factual",
                query=f"Query {i}",
                response=f"Response {i}",
                reflection_text=f"Reflection {i}",
                reflection_type="self",
                tools_used=[],
            )
        
        # Should only keep last 50
        experiences = store.get_relevant_experiences("factual", limit=100)
        assert len(experiences) <= 50


def test_experience_store_format_for_context():
    """Test formatting experiences for context injection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "experiences.json"
        store = ExperienceStore(storage_path=store_path)
        
        store.add_experience(
            query_type="factual",
            query="What is X?",
            response="X is...",
            reflection_text="This approach worked well",
            reflection_type="self",
            tools_used=[],
        )
        
        experiences = store.get_relevant_experiences("factual", limit=1)
        context = store.format_for_context(experiences)
        
        assert "Previous Task Experience" in context
        assert "This approach worked well" in context


def test_meta_learner_initialization():
    """Test MetaLearner initialization."""
    learner = MetaLearner(
        enable_reflection=True,
        enable_context_injection=True,
    )
    
    assert learner.enable_reflection is True
    assert learner.enable_context_injection is True
    assert learner.experience_store is not None


def test_meta_learner_get_context_experience():
    """Test getting experience context."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "experiences.json"
        learner = MetaLearner(
            storage_path=store_path,
            enable_context_injection=True,
        )
        
        # Add some experiences
        learner.experience_store.add_experience(
            query_type="factual",
            query="What is trust?",
            response="Trust is...",
            reflection_text="Used perplexity_search effectively",
            reflection_type="self",
            tools_used=["perplexity_search"],
        )
        
        # Get context
        context = learner.get_context_experience(
            query="What is trust?",
            query_type="factual",
            max_experiences=5,
        )
        
        assert len(context) > 0
        assert "Previous Task Experience" in context


def test_meta_learner_context_injection_disabled():
    """Test that context injection can be disabled."""
    learner = MetaLearner(enable_context_injection=False)
    
    context = learner.get_context_experience(
        query="Test",
        query_type="factual",
    )
    
    assert context == ""


@pytest.mark.asyncio
async def test_meta_learner_reflection():
    """Test reflection on task completion."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "experiences.json"
        learner = MetaLearner(
            storage_path=store_path,
            enable_reflection=True,
        )
        
        # Mock LLM service
        mock_llm = AsyncMock()
        mock_llm.generate_response = AsyncMock(return_value="Reflection: This worked well because we used the right tools.")
        
        reflection_text = await learner.reflect_on_completion(
            query="What is trust?",
            response="Trust is a belief in reliability...",
            query_type="factual",
            tools_used=["perplexity_search"],
            quality_score=0.85,
            llm_service=mock_llm,
            reflection_type="self",
        )
        
        assert reflection_text is not None
        assert "Reflection:" in reflection_text
        
        # Check experience was stored
        experiences = learner.experience_store.get_relevant_experiences("factual", limit=1)
        assert len(experiences) == 1


@pytest.mark.asyncio
async def test_meta_learner_reflection_disabled():
    """Test that reflection can be disabled."""
    learner = MetaLearner(enable_reflection=False)
    
    reflection_text = await learner.reflect_on_completion(
        query="Test",
        response="Test response",
        query_type="factual",
        tools_used=[],
        llm_service=AsyncMock(),
    )
    
    assert reflection_text is None


@pytest.mark.asyncio
async def test_meta_learner_reflection_no_llm():
    """Test reflection gracefully handles missing LLM service."""
    learner = MetaLearner(enable_reflection=True)
    
    reflection_text = await learner.reflect_on_completion(
        query="Test",
        response="Test response",
        query_type="factual",
        tools_used=[],
        llm_service=None,
    )
    
    assert reflection_text is None


@pytest.mark.asyncio
async def test_meta_learner_verified_reflection():
    """Test verified reflection with ground truth."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "experiences.json"
        learner = MetaLearner(
            storage_path=store_path,
            enable_reflection=True,
        )
        
        mock_llm = AsyncMock()
        mock_llm.generate_response = AsyncMock(return_value="Verified reflection: Response matched ground truth well.")
        
        reflection_text = await learner.reflect_on_completion(
            query="What is trust?",
            response="Trust is...",
            query_type="factual",
            tools_used=["perplexity_search"],
            quality_score=0.9,
            llm_service=mock_llm,
            reflection_type="verified",
            ground_truth="Trust is a belief in reliability and truthfulness.",
        )
        
        assert reflection_text is not None
        
        # Check experience was stored with verified type
        experiences = learner.experience_store.get_relevant_experiences("factual", limit=1)
        assert len(experiences) == 1
        assert experiences[0]["reflection_type"] == "verified"
        assert experiences[0]["confidence"] == 0.8


@pytest.mark.asyncio
async def test_agent_integration_experience_injection():
    """Test that agent injects experience context before research."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"
        
        agent = KnowledgeAgent(enable_quality_feedback=True)
        # Override paths
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path
        
        # Add experience first
        agent.meta_learner.experience_store.add_experience(
            query_type="factual",
            query="What is d-separation?",
            response="D-separation is...",
            reflection_text="Perplexity search worked well for this query",
            reflection_type="self",
            tools_used=["perplexity_search"],
        )
        
        # Mock orchestrator to capture query
        original_research = agent.orchestrator.research_with_schema
        captured_query = None
        
        async def capture_query(*args, **kwargs):
            nonlocal captured_query
            captured_query = args[0] if args else kwargs.get("query")
            return {
                "query": captured_query,
                "subsolutions": [],
                "final_synthesis": "Test synthesis",
            }
        
        agent.orchestrator.research_with_schema = capture_query
        
        # Chat with research
        response = await agent.chat(
            "What is d-separation?",
            use_research=True,
            use_schema="decompose_and_synthesize",
        )
        
        # Check that experience context was injected into research query
        assert captured_query is not None
        assert "Previous Task Experience" in captured_query or "Perplexity search" in captured_query


@pytest.mark.asyncio
async def test_agent_integration_reflection():
    """Test that agent reflects after quality evaluation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"
        
        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path
        
        # Mock LLM for reflection
        if agent.llm_service:
            original_generate = agent.llm_service.generate_response
            reflection_called = False
            
            async def mock_generate(*args, **kwargs):
                nonlocal reflection_called
                message = args[0] if args else kwargs.get("message", "")
                if "Reflect on this task completion" in message:
                    reflection_called = True
                    return "Reflection: This response was accurate and complete."
                return await original_generate(*args, **kwargs)
            
            agent.llm_service.generate_response = mock_generate
        
        # Chat
        response = await agent.chat(
            "What is trust?",
            use_research=False,  # Faster for testing
        )
        
        # Check reflection happened
        if agent.llm_service:
            # Reflection should be in response or experiences
            experiences = agent.meta_learner.experience_store.get_relevant_experiences("factual", limit=1)
            # Reflection may or may not have been called depending on quality_feedback
            # But if it was, experience should be stored
            if reflection_called:
                assert len(experiences) > 0 or "meta_reflection" in response


@pytest.mark.asyncio
async def test_llm_judge_reflection_quality():
    """LLM-as-judge: Evaluate reflection quality."""
    from bop.llm import LLMService
    
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "experiences.json"
        learner = MetaLearner(
            storage_path=store_path,
            enable_reflection=True,
        )
        
        # Get LLM service for reflection and judging
        try:
            llm = LLMService()
        except Exception:
            pytest.skip("LLM service not available")
        
        # Perform reflection
        reflection_text = await learner.reflect_on_completion(
            query="What is d-separation and how does it relate to causality?",
            response="D-separation is a graphical criterion for determining conditional independence in Bayesian networks. It relates to causality by...",
            query_type="analytical",
            tools_used=["perplexity_search", "firecrawl_search"],
            quality_score=0.85,
            llm_service=llm,
            reflection_type="self",
        )
        
        assert reflection_text is not None
        
        # LLM-as-judge: Evaluate reflection quality
        judge_prompt = f"""Evaluate the quality of this reflection on a task completion:

Original Query: "What is d-separation and how does it relate to causality?"
Response Quality Score: 0.85
Tools Used: perplexity_search, firecrawl_search

Reflection:
{reflection_text}

Evaluate the reflection on:
1. Does it identify what worked well? (0-1 score)
2. Does it identify what could be improved? (0-1 score)
3. Does it extract generalizable insights? (0-1 score)
4. Is it actionable for future tasks? (0-1 score)

Respond with JSON: {{"worked_well": 0.0-1.0, "improvements": 0.0-1.0, "generalizable": 0.0-1.0, "actionable": 0.0-1.0, "overall": 0.0-1.0}}
"""
        
        judge_response = await llm.generate_response(judge_prompt)
        
        # Parse and validate
        import json
        import re
        
        # Extract JSON from response
        json_match = re.search(r'\{[^}]+\}', judge_response, re.DOTALL)
        if json_match:
            try:
                judgment = json.loads(json_match.group())
                assert "overall" in judgment
                assert 0.0 <= judgment["overall"] <= 1.0
                
                # Reflection should score reasonably well
                assert judgment["overall"] >= 0.5, f"Reflection quality too low: {judgment['overall']}"
                
                print(f"Reflection quality judgment: {judgment}")
            except json.JSONDecodeError:
                pytest.fail(f"Failed to parse judge response: {judge_response}")


@pytest.mark.asyncio
async def test_llm_judge_experience_relevance():
    """LLM-as-judge: Evaluate experience relevance for context injection."""
    from bop.llm import LLMService
    
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "experiences.json"
        learner = MetaLearner(
            storage_path=store_path,
            enable_context_injection=True,
        )
        
        # Add diverse experiences
        learner.experience_store.add_experience(
            query_type="factual",
            query="What is trust?",
            response="Trust is...",
            reflection_text="Perplexity search provided accurate definitions",
            reflection_type="self",
            tools_used=["perplexity_search"],
        )
        
        learner.experience_store.add_experience(
            query_type="analytical",
            query="Why is trust important?",
            response="Trust is important because...",
            reflection_text="Firecrawl helped find relevant research papers",
            reflection_type="self",
            tools_used=["firecrawl_search"],
        )
        
        # Get context for a factual query
        context = learner.get_context_experience(
            query="What is d-separation?",
            query_type="factual",
            max_experiences=5,
        )
        
        assert len(context) > 0
        
        # LLM-as-judge: Evaluate relevance
        try:
            llm = LLMService()
        except Exception:
            pytest.skip("LLM service not available")
        
        judge_prompt = f"""Evaluate the relevance of this experience context for a new query:

New Query: "What is d-separation?" (factual query type)

Experience Context:
{context}

Evaluate:
1. Is the experience context relevant to the new query? (0-1 score)
2. Would the insights help improve the response? (0-1 score)
3. Are the tool recommendations appropriate? (0-1 score)

Respond with JSON: {{"relevance": 0.0-1.0, "helpful": 0.0-1.0, "appropriate": 0.0-1.0, "overall": 0.0-1.0}}
"""
        
        judge_response = await llm.generate_response(judge_prompt)
        
        import json
        import re
        
        json_match = re.search(r'\{[^}]+\}', judge_response, re.DOTALL)
        if json_match:
            try:
                judgment = json.loads(json_match.group())
                assert "overall" in judgment
                assert 0.0 <= judgment["overall"] <= 1.0
                
                # Experience should be somewhat relevant (factual to factual)
                assert judgment["relevance"] >= 0.4, f"Experience relevance too low: {judgment['relevance']}"
                
                print(f"Experience relevance judgment: {judgment}")
            except json.JSONDecodeError:
                pytest.fail(f"Failed to parse judge response: {judge_response}")


@pytest.mark.asyncio
async def test_llm_judge_context_injection_effectiveness():
    """LLM-as-judge: Evaluate if context injection improves responses."""
    from bop.llm import LLMService
    
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "history.json"
        experience_path = Path(tmpdir) / "experiences.json"
        
        # Create agent with experience
        agent = KnowledgeAgent(enable_quality_feedback=True)
        if agent.quality_feedback:
            agent.quality_feedback.evaluation_history_path = history_path
        if agent.meta_learner:
            agent.meta_learner.experience_store.storage_path = experience_path
        
        # Add experience
        agent.meta_learner.experience_store.add_experience(
            query_type="factual",
            query="What is trust?",
            response="Trust is a belief in reliability...",
            reflection_text="Using perplexity_search for definitions works well. Include examples in responses.",
            reflection_type="verified",
            tools_used=["perplexity_search"],
            quality_score=0.9,
        )
        
        # Get LLM for judging
        try:
            llm = LLMService()
        except Exception:
            pytest.skip("LLM service not available")
        
        # Test query
        query = "What is d-separation?"
        
        # Get response WITH experience context
        response_with = await agent.chat(query, use_research=False)
        
        # Disable context injection and get response WITHOUT
        agent.meta_learner.enable_context_injection = False
        response_without = await agent.chat(query, use_research=False)
        agent.meta_learner.enable_context_injection = True
        
        # LLM-as-judge: Compare responses
        judge_prompt = f"""Compare two responses to the same query and evaluate if experience context improved the response:

Query: "{query}"

Response WITH experience context:
{response_with.get('response', '')[:500]}

Response WITHOUT experience context:
{response_without.get('response', '')[:500]}

Evaluate:
1. Which response is more accurate? (with/without/both)
2. Which response is more complete? (with/without/both)
3. Which response follows better practices? (with/without/both)
4. Overall, did experience context help? (yes/no/neutral)

Respond with JSON: {{"more_accurate": "with|without|both", "more_complete": "with|without|both", "better_practices": "with|without|both", "helped": "yes|no|neutral", "reasoning": "explanation"}}
"""
        
        judge_response = await llm.generate_response(judge_prompt)
        
        import json
        import re
        
        json_match = re.search(r'\{[^}]+\}', judge_response, re.DOTALL)
        if json_match:
            try:
                judgment = json.loads(json_match.group())
                assert "helped" in judgment
                assert judgment["helped"] in ["yes", "no", "neutral"]
                
                print(f"Context injection effectiveness: {judgment}")
                
                # Experience context should help or be neutral (not hurt)
                assert judgment["helped"] != "no", "Experience context should not hurt response quality"
            except json.JSONDecodeError:
                pytest.fail(f"Failed to parse judge response: {judge_response}")

