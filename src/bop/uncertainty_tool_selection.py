"""
MUSE-based tool selection for optimal subset selection.

Uses uncertainty metrics to select the best subset of tools before execution.
"""

from typing import Any, Dict, List, Tuple

import numpy as np

from .context_topology import ContextNode
from .uncertainty import (
    aggregate_with_aleatoric_weighting,
    extract_prediction_from_result,
    select_calibrated_subset_muse,
)


def select_tools_with_muse(
    candidate_tools: List[str],
    tool_metadata: List[Dict[str, Any]],
    subproblem: str,
    max_tools: int = 3,
    strategy: str = "greedy",
    beta: float = 0.5,
    min_credibility: float = 0.3,  # NEW: Filter low-credibility sources
) -> Tuple[List[str], Dict[str, Any]]:
    """
    Select optimal subset of tools using MUSE algorithm.

    Uses uncertainty metrics to select tools that:
    - Maximize diversity (epistemic uncertainty) - greedy strategy
    - Minimize total uncertainty - conservative strategy

    Args:
        candidate_tools: List of tool identifiers (e.g., "perplexity_search")
        tool_metadata: List of metadata dicts for each tool (source credibility, historical performance, etc.)
        subproblem: The subproblem being addressed (for context)
        max_tools: Maximum number of tools to select
        strategy: "greedy" (maximize diversity) or "conservative" (minimize uncertainty)
        beta: Weighting factor for aleatoric uncertainty

    Returns:
        (selected_tool_ids, selection_metadata)
    """
    if not candidate_tools or not tool_metadata:
        return [], {"epistemic_uncertainty": 0.5, "total_uncertainty": 0.5, "selection_reason": "no_candidates"}

    if len(candidate_tools) != len(tool_metadata):
        # Pad or truncate to match
        min_len = min(len(candidate_tools), len(tool_metadata))
        candidate_tools = candidate_tools[:min_len]
        tool_metadata = tool_metadata[:min_len]

    # Filter by minimum credibility (source credibility integration)
    filtered_tools = []
    filtered_metadata = []
    for tool_id, metadata in zip(candidate_tools, tool_metadata):
        credibility = metadata.get("credibility", metadata.get("confidence", 0.5))
        if credibility >= min_credibility:
            filtered_tools.append(tool_id)
            filtered_metadata.append(metadata)

    if not filtered_tools:
        # If all filtered out, use original (with warning)
        filtered_tools = candidate_tools
        filtered_metadata = tool_metadata

    # Extract predictions and confidence scores from metadata
    predictions = []
    confidence_scores = []

    for tool_id, metadata in zip(filtered_tools, filtered_metadata):
        # Use source credibility as confidence (prioritize credibility)
        confidence = metadata.get("credibility", metadata.get("confidence", 0.5))

        # Create a mock node for prediction extraction
        # Use historical performance or default uncertainty
        metadata.get("epistemic_uncertainty", 0.5)
        metadata.get("aleatoric_uncertainty", 0.3)

        # Create binary prediction: [confidence, 1-confidence]
        pred = np.array([confidence, 1.0 - confidence])
        predictions.append((tool_id, pred))
        confidence_scores.append(confidence)

    # Apply MUSE subset selection
    try:
        selected_ids, epistemic, total = select_calibrated_subset_muse(
            predictions,
            confidence_scores,
            beta=beta,
            strategy=strategy,
            m_min=1,  # Minimum 1 tool
            epsilon_tol=0.05,
        )

        # Limit to max_tools
        selected_ids = selected_ids[:max_tools]

        selection_metadata = {
            "epistemic_uncertainty": float(epistemic),
            "total_uncertainty": float(total),
            "selection_reason": f"muse_{strategy}",
            "num_candidates": len(candidate_tools),
            "num_filtered": len(filtered_tools),  # NEW: Show filtering effect
            "num_selected": len(selected_ids),
            "min_credibility_filter": min_credibility,  # NEW: Show filter threshold
        }

        return selected_ids, selection_metadata
    except Exception as e:
        # Fallback: select top tools by confidence
        sorted_tools = sorted(
            zip(candidate_tools, confidence_scores),
            key=lambda x: x[1],
            reverse=True
        )
        selected_ids = [tool_id for tool_id, _ in sorted_tools[:max_tools]]

        return selected_ids, {
            "epistemic_uncertainty": 0.5,
            "total_uncertainty": 0.5,
            "selection_reason": f"fallback_due_to_error: {str(e)}",
            "num_candidates": len(candidate_tools),
            "num_selected": len(selected_ids),
        }


