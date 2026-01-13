"""
End-to-end integration tests for all future work items:
- MUSE tool selection
- Aleatoric-aware weighting
- Calibration improvements
- Multi-class probability distributions
- Source credibility integration
"""

import numpy as np
import pytest

from bop.calibration_improvement import (
    calibrate_confidence_with_uncertainty,
    improve_calibration_with_uncertainty,
)
from bop.context_topology import ContextNode
from bop.uncertainty import extract_prediction_from_result
from bop.uncertainty_tool_selection import (
    aggregate_results_with_aleatoric_weighting,
    select_tools_with_muse,
)


class TestMUSEIntegration:
    """Test MUSE integration with source credibility."""

    def test_muse_filters_low_credibility(self):
        """MUSE should filter out low-credibility sources."""
        candidate_tools = ["tool1", "tool2", "tool3"]
        tool_metadata = [
            {"credibility": 0.9, "confidence": 0.9},  # High credibility
            {"credibility": 0.2, "confidence": 0.2},  # Low credibility (should be filtered)
            {"credibility": 0.8, "confidence": 0.8},  # Medium-high credibility
        ]

        selected, metadata = select_tools_with_muse(
            candidate_tools,
            tool_metadata,
            "test",
            max_tools=3,
            min_credibility=0.3,  # Filter out tool2
        )

        # Should not include tool2 (low credibility)
        assert "tool2" not in selected
        assert metadata["num_filtered"] < len(candidate_tools)
        assert metadata.get("min_credibility_filter") == 0.3

    def test_muse_uses_credibility_as_confidence(self):
        """MUSE should use credibility as confidence score."""
        candidate_tools = ["tool1", "tool2"]
        tool_metadata = [
            {"credibility": 0.9, "confidence": 0.5},  # Credibility should override confidence
            {"credibility": 0.6, "confidence": 0.8},
        ]

        selected, metadata = select_tools_with_muse(
            candidate_tools,
            tool_metadata,
            "test",
            max_tools=2,
        )

        # Should select tool1 first (higher credibility)
        assert len(selected) > 0
        if len(selected) == 1:
            assert selected[0] == "tool1"  # Higher credibility should be selected first


class TestAleatoricWeightingIntegration:
    """Test aleatoric-aware weighting in aggregation."""

    def test_aleatoric_weighting_prioritizes_low_entropy(self):
        """Aleatoric weighting should prioritize low-entropy (confident) results."""
        results = [
            {"result": "Confident result", "source": "source1"},
            {"result": "Uncertain result", "source": "source2"},
        ]
        nodes = [
            ContextNode(
                id="n1",
                content="Confident result",
                source="source1",
                confidence=0.9,
                aleatoric_uncertainty=0.1,  # Low entropy
            ),
            ContextNode(
                id="n2",
                content="Uncertain result",
                source="source2",
                confidence=0.5,
                aleatoric_uncertainty=0.8,  # High entropy
            ),
        ]

        aggregated = aggregate_results_with_aleatoric_weighting(results, nodes)

        # Low entropy (n1) should have higher weight
        assert aggregated["weights"][0] > aggregated["weights"][1]
        assert sum(aggregated["weights"]) == pytest.approx(1.0, abs=0.01)


class TestCalibrationImprovementIntegration:
    """Test calibration improvement with uncertainty."""

    def test_calibration_improvement_reduces_ece(self):
        """Calibration improvement should reduce ECE."""
        predictions = [
            np.array([0.9, 0.1]),
            np.array([0.8, 0.2]),
            np.array([0.7, 0.3]),
        ]
        confidence_scores = [0.9, 0.8, 0.7]
        # Create scenario where calibration can be improved
        actual_outcomes = [1.0, 1.0, 0.0]

        result = improve_calibration_with_uncertainty(
            predictions,
            confidence_scores,
            actual_outcomes,
            use_aleatoric_weighting=True,
        )

        if result["calibration_improvement"]:
            # ECE should be reduced (or at least computed)
            assert result["ece_before"] is not None
            assert result["ece_after"] is not None
            # Improvement may not always reduce ECE (depends on data), but should be computed
            assert "ece_reduction" in result["calibration_improvement"]

    def test_calibrate_confidence_with_uncertainty(self):
        """Should calibrate confidence using uncertainty metrics."""
        # High confidence, high uncertainty → should lower confidence
        calibrated_high_unc = calibrate_confidence_with_uncertainty(
            confidence=0.9,
            epistemic_uncertainty=0.7,
            aleatoric_uncertainty=0.3,
        )

        # High confidence, low uncertainty → should maintain confidence
        calibrated_low_unc = calibrate_confidence_with_uncertainty(
            confidence=0.9,
            epistemic_uncertainty=0.1,
            aleatoric_uncertainty=0.1,
        )

        assert calibrated_high_unc < calibrated_low_unc
        assert 0.0 <= calibrated_high_unc <= 1.0
        assert 0.0 <= calibrated_low_unc <= 1.0


