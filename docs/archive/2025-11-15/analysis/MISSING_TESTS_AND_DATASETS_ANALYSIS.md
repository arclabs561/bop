# Missing Tests and Datasets Analysis

## Executive Summary

Based on deep MCP research and codebase analysis, this document identifies critical test scenarios and datasets that would significantly strengthen BOP's validation framework, particularly for uncertainty quantification, source credibility, and multi-document comprehension.

## Critical Missing Tests

### 1. Fact Verification with Conflicting Sources ⭐⭐⭐

**Why Critical:**
- BOP aggregates multiple sources but lacks tests with known ground truth for conflicting claims
- Essential for validating trust metrics, source credibility, and uncertainty quantification
- Tests calibration of confidence scores when sources disagree

**Test Scenarios:**
```python
# Test: FEVER-style fact verification
- Claim: "D-separation is a graphical criterion for conditional independence"
- Source 1: SUPPORTED (high credibility, arxiv paper)
- Source 2: REFUTED (low credibility, blog post with error)
- Source 3: NOTENOUGHINFO (medium credibility, incomplete explanation)
- Expected: System should identify conflict, weight high-credibility source, report uncertainty
```

**Datasets:**
- **FEVER** (185,445 claims with SUPPORTED/REFUTED/NOTENOUGHINFO labels)
- **FEVEROUS** (87,026 claims with structured/unstructured evidence)
- **SciFact** (1,409 scientific claims with evidence from research papers)

**Implementation Priority:** HIGH - Directly tests core uncertainty and trust features

### 2. Multi-Document Question Answering ⭐⭐⭐

**Why Critical:**
- BOP synthesizes from multiple sources but lacks multi-hop reasoning tests
- Tests ability to connect information across documents
- Validates d-separation preservation in complex reasoning chains

**Test Scenarios:**
```python
# Test: HotpotQA-style multi-hop reasoning
- Query: "What is the relationship between d-separation and Fisher Information?"
- Document 1: Explains d-separation (from Pearl's work)
- Document 2: Explains Fisher Information (from information geometry)
- Document 3: Connects them (from recent research)
- Expected: System should synthesize across all three, maintain causal structure
```

**Datasets:**
- **HotpotQA** (113k questions requiring multi-hop reasoning)
- **2WikiMultihopQA** (Multi-hop QA over Wikipedia)
- **MuSiQue** (Multi-hop questions with reasoning chains)

**Implementation Priority:** HIGH - Tests core synthesis capabilities

### 3. Calibration Error Ground Truth ⭐⭐⭐

**Why Critical:**
- BOP computes calibration error but lacks tests with known ground truth
- Can't validate if calibration improvement actually works
- No way to measure if uncertainty metrics are well-calibrated

**Test Scenarios:**
```python
# Test: Known calibration scenarios
- Scenario 1: Overconfident system (confidence 0.9, accuracy 0.6)
  Expected: Calibration improvement should reduce confidence
- Scenario 2: Underconfident system (confidence 0.4, accuracy 0.8)
  Expected: Calibration improvement should increase confidence
- Scenario 3: Well-calibrated system (confidence matches accuracy)
  Expected: Calibration improvement should maintain calibration
```

**Datasets:**
- **Calibration Benchmarks** (synthetic datasets with known calibration properties)
- **MS MARCO** (with relevance judgments for calibration)
- **TREC datasets** (with ground truth relevance for calibration)

**Implementation Priority:** HIGH - Essential for validating calibration improvements

### 4. Source Credibility Ground Truth ⭐⭐⭐

**Why Critical:**
- BOP uses source credibility but lacks tests with known credibility scores
- Can't validate if MUSE selection actually prioritizes credible sources
- No way to measure credibility learning accuracy

**Test Scenarios:**
```python
# Test: Known source credibility
- Source 1: arxiv.org paper (ground truth credibility: 0.9)
- Source 2: Wikipedia (ground truth credibility: 0.7)
- Source 3: Random blog (ground truth credibility: 0.3)
- Expected: MUSE should select sources 1 and 2, filter source 3
```

