# SSH Integration: Concrete Implementation Plan

## Executive Summary

Based on codebase review and research synthesis, this document provides concrete, actionable
implementation steps to integrate SSH theoretical insights into BOP. Each recommendation
includes specific file locations, function signatures, and test requirements.

## Context: What We're Building and Why

This implementation plan addresses four key insights from SSH research:

1. **Information Bottleneck for RAG**: Most retrieved content is noise. Principled filtering
   (IB) can achieve 2.5% compression without accuracy loss, addressing the "waste" component
   of the degradation triple.

2. **Adaptive Reasoning Depth**: Problems have minimum reasoning thresholds. Learning these
   thresholds per query type optimizes the "depth" component of the resource triple, avoiding
   unnecessary compute on simple queries while ensuring sufficient depth for complex ones.

3. **Resource Triple Metrics**: Explicit tracking of depth-width-coordination enables
   understanding of fundamental computational constraints. These are non-interchangeable
   resources - you can't "beat" the constraints, only optimize allocation.

4. **Logical Depth**: Bennett's logical depth formalizes "valuable, hard-earned knowledge"
   - information that requires significant computational effort. This connects to BOP's
   knowledge structure research goal of understanding the "shape of ideas."

Each feature addresses a specific aspect of the SSH theoretical framework while building on
BOP's existing architecture (MCP lazy evaluation, context topology, d-separation preservation).

## Current State Analysis

### What BOP Already Has

1. **Relevance Scoring** (`src/bop/provenance.py:158-249`)
   - `_compute_relevance_breakdown()` computes word overlap, semantic similarity, token matches
   - Used for provenance/matching, NOT for filtering before synthesis
   - Tests: `tests/test_relevance_breakdowns.py`

2. **Information Gain Tracking** (`src/bop/constraints.py:46-66`)
   - `ToolConstraint` has `information_gain` field (0-1 scale)
   - Constraint solver uses `min_information` threshold
   - NOT formal Information Bottleneck objective (no mutual information computation)

3. **Adaptive Schema Selection** (`src/bop/adaptive_quality.py:280-377`)
   - `AdaptiveQualityManager.get_adaptive_strategy()` learns schema selection
   - Tracks query type → schema performance
   - Does NOT track reasoning depth thresholds or implement early stopping

4. **Synthesis Filtering** (`src/bop/llm.py:378-420`)
   - `synthesize_tool_results()` filters only for `result` field existence
   - Truncates to 500 chars per result
   - NO relevance-based filtering, NO IB-based compression

5. **Context Topology** (`src/bop/context_topology.py`)
   - Computes Fisher Information estimate (heuristic)
   - Tracks cliques, Betti numbers, Euler characteristic
   - Does NOT compute logical depth

### Critical Gaps Identified

1. **No IB-based filtering before synthesis** - All results passed to LLM regardless of relevance
2. **No reasoning depth threshold tracking** - Fixed schema decomposition, no adaptive depth
3. **No early stopping** - Always completes all subproblems even if threshold met
4. **No resource triple metrics** - No explicit tracking of depth-width-coordination tradeoffs
5. **No logical depth computation** - Topology analysis doesn't compute Bennett's logical depth

## Priority 1: Information Bottleneck Filtering (High Impact, Medium Effort)

### Implementation

**File**: `src/bop/information_bottleneck.py` (NEW)

