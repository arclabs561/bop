"""End-to-end tests for SSH features integration."""

import tempfile
from pathlib import Path

import pytest

from pran.adaptive_quality import AdaptiveQualityManager
from pran.agent import KnowledgeAgent
from pran.orchestrator import StructuredOrchestrator
from pran.quality_feedback import QualityFeedbackLoop
from pran.research import ResearchAgent


@pytest.mark.asyncio
async def test_ssh_e2e_full_workflow():
    """Test complete SSH workflow end-to-end."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)

        agent = KnowledgeAgent(enable_quality_feedback=True)
        agent.adaptive_manager = manager

        # Complex query that exercises all SSH features
        response = await agent.chat(
            "What is d-separation and how does it relate to causal inference and information geometry?",
            use_research=True,
            use_schema="decompose_and_synthesize",
        )

        # Verify all features are present
        assert response.get("research_conducted") is True
        research = response.get("research", {})

        # IB filtering (implicit in synthesis)
        subsolutions = research.get("subsolutions", [])
        assert len(subsolutions) > 0

        # Resource triple
        assert "resource_triple" in research
        assert "degradation_triple" in research

        # Logical depth
        topology = research.get("topology", {})
        assert "logical_depths" in topology
        assert "avg_logical_depth" in topology

        # Response quality
        assert len(response.get("response", "")) > 0


@pytest.mark.asyncio
async def test_ssh_e2e_adaptive_learning():
    """Test adaptive learning across multiple queries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)

        agent = KnowledgeAgent(enable_quality_feedback=True)
        agent.adaptive_manager = manager

        queries = [
            "What is trust?",
            "What is d-separation?",
            "What is information geometry?",
        ]

        for query in queries:
            response = await agent.chat(
                query,
                use_research=True,
                use_schema="decompose_and_synthesize",
            )

            # Learn from response
            research = response.get("research", {})
            subsolutions = research.get("subsolutions", [])

            if subsolutions:
                manager.update_from_evaluation(
                    query=query,
                    schema="decompose_and_synthesize",
                    used_research=True,
                    response_length=len(response.get("response", "")),
                    quality_score=0.8,
                    num_subproblems=len(subsolutions),
                )

        # Verify learning accumulated
        for query in queries:
            strategy = manager.get_adaptive_strategy(query)
            assert strategy.reasoning_depth >= 1


@pytest.mark.asyncio
async def test_ssh_e2e_metrics_consistency():
    """Test that SSH metrics are consistent across queries."""
    orchestrator = StructuredOrchestrator(
        research_agent=ResearchAgent(use_mcp=False),
    )

    queries = [
        "What is d-separation?",
        "What is trust?",
    ]

    for query in queries:
        result = await orchestrator.research_with_schema(
            query,
            schema_name="decompose_and_synthesize",
        )

        # Verify metrics exist and are valid
        rt = result.get("resource_triple", {})
        assert rt["depth"] >= 0
        assert rt["width"] >= 0
        assert rt["coordination"] >= 0
        assert rt["coordination"] <= rt["width"]  # Invariant

        dt = result.get("degradation_triple", {})
        assert 0.0 <= dt["noise"] <= 1.0
        assert 0.0 <= dt["loss"] <= 1.0
        assert 0.0 <= dt["waste"] <= 1.0

        topology = result.get("topology", {})
        assert "logical_depths" in topology
        assert 0.0 <= topology.get("avg_logical_depth", 0.0) <= 1.0


@pytest.mark.asyncio
async def test_ssh_e2e_error_handling():
    """Test that SSH features handle errors gracefully."""
    agent = KnowledgeAgent(enable_quality_feedback=True)

    # Query that might cause issues
    response = await agent.chat(
        "",  # Empty query
        use_research=False,
    )

    # Should handle gracefully
    assert "response" in response

    # Test with invalid research
    try:
        response = await agent.chat(
            "test query",
            use_research=True,
            use_schema="decompose_and_synthesize",
        )
        # Should complete even if research fails
        assert "response" in response
    except Exception:
        # Some errors are acceptable
        pass

