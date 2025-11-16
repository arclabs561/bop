# Gaps Analysis and Integration Plan

## Critical Gaps Identified

### 1. **Probability Distribution Extraction** ⚠️ CRITICAL
**Problem**: The uncertainty module expects probability distributions `np.ndarray`, but BOP works with text results from MCP tools.

**Current State**:
- MCP tools return text results: `{"result": "text...", "source": "perplexity", ...}`
- Uncertainty module expects: `np.array([0.8, 0.2])` (probability distribution)

**Solution Needed**:
- Convert text results to probability distributions
- Options:
  - Use confidence scores from nodes: `[confidence, 1-confidence]` (binary)
  - Extract semantic similarity scores and normalize
  - Use LLM to generate probability distributions from text
  - Map text quality indicators to distributions

### 2. **Heuristic vs JSD-Based Uncertainty** ⚠️ HIGH PRIORITY
**Problem**: `orchestrator._estimate_epistemic_uncertainty` still uses heuristics, not JSD.

**Current State**:
```python
# Heuristic-based (orchestrator.py:978-1013)
epistemic = (source_uncertainty * source_factor * completeness_factor)
```

**Solution Needed**:
- Replace with JSD-based computation
- Aggregate multiple source predictions
- Compute epistemic uncertainty from disagreement

### 3. **Clique Uncertainty Not Using JSD** ⚠️ HIGH PRIORITY
**Problem**: `ContextTopology._compute_clique_trust` doesn't use JSD for uncertainty.

**Current State**:
- Uses simple averages: `avg_credibility`, `avg_confidence`
- No JSD-based epistemic uncertainty computation

**Solution Needed**:
- Add `compute_clique_uncertainty` method using JSD
- Integrate with existing trust computation

### 4. **Multi-Source Aggregation Not Using MUSE** ⚠️ MEDIUM PRIORITY
**Problem**: Results from multiple tools are synthesized but not aggregated using MUSE subset selection.

**Current State**:
- Tools are selected and executed
- Results are synthesized via LLM
- No uncertainty-aware subset selection

**Solution Needed**:
- Convert tool results to predictions
- Apply MUSE subset selection before synthesis
- Use aleatoric-aware weighting

### 5. **Pipeline Uncertainty Tracking Missing** ⚠️ MEDIUM PRIORITY
**Problem**: No tracking of uncertainty at each pipeline stage (operational vs output).

**Current State**:
- Uncertainty computed per node
- No stage-by-stage tracking
- No operational vs output distinction

**Solution Needed**:
- Add `PipelineUncertainty` dataclass
- Track uncertainty at each stage
- Distinguish operational vs output uncertainty

### 6. **Source Credibility Not Integrated** ⚠️ LOW PRIORITY
**Problem**: Source credibility scores exist but aren't used in uncertainty computation.

**Current State**:
- `ContextNode.credibility` tracks source trustworthiness
- Not used in JSD/MUSE computations

**Solution Needed**:
- Use credibility as confidence scores in MUSE
- Weight predictions by credibility
- Filter low-credibility sources

## Integration Plan

### Phase 1: Probability Distribution Extraction (CRITICAL)

**1.1 Create Helper Function**
```python
# src/bop/uncertainty.py
def extract_prediction_from_result(
    result: Dict[str, Any],
    node: Optional[ContextNode] = None
) -> np.ndarray:
    """
    Extract probability distribution from BOP result.
    
    Strategies (in order of preference):
    1. Use node confidence: [confidence, 1-confidence] (binary)
    2. Use source credibility: [credibility, 1-credibility]
    3. Use semantic similarity scores (if available)
    4. Default: [0.5, 0.5] (uniform)
    """
```

**1.2 Multi-Class Support**
- For multi-class scenarios, extract from relevance scores
- Use token importance or claim quality scores
- Normalize to probability distribution

### Phase 2: Replace Heuristics with JSD (HIGH PRIORITY)

