"""
Information-theoretic uncertainty quantification for BOP.

Based on:
- "Rethinking the Uncertainty" (2410.20199v1)
- "MUSE: Multi-LLM Uncertainty via Subset Ensembles" (2507.07236v2)
"""

from typing import List, Tuple, Optional, Dict, Any, Union
import numpy as np

# Type hint for ContextNode (avoid circular import)
try:
    from bop.context_topology import ContextNode
except ImportError:
    ContextNode = Any

try:
    from scipy.spatial.distance import jensenshannon
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


def compute_jsd(p1: np.ndarray, p2: np.ndarray) -> float:
    """
    Compute Jensen-Shannon Divergence between two probability distributions.
    
    JSD(P||Q) = 0.5 * KL(P||M) + 0.5 * KL(Q||M)
    where M = 0.5 * (P + Q)
    
    Returns value in [0, 1] (normalized by log(2) if using base 2).
    
    Args:
        p1: First probability distribution (must sum to 1)
        p2: Second probability distribution (must sum to 1)
    
    Returns:
        JSD value in [0, 1]
    """
    # Ensure valid probability distributions
    p1 = np.asarray(p1, dtype=np.float64)
    p2 = np.asarray(p2, dtype=np.float64)
    
    # Normalize to sum to 1
    p1 = p1 / (p1.sum() + 1e-10)
    p2 = p2 / (p2.sum() + 1e-10)
    
    # Add small epsilon to avoid log(0)
    p1 = np.clip(p1, 1e-10, 1.0)
    p2 = np.clip(p2, 1e-10, 1.0)
    
    if SCIPY_AVAILABLE:
        # Use scipy's optimized implementation
        jsd = float(jensenshannon(p1, p2, base=2))
    else:
        # Fallback: manual computation using KL divergence
        m = 0.5 * (p1 + p2)
        # Add small epsilon to avoid division by zero
        m = np.clip(m, 1e-10, 1.0)
        # KL(P||M) = Σ P(i) * log(P(i) / M(i))
        kl_pm = np.sum(p1 * np.log2(p1 / m))
        kl_qm = np.sum(p2 * np.log2(p2 / m))
        jsd = float(0.5 * kl_pm + 0.5 * kl_qm)
    
    return jsd


def compute_epistemic_uncertainty_jsd(
    predictions: List[np.ndarray],
    mean_prediction: Optional[np.ndarray] = None
) -> float:
    """
    Compute epistemic uncertainty as average JSD from mean.
    
    U_epistemic = (1/|S|) Σ JS(p_i || p̄)
    
    This measures disagreement among sources/models.
    Higher values indicate more disagreement (higher epistemic uncertainty).
    
    Args:
        predictions: List of probability distributions (one per source)
        mean_prediction: Optional pre-computed mean (will compute if None)
    
    Returns:
        Epistemic uncertainty in [0, 1]
    """
    if not predictions:
        return 0.5  # Default uncertainty if no predictions
    
    predictions = [np.asarray(p, dtype=np.float64) for p in predictions]
    
    # Compute mean if not provided
    if mean_prediction is None:
        mean_prediction = np.mean(predictions, axis=0)
    else:
        mean_prediction = np.asarray(mean_prediction, dtype=np.float64)
    
    # Normalize mean
    mean_prediction = mean_prediction / (mean_prediction.sum() + 1e-10)
    
    # Compute JSD for each prediction
    jsds = [compute_jsd(p, mean_prediction) for p in predictions]
    
    return float(np.mean(jsds))


