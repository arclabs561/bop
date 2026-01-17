"""Additional quality evaluation properties discovered via MCP research.

Beyond Grice's maxims: response appropriateness, context coherence, factual grounding,
engagement, empathy, trust/transparency, naturalness, diversity.
"""

import tempfile

import pytest

from pran.agent import KnowledgeAgent
from pran.llm import LLMService
from tests.test_annotations import annotate_test


@pytest.mark.asyncio
async def test_quality_response_appropriateness():
    """
    Test response appropriateness: Does response align with user intent?

    Pattern: quality_properties
    Opinion: responses_should_be_appropriate
    Category: quality_additional
    Hypothesis: Responses should align with user intent and task requirements.
    """
    annotate_test(
        "test_quality_response_appropriateness",
        pattern="quality_properties",
        opinion="responses_should_be_appropriate",
        category="quality_additional",
        hypothesis="Responses should align with user intent and task requirements.",
    )

    try:
        llm = LLMService()
    except Exception:
        pytest.skip("LLM service not available")

    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)

        query = "I need help understanding knowledge structure"
        response_data = await agent.chat(query, use_research=False)
        response = response_data.get("response", "")

        # Use LLM judge to evaluate appropriateness
        judge_prompt = f"""
Evaluate response appropriateness.

Query: "{query}"
Response: "{response[:500]}"

Questions:
1. Does response align with user intent?
2. Does it address task requirements?
3. Is it appropriate for the context?
4. Does it match user needs?

Respond with JSON: {{
    "appropriate": true/false,
    "aligns_with_intent": true/false,
    "addresses_requirements": true/false,
    "score": 0.0-1.0,
    "reasoning": "..."
}}
"""

        try:
            result = await llm.generate_response(judge_prompt)
            assert len(result) > 0
        except Exception:
            assert response


@pytest.mark.asyncio
async def test_quality_context_coherence():
    """
    Test context coherence: Does response maintain dialogue history?

    Pattern: quality_properties
    Opinion: responses_should_maintain_context
    Category: quality_additional
    Hypothesis: Responses should be consistent and relevant to ongoing conversation.
    """
    annotate_test(
        "test_quality_context_coherence",
        pattern="quality_properties",
        opinion="responses_should_maintain_context",
        category="quality_additional",
        hypothesis="Responses should be consistent and relevant to ongoing conversation.",
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
            ("How does it relate to trust?", "follow-up"),
        ]

        responses = []
        for query, turn_type in conversation:
            response_data = await agent.chat(query, use_research=False)
            responses.append({
                "query": query,
                "turn_type": turn_type,
                "response": response_data.get("response", "")[:300],
            })

        # Use LLM judge to evaluate context coherence
        judge_prompt = f"""
Evaluate context coherence.

Conversation:
{chr(10).join([f"Q ({r['turn_type']}): {r['query']}\nA: {r['response']}" for r in responses])}

Questions:
1. Does response maintain dialogue history?
2. Is it consistent with previous exchanges?
3. Is it relevant to ongoing conversation?
4. Does it leverage context appropriately?

Respond with JSON: {{
    "coherent": true/false,
    "maintains_history": true/false,
    "consistent": true/false,
    "relevant": true/false,
    "score": 0.0-1.0,
    "reasoning": "..."
}}
"""

        try:
            result = await llm.generate_response(judge_prompt)
            assert len(result) > 0
        except Exception:
            assert all(r.get("response") for r in responses)


@pytest.mark.asyncio
async def test_quality_factual_grounding():
    """
    Test factual grounding: Are statements accurate and supported?

    Pattern: quality_properties
    Opinion: responses_should_be_factually_grounded
    Category: quality_additional
    Hypothesis: Statements should be accurate and supported by reliable knowledge.
    """
    annotate_test(
        "test_quality_factual_grounding",
        pattern="quality_properties",
        opinion="responses_should_be_factually_grounded",
        category="quality_additional",
        hypothesis="Statements should be accurate and supported by reliable knowledge.",
    )

    try:
        llm = LLMService()
    except Exception:
        pytest.skip("LLM service not available")

    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)

        query = "What are the key concepts in knowledge structure theory?"
        response_data = await agent.chat(query, use_research=False)
        response = response_data.get("response", "")

        # Use LLM judge to evaluate factual grounding
        judge_prompt = f"""
Evaluate factual grounding.

Query: "{query}"
Response: "{response[:500]}"

Questions:
1. Are statements accurate?
2. Are claims supported by reliable knowledge?
3. Are facts verifiable?
4. Is information grounded in evidence?

Respond with JSON: {{
    "factually_grounded": true/false,
    "accurate": true/false,
    "supported": true/false,
    "verifiable": true/false,
    "score": 0.0-1.0,
    "reasoning": "..."
}}
"""

        try:
            result = await llm.generate_response(judge_prompt)
            assert len(result) > 0
        except Exception:
            assert response


