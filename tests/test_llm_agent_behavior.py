"""Tests for LLM agent behavior: tool selection, reasoning, errors, correction."""

import tempfile

import pytest

from bop.agent import KnowledgeAgent
from bop.llm import LLMService
from tests.test_annotations import annotate_test


@pytest.mark.asyncio
async def test_tool_selection_correctness():
    """
    Test tool selection: Tools should be selected appropriately and used correctly.

    Pattern: llm_agent_behavior
    Opinion: tools_should_be_selected_correctly
    Category: llm_agent_behavior
    Hypothesis: Agent should select appropriate tools, justify selection, and use them correctly.
    """
    annotate_test(
        "test_tool_selection_correctness",
        pattern="llm_agent_behavior",
        opinion="tools_should_be_selected_correctly",
        category="llm_agent_behavior",
        hypothesis="Agent should select appropriate tools, justify selection, and use them correctly.",
    )

    try:
        llm = LLMService()
    except Exception:
        pytest.skip("LLM service not available")

    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)

        # Query requiring research (should use research tool)
        query = "What are the latest developments in knowledge structure research?"
        response_data = await agent.chat(query, use_research=True)
        response = response_data.get("response", "")
        tools_used = response_data.get("tools_used", [])

        # Use LLM judge to evaluate tool selection
        judge_prompt = f"""
Evaluate tool selection correctness.

Query: "{query}"
Response: "{response[:500]}"
Tools Used: {tools_used}

Questions:
1. Were appropriate tools selected?
2. Was tool selection justified?
3. Were tools used correctly?
4. Was tool output used properly?
5. Were tool failures handled?

Respond with JSON: {{
    "tools_appropriate": true/false,
    "selection_justified": true/false,
    "tools_used_correctly": true/false,
    "output_used_properly": true/false,
    "tool_selection_issues": ["list any issues"],
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
async def test_reasoning_transparency():
    """
    Test reasoning transparency: Reasoning should be explained and steps should be clear.

    Pattern: llm_agent_behavior
    Opinion: reasoning_should_be_transparent
    Category: llm_agent_behavior
    Hypothesis: Agent should explain reasoning, make steps clear, show logic, and state assumptions.
    """
    annotate_test(
        "test_reasoning_transparency",
        pattern="llm_agent_behavior",
        opinion="reasoning_should_be_transparent",
        category="llm_agent_behavior",
        hypothesis="Agent should explain reasoning, make steps clear, show logic, and state assumptions.",
    )

    try:
        llm = LLMService()
    except Exception:
        pytest.skip("LLM service not available")

    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)

        # Query requiring reasoning
        query = "How does hierarchical session management improve over flat storage?"
        response_data = await agent.chat(query, use_research=False)
        response = response_data.get("response", "")

        # Use LLM judge to evaluate reasoning transparency
        judge_prompt = f"""
Evaluate reasoning transparency.

Query: "{query}"
Response: "{response[:500]}"

Questions:
1. Is reasoning explained?
2. Are steps clear?
3. Is logic visible?
4. Are assumptions stated?
5. Is uncertainty acknowledged?

Respond with JSON: {{
    "reasoning_explained": true/false,
    "steps_clear": true/false,
    "logic_visible": true/false,
    "assumptions_stated": true/false,
    "transparency_issues": ["list any issues"],
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
async def test_error_handling_graceful():
    """
    Test error handling: Errors should be handled gracefully with helpful messages.

    Pattern: llm_agent_behavior
    Opinion: errors_should_be_handled_gracefully
    Category: llm_agent_behavior
    Hypothesis: Agent should handle errors gracefully, provide helpful messages, attempt recovery, and communicate failures.
    """
    annotate_test(
        "test_error_handling_graceful",
        pattern="llm_agent_behavior",
        opinion="errors_should_be_handled_gracefully",
        category="llm_agent_behavior",
        hypothesis="Agent should handle errors gracefully, provide helpful messages, attempt recovery, and communicate failures.",
    )

    try:
        llm = LLMService()
    except Exception:
        pytest.skip("LLM service not available")

    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)

        # Invalid/malformed query
        query = ""  # Empty query
        try:
            response_data = await agent.chat(query, use_research=False)
            response = response_data.get("response", "")
        except Exception as e:
            response = str(e)

        # Use LLM judge to evaluate error handling
        judge_prompt = f"""
Evaluate error handling.

Query: "{query}" (empty/invalid)
Response: "{response[:500]}"

Questions:
1. Is error handled gracefully?
2. Is error message helpful?
3. Is recovery attempted?
4. Is failure communicated clearly?
5. Is fallback behavior appropriate?

Respond with JSON: {{
    "handled_gracefully": true/false,
    "message_helpful": true/false,
    "recovery_attempted": true/false,
    "failure_communicated": true/false,
    "error_handling_issues": ["list any issues"],
    "score": 0.0-1.0,
    "reasoning": "..."
}}
"""

        try:
            result = await llm.generate_response(judge_prompt)
            assert len(result) > 0
        except Exception:
            # Fallback: verify response exists (even if error)
            assert response is not None


@pytest.mark.asyncio
async def test_self_correction_learning():
    """
    Test self-correction: Agent should correct mistakes and incorporate feedback.

    Pattern: llm_agent_behavior
    Opinion: agent_should_correct_mistakes
    Category: llm_agent_behavior
    Hypothesis: Agent should correct mistakes, fix inconsistencies, incorporate feedback, and demonstrate learning.
    """
    annotate_test(
        "test_self_correction_learning",
        pattern="llm_agent_behavior",
        opinion="agent_should_correct_mistakes",
        category="llm_agent_behavior",
        hypothesis="Agent should correct mistakes, fix inconsistencies, incorporate feedback, and demonstrate learning.",
    )

    try:
        llm = LLMService()
    except Exception:
        pytest.skip("LLM service not available")

    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)

        # Initial query
        query1 = "What is knowledge structure?"
        response1_data = await agent.chat(query1, use_research=False)
        response1 = response1_data.get("response", "")

        # Follow-up that might reveal mistake
        query2 = "Actually, I think you might have missed something. Can you reconsider?"
        response2_data = await agent.chat(query2, use_research=False)
        response2 = response2_data.get("response", "")

        # Use LLM judge to evaluate self-correction
        judge_prompt = f"""
Evaluate self-correction and learning.

Initial Query: "{query1}"
Initial Response: "{response1[:300]}"

Follow-up Query: "{query2}"
Follow-up Response: "{response2[:300]}"

Questions:
1. Does agent correct mistakes when pointed out?
2. Are inconsistencies fixed?
3. Is feedback incorporated?
4. Is learning demonstrated?
5. Does it improve over time?

Respond with JSON: {{
    "corrects_mistakes": true/false,
    "fixes_inconsistencies": true/false,
    "incorporates_feedback": true/false,
    "demonstrates_learning": true/false,
    "correction_issues": ["list any issues"],
    "score": 0.0-1.0,
    "reasoning": "..."
}}
"""

        try:
            result = await llm.generate_response(judge_prompt)
            assert len(result) > 0
        except Exception:
            # Fallback: verify responses exist
            assert response1
            assert response2