**Datasets:**
- **Source Credibility Benchmarks** (datasets with expert-annotated credibility)
- **FEVER** (Wikipedia sources with known reliability)
- **SciFact** (Research papers with citation-based credibility)

**Implementation Priority:** HIGH - Tests MUSE selection and credibility filtering

### 5. Temporal Knowledge Evolution ⭐⭐

**Why Critical:**
- BOP tracks temporal aspects but lacks tests with known evolution
- Tests how system handles changing knowledge over time
- Validates temporal tracking and evolution detection

**Test Scenarios:**
```python
# Test: Temporal knowledge evolution
- Query: "What is the latest research on uncertainty quantification?"
- Source 1: 2020 paper (older knowledge)
- Source 2: 2024 paper (newer knowledge, supersedes Source 1)
- Expected: System should prioritize Source 2, note temporal evolution
```

**Datasets:**
- **TSVer** (287 claims with time-series evidence)
- **Temporal FEVER** (claims with temporal annotations)
- **Research paper timelines** (arXiv papers with publication dates)

**Implementation Priority:** MEDIUM - Enhances temporal features

### 6. Adversarial Source Injection ⭐⭐

**Why Critical:**
- BOP has adversarial tests but not for source credibility manipulation
- Tests resistance to adversarial sources trying to game credibility
- Validates trust metrics under attack

**Test Scenarios:**
```python
# Test: Adversarial source injection
- Adversarial Source: High credibility metadata but low-quality content
- Expected: System should detect mismatch, reduce credibility, report uncertainty
```

**Implementation Priority:** MEDIUM - Security and robustness

### 7. Multi-Modal Knowledge Integration ⭐

**Why Critical:**
- BOP focuses on text but knowledge comes in multiple forms
- Tests ability to integrate structured (tables) and unstructured (text) sources
- Validates FEVEROUS-style multi-modal evidence

**Test Scenarios:**
```python
# Test: Multi-modal evidence
- Claim: "D-separation has 3 conditions"
- Evidence 1: Text explanation
- Evidence 2: Table with conditions
- Expected: System should synthesize both, maintain structure
```

**Datasets:**
- **FEVEROUS** (structured + unstructured evidence)
- **WikiTableQuestions** (QA over tables)
- **HybridQA** (text + table reasoning)

**Implementation Priority:** LOW - Future enhancement

### 8. Real Research Paper Integration ⭐⭐⭐

**Why Critical:**
- BOP uses arXiv but lacks tests with actual paper content
- Tests real-world knowledge structure research scenarios
- Validates provenance tracking with real academic sources

**Test Scenarios:**
```python
# Test: Real research paper synthesis
- Query: "What is the relationship between d-separation and information geometry?"
- Source 1: Pearl's "Causality" (foundational)
- Source 2: Amari's "Information Geometry" (foundational)
- Source 3: Recent paper connecting them (synthesis)
- Expected: System should synthesize, show provenance, track citations
```

**Datasets:**
- **arXiv abstracts + full text** (real research papers)
- **PubMed abstracts** (biomedical research)
- **Semantic Scholar** (research paper metadata + citations)

**Implementation Priority:** HIGH - Real-world validation

### 9. Uncertainty Calibration with Known Distributions ⭐⭐⭐

**Why Critical:**
- BOP computes epistemic/aleatoric uncertainty but lacks ground truth
- Can't validate if JSD-based uncertainty is accurate
- No way to measure if uncertainty metrics match reality

**Test Scenarios:**
```python
# Test: Known uncertainty distributions
- Scenario: 5 sources with known prediction distributions
- Ground truth: Epistemic uncertainty = 0.3, Aleatoric = 0.2
- Expected: BOP's JSD-based computation should match ground truth
```

**Datasets:**
- **Synthetic uncertainty datasets** (known probability distributions)
- **Ensemble prediction datasets** (multiple model predictions with known uncertainty)

**Implementation Priority:** HIGH - Validates core uncertainty features

### 10. Cross-Domain Knowledge Transfer ⭐

**Why Critical:**
- BOP works across domains but lacks tests for transfer learning
- Tests if knowledge structures generalize across domains
- Validates d-separation preservation across domains

