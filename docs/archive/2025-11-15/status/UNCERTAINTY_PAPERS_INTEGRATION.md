# Integration of Uncertainty Quantification Research into BOP

## Executive Summary

This document analyzes two recent arXiv papers on uncertainty quantification in LLMs and proposes concrete integration steps for BOP's framework:

1. **"Rethinking the Uncertainty: A Critical Review and Analysis in the Era of Large Language Models"** (2410.20199v1)
2. **"Simple Yet Effective: An Information-Theoretic Approach to Multi-LLM Uncertainty Quantification"** (2507.07236v2) - MUSE by Maya Kruse et al.

## Key Insights from Paper 1: "Rethinking the Uncertainty"

### 1. Operational vs Output Uncertainty Distinction

**Critical Framework:**
- **Operational Uncertainty**: Arises from pre-training to inference (data acquisition, model design, training, alignment, inference)
- **Output Uncertainty**: Focuses on quality of generated content (lack of evidence, contradictions, multiple knowledge frames)

**BOP Relevance:**
- BOP's research pipeline spans multiple stages (query decomposition → tool selection → synthesis)
- Each stage introduces operational uncertainty
- Final response quality introduces output uncertainty
- **Action**: Track uncertainty separately at each pipeline stage

### 2. Uncertainty vs Confidence vs Reliability

**Key Distinction:**
- **Uncertainty**: Extent to which model "knows" or "doesn't know" (epistemic/aleatoric)
- **Confidence**: Predicted probability score (can be misleading - high confidence ≠ low uncertainty)
- **Reliability**: Alignment between confidence and actual accuracy (calibration)

**BOP Relevance:**
- BOP already separates `credibility` (external) and `confidence` (internal)
- Need to ensure `confidence` scores are calibrated (already tracking `calibration_error`)
- **Action**: Enhance calibration monitoring and add reliability metrics

### 3. Sources of Uncertainty Throughout LLM Lifecycle

**Operational Uncertainty Sources:**
- Data uncertainty (semantic ambiguity, linguistic variability, errors, insufficient coverage, contamination, human biases)
- Model uncertainty (architecture, parameter estimation, optimization)
- Distributional uncertainty (in-domain vs out-of-domain)
- Sampling/decoding strategy uncertainty

**BOP Relevance:**
- BOP uses multiple MCP tools (Perplexity, Firecrawl, Tavily, arXiv, Kagi) - each has different training/data characteristics
- Tool selection introduces model uncertainty
- Query decomposition introduces distributional uncertainty
- **Action**: Track uncertainty sources per tool and per query type

## Key Insights from Paper 2: "MUSE - Multi-LLM Uncertainty via Subset Ensembles"

### 1. Jensen-Shannon Divergence for Epistemic Uncertainty

**Mathematical Foundation:**
```
U_epistemic(S) = (1/|S|) Σ JS(p_i || p̄)
```
where:
- `S` = subset of sources/models
- `p_i` = predictive distribution from source i
- `p̄` = mean distribution across subset
- `JS` = Jensen-Shannon Divergence (symmetric, bounded [0,1])

**BOP Relevance:**
- BOP aggregates results from multiple MCP tools (similar to multi-LLM ensemble)
- Currently uses heuristic overlap/coherence for epistemic uncertainty
- **Action**: Replace heuristic with JSD-based epistemic uncertainty computation

### 2. Information-Theoretic Uncertainty Decomposition

**Total Uncertainty:**
```
U_total(S) = U_epistemic(S) + β·U_aleatoric(S)
```

**Epistemic Uncertainty:**
- Measured via JSD: disagreement among sources
- Reducible through better source selection/aggregation

**Aleatoric Uncertainty:**
- Measured via entropy: H(p) = -p log p - (1-p) log(1-p)
- Irreducible (inherent data ambiguity)

**BOP Relevance:**
- BOP already separates epistemic and aleatoric uncertainty in `ContextNode`
- Current epistemic estimation is heuristic-based
- **Action**: Implement JSD-based epistemic uncertainty and entropy-based aleatoric uncertainty

### 3. Subset Selection for Calibrated Ensembles

**MUSE Algorithm:**
- Greedy: Start with most confident source, iteratively add sources that increase diversity (epistemic uncertainty) up to tolerance
- Conservative: Select sources that minimize total uncertainty (epistemic + aleatoric)

**BOP Relevance:**
- BOP selects tools via `ToolSelector` and constraint solver
- Could enhance tool selection to optimize for uncertainty reduction
- **Action**: Add uncertainty-aware tool selection that balances diversity and reliability

### 4. Calibration Improvements

**Key Finding:**
- Multi-source aggregation improves both AUROC and calibration (ECE, Brier Score)
- Selective aggregation (MUSE) outperforms naive averaging
- Aleatoric-aware weighting improves stability

**BOP Relevance:**
- BOP already tracks calibration error
- Could improve calibration by better uncertainty-aware aggregation
- **Action**: Implement aleatoric-aware weighting in source aggregation

## Proposed Integration Steps

### Phase 1: Information-Theoretic Uncertainty Computation

**1.1 Implement Jensen-Shannon Divergence**

