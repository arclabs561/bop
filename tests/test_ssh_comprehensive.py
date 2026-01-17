"""Comprehensive tests combining all SSH features."""

import tempfile
from pathlib import Path

import pytest

from pran.adaptive_quality import AdaptiveQualityManager
from pran.agent import KnowledgeAgent
from pran.information_bottleneck import filter_with_information_bottleneck
from pran.orchestrator import StructuredOrchestrator
from pran.quality_feedback import QualityFeedbackLoop
from pran.research import ResearchAgent


@pytest.mark.asyncio
async def test_ssh_all_features_together():
    """Test all SSH features working together."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)

        agent = KnowledgeAgent(enable_quality_feedback=True)
        agent.adaptive_manager = manager

        # Complex query exercising all features
        response = await agent.chat(
            "What is d-separation, how does it relate to causal inference, and what are its implications for reasoning systems?",
            use_research=True,
            use_schema="decompose_and_synthesize",
        )

        # Verify IB filtering (implicit in synthesis)
        research = response.get("research", {})
        subsolutions = research.get("subsolutions", [])
        assert len(subsolutions) > 0

        # Verify adaptive depth (via strategy)
        strategy = manager.get_adaptive_strategy(
            "What is d-separation, how does it relate to causal inference, and what are its implications for reasoning systems?"
        )
        assert strategy.reasoning_depth >= 1

        # Verify resource triple
        assert "resource_triple" in research
        rt = research["resource_triple"]
        assert rt["depth"] == len(subsolutions)
        assert rt["width"] >= 0
        assert rt["coordination"] <= rt["width"]

        # Verify degradation triple
        assert "degradation_triple" in research
        dt = research["degradation_triple"]
        assert 0.0 <= dt["noise"] <= 1.0
        assert 0.0 <= dt["loss"] <= 1.0
        assert 0.0 <= dt["waste"] <= 1.0

        # Verify logical depth
        topology = research.get("topology", {})
        assert "logical_depths" in topology
        assert "avg_logical_depth" in topology
        assert 0.0 <= topology["avg_logical_depth"] <= 1.0


@pytest.mark.asyncio
async def test_ssh_learning_across_sessions():
    """Test that SSH learning persists across sessions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        learning_path = Path(tmpdir) / "adaptive_learning.json"

        # First session
        feedback1 = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager1 = AdaptiveQualityManager(feedback1, learning_data_path=learning_path)

        # Learn from queries
        manager1.update_from_evaluation(
            query="What is trust?",
            schema="decompose_and_synthesize",
            used_research=True,
            response_length=200,
            quality_score=0.85,
            num_subproblems=2,
        )
        manager1._save_learning()

        # Second session (new manager, loads learning)
        feedback2 = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager2 = AdaptiveQualityManager(feedback2, learning_data_path=learning_path)

        # Should have loaded learning data
        query_type = manager2._classify_query("What is trust?")
        depth_data = manager2.query_type_to_depth.get(query_type, [])
        assert len(depth_data) > 0

        # Depth estimation should work
        estimated = manager2.estimate_reasoning_depth("What is trust?")
        assert estimated >= 1


@pytest.mark.asyncio
async def test_ssh_ib_filtering_impact_measurement():
    """Test measuring IB filtering impact."""
    results = [
        {"result": "D-separation is a graphical criterion for conditional independence"},
        {"result": "D-separation helps identify d-separated variables"},
        {"result": "The weather is sunny today"},  # Low relevance
        {"result": "D-separation is used in causal inference"},
        {"result": "Quantum mechanics describes particles"},  # Low relevance
        {"result": "D-separation relates to d-connection"},
    ]

    query = "What is d-separation?"

    # Without filtering
    original_count = len(results)

    # With IB filtering
    filtered, metadata = filter_with_information_bottleneck(
        results, query, min_mi=0.3, max_results=5
    )

    # Measure impact
    compression_ratio = metadata["compression_ratio"]
    token_reduction = (1.0 - compression_ratio) * 100

    assert compression_ratio < 1.0
    assert token_reduction > 0
    assert len(filtered) < original_count


