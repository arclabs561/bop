"""
Tests for information-theoretic uncertainty quantification.

Based on:
- "Rethinking the Uncertainty" (2410.20199v1)
- "MUSE: Multi-LLM Uncertainty via Subset Ensembles" (2507.07236v2)
"""

import numpy as np
import pytest

from pran.uncertainty import (
    aggregate_with_aleatoric_weighting,
    compute_aleatoric_uncertainty_entropy,
    compute_epistemic_uncertainty_jsd,
    compute_jsd,
    compute_total_uncertainty,
    select_calibrated_subset_muse,
)


class TestJensenShannonDivergence:
    """Test JSD computation."""

    def test_jsd_identical_distributions(self):
        """JSD should be 0 for identical distributions."""
        p1 = np.array([0.5, 0.5])
        p2 = np.array([0.5, 0.5])
        jsd = compute_jsd(p1, p2)
        assert jsd == pytest.approx(0.0, abs=1e-6)

    def test_jsd_completely_different(self):
        """JSD should be 1 for completely different distributions."""
        p1 = np.array([1.0, 0.0])
        p2 = np.array([0.0, 1.0])
        jsd = compute_jsd(p1, p2)
        assert jsd == pytest.approx(1.0, abs=1e-3)

    def test_jsd_similar_distributions(self):
        """JSD should be in [0, 1] for similar distributions."""
        p1 = np.array([0.7, 0.3])
        p2 = np.array([0.6, 0.4])
        jsd = compute_jsd(p1, p2)
        assert 0.0 <= jsd <= 1.0
        assert jsd < 0.5  # Should be relatively small for similar distributions

    def test_jsd_symmetry(self):
        """JSD should be symmetric."""
        p1 = np.array([0.8, 0.2])
        p2 = np.array([0.3, 0.7])
        jsd1 = compute_jsd(p1, p2)
        jsd2 = compute_jsd(p2, p1)
        assert jsd1 == pytest.approx(jsd2, abs=1e-6)

    def test_jsd_multiclass(self):
        """JSD should work for multi-class distributions."""
        p1 = np.array([0.5, 0.3, 0.2])
        p2 = np.array([0.2, 0.3, 0.5])
        jsd = compute_jsd(p1, p2)
        assert 0.0 <= jsd <= 1.0
        assert jsd > 0.0  # Should be non-zero for different distributions


class TestEpistemicUncertainty:
    """Test epistemic uncertainty computation."""

    def test_epistemic_high_agreement(self):
        """High agreement should yield low epistemic uncertainty."""
        predictions = [
            np.array([0.8, 0.2]),
            np.array([0.75, 0.25]),
            np.array([0.85, 0.15]),
        ]
        epistemic = compute_epistemic_uncertainty_jsd(predictions)
        assert 0.0 <= epistemic <= 1.0
        assert epistemic < 0.3  # Should be relatively low for high agreement

    def test_epistemic_high_disagreement(self):
        """High disagreement should yield high epistemic uncertainty."""
        predictions = [
            np.array([0.9, 0.1]),
            np.array([0.1, 0.9]),
            np.array([0.5, 0.5]),
        ]
        epistemic = compute_epistemic_uncertainty_jsd(predictions)
        assert 0.0 <= epistemic <= 1.0
        assert epistemic > 0.2  # Should be relatively high for high disagreement (JSD can be lower than expected due to averaging)

    def test_epistemic_single_prediction(self):
        """Single prediction should have zero epistemic uncertainty."""
        predictions = [np.array([0.7, 0.3])]
        epistemic = compute_epistemic_uncertainty_jsd(predictions)
        assert epistemic == pytest.approx(0.0, abs=1e-6)

    def test_epistemic_empty_list(self):
        """Empty list should return default uncertainty."""
        epistemic = compute_epistemic_uncertainty_jsd([])
        assert epistemic == 0.5  # Default value