```python
"""
Information Bottleneck-based filtering for retrieval results.

Implements IB principle: max I(compressed; target) - beta * I(compressed; original)
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from .provenance import _compute_semantic_similarity

def compute_mutual_information_estimate(
    passage: str,
    target: str,
    method: str = "semantic_similarity"
) -> float:
    """
    Estimate I(passage; target) using semantic similarity.
    
    For true MI, would need: I(X;Y) = H(X) - H(X|Y)
    Heuristic: Use semantic similarity as proxy for mutual information.
    """
    if method == "semantic_similarity":
        return _compute_semantic_similarity(passage, target)
    # Future: Add entropy-based estimation
    return 0.0

def filter_with_information_bottleneck(
    retrieved_results: List[Dict[str, Any]],
    query: str,
    target_output: Optional[str] = None,
    beta: float = 0.5,
    min_mi: float = 0.3,
    max_results: Optional[int] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Filter retrieved results using Information Bottleneck principle.
    
    Objective: max I(compressed; target) - beta * I(compressed; original)
    
    Args:
        retrieved_results: List of tool results with 'result' field
        query: Original query
        target_output: Optional target output (if available from similar queries)
        beta: Tradeoff parameter (higher = more compression)
        min_mi: Minimum mutual information threshold
        max_results: Maximum number of results to return
    
    Returns:
        (filtered_results, metadata) where metadata includes:
        - compression_ratio: len(filtered) / len(original)
        - avg_mi: Average mutual information of filtered results
        - removed_count: Number of results filtered out
    """
    if not retrieved_results:
        return [], {"compression_ratio": 1.0, "avg_mi": 0.0, "removed_count": 0}
    
    # Compute MI for each result
    mi_scores = []
    for result in retrieved_results:
        result_text = result.get("result", "")
        if not result_text:
            mi_scores.append((result, 0.0))
            continue
        
        # Estimate I(result; query)
        mi_query = compute_mutual_information_estimate(result_text, query)
        
        # If target_output available, estimate I(result; target)
        if target_output:
            mi_target = compute_mutual_information_estimate(result_text, target_output)
            # Weighted: prefer results that match both query and target
            mi = 0.6 * mi_target + 0.4 * mi_query
        else:
            mi = mi_query
        
        mi_scores.append((result, mi))
    
    # Filter by minimum MI threshold
    filtered = [(r, mi) for r, mi in mi_scores if mi >= min_mi]
    
    # Sort by MI (highest first)
    filtered.sort(key=lambda x: x[1], reverse=True)
    
    # Apply max_results limit
    if max_results and len(filtered) > max_results:
        filtered = filtered[:max_results]
    
    filtered_results = [r for r, _ in filtered]
    avg_mi = np.mean([mi for _, mi in filtered]) if filtered else 0.0
    
    metadata = {
        "compression_ratio": len(filtered_results) / len(retrieved_results),
        "avg_mi": float(avg_mi),
        "removed_count": len(retrieved_results) - len(filtered_results),
        "beta": beta,
        "min_mi": min_mi,
    }
    
    return filtered_results, metadata
```

**Integration Point**: `src/bop/llm.py:378-420`

Modify `synthesize_tool_results()`:

```python
async def synthesize_tool_results(
    self,
    tool_results: List[Dict[str, Any]],
    subproblem: str,
    use_ib_filtering: bool = True,  # NEW
    ib_beta: float = 0.5,  # NEW
) -> str:
    """Synthesize results from multiple tools into coherent answer."""
    if not tool_results:
        return f"No results found for: {subproblem}"

    # Filter valid results
    valid_results = [r for r in tool_results if r and r.get("result")]

    if not valid_results:
        return f"No valid results found for: {subproblem}"

    # NEW: Apply IB filtering before synthesis
    if use_ib_filtering and len(valid_results) > 2:
        try:
            from .information_bottleneck import filter_with_information_bottleneck
            filtered_results, ib_metadata = filter_with_information_bottleneck(
                valid_results,
                query=subproblem,
                beta=ib_beta,
                min_mi=0.3,
                max_results=5,  # Limit to top 5 most relevant
            )
            if filtered_results:
                valid_results = filtered_results
                logger.debug(f"IB filtering: {ib_metadata['compression_ratio']:.2%} compression, "
                           f"removed {ib_metadata['removed_count']} results")
        except Exception as e:
            logger.warning(f"IB filtering failed: {e}, using all results")

    # Build synthesis prompt (unchanged)
    results_text = "\n\n".join(
        f"Tool: {r.get('tool', 'unknown')}\nResult: {r.get('result', '')[:500]}"
        for r in valid_results
    )
    # ... rest unchanged
```

**Tests**: `tests/test_information_bottleneck.py` (NEW)

```python
"""Tests for Information Bottleneck filtering."""

import pytest
from bop.information_bottleneck import (
    filter_with_information_bottleneck,
    compute_mutual_information_estimate,
)

def test_ib_filtering_removes_low_relevance():
    """Test that IB filtering removes low-relevance results."""
    results = [
        {"result": "D-separation is a graphical criterion for conditional independence"},
        {"result": "The weather is sunny today"},
        {"result": "D-separation helps identify d-separated variables in DAGs"},
    ]
    query = "What is d-separation?"
    
    filtered, metadata = filter_with_information_bottleneck(
        results, query, min_mi=0.3
    )
    
    assert len(filtered) < len(results)
    assert metadata["removed_count"] > 0
    assert metadata["compression_ratio"] < 1.0

def test_ib_filtering_preserves_high_relevance():
    """Test that IB filtering preserves high-relevance results."""
    results = [
        {"result": "D-separation is a graphical criterion"},
        {"result": "D-separation determines conditional independence"},
    ]
    query = "What is d-separation?"
    
    filtered, metadata = filter_with_information_bottleneck(
        results, query, min_mi=0.3
    )
    
    assert len(filtered) == len(results)  # Both should pass
    assert metadata["avg_mi"] > 0.5

def test_ib_filtering_with_target():
    """Test IB filtering with target output."""
    results = [
        {"result": "D-separation is used in causal inference"},
        {"result": "D-separation is a graphical method"},
    ]
    query = "What is d-separation?"
    target = "D-separation is a graphical criterion for conditional independence"
    
    filtered, metadata = filter_with_information_bottleneck(
        results, query, target_output=target
    )
    
    assert len(filtered) > 0
    assert metadata["avg_mi"] > 0.0
```