```python
# src/bop/uncertainty.py (NEW)
import numpy as np
from scipy.spatial.distance import jensenshannon

def compute_jsd(p1: np.ndarray, p2: np.ndarray) -> float:
    """
    Compute Jensen-Shannon Divergence between two probability distributions.
    
    JSD(P||Q) = 0.5 * KL(P||M) + 0.5 * KL(Q||M)
    where M = 0.5 * (P + Q)
    
    Returns value in [0, 1] (normalized by log(2))
    """
    return float(jensenshannon(p1, p2, base=2))

def compute_epistemic_uncertainty_jsd(
    predictions: List[np.ndarray],
    mean_prediction: Optional[np.ndarray] = None
) -> float:
    """
    Compute epistemic uncertainty as average JSD from mean.
    
    U_epistemic = (1/|S|) Σ JS(p_i || p̄)
    """
    if mean_prediction is None:
        mean_prediction = np.mean(predictions, axis=0)
    
    jsds = [compute_jsd(p, mean_prediction) for p in predictions]
    return float(np.mean(jsds))
```

**1.2 Implement Aleatoric Uncertainty (Entropy)**

```python
def compute_aleatoric_uncertainty_entropy(
    predictions: List[np.ndarray]
) -> float:
    """
    Compute aleatoric uncertainty as average entropy.
    
    U_aleatoric = (1/|S|) Σ H(p_i)
    where H(p) = -Σ p_i log p_i
    """
    entropies = []
    for p in predictions:
        # Add small epsilon to avoid log(0)
        p_safe = np.clip(p, 1e-10, 1.0 - 1e-10)
        entropy = -np.sum(p_safe * np.log2(p_safe))
        entropies.append(entropy)
    
    return float(np.mean(entropies))
```

**1.3 Update ContextTopology to Use JSD**

```python
# src/bop/context_topology.py
from .uncertainty import compute_epistemic_uncertainty_jsd, compute_aleatoric_uncertainty_entropy

def compute_clique_uncertainty(self, nodes: Set[str]) -> Dict[str, float]:
    """
    Compute uncertainty metrics for a clique using JSD and entropy.
    """
    # Extract predictions from nodes (convert to probability distributions)
    predictions = []
    for node_id in nodes:
        node = self.nodes[node_id]
        # Convert confidence/uncertainty to probability distribution
        # For binary: [confidence, 1-confidence] or [1-uncertainty, uncertainty]
        pred = np.array([1.0 - node.epistemic_uncertainty, node.epistemic_uncertainty])
        predictions.append(pred)
    
    if not predictions:
        return {"epistemic": 0.5, "aleatoric": 0.3, "total": 0.5}
    
    predictions = np.array(predictions)
    mean_pred = np.mean(predictions, axis=0)
    
    # Compute uncertainties
    epistemic = compute_epistemic_uncertainty_jsd(predictions, mean_pred)
    aleatoric = compute_aleatoric_uncertainty_entropy(predictions)
    
    # Total uncertainty (β = 0.5 for balance)
    beta = 0.5
    total = epistemic + beta * aleatoric
    
    return {
        "epistemic": float(epistemic),
        "aleatoric": float(aleatoric),
        "total": float(total)
    }
```

### Phase 2: Multi-Source Ensemble (MUSE-Inspired)

**2.1 Implement Subset Selection Algorithm**

```python
# src/bop/uncertainty.py
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
    
    Returns:
        (selected_source_ids, epistemic_uncertainty, total_uncertainty)
    """
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
```

**2.2 Update Orchestrator to Use MUSE**

```python
# src/bop/orchestrator.py
from .uncertainty import select_calibrated_subset_muse

def _aggregate_results_with_uncertainty(
    self,
    results: List[Dict[str, Any]],
    query: str
) -> Dict[str, Any]:
    """
    Aggregate results using uncertainty-aware subset selection.
    """
    # Convert results to predictions
    predictions = []
    confidence_scores = []
    
    for result in results:
        # Extract prediction distribution (simplified - would need proper extraction)
        source_id = result.get("source", "unknown")
        confidence = result.get("confidence", 0.5)
        
        # Convert to probability distribution (binary for simplicity)
        # In practice, would extract from LLM output
        pred = np.array([confidence, 1.0 - confidence])
        
        predictions.append((source_id, pred))
        confidence_scores.append(confidence)
    
    # Select calibrated subset
    selected_ids, epistemic, total = select_calibrated_subset_muse(
        predictions,
        confidence_scores,
        strategy="greedy"
    )
    
    # Aggregate selected results
    selected_results = [
        r for r in results
        if r.get("source") in selected_ids
    ]
    
    return {
        "aggregated_result": self._synthesize_results(selected_results),
        "epistemic_uncertainty": epistemic,
        "total_uncertainty": total,
        "selected_sources": selected_ids
    }
```

### Phase 3: Operational vs Output Uncertainty Tracking

**3.1 Add Uncertainty Tracking Per Pipeline Stage**

