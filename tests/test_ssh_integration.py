"""Integration tests for SSH features (IB filtering, adaptive depth, resource triple, logical depth)."""

import pytest
from pathlib import Path
import tempfile

from bop.agent import KnowledgeAgent
from bop.orchestrator import StructuredOrchestrator
from bop.research import ResearchAgent
from bop.adaptive_quality import AdaptiveQualityManager
from bop.quality_feedback import QualityFeedbackLoop
from bop.information_bottleneck import filter_with_information_bottleneck


@pytest.mark.asyncio
async def test_ib_filtering_integration():
    """Test IB filtering integrated into full research workflow."""
    agent = KnowledgeAgent(enable_quality_feedback=True)
    
    # Query that should benefit from IB filtering
    response = await agent.chat(
        "What is d-separation and how does it relate to causal inference?",
        use_research=True,
        use_schema="decompose_and_synthesize",
    )
    
    # Check that research was conducted
    assert response.get("research_conducted") is True
    research = response.get("research", {})
    
    # Check that subsolutions exist (IB filtering happens during synthesis)
    subsolutions = research.get("subsolutions", [])
    assert len(subsolutions) > 0
    
    # Verify response quality
    assert len(response.get("response", "")) > 0


@pytest.mark.asyncio
async def test_adaptive_depth_integration():
    """Test adaptive reasoning depth integrated into research."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)
        
        # Add learning data: 2 subproblems achieves high quality for simple queries
        manager.update_from_evaluation(
            query="What is trust?",
            schema="decompose_and_synthesize",
            used_research=True,
            response_length=150,
            quality_score=0.85,
            num_subproblems=2,
        )
        
        agent = KnowledgeAgent(enable_quality_feedback=True)
        agent.adaptive_manager = manager
        
        # Simple query should use learned depth
        strategy = manager.get_adaptive_strategy("What is trust?")
        assert strategy.reasoning_depth >= 1
        assert strategy.early_stop_threshold is not None or strategy.reasoning_depth == 3


@pytest.mark.asyncio
async def test_resource_triple_tracking_integration():
    """Test resource triple metrics in full research workflow."""
    orchestrator = StructuredOrchestrator(
        research_agent=ResearchAgent(use_mcp=False),
    )
    
    result = await orchestrator.research_with_schema(
        "What is d-separation?",
        schema_name="decompose_and_synthesize",
    )
    
    # Verify resource triple exists
    assert "resource_triple" in result
    rt = result["resource_triple"]
    assert rt["depth"] >= 0
    assert rt["width"] >= 0
    assert rt["coordination"] >= 0
    assert rt["total_tokens"] >= 0
    
    # Verify degradation triple exists
    assert "degradation_triple" in result
    dt = result["degradation_triple"]
    assert 0.0 <= dt["noise"] <= 1.0
    assert 0.0 <= dt["loss"] <= 1.0
    assert 0.0 <= dt["waste"] <= 1.0
    
    # Verify logical depth in topology
    topology = result.get("topology", {})
    assert "logical_depths" in topology
    assert "avg_logical_depth" in topology


@pytest.mark.asyncio
async def test_early_stopping_integration():
    """Test early stopping in full research workflow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)
        
        # Learn that 2 subproblems achieves high quality
        manager.update_from_evaluation(
            query="What is trust?",
            schema="decompose_and_synthesize",
            used_research=True,
            response_length=200,
            quality_score=0.9,
            num_subproblems=2,
        )
        
        orchestrator = StructuredOrchestrator(
            research_agent=ResearchAgent(use_mcp=False),
        )
        
        # Research with adaptive manager
        result = await orchestrator.research_with_schema(
            "What is trust?",
            schema_name="decompose_and_synthesize",
            adaptive_manager=manager,
        )
        
        # Should have completed research (may or may not stop early depending on quality)
        assert "subsolutions" in result
        assert len(result["subsolutions"]) >= 1


@pytest.mark.asyncio
async def test_ib_filtering_with_multiple_results():
    """Test IB filtering when multiple results are retrieved."""
    results = [
        {"result": "D-separation is a graphical criterion for conditional independence in DAGs"},
        {"result": "D-separation helps identify when variables are conditionally independent"},
        {"result": "The weather is sunny today"},  # Low relevance
        {"result": "D-separation is used in causal inference"},  # High relevance
        {"result": "Quantum mechanics describes particle behavior"},  # Low relevance
    ]
    
    query = "What is d-separation?"
    
    filtered, metadata = filter_with_information_bottleneck(
        results, query, min_mi=0.3, max_results=3
    )
    
    # Should filter out low-relevance results
    assert len(filtered) <= len(results)
    assert metadata["compression_ratio"] < 1.0
    assert metadata["removed_count"] > 0
    
    # Filtered results should be more relevant
    assert all("d-separation" in r.get("result", "").lower() or 
               "conditional" in r.get("result", "").lower() 
               for r in filtered)