**Test Scenarios:**
```python
# Test: Cross-domain reasoning
- Domain 1: Statistics (d-separation)
- Domain 2: Machine Learning (causal inference)
- Query: "How does d-separation apply to ML?"
- Expected: System should transfer knowledge, maintain structure
```

**Datasets:**
- **Cross-domain QA datasets**
- **Domain adaptation benchmarks**

**Implementation Priority:** LOW - Research direction

## Critical Missing Datasets

### 1. Fact Verification Datasets ⭐⭐⭐

**FEVER** (Fact Extraction and VERification)
- **Size:** 185,445 claims
- **Labels:** SUPPORTED, REFUTED, NOTENOUGHINFO
- **Evidence:** Wikipedia sentences
- **Use Case:** Test source conflict resolution, trust metrics, uncertainty

**FEVEROUS** (FEVER Over Unstructured and Structured)
- **Size:** 87,026 claims
- **Evidence:** Wikipedia sentences + tables
- **Use Case:** Test multi-modal evidence synthesis

**SciFact**
- **Size:** 1,409 scientific claims
- **Evidence:** Research paper abstracts
- **Use Case:** Test scientific fact verification, source credibility

**Implementation:**
```python
# Load FEVER dataset
from datasets import load_dataset
fever = load_dataset("fever", "v1.0")

# Test with conflicting sources
for claim in fever["train"]:
    if claim["label"] == "REFUTED":
        # Test: System should identify refutation, report high uncertainty
        pass
```

### 2. Multi-Document QA Datasets ⭐⭐⭐

**HotpotQA**
- **Size:** 113k questions
- **Type:** Multi-hop reasoning over Wikipedia
- **Use Case:** Test multi-document synthesis, d-separation preservation

**2WikiMultihopQA**
- **Size:** 200k questions
- **Type:** Multi-hop reasoning with reasoning chains
- **Use Case:** Test reasoning chain validation

**MuSiQue**
- **Size:** 25k questions
- **Type:** Multi-hop with explicit reasoning steps
- **Use Case:** Test step-by-step reasoning validation

**Implementation:**
```python
# Load HotpotQA
hotpot = load_dataset("hotpot_qa", "fullwiki")

# Test multi-hop reasoning
for question in hotpot["train"]:
    # Test: System should connect information across documents
    pass
```

### 3. Calibration Benchmarks ⭐⭐⭐

**MS MARCO**
- **Size:** 1M queries with relevance judgments
- **Use Case:** Test calibration error with ground truth relevance

**TREC Datasets**
- **Various tracks:** Ad-hoc, Web, Robust
- **Use Case:** Test calibration across different domains

**Synthetic Calibration Datasets**
- **Custom:** Known overconfidence/underconfidence scenarios
- **Use Case:** Test calibration improvement algorithms

**Implementation:**
```python
# Create synthetic calibration dataset
calibration_data = {
    "overconfident": {
        "predictions": [0.9, 0.8, 0.7],
        "actual": [0.6, 0.5, 0.4],  # System overconfident
        "expected_ece": 0.3
    },
    "well_calibrated": {
        "predictions": [0.9, 0.8, 0.7],
        "actual": [0.9, 0.8, 0.7],  # Perfect calibration
        "expected_ece": 0.0
    }
}
```

### 4. Source Credibility Datasets ⭐⭐⭐

**FEVER Source Reliability**
- **Wikipedia sources** with known reliability scores
- **Use Case:** Test credibility-based filtering

**SciFact Citation Networks**
- **Research papers** with citation-based credibility
- **Use Case:** Test academic source credibility

**Expert-Annotated Credibility**
- **Custom dataset** with expert credibility scores
- **Use Case:** Test credibility learning accuracy

**Implementation:**
```python
# Load source credibility dataset
credibility_data = {
    "arxiv.org": 0.9,
    "wikipedia.org": 0.7,
    "random-blog.com": 0.3
}

# Test MUSE selection with known credibility
```

### 5. Knowledge Graph Datasets ⭐⭐

**Wikidata**
- **Size:** Billions of triples
- **Use Case:** Test knowledge graph integration, topological analysis

