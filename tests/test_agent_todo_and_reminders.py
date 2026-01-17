"""Tests for TODO list management and system reminders."""

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


@pytest.fixture
def temp_scratchpad():
    """Create temporary scratchpad directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["BOP_ENABLE_SCRATCHPAD"] = "true"
        os.environ["BOP_SCRATCHPAD_DIR"] = tmpdir
        yield Path(tmpdir)
        # Cleanup
        if "BOP_ENABLE_SCRATCHPAD" in os.environ:
            del os.environ["BOP_ENABLE_SCRATCHPAD"]
        if "BOP_SCRATCHPAD_DIR" in os.environ:
            del os.environ["BOP_SCRATCHPAD_DIR"]


def test_todo_list_update_structure(agent):
    """Test that TODO list update returns proper structure."""
    todos = [
        {"id": "1", "content": "Task 1", "status": "completed", "priority": "high"},
        {"id": "2", "content": "Task 2", "status": "in_progress", "priority": "high"},
        {"id": "3", "content": "Task 3", "status": "pending", "priority": "medium"},
    ]

    result = agent.update_todo_list(todos)

    assert "todos" in result
    assert "progress" in result
    assert "instructions" in result

    assert result["progress"]["completed"] == 1
    assert result["progress"]["total"] == 3
    assert len(result["todos"]) == 3
    assert len(result["instructions"]) > 0


def test_todo_list_instructions_embedded(agent):
    """Test that instructions are embedded in TODO list results."""
    todos = [
        {"id": "1", "content": "Test task", "status": "in_progress", "priority": "high"},
    ]

    result = agent.update_todo_list(todos)

    instructions = result["instructions"]
    assert "TODO list updated successfully" in instructions
    assert "Keep using the TODO list" in instructions
    assert "Current task in progress" in instructions or "Next task" in instructions


def test_todo_list_validation(agent):
    """Test that invalid TODO items are filtered."""
    todos = [
        {"id": "1"},  # Missing content
        {"content": "test"},  # Missing id
        {"id": "3", "content": "valid", "status": "invalid_status"},  # Invalid status
        {"id": "4", "content": "valid task", "status": "pending"},  # Valid
    ]

    result = agent.update_todo_list(todos)

    # Should filter invalid items
    assert len(result["todos"]) <= 2  # At most 2 valid items
    assert any(item["id"] == "4" for item in result["todos"])


def test_todo_list_empty_handling(agent):
    """Test that empty TODO list is handled gracefully."""
    result = agent.update_todo_list([])

    assert result["progress"]["total"] == 0
    assert result["progress"]["completed"] == 0
    assert len(result["todos"]) == 0


def test_system_reminders_without_todo(agent):
    """Test system reminder generation without TODO list."""
    agent.todo_list = []
    reminders = agent._generate_system_reminders("Test message")

    assert len(reminders) > 0
    assert any("Do what has been asked" in r for r in reminders)


def test_system_reminders_with_todo(agent):
    """Test system reminder generation with TODO list."""
    agent.update_todo_list([
        {"id": "1", "content": "Test task", "status": "in_progress", "priority": "high"},
    ])

    reminders = agent._generate_system_reminders("Test message")

    assert len(reminders) > 0
    assert any("todo list" in r.lower() for r in reminders)
    assert any("Test task" in r for r in reminders)


def test_system_reminders_formatting(agent):
    """Test that reminders are properly formatted."""
    agent.update_todo_list([
        {"id": "1", "content": "Task 1", "status": "completed", "priority": "high"},
        {"id": "2", "content": "Task 2", "status": "in_progress", "priority": "high"},
        {"id": "3", "content": "Task 3", "status": "pending", "priority": "medium"},
    ])

    reminders = agent._generate_system_reminders("Test message")

    # Should have formatted TODO list in reminders
    reminder_text = " ".join(reminders)
    assert "✓" in reminder_text or "→" in reminder_text or "○" in reminder_text
    assert "Progress:" in reminder_text


def test_scratchpad_persistence(agent, temp_scratchpad):
    """Test file-based scratchpad persistence."""
    # Update TODO list
    todos = [
        {"id": "1", "content": "Persistent task", "status": "in_progress", "priority": "high"},
    ]
    agent.update_todo_list(todos)

    # Check if file was created
    todo_file = temp_scratchpad / "todo.md"
    assert todo_file.exists(), "Scratchpad file should be created"

    # Verify content
    content = todo_file.read_text()
    assert "Persistent task" in content
    assert "in_progress" in content


def test_scratchpad_loading(agent, temp_scratchpad):
    """Test that TODO list loads from scratchpad."""
    # Create scratchpad file manually
    todo_file = temp_scratchpad / "todo.md"
    todo_file.write_text("""# TODO List
Last updated: 2025-01-16T10:00:00Z

→ [1] Test task (status: in_progress, priority: high)
○ [2] Another task (status: pending, priority: medium)

Progress: 0/2 completed
""")

    # Create new agent (should load from scratchpad)
    agent2 = KnowledgeAgent(enable_system_reminders=True)
    agent2.enable_scratchpad = True
    agent2.scratchpad_dir = temp_scratchpad
    agent2._load_todo_from_scratchpad()

    # Should have loaded TODO items
    assert len(agent2.todo_list) >= 1
    assert any(item.get("content") == "Test task" for item in agent2.todo_list)


def test_todo_list_metrics_tracking(agent):
    """Test that TODO updates are tracked in metrics."""
    initial_updates = len(agent._metrics["todo_updates"])

    agent.update_todo_list([
        {"id": "1", "content": "Test", "status": "pending", "priority": "medium"},
    ])

    assert len(agent._metrics["todo_updates"]) > initial_updates
    update = agent._metrics["todo_updates"][-1]
    assert "todo_count" in update
    assert "completed" in update
    assert "timestamp" in update


def test_reminder_metrics_tracking(agent):
    """Test that reminder generations are tracked."""
    initial_reminders = len(agent._metrics["reminder_generations"])

    agent._generate_system_reminders("Test message")

    assert len(agent._metrics["reminder_generations"]) > initial_reminders
    reminder_event = agent._metrics["reminder_generations"][-1]
    assert "reminder_count" in reminder_event
    assert "has_todo" in reminder_event
    assert "timestamp" in reminder_event

