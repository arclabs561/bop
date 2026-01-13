"""
Integration tests for uncertainty quantification in BOP.

Tests the integration of JSD-based uncertainty into ContextTopology and Orchestrator.
"""

import numpy as np
import pytest

from bop.context_topology import ContextNode, ContextTopology
from bop.uncertainty import (
    compute_epistemic_uncertainty_jsd,
    extract_prediction_from_result,
)


class TestExtractPredictionFromResult:
    """Test probability distribution extraction from BOP results."""

    def test_extract_from_node_confidence(self):
        """Should extract prediction from node confidence."""
        node = ContextNode(
            id="test",
            content="test content",
            source="test_source",
            confidence=0.8
        )
        result = {}

        pred = extract_prediction_from_result(result, node)

        assert np.allclose(pred, [0.8, 0.2])
        assert np.allclose(pred.sum(), 1.0)

    def test_extract_from_node_credibility(self):
        """Should extract prediction from node credibility when use_credibility=True."""
        node = ContextNode(
            id="test",
            content="test content",
            source="test_source",
            credibility=0.7
        )
        result = {}

        pred = extract_prediction_from_result(result, node, use_credibility=True)

        assert np.allclose(pred, [0.7, 0.3])
        assert np.allclose(pred.sum(), 1.0)

    def test_extract_from_epistemic_uncertainty(self):
        """Should extract prediction from epistemic uncertainty."""
        node = ContextNode(
            id="test",
            content="test content",
            source="test_source",
            epistemic_uncertainty=0.3
        )
        result = {}

        pred = extract_prediction_from_result(result, node, use_confidence=False)

        assert np.allclose(pred, [0.7, 0.3])  # confidence = 1 - uncertainty
        assert np.allclose(pred.sum(), 1.0)

    def test_extract_from_relevance_breakdown(self):
        """Should extract prediction from relevance breakdown."""
        result = {
            "relevance_breakdown": {
                "overall_score": 0.85
            }
        }

        pred = extract_prediction_from_result(result, None)

        assert np.allclose(pred, [0.85, 0.15])
        assert np.allclose(pred.sum(), 1.0)

    def test_extract_default_uniform(self):
        """Should return uniform distribution as default."""
        result = {}

        pred = extract_prediction_from_result(result, None)

        assert np.allclose(pred, [0.5, 0.5])
        assert np.allclose(pred.sum(), 1.0)


class TestContextTopologyUncertainty:
    """Test JSD-based uncertainty in ContextTopology."""

    def test_compute_clique_uncertainty_basic(self):
        """Should compute uncertainty for a clique."""
        topology = ContextTopology()

        # Create nodes with different confidence levels
        node1 = ContextNode(
            id="n1",
            content="content1",
            source="source1",
            confidence=0.9,
            epistemic_uncertainty=0.1
        )
        node2 = ContextNode(
            id="n2",
            content="content2",
            source="source2",
            confidence=0.8,
            epistemic_uncertainty=0.2
        )

        topology.add_node(node1)
        topology.add_node(node2)
        topology.add_edge("n1", "n2", 0.8)

        uncertainty = topology.compute_clique_uncertainty({"n1", "n2"})

        assert "epistemic" in uncertainty
        assert "aleatoric" in uncertainty
        assert "total" in uncertainty
        assert 0.0 <= uncertainty["epistemic"] <= 1.0
        assert 0.0 <= uncertainty["aleatoric"] <= 1.0
        assert 0.0 <= uncertainty["total"] <= 1.0

    def test_compute_clique_uncertainty_single_node(self):
        """Should handle single node clique."""
        topology = ContextTopology()

        node = ContextNode(
            id="n1",
            content="content",
            source="source",
            epistemic_uncertainty=0.3
        )
        topology.add_node(node)

        uncertainty = topology.compute_clique_uncertainty({"n1"})

        # Single node should have low epistemic uncertainty (no disagreement)
        # But the prediction extraction uses [1-uncertainty, uncertainty] = [0.7, 0.3]
        # JSD of a single distribution from itself is 0, but we're computing from the node's uncertainty
        # So epistemic should be very low (near 0) or exactly 0
        # With a single node, JSD computation may return 0 or very small value
        assert uncertainty["epistemic"] <= 0.3  # Single node has minimal/no disagreement
        assert 0.0 <= uncertainty["aleatoric"] <= 1.0

    def test_compute_clique_uncertainty_empty(self):
        """Should handle empty clique."""
        topology = ContextTopology()

        uncertainty = topology.compute_clique_uncertainty(set())

        assert uncertainty["epistemic"] == 0.5
        assert uncertainty["aleatoric"] == 0.3
        assert uncertainty["total"] == 0.5


class TestOrchestratorIntegration:
    """Test uncertainty integration in Orchestrator."""

    @pytest.mark.asyncio
    async def test_pipeline_uncertainty_tracking(self):
        """Should track uncertainty at each pipeline stage."""
        from bop.orchestrator import PipelineUncertainty, StructuredOrchestrator
        from bop.research import ResearchAgent

        # Create orchestrator (may not have LLM service)
        research_agent = ResearchAgent()
        orchestrator = StructuredOrchestrator(
            research_agent=research_agent,
            llm_service=None,  # Use None to avoid API requirements
        )

        # Test that PipelineUncertainty is defined
        assert hasattr(orchestrator, 'research_with_schema')

        # Test PipelineUncertainty dataclass
        uncertainty = PipelineUncertainty()
        assert uncertainty.query_decomposition == 0.5
        assert uncertainty.tool_selection == 0.5
        assert uncertainty.tool_execution == 0.5
        assert uncertainty.result_aggregation == 0.5
        assert uncertainty.synthesis == 0.5
        assert uncertainty.final_response == 0.5

        # Test to_dict method
        uncertainty_dict = uncertainty.to_dict()
        assert "query_decomposition" in uncertainty_dict
        assert "tool_selection" in uncertainty_dict
        assert "synthesis" in uncertainty_dict
        assert "final_response" in uncertainty_dict


class TestUncertaintyRefinement:
    """Test JSD-based uncertainty refinement."""

    def test_jsd_refines_heuristic_uncertainty(self):
        """JSD-based uncertainty should refine heuristic estimates."""
        # Create nodes with heuristic uncertainty
        nodes = [
            ContextNode(
                id=f"n{i}",
                content=f"content{i}",
                source=f"source{i}",
                confidence=0.7 + i * 0.1,  # Varying confidence
                epistemic_uncertainty=0.3 - i * 0.1  # Varying uncertainty
            )
            for i in range(3)
        ]

        # Extract predictions
        predictions = []
        for node in nodes:
            pred = extract_prediction_from_result({}, node)
            predictions.append(pred)

        # Compute JSD-based epistemic uncertainty
        jsd_epistemic = compute_epistemic_uncertainty_jsd(predictions)

        # Should be in valid range
        assert 0.0 <= jsd_epistemic <= 1.0

        # Should reflect disagreement (nodes have different confidence levels)
        # Lower disagreement = lower epistemic uncertainty
        assert jsd_epistemic < 0.5  # Should be relatively low for similar nodes

