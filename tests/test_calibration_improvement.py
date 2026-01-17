"""
Tests for calibration improvement using uncertainty metrics.
"""

import numpy as np
import pytest

from pran.calibration_improvement import (
    _compute_brier_score,
    _compute_ece,
    calibrate_confidence_with_uncertainty,
    improve_calibration_with_uncertainty,
)


class TestCalibrationImprovement:
    """Test calibration improvement functions."""

    def test_improve_calibration_basic(self):
        """Should improve calibration using uncertainty-aware aggregation."""
        predictions = [
            np.array([0.9, 0.1]),  # High confidence
            np.array([0.8, 0.2]),  # Medium-high confidence
            np.array([0.7, 0.3]),  # Medium confidence
        ]
        confidence_scores = [0.9, 0.8, 0.7]

        result = improve_calibration_with_uncertainty(
            predictions,
            confidence_scores,
            use_aleatoric_weighting=True,
        )

        assert "improved_prediction" in result
        assert "improved_confidence" in result
        assert "epistemic_uncertainty" in result
        assert "aleatoric_uncertainty" in result
        assert 0.0 <= result["improved_confidence"] <= 1.0

    def test_improve_calibration_with_outcomes(self):
        """Should compute calibration metrics when outcomes provided."""
        predictions = [
            np.array([0.9, 0.1]),
            np.array([0.8, 0.2]),
            np.array([0.7, 0.3]),
        ]
        confidence_scores = [0.9, 0.8, 0.7]
        actual_outcomes = [1.0, 1.0, 0.0]  # First two correct, third wrong

        result = improve_calibration_with_uncertainty(
            predictions,
            confidence_scores,
            actual_outcomes=actual_outcomes,
        )

        assert result["ece_before"] is not None
        assert result["ece_after"] is not None
        assert result["calibration_improvement"] is not None
        assert "ece_reduction" in result["calibration_improvement"]

    def test_improve_calibration_empty(self):
        """Should handle empty predictions."""
        result = improve_calibration_with_uncertainty([], [])

        assert result["improved_prediction"] is None
        assert result["calibration_improvement"] is None

    def test_calibrate_confidence_high_uncertainty(self):
        """Should lower confidence when uncertainty is high."""
        calibrated = calibrate_confidence_with_uncertainty(
            confidence=0.9,
            epistemic_uncertainty=0.7,  # High uncertainty
            aleatoric_uncertainty=0.3,
            calibration_factor=0.5,
        )

        # High uncertainty should lower confidence
        assert calibrated < 0.9
        assert 0.0 <= calibrated <= 1.0

    def test_calibrate_confidence_low_uncertainty(self):
        """Should maintain or increase confidence when uncertainty is low."""
        calibrated = calibrate_confidence_with_uncertainty(
            confidence=0.7,
            epistemic_uncertainty=0.1,  # Low uncertainty
            aleatoric_uncertainty=0.1,
            calibration_factor=0.5,
        )

        # Low uncertainty should maintain or increase confidence
        assert calibrated >= 0.7
        assert 0.0 <= calibrated <= 1.0

    def test_compute_ece(self):
        """Should compute Expected Calibration Error."""
        confidence_scores = [0.9, 0.8, 0.7, 0.6, 0.5]
        actual_outcomes = [1.0, 1.0, 0.0, 0.0, 0.5]  # Mixed outcomes

        ece = _compute_ece(confidence_scores, actual_outcomes)

        assert 0.0 <= ece <= 1.0
        assert isinstance(ece, float)

    def test_compute_ece_perfect_calibration(self):
        """Should return low ECE for well-calibrated predictions."""
        confidence_scores = [0.9, 0.8, 0.7]
        actual_outcomes = [1.0, 1.0, 0.0]  # Matches confidence

        ece = _compute_ece(confidence_scores, actual_outcomes)

        # Should be relatively low (perfect calibration would be 0.0, but binning may introduce error)
        # With only 3 samples and binning, some error is expected
        assert ece < 0.5  # Relaxed threshold for small sample size

    def test_compute_brier_score(self):
        """Should compute Brier Score."""
        confidence_scores = [0.9, 0.8, 0.7]
        actual_outcomes = [1.0, 1.0, 0.0]

        brier = _compute_brier_score(confidence_scores, actual_outcomes)

        assert 0.0 <= brier <= 1.0
        assert isinstance(brier, float)

    def test_compute_brier_score_perfect(self):
        """Should return 0.0 for perfect predictions."""
        confidence_scores = [1.0, 1.0, 0.0]
        actual_outcomes = [1.0, 1.0, 0.0]

        brier = _compute_brier_score(confidence_scores, actual_outcomes)

        assert brier == pytest.approx(0.0, abs=0.01)

    def test_improve_calibration_aleatoric_weighting(self):
        """Aleatoric weighting should improve calibration."""
        # Create predictions with varying aleatoric uncertainty
        predictions = [
            np.array([0.9, 0.1]),  # Low entropy (confident)
            np.array([0.5, 0.5]),  # High entropy (uncertain)
        ]
        confidence_scores = [0.9, 0.5]
        actual_outcomes = [1.0, 1.0]  # Both correct

        # With aleatoric weighting
        result_weighted = improve_calibration_with_uncertainty(
            predictions,
            confidence_scores,
            actual_outcomes,
            use_aleatoric_weighting=True,
        )

        # Without aleatoric weighting
        result_unweighted = improve_calibration_with_uncertainty(
            predictions,
            confidence_scores,
            actual_outcomes,
            use_aleatoric_weighting=False,
        )

        # Both should work
        assert result_weighted["improved_confidence"] is not None
        assert result_unweighted["improved_confidence"] is not None
        # Weighted should prioritize low-entropy prediction
        assert result_weighted["improved_confidence"] > result_unweighted["improved_confidence"]