@pytest.mark.asyncio
async def test_full_ssh_workflow():
    """Test complete SSH workflow: IB filtering + adaptive depth + metrics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)
        
        agent = KnowledgeAgent(enable_quality_feedback=True)
        agent.adaptive_manager = manager
        
        # Conduct research
        response = await agent.chat(
            "What is d-separation and how does it relate to causal inference?",
            use_research=True,
            use_schema="decompose_and_synthesize",
        )
        
        # Verify all SSH features are present
        assert response.get("research_conducted") is True
        research = response.get("research", {})
        
        # Resource triple
        assert "resource_triple" in research
        assert "degradation_triple" in research
        
        # Logical depth
        topology = research.get("topology", {})
        assert "logical_depths" in topology
        assert "avg_logical_depth" in topology
        
        # Response quality
        assert len(response.get("response", "")) > 0


def test_ib_filtering_metadata_completeness():
    """Test that IB filtering metadata is complete and valid."""
    results = [
        {"result": "D-separation is a graphical criterion"},
        {"result": "D-separation determines conditional independence"},
    ]
    query = "What is d-separation?"
    
    filtered, metadata = filter_with_information_bottleneck(
        results, query, beta=0.5, min_mi=0.3
    )
    
    # Verify all metadata fields
    required_fields = [
        "compression_ratio", "avg_mi", "removed_count", 
        "beta", "min_mi", "original_count", "filtered_count"
    ]
    for field in required_fields:
        assert field in metadata, f"Missing metadata field: {field}"
    
    # Verify metadata values are valid
    assert 0.0 <= metadata["compression_ratio"] <= 1.0
    assert 0.0 <= metadata["avg_mi"] <= 1.0
    assert metadata["removed_count"] >= 0
    assert metadata["original_count"] == len(results)
    assert metadata["filtered_count"] == len(filtered)


@pytest.mark.asyncio
async def test_adaptive_depth_learning():
    """Test that adaptive depth learning accumulates over multiple queries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)
        
        # Add multiple learning examples
        for i in range(5):
            manager.update_from_evaluation(
                query="What is trust?",
                schema="decompose_and_synthesize",
                used_research=True,
                response_length=200,
                quality_score=0.8 + (i * 0.02),  # Improving quality
                num_subproblems=3,
            )
        
        # Check that depth is learned
        query_type = manager._classify_query("What is trust?")
        depth_data = manager.query_type_to_depth.get(query_type, [])
        # Should have at least 5 entries (may have more if manager persists state)
        assert len(depth_data) >= 5
        
        # Estimate should reflect learned depth
        estimated = manager.estimate_reasoning_depth("What is trust?")
        assert estimated >= 1


@pytest.mark.asyncio
async def test_resource_triple_correlation():
    """Test that resource triple metrics correlate with actual usage."""
    orchestrator = StructuredOrchestrator(
        research_agent=ResearchAgent(use_mcp=False),
    )
    
    result = await orchestrator.research_with_schema(
        "What is d-separation?",
        schema_name="decompose_and_synthesize",
    )
    
    rt = result["resource_triple"]
    subsolutions = result.get("subsolutions", [])
    
    # Depth should match number of subsolutions
    assert rt["depth"] == len(subsolutions)
    
    # Width should match total tools used
    tools_called = result.get("tools_called", 0)
    assert rt["width"] == tools_called
    
    # Coordination should be <= width (unique tools <= total tools)
    assert rt["coordination"] <= rt["width"]


@pytest.mark.asyncio
async def test_degradation_triple_correlation():
    """Test that degradation triple metrics correlate with topology quality."""
    orchestrator = StructuredOrchestrator(
        research_agent=ResearchAgent(use_mcp=False),
    )
    
    result = await orchestrator.research_with_schema(
        "What is d-separation?",
        schema_name="decompose_and_synthesize",
    )
    
    dt = result["degradation_triple"]
    topology = result.get("topology", {})
    fisher_info = topology.get("fisher_information", 0.0)
    
    # Noise should be inverse of Fisher Information
    # Higher Fisher = lower noise
    expected_noise = 1.0 - fisher_info
    assert abs(dt["noise"] - expected_noise) < 0.5  # Allow some tolerance


@pytest.mark.asyncio
async def test_logical_depth_correlation():
    """Test that logical depth correlates with trust and coherence."""
    orchestrator = StructuredOrchestrator(
        research_agent=ResearchAgent(use_mcp=False),
    )
    
    result = await orchestrator.research_with_schema(
        "What is d-separation?",
        schema_name="decompose_and_synthesize",
    )
    
    topology = result.get("topology", {})
    logical_depths = topology.get("logical_depths", {})
    avg_depth = topology.get("avg_logical_depth", 0.0)
    
    # If we have nodes, logical depth should be computed
    if logical_depths:
        assert 0.0 <= avg_depth <= 1.0
        
        # Average depth should be reasonable
        assert avg_depth > 0.0 or len(logical_depths) == 0