def compute_aleatoric_uncertainty_entropy(
    predictions: List[np.ndarray]
) -> float:
    """
    Compute aleatoric uncertainty as average entropy.
    
    U_aleatoric = (1/|S|) Σ H(p_i)
    where H(p) = -Σ p_i log_2 p_i
    
    This measures inherent randomness/ambiguity in the data.
    Higher values indicate more inherent uncertainty (irreducible).
    
    Args:
        predictions: List of probability distributions (one per source)
    
    Returns:
        Aleatoric uncertainty in [0, 1] (normalized by log_2(n) for n classes)
    """
    if not predictions:
        return 0.3  # Default aleatoric uncertainty
    
    predictions = [np.asarray(p, dtype=np.float64) for p in predictions]
    
    entropies = []
    for p in predictions:
        # Normalize
        p = p / (p.sum() + 1e-10)
        
        # Add small epsilon to avoid log(0)
        p_safe = np.clip(p, 1e-10, 1.0 - 1e-10)
        
        # Compute entropy
        entropy = -np.sum(p_safe * np.log2(p_safe))
        entropies.append(entropy)
    
    avg_entropy = float(np.mean(entropies))
    
    # Normalize by log_2(n) where n is number of classes
    # For binary: max entropy = log_2(2) = 1.0
    # For n classes: max entropy = log_2(n)
    n_classes = len(predictions[0])
    max_entropy = np.log2(n_classes) if n_classes > 1 else 1.0
    
    # Normalize to [0, 1]
    normalized = avg_entropy / (max_entropy + 1e-10)
    
    return float(np.clip(normalized, 0.0, 1.0))


def compute_total_uncertainty(
    epistemic: float,
    aleatoric: float,
    beta: float = 0.5
) -> float:
    """
    Compute total uncertainty as weighted sum.
    
    U_total = U_epistemic + β · U_aleatoric
    
    Args:
        epistemic: Epistemic uncertainty (reducible)
        aleatoric: Aleatoric uncertainty (irreducible)
        beta: Weighting factor for aleatoric uncertainty
    
    Returns:
        Total uncertainty in [0, 1]
    """
    total = epistemic + beta * aleatoric
    return float(np.clip(total, 0.0, 1.0))


def aggregate_with_aleatoric_weighting(
    predictions: List[np.ndarray],
    entropies: Optional[List[float]] = None
) -> np.ndarray:
    """
    Aggregate predictions with aleatoric-aware weighting.
    
    Weight = 1 - H(p_i)  (higher weight for lower entropy = more confident)
    
    Args:
        predictions: List of probability distributions
        entropies: Optional pre-computed entropies (will compute if None)
    
    Returns:
        Weighted average prediction
    """
    if not predictions:
        raise ValueError("Cannot aggregate empty predictions")
    
    predictions = [np.asarray(p, dtype=np.float64) for p in predictions]
    
    # Compute entropies if not provided
    if entropies is None:
        entropies = []
        for p in predictions:
            p_norm = p / (p.sum() + 1e-10)
            p_safe = np.clip(p_norm, 1e-10, 1.0 - 1e-10)
            entropy = -np.sum(p_safe * np.log2(p_safe))
            entropies.append(entropy)
    
    # Compute weights (inverse of entropy, normalized)
    weights = np.array([1.0 - h for h in entropies])
    weights = np.clip(weights, 0.0, 1.0)  # Ensure non-negative
    
    # Normalize weights
    weight_sum = weights.sum()
    if weight_sum > 0:
        weights = weights / weight_sum
    else:
        # Fallback to uniform if all weights are zero
        weights = np.ones(len(predictions)) / len(predictions)
    
    # Weighted average
    weighted_pred = np.sum(
        [w * p for w, p in zip(weights, predictions)],
        axis=0
    )
    
    # Normalize result
    weighted_pred = weighted_pred / (weighted_pred.sum() + 1e-10)
    
    return weighted_pred


def select_calibrated_subset_muse(
    predictions: List[Tuple[str, np.ndarray]],  # (source_id, prediction)
    confidence_scores: List[float],
    beta: float = 0.5,
    epsilon_tol: float = 0.04,
    m_min: int = 2,
    strategy: str = "greedy"
) -> Tuple[List[str], float, float]:
    """
    Select well-calibrated subset of sources using MUSE algorithm.
    
    Greedy: Start with most confident, add sources that increase diversity (epistemic)
    Conservative: Select sources that minimize total uncertainty
    
    Args:
        predictions: List of (source_id, prediction_distribution) tuples
        confidence_scores: Confidence scores for each source
        beta: Weighting factor for aleatoric uncertainty
        epsilon_tol: Tolerance for epistemic uncertainty increase (greedy) or decrease (conservative)
        m_min: Minimum subset size
        strategy: "greedy" or "conservative"
    
    Returns:
        (selected_source_ids, epistemic_uncertainty, total_uncertainty)
    """
    if not predictions:
        return [], 0.5, 0.5
    
    if len(predictions) != len(confidence_scores):
        raise ValueError("Predictions and confidence scores must have same length")
    
    # Sort by confidence (descending)
    sorted_items = sorted(
        zip(predictions, confidence_scores),
        key=lambda x: x[1],
        reverse=True
    )
    
    if strategy == "greedy":
        return _greedy_subset_selection(
            sorted_items, beta, epsilon_tol, m_min
        )
    elif strategy == "conservative":
        return _conservative_subset_selection(
            sorted_items, beta, epsilon_tol, m_min
        )
    else:
        raise ValueError(f"Unknown strategy: {strategy}")