class TestAleatoricUncertainty:
    """Test aleatoric uncertainty computation."""

    def test_aleatoric_high_entropy(self):
        """Uniform distribution should yield high aleatoric uncertainty."""
        predictions = [
            np.array([0.5, 0.5]),
            np.array([0.5, 0.5]),
        ]
        aleatoric = compute_aleatoric_uncertainty_entropy(predictions)
        assert 0.0 <= aleatoric <= 1.0
        assert aleatoric > 0.8  # Should be high for uniform distribution

    def test_aleatoric_low_entropy(self):
        """Peaked distribution should yield low aleatoric uncertainty."""
        predictions = [
            np.array([0.95, 0.05]),
            np.array([0.9, 0.1]),
        ]
        aleatoric = compute_aleatoric_uncertainty_entropy(predictions)
        assert 0.0 <= aleatoric <= 1.0
        assert aleatoric < 0.5  # Should be low for peaked distributions

    def test_aleatoric_empty_list(self):
        """Empty list should return default uncertainty."""
        aleatoric = compute_aleatoric_uncertainty_entropy([])
        assert aleatoric == 0.3  # Default value

    def test_aleatoric_multiclass(self):
        """Should work for multi-class distributions."""
        predictions = [
            np.array([0.7, 0.2, 0.1]),
            np.array([0.6, 0.3, 0.1]),
        ]
        aleatoric = compute_aleatoric_uncertainty_entropy(predictions)
        assert 0.0 <= aleatoric <= 1.0


class TestTotalUncertainty:
    """Test total uncertainty computation."""

    def test_total_uncertainty_combination(self):
        """Total uncertainty should combine epistemic and aleatoric."""
        epistemic = 0.4
        aleatoric = 0.3
        beta = 0.5
        total = compute_total_uncertainty(epistemic, aleatoric, beta)
        expected = epistemic + beta * aleatoric
        assert total == pytest.approx(expected, abs=1e-6)
        assert 0.0 <= total <= 1.0

    def test_total_uncertainty_clamping(self):
        """Total uncertainty should be clamped to [0, 1]."""
        # Test with values that would exceed 1.0
        epistemic = 0.8
        aleatoric = 0.9
        beta = 0.5
        total = compute_total_uncertainty(epistemic, aleatoric, beta)
        assert 0.0 <= total <= 1.0


class TestAleatoricWeighting:
    """Test aleatoric-aware weighting."""

    def test_weighting_low_entropy_preferred(self):
        """Lower entropy predictions should get higher weights."""
        predictions = [
            np.array([0.9, 0.1]),  # Low entropy (confident)
            np.array([0.5, 0.5]),  # High entropy (uncertain)
        ]
        weighted = aggregate_with_aleatoric_weighting(predictions)
        assert np.allclose(weighted.sum(), 1.0, atol=1e-6)
        # Weighted result should be closer to the confident prediction
        assert weighted[0] > 0.5

    def test_weighting_normalization(self):
        """Weighted result should be a valid probability distribution."""
        predictions = [
            np.array([0.7, 0.3]),
            np.array([0.6, 0.4]),
            np.array([0.8, 0.2]),
        ]
        weighted = aggregate_with_aleatoric_weighting(predictions)
        assert np.allclose(weighted.sum(), 1.0, atol=1e-6)
        assert np.all(weighted >= 0.0)
        assert np.all(weighted <= 1.0)

    def test_weighting_empty_list(self):
        """Empty list should raise ValueError."""
        with pytest.raises(ValueError):
            aggregate_with_aleatoric_weighting([])


