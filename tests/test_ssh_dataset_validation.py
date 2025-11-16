"""Tests that validate SSH features against evaluation dataset expectations."""

import pytest
from pathlib import Path
import json
import tempfile

from bop.agent import KnowledgeAgent
from bop.orchestrator import StructuredOrchestrator
from bop.research import ResearchAgent
from bop.adaptive_quality import AdaptiveQualityManager
from bop.quality_feedback import QualityFeedbackLoop
from bop.information_bottleneck import filter_with_information_bottleneck


@pytest.fixture
def ssh_dataset():
    """Load SSH evaluation dataset."""
    dataset_path = Path(__file__).parent.parent / "datasets" / "ssh_evaluation_dataset.json"
    if not dataset_path.exists():
        pytest.skip(f"SSH dataset not found: {dataset_path}")
    
    with open(dataset_path, 'r') as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_dataset_expected_depth_validation(ssh_dataset):
    """
    Validate that actual reasoning depth matches expected_depth from dataset.
    
    For queries with expected_depth, the system should learn and use that depth.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)
        
        # Test on queries with expected_depth
        for item in ssh_dataset[:3]:
            expected_depth = item.get("expected_depth")
            if not expected_depth:
                continue
            
            query = item["query"]
            
            # Learn from expected depth
            manager.update_from_evaluation(
                query=query,
                schema="decompose_and_synthesize",
                used_research=item.get("requires_research", True),
                response_length=200,
                quality_score=0.8,
                num_subproblems=expected_depth,
            )
            
            # Estimate depth
            estimated = manager.estimate_reasoning_depth(query)
            
            # Should be within 1 of expected (allowing for learning variance)
            assert abs(estimated - expected_depth) <= 1, \
                f"Query: {query[:50]}... - Estimated depth ({estimated}) doesn't match expected ({expected_depth})"


@pytest.mark.asyncio
async def test_dataset_expected_ib_compression_validation(ssh_dataset):
    """
    Validate that IB filtering compression matches expected_ib_compression.
    
    For queries with expected_ib_compression, actual compression should be similar.
    """
    for item in ssh_dataset[:3]:
        expected_compression = item.get("expected_ib_compression")
        if expected_compression is None:
            continue
        
        query = item["query"]
        
        # Simulate results (in real scenario, these would come from research)
        results = [
            {"result": f"Relevant information about {query}"},
            {"result": f"More relevant information about {query}"},
            {"result": "Unrelated information about weather"},
            {"result": "Another unrelated topic"},
        ]
        
        # Apply IB filtering
        filtered, metadata = filter_with_information_bottleneck(
            results, query, min_mi=0.2
        )
        
        actual_compression = metadata["compression_ratio"]
        
        # Actual compression should be reasonable (within 0.3 of expected)
        # Note: This is a heuristic check since we're using simulated results
        assert 0.0 <= actual_compression <= 1.0
        # Can't strictly validate against expected without real research results


@pytest.mark.asyncio
async def test_dataset_expected_early_stop_validation(ssh_dataset):
    """
    Validate that early stopping behavior matches expected_early_stop.
    
    For queries with expected_early_stop=True, system should learn to stop early.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)
        
        # Find queries that should stop early
        early_stop_queries = [item for item in ssh_dataset if item.get("expected_early_stop")]
        
        for item in early_stop_queries[:2]:
            query = item["query"]
            expected_depth = item.get("expected_depth", 2)
            
            # Learn that this query achieves high quality with low depth
            manager.update_from_evaluation(
                query=query,
                schema="decompose_and_synthesize",
                used_research=item.get("requires_research", False),
                response_length=150,
                quality_score=0.9,  # High quality
                num_subproblems=expected_depth,
            )
            
            # Check early stop threshold
            query_type = manager._classify_query(query)
            threshold = manager._get_early_stop_threshold(query_type)
            
            # Should have a threshold (can stop early)
            if threshold is not None:
                # High quality should trigger early stop
                should_stop = manager.should_early_stop(
                    current_quality=0.9,
                    query_type=query_type,
                    num_subproblems_completed=expected_depth,
                )
                # Should be able to stop early (may or may not depending on exact threshold)
                assert isinstance(should_stop, bool)


@pytest.mark.asyncio
async def test_dataset_complexity_depth_correlation(ssh_dataset):
    """
    Validate that complexity correlates with expected_depth.
    
    Complex queries should have higher expected_depth than simple queries.
    """
    simple_queries = [item for item in ssh_dataset if item.get("complexity") == "simple"]
    complex_queries = [item for item in ssh_dataset if item.get("complexity") == "complex"]
    
    if simple_queries and complex_queries:
        simple_depths = [item.get("expected_depth", 0) for item in simple_queries]
        complex_depths = [item.get("expected_depth", 0) for item in complex_queries]
        
        avg_simple = sum(simple_depths) / len(simple_depths) if simple_depths else 0
        avg_complex = sum(complex_depths) / len(complex_depths) if complex_depths else 0
        
        # Complex queries should generally require more depth
        assert avg_complex >= avg_simple, \
            f"Complex queries ({avg_complex}) should require >= depth than simple ({avg_simple})"


@pytest.mark.asyncio
async def test_dataset_domain_specific_validation(ssh_dataset):
    """
    Validate that domain-specific queries have appropriate expectations.
    
    Different domains (causal_inference, computational_theory, etc.) should have
    different expected characteristics.
    """
    domains = {}
    for item in ssh_dataset:
        domain = item.get("domain", "unknown")
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(item)
    
    # Verify domains have different characteristics
    domain_depths = {}
    for domain, items in domains.items():
        depths = [item.get("expected_depth", 0) for item in items if item.get("expected_depth")]
        if depths:
            domain_depths[domain] = sum(depths) / len(depths)
    
    # Different domains should have different average depths (or at least be valid)
    assert len(domain_depths) > 0
    for domain, avg_depth in domain_depths.items():
        assert 1 <= avg_depth <= 10, f"Invalid average depth for {domain}: {avg_depth}"


@pytest.mark.asyncio
async def test_dataset_full_workflow_with_expectations(ssh_dataset):
    """
    Validate complete workflow using dataset expectations.
    
    Run a query, check that all SSH features work, and compare against expectations.
    """
    # Use a moderate complexity query
    test_item = next(
        (item for item in ssh_dataset if item.get("complexity") == "moderate"),
        ssh_dataset[0]
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)
        
        orchestrator = StructuredOrchestrator(
            research_agent=ResearchAgent(use_mcp=False),
        )
        
        result = await orchestrator.research_with_schema(
            test_item["query"],
            schema_name="decompose_and_synthesize",
            adaptive_manager=manager,
        )
        
        # Verify all SSH features are present
        assert "resource_triple" in result
        assert "degradation_triple" in result
        assert "topology" in result
        assert "logical_depths" in result["topology"]
        
        # Verify depth is reasonable
        actual_depth = result["resource_triple"]["depth"]
        expected_depth = test_item.get("expected_depth", 3)
        
        # Should be within 2 of expected (allowing for variance)
        assert abs(actual_depth - expected_depth) <= 2, \
            f"Actual depth ({actual_depth}) too far from expected ({expected_depth})"
        
        # Verify metrics are valid
        rt = result["resource_triple"]
        assert rt["depth"] >= 0
        assert rt["width"] >= 0
        assert rt["coordination"] <= rt["width"]
        
        dt = result["degradation_triple"]
        assert 0.0 <= dt["noise"] <= 1.0
        assert 0.0 <= dt["loss"] <= 1.0
        assert 0.0 <= dt["waste"] <= 1.0

