# Ambient Work Analysis: Trust/Uncertainty in Knowledge Graphs (2024-2025)

## What's Actually Being Built

### 1. unKR Library (SIGIR 2024)

**What it is**: PyTorch Lightning-based library for uncertain KG reasoning
**Key features**:
- Modular architecture: Data Processor, Model Hub, Trainer, Evaluator, Controller
- Two tasks: **Confidence prediction** (MSE/MAE) and **Link prediction** (Hits@k, MRR)
- Models: BEURrE, FocusE, GTransE, PASSLEAF, UKGE, UKGsE, UPGAT, GMUC
- Data format: `(h, r, t, s)` where `s` is confidence score [0,1]

**What we can learn**:
- Confidence scores are **first-class citizens** in the data model
- Evaluation split: confidence prediction vs link prediction
- High-confidence triples (>0.7) used for link prediction testing
- Modular design enables extensibility

### 2. UaG Framework (Uncertainty Aware KG Reasoning)

**What it is**: Conformal prediction framework for KG-LLM systems
**Key innovations**:
- **Error rate control**: Formal guarantees on coverage
- **Multi-step reasoning**: Handles error propagation through reasoning chains
- **Empirical Coverage Rate (ECR)**: Measures actual vs target error rates
- **Average Prediction Set Size (APSS)**: Efficiency metric

**What works**:
- 40% reduction in prediction set size vs baselines
- Satisfies uncertainty constraints while maintaining reasonable set sizes
- Tested on multi-hop KG QA datasets

**What we can learn**:
- Conformal prediction provides **formal guarantees** (not just heuristics)
- Multi-step reasoning requires explicit error propagation
- Production systems need **calibrated confidence** (not just raw scores)

### 3. TRAIL Framework (Temporal Reasoning with Adaptive Inference)

**What it is**: Continual confidence evaluation and refinement
**Key features**:
- **Dynamic confidence scores**: Updated as evidence accumulates
- **Threshold-based pruning**: Low-confidence facts filtered out
- **Evidence-driven updates**: Confidence changes with new information

**What we can learn**:
- Trust/confidence must be **temporal** (not static)
- Continuous refinement is essential
- Threshold-based filtering is practical

### 4. Production Patterns (2024)

**Common implementations**:
1. **Confidence scores** attached to facts (0-1 scale)
2. **Schema validation** rules (prevent logical inconsistencies)
3. **Provenance tracking** (which sources contributed)
4. **Multi-source aggregation** (weighted by source trust)
5. **Threshold-based inclusion** (only high-confidence facts)
6. **Graph databases** with custom schema fields (Neo4j, etc.)

**What works in practice**:
- Start simple: confidence scores + schema validation
- Layer sophistication: conformal prediction, uncertainty decomposition
- Hybrid human-AI: human verification for high-impact facts
- Regular audits: recalibrate thresholds over time

## Key Insights

### What's Actually Working

1. **Confidence scores are the standard** - Every production system uses them
2. **Schema validation is essential** - Prevents obvious errors
3. **Provenance matters** - Track sources for accountability
4. **Threshold-based filtering** - Practical quality control
5. **Modular architectures** - Enable extensibility

### What's Still Theoretical

1. **Full epistemic/aleatoric decomposition** - Most systems use total uncertainty
2. **Explainable uncertainty** - Why is the model uncertain? (rarely implemented)
3. **Complex trust propagation** - Simple heuristics work better than complex models
4. **Temporal trust dynamics** - Most systems assume static trust

### What's Emerging

1. **Conformal prediction** - Moving from theory to practice (UaG)
2. **Multi-step error propagation** - Critical for reasoning chains
3. **Calibration** - Ensuring confidence aligns with accuracy
4. **Uncertainty-aware retrieval** - Using uncertainty to guide KG queries

## Implications for Our Implementation

### What We Should Do

1. **Confidence scores as core** - Already integrated in ContextNode ✓
2. **Schema validation** - Add consistency checking
3. **Provenance tracking** - Track sources (already have source field)
4. **Threshold-based filtering** - Use in attractor basin selection ✓
5. **Modular design** - Already have this ✓

### What We Should Add

1. **Calibration monitoring** - Track ECE (Expected Calibration Error)
2. **Multi-step error propagation** - For reasoning chains
3. **Conformal prediction** - For formal guarantees (future work)
4. **Temporal confidence updates** - As evidence accumulates

### What We Should Avoid

1. **Over-engineering** - Start simple, add complexity as needed
2. **Theoretical purity** - Practical heuristics often work better
3. **Binary trust** - Use continuous scores (we do this ✓)
4. **Ignoring provenance** - Track sources (we do this ✓)

## Testing Strategy

Based on ambient work, we should test:

1. **Confidence prediction** - Can we predict confidence accurately?
2. **Link prediction** - Can we predict missing links?
3. **Calibration** - Do confidence scores align with accuracy?
4. **Adversarial detection** - Can we identify low-trust clusters?
5. **Multi-step reasoning** - Does trust propagate correctly?

## Integration Points

Our current implementation aligns well with ambient work:

- ✓ Confidence scores in nodes
- ✓ Trust-aware clique computation
- ✓ Adversarial pattern detection
- ✓ Source credibility tracking
- ✓ Trust propagation with decay

**What to refine**:
- Add calibration monitoring
- Add schema validation
- Add temporal confidence updates
- Consider conformal prediction for formal guarantees

