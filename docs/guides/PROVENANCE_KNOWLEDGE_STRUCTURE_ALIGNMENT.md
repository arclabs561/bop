# Provenance Features: Knowledge Structure Research Alignment

## Overview

All provenance features in BOP are designed to support the core purpose: **Knowledge Structure Research**. This document explains how each feature aligns with BOP's theoretical foundations.

## Theoretical Foundations

BOP's core purpose is understanding the "shape of ideas" through:
1. **Topological Analysis**: Clique complexes, d-separation, attractor basins
2. **Information Geometry**: Fisher Information, statistical manifolds
3. **Trust/Uncertainty Modeling**: Source credibility, confidence calibration
4. **Causal Structure Preservation**: D-separation via MCP lazy evaluation

## Provenance Feature Alignment

### 1. Token-Level Provenance

**Purpose**: Track which query tokens matched which document tokens.

**Knowledge Structure Support**:
- **Semantic Structure Mapping**: Token matches reflect semantic relationships in the knowledge graph
- **Information Geometry**: High-quality token matches indicate strong structure (high Fisher Information)
- **Clique Formation**: Multiple sources with similar token matches form coherent cliques
- **D-Separation Preservation**: Token matching only links semantically related concepts (no spurious connections)

**Implementation**:
- Levenshtein distance for fuzzy matching (handles word variations)
- Position-aware scoring (earlier matches = more important)
- Quality filtering (stop words, short words excluded)

### 2. Relevance Score Breakdowns

**Purpose**: Explain why a source was selected with detailed component scores.

**Knowledge Structure Support**:
- **Fisher Information Correlation**: High relevance = high Fisher Information = strong manifold structure
- **Topological Stability**: High relevance × quality = stable knowledge structure (attractor basin)
- **Trust Calibration**: Relevance scores enable Expected Calibration Error (ECE) computation
- **Information Contribution**: Component breakdowns show how each factor contributes to structure

**Implementation**:
- Adaptive weights (token match quality affects weighting)
- Component breakdowns (word overlap, semantic similarity, token matches)
- Visual indicators (🟢🟡🔴) for quick scanning
- Clamped to [0, 1] for calibration

### 3. Query Refinement Suggestions

**Purpose**: Guide users to explore knowledge structures more effectively.

**Knowledge Structure Support**:
- **D-Separation Preservation**: Suggestions respect existing knowledge structure (no spurious paths)
- **Attractor Basin Exploration**: Suggests queries to explore stable knowledge structures
- **Clique Discovery**: Guides users to find coherent source clusters
- **Information Geometry**: Suggests queries that increase Fisher Information (stronger structure)

**Implementation**:
- Priority-based ordering (high/medium/low)
- Smart concept extraction (filters stop words, prioritizes longer terms)
- Deduplication of similar queries
- Context-aware suggestions (based on provenance data)

### 4. Quality-Aware Claim Extraction

**Purpose**: Extract high-quality claims that represent stable knowledge structures.

**Knowledge Structure Support**:
- **Topological Stability**: Quality × Relevance predicts stable structures (cliques, attractors)
- **Attractor Basin Identification**: High-quality claims with high relevance = attractor basins
- **Information Content**: Quality scores reflect information content (Fisher Information)
- **Clique Formation**: High-quality claims are more likely to form coherent cliques

**Implementation**:
- Quality scoring (position, length, indicators)
- Claims sorted by quality × relevance (topological stability)
- Better filtering of filler sentences
- Position-aware extraction (earlier = more important)

### 5. Source Relationship Mapping

**Purpose**: Map relationships between sources (agreement, disagreement, consensus).

**Knowledge Structure Support**:
- **Clique Analysis**: Source agreement = clique formation (coherent knowledge structures)
- **Attractor Basins**: Multiple sources agreeing = stable attractor basin
- **D-Separation**: Independent sources remain d-separated (no spurious correlations)
- **Condorcet Jury Theorem**: Multiple independent sources increase accuracy

**Implementation**:
- Source agreement matrix (consensus vs. conflict)
- Clique detection (sources that agree form cliques)
- Trust propagation (trust flows through source relationships)
- Verification tracking (multiple verifications = higher confidence)

## Statistical Validation

All provenance features are validated through hard tests:

1. **D-Separation Preservation**: Verified that independent concepts remain independent
2. **Clique Coherence**: Verified that nodes in cliques are highly correlated
3. **Trust Calibration**: Computed Expected Calibration Error (ECE) for trust scores
4. **Information Geometry**: Verified that relevance scores correlate with Fisher Information
5. **Attractor Basin Identification**: Verified that convergent sources form mbopmal cliques

## Integration with Core Components

### ContextTopology
- Provenance data feeds into topology analysis
- Relevance scores inform clique formation
- Source relationships create edges in knowledge graph
- Quality scores contribute to topological stability

### StructuredOrchestrator
- Provenance preserves d-separation in orchestration
- Token matches reflect semantic structure
- Relevance scores guide tool selection
- Query refinement respects causal structure

### KnowledgeAgent
- Provenance enables progressive disclosure
- Quality scores inform response adaptation
- Source mapping supports trust metrics
- Query refinement guides user exploration

## Usage Examples

### Example 1: Exploring Knowledge Structure

```python
agent = KnowledgeAgent(enable_quality_feedback=True)
response = await agent.chat(
    message="What is d-separation and how does it relate to information geometry?",
    use_research=True,
)

# Access provenance (knowledge structure mapping)
provenance = response["research"]["provenance"]

# Access topology (knowledge structure analysis)
topology = response["research"]["topology"]
cliques = topology["cliques"]  # Coherent knowledge structures

# Access source matrix (knowledge structure relationships)
source_matrix = response["research"]["source_matrix"]
```

### Example 2: Validating Theoretical Claims

```python
# Run hard theoretical validation
from evaluations.hard_theoretical_validation import main
exit_code = await main()

# Validates:
# - D-separation preservation
# - Clique coherence
# - Trust calibration
# - Provenance accuracy
```

## Conclusion

All provenance features are harmonized with BOP's core purpose: **Knowledge Structure Research**. They support:
- Topological analysis (cliques, attractors, d-separation)
- Information geometry (Fisher Information, manifold structure)
- Trust/uncertainty modeling (calibration, credibility)
- Causal structure preservation (d-separation via MCP)

This alignment ensures that provenance features enhance, rather than distract from, BOP's theoretical foundations.

