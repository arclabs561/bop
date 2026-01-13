"""Tests for token-level tracking and context window management."""

import os

import pytest

os.environ["BOP_ENABLE_OBSERVABILITY"] = "true"


@pytest.fixture
def agent():
    """Create agent for testing."""
    from src.bop.agent import KnowledgeAgent
    return KnowledgeAgent(enable_system_reminders=True)


def test_token_estimation_basic(agent):
    """Test basic token estimation."""
    text = "This is a test message with some words."
    tokens = agent._estimate_tokens(text)

    assert tokens > 0
    # Should be reasonable estimate
    assert tokens <= len(text)  # Never exceeds character count
    assert tokens >= len(text) // 10  # At least some reasonable fraction


def test_token_estimation_empty(agent):
    """Test token estimation with empty text."""
    assert agent._estimate_tokens("") == 0
    assert agent._estimate_tokens(None) == 0


def test_token_estimation_long_text(agent):
    """Test token estimation with long text."""
    long_text = "word " * 1000  # 5000 characters
    tokens = agent._estimate_tokens(long_text)

    assert tokens > 0
    # Should scale with text length
    assert tokens > agent._estimate_tokens("word")


def test_conversation_token_count(agent):
    """Test conversation token counting."""
    agent.conversation_history = [
        {"role": "user", "content": "Test message 1 with some content"},
        {"role": "assistant", "content": "Response 1 with more content here"},
        {"role": "user", "content": "Another test message"},
    ]

    token_count = agent._get_conversation_token_count()

    assert token_count > 0
    # Should account for all messages plus overhead
    content_tokens = sum(agent._estimate_tokens(msg.get("content", "")) for msg in agent.conversation_history)
    assert token_count >= content_tokens
    # Should include overhead (10 per message)
    assert token_count >= content_tokens + (len(agent.conversation_history) * 10)


def test_token_based_compaction_trigger(agent):
    """Test that token-based compaction triggers correctly."""
    # This test would require tiktoken to be available
    # For now, test the fallback behavior

    # Fill history
    for i in range(15):
        agent.conversation_history.append({
            "role": "user" if i % 2 == 0 else "assistant",
            "content": f"Test message {i} with some content to make it longer"
        })

    # Should use message count fallback if no tokenizer
    if agent._tokenizer is None:
        # Message-based compaction should still work
        threshold = int(agent.max_conversation_history * 0.7)
        assert len(agent.conversation_history) > threshold


def test_tokenizer_initialization(agent):
    """Test that tokenizer initializes correctly."""
    # Tokenizer may or may not be available
    # Test that agent handles both cases
    if agent._tokenizer is not None:
        # tiktoken is available
        assert hasattr(agent._tokenizer, 'encode')
    else:
        # Fallback to character estimation
        assert agent._estimate_tokens("test") > 0


def test_token_count_scales_with_content(agent):
    """Test that token count scales appropriately with content."""
    short_text = "Hello"
    long_text = "Hello " * 100

    short_tokens = agent._estimate_tokens(short_text)
    long_tokens = agent._estimate_tokens(long_text)

    assert long_tokens > short_tokens
    # Should scale roughly linearly (within reason)
    assert long_tokens > short_tokens * 50  # At least 50x for 100x content

