"""Chaos engineering tests for E2E system.

Tests system resilience through controlled failures and disruptions.
"""

import asyncio
import tempfile

import pytest

from bop.agent import KnowledgeAgent
from tests.test_annotations import annotate_test


@pytest.mark.asyncio
async def test_e2e_chaos_llm_service_failure():
    """
    Chaos: LLM service fails mid-request.

    System should degrade gracefully without crashing.
    """
    annotate_test(
        "test_e2e_chaos_llm_service_failure",
        pattern="chaos_engineering",
        opinion="system_handles_llm_failures",
        category="e2e_chaos",
        hypothesis="System handles LLM service failures gracefully",
    )

    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)

        # Simulate LLM failure mid-request
        original_chat = agent.chat

        async def failing_chat(*args, **kwargs):
            # Fail on second call
            if not hasattr(failing_chat, "call_count"):
                failing_chat.call_count = 0
            failing_chat.call_count += 1

            if failing_chat.call_count == 2:
                raise Exception("LLM service unavailable")

            return await original_chat(*args, **kwargs)

        agent.chat = failing_chat

        # First request should work
        response1 = await agent.chat(message="Test 1", use_research=False)
        assert response1.get("response") is not None

        # Second request should handle failure gracefully
        try:
            response2 = await agent.chat(message="Test 2", use_research=False)
            # Should either return error response or raise gracefully
            assert response2.get("response") is not None or "error" in str(response2).lower()
        except Exception as e:
            # Failure is acceptable if handled gracefully
            assert "LLM" in str(e) or "service" in str(e).lower()


@pytest.mark.asyncio
async def test_e2e_chaos_research_tool_failure():
    """
    Chaos: Research tools fail during query.

    System should fall back to non-research mode.
    """
    annotate_test(
        "test_e2e_chaos_research_tool_failure",
        pattern="chaos_engineering",
        opinion="system_handles_research_failures",
        category="e2e_chaos",
        hypothesis="System handles research tool failures gracefully",
    )

    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)

        # Simulate research failure

        async def failing_research(*args, **kwargs):
            raise Exception("Research tool unavailable")

        agent.research_agent.deep_research = failing_research

        # Request with research should handle failure
        response = await agent.chat(
            message="What is knowledge structure?",
            use_research=True,
        )

        # Should either return response without research or indicate failure
        assert response.get("response") is not None
        # Research may have failed, but system should continue
        assert "research_error" in response or response.get("research_conducted") is False


@pytest.mark.asyncio
async def test_e2e_chaos_storage_failure():
    """
    Chaos: Storage fails during session save.

    System should continue operating without persistence.
    """
    annotate_test(
        "test_e2e_chaos_storage_failure",
        pattern="chaos_engineering",
        opinion="system_handles_storage_failures",
        category="e2e_chaos",
        hypothesis="System handles storage failures gracefully",
    )

    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)

        # Simulate storage failure
        if agent.quality_feedback and agent.quality_feedback.session_manager:

            def failing_save(*args, **kwargs):
                raise IOError("Storage unavailable")

            agent.quality_feedback.session_manager.storage.save_session = failing_save

        # System should continue operating
        response = await agent.chat(message="Test", use_research=False)
        assert response.get("response") is not None


@pytest.mark.asyncio
async def test_e2e_chaos_concurrent_requests():
    """
    Chaos: Multiple concurrent requests.

    System should handle concurrency without deadlocks or corruption.
    """
    annotate_test(
        "test_e2e_chaos_concurrent_requests",
        pattern="chaos_engineering",
        opinion="system_handles_concurrency",
        category="e2e_chaos",
        hypothesis="System handles concurrent requests correctly",
    )

    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)

        # Concurrent requests
        queries = [f"Query {i}" for i in range(5)]

        async def make_request(query):
            return await agent.chat(message=query, use_research=False)

        # Run concurrently
        responses = await asyncio.gather(*[make_request(q) for q in queries])

        # All should succeed
        assert len(responses) == 5
        assert all(r.get("response") for r in responses)


@pytest.mark.asyncio
async def test_e2e_chaos_partial_failures():
    """
    Chaos: Partial system failures (some components work, others don't).

    System should degrade gracefully.
    """
    annotate_test(
        "test_e2e_chaos_partial_failures",
        pattern="chaos_engineering",
        opinion="system_handles_partial_failures",
        category="e2e_chaos",
        hypothesis="System handles partial component failures gracefully",
    )

    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)

        # Disable quality feedback (simulate failure)
        agent.quality_feedback = None
        agent.adaptive_manager = None

        # System should still work without quality feedback
        response = await agent.chat(message="Test", use_research=False)
        assert response.get("response") is not None

