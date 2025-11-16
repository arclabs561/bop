"""Evaluation tests using SSH-specific dataset."""

import pytest
from pathlib import Path
import json

from bop.agent import KnowledgeAgent
from bop.orchestrator import StructuredOrchestrator
from bop.research import ResearchAgent
from bop.adaptive_quality import AdaptiveQualityManager
from bop.quality_feedback import QualityFeedbackLoop
import tempfile


@pytest.fixture
def ssh_dataset():
    """Load SSH evaluation dataset."""
    dataset_path = Path(__file__).parent.parent / "datasets" / "ssh_evaluation_dataset.json"
    if not dataset_path.exists():
        pytest.skip(f"SSH dataset not found: {dataset_path}")
    
    with open(dataset_path, 'r') as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_ssh_dataset_ib_filtering(ssh_dataset):
    """Test IB filtering on SSH evaluation dataset."""
    agent = KnowledgeAgent(enable_quality_feedback=True)
    
    for item in ssh_dataset[:3]:  # Test first 3 queries
        query = item["query"]
        expected_compression = item.get("expected_ib_compression", 0.5)
        
        response = await agent.chat(
            query,
            use_research=item.get("requires_research", True),
            use_schema="decompose_and_synthesize",
        )
        
        # Verify research was conducted if required
        if item.get("requires_research"):
            assert response.get("research_conducted") is True
        
        # Verify response quality
        assert len(response.get("response", "")) > 0


@pytest.mark.asyncio
async def test_ssh_dataset_adaptive_depth(ssh_dataset):
    """Test adaptive reasoning depth on SSH evaluation dataset."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)
        
        agent = KnowledgeAgent(enable_quality_feedback=True)
        agent.adaptive_manager = manager
        
        # Test queries and learn depth
        for item in ssh_dataset[:5]:
            query = item["query"]
            expected_depth = item.get("expected_depth", 3)
            
            # Get strategy
            strategy = manager.get_adaptive_strategy(query)
            
            # Verify reasoning depth is set
            assert strategy.reasoning_depth >= 1
            
            # After learning, depth should approach expected
            manager.update_from_evaluation(
                query=query,
                schema="decompose_and_synthesize",
                used_research=item.get("requires_research", True),
                response_length=200,
                quality_score=0.8,
                num_subproblems=expected_depth,
            )


@pytest.mark.asyncio
async def test_ssh_dataset_resource_triple(ssh_dataset):
    """Test resource triple tracking on SSH evaluation dataset."""
    orchestrator = StructuredOrchestrator(
        research_agent=ResearchAgent(use_mcp=False),
    )
    
    for item in ssh_dataset[:3]:
        query = item["query"]
        
        result = await orchestrator.research_with_schema(
            query,
            schema_name="decompose_and_synthesize",
        )
        
        # Verify resource triple exists
        assert "resource_triple" in result
        rt = result["resource_triple"]
        
        # Verify metrics are valid
        assert rt["depth"] >= 0
        assert rt["width"] >= 0
        assert rt["coordination"] >= 0
        assert rt["coordination"] <= rt["width"]  # Invariant
        
        # Verify degradation triple exists
        assert "degradation_triple" in result
        dt = result["degradation_triple"]
        
        assert 0.0 <= dt["noise"] <= 1.0
        assert 0.0 <= dt["loss"] <= 1.0
        assert 0.0 <= dt["waste"] <= 1.0


@pytest.mark.asyncio
async def test_ssh_dataset_logical_depth(ssh_dataset):
    """Test logical depth computation on SSH evaluation dataset."""
    orchestrator = StructuredOrchestrator(
        research_agent=ResearchAgent(use_mcp=False),
    )
    
    for item in ssh_dataset[:3]:
        query = item["query"]
        
        result = await orchestrator.research_with_schema(
            query,
            schema_name="decompose_and_synthesize",
        )
        
        # Verify logical depth in topology
        topology = result.get("topology", {})
        assert "logical_depths" in topology
        assert "avg_logical_depth" in topology
        
        avg_depth = topology["avg_logical_depth"]
        assert 0.0 <= avg_depth <= 1.0


@pytest.mark.asyncio
async def test_ssh_dataset_early_stopping(ssh_dataset):
    """Test early stopping on SSH evaluation dataset."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)
        
        # Learn from simple queries
        simple_queries = [item for item in ssh_dataset if item.get("expected_early_stop")]
        
        for item in simple_queries[:2]:
            manager.update_from_evaluation(
                query=item["query"],
                schema="decompose_and_synthesize",
                used_research=item.get("requires_research", False),
                response_length=150,
                quality_score=0.85,
                num_subproblems=item.get("expected_depth", 2),
            )
        
        orchestrator = StructuredOrchestrator(
            research_agent=ResearchAgent(use_mcp=False),
        )
        
        # Test early stopping on learned queries
        for item in simple_queries[:2]:
            result = await orchestrator.research_with_schema(
                item["query"],
                schema_name="decompose_and_synthesize",
                adaptive_manager=manager,
            )
            
            # Should have completed (may or may not stop early)
            assert "subsolutions" in result
            assert len(result["subsolutions"]) >= 1


@pytest.mark.asyncio
async def test_ssh_dataset_full_workflow(ssh_dataset):
    """Test complete SSH workflow on evaluation dataset."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)
        
        agent = KnowledgeAgent(enable_quality_feedback=True)
        agent.adaptive_manager = manager
        
        # Test on a complex query
        complex_query = next(
            item for item in ssh_dataset 
            if item.get("complexity") == "complex"
        )
        
        response = await agent.chat(
            complex_query["query"],
            use_research=True,
            use_schema="decompose_and_synthesize",
        )
        
        # Verify all SSH features
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