**Expected Impact**:
- 20-30% reduction in tokens passed to synthesis LLM
- Improved synthesis quality (less noise)
- Measurable via compression ratio and quality metrics

---

## Priority 2: Adaptive Reasoning Depth Allocation (High Impact, High Effort)

### Implementation

**File**: `src/bop/adaptive_quality.py` (EXTEND)

Add to `AdaptiveStrategy` dataclass:

```python
@dataclass
class AdaptiveStrategy:
    schema_selection: str
    expected_length: int
    should_use_research: bool
    tool_preferences: List[str]
    confidence: float
    # NEW FIELDS:
    reasoning_depth: int  # Estimated minimum reasoning depth (subproblems)
    early_stop_threshold: Optional[float] = None  # Quality threshold for early stopping
```

Add to `AdaptiveQualityManager`:

```python
# NEW: Track reasoning depth thresholds
self.query_type_to_depth: Dict[str, List[Tuple[int, float]]] = defaultdict(list)
# Format: (num_subproblems, quality_score)

def estimate_reasoning_depth(
    self,
    query: str,
    query_type: Optional[str] = None,
) -> int:
    """
    Estimate minimum reasoning depth (number of subproblems) for query.
    
    Based on learned patterns: queries that achieved high quality with N subproblems
    suggest N is the minimum threshold.
    """
    if query_type is None:
        query_type = self._classify_query(query)
    
    depth_data = self.query_type_to_depth.get(query_type, [])
    if not depth_data:
        # Default: use schema-based heuristic
        return 3  # Default decompose_and_synthesize uses 3-5
    
    # Find depth associated with high quality (score > 0.7)
    high_quality_depths = [depth for depth, score in depth_data if score > 0.7]
    if high_quality_depths:
        # Use median of high-quality depths as threshold
        return int(statistics.median(high_quality_depths))
    
    # Fallback: use minimum depth that achieved decent quality
    decent_depths = [depth for depth, score in depth_data if score > 0.6]
    if decent_depths:
        return min(decent_depths)
    
    return 3  # Default

def should_early_stop(
    self,
    current_quality: float,
    query_type: str,
    num_subproblems_completed: int,
) -> bool:
    """
    Determine if reasoning should stop early (threshold met).
    
    Returns True if:
    1. Current quality exceeds learned threshold for this query type
    2. Additional subproblems unlikely to improve quality significantly
    """
    depth_data = self.query_type_to_depth.get(query_type, [])
    if not depth_data:
        return False  # No data, continue
    
    # Find quality threshold for this depth
    matching_depths = [
        (depth, score) for depth, score in depth_data
        if depth == num_subproblems_completed
    ]
    if not matching_depths:
        return False
    
    # If current quality exceeds learned threshold, can stop
    avg_threshold = statistics.mean([score for _, score in matching_depths])
    if current_quality >= avg_threshold * 0.95:  # 95% of threshold
        return True
    
    return False

def update_from_evaluation(
    self,
    query: str,
    schema: str,
    used_research: bool,
    response_length: int,
    quality_score: float,
    num_subproblems: Optional[int] = None,  # NEW
):
    """Update learning from evaluation (EXTENDED)."""
    # ... existing code ...
    
    # NEW: Track reasoning depth
    if num_subproblems is not None:
        query_type = self._classify_query(query)
        self.query_type_to_depth[query_type].append((num_subproblems, quality_score))
        # Keep only last 50 entries per query type
        if len(self.query_type_to_depth[query_type]) > 50:
            self.query_type_to_depth[query_type] = self.query_type_to_depth[query_type][-50:]
```

**Integration Point**: `src/bop/orchestrator.py:261-524`

Modify `research_with_schema()` to support early stopping:

