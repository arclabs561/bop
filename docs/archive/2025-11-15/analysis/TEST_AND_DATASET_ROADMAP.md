# Test and Dataset Integration Roadmap

## Summary

Based on deep MCP research and codebase analysis, this roadmap outlines the critical tests and datasets needed to strengthen BOP's validation framework.

## Critical Missing Tests (Priority Order)

### ⭐⭐⭐ Highest Priority

1. **Fact Verification Tests** (FEVER dataset)
   - Test conflicting sources with ground truth labels
   - Test trust metrics accuracy
   - Test uncertainty quantification with known conflicts
   - **Status:** Framework created (`test_fever_fact_verification.py`)
   - **Next:** Integrate actual FEVER dataset

2. **Calibration Ground Truth Tests**
   - Test calibration improvement with known scenarios
   - Test ECE/Brier Score computation accuracy
   - **Status:** ✅ Implemented (`test_calibration_ground_truth.py`)
   - **Dataset:** ✅ Created (`datasets/calibration_ground_truth.json`)

3. **Source Credibility Ground Truth Tests**
   - Test MUSE selection with known credibility
   - Test credibility filtering accuracy
   - **Status:** ✅ Implemented (`test_source_credibility_ground_truth.py`)
   - **Dataset:** ✅ Created (`datasets/source_credibility_ground_truth.json`)

4. **Real Research Paper Tests**
   - Test with actual arXiv papers
   - Test provenance tracking with real sources
   - **Status:** Framework exists, needs real paper integration

### ⭐⭐ High Priority

5. **Multi-Document QA Tests** (HotpotQA)
   - Test multi-hop reasoning
   - Test d-separation preservation
   - **Status:** Not implemented
   - **Dataset:** HotpotQA (113k questions)

6. **Temporal Evolution Tests**
   - Test knowledge evolution tracking
   - Test temporal reasoning
   - **Status:** Partial (temporal queries exist)
   - **Dataset:** TSVer (287 claims with time-series)

7. **Adversarial Source Tests**
   - Test credibility manipulation resistance
   - **Status:** Adversarial tests exist, but not for source credibility
   - **Next:** Add source-specific adversarial tests

### ⭐ Medium Priority

8. **Multi-Modal Tests** (FEVEROUS)
   - Test structured + unstructured evidence
   - **Status:** Not implemented
   - **Dataset:** FEVEROUS (87k claims)

9. **Uncertainty Calibration Tests**
   - Test JSD-based uncertainty accuracy
   - **Status:** Partial (uncertainty tests exist, but no ground truth)
   - **Next:** Create uncertainty ground truth dataset

## Critical Missing Datasets

### ⭐⭐⭐ Highest Priority

1. **FEVER** (Fact Extraction and VERification)
   - **Size:** 185,445 claims
   - **Labels:** SUPPORTED, REFUTED, NOTENOUGHINFO
   - **Integration:** Use HuggingFace `datasets` library
   - **Use Case:** Fact verification, conflicting sources

2. **HotpotQA** (Multi-hop Question Answering)
   - **Size:** 113k questions
   - **Integration:** Use HuggingFace `datasets` library
   - **Use Case:** Multi-document reasoning, d-separation

3. **Calibration Ground Truth**
   - **Status:** ✅ Created (`datasets/calibration_ground_truth.json`)
   - **Use Case:** Calibration improvement validation

4. **Source Credibility Ground Truth**
   - **Status:** ✅ Created (`datasets/source_credibility_ground_truth.json`)
   - **Use Case:** Credibility filtering validation

### ⭐⭐ High Priority

5. **SciFact** (Scientific Fact Checking)
   - **Size:** 1,409 claims
   - **Integration:** Use HuggingFace or direct download
   - **Use Case:** Scientific fact verification

6. **TSVer** (Time-Series Verification)
   - **Size:** 287 claims
   - **Integration:** Direct download from paper
   - **Use Case:** Temporal reasoning

7. **arXiv Research Papers**
   - **Size:** Millions of papers
   - **Integration:** Use arXiv MCP tool
   - **Use Case:** Real research paper synthesis

### ⭐ Medium Priority

8. **FEVEROUS** (Multi-modal evidence)
   - **Size:** 87,026 claims
   - **Integration:** Use HuggingFace
   - **Use Case:** Multi-modal synthesis

9. **Wikidata/DBpedia**
   - **Size:** Billions of triples
   - **Integration:** Use SPARQL endpoints
   - **Use Case:** Knowledge graph integration

## Implementation Plan

### Week 1: Critical Tests

