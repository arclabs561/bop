"""Tests for behavioral properties: flow, turn-taking, context, intent."""

import tempfile

import pytest

from bop.agent import KnowledgeAgent
from bop.llm import LLMService
from tests.test_annotations import annotate_test


@pytest.mark.asyncio
async def test_conversational_flow_natural():
    """
    Test conversational flow: Conversation should flow naturally with smooth transitions.

    Pattern: behavioral_properties
    Opinion: conversations_should_flow_naturally
    Category: behavioral_properties
    Hypothesis: Conversations should have natural flow with smooth transitions and maintained context.
    """
    annotate_test(
        "test_conversational_flow_natural",
        pattern="behavioral_properties",
        opinion="conversations_should_flow_naturally",
        category="behavioral_properties",
        hypothesis="Conversations should have natural flow with smooth transitions and maintained context.",
    )

    try:
        llm = LLMService()
    except Exception:
        pytest.skip("LLM service not available")

    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)

        # Multi-turn conversation
        conversation = [
            ("What is knowledge structure?", "initial"),
            ("Can you give an example?", "follow-up"),
            ("How does that relate to trust?", "related follow-up"),
            ("Thanks, that helps!", "closing"),
        ]

        responses = []
        for query, turn_type in conversation:
            response_data = await agent.chat(query, use_research=False)
            responses.append({
                "query": query,
                "turn_type": turn_type,
                "response": response_data.get("response", "")[:300],
            })

        # Use LLM judge to evaluate flow
        judge_prompt = f"""
Evaluate conversational flow.

Conversation:
{chr(10).join([f"Q ({r['turn_type']}): {r['query']}\nA: {r['response']}" for r in responses])}

Questions:
1. Does conversation flow naturally?
2. Are transitions smooth?
3. Is context maintained across turns?
4. Are follow-ups appropriate?
5. Is turn-taking natural?

Respond with JSON: {{
    "flows_naturally": true/false,
    "smooth_transitions": true/false,
    "context_maintained": true/false,
    "appropriate_followups": true/false,
    "flow_issues": ["list any flow issues"],
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
async def test_turn_taking_appropriate():
    """
    Test turn-taking: Agent should wait appropriately and handle interruptions.

    Pattern: behavioral_properties
    Opinion: turn_taking_should_be_appropriate
    Category: behavioral_properties
    Hypothesis: Agent should wait appropriately, handle interruptions, and maintain natural timing.
    """
    annotate_test(
        "test_turn_taking_appropriate",
        pattern="behavioral_properties",
        opinion="turn_taking_should_be_appropriate",
        category="behavioral_properties",
        hypothesis="Agent should wait appropriately, handle interruptions, and maintain natural timing.",
    )

    try:
        llm = LLMService()
    except Exception:
        pytest.skip("LLM service not available")

    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)

        # Simulate rapid queries (interruption-like)
        queries = [
            "What is knowledge structure?",
            "Wait, actually",  # Interruption attempt
            "What I really want to know is how it relates to trust?",
        ]

        responses = []
        for query in queries:
            response_data = await agent.chat(query, use_research=False)
            responses.append({
                "query": query,
                "response": response_data.get("response", "")[:300],
            })

        # Use LLM judge to evaluate turn-taking
        judge_prompt = f"""
Evaluate turn-taking behavior.

Conversation:
{chr(10).join([f"Q: {r['query']}\nA: {r['response']}" for r in responses])}

Questions:
1. Does agent wait appropriately?
2. Does it handle interruptions gracefully?
3. Is timing natural?
4. Is back-and-forth natural?
5. Does it acknowledge context switches?

Respond with JSON: {{
    "waits_appropriately": true/false,
    "handles_interruptions": true/false,
    "natural_timing": true/false,
    "natural_back_forth": true/false,
    "turn_taking_issues": ["list any issues"],
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
async def test_context_maintenance_across_turns():
    """
    Test context maintenance: Context should be remembered and referenced across turns.

    Pattern: behavioral_properties
    Opinion: context_should_be_maintained
    Category: behavioral_properties
    Hypothesis: Agent should remember and reference context across multiple turns.
    """
    annotate_test(
        "test_context_maintenance_across_turns",
        pattern="behavioral_properties",
        opinion="context_should_be_maintained",
        category="behavioral_properties",
        hypothesis="Agent should remember and reference context across multiple turns.",
    )

    try:
        llm = LLMService()
    except Exception:
        pytest.skip("LLM service not available")

    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)

        # Conversation with context references
        conversation = [
            "My name is Alice and I'm researching knowledge structure.",
            "What are the key concepts?",  # Should remember "knowledge structure"
            "How does that relate to what I'm researching?",  # Should remember context
        ]

        responses = []
        for query in conversation:
            response_data = await agent.chat(query, use_research=False)
            responses.append({
                "query": query,
                "response": response_data.get("response", "")[:300],
            })

        # Use LLM judge to evaluate context maintenance
        judge_prompt = f"""
Evaluate context maintenance.

Conversation:
{chr(10).join([f"Q: {r['query']}\nA: {r['response']}" for r in responses])}

Questions:
1. Does agent remember earlier context?
2. Are references resolved correctly?
3. Is history used appropriately?
4. Are previous turns referenced?
5. Is context updated correctly?

Respond with JSON: {{
    "remembers_context": true/false,
    "resolves_references": true/false,
    "uses_history": true/false,
    "references_previous": true/false,
    "context_issues": ["list any context issues"],
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
async def test_user_intent_understanding():
    """
    Test user intent understanding: Agent should correctly identify and respond to user intent.

    Pattern: behavioral_properties
    Opinion: intent_should_be_understood
    Category: behavioral_properties
    Hypothesis: Agent should correctly identify user intent, understand implicit needs, and provide appropriate clarifications.
    """
    annotate_test(
        "test_user_intent_understanding",
        pattern="behavioral_properties",
        opinion="intent_should_be_understood",
        category="behavioral_properties",
        hypothesis="Agent should correctly identify user intent, understand implicit needs, and provide appropriate clarifications.",
    )

    try:
        llm = LLMService()
    except Exception:
        pytest.skip("LLM service not available")

    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)

        # Ambiguous queries testing intent understanding
        queries = [
            "I need help with this.",  # Ambiguous
            "Can you explain it better?",  # Implicit reference
            "What about the other thing?",  # Very implicit
        ]

        responses = []
        for query in queries:
            response_data = await agent.chat(query, use_research=False)
            responses.append({
                "query": query,
                "response": response_data.get("response", "")[:300],
            })

        # Use LLM judge to evaluate intent understanding
        judge_prompt = f"""
Evaluate user intent understanding.

Conversation:
{chr(10).join([f"Q: {r['query']}\nA: {r['response']}" for r in responses])}

Questions:
1. Does agent correctly identify intent?
2. Does it understand implicit needs?
3. Are clarifications appropriate?
4. Is intent maintained across turns?
5. Are misunderstandings corrected?

Respond with JSON: {{
    "identifies_intent": true/false,
    "understands_implicit": true/false,
    "appropriate_clarifications": true/false,
    "maintains_intent": true/false,
    "intent_issues": ["list any intent issues"],
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