```python
async def research_with_schema(
    self,
    query: str,
    schema_name: str = "decompose_and_synthesize",
    max_tools_per_subproblem: int = 2,
    preserve_d_separation: bool = True,
    prior_beliefs: Optional[List[Dict[str, Any]]] = None,
    adaptive_manager: Optional[Any] = None,  # NEW
) -> Dict[str, Any]:
    """Conduct research using structured schema (EXTENDED)."""
    # ... existing decomposition code ...
    
    # NEW: Get adaptive reasoning depth estimate
    estimated_depth = None
    if adaptive_manager:
        estimated_depth = adaptive_manager.estimate_reasoning_depth(query)
        logger.info(f"Estimated reasoning depth: {estimated_depth} subproblems")
    
    subsolutions = []
    conditioning_set = set()
    
    for i, subproblem in enumerate(decomposition):
        # NEW: Check for early stopping
        if adaptive_manager and i > 0:
            # Estimate current quality (heuristic: based on subsolution quality)
            current_quality = self._estimate_current_quality(subsolutions)
            query_type = adaptive_manager._classify_query(query)
            
            if adaptive_manager.should_early_stop(
                current_quality, query_type, len(subsolutions)
            ):
                logger.info(f"Early stopping: quality threshold met after {len(subsolutions)} subproblems")
                break
        
        # ... existing subproblem processing ...
```

**Tests**: `tests/test_adaptive_reasoning_depth.py` (NEW)

```python
"""Tests for adaptive reasoning depth allocation."""

import pytest
from bop.adaptive_quality import AdaptiveQualityManager
from bop.quality_feedback import QualityFeedbackLoop

def test_estimate_reasoning_depth():
    """Test reasoning depth estimation."""
    feedback = QualityFeedbackLoop()
    manager = AdaptiveQualityManager(feedback)
    
    # Add learning data
    for _ in range(5):
        manager.update_from_evaluation(
            query="What is d-separation?",
            schema="decompose_and_synthesize",
            used_research=True,
            response_length=200,
            quality_score=0.8,
            num_subproblems=3,
        )
    
    depth = manager.estimate_reasoning_depth("What is d-separation?")
    assert depth == 3

def test_early_stopping():
    """Test early stopping logic."""
    feedback = QualityFeedbackLoop()
    manager = AdaptiveQualityManager(feedback)
    
    # Add learning: 3 subproblems achieves 0.8 quality
    manager.update_from_evaluation(
        query="What is trust?",
        schema="decompose_and_synthesize",
        used_research=True,
        response_length=200,
        quality_score=0.8,
        num_subproblems=3,
    )
    
    # Should stop early if quality threshold met
    should_stop = manager.should_early_stop(
        current_quality=0.78,  # 95% of 0.8 = 0.76
        query_type="analytical",
        num_subproblems_completed=3,
    )
    assert should_stop is True
```

**Expected Impact**:
- 15-25% reduction in compute for queries that meet quality threshold early
- Better resource allocation (more depth for complex queries, less for simple)
- Measurable via subproblems completed vs. quality achieved

---

## Priority 3: Resource Triple Metrics (Medium Impact, Low Effort)

### Implementation

**File**: `src/bop/orchestrator.py` (EXTEND)

Add to `research_with_schema()` return value:

```python
# NEW: Resource triple metrics
resource_metrics = {
    "depth": len(subsolutions),  # Reasoning depth (subproblems)
    "width": sum(len(s.get("tools_used", [])) for s in subsolutions),  # Parallelism (tools)
    "coordination": len(set(tool for s in subsolutions for tool in s.get("tools_used", []))),  # Unique tools
    "total_tokens": sum(len(s.get("synthesis", "")) for s in subsolutions),  # Total compute
}

# NEW: Degradation triple metrics
degradation_metrics = {
    "noise": 1.0 - (fisher_info if fisher_info > 0 else 0.5),  # Inverse of Fisher Information
    "loss": pipeline_uncertainty.synthesis,  # Synthesis uncertainty
    "waste": 1.0 - (len(filtered_results) / len(all_results) if all_results else 1.0),  # Compression waste
}

return {
    # ... existing fields ...
    "resource_triple": resource_metrics,
    "degradation_triple": degradation_metrics,
}
```

**Documentation**: Update `ARCHITECTURE.md` with explicit triple principle framing.

**Tests**: `tests/test_resource_triple_metrics.py` (NEW)