1. **Integrate FEVER Dataset**
   ```python
   from datasets import load_dataset
   fever = load_dataset("fever", "v1.0")
   ```

2. **Complete FEVER Tests**
   - Implement actual FEVER integration
   - Test conflicting sources
   - Test trust metrics accuracy

3. **Integrate HotpotQA**
   ```python
   hotpot = load_dataset("hotpot_qa", "fullwiki")
   ```

### Week 2: Dataset Integration

4. **Create Dataset Loaders**
   - `datasets/load_fever.py`
   - `datasets/load_hotpotqa.py`
   - `datasets/load_scifact.py`

5. **Add to Test Infrastructure**
   - Update `conftest.py` with dataset fixtures
   - Create dataset validation utilities

### Week 3: Advanced Tests

6. **Multi-Document QA Tests**
   - Implement HotpotQA tests
   - Test multi-hop reasoning
   - Test d-separation preservation

7. **Temporal Evolution Tests**
   - Integrate TSVer
   - Test knowledge evolution
   - Test temporal reasoning

### Week 4: Real-World Validation

8. **Real Research Paper Tests**
   - Use arXiv MCP tool
   - Test with actual papers
   - Test provenance tracking

9. **Comprehensive Benchmark Suite**
   - Run all tests with real datasets
   - Generate benchmark report
   - Validate all features

## Quick Start: Using New Datasets

### FEVER Integration

```python
# tests/test_fever_integration.py
from datasets import load_dataset
import pytest

@pytest.fixture
def fever_dataset():
    return load_dataset("fever", "v1.0", split="train[:100]")

@pytest.mark.asyncio
async def test_fever_claim_verification(fever_dataset):
    agent = KnowledgeAgent()
    
    for claim_data in fever_dataset:
        response = await agent.chat(
            f"Verify: {claim_data['claim']}",
            use_research=True
        )
        
        # Validate against FEVER label
        label = claim_data["label"]
        trust = response["research"]["topology"]["trust_summary"]["avg_trust"]
        
        if label == "SUPPORTED":
            assert trust > 0.7
        elif label == "REFUTED":
            assert trust < 0.5
```

### HotpotQA Integration

```python
# tests/test_hotpotqa_integration.py
from datasets import load_dataset

@pytest.fixture
def hotpotqa_dataset():
    return load_dataset("hotpot_qa", "fullwiki", split="train[:50]")

@pytest.mark.asyncio
async def test_multi_hop_reasoning(hotpotqa_dataset):
    agent = KnowledgeAgent()
    
    for question_data in hotpotqa_dataset:
        response = await agent.chat(
            question_data["question"],
            use_research=True
        )
        
        # Validate multi-hop reasoning
        assert len(response["research"]["subsolutions"]) >= 2
        # Check if answer is correct (would need ground truth)
```

## Expected Improvements

### With FEVER Integration
- ✅ Validates trust metrics with ground truth
- ✅ Tests uncertainty quantification accuracy
- ✅ Validates source conflict resolution

### With HotpotQA Integration
- ✅ Tests multi-document synthesis
- ✅ Validates d-separation preservation
- ✅ Tests reasoning chain validation

### With Calibration Ground Truth
- ✅ Validates calibration improvement algorithms
- ✅ Tests ECE/Brier Score accuracy
- ✅ Measures calibration improvement effectiveness

### With Source Credibility Ground Truth
- ✅ Validates MUSE selection accuracy
- ✅ Tests credibility filtering effectiveness
- ✅ Measures credibility learning accuracy

## Success Metrics

1. **Test Coverage**
   - Fact verification: 90%+ accuracy on FEVER
   - Calibration: ECE reduction > 20%
   - Credibility: MUSE selection accuracy > 80%

2. **Dataset Integration**
   - FEVER: 100% integrated
   - HotpotQA: 100% integrated
   - Calibration ground truth: ✅ Complete
   - Credibility ground truth: ✅ Complete

3. **Real-World Validation**
   - Real research papers: Provenance tracking accuracy
   - Temporal evolution: Evolution detection accuracy
   - Multi-modal: Synthesis quality

## Conclusion

These tests and datasets will significantly strengthen BOP's validation framework, providing:
- **Ground truth** for uncertainty, calibration, and credibility
- **Real-world scenarios** for fact verification and multi-document QA
- **Comprehensive benchmarks** for all core features

**Next Steps:**
1. Integrate FEVER dataset (Week 1)
2. Complete FEVER tests (Week 1)
3. Integrate HotpotQA (Week 2)
4. Add real research paper tests (Week 3)
5. Create comprehensive benchmark suite (Week 4)