def _greedy_subset_selection(
    sorted_items: List[Tuple[Tuple[str, np.ndarray], float]],
    beta: float,
    epsilon_tol: float,
    m_min: int
) -> Tuple[List[str], float, float]:
    """Greedy subset selection: maximize diversity up to tolerance."""
    if not sorted_items:
        return [], 0.5, 0.5
    
    # Start with most confident source
    (first_id, first_pred), _ = sorted_items[0]
    selected = [(first_id, first_pred)]
    selected_ids = [first_id]
    
    prev_epistemic = 0.0  # Single source has no disagreement
    
    # Iteratively add sources
    for (source_id, pred), _ in sorted_items[1:]:
        # Try adding this source
        candidate = selected + [(source_id, pred)]
        candidate_preds = [p for _, p in candidate]
        
        # Compute epistemic uncertainty
        epistemic = compute_epistemic_uncertainty_jsd(candidate_preds)
        
        # Check if adding increases epistemic uncertainty enough
        epistemic_increase = epistemic - prev_epistemic
        
        # Stop if we've reached minimum size and increase is too small
        if len(selected) >= m_min and epistemic_increase <= epsilon_tol:
            break
        
        # Add source
        selected.append((source_id, pred))
        selected_ids.append(source_id)
        prev_epistemic = epistemic
    
    # Compute final uncertainties
    selected_preds = [p for _, p in selected]
    final_epistemic = compute_epistemic_uncertainty_jsd(selected_preds)
    final_aleatoric = compute_aleatoric_uncertainty_entropy(selected_preds)
    final_total = compute_total_uncertainty(final_epistemic, final_aleatoric, beta)
    
    return selected_ids, final_epistemic, final_total


def _conservative_subset_selection(
    sorted_items: List[Tuple[Tuple[str, np.ndarray], float]],
    beta: float,
    epsilon_tol: float,
    m_min: int
) -> Tuple[List[str], float, float]:
    """Conservative subset selection: minimize total uncertainty."""
    if not sorted_items:
        return [], 0.5, 0.5
    
    # Start with most confident source
    (first_id, first_pred), _ = sorted_items[0]
    selected = [(first_id, first_pred)]
    selected_ids = [first_id]
    
    prev_total = float('inf')  # Start with infinite uncertainty
    
    # Iteratively add sources
    for (source_id, pred), _ in sorted_items[1:]:
        # Try adding this source
        candidate = selected + [(source_id, pred)]
        candidate_preds = [p for _, p in candidate]
        
        # Compute uncertainties
        epistemic = compute_epistemic_uncertainty_jsd(candidate_preds)
        aleatoric = compute_aleatoric_uncertainty_entropy(candidate_preds)
        total = compute_total_uncertainty(epistemic, aleatoric, beta)
        
        # Check if adding reduces total uncertainty
        uncertainty_reduction = prev_total - total
        
        # Stop if we've reached minimum size and reduction is too small
        if len(selected) >= m_min and uncertainty_reduction < epsilon_tol:
            break
        
        # Add source if it reduces uncertainty
        if total < prev_total:
            selected.append((source_id, pred))
            selected_ids.append(source_id)
            prev_total = total
        else:
            # Stop if adding increases uncertainty
            break
    
    # Compute final uncertainties
    selected_preds = [p for _, p in selected]
    final_epistemic = compute_epistemic_uncertainty_jsd(selected_preds)
    final_aleatoric = compute_aleatoric_uncertainty_entropy(selected_preds)
    final_total = compute_total_uncertainty(final_epistemic, final_aleatoric, beta)
    
    return selected_ids, final_epistemic, final_total



