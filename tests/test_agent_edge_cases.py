"""Edge case tests for agent features."""

import json
import os
import tempfile
from pathlib import Path

import pytest

os.environ["BOP_ENABLE_OBSERVABILITY"] = "true"


@pytest.fixture
def agent():
    """Create agent for testing."""
    from src.pran.agent import KnowledgeAgent
    return KnowledgeAgent(enable_system_reminders=True)


def test_token_estimation_none(agent):
    """Test token estimation with None."""
    assert agent._estimate_tokens(None) == 0


def test_token_estimation_empty_string(agent):
    """Test token estimation with empty string."""
    assert agent._estimate_tokens("") == 0
    assert agent._estimate_tokens("   ") == 0  # Whitespace only


def test_token_estimation_non_string(agent):
    """Test token estimation with non-string types."""
    # Should handle gracefully
    assert agent._estimate_tokens(123) == 0  # Non-string converted
    assert agent._estimate_tokens([]) == 0
    assert agent._estimate_tokens({}) == 0


def test_token_estimation_very_long_string(agent):
    """Test token estimation with very long string."""
    long_text = "word " * 10000  # 50,000 characters
    tokens = agent._estimate_tokens(long_text)
    assert tokens > 0
    assert tokens < len(long_text)  # Should be less than character count


def test_token_estimation_unicode(agent):
    """Test token estimation with Unicode characters."""
    unicode_text = "Hello 世界 🌍"
    tokens = agent._estimate_tokens(unicode_text)
    assert tokens > 0


def test_conversation_token_count_empty(agent):
    """Test token count with empty conversation."""
    agent.conversation_history = []
    assert agent._get_conversation_token_count() == 0


def test_conversation_token_count_invalid_messages(agent):
    """Test token count with invalid message structures."""
    agent.conversation_history = [
        None,
        "not a dict",
        {"role": "user"},  # Missing content
        {"content": "test"},  # Missing role
        {"role": "user", "content": ""},  # Empty content
        {"role": "user", "content": "valid message"},
    ]

    # Should handle gracefully
    count = agent._get_conversation_token_count()
    assert count > 0  # Should count valid messages


def test_save_metrics_permission_error(agent, monkeypatch):
    """Test metrics save handles permission errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics_file = Path(tmpdir) / "metrics.json"
        agent.metrics_path = metrics_file

        # Simulate permission error
        def mock_write_text(*args, **kwargs):
            raise PermissionError("Permission denied")

        monkeypatch.setattr(metrics_file, "write_text", mock_write_text)

        # Should not crash
        agent._save_metrics()
        # File should not exist (write failed)
        assert not metrics_file.exists()


def test_save_metrics_disk_full(agent, monkeypatch):
    """Test metrics save handles disk full errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics_file = Path(tmpdir) / "metrics.json"
        agent.metrics_path = metrics_file

        # Simulate disk full
        def mock_write_text(*args, **kwargs):
            raise OSError("No space left on device")

        monkeypatch.setattr(metrics_file, "write_text", mock_write_text)

        # Should not crash
        agent._save_metrics()


def test_load_metrics_corrupted_json(agent):
    """Test metrics load handles corrupted JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics_file = Path(tmpdir) / "agent_metrics.json"
        metrics_file.write_text("{ invalid json }")
        agent.metrics_path = metrics_file

        # Should not crash
        agent._load_metrics()
        # Should still have empty metrics
        assert agent._metrics is not None


def test_load_metrics_missing_keys(agent):
    """Test metrics load handles missing keys."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics_file = Path(tmpdir) / "agent_metrics.json"
        metrics_file.write_text(json.dumps({
            "version": "1.0",
            "last_updated": "2025-01-16T10:00:00Z",
            # Missing "metrics" key
        }))
        agent.metrics_path = metrics_file

        # Should not crash
        agent._load_metrics()


def test_load_metrics_invalid_structure(agent):
    """Test metrics load handles invalid structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics_file = Path(tmpdir) / "agent_metrics.json"
        metrics_file.write_text(json.dumps({
            "version": "1.0",
            "metrics": "not a dict",  # Invalid type
        }))
        agent.metrics_path = metrics_file

        # Should not crash
        agent._load_metrics()


def test_load_metrics_invalid_list_items(agent):
    """Test metrics load handles invalid list items."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics_file = Path(tmpdir) / "agent_metrics.json"
        metrics_file.write_text(json.dumps({
            "version": "1.0",
            "metrics": {
                "compaction_events": ["not a dict", 123, None],  # Invalid items
            }
        }))
        agent.metrics_path = metrics_file

        # Should not crash
        agent._load_metrics()
        # Should skip invalid items
        assert isinstance(agent._metrics["compaction_events"], list)


def test_health_check_empty_metrics(agent):
    """Test health check with empty metrics."""
    agent._metrics = {
        "compaction_events": [],
        "todo_updates": [],
        "reminder_generations": [],
        "errors": [],
    }

    # Should return None (no operations yet)
    result = agent._check_health_and_auto_optimize()
    assert result is None


def test_health_check_division_by_zero(agent):
    """Test health check handles division by zero."""
    # Create metrics that might cause division issues
    agent._metrics = {
        "compaction_events": [],
        "todo_updates": [{"todo_count": 0}],
        "reminder_generations": [],
        "errors": [],
    }

    # Fill to trigger health check
    for i in range(20):
        agent._metrics["todo_updates"].append({"todo_count": 0})

    # Should not crash
    agent._check_health_and_auto_optimize()
    # May return None or result, but shouldn't crash


def test_compaction_empty_messages(agent):
    """Test compaction with empty message content."""
    import asyncio

    agent.conversation_history = [
        {"role": "user", "content": ""},
        {"role": "assistant", "content": "   "},  # Whitespace only
        {"role": "user", "content": "valid message"},
    ] * 10  # Repeat to get enough messages

    # Should handle gracefully
    asyncio.run(agent._compact_conversation_history())


def test_compaction_invalid_message_structure(agent):
    """Test compaction with invalid message structures."""
    import asyncio

    agent.conversation_history = [
        None,
        "not a dict",
        {"role": "user"},  # Missing content
        {"content": "test"},  # Missing role
        {"role": "user", "content": "valid"},
    ] * 5  # Repeat to get enough messages

    # Should handle gracefully
    asyncio.run(agent._compact_conversation_history())


def test_instruction_tracking_division_by_zero(agent):
    """Test instruction tracking handles division by zero."""
    # Empty TODO list
    result = agent.update_todo_list([])

    # Should not crash
    assert result["progress"]["total"] == 0
    assert result["progress"]["completed"] == 0

    # Check metrics were tracked
    if agent._metrics and "instruction_usage" in agent._metrics:
        usage = agent._metrics["instruction_usage"][-1]
        assert usage["context"]["completion_rate"] == 0.0


def test_instruction_tracking_invalid_completion_rate(agent):
    """Test instruction tracking handles invalid completion rates."""
    # Create TODO list with more completed than total (shouldn't happen, but test)
    todos = [
        {"id": "1", "content": "Task", "status": "completed"},
    ]
    result = agent.update_todo_list(todos)

    # Should handle gracefully
    assert result["progress"]["total"] == 1
    assert result["progress"]["completed"] == 1

    # Completion rate should be 1.0 (not > 1.0)
    if agent._metrics and "instruction_usage" in agent._metrics:
        usage = agent._metrics["instruction_usage"][-1]
        assert 0.0 <= usage["context"]["completion_rate"] <= 1.0