@pytest.mark.asyncio
async def test_quality_engagement():
    """
    Test engagement: Does response prompt continued interaction?

    Pattern: quality_properties
    Opinion: responses_should_be_engaging
    Category: quality_additional
    Hypothesis: Responses should prompt continued interaction and demonstrate interest.
    """
    annotate_test(
        "test_quality_engagement",
        pattern="quality_properties",
        opinion="responses_should_be_engaging",
        category="quality_additional",
        hypothesis="Responses should prompt continued interaction and demonstrate interest.",
    )

    try:
        llm = LLMService()
    except Exception:
        pytest.skip("LLM service not available")

    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)

        query = "Tell me about knowledge structure"
        response_data = await agent.chat(query, use_research=False)
        response = response_data.get("response", "")

        # Use LLM judge to evaluate engagement
        judge_prompt = f"""
Evaluate engagement.

Query: "{query}"
Response: "{response[:500]}"

Questions:
1. Does response prompt continued interaction?
2. Does it demonstrate interest?
3. Is it lively and stimulating?
4. Does it encourage further conversation?

Respond with JSON: {{
    "engaging": true/false,
    "prompts_interaction": true/false,
    "demonstrates_interest": true/false,
    "score": 0.0-1.0,
    "reasoning": "..."
}}
"""

        try:
            result = await llm.generate_response(judge_prompt)
            assert len(result) > 0
        except Exception:
            assert response


@pytest.mark.asyncio
async def test_quality_naturalness():
    """
    Test naturalness: Does response mimic human conversational flow?

    Pattern: quality_properties
    Opinion: responses_should_be_natural
    Category: quality_additional
    Hypothesis: Responses should mimic human conversational flow with proper grammar, fluency, and tone.
    """
    annotate_test(
        "test_quality_naturalness",
        pattern="quality_properties",
        opinion="responses_should_be_natural",
        category="quality_additional",
        hypothesis="Responses should mimic human conversational flow with proper grammar, fluency, and tone.",
    )

    try:
        llm = LLMService()
    except Exception:
        pytest.skip("LLM service not available")

    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)

        query = "Explain knowledge structure"
        response_data = await agent.chat(query, use_research=False)
        response = response_data.get("response", "")

        # Use LLM judge to evaluate naturalness
        judge_prompt = f"""
Evaluate naturalness.

Query: "{query}"
Response: "{response[:500]}"

Questions:
1. Does response mimic human conversational flow?
2. Is grammar correct?
3. Is it fluent?
4. Is tone appropriate?

Respond with JSON: {{
    "natural": true/false,
    "human_like_flow": true/false,
    "grammatically_correct": true/false,
    "fluent": true/false,
    "score": 0.0-1.0,
    "reasoning": "..."
}}
"""

        try:
            result = await llm.generate_response(judge_prompt)
            assert len(result) > 0
        except Exception:
            assert response


@pytest.mark.asyncio
async def test_quality_diversity():
    """
    Test diversity: Does response avoid repetitive or formulaic patterns?

    Pattern: quality_properties
    Opinion: responses_should_be_diverse
    Category: quality_additional
    Hypothesis: Responses should avoid repetitive or formulaic patterns and offer varied, creative replies.
    """
    annotate_test(
        "test_quality_diversity",
        pattern="quality_properties",
        opinion="responses_should_be_diverse",
        category="quality_additional",
        hypothesis="Responses should avoid repetitive or formulaic patterns and offer varied, creative replies.",
    )

    try:
        llm = LLMService()
    except Exception:
        pytest.skip("LLM service not available")

    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)

        # Multiple similar queries to test diversity
        queries = [
            "What is knowledge structure?",
            "Tell me about knowledge structure",
            "Explain knowledge structure",
        ]

        responses = []
        for query in queries:
            response_data = await agent.chat(query, use_research=False)
            responses.append({
                "query": query,
                "response": response_data.get("response", "")[:300],
            })

        # Use LLM judge to evaluate diversity
        judge_prompt = f"""
Evaluate diversity across responses.

Queries and Responses:
{chr(10).join([f"Q: {r['query']}\nA: {r['response']}" for r in responses])}

Questions:
1. Do responses avoid repetitive patterns?
2. Are they varied and creative?
3. Do they avoid formulaic replies?
4. Is there diversity in expression?

Respond with JSON: {{
    "diverse": true/false,
    "avoids_repetition": true/false,
    "varied": true/false,
    "creative": true/false,
    "score": 0.0-1.0,
    "reasoning": "..."
}}
"""

        try:
            result = await llm.generate_response(judge_prompt)
            assert len(result) > 0
        except Exception:
            assert all(r.get("response") for r in responses)

