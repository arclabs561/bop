# SSH Integration: Refined Next Steps

## Summary

After reviewing BOP's tests and implementation, we've identified concrete integration opportunities for SSH theoretical insights. This document provides prioritized, actionable next steps with specific code locations and test requirements.

## Key Findings from Codebase Review

### What Works Well
- ✅ Relevance scoring infrastructure exists (`provenance.py`)
- ✅ Adaptive learning framework exists (`adaptive_quality.py`)
- ✅ Constraint solver has information gain tracking (`constraints.py`)
- ✅ Topology analysis provides Fisher Information estimates (`context_topology.py`)

### Critical Gaps
- ❌ No IB-based filtering before synthesis (all results passed to LLM)
- ❌ No reasoning depth threshold tracking (fixed schema decomposition)
- ❌ No early stopping (always completes all subproblems)
- ❌ No resource triple metrics (implicit but not explicit)
- ❌ No logical depth computation (topology analysis doesn't compute it)

## Recommended Implementation Order

### 1. Information Bottleneck Filtering (START HERE)

**Why First**: 
- Direct application of research findings (arXiv 2406.01549)
- High impact (20-30% token reduction)
- Medium effort (new module, integrate into existing synthesis)
- Low risk (fallback to all results if filtering fails)

**Concrete Steps**:
1. Create `src/bop/information_bottleneck.py` with `filter_with_information_bottleneck()`
2. Modify `src/bop/llm.py:synthesize_tool_results()` to apply IB filtering
3. Add tests in `tests/test_information_bottleneck.py`
4. Measure compression ratio and quality impact

**Files to Modify**:
- `src/bop/llm.py` (line 378-420)
- `src/bop/orchestrator.py` (line 490-503, pass IB metadata)

**Success Criteria**:
- 20-30% compression without quality degradation
- Measurable via `compression_ratio` and `avg_mi` in metadata

### 2. Adaptive Reasoning Depth Allocation

**Why Second**:
- Addresses SSH core insight (minimum reasoning thresholds)
- High impact (15-25% compute reduction)
- High effort (extends adaptive learning framework)
- Medium risk (early stopping could miss important information)

**Concrete Steps**:
1. Extend `AdaptiveStrategy` dataclass with `reasoning_depth` and `early_stop_threshold`
2. Add `estimate_reasoning_depth()` and `should_early_stop()` to `AdaptiveQualityManager`
3. Modify `research_with_schema()` to support early stopping
4. Track `num_subproblems` in `update_from_evaluation()`

**Files to Modify**:
- `src/bop/adaptive_quality.py` (lines 20-30, 280-377, 379-556)
- `src/bop/orchestrator.py` (lines 201-232, 261-524)

**Success Criteria**:
- Early stopping when quality threshold met
- Reduced compute for simple queries, maintained quality for complex

### 3. Resource Triple Metrics

**Why Third**:
- Low effort (add metrics to existing return structure)
- Medium impact (theoretical clarity, design guidance)
- Low risk (optional metrics, don't break existing functionality)

**Concrete Steps**:
1. Add `resource_triple` and `degradation_triple` to `research_with_schema()` return
2. Update `ARCHITECTURE.md` with explicit triple principle framing
3. Add tests for metrics tracking

**Files to Modify**:
- `src/bop/orchestrator.py` (lines 600-650, add to return dict)
- `ARCHITECTURE.md` (add "Resource Triple Framework" section)

**Success Criteria**:
- Metrics tracked and documented
- Clearer understanding of resource tradeoffs

### 4. Logical Depth Computation

**Why Fourth**:
- Low impact (nice-to-have, not critical for core functionality)
- Medium effort (new computation, integrate into topology)
- Low risk (heuristic approximation, doesn't affect core logic)

**Concrete Steps**:
1. Add `compute_logical_depth_estimate()` to `ContextTopology`
2. Integrate into topology analysis in `research_with_schema()`
3. Add tests

**Files to Modify**:
- `src/bop/context_topology.py` (add new method)
- `src/bop/orchestrator.py` (add to topology metrics)

**Success Criteria**:
- Logical depth computed for all nodes
- Correlates with trust/coherence as expected

## Immediate Next Actions

### This Week: IB Filtering Implementation

1. **Create module** (`src/bop/information_bottleneck.py`):
   ```bash
   # Copy implementation from SSH_IMPLEMENTATION_PLAN.md
   ```

2. **Integrate into synthesis**:
   - Modify `src/bop/llm.py:synthesize_tool_results()`
   - Add `use_ib_filtering` parameter (default True)
   - Add error handling (fallback to all results)

3. **Write tests**:
   - `tests/test_information_bottleneck.py`
   - Test filtering removes low-relevance results
   - Test filtering preserves high-relevance results
   - Test with target output

4. **Measure impact**:
   - Run on sample queries
   - Track compression ratio
   - Compare quality scores (before/after)

### Next Week: Adaptive Depth

1. **Extend adaptive learning**:
   - Add `reasoning_depth` to `AdaptiveStrategy`
   - Add `estimate_reasoning_depth()` method
   - Add `should_early_stop()` method

2. **Integrate early stopping**:
   - Modify `research_with_schema()` to check for early stop
   - Track `num_subproblems` in evaluations

3. **Write tests**:
   - `tests/test_adaptive_reasoning_depth.py`
   - Test depth estimation
   - Test early stopping logic

## Testing Strategy

### Unit Tests
- Each new function/module
- Test edge cases (empty results, single result, etc.)
- Test fallback behavior

### Integration Tests
- End-to-end with real queries
- Compare before/after metrics
- Verify quality maintained or improved

### Property Tests
- Compression ratio < 1.0
- Depth >= 1
- Early stop only when threshold met

### Performance Tests
- Measure token/compute savings
- Track quality scores
- Compare to baseline

## Risk Mitigation

1. **IB Filtering**: 
   - Fallback to all results if filtering fails
   - Conservative `min_mi` threshold (0.3)
   - Log warnings, don't fail silently

2. **Early Stopping**:
   - Conservative thresholds (95% of learned threshold)
   - Only stop after at least 2 subproblems
   - Log early stop decisions

3. **Metrics**:
   - Optional (don't break existing functionality)
   - Default values if computation fails

4. **Logical Depth**:
   - Heuristic (document as approximation)
   - Don't use for critical decisions

## Success Metrics

### IB Filtering
- ✅ 20-30% token reduction
- ✅ Quality maintained or improved
- ✅ Compression ratio tracked

### Adaptive Depth
- ✅ 15-25% compute reduction for simple queries
- ✅ Quality maintained for complex queries
- ✅ Early stopping working correctly

### Resource Triple
- ✅ Metrics tracked
- ✅ Documented in ARCHITECTURE.md
- ✅ Used for design decisions

### Logical Depth
- ✅ Computed for all nodes
- ✅ Correlates with trust/coherence
- ✅ Documented as heuristic

## Documentation Updates

1. **ARCHITECTURE.md**:
   - Add "Resource Triple Framework" section
   - Document IB filtering integration
   - Document adaptive reasoning depth

2. **AGENTS.md**:
   - Update orchestrator description
   - Document new parameters

3. **README.md**:
   - Mention IB filtering (if user-visible)
   - Document new metrics (if exposed)

## Questions to Resolve

1. **IB Filtering**: Should `use_ib_filtering` be user-configurable or always-on?
2. **Early Stopping**: Should early stop be user-configurable or automatic?
3. **Metrics**: Should resource triple metrics be exposed to users or internal only?
4. **Logical Depth**: Should logical depth be used for ranking/selection or just analysis?

## References

- `SSH_THEORETICAL_SYNTHESIS.md` - Research findings and opportunities
- `SSH_IMPLEMENTATION_PLAN.md` - Detailed implementation plan with code
- `ARCHITECTURE.md` - Current architecture documentation
- `tests/test_adaptive_quality.py` - Existing adaptive learning tests
- `tests/test_relevance_breakdowns.py` - Existing relevance tests

