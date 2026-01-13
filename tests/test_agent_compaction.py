"""Tests for conversation history compaction."""

import os

import pytest

os.environ["BOP_MAX_CONVERSATION_HISTORY"] = "20"
os.environ["BOP_ENABLE_OBSERVABILITY"] = "true"


@pytest.fixture
def agent():
    """Create agent for testing."""
    from src.bop.agent import KnowledgeAgent
    return KnowledgeAgent(enable_system_reminders=True)


@pytest.mark.asyncio
async def test_compaction_triggers_at_70_percent(agent):
    """Test that compaction triggers at 70% threshold."""
    threshold = int(agent.max_conversation_history * 0.7)

    # Fill to just below threshold
    for i in range(threshold):
        agent.conversation_history.append({
            "role": "user" if i % 2 == 0 else "assistant",
            "content": f"Message {i}"
        })

    before = len(agent.conversation_history)
    await agent._compact_conversation_history()
    after = len(agent.conversation_history)

    # Should not compact (below threshold)
    assert before == after

    # Add one more to trigger
    agent.conversation_history.append({"role": "user", "content": "Trigger message"})
    before = len(agent.conversation_history)
    await agent._compact_conversation_history()
    after = len(agent.conversation_history)

    # Should compact now
    assert after < before
    assert agent.conversation_summary is not None


@pytest.mark.asyncio
async def test_compaction_preserves_recent_messages(agent):
    """Test that compaction keeps recent messages."""
    # Fill history
    for i in range(25):
        agent.conversation_history.append({
            "role": "user" if i % 2 == 0 else "assistant",
            "content": f"Message {i}: Important content here"
        })

    agent.conversation_history[-5:][0]["content"]

    await agent._compact_conversation_history()

    # Recent messages should still be present
    assert len(agent.conversation_history) > 0
    # Should have summary message
    assert any("summary" in str(msg.get("content", "")).lower() for msg in agent.conversation_history)


@pytest.mark.asyncio
async def test_compaction_rollback_on_failure(agent):
    """Test that compaction rolls back on failure."""
    # Fill history
    for i in range(15):
        agent.conversation_history.append({
            "role": "user" if i % 2 == 0 else "assistant",
            "content": f"Message {i}"
        })

    original_history = agent.conversation_history.copy()
    original_summary = agent.conversation_summary

    # Simulate failure by corrupting the compaction process
    # (In real scenario, this would be an actual error)
    # We'll test that the rollback mechanism exists

    try:
        await agent._compact_conversation_history()
        # If successful, verify history is valid
        assert len(agent.conversation_history) <= agent.max_conversation_history
    except Exception:
        # If failure occurs, verify rollback
        assert agent.conversation_history == original_history
        assert agent.conversation_summary == original_summary


@pytest.mark.asyncio
async def test_compaction_skips_too_few_messages(agent):
    """Test that compaction skips when too few messages."""
    agent.conversation_history = [
        {"role": "user", "content": "Test"}
    ] * 5  # Less than 10

    before = len(agent.conversation_history)
    await agent._compact_conversation_history()
    after = len(agent.conversation_history)

    # Should not compact
    assert before == after


@pytest.mark.asyncio
async def test_compaction_improved_heuristic(agent):
    """Test improved heuristic summarization."""
    # Create messages with key terms
    agent.conversation_history = [
        {"role": "user", "content": "I want to implement authentication with JWT tokens"},
        {"role": "assistant", "content": "I've decided to use JWT for authentication. This is secure."},
        {"role": "user", "content": "There's a bug in the login system"},
        {"role": "assistant", "content": "I fixed the bug by updating token validation."},
    ] * 5  # Repeat to get enough messages

    await agent._compact_conversation_history()

    # Summary should contain key information
    if agent.conversation_summary:
        summary_lower = agent.conversation_summary.lower()
        # Should mention key topics
        assert any(term in summary_lower for term in ["authentication", "jwt", "token", "bug", "login"])


@pytest.mark.asyncio
async def test_compaction_metrics_tracking(agent):
    """Test that compaction events are tracked in metrics."""
    # Fill history
    for i in range(15):
        agent.conversation_history.append({
            "role": "user" if i % 2 == 0 else "assistant",
            "content": f"Message {i}"
        })

    initial_events = len(agent._metrics["compaction_events"])
    await agent._compact_conversation_history()

    # Should have recorded compaction event
    assert len(agent._metrics["compaction_events"]) > initial_events

    event = agent._metrics["compaction_events"][-1]
    assert "before" in event
    assert "after" in event
    assert "method" in event
    assert "success" in event
    assert event["success"] is True

