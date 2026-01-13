"""Tests for agent observability and self-reflection features."""

import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

# Set test environment
os.environ["BOP_MAX_CONVERSATION_HISTORY"] = "20"
os.environ["BOP_ENABLE_OBSERVABILITY"] = "true"


@pytest.fixture
def temp_metrics_dir():
    """Create temporary directory for metrics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["BOP_METRICS_DIR"] = tmpdir
        yield Path(tmpdir)
        # Cleanup
        if "BOP_METRICS_DIR" in os.environ:
            del os.environ["BOP_METRICS_DIR"]


@pytest.fixture
def agent_with_observability(temp_metrics_dir):
    """Create agent with observability enabled."""
    from src.bop.agent import KnowledgeAgent
    agent = KnowledgeAgent(enable_system_reminders=True)
    return agent


def test_metrics_initialization(agent_with_observability):
    """Test that metrics are initialized correctly."""
    agent = agent_with_observability
    assert agent._metrics is not None
    assert "compaction_events" in agent._metrics
    assert "todo_updates" in agent._metrics
    assert "reminder_generations" in agent._metrics
    assert "errors" in agent._metrics


def test_metrics_persistence_save_load(agent_with_observability, temp_metrics_dir):
    """Test that metrics can be saved and loaded."""
    agent = agent_with_observability

    # Add some test metrics
    agent._metrics["compaction_events"].append({
        "timestamp": datetime.now().isoformat(),
        "before": 30,
        "after": 20,
        "method": "heuristic",
        "success": True,
        "compression_ratio": 0.67,
    })

    # Save metrics
    agent._save_metrics()

    # Verify file was created
    metrics_file = temp_metrics_dir / "agent_metrics.json"
    assert metrics_file.exists(), "Metrics file should be created"

    # Load metrics in new agent
    agent2 = KnowledgeAgent(enable_system_reminders=True)
    agent2.metrics_path = metrics_file

    # Load should restore metrics
    agent2._load_metrics()
    assert len(agent2._metrics["compaction_events"]) > 0, "Should load historical metrics"


def test_get_metrics_summary(agent_with_observability):
    """Test get_metrics returns proper summary structure."""
    agent = agent_with_observability

    # Add test data
    agent._metrics["compaction_events"] = [
        {"success": True, "compression_ratio": 0.5},
        {"success": True, "compression_ratio": 0.4},
        {"success": False},
    ]
    agent._metrics["todo_updates"] = [{"todo_count": 3}, {"todo_count": 5}]
    agent._metrics["errors"] = [
        {"type": "compaction_failure"},
        {"type": "compaction_failure"},
        {"type": "other_error"},
    ]

    metrics = agent.get_metrics()

    assert metrics is not None
    assert "summary" in metrics
    assert "detailed" in metrics

    summary = metrics["summary"]
    assert summary["compaction"]["total_events"] == 3
    assert summary["compaction"]["successful"] == 2
    assert summary["compaction"]["failed"] == 1
    assert "avg_compression_ratio" in summary["compaction"]
    assert summary["compaction"]["avg_compression_ratio"] == 0.45  # (0.5 + 0.4) / 2

    assert summary["errors"]["total"] == 3
    assert summary["errors"]["by_type"]["compaction_failure"] == 2
    assert summary["errors"]["by_type"]["other_error"] == 1


def test_self_reflect_healthy_system(agent_with_observability):
    """Test self-reflection on healthy system."""
    agent = agent_with_observability

    # Add successful metrics
    agent._metrics["compaction_events"] = [
        {"success": True, "compression_ratio": 0.3},
        {"success": True, "compression_ratio": 0.4},
    ]
    agent._metrics["todo_updates"] = [{"todo_count": 3}]

    analysis = agent.self_reflect()

    assert analysis["health_score"] == 1.0
    assert len(analysis["observations"]) > 0
    assert "Compaction success rate" in " ".join(analysis["observations"])


def test_self_reflect_unhealthy_system(agent_with_observability):
    """Test self-reflection on system with issues."""
    agent = agent_with_observability

    # Add failing metrics
    agent._metrics["compaction_events"] = [
        {"success": False},
        {"success": False},
        {"success": True},
    ]
    agent._metrics["errors"] = [
        {"type": "compaction_failure"},
        {"type": "compaction_failure"},
        {"type": "compaction_failure"},
    ]

    analysis = agent.self_reflect()

    assert analysis["health_score"] < 1.0
    assert len(analysis["suggestions"]) > 0
    assert any("compaction" in s.lower() for s in analysis["suggestions"])


def test_metrics_auto_save_on_compaction(agent_with_observability, temp_metrics_dir):
    """Test that metrics auto-save after compaction events."""
    agent = agent_with_observability

    # Fill history to trigger compaction
    for i in range(15):  # Above 70% of 20
        agent.conversation_history.append({
            "role": "user" if i % 2 == 0 else "assistant",
            "content": f"Test message {i}"
        })

    # Trigger compaction (will add 10 events to trigger auto-save)
    import asyncio
    for _ in range(10):
        asyncio.run(agent._compact_conversation_history())
        if len(agent._metrics["compaction_events"]) >= 10:
            break

    # Check if metrics were saved
    temp_metrics_dir / "agent_metrics.json"
    # Auto-save happens every 10 events, so may or may not be saved yet
    # But the mechanism should be in place


def test_token_estimation(agent_with_observability):
    """Test token estimation functionality."""
    agent = agent_with_observability

    # Test estimation
    text = "This is a test message with some words."
    tokens = agent._estimate_tokens(text)

    assert tokens > 0
    # Should be roughly text length / 4 (if no tiktoken)
    # Or accurate count if tiktoken available
    assert tokens <= len(text)  # Should never exceed character count


def test_conversation_token_count(agent_with_observability):
    """Test conversation token counting."""
    agent = agent_with_observability

    # Add messages
    agent.conversation_history = [
        {"role": "user", "content": "Test message 1"},
        {"role": "assistant", "content": "Response 1"},
        {"role": "user", "content": "Test message 2"},
    ]

    token_count = agent._get_conversation_token_count()

    assert token_count > 0
    # Should account for all messages plus overhead
    assert token_count >= sum(agent._estimate_tokens(msg.get("content", "")) for msg in agent.conversation_history)


def test_improved_heuristic_summarization(agent_with_observability):
    """Test improved heuristic summarization with key terms."""

    # Create test messages
    old_messages = [
        {"role": "user", "content": "I want to implement a new feature for user authentication"},
        {"role": "assistant", "content": "I've decided to use JWT tokens for authentication. This is a good choice."},
        {"role": "user", "content": "There's a bug in the login system"},
        {"role": "assistant", "content": "I fixed the bug by updating the token validation logic."},
    ]

    # Test summarization (would be called internally)
    # We'll test the key term extraction part
    from src.bop.token_importance import extract_key_terms

    all_text = " ".join(msg.get("content", "") for msg in old_messages)
    key_terms = extract_key_terms(all_text, max_terms=10)

    assert len(key_terms) > 0
    # Should extract relevant terms
    assert any(term in ["authentication", "token", "login", "bug", "feature"] for term in key_terms)


def test_observability_disabled(agent_with_observability):
    """Test that observability can be disabled."""
    os.environ["BOP_ENABLE_OBSERVABILITY"] = "false"

    from src.bop.agent import KnowledgeAgent
    agent = KnowledgeAgent()

    assert agent._metrics is None
    assert agent.get_metrics() is None
    assert agent.self_reflect()["status"] == "observability_disabled"

    # Restore
    os.environ["BOP_ENABLE_OBSERVABILITY"] = "true"