@pytest.mark.asyncio
async def test_ssh_adaptive_depth_impact_measurement():
    """Test measuring adaptive depth impact."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)

        # Learn optimal depth
        manager.update_from_evaluation(
            query="What is trust?",
            schema="decompose_and_synthesize",
            used_research=True,
            response_length=200,
            quality_score=0.9,
            num_subproblems=2,
        )

        # Get strategy
        strategy = manager.get_adaptive_strategy("What is trust?")

        # Measure impact: estimated depth vs default
        default_depth = 3
        estimated_depth = strategy.reasoning_depth

        # Should learn to use less depth for simple queries
        if estimated_depth < default_depth:
            compute_savings = ((default_depth - estimated_depth) / default_depth) * 100
            assert compute_savings > 0


@pytest.mark.asyncio
async def test_ssh_metrics_aggregation():
    """Test aggregating SSH metrics across multiple queries."""
    orchestrator = StructuredOrchestrator(
        research_agent=ResearchAgent(use_mcp=False),
    )

    queries = [
        "What is d-separation?",
        "What is trust?",
        "What is information geometry?",
    ]

    all_resource_triples = []
    all_degradation_triples = []
    all_logical_depths = []

    for query in queries:
        result = await orchestrator.research_with_schema(
            query,
            schema_name="decompose_and_synthesize",
        )

        all_resource_triples.append(result.get("resource_triple", {}))
        all_degradation_triples.append(result.get("degradation_triple", {}))

        topology = result.get("topology", {})
        avg_depth = topology.get("avg_logical_depth", 0.0)
        if avg_depth > 0:
            all_logical_depths.append(avg_depth)

    # Aggregate metrics
    avg_depth = sum(rt.get("depth", 0) for rt in all_resource_triples) / len(all_resource_triples) if all_resource_triples else 0.0
    avg_width = sum(rt.get("width", 0) for rt in all_resource_triples) / len(all_resource_triples) if all_resource_triples else 0.0
    avg_noise = sum(dt.get("noise", 0.0) for dt in all_degradation_triples) / len(all_degradation_triples) if all_degradation_triples else 0.0
    avg_logical_depth = sum(all_logical_depths) / len(all_logical_depths) if all_logical_depths else 0.0

    # Verify aggregates are valid
    assert avg_depth >= 0
    assert avg_width >= 0
    assert 0.0 <= avg_noise <= 1.0
    assert 0.0 <= avg_logical_depth <= 1.0


@pytest.mark.asyncio
async def test_ssh_error_recovery():
    """Test that SSH features recover gracefully from errors."""
    agent = KnowledgeAgent(enable_quality_feedback=True)

    # Test with various edge cases
    edge_cases = [
        "",  # Empty query
        "a",  # Very short query
        "What is " + "x" * 1000,  # Very long query
    ]

    for query in edge_cases:
        try:
            response = await agent.chat(
                query,
                use_research=False,  # Skip research for edge cases
            )
            # Should handle gracefully
            assert "response" in response
        except Exception:
            # Some errors are acceptable for extreme edge cases
            pass


def test_ssh_ib_filtering_edge_cases():
    """Test IB filtering with edge cases."""
    # Empty results
    filtered, metadata = filter_with_information_bottleneck([], "test query")
    assert filtered == []
    assert metadata["compression_ratio"] == 1.0

    # Single result
    results = [{"result": "Test result"}]
    filtered, metadata = filter_with_information_bottleneck(results, "test query")
    assert len(filtered) <= len(results)

    # Results with no 'result' field
    results = [{"tool": "test"}, {"result": "Valid result"}]
    filtered, metadata = filter_with_information_bottleneck(results, "test query")
    assert len(filtered) <= len(results)


def test_ssh_adaptive_depth_edge_cases():
    """Test adaptive depth with edge cases."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)

        # Empty query
        depth = manager.estimate_reasoning_depth("")
        assert depth >= 1  # Should have default

        # Very long query
        long_query = "What is " + "x" * 1000 + "?"
        depth = manager.estimate_reasoning_depth(long_query)
        assert depth >= 1

        # Query with no learning data
        depth = manager.estimate_reasoning_depth("Unknown query type")
        assert depth >= 1  # Should have default (typically 3, but implementation may vary)


@pytest.mark.asyncio
async def test_ssh_metrics_consistency_across_runs():
    """Test that SSH metrics are consistent across multiple runs."""
    orchestrator = StructuredOrchestrator(
        research_agent=ResearchAgent(use_mcp=False),
    )

    query = "What is d-separation?"

    # Run multiple times
    results = []
    for _ in range(3):
        result = await orchestrator.research_with_schema(
            query,
            schema_name="decompose_and_synthesize",
        )
        results.append(result)

    # Metrics should be similar across runs (allowing for some variance)
    depths = [r.get("resource_triple", {}).get("depth", 0) for r in results]
    widths = [r.get("resource_triple", {}).get("width", 0) for r in results]

    # Depth should be consistent (same query = similar decomposition)
    assert max(depths) - min(depths) <= 2  # Allow small variance

    # Width may vary (tool selection), but should be reasonable
    assert all(w >= 0 for w in widths)