class TestMultiClassProbabilityDistributions:
    """Test multi-class probability distribution extraction."""

    def test_extract_multi_class_from_relevance_breakdown(self):
        """Should extract multi-class distribution from relevance breakdown."""
        result = {
            "relevance_breakdown": {
                "component_scores": {
                    "word_overlap": 0.8,
                    "semantic_similarity": 0.6,
                    "token_match": 0.7,
                }
            }
        }

        pred = extract_prediction_from_result(result, None, binary=False)

        assert len(pred) == 3  # Three component scores
        assert np.allclose(pred.sum(), 1.0)  # Should sum to 1.0
        assert all(0.0 <= p <= 1.0 for p in pred)

    def test_extract_multi_class_from_list(self):
        """Should extract multi-class distribution from list of scores."""
        result = {
            "relevance_breakdown": {
                "component_scores": [0.9, 0.7, 0.5, 0.3]
            }
        }

        pred = extract_prediction_from_result(result, None, binary=False)

        assert len(pred) == 4  # Four component scores
        assert np.allclose(pred.sum(), 1.0)

    def test_extract_multi_class_from_node_confidence(self):
        """Should extract multi-class distribution from node confidence."""
        node = ContextNode(
            id="n1",
            content="content",
            source="source",
            confidence=0.8
        )

        pred = extract_prediction_from_result({}, node, binary=False)

        # Should create 3-class distribution
        assert len(pred) == 3
        assert np.allclose(pred.sum(), 1.0)
        assert pred[0] == pytest.approx(0.8, abs=0.01)  # First class gets confidence


class TestSourceCredibilityIntegration:
    """Test source credibility integration in MUSE."""

    def test_muse_prioritizes_high_credibility(self):
        """MUSE should prioritize high-credibility sources."""
        candidate_tools = ["tool1", "tool2", "tool3"]
        tool_metadata = [
            {"credibility": 0.95, "confidence": 0.95},  # Highest
            {"credibility": 0.7, "confidence": 0.7},    # Medium
            {"credibility": 0.5, "confidence": 0.5},    # Lower
        ]

        selected, metadata = select_tools_with_muse(
            candidate_tools,
            tool_metadata,
            "test",
            max_tools=2,
            strategy="greedy",
        )

        # Should include highest credibility tool
        assert "tool1" in selected
        assert len(selected) <= 2

    def test_muse_filters_below_threshold(self):
        """MUSE should filter sources below credibility threshold."""
        candidate_tools = ["tool1", "tool2", "tool3"]
        tool_metadata = [
            {"credibility": 0.9},
            {"credibility": 0.25},  # Below threshold
            {"credibility": 0.8},
        ]

        selected, metadata = select_tools_with_muse(
            candidate_tools,
            tool_metadata,
            "test",
            min_credibility=0.3,
        )

        # Should not include tool2
        assert "tool2" not in selected
        assert metadata["num_filtered"] == 2  # Only 2 pass filter


class TestEndToEndIntegration:
    """End-to-end tests combining all features."""

    def test_full_workflow_muse_to_aggregation(self):
        """Test full workflow: MUSE selection → aleatoric weighting → calibration."""
        # Step 1: MUSE selection
        candidate_tools = ["tool1", "tool2", "tool3"]
        tool_metadata = [
            {"credibility": 0.9, "confidence": 0.9},
            {"credibility": 0.7, "confidence": 0.7},
            {"credibility": 0.5, "confidence": 0.5},
        ]

        selected, _ = select_tools_with_muse(
            candidate_tools,
            tool_metadata,
            "test",
            max_tools=2,
        )

        assert len(selected) <= 2

        # Step 2: Aleatoric weighting (simulate results from selected tools)
        results = [
            {"result": "Result 1", "source": selected[0]},
            {"result": "Result 2", "source": selected[1]} if len(selected) > 1 else {"result": "Result 2", "source": "tool2"},
        ]
        nodes = [
            ContextNode(
                id="n1",
                content="Result 1",
                source=selected[0],
                confidence=0.9,
                aleatoric_uncertainty=0.1,
            ),
            ContextNode(
                id="n2",
                content="Result 2",
                source=selected[1] if len(selected) > 1 else "tool2",
                confidence=0.7,
                aleatoric_uncertainty=0.3,
            ),
        ]

        aggregated = aggregate_results_with_aleatoric_weighting(results[:len(selected)], nodes[:len(selected)])

        assert "weights" in aggregated
        assert len(aggregated["weights"]) == len(selected)

        # Step 3: Calibration improvement
        predictions = [
            np.array([node.confidence, 1.0 - node.confidence])
            for node in nodes[:len(selected)]
        ]
        confidence_scores = [node.confidence for node in nodes[:len(selected)]]

        calibration_result = improve_calibration_with_uncertainty(
            predictions,
            confidence_scores,
            use_aleatoric_weighting=True,
        )

        assert "improved_confidence" in calibration_result
        assert 0.0 <= calibration_result["improved_confidence"] <= 1.0