def aggregate_results_with_aleatoric_weighting(
    results: List[Dict[str, Any]],
    nodes: List[ContextNode],
) -> Dict[str, Any]:
    """
    Aggregate tool results using aleatoric-aware weighting.

    Weights results by their aleatoric uncertainty (lower entropy = higher weight).
    This prioritizes confident, low-uncertainty results over high-entropy ones.

    Args:
        results: List of tool result dictionaries
        nodes: List of corresponding ContextNode objects

    Returns:
        Aggregated result dictionary with weighted synthesis
    """
    if not results or not nodes:
        return {"aggregated": "", "weights": [], "aleatoric_uncertainties": []}

    if len(results) != len(nodes):
        # Mismatch: use simple concatenation
        return {
            "aggregated": "\n\n".join(r.get("result", "") for r in results),
            "weights": [1.0 / len(results)] * len(results),
            "aleatoric_uncertainties": [],
        }

    # Extract predictions and compute aleatoric uncertainties
    predictions = []
    aleatoric_uncertainties = []

    for result, node in zip(results, nodes):
        pred = extract_prediction_from_result(result, node)
        predictions.append(pred)

        # Compute aleatoric uncertainty (entropy)
        p_safe = np.clip(pred, 1e-10, 1.0 - 1e-10)
        entropy = -np.sum(p_safe * np.log2(p_safe))
        aleatoric_uncertainties.append(float(entropy))

    # Aggregate with aleatoric-aware weighting
    try:
        weighted_pred = aggregate_with_aleatoric_weighting(
            predictions,
            entropies=aleatoric_uncertainties
        )

        # Compute weights for result aggregation
        # Weight = 1 - normalized_entropy (lower entropy = higher weight)
        max_entropy = max(aleatoric_uncertainties) if aleatoric_uncertainties else 1.0
        if max_entropy > 0:
            normalized_entropies = [e / max_entropy for e in aleatoric_uncertainties]
            weights = [1.0 - ne for ne in normalized_entropies]
        else:
            weights = [1.0] * len(results)

        # Normalize weights
        weight_sum = sum(weights)
        if weight_sum > 0:
            weights = [w / weight_sum for w in weights]
        else:
            weights = [1.0 / len(results)] * len(results)

        # Weighted aggregation of result texts
        result_texts = [r.get("result", "") for r in results]
        weighted_synthesis = "\n\n".join(
            f"[Weight: {w:.2f}] {text[:200]}..."
            if len(text) > 200 else f"[Weight: {w:.2f}] {text}"
            for w, text in zip(weights, result_texts)
        )

        # Also create a simple weighted concatenation
        # (in practice, would use LLM to synthesize with weights)
        aggregated_text = "\n\n".join(result_texts)

        return {
            "aggregated": aggregated_text,
            "weighted_synthesis": weighted_synthesis,
            "weights": weights,
            "aleatoric_uncertainties": aleatoric_uncertainties,
            "weighted_prediction": weighted_pred.tolist(),
        }
    except Exception as e:
        # Fallback: uniform weighting
        return {
            "aggregated": "\n\n".join(r.get("result", "") for r in results),
            "weights": [1.0 / len(results)] * len(results),
            "aleatoric_uncertainties": aleatoric_uncertainties,
            "error": str(e),
        }

