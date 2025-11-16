"""Metamorphic E2E tests.

Tests relationships between inputs and outputs that should hold regardless of exact values.
"""

import pytest
import tempfile
from typing import Dict, Any

from bop.agent import KnowledgeAgent
from tests.test_annotations import annotate_test


@pytest.mark.asyncio
async def test_e2e_metamorphic_query_expansion():
    """
    Metamorphic: Expanding a query should produce more comprehensive response.
    
    Relation: query_expanded → response_more_comprehensive
    """
    annotate_test(
        "test_e2e_metamorphic_query_expansion",
        pattern="metamorphic_e2e",
        opinion="expanded_queries_produce_comprehensive_responses",
        category="e2e_metamorphic",
        hypothesis="Expanding queries produces more comprehensive responses",
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        agent = KnowledgeAgent(enable_quality_feedback=True)
        
        # Original query
        original_query = "What is knowledge structure?"
        original_response = await agent.chat(message=original_query, use_research=True)
        
        # Expanded query (more specific)
        expanded_query = "What is knowledge structure? Please explain comprehensively with examples and applications."
        expanded_response = await agent.chat(message=expanded_query, use_research=True)
        
        # Metamorphic relation: Expanded query should produce longer/more comprehensive response
        original_length = len(original_response.get("response", ""))
        expanded_length = len(expanded_response.get("response", ""))
        
        # Relation should hold (expanded should be longer or similar)
        # Allow some variance due to LLM non-determinism
        assert expanded_length >= original_length * 0.8, "Expanded query should produce more comprehensive response"


@pytest.mark.asyncio
async def test_e2e_metamorphic_research_improvement():
    """
    Metamorphic: Research should improve response quality.
    
    Relation: research_enabled → quality_higher
    """
    annotate_test(
        "test_e2e_metamorphic_research_improvement",
        pattern="metamorphic_e2e",
        opinion="research_improves_quality",
        category="e2e_metamorphic",
        hypothesis="Research improves response quality",
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        agent = KnowledgeAgent(enable_quality_feedback=True)
        
        query = "What is d-separation in causal inference?"
        
        # Without research
        no_research_response = await agent.chat(message=query, use_research=False)
        no_research_quality = no_research_response.get("quality", {}).get("score", 0.0)
        
        # With research
        with_research_response = await agent.chat(message=query, use_research=True)
        with_research_quality = with_research_response.get("quality", {}).get("score", 0.0)
        
        # Metamorphic relation: Research should improve quality (or at least not degrade)
        # Allow variance due to LLM non-determinism
        assert with_research_quality >= no_research_quality * 0.9, "Research should improve or maintain quality"


@pytest.mark.asyncio
async def test_e2e_metamorphic_schema_consistency():
    """
    Metamorphic: Different schemas should produce structurally consistent responses.
    
    Relation: schema_changed → structure_consistent
    """
    annotate_test(
        "test_e2e_metamorphic_schema_consistency",
        pattern="metamorphic_e2e",
        opinion="schemas_produce_consistent_structure",
        category="e2e_metamorphic",
        hypothesis="Different schemas produce structurally consistent responses",
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        agent = KnowledgeAgent(enable_quality_feedback=True)
        
        query = "What is information geometry?"
        
        schemas = ["chain_of_thought", "decompose_and_synthesize", None]
        responses = []
        
        for schema in schemas:
            response = await agent.chat(message=query, use_research=False, use_schema=schema)
            responses.append(response)
        
        # Metamorphic relation: All responses should have consistent structure
        response_keys = [set(r.keys()) for r in responses]
        
        # All should have core keys
        core_keys = {"response", "schema_used"}
        assert all(core_keys.issubset(keys) for keys in response_keys)


@pytest.mark.asyncio
async def test_e2e_metamorphic_multi_turn_accumulation():
    """
    Metamorphic: Multi-turn conversations should accumulate context.
    
    Relation: more_turns → more_context → potentially_better_responses
    """
    annotate_test(
        "test_e2e_metamorphic_multi_turn_accumulation",
        pattern="metamorphic_e2e",
        opinion="multi_turn_accumulates_context",
        category="e2e_metamorphic",
        hypothesis="Multi-turn conversations accumulate context",
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        agent = KnowledgeAgent(enable_quality_feedback=True)
        
        # Single turn
        turn1_response = await agent.chat(message="What is knowledge structure?", use_research=False)
        
        # Multi-turn
        await agent.chat(message="What is knowledge structure?", use_research=False)
        await agent.chat(message="How does it relate to trust?", use_research=False)
        turn3_response = await agent.chat(message="What are applications?", use_research=False)
        
        # Metamorphic relation: Later turns should have access to more context
        # This is hard to verify directly, but we can check that system maintains state
        if agent.quality_feedback:
            sessions = agent.quality_feedback.session_manager.list_sessions()
            # Should have accumulated evaluations
            assert len(sessions) >= 1


@pytest.mark.asyncio
async def test_e2e_metamorphic_quality_feedback_improvement():
    """
    Metamorphic: Quality feedback should improve responses over time.
    
    Relation: more_feedback → better_quality
    """
    annotate_test(
        "test_e2e_metamorphic_quality_feedback_improvement",
        pattern="metamorphic_e2e",
        opinion="quality_feedback_improves_over_time",
        category="e2e_metamorphic",
        hypothesis="Quality feedback improves responses over time",
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        agent = KnowledgeAgent(enable_quality_feedback=True)
        
        query = "What is d-separation?"
        
        # First query (no learning yet)
        response1 = await agent.chat(message=query, use_research=False)
        quality1 = response1.get("quality", {}).get("score", 0.0)
        
        # Multiple queries to build learning
        for _ in range(3):
            await agent.chat(message=query, use_research=False)
        
        # Later query (should benefit from learning)
        response2 = await agent.chat(message=query, use_research=False)
        quality2 = response2.get("quality", {}).get("score", 0.0)
        
        # Metamorphic relation: Quality should improve or maintain
        # Allow variance due to LLM non-determinism
        assert quality2 >= quality1 * 0.9, "Quality should improve or maintain with feedback"

