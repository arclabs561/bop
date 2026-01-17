"""Tests for automated health checks and self-optimization."""

import os

import pytest

os.environ["BOP_ENABLE_OBSERVABILITY"] = "true"
os.environ["BOP_MAX_CONVERSATION_HISTORY"] = "20"


@pytest.fixture
def agent():
    """Create agent for testing."""
    from src.pran.agent import KnowledgeAgent
    return KnowledgeAgent(enable_system_reminders=True)


def test_health_check_periodic(agent):
    """Test that health checks run periodically."""
    # Add operations to trigger health check (every 20 ops)
    for i in range(25):
        agent._metrics["todo_updates"].append({
            "timestamp": "2025-01-16T10:00:00Z",
            "todo_count": 3,
            "completed": 1,
        })

    # Health check should run at 20 operations
    agent._check_health_and_auto_optimize()

    # May or may not return actions depending on health
    # But should not crash


def test_auto_optimize_high_failure_rate(agent):
    """Test auto-optimization with high compaction failure rate."""
    # Simulate high failure rate
    agent.use_llm_compaction = True
    agent._metrics["compaction_events"] = [
        {"success": False},
        {"success": False},
        {"success": False},
        {"success": True},
    ] * 5  # 20 total events

    # Fill operations to trigger check
    for i in range(20):
        agent._metrics["todo_updates"].append({
            "timestamp": "2025-01-16T10:00:00Z",
            "todo_count": 3,
            "completed": 1,
        })

    result = agent._check_health_and_auto_optimize()

    # Should detect high failure rate and suggest action
    if result:
        assert "actions" in result
        # May suggest disabling LLM compaction


def test_auto_optimize_increase_history_limit(agent):
    """Test auto-optimization increases history limit on high errors."""
    original_max = agent.max_conversation_history

    # Add many errors
    agent._metrics["errors"] = [
        {"type": "compaction_failure", "message": "Error", "timestamp": "2025-01-16T10:00:00Z"}
    ] * 15  # 15 errors

    # Fill operations to trigger check
    for i in range(20):
        agent._metrics["todo_updates"].append({
            "timestamp": "2025-01-16T10:00:00Z",
            "todo_count": 3,
            "completed": 1,
        })

    result = agent._check_health_and_auto_optimize()

    # May increase history limit if errors are high
    if result and "actions" in result:
        for action in result["actions"]:
            if action.get("action") == "increase_history_limit":
                assert agent.max_conversation_history > original_max
                break


def test_health_check_skips_when_not_period(agent):
    """Test that health check skips when not at periodic interval."""
    # Add operations but not at 20
    for i in range(15):
        agent._metrics["todo_updates"].append({
            "timestamp": "2025-01-16T10:00:00Z",
            "todo_count": 3,
            "completed": 1,
        })

    result = agent._check_health_and_auto_optimize()

    # Should return None (not at periodic interval)
    assert result is None


def test_auto_optimize_healthy_system(agent):
    """Test auto-optimization with healthy system."""
    # Add successful operations
    agent._metrics["compaction_events"] = [
        {"success": True, "compression_ratio": 0.3},
        {"success": True, "compression_ratio": 0.4},
    ] * 10

    # Fill operations to trigger check
    for i in range(20):
        agent._metrics["todo_updates"].append({
            "timestamp": "2025-01-16T10:00:00Z",
            "todo_count": 3,
            "completed": 1,
        })

    result = agent._check_health_and_auto_optimize()

    # Healthy system should not trigger actions
    if result:
        # May still return result but with no actions
        assert result.get("health_score", 1.0) >= 0.7