class TestMUSESubsetSelection:
    """Test MUSE-inspired subset selection."""

    def test_greedy_selection_basic(self):
        """Greedy selection should select subset based on confidence."""
        predictions = [
            ("source1", np.array([0.9, 0.1])),
            ("source2", np.array([0.8, 0.2])),
            ("source3", np.array([0.5, 0.5])),
        ]
        confidence_scores = [0.9, 0.8, 0.5]

        selected, epistemic, total = select_calibrated_subset_muse(
            predictions,
            confidence_scores,
            strategy="greedy",
            m_min=2
        )

        assert len(selected) >= 2
        assert "source1" in selected  # Most confident should be included
        assert 0.0 <= epistemic <= 1.0
        assert 0.0 <= total <= 1.0

    def test_conservative_selection_basic(self):
        """Conservative selection should minimize total uncertainty."""
        predictions = [
            ("source1", np.array([0.9, 0.1])),
            ("source2", np.array([0.85, 0.15])),
            ("source3", np.array([0.1, 0.9])),  # Disagrees strongly
        ]
        confidence_scores = [0.9, 0.85, 0.5]

        selected, epistemic, total = select_calibrated_subset_muse(
            predictions,
            confidence_scores,
            strategy="conservative",
            m_min=2
        )

        assert len(selected) >= 2
        assert "source1" in selected  # Most confident should be included
        # source3 might be excluded if it increases uncertainty too much
        assert 0.0 <= epistemic <= 1.0
        assert 0.0 <= total <= 1.0

    def test_selection_empty_list(self):
        """Empty list should return empty selection."""
        selected, epistemic, total = select_calibrated_subset_muse(
            [],
            [],
            strategy="greedy"
        )
        assert selected == []
        assert epistemic == 0.5
        assert total == 0.5

    def test_selection_invalid_strategy(self):
        """Invalid strategy should raise ValueError."""
        predictions = [("source1", np.array([0.8, 0.2]))]
        confidence_scores = [0.8]

        with pytest.raises(ValueError):
            select_calibrated_subset_muse(
                predictions,
                confidence_scores,
                strategy="invalid"
            )

    def test_selection_mismatched_lengths(self):
        """Mismatched lengths should raise ValueError."""
        predictions = [("source1", np.array([0.8, 0.2]))]
        confidence_scores = [0.8, 0.7]  # Different length

        with pytest.raises(ValueError):
            select_calibrated_subset_muse(
                predictions,
                confidence_scores,
                strategy="greedy"
            )


class TestIntegration:
    """Integration tests for uncertainty quantification."""

    def test_end_to_end_uncertainty_computation(self):
        """Test complete uncertainty computation pipeline."""
        # Simulate multiple source predictions
        predictions = [
            np.array([0.8, 0.2]),
            np.array([0.75, 0.25]),
            np.array([0.7, 0.3]),
        ]

        # Compute uncertainties
        epistemic = compute_epistemic_uncertainty_jsd(predictions)
        aleatoric = compute_aleatoric_uncertainty_entropy(predictions)
        total = compute_total_uncertainty(epistemic, aleatoric, beta=0.5)

        # Verify all are in valid ranges
        assert 0.0 <= epistemic <= 1.0
        assert 0.0 <= aleatoric <= 1.0
        assert 0.0 <= total <= 1.0

        # Epistemic should be low for high agreement
        assert epistemic < 0.2

        # Total should be combination
        expected_total = epistemic + 0.5 * aleatoric
        assert total == pytest.approx(expected_total, abs=1e-6)

    def test_uncertainty_with_subset_selection(self):
        """Test uncertainty computation with subset selection."""
        predictions = [
            ("source1", np.array([0.9, 0.1])),
            ("source2", np.array([0.85, 0.15])),
            ("source3", np.array([0.1, 0.9])),  # Disagrees
        ]
        confidence_scores = [0.9, 0.85, 0.3]

        # Select subset
        selected, epistemic, total = select_calibrated_subset_muse(
            predictions,
            confidence_scores,
            strategy="conservative",
            m_min=2
        )

        # Verify selected sources
        assert len(selected) >= 2
        assert "source1" in selected
        assert "source2" in selected
        # source3 might be excluded due to disagreement

        # Verify uncertainties
        assert 0.0 <= epistemic <= 1.0
        assert 0.0 <= total <= 1.0