```python
# src/bop/orchestrator.py
@dataclass
class PipelineUncertainty:
    """Track uncertainty at each pipeline stage."""
    query_decomposition: float = 0.5  # Operational
    tool_selection: float = 0.5  # Operational
    tool_execution: float = 0.5  # Operational
    result_aggregation: float = 0.5  # Operational
    synthesis: float = 0.5  # Output
    final_response: float = 0.5  # Output
```

**3.2 Update Research Flow to Track Uncertainty**

```python
# src/bop/orchestrator.py
async def research_with_schema(
    self,
    query: str,
    schema_name: str,
    ...
) -> Dict[str, Any]:
    """
    Enhanced with uncertainty tracking at each stage.
    """
    uncertainty_tracker = PipelineUncertainty()
    
    # Stage 1: Query decomposition
    subsolutions = await self._decompose_query(query, schema_name)
    uncertainty_tracker.query_decomposition = self._estimate_decomposition_uncertainty(subsolutions)
    
    # Stage 2: Tool selection
    tools_selected = self._select_tools(...)
    uncertainty_tracker.tool_selection = self._estimate_selection_uncertainty(tools_selected)
    
    # Stage 3: Tool execution
    results = await self._execute_tools(...)
    uncertainty_tracker.tool_execution = self._estimate_execution_uncertainty(results)
    
    # Stage 4: Aggregation (with MUSE)
    aggregated = self._aggregate_results_with_uncertainty(results, query)
    uncertainty_tracker.result_aggregation = aggregated["epistemic_uncertainty"]
    
    # Stage 5: Synthesis
    synthesis = await self._synthesize(...)
    uncertainty_tracker.synthesis = self._estimate_synthesis_uncertainty(synthesis)
    
    # Stage 6: Final response
    final_response = await self._generate_response(...)
    uncertainty_tracker.final_response = self._estimate_output_uncertainty(final_response)
    
    return {
        ...,
        "uncertainty_tracking": uncertainty_tracker,
        "epistemic_uncertainty": aggregated["epistemic_uncertainty"],
        "total_uncertainty": aggregated["total_uncertainty"]
    }
```

### Phase 4: Aleatoric-Aware Weighting

**4.1 Implement Weighted Aggregation**

```python
# src/bop/uncertainty.py
def aggregate_with_aleatoric_weighting(
    predictions: List[np.ndarray],
    entropies: List[float]
) -> np.ndarray:
    """
    Aggregate predictions with aleatoric-aware weighting.
    
    Weight = 1 - H(p_i)  (higher weight for lower entropy = more confident)
    """
    weights = [1.0 - h for h in entropies]
    weights = np.array(weights)
    weights = weights / np.sum(weights)  # Normalize
    
    weighted_pred = np.sum(
        [w * p for w, p in zip(weights, predictions)],
        axis=0
    )
    
    return weighted_pred
```

## Testing Strategy

### Unit Tests

1. **JSD Computation**
   - Test with identical distributions (should be 0)
   - Test with completely different distributions (should be 1)
   - Test with similar distributions (should be in [0, 1])

2. **Epistemic Uncertainty**
   - Test with high agreement (low JSD)
   - Test with high disagreement (high JSD)
   - Test with empty set (edge case)

3. **Aleatoric Uncertainty**
   - Test with high entropy (uniform distribution)
   - Test with low entropy (peaked distribution)
   - Test with binary predictions

4. **Subset Selection**
   - Test greedy strategy
   - Test conservative strategy
   - Test with varying confidence scores
   - Test with minimum subset size constraint

### Integration Tests

1. **End-to-End Uncertainty Tracking**
   - Verify uncertainty decreases through pipeline stages
   - Verify operational vs output uncertainty distinction
   - Verify calibration improvements

2. **Multi-Source Aggregation**
   - Compare naive averaging vs MUSE selection
   - Verify calibration improvements
   - Verify robustness to weak sources

## Implementation Priority

1. **High Priority** (Immediate):
   - Implement JSD computation
   - Replace heuristic epistemic uncertainty with JSD-based
   - Add entropy-based aleatoric uncertainty

2. **Medium Priority** (Next Sprint):
   - Implement MUSE-inspired subset selection
   - Add uncertainty tracking per pipeline stage
   - Implement aleatoric-aware weighting

3. **Low Priority** (Future):
   - Operational vs output uncertainty distinction in UI
   - Uncertainty visualization improvements
   - Advanced calibration techniques

## Alignment with BOP's Core Purpose

These enhancements align with BOP's mission of **knowledge structure research**:

1. **Topological Analysis**: JSD measures disagreement/disagreement structure (clique coherence)
2. **D-Separation**: Uncertainty-aware aggregation preserves conditional independence
3. **Information Geometry**: JSD and entropy are information-theoretic measures (Fisher Information connection)
4. **Trust Modeling**: Better uncertainty quantification improves trust calibration
5. **Source Agreement**: MUSE identifies well-calibrated source subsets (clique identification)

## References

1. Beigi, M., et al. (2024). "Rethinking the Uncertainty: A Critical Review and Analysis in the Era of Large Language Models." arXiv:2410.20199v1
2. Kruse, M., et al. (2025). "Simple Yet Effective: An Information-Theoretic Approach to Multi-LLM Uncertainty Quantification." arXiv:2507.07236v2

