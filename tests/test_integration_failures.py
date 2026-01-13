"""Integration tests for failure scenarios."""

import tempfile

from bop.agent import KnowledgeAgent


async def test_agent_with_corrupted_sessions():
    """Test agent handles corrupted session files."""
    with tempfile.TemporaryDirectory():
        # Create agent
        agent = KnowledgeAgent(enable_quality_feedback=True)
        manager = agent.quality_feedback.session_manager

        # Create a session
        session_id = manager.create_session()
        manager.flush_buffer()

        # Corrupt the session file
        session_file = manager.sessions_dir / f"{session_id}.json"
        session_file.write_text("corrupted")

        # Agent should still work
        response = await agent.chat("test query")
        assert "response" in response


async def test_agent_with_storage_failure():
    """Test agent handles storage failures gracefully."""
    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)
        manager = agent.quality_feedback.session_manager

        # Mock storage to fail

        def failing_save(session):
            raise IOError("Storage failure")

        manager.storage.save_session = failing_save

        # Agent should still respond (may lose persistence but shouldn't crash)
        response = await agent.chat("test query")
        assert "response" in response


async def test_agent_with_index_corruption():
    """Test agent handles index corruption."""
    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)
        manager = agent.quality_feedback.session_manager

        # Create some sessions
        for i in range(3):
            manager.create_session()
        manager.flush_buffer()

        # Corrupt index
        if manager.enable_indexing:
            index_file = manager.index_file
            index_file.write_text("corrupted")

        # Agent should still work
        response = await agent.chat("test query")
        assert "response" in response


async def test_agent_buffer_flush_failure():
    """Test agent handles buffer flush failures."""
    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)
        manager = agent.quality_feedback.session_manager

        # Add evaluation
        manager.add_evaluation(
            query="test",
            response="response",
            response_length=100,
            score=0.7,
            judgment_type="relevance",
            quality_flags=[],
            reasoning="",
            metadata={},
        )

        # Mock flush to fail

        def failing_flush(storage):
            raise IOError("Flush failure")

        manager.write_buffer.flush = failing_flush

        # Should handle gracefully
        try:
            manager.flush_buffer()
        except Exception:
            pass  # Expected to fail, but shouldn't crash agent

        # Agent should still work
        response = await agent.chat("test query")
        assert "response" in response


async def test_agent_quality_feedback_failure():
    """Test agent handles quality feedback failures."""
    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)

        # Mock quality feedback to fail

        def failing_eval(*args, **kwargs):
            raise Exception("Quality feedback failure")

        agent.quality_feedback.evaluate_and_learn = failing_eval

        # Agent should still respond
        response = await agent.chat("test query")
        assert "response" in response


async def test_agent_adaptive_manager_failure():
    """Test agent handles adaptive manager failures."""
    with tempfile.TemporaryDirectory():
        agent = KnowledgeAgent(enable_quality_feedback=True)

        # Mock adaptive manager to fail
        if agent.adaptive_manager:

            def failing_strategy(*args, **kwargs):
                raise Exception("Adaptive manager failure")

            agent.adaptive_manager.get_adaptive_strategy = failing_strategy

        # Agent should still respond
        response = await agent.chat("test query")
        assert "response" in response

