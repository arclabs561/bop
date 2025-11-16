# Developer Questions Answered

This document answers common questions from developers exploring BOP for the first time, based on actual codebase exploration.

## 1. What's the simplest query that exercises the full stack?

**Answer**: The simplest end-to-end query that exercises all major components:

```python
from bop.agent import KnowledgeAgent

agent = KnowledgeAgent(enable_quality_feedback=True)
response = await agent.chat(
    "What is d-separation?",
    use_schema="decompose_and_synthesize",
    use_research=True,
)
```

**What this exercises**:
- Schema-guided decomposition (`decompose_and_synthesize`)
- Research via MCP tools (Perplexity, Firecrawl, etc.)
- Tool selection (heuristic or constraint-based)
- Topology analysis (clique complexes, trust metrics)
- Synthesis with Information Bottleneck filtering
- Quality feedback loop
- Adaptive learning updates
- Progressive disclosure tiers

**See also**: `tests/test_ssh_e2e.py::test_ssh_e2e_full_workflow()` for a complete example.

## 2. How do you debug when research fails but the agent continues?

**Answer**: Research failures are handled gracefully with error tracking:

```python
# In agent.py chat() method (lines 129-147)
if use_research:
    try:
        research_result = await self.orchestrator.research_with_schema(...)
        response["research_conducted"] = True
        response["research"] = research_result
    except Exception as e:
        # If research fails, continue without it
        response["research_conducted"] = False
        response["research_error"] = str(e)  # Error message captured
```

**Debugging steps**:
1. Check `response.get("research_error")` for the exception message
2. Check `response.get("research_conducted")` to see if research succeeded
3. Tool failures in orchestrator are logged but don't stop processing (see `orchestrator.py:500-503`)
4. Use logging: `logger.debug()` statements throughout show tool selection and failures

**Test coverage**: `tests/test_e2e_chaos_engineering.py::test_e2e_chaos_research_tool_failure()` demonstrates expected behavior.

## 3. What metrics show adaptive learning is actually helping?

**Answer**: Adaptive learning provides several metrics via `AdaptiveQualityManager.get_performance_insights()`:

**Key Metrics**:
- **Query Type Performance**: Mean scores by query type (factual, procedural, analytical, etc.)
- **Schema Recommendations**: Best schema per query type with confidence scores
- **Research Effectiveness**: Improvement delta when research is enabled vs. disabled
- **Optimal Response Lengths**: Learned target lengths per query type
- **Reasoning Depth Thresholds**: Minimum subproblems needed for quality

**Example**:
```python
insights = agent.adaptive_manager.get_performance_insights()
# Returns:
# {
#   "query_type_performance": {"factual": {"mean": 0.75, "count": 15}},
#   "schema_recommendations": {"factual": {"schema": "chain_of_thought", "score": 0.75}},
#   "research_effectiveness": {"factual": {"improvement": 0.05}},
# }
```

**Validation**: Tests in `tests/test_adaptive_quality.py` and `tests/test_hierarchical_deep_analysis.py::test_actual_adaptive_learning_improvement()` verify learning occurs.

**CLI Command**: `bop quality --adaptive` shows these insights in a formatted table.

## 4. When should you use constraint solver vs. heuristics?

**Answer**: The constraint solver is used when `BOP_USE_CONSTRAINTS=true` and PySAT is available. The system automatically falls back to heuristics if constraints fail.

**When to use constraints**:
- **Complex queries** with multiple subproblems requiring optimal tool selection
- **Cost optimization** is important (constraints minimize cost while meeting information requirements)
- **Complex dependencies** between tools (e.g., search before scrape)
- **Budget constraints** need to be enforced

**When heuristics are sufficient**:
- **Simple queries** with obvious tool selection
- **Real-time constraints** where solver overhead isn't worth it
- **Development/debugging** where you want predictable behavior

**Implementation** (see `orchestrator.py:296-308`):
```python
if self.use_constraints and self.constraint_solver:
    tools = self._select_tools_with_constraints(...)
    if not tools:  # Automatic fallback
        tools = self.tool_selector.select_tools(subproblem)
else:
    tools = self.tool_selector.select_tools(subproblem)
```

**Recommendation**: Start with heuristics (default), enable constraints for production workloads where cost/latency optimization matters. See `ARCHITECTURE.md:403-410` for detailed guidance.

## 5. How do you validate that trust metrics are calibrated correctly?

**Answer**: Trust calibration is validated through multiple mechanisms:

**1. Ground Truth Datasets**:
- `datasets/calibration_ground_truth.json` contains known scenarios
- Tests in `tests/test_calibration_ground_truth.py` verify ECE (Expected Calibration Error) computation
- Scripts in `scripts/evaluate_with_datasets.py` run calibration evaluation

**2. Calibration Metrics**:
- **ECE (Expected Calibration Error)**: Measures how well confidence matches accuracy
  - Excellent: < 0.1
  - Good: 0.1 - 0.2
  - Needs improvement: > 0.2
- **Brier Score**: Measures prediction accuracy
- **Calibration Improvement**: Tracks ECE reduction over time

**3. Validation Tests**:
- `tests/test_hard_evaluations.py::test_trust_calibration_accuracy()` verifies high-quality sources have higher credibility
- `tests/test_calibration_ground_truth.py` tests overconfident/underconfident/well-calibrated scenarios
- `tests/test_hard_theoretical_claims.py::test_trust_calibration_error_computation()` validates ECE computation

**4. Continuous Monitoring**:
- Calibration error is included in `response["research"]["topology"]["trust_summary"]["calibration_error"]`
- Adaptive learning tracks calibration improvements
- `bop quality` command shows calibration metrics

**Usage**:
```python
# Check calibration in response
topology = response["research"]["topology"]
calibration_error = topology["trust_summary"]["calibration_error"]
if calibration_error > 0.2:
    print("Warning: Trust scores may be unreliable")
```

## Additional Insights

### Error Handling Philosophy

BOP follows a "graceful degradation" philosophy:
- Research failures → continue without research
- Tool failures → try other tools, continue with partial results
- Topology analysis failures → log error, continue without topology metrics
- LLM failures → fall back to heuristic synthesis

This ensures the system remains usable even when components fail.

### Performance Considerations

**Constraint Solver Overhead**:
- Constraint solving adds ~10-50ms per subproblem
- Worth it for complex queries with 5+ subproblems
- Not worth it for simple queries with 1-2 subproblems

**Adaptive Learning Overhead**:
- Learning updates are asynchronous (don't block responses)
- Persistence happens in background
- Initial load from history is one-time cost

**Topology Analysis Cost**:
- Clique computation: O(n²) in worst case, but typically O(n) for sparse graphs
- Betti numbers: Graph-level approximation (fast)
- Fisher Information: Heuristic estimate (fast)

### Testing Strategy

BOP uses a comprehensive testing strategy:
- **Unit tests**: Individual components (`test_*.py`)
- **Integration tests**: Component interactions (`test_*_integration.py`)
- **E2E tests**: Full workflows (`test_e2e_*.py`)
- **Property-based tests**: Invariants (`test_*_property_based.py`)
- **Chaos engineering**: Failure scenarios (`test_e2e_chaos_engineering.py`)
- **Mutation testing**: Test quality (`test-mutate`)

This multi-layered approach ensures reliability across different failure modes.

