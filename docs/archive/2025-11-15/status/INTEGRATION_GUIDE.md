# Integration Guide: Trust & Uncertainty Based on Ambient Work

## What We Learned from Ambient Work (2024-2025)

### Key Production Patterns

1. **Confidence Scores as First-Class Citizens**
   - Every production system uses confidence scores (0-1 scale)
   - Scores attached to facts, not just edges
   - High-confidence triples (>0.7) used for critical operations

2. **Schema Validation**
   - Simple validation rules prevent obvious errors
   - Domain-specific schemas in production
   - Violations tracked but don't block (flag for review)

3. **Temporal Confidence Updates**
   - Confidence changes as evidence accumulates (TRAIL pattern)
   - Bayesian-style updates: increase with supporting evidence, decrease with contradictions
   - Continuous refinement is essential

4. **Calibration Monitoring**
   - Expected Calibration Error (ECE) tracks alignment between confidence and accuracy
   - Critical for production systems
   - Enables trust-aware decision making

5. **Provenance Tracking**
   - Track which sources contributed to each claim
   - Essential for accountability and debugging
   - Enables source-level credibility assessment

## What We Integrated

### 1. Confidence Scores in ContextNode

```python
node = ContextNode(
    id="n1",
    content="Claim",
    source="perplexity",
    credibility=0.8,      # Source trustworthiness
    confidence=0.7,        # Structural support
    epistemic_uncertainty=0.3,
    aleatoric_uncertainty=0.2,
)
```

### 2. Schema Consistency Checking

```python
violations = topology.check_schema_consistency(node)
# Returns list of violation messages
# Violations tracked in topology.schema_violations
```

### 3. Temporal Confidence Updates

```python
# Update confidence based on new evidence
topology.update_confidence_from_evidence(
    node_id="n1",
    new_evidence=True,      # Evidence supports claim
    evidence_quality=0.8,   # Quality of evidence
)
```

### 4. Calibration Tracking

```python
# Automatically tracks (predicted_confidence, actual_outcome)
# Computes ECE in trust summary
summary = topology._get_trust_summary()
print(summary["calibration_error"])  # Expected Calibration Error
```

### 5. Trust-Aware Attractor Basins

```python
# Filter basins by trust threshold
basins = topology.get_attractor_basins(min_trust=0.6)
# Only returns high-trust, coherent knowledge clusters
```

## Testing Strategy

Based on ambient work, we test:

1. **Confidence Prediction** - Can we predict confidence accurately?
2. **Link Prediction** - Can we predict missing links?
3. **Calibration** - Do confidence scores align with accuracy?
4. **Adversarial Detection** - Can we identify low-trust clusters?
5. **Multi-step Reasoning** - Does trust propagate correctly?

See `tests/test_trust_integration.py` for examples.

## Usage Examples

### Basic Trust-Aware Topology

```python
from bop.context_topology import ContextTopology, ContextNode

topology = ContextTopology()

# Add nodes with trust information
node1 = ContextNode(
    id="n1",
    content="High-confidence claim",
    source="trusted_source",
    credibility=0.9,
    confidence=0.8,
)
topology.add_node(node1)

# Check schema consistency
violations = topology.check_schema_consistency(node1)

# Update confidence from evidence
topology.update_confidence_from_evidence("n1", new_evidence=True, evidence_quality=0.8)

# Get trust summary (includes calibration)
summary = topology._get_trust_summary()
print(f"Calibration error: {summary['calibration_error']}")
print(f"Schema violations: {summary['schema_violations']}")
```

### Trust-Aware Clique Computation

```python
# Compute cliques (automatically includes trust metrics)
cliques = topology.compute_cliques()

# Get trust-aware attractor basins
basins = topology.get_attractor_basins(min_trust=0.6, min_coherence=0.5)
```

### Integration with Orchestrator

The orchestrator automatically:
- Checks schema consistency for new nodes
- Tracks confidence predictions for calibration
- Uses trust-aware filtering in attractor basins

See `src/bop/orchestrator.py` for implementation.

## What's Next (Future Work)

Based on ambient work, potential enhancements:

1. **Conformal Prediction** - For formal guarantees on error rates (UaG pattern)
2. **Multi-step Error Propagation** - Track uncertainty through reasoning chains
3. **Domain-Specific Schemas** - Expand schema validation beyond placeholders
4. **Source Aggregation** - Weighted aggregation from multiple sources
5. **Threshold-Based Filtering** - Automatic filtering of low-confidence facts

## References

- **unKR Library** (SIGIR 2024): PyTorch Lightning-based uncertain KG reasoning
- **UaG Framework**: Conformal prediction for KG-LLM systems
- **TRAIL Framework**: Temporal confidence updates and refinement
- **Production Patterns**: Confidence scores, schema validation, provenance tracking

See `AMBIENT_WORK_ANALYSIS.md` for detailed analysis.