def extract_prediction_from_result(
    result: Dict[str, Any],
    node: Optional[Any] = None,
    use_confidence: bool = True,
    use_credibility: bool = False,
    binary: bool = True
) -> np.ndarray:
    """
    Extract probability distribution from BOP result.
    
    Converts text results and node metadata into probability distributions
    for uncertainty computation.
    
    Strategies (in order of preference):
    1. Use node confidence: [confidence, 1-confidence] (binary)
    2. Use node credibility: [credibility, 1-credibility] (if use_credibility=True)
    3. Use epistemic uncertainty: [1-uncertainty, uncertainty]
    4. Use relevance scores (if available in result)
    5. Default: [0.5, 0.5] (uniform)
    
    Args:
        result: Dictionary with result data (from MCP tool)
        node: Optional ContextNode with confidence/uncertainty metadata
        use_confidence: If True, use node.confidence (default: True)
        use_credibility: If True, prefer node.credibility over confidence
        binary: If True, return binary distribution [p, 1-p]. If False, return multi-class
    
    Returns:
        Probability distribution as numpy array (sums to 1.0)
    """
    # Strategy 1: Use node confidence (most reliable)
    if node is not None and use_confidence and not use_credibility:
        if hasattr(node, 'confidence') and node.confidence is not None:
            confidence = float(node.confidence)
            confidence = np.clip(confidence, 0.0, 1.0)
            if binary:
                return np.array([confidence, 1.0 - confidence])
            else:
                # Multi-class: distribute confidence across classes
                n_classes = 3  # Default: 3 classes (positive, neutral, negative)
                pred = np.ones(n_classes) * (1.0 - confidence) / (n_classes - 1)
                pred[0] = confidence  # First class gets the confidence
                return pred / pred.sum()  # Normalize
    
    # Strategy 2: Use node credibility
    if node is not None and use_credibility:
        if hasattr(node, 'credibility') and node.credibility is not None:
            credibility = float(node.credibility)
            credibility = np.clip(credibility, 0.0, 1.0)
            if binary:
                return np.array([credibility, 1.0 - credibility])
    
    # Strategy 3: Use epistemic uncertainty (inverse)
    if node is not None:
        if hasattr(node, 'epistemic_uncertainty') and node.epistemic_uncertainty is not None:
            uncertainty = float(node.epistemic_uncertainty)
            uncertainty = np.clip(uncertainty, 0.0, 1.0)
            confidence = 1.0 - uncertainty
            if binary:
                return np.array([confidence, uncertainty])
    
    # Strategy 4: Use relevance scores from result (if available) - multi-class support
    if "relevance_breakdown" in result:
        relevance = result["relevance_breakdown"]
        if isinstance(relevance, dict):
            if "overall_score" in relevance:
                score = float(relevance["overall_score"])
                score = np.clip(score, 0.0, 1.0)
                if binary:
                    return np.array([score, 1.0 - score])
            # Multi-class: use component scores if available
            if not binary and "component_scores" in relevance:
                component_scores = relevance["component_scores"]
                if isinstance(component_scores, (list, dict)):
                    if isinstance(component_scores, dict):
                        scores = list(component_scores.values())
                    else:
                        scores = component_scores
                    if scores:
                        scores = [float(s) for s in scores]
                        scores = np.array(scores)
                        scores = np.clip(scores, 0.0, 1.0)
                        # Normalize to probability distribution
                        scores = scores / (scores.sum() + 1e-10)
                        return scores
    
    # Strategy 5: Use overlap_ratio (if available)
    if "overlap_ratio" in result:
        overlap = float(result["overlap_ratio"])
        overlap = np.clip(overlap, 0.0, 1.0)
        if binary:
            return np.array([overlap, 1.0 - overlap])
    
    # Strategy 6: Use semantic similarity (if available)
    if "semantic_similarity" in result:
        similarity = float(result["semantic_similarity"])
        similarity = np.clip(similarity, 0.0, 1.0)
        if binary:
            return np.array([similarity, 1.0 - similarity])
    
    # Default: Uniform distribution (maximum uncertainty)
    if binary:
        return np.array([0.5, 0.5])
    else:
        n_classes = 3
        return np.ones(n_classes) / n_classes
