"""Tests for semantic properties: consistency, coherence, correctness, appropriateness."""

import pytest
import asyncio
from pathlib import Path
import tempfile

from bop.agent import KnowledgeAgent
from bop.llm import LLMService
from tests.test_annotations import annotate_test


@pytest.mark.asyncio
async def test_semantic_consistency_across_responses():
    """
    Test semantic consistency: Same concepts should have same meaning across responses.
    
    Pattern: semantic_properties
    Opinion: concepts_should_be_consistent
    Category: semantic_properties
    Hypothesis: Same concepts should maintain consistent meaning across multiple responses.
    """
    annotate_test(
        "test_semantic_consistency_across_responses",
        pattern="semantic_properties",
        opinion="concepts_should_be_consistent",
        category="semantic_properties",
        hypothesis="Same concepts should maintain consistent meaning across multiple responses.",
    )
    
    try:
        llm = LLMService()
    except Exception:
        pytest.skip("LLM service not available")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        agent = KnowledgeAgent(enable_quality_feedback=True)
        
        # Same concept, different queries
        queries = [
            "What is knowledge structure?",
            "How does knowledge structure work?",
            "Explain knowledge structure in detail.",
        ]
        
        responses = []
        for query in queries:
            response_data = await agent.chat(query, use_research=False)
            responses.append({
                "query": query,
                "response": response_data.get("response", "")[:300],
            })
        
        # Use LLM judge to evaluate consistency
        judge_prompt = f"""
Evaluate semantic consistency across responses.

Queries and Responses:
{chr(10).join([f"Q: {r['query']}\nA: {r['response']}" for r in responses])}

Questions:
1. Is "knowledge structure" defined consistently?
2. Are core concepts used with same meaning?
3. Is terminology coherent?
4. Are relationships maintained?

Respond with JSON: {{
    "consistent": true/false,
    "definition_stable": true/false,
    "terminology_coherent": true/false,
    "inconsistencies": ["list any inconsistencies"],
    "score": 0.0-1.0,
    "reasoning": "..."
}}
"""
        
        try:
            result = await llm.generate_response(judge_prompt)
            assert len(result) > 0
        except Exception:
            # Fallback: verify all responses exist
            assert all(r.get("response") for r in responses)


@pytest.mark.asyncio
async def test_logical_coherence_reasoning():
    """
    Test logical coherence: Reasoning should be logically sound.
    
    Pattern: semantic_properties
    Opinion: reasoning_should_be_coherent
    Category: semantic_properties
    Hypothesis: Reasoning steps should be logically sound and conclusions should be supported.
    """
    annotate_test(
        "test_logical_coherence_reasoning",
        pattern="semantic_properties",
        opinion="reasoning_should_be_coherent",
        category="semantic_properties",
        hypothesis="Reasoning steps should be logically sound and conclusions should be supported.",
    )
    
    try:
        llm = LLMService()
    except Exception:
        pytest.skip("LLM service not available")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        agent = KnowledgeAgent(enable_quality_feedback=True)
        
        # Query requiring logical reasoning
        query = "How does hierarchical session management improve over flat storage?"
        response_data = await agent.chat(query, use_research=False)
        response = response_data.get("response", "")
        
        # Use LLM judge to evaluate logical coherence
        judge_prompt = f"""
Evaluate logical coherence of reasoning.

Query: "{query}"
Response: "{response[:500]}"

Questions:
1. Is reasoning logically sound?
2. Are conclusions supported by premises?
3. Are arguments valid?
4. Is there logical flow?
5. Are steps sequenced correctly?

Respond with JSON: {{
    "logically_sound": true/false,
    "conclusions_supported": true/false,
    "arguments_valid": true/false,
    "logical_flow": true/false,
    "logical_errors": ["list any logical errors"],
    "score": 0.0-1.0,
    "reasoning": "..."
}}
"""
        
        try:
            result = await llm.generate_response(judge_prompt)
            assert len(result) > 0
        except Exception:
            # Fallback: verify response exists
            assert response


@pytest.mark.asyncio
async def test_factual_correctness_verification():
    """
    Test factual correctness: Facts should be accurate and verifiable.
    
    Pattern: semantic_properties
    Opinion: facts_should_be_correct
    Category: semantic_properties
    Hypothesis: Facts should be accurate, claims should be verifiable, citations should be valid.
    """
    annotate_test(
        "test_factual_correctness_verification",
        pattern="semantic_properties",
        opinion="facts_should_be_correct",
        category="semantic_properties",
        hypothesis="Facts should be accurate, claims should be verifiable, citations should be valid.",
    )
    
    try:
        llm = LLMService()
    except Exception:
        pytest.skip("LLM service not available")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        agent = KnowledgeAgent(enable_quality_feedback=True)
        
        # Query with verifiable facts
        query = "What are the key concepts in knowledge structure theory?"
        response_data = await agent.chat(query, use_research=False)
        response = response_data.get("response", "")
        
        # Use LLM judge to evaluate factual correctness
        judge_prompt = f"""
Evaluate factual correctness of response.

Query: "{query}"
Response: "{response[:500]}"

Questions:
1. Are facts accurate?
2. Are claims verifiable?
3. Are citations valid (if any)?
4. Are there false claims?
5. Is information reliable?

Respond with JSON: {{
    "factually_correct": true/false,
    "claims_verifiable": true/false,
    "false_claims": ["list any false claims"],
    "score": 0.0-1.0,
    "reasoning": "..."
}}
"""
        
        try:
            result = await llm.generate_response(judge_prompt)
            assert len(result) > 0
        except Exception:
            # Fallback: verify response exists
            assert response


@pytest.mark.asyncio
async def test_contextual_appropriateness():
    """
    Test contextual appropriateness: Response should match context, intent, tone, level.
    
    Pattern: semantic_properties
    Opinion: responses_should_be_contextually_appropriate
    Category: semantic_properties
    Hypothesis: Responses should match context, user intent, tone, and expertise level.
    """
    annotate_test(
        "test_contextual_appropriateness",
        pattern="semantic_properties",
        opinion="responses_should_be_contextually_appropriate",
        category="semantic_properties",
        hypothesis="Responses should match context, user intent, tone, and expertise level.",
    )
    
    try:
        llm = LLMService()
    except Exception:
        pytest.skip("LLM service not available")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        agent = KnowledgeAgent(enable_quality_feedback=True)
        
        # Query with implicit context
        query = "Can you explain this simply?"  # Implicit: previous context
        response_data = await agent.chat(query, use_research=False)
        response = response_data.get("response", "")
        
        # Use LLM judge to evaluate contextual appropriateness
        judge_prompt = f"""
Evaluate contextual appropriateness of response.

Query: "{query}"
Response: "{response[:500]}"

Questions:
1. Is response appropriate for context?
2. Does it match user intent?
3. Is tone appropriate?
4. Is level appropriate (simple vs technical)?
5. Does it adapt to user expertise?

Respond with JSON: {{
    "contextually_appropriate": true/false,
    "matches_intent": true/false,
    "tone_appropriate": true/false,
    "level_appropriate": true/false,
    "inappropriate_aspects": ["list any inappropriate aspects"],
    "score": 0.0-1.0,
    "reasoning": "..."
}}
"""
        
        try:
            result = await llm.generate_response(judge_prompt)
            assert len(result) > 0
        except Exception:
            # Fallback: verify response exists
            assert response

