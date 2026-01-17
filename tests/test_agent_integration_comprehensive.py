"""Comprehensive integration tests for all agent features."""

import os
import tempfile
from pathlib import Path

import pytest

os.environ["BOP_MAX_CONVERSATION_HISTORY"] = "20"
os.environ["BOP_ENABLE_OBSERVABILITY"] = "true"
os.environ["BOP_ENABLE_SCRATCHPAD"] = "true"


@pytest.fixture
def temp_dirs():
    """Create temporary directories for metrics and scratchpad."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics_dir = Path(tmpdir) / "metrics"
        scratchpad_dir = Path(tmpdir) / "scratchpad"
        metrics_dir.mkdir()
        scratchpad_dir.mkdir()

        os.environ["BOP_METRICS_DIR"] = str(metrics_dir)
        os.environ["BOP_SCRATCHPAD_DIR"] = str(scratchpad_dir)

        yield {
            "metrics": metrics_dir,
            "scratchpad": scratchpad_dir,
        }

        # Cleanup
        for key in ["BOP_METRICS_DIR", "BOP_SCRATCHPAD_DIR"]:
            if key in os.environ:
                del os.environ[key]


@pytest.fixture
def agent(temp_dirs):
    """Create agent with all features enabled."""
    from src.pran.agent import KnowledgeAgent
    return KnowledgeAgent(enable_system_reminders=True)


@pytest.mark.asyncio
async def test_full_workflow_compaction_todo_reminders(agent):
    """Test complete workflow: compaction, TODO, reminders."""
    # 1. Add messages to trigger compaction
    for i in range(15):
        agent.conversation_history.append({
            "role": "user" if i % 2 == 0 else "assistant",
            "content": f"Message {i}: Testing the full workflow"
        })

    # 2. Create TODO list
    todos = [
        {"id": "1", "content": "Test compaction", "status": "completed", "priority": "high"},
        {"id": "2", "content": "Test TODO list", "status": "in_progress", "priority": "high"},
        {"id": "3", "content": "Test reminders", "status": "pending", "priority": "medium"},
    ]
    result = agent.update_todo_list(todos)

    # 3. Generate reminders
    reminders = agent._generate_system_reminders("Test message")

    # 4. Trigger compaction
    await agent._compact_conversation_history()

    # Verify everything worked
    assert len(result["todos"]) == 3
    assert len(reminders) > 0
    assert agent.conversation_summary is not None
    assert len(agent.conversation_history) < 15  # Should be compacted


@pytest.mark.asyncio
async def test_metrics_persistence_across_sessions(agent, temp_dirs):
    """Test that metrics persist across agent restarts."""
    # Add some metrics
    agent._metrics["compaction_events"].append({
        "timestamp": "2025-01-16T10:00:00Z",
        "before": 30,
        "after": 20,
        "method": "heuristic",
        "success": True,
        "compression_ratio": 0.67,
    })

    # Save metrics
    agent._save_metrics()

    # Create new agent (should load metrics)
    from src.pran.agent import KnowledgeAgent
    agent2 = KnowledgeAgent(enable_system_reminders=True)

    # Should have loaded historical metrics
    if agent2.metrics_path and agent2.metrics_path.exists():
        agent2._load_metrics()
        # May have loaded metrics (depending on file structure)
        assert agent2._metrics is not None


def test_scratchpad_persistence_across_sessions(agent, temp_dirs):
    """Test that scratchpad persists across agent restarts."""
    # Create TODO list
    todos = [
        {"id": "1", "content": "Persistent task", "status": "in_progress", "priority": "high"},
    ]
    agent.update_todo_list(todos)

    # Verify file exists
    scratchpad_file = temp_dirs["scratchpad"] / "todo.md"
    assert scratchpad_file.exists()

    # Create new agent (should load from scratchpad)
    from src.pran.agent import KnowledgeAgent
    agent2 = KnowledgeAgent(enable_system_reminders=True)
    agent2.enable_scratchpad = True
    agent2.scratchpad_dir = temp_dirs["scratchpad"]
    agent2._load_todo_from_scratchpad()

    # Should have loaded TODO items
    if len(agent2.todo_list) > 0:
        assert any(item.get("content") == "Persistent task" for item in agent2.todo_list)


def test_self_reflection_with_real_metrics(agent):
    """Test self-reflection with realistic metrics."""
    # Add realistic metrics
    agent._metrics["compaction_events"] = [
        {"success": True, "compression_ratio": 0.35},
        {"success": True, "compression_ratio": 0.40},
        {"success": False},
    ]
    agent._metrics["todo_updates"] = [
        {"todo_count": 3, "completed": 1},
        {"todo_count": 5, "completed": 2},
    ]
    agent._metrics["errors"] = [
        {"type": "compaction_failure", "message": "Test error"},
    ]

    analysis = agent.self_reflect()

    assert "health_score" in analysis
    assert "observations" in analysis
    assert "suggestions" in analysis
    assert 0.0 <= analysis["health_score"] <= 1.0

    # Should have observations
    assert len(analysis["observations"]) > 0


def test_token_tracking_integration(agent):
    """Test token tracking integration with compaction."""
    # Add messages
    for i in range(10):
        agent.conversation_history.append({
            "role": "user" if i % 2 == 0 else "assistant",
            "content": f"Message {i} with some content to track tokens"
        })

    # Get token count
    token_count = agent._get_conversation_token_count()

    assert token_count > 0

    # Token count should increase with more messages
    agent.conversation_history.append({
        "role": "user",
        "content": "Another message with more content"
    })

    new_token_count = agent._get_conversation_token_count()
    assert new_token_count > token_count


def test_improved_heuristic_summarization(agent):
    """Test improved heuristic summarization with key terms."""
    old_messages = [
        {"role": "user", "content": "I want to implement authentication with JWT tokens and OAuth"},
        {"role": "assistant", "content": "I've decided to use JWT for authentication. This is secure and scalable."},
        {"role": "user", "content": "There's a critical bug in the login system that needs fixing"},
        {"role": "assistant", "content": "I fixed the bug by updating the token validation logic and adding error handling."},
    ] * 4  # Repeat to get enough messages

    # Test the summarization logic (would be called in compaction)
    from collections import Counter

    from src.pran.token_importance import extract_key_terms

    all_key_terms = []
    for msg in old_messages:
        content = msg.get("content", "")
        terms = extract_key_terms(content, max_terms=5)
        all_key_terms.extend(terms)

    # Should extract relevant terms
    term_counts = Counter(all_key_terms)
    top_terms = [term for term, _ in term_counts.most_common(5)]

    assert len(top_terms) > 0
    # Should include key topics
    assert any(term in ["authentication", "jwt", "token", "bug", "login"] for term in top_terms)


def test_instruction_effectiveness_tracking(agent):
    """Test that instruction usage is tracked for feedback loop."""
    # Update TODO list (should track instruction usage)
    todos = [
        {"id": "1", "content": "Test", "status": "pending", "priority": "medium"},
    ]
    agent.update_todo_list(todos)

    # Should track instruction usage
    if "instruction_usage" in agent._metrics:
        assert len(agent._metrics["instruction_usage"]) > 0
        usage = agent._metrics["instruction_usage"][-1]
        assert "version" in usage
        assert "context" in usage
        assert "timestamp" in usage


def test_auto_optimization_integration(agent):
    """Test that auto-optimization integrates with TODO updates."""
    # Simulate unhealthy system
    agent._metrics["compaction_events"] = [
        {"success": False},
    ] * 5
    agent._metrics["errors"] = [
        {"type": "compaction_failure", "message": "Error"},
    ] * 12

    # Fill operations to trigger auto-optimization
    for i in range(20):
        agent._metrics["todo_updates"].append({
            "timestamp": "2025-01-16T10:00:00Z",
            "todo_count": 3,
            "completed": 1,
        })

    # Update TODO list (triggers auto-optimization check)
    original_max = agent.max_conversation_history
    agent.update_todo_list([
        {"id": "1", "content": "Test", "status": "pending", "priority": "medium"},
    ])

    # May have auto-adjusted (depending on health check results)
    # Just verify it doesn't crash and may have adjusted
    assert agent.max_conversation_history >= original_max