**DBpedia**
- **Size:** Millions of entities
- **Use Case:** Test structured knowledge integration

**YAGO**
- **Size:** Millions of facts
- **Use Case:** Test knowledge graph reasoning

**Implementation:**
```python
# Load Wikidata
from wikidata.client import Client
client = Client()

# Test knowledge graph integration
entity = client.get("Q12345")  # d-separation entity
# Test: System should integrate KG structure
```

### 6. Research Paper Datasets ⭐⭐⭐

**arXiv Abstracts + Full Text**
- **Size:** Millions of papers
- **Use Case:** Test real research paper synthesis, provenance

**PubMed Abstracts**
- **Size:** Millions of biomedical papers
- **Use Case:** Test scientific knowledge synthesis

**Semantic Scholar**
- **Size:** Millions of papers with citations
- **Use Case:** Test citation-based credibility, knowledge graphs

**Implementation:**
```python
# Load arXiv dataset
from datasets import load_dataset
arxiv = load_dataset("scientific_papers", "arxiv")

# Test with real research papers
for paper in arxiv["train"]:
    # Test: System should synthesize, show provenance
    pass
```

### 7. Temporal Knowledge Datasets ⭐⭐

**TSVer** (Time-Series Verification)
- **Size:** 287 claims with time-series evidence
- **Use Case:** Test temporal reasoning, knowledge evolution

**Temporal FEVER**
- **FEVER claims** with temporal annotations
- **Use Case:** Test temporal fact verification

**Research Paper Timelines**
- **arXiv papers** with publication dates
- **Use Case:** Test temporal knowledge tracking

**Implementation:**
```python
# Load TSVer
tsver = load_dataset("tsver")

# Test temporal reasoning
for claim in tsver:
    # Test: System should handle temporal evidence
    pass
```

## Implementation Plan

### Phase 1: Critical Tests (High Priority) ⭐⭐⭐

1. **Fact Verification Tests** (FEVER dataset)
   - Test conflicting sources
   - Test trust metrics with ground truth
   - Test uncertainty quantification

2. **Calibration Ground Truth Tests**
   - Test calibration improvement with known scenarios
   - Test ECE computation accuracy
   - Test Brier Score computation

3. **Source Credibility Tests**
   - Test MUSE selection with known credibility
   - Test credibility filtering accuracy
   - Test credibility learning

4. **Real Research Paper Tests**
   - Test with actual arXiv papers
   - Test provenance tracking with real sources
   - Test citation-based credibility

### Phase 2: Important Tests (Medium Priority) ⭐⭐

5. **Multi-Document QA Tests** (HotpotQA)
   - Test multi-hop reasoning
   - Test d-separation preservation
   - Test synthesis across documents

6. **Temporal Evolution Tests**
   - Test knowledge evolution tracking
   - Test temporal reasoning
   - Test source prioritization by time

7. **Adversarial Source Tests**
   - Test credibility manipulation resistance
   - Test trust metric robustness
   - Test uncertainty under attack

### Phase 3: Enhancement Tests (Low Priority) ⭐

8. **Multi-Modal Tests** (FEVEROUS)
   - Test structured + unstructured evidence
   - Test table + text synthesis

9. **Cross-Domain Tests**
   - Test knowledge transfer
   - Test domain adaptation

## Dataset Integration Strategy

### 1. Use HuggingFace Datasets

```python
# Easy integration with existing datasets
from datasets import load_dataset

fever = load_dataset("fever", "v1.0")
hotpot = load_dataset("hotpot_qa", "fullwiki")
```

### 2. Create Custom Datasets

```python
# For calibration, credibility, uncertainty ground truth
datasets/
  calibration_ground_truth.json
  credibility_ground_truth.json
  uncertainty_ground_truth.json
```

### 3. Use MCP Tools for Real Data

```python
# Use arXiv MCP tool for real research papers
from bop.mcp_tools import call_mcp_tool

# Search real papers
result = await call_mcp_tool(
    "mcp_arxiv-mcp-server_search_papers",
    query="d-separation information geometry",
    categories=["cs.AI", "stat.ML"]
)
```

