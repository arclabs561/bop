# Test Suite Organization

Complete organization structure for discoverability and usability.

## Directory Structure

```
tests/
├── README.md                          # Quick reference guide
├── TEST_INDEX.md                      # Complete test index
├── DISCOVERY_GUIDE.md                 # Discovery guide
├── EVALUATION_INDEX.md                # Evaluation files index
├── RUNFILES_INDEX.md                  # Run files index
├── ORGANIZATION.md                    # This file
├── run_all_tests.py                   # Unified test runner
├── annotate_tests.py                 # Test annotation management
├── conftest.py                        # Pytest configuration
├── test_annotations.py               # Annotation utilities
├── test_annotations.json              # Stored annotations
│
├── Quality Tests/
│   ├── test_grice_maxims.py          # Grice's maxims (7 tests)
│   ├── test_semantic_properties.py   # Semantic properties (4 tests)
│   ├── test_behavioral_properties.py # Behavioral properties (4 tests)
│   ├── test_llm_agent_behavior.py    # LLM agent behavior (4 tests)
│   ├── test_additional_quality_properties.py # Additional quality (6 tests)
│   ├── test_quality_property_based.py # Property-based quality (10 tests)
│   ├── test_grice_property_based.py  # Property-based Grice (5 tests)
│   └── test_behavioral_property_based.py # Property-based behavioral (4 tests)
│
├── Integration Tests/
│   └── test_integration_quality_systems.py # Integration (5 tests)
│
├── Performance Tests/
│   └── test_performance_quality_systems.py # Performance (5 tests)
│
├── Safety Tests/
│   └── test_safety_quality_systems.py # Safety (5 tests)
│
├── Benchmark Tests/
│   └── test_benchmark_quality_metrics.py # Benchmark (5 tests)
│
├── Regression Tests/
│   └── test_regression_quality_systems.py # Regression (5 tests)
│
├── Mutation Testing/
│   ├── test_mutation_agent.py             # Mutation-focused tests (17 tests)
│   └── MUTATION_TESTING.md                # Mutation testing guide
│
├── Framework Tests/
│   └── test_comprehensive_evaluation_frameworks.py # Frameworks (8 tests)
│
├── Property-Based Tests/
│   ├── test_advanced_property_invariants.py # Advanced invariants (6 tests)
│   ├── test_custom_property_strategies.py # Custom strategies (3 tests)
│   └── test_metamorphic_properties.py # Metamorphic (4 tests)
│
├── Hierarchical Tests/
│   ├── test_session_manager.py
│   ├── test_session_manager_edge_cases.py
│   ├── test_hierarchical_system_interplay.py
│   ├── test_hierarchical_critical_gaps.py
│   ├── test_hierarchical_deep_analysis.py
│   ├── test_hierarchical_hidden_failures.py
│   └── test_hierarchical_data_loss_scenarios.py
│
└── Documentation/
    ├── ANNOTATION_GUIDE.md
    ├── MULTI_TURN_TESTING_SUMMARY.md
    ├── PROPERTY_BASED_TESTING_SUMMARY.md
    ├── MCP_FINAL_COMPREHENSIVE_REPORT.md
    └── ... (other documentation files)
```

## Test Categories

### 1. Quality Tests (42 tests)
- LLM-judged quality tests
- Property-based quality tests
- Semantic and behavioral property tests

### 2. Integration Tests (5 tests)
- Component interaction tests
- End-to-end pipeline tests

### 3. Performance Tests (5 tests)
- Latency, throughput, memory tests
- Concurrent operation tests

### 4. Safety Tests (5 tests)
- Security and robustness tests
- Adversarial input handling

### 5. Benchmark Tests (5 tests)
- HELM, Chatbot Arena, MT-Bench metrics

### 6. Regression Tests (5 tests)
- Backward compatibility tests
- Stability tests

### 7. Framework Tests (8 tests)
- Comprehensive evaluation framework tests

### 8. Property-Based Tests (13 tests)
- Advanced invariants
- Custom strategies
- Metamorphic properties

### 9. Hierarchical Tests (7+ files)
- Session management tests
- Hierarchical system tests

### 10. Mutation Tests (17 tests)
- Mutation testing for agent code
- Test quality evaluation
- See [MUTATION_TESTING.md](MUTATION_TESTING.md)

## Discovery Methods

### 1. Test Index
- **File**: `TEST_INDEX.md`
- **Content**: Complete catalog of all tests
- **Usage**: `cat tests/TEST_INDEX.md`

### 2. Test Runner
- **File**: `run_all_tests.py`
- **Usage**: `python tests/run_all_tests.py --list`

### 3. Discovery Guide
- **File**: `DISCOVERY_GUIDE.md`
- **Content**: Quick discovery guide

### 4. README
- **File**: `README.md`
- **Content**: Quick reference

## Execution Methods

### 1. Pytest (Standard)
```bash
pytest tests/ -v
pytest tests/ -k "quality" -v
pytest tests/ -m "llm_judge" -v
```

### 2. Unified Runner
```bash
python tests/run_all_tests.py
python tests/run_all_tests.py --category quality
python tests/run_all_tests.py --pattern integration
```

### 3. Direct File Execution
```bash
pytest tests/test_grice_maxims.py -v
python tests/run_all_tests.py --files test_grice_maxims.py
```

## Evaluation Files

### Core Modules
- `src/bop/semantic_eval.py` - Semantic evaluation
- `src/bop/eval.py` - Evaluation utilities
- `src/bop/quality_feedback.py` - Quality feedback
- `src/bop/adaptive_quality.py` - Adaptive quality

### Scripts
- `scripts/run_semantic_evaluation.py` - Evaluation runner
- `scripts/run_semantic_evaluation_v2.py` - Enhanced runner
- `scripts/run_mutation_tests.sh` - Mutation testing runner

## Test Annotations

All tests are annotated with:
- **Pattern**: Testing methodology
- **Opinion**: Hypothesis being tested
- **Category**: Test category
- **Hypothesis**: What the test validates

View annotations:
```bash
cat tests/test_annotations.json
```

## Statistics

- **Total Tests**: 92+ comprehensive tests
- **Test Files**: 89+ test files
- **Documentation**: 40+ markdown files
- **Categories**: 12 test categories
- **Frameworks**: 5 evaluation frameworks

## Quick Links

- [TEST_INDEX.md](TEST_INDEX.md) - Complete test index
- [README.md](README.md) - Quick reference
- [DISCOVERY_GUIDE.md](DISCOVERY_GUIDE.md) - Discovery guide
- [EVALUATION_INDEX.md](EVALUATION_INDEX.md) - Evaluation index
- [RUNFILES_INDEX.md](RUNFILES_INDEX.md) - Run files index