**2.1 Update Orchestrator**
```python
# src/bop/orchestrator.py
from .uncertainty import (
    compute_epistemic_uncertainty_jsd,
    extract_prediction_from_result
)

def _estimate_epistemic_uncertainty_jsd(
    self,
    results: List[Dict[str, Any]],
    nodes: List[ContextNode]
) -> float:
    """
    Compute epistemic uncertainty using JSD from multiple results.
    """
    # Extract predictions
    predictions = []
    for result, node in zip(results, nodes):
        pred = extract_prediction_from_result(result, node)
        predictions.append(pred)
    
    # Compute epistemic uncertainty
    return compute_epistemic_uncertainty_jsd(predictions)
```

**2.2 Update ContextTopology**
```python
# src/bop/context_topology.py
from .uncertainty import (
    compute_epistemic_uncertainty_jsd,
    compute_aleatoric_uncertainty_entropy,
    compute_total_uncertainty
)

def compute_clique_uncertainty(self, nodes: Set[str]) -> Dict[str, float]:
    """
    Compute uncertainty metrics for a clique using JSD and entropy.
    """
    # Extract predictions from nodes
    predictions = []
    for node_id in nodes:
        node = self.nodes[node_id]
        # Convert to probability distribution
        pred = np.array([
            1.0 - node.epistemic_uncertainty,  # Confidence
            node.epistemic_uncertainty  # Uncertainty
        ])
        predictions.append(pred)
    
    # Compute uncertainties
    epistemic = compute_epistemic_uncertainty_jsd(predictions)
    aleatoric = compute_aleatoric_uncertainty_entropy(predictions)
    total = compute_total_uncertainty(epistemic, aleatoric, beta=0.5)
    
    return {
        "epistemic": epistemic,
        "aleatoric": aleatoric,
        "total": total
    }
```

### Phase 3: MUSE Integration (MEDIUM PRIORITY)

**3.1 Add MUSE to Result Aggregation**
```python
# src/bop/orchestrator.py
from .uncertainty import select_calibrated_subset_muse, extract_prediction_from_result

async def _aggregate_results_with_muse(
    self,
    tool_results: List[Dict[str, Any]],
    nodes: List[ContextNode]
) -> Dict[str, Any]:
    """
    Aggregate tool results using MUSE subset selection.
    """
    # Convert to predictions
    predictions = []
    confidence_scores = []
    
    for result, node in zip(tool_results, nodes):
        source_id = node.source
        pred = extract_prediction_from_result(result, node)
        confidence = node.confidence  # Use node confidence
        
        predictions.append((source_id, pred))
        confidence_scores.append(confidence)
    
    # Select calibrated subset
    selected_ids, epistemic, total = select_calibrated_subset_muse(
        predictions,
        confidence_scores,
        strategy="greedy"
    )
    
    # Filter results
    selected_results = [
        (r, n) for r, n in zip(tool_results, nodes)
        if n.source in selected_ids
    ]
    
    return {
        "selected_results": [r for r, _ in selected_results],
        "selected_nodes": [n for _, n in selected_results],
        "epistemic_uncertainty": epistemic,
        "total_uncertainty": total,
        "selected_sources": selected_ids
    }
```

### Phase 4: Pipeline Uncertainty Tracking (MEDIUM PRIORITY)

**4.1 Add PipelineUncertainty Dataclass**
```python
# src/bop/orchestrator.py
from dataclasses import dataclass

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

**4.2 Integrate into Research Flow**
- Track uncertainty at each stage
- Store in research results
- Display in CLI/Web UI

## Implementation Order

1. **Phase 1** (CRITICAL): Probability distribution extraction
2. **Phase 2** (HIGH): Replace heuristics with JSD
3. **Phase 3** (MEDIUM): MUSE integration
4. **Phase 4** (MEDIUM): Pipeline tracking

## Testing Strategy

1. **Unit Tests**: Test probability extraction from various result types
2. **Integration Tests**: Verify JSD replaces heuristics correctly
3. **E2E Tests**: Test MUSE selection improves calibration
4. **Regression Tests**: Ensure existing functionality still works

