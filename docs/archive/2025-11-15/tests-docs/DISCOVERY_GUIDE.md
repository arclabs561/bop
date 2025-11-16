# Test Discovery Guide

Quick guide to discovering and using all tests, evaluations, and run files.

## Quick Discovery

### 1. List All Test Categories
```bash
python tests/run_all_tests.py --list
```

### 2. View Test Index
```bash
cat tests/TEST_INDEX.md
```

### 3. View Test README
```bash
cat tests/README.md
```

## Finding Tests

### By Category
```bash
# Quality tests
python tests/run_all_tests.py --category quality

# Integration tests
python tests/run_all_tests.py --category integration

# Performance tests
python tests/run_all_tests.py --category performance
```

### By Pattern
```bash
# Integration pattern
python tests/run_all_tests.py --pattern integration

# Safety pattern
python tests/run_all_tests.py --pattern safety
```

### By Keyword
```bash
# All quality-related tests
pytest tests/ -k "quality" -v

# Mutation testing
just test-mutate-quick

# All integration tests
pytest tests/ -k "integration" -v
```

### By File
```bash
# Specific test file
python tests/run_all_tests.py --files test_grice_maxims.py

# Multiple files
python tests/run_all_tests.py --files test_grice_maxims.py test_semantic_properties.py
```

## Test Categories

| Category | Description | Test Files |
|----------|-------------|------------|
| **quality** | Grice's maxims, semantic, behavioral | 8 files |
| **property** | Property-based tests (Hypothesis) | 6 files |
| **integration** | Component interaction tests | 1 file |
| **performance** | Latency, throughput, memory | 1 file |
| **safety** | Security and robustness | 1 file |
| **benchmark** | HELM, Chatbot Arena, MT-Bench | 1 file |
| **regression** | Backward compatibility | 1 file |
| **framework** | Evaluation frameworks | 1 file |
| **hierarchical** | Session management | 7 files |
| **multi_turn** | Conversation flow | 1 file |
| **adversarial** | Adversarial testing | 1 file |
| **core** | Core system functionality | 4 files |
| **mutation** | Mutation testing | 1 file |

## Test Types

### LLM-Judged Tests (25 tests)
Tests requiring LLM evaluation:
- `test_grice_maxims.py`
- `test_semantic_properties.py`
- `test_behavioral_properties.py`
- `test_llm_agent_behavior.py`
- `test_additional_quality_properties.py`

### Property-Based Tests (32 tests)
Hypothesis-based property tests:
- `test_quality_property_based.py`
- `test_grice_property_based.py`
- `test_behavioral_property_based.py`
- `test_advanced_property_invariants.py`
- `test_custom_property_strategies.py`
- `test_metamorphic_properties.py`

### Functional Tests
Standard functional tests:
- `test_agent_integration.py`
- `test_quality_feedback.py`
- `test_semantic_eval.py`
- `test_semantic_realistic.py`

## Running Tests

### All Tests
```bash
pytest tests/ -v
```

### By Category
```bash
python tests/run_all_tests.py --category <category>
```

### By Pattern
```bash
python tests/run_all_tests.py --pattern <pattern>
```

### Specific Files
```bash
python tests/run_all_tests.py --files <file1> <file2> ...
```

## Test Annotations

All tests are annotated with metadata:
- **Pattern**: Testing methodology
- **Opinion**: Hypothesis being tested
- **Category**: Test category
- **Hypothesis**: What the test validates

View annotations:
```bash
cat tests/TEST_ANNOTATIONS.json
```

## Documentation Files

- **TEST_INDEX.md** - Complete test index
- **README.md** - Quick reference
- **DISCOVERY_GUIDE.md** - This file
- **MAKE_DISCOVERABLE.md** - Organization details
- **ANNOTATION_GUIDE.md** - Annotation system guide
- Various category-specific summaries

## Evaluation Files

### Core Evaluation
- `src/bop/semantic_eval.py` - Semantic evaluation framework
- `src/bop/eval.py` - Evaluation utilities

### Quality Management
- `src/bop/quality_feedback.py` - Quality feedback loop
- `src/bop/adaptive_quality.py` - Adaptive quality management

## Quick Reference

### Most Important Tests
1. **Integration**: `test_integration_quality_systems.py`
2. **Quality**: `test_quality_property_based.py`, `test_grice_maxims.py`
3. **Performance**: `test_performance_quality_systems.py`
4. **Safety**: `test_safety_quality_systems.py`
5. **Benchmark**: `test_benchmark_quality_metrics.py`

### Test Statistics
- **Total**: 92+ comprehensive tests
- **LLM-Judged**: 25 tests
- **Property-Based**: 32 tests
- **Integration**: 5 tests
- **Performance**: 5 tests
- **Safety**: 5 tests
- **Benchmark**: 5 tests
- **Regression**: 5 tests
- **Framework**: 8 tests