```python
"""Tests for resource triple metrics."""

import pytest
from bop.orchestrator import StructuredOrchestrator

@pytest.mark.asyncio
async def test_resource_triple_tracking():
    """Test that resource triple metrics are tracked."""
    orchestrator = StructuredOrchestrator()
    
    result = await orchestrator.research_with_schema(
        "What is d-separation?",
        schema_name="decompose_and_synthesize",
    )
    
    assert "resource_triple" in result
    assert "depth" in result["resource_triple"]
    assert "width" in result["resource_triple"]
    assert "coordination" in result["resource_triple"]
    
    assert "degradation_triple" in result
    assert "noise" in result["degradation_triple"]
    assert "loss" in result["degradation_triple"]
    assert "waste" in result["degradation_triple"]
```

**Expected Impact**:
- Clearer understanding of resource tradeoffs
- Better design decisions based on explicit metrics
- Easier to communicate architectural choices

---

## Priority 4: Logical Depth Computation (Low Impact, Medium Effort)

### Implementation

**File**: `src/bop/context_topology.py` (EXTEND)

Add method to `ContextTopology`:

```python
def compute_logical_depth_estimate(
    self,
    node_id: str,
    compression_ratio: float = 0.1,
) -> float:
    """
    Estimate Bennett's logical depth for a context node.
    
    Logical depth = computational effort to produce string from compressed description.
    
    Heuristic approximation:
    - High trust + high coherence = high logical depth (hard-earned knowledge)
    - Low trust + low coherence = low logical depth (easily produced)
    
    Args:
        node_id: Node identifier
        compression_ratio: Assumed compression ratio for description
    
    Returns:
        Estimated logical depth (0-1 normalized)
    """
    if node_id not in self.nodes:
        return 0.0
    
    node = self.nodes[node_id]
    
    # Logical depth correlates with:
    # 1. Trust (high trust = valuable knowledge)
    # 2. Coherence (high coherence = structured knowledge)
    # 3. Verification count (more verification = more effort)
    
    trust_component = node.trust_score
    coherence_component = node.coherence_score if hasattr(node, 'coherence_score') else 0.5
    verification_component = min(1.0, node.verification_count / 5.0)  # Normalize
    
    # Weighted combination
    logical_depth = (
        0.4 * trust_component +
        0.3 * coherence_component +
        0.3 * verification_component
    )
    
    # Apply compression ratio (more compression = more depth required)
    logical_depth *= (1.0 + compression_ratio)
    
    return min(1.0, logical_depth)
```

**Integration**: Add to topology analysis in `research_with_schema()`.

**Tests**: `tests/test_logical_depth.py` (NEW)

**Expected Impact**:
- Formal measure of knowledge value
- Better understanding of which knowledge structures are "deep"
- Connection to algorithmic information theory

---

## Implementation Timeline

### Week 1: Priority 1 (IB Filtering)
- [ ] Create `src/bop/information_bottleneck.py`
- [ ] Integrate into `synthesize_tool_results()`
- [ ] Write tests
- [ ] Measure compression ratio and quality impact

### Week 2: Priority 2 (Adaptive Depth)
- [ ] Extend `AdaptiveStrategy` and `AdaptiveQualityManager`
- [ ] Integrate early stopping into `research_with_schema()`
- [ ] Write tests
- [ ] Measure compute savings

### Week 3: Priority 3 (Resource Triple)
- [ ] Add metrics to `research_with_schema()` return
- [ ] Update `ARCHITECTURE.md`
- [ ] Write tests

### Week 4: Priority 4 (Logical Depth)
- [ ] Add `compute_logical_depth_estimate()` to `ContextTopology`
- [ ] Integrate into topology analysis
- [ ] Write tests

## Success Metrics

1. **IB Filtering**: 20-30% token reduction, quality maintained or improved
2. **Adaptive Depth**: 15-25% compute reduction for simple queries, quality maintained
3. **Resource Triple**: Metrics tracked and documented
4. **Logical Depth**: Computed for all topology nodes, correlates with trust/coherence

## Testing Strategy

1. **Unit Tests**: Each new function/module
2. **Integration Tests**: End-to-end with real queries
3. **Property Tests**: Invariants (compression ratio < 1.0, depth >= 1, etc.)
4. **Performance Tests**: Measure token/compute savings

## Risk Mitigation

1. **IB Filtering**: Fallback to all results if filtering fails
2. **Early Stopping**: Conservative thresholds (95% of learned threshold)
3. **Metrics**: Optional (don't break existing functionality)
4. **Logical Depth**: Heuristic (document as approximation)