## Test Implementation Examples

### Example 1: FEVER Fact Verification Test

```python
def test_fever_fact_verification():
    """Test fact verification with FEVER dataset."""
    from datasets import load_dataset
    
    fever = load_dataset("fever", "v1.0", split="train[:100]")
    
    agent = KnowledgeAgent()
    
    for claim_data in fever:
        claim = claim_data["claim"]
        label = claim_data["label"]  # SUPPORTED, REFUTED, NOTENOUGHINFO
        evidence = claim_data["evidence"]
        
        response = await agent.chat(
            f"Verify this claim: {claim}",
            use_research=True
        )
        
        # Check if system correctly identifies label
        if label == "REFUTED":
            assert response["research"]["topology"]["trust_summary"]["avg_trust"] < 0.5
        elif label == "SUPPORTED":
            assert response["research"]["topology"]["trust_summary"]["avg_trust"] > 0.7
        
        # Check if evidence is correctly cited
        assert any(ev in response["response"] for ev in evidence)
```

### Example 2: Calibration Ground Truth Test

```python
def test_calibration_improvement_ground_truth():
    """Test calibration improvement with known ground truth."""
    # Known overconfident scenario
    predictions = [0.9, 0.8, 0.7]
    actual = [0.6, 0.5, 0.4]  # System overconfident
    
    from bop.calibration_improvement import improve_calibration_with_uncertainty
    
    result = improve_calibration_with_uncertainty(
        predictions=[np.array([p, 1-p]) for p in predictions],
        confidence_scores=predictions,
        actual_outcomes=actual,
    )
    
    # Calibration should improve (ECE should decrease)
    assert result["ece_after"] < result["ece_before"]
    assert result["calibration_improvement"]["ece_reduction"] > 0
```

### Example 3: Source Credibility Ground Truth Test

```python
def test_muse_selection_credibility_ground_truth():
    """Test MUSE selection with known source credibility."""
    candidate_tools = ["arxiv", "wikipedia", "blog"]
    tool_metadata = [
        {"credibility": 0.9},  # arxiv (ground truth: high)
        {"credibility": 0.7},  # wikipedia (ground truth: medium)
        {"credibility": 0.3},  # blog (ground truth: low)
    ]
    
    from bop.uncertainty_tool_selection import select_tools_with_muse
    
    selected, metadata = select_tools_with_muse(
        candidate_tools,
        tool_metadata,
        "test query",
        min_credibility=0.5,  # Should filter blog
    )
    
    # Should select arxiv and wikipedia, filter blog
    assert "arxiv" in selected
    assert "wikipedia" in selected
    assert "blog" not in selected
    assert metadata["num_filtered"] == 2
```

## Next Steps

1. **Immediate (This Week):**
   - Implement FEVER fact verification tests
   - Create calibration ground truth dataset
   - Add source credibility ground truth tests

2. **Short Term (This Month):**
   - Integrate HotpotQA for multi-document QA
   - Add real arXiv paper tests
   - Create uncertainty ground truth dataset

3. **Long Term (Next Quarter):**
   - Integrate FEVEROUS for multi-modal tests
   - Add temporal evolution tests
   - Create comprehensive benchmark suite

## Conclusion

These missing tests and datasets would significantly strengthen BOP's validation framework, particularly for:
- **Uncertainty Quantification**: Ground truth for calibration and uncertainty metrics
- **Source Credibility**: Known credibility scores for validation
- **Multi-Document Reasoning**: Real multi-hop QA scenarios
- **Fact Verification**: Conflicting sources with ground truth labels
- **Real-World Validation**: Actual research papers and academic sources

**Priority Order:**
1. Fact Verification (FEVER) ⭐⭐⭐
2. Calibration Ground Truth ⭐⭐⭐
3. Source Credibility Ground Truth ⭐⭐⭐
4. Real Research Papers ⭐⭐⭐
5. Multi-Document QA (HotpotQA) ⭐⭐
6. Temporal Evolution ⭐⭐
7. Multi-Modal (FEVEROUS) ⭐

