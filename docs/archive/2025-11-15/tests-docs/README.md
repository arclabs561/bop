# Test Suite

Comprehensive test suite for the BOP (Knowledge Structure Research Agent) system.

## Quick Start

### Run All Tests
```bash
pytest tests/ -v
```

### Run by Category
```bash
python tests/run_all_tests.py --category quality
python tests/run_all_tests.py --category integration
python tests/run_all_tests.py --category performance
```

### Run by Pattern
```bash
python tests/run_all_tests.py --pattern integration
python tests/run_all_tests.py --pattern safety
```

### List Available Categories
```bash
python tests/run_all_tests.py --list
```

## Test Organization

### By Category
- **Quality** - Grice's mbopms, semantic properties, behavioral properties
- **Property-Based** - Hypothesis-based property tests
- **Integration** - Component interaction tests
- **Performance** - Latency, throughput, memory tests
- **Safety** - Security and robustness tests
- **Benchmark** - HELM, Chatbot Arena, MT-Bench metrics
- **Regression** - Backward compatibility and stability tests
- **Framework** - Comprehensive evaluation framework tests
- **Hierarchical** - Session management tests
- **Multi-Turn** - Conversation flow tests
- **Adversarial** - Adversarial testing
- **Core** - Core system functionality tests

### By Type
- **LLM-Judged** - Tests requiring LLM evaluation (25 tests)
- **Property-Based** - Hypothesis property tests (32 tests)
- **Functional** - Standard functional tests
- **Integration** - Multi-component tests
- **Performance** - Performance and scalability tests
- **Safety** - Security and robustness tests

## Test Index

See [TEST_INDEX.md](TEST_INDEX.md) for complete test index.

## Test Annotations

All tests are annotated with:
- **Pattern**: Testing methodology
- **Opinion**: Hypothesis being tested
- **Category**: Test category
- **Hypothesis**: What the test validates

View annotations:
```bash
cat tests/TEST_ANNOTATIONS.json
```

## Evaluation Framework

### Semantic Evaluation
- **`src/bop/semantic_eval.py`** - Core semantic evaluation
- **`src/bop/eval.py`** - Evaluation utilities

### Quality Feedback
- **`src/bop/quality_feedback.py`** - Quality feedback loop
- **`src/bop/adaptive_quality.py`** - Adaptive quality management

## Mutation Testing

Evaluate test quality by introducing mutations to code:

```bash
# Quick mutation test
just test-mutate-quick

# Full mutation testing with HTML report
just test-mutate-html

# View results
just test-mutate-show
```

See [MUTATION_TESTING.md](MUTATION_TESTING.md) for complete guide.

## Documentation

- [TEST_INDEX.md](TEST_INDEX.md) - Complete test index
- [ANNOTATION_GUIDE.md](ANNOTATION_GUIDE.md) - Test annotation guide
- [MUTATION_TESTING.md](MUTATION_TESTING.md) - Mutation testing guide
- [MULTI_TURN_TESTING_SUMMARY.md](MULTI_TURN_TESTING_SUMMARY.md) - Multi-turn testing
- [PROPERTY_BASED_TESTING_SUMMARY.md](PROPERTY_BASED_TESTING_SUMMARY.md) - Property-based testing
- [MCP_FINAL_COMPREHENSIVE_REPORT.md](MCP_FINAL_COMPREHENSIVE_REPORT.md) - MCP tool usage report

## Test Statistics

- **Total Tests**: 92+ comprehensive tests
- **Coverage**: Quality, semantic, behavioral, integration, performance, safety, benchmark, regression, framework
- **Frameworks**: HELM, Chatbot Arena, MT-Bench, Ragas, DeepEval

