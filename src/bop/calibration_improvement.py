"""
Calibration improvement using uncertainty metrics.

Uses epistemic and aleatoric uncertainty to improve Expected Calibration Error (ECE)
and Brier Score, as shown in MUSE paper.
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from .uncertainty import (
    compute_epistemic_uncertainty_jsd,
    compute_aleatoric_uncertainty_entropy,
    aggregate_with_aleatoric_weighting,
)


def improve_calibration_with_uncertainty(
    predictions: List[np.ndarray],
    confidence_scores: List[float],
    actual_outcomes: Optional[List[float]] = None,
    use_aleatoric_weighting: bool = True,
) -> Dict[str, Any]:
    """
    Improve calibration using uncertainty-aware aggregation.
    
    Based on MUSE paper findings:
    - Multi-source aggregation improves calibration (ECE, Brier Score)
    - Aleatoric-aware weighting improves stability
    - Selective aggregation (MUSE) outperforms naive averaging
    
    Args:
        predictions: List of probability distributions
        confidence_scores: Confidence scores for each prediction
        actual_outcomes: Optional actual outcomes (0/1) for calibration computation
        use_aleatoric_weighting: Whether to use aleatoric-aware weighting
    
    Returns:
        Dictionary with improved predictions and calibration metrics
    """
    if not predictions:
        return {
            "improved_prediction": None,
            "calibration_improvement": None,
            "ece_before": None,
            "ece_after": None,
            "brier_before": None,
            "brier_after": None,
        }
    
    predictions = [np.asarray(p, dtype=np.float64) for p in predictions]
    
    # Compute uncertainties
    epistemic = compute_epistemic_uncertainty_jsd(predictions)
    aleatoric = compute_aleatoric_uncertainty_entropy(predictions)
    
    # Aggregate predictions
    if use_aleatoric_weighting:
        # Use aleatoric-aware weighting (prioritize low-entropy predictions)
        improved_pred = aggregate_with_aleatoric_weighting(predictions)
    else:
        # Simple average
        improved_pred = np.mean(predictions, axis=0)
        improved_pred = improved_pred / (improved_pred.sum() + 1e-10)
    
    # Extract confidence from improved prediction (for binary: [confidence, 1-confidence])
    if len(improved_pred) >= 2:
        improved_confidence = float(improved_pred[0])
    else:
        improved_confidence = float(np.mean(confidence_scores))
    
    # Compute calibration metrics if outcomes available
    calibration_improvement = None
    ece_before = None
    ece_after = None
    brier_before = None
    brier_after = None
    
    if actual_outcomes and len(actual_outcomes) == len(confidence_scores):
        # Compute ECE and Brier before (using original confidence scores)
        ece_before = _compute_ece(confidence_scores, actual_outcomes)
        brier_before = _compute_brier_score(confidence_scores, actual_outcomes)
        
        # Compute ECE and Brier after (using individually calibrated confidences)
        # Calibrate each prediction individually using uncertainty
        calibrated_confidences = []
        for i, (pred, conf) in enumerate(zip(predictions, confidence_scores)):
            # Compute individual uncertainties for this prediction
            # Use epistemic uncertainty from disagreement with other predictions
            other_preds = [p for j, p in enumerate(predictions) if j != i]
            if other_preds:
                # Epistemic = disagreement with others
                epistemic = compute_epistemic_uncertainty_jsd([pred] + other_preds[:1])  # Compare with one other
            else:
                epistemic = 0.0
            
            # Aleatoric = entropy of this prediction
            aleatoric = compute_aleatoric_uncertainty_entropy([pred])
            
            # Calibrate this confidence
            calibrated_conf = calibrate_confidence_with_uncertainty(
                conf,
                epistemic,
                aleatoric,
                calibration_factor=0.7,  # Stronger calibration
            )
            calibrated_confidences.append(calibrated_conf)
        
        # If we couldn't calibrate individually, use improved_confidence as fallback
        if not calibrated_confidences:
            calibrated_confidences = [improved_confidence] * len(confidence_scores)
        
        ece_after = _compute_ece(calibrated_confidences, actual_outcomes)
        brier_after = _compute_brier_score(calibrated_confidences, actual_outcomes)
        
        # Calibration improvement
        if ece_before is not None and ece_after is not None:
            calibration_improvement = {
                "ece_reduction": float(ece_before - ece_after),
                "brier_reduction": float(brier_before - brier_after) if brier_before and brier_after else None,
                "relative_ece_improvement": float((ece_before - ece_after) / ece_before) if ece_before > 0 else 0.0,
            }
    
    return {
        "improved_prediction": improved_pred.tolist(),
        "improved_confidence": improved_confidence,
        "epistemic_uncertainty": float(epistemic),
        "aleatoric_uncertainty": float(aleatoric),
        "calibration_improvement": calibration_improvement,
        "ece_before": ece_before,
        "ece_after": ece_after,
        "brier_before": brier_before,
        "brier_after": brier_after,
    }


def _compute_ece(confidence_scores: List[float], actual_outcomes: List[float], bins: int = 10) -> float:
    """
    Compute Expected Calibration Error (ECE).
    
    ECE = Σ(n_i / N) × |acc_i - conf_i|
    """
    if not confidence_scores or not actual_outcomes:
        return 0.0
    
    bin_boundaries = np.linspace(0, 1, bins + 1)
    bin_lowers = bin_boundaries[:-1]
    bin_uppers = bin_boundaries[1:]
    
    ece = 0.0
    n_total = len(confidence_scores)
    
    for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
        in_bin = [
            (conf, actual)
            for conf, actual in zip(confidence_scores, actual_outcomes)
            if bin_lower <= conf < bin_upper
        ]
        if in_bin:
            accuracy_in_bin = np.mean([actual for _, actual in in_bin])
            avg_confidence_in_bin = np.mean([conf for conf, _ in in_bin])
            ece += len(in_bin) / n_total * abs(accuracy_in_bin - avg_confidence_in_bin)
    
    return float(ece)


def _compute_brier_score(confidence_scores: List[float], actual_outcomes: List[float]) -> float:
    """
    Compute Brier Score.
    
    Brier = (1/N) × Σ(conf_i - outcome_i)²
    """
    if not confidence_scores or not actual_outcomes:
        return 0.0
    
    squared_errors = [(conf - actual) ** 2 for conf, actual in zip(confidence_scores, actual_outcomes)]
    return float(np.mean(squared_errors))


def calibrate_confidence_with_uncertainty(
    confidence: float,
    epistemic_uncertainty: float,
    aleatoric_uncertainty: float,
    calibration_factor: float = 0.5,
) -> float:
    """
    Calibrate confidence score using uncertainty metrics.
    
    Adjusts confidence downward if uncertainty is high, upward if uncertainty is low.
    This helps align confidence with actual accuracy.
    
    Based on MUSE paper: uncertainty-aware calibration improves ECE.
    
    Args:
        confidence: Original confidence score
        epistemic_uncertainty: Epistemic uncertainty (reducible)
        aleatoric_uncertainty: Aleatoric uncertainty (irreducible)
        calibration_factor: How much to adjust (0.0 = no adjustment, 1.0 = full adjustment)
    
    Returns:
        Calibrated confidence score
    """
    # Normalize uncertainties to [0, 1] range
    # Epistemic uncertainty (JSD) is already in [0, 1]
    # Aleatoric uncertainty (entropy) needs normalization (max entropy for binary = 1.0)
    normalized_aleatoric = min(aleatoric_uncertainty / 1.0, 1.0)  # Binary max entropy = 1.0
    
    # Weighted total uncertainty (epistemic is more important for calibration)
    total_uncertainty = 0.7 * epistemic_uncertainty + 0.3 * normalized_aleatoric
    
    # Adjust confidence: high uncertainty → lower confidence, low uncertainty → increase confidence
    # Use temperature scaling approach: calibrated = confidence / (1 + uncertainty * factor)
    temperature = 1.0 + total_uncertainty * calibration_factor
    calibrated = confidence / temperature
    
    # For low uncertainty cases, increase confidence slightly
    if total_uncertainty < 0.2 and confidence < 0.8:
        # Low uncertainty, moderate confidence → can increase
        calibrated = calibrated * (1.0 + (0.2 - total_uncertainty) * 0.3)
    
    # Also apply direct adjustment for overconfident cases
    if confidence > 0.7 and total_uncertainty > 0.3:
        # Overconfident: reduce more aggressively
        calibrated = calibrated * (1.0 - total_uncertainty * 0.5)
    
    return float(np.clip(calibrated, 0.0, 1.0))

