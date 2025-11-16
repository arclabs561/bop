# Test Suite Index

Comprehensive index of all tests, evaluations, and run files for discoverability and usability.

## Test Categories

### Quality & Semantic Evaluation Tests

#### LLM-Judged Tests (25 tests)
- **`test_grice_maxims.py`** (7 tests) - Grice's maxims: Quality, Quantity, Relation, Manner, Benevolence, Transparency
- **`test_semantic_properties.py`** (4 tests) - Semantic properties: Consistency, Coherence, Correctness, Appropriateness
- **`test_behavioral_properties.py`** (4 tests) - Behavioral properties: Flow, Turn-taking, Context, Intent
- **`test_llm_agent_behavior.py`** (4 tests) - LLM agent behaviors: Tool selection, Reasoning, Errors, Correction
- **`test_additional_quality_properties.py`** (6 tests) - Additional quality: Appropriateness, Coherence, Grounding, Engagement, Naturalness, Diversity

#### Property-Based Tests (40+ tests)
- **`test_quality_property_based.py`** (10 tests) - Quality property invariants using Hypothesis
- **`test_grice_property_based.py`** (5 tests) - Grice's maxims property-based tests
- **`test_behavioral_property_based.py`** (4 tests) - Behavioral property-based tests
- **`test_advanced_property_invariants.py`** (6 tests) - Advanced invariants: Triangle inequality, Subadditivity, Compositionality
- **`test_custom_property_strategies.py`** (3 tests) - Custom Hypothesis strategies for realistic inputs
- **`test_metamorphic_properties.py`** (4 tests) - Metamorphic property tests
- **`test_ssh_property_based.py`** (8 tests) - SSH features property-based tests (IB filtering, adaptive depth, resource triple, logical depth)

### SSH Integration Tests (22+ tests)
- **`test_ssh_integration.py`** (10 tests) - SSH features integration (IB filtering, adaptive depth, resource triple, logical depth)
- **`test_ssh_e2e.py`** (4 tests) - SSH features end-to-end workflows
- **`test_ssh_comprehensive.py`** (8 tests) - Comprehensive SSH feature tests (all features together, learning, metrics)
- **`test_information_bottleneck.py`** (11 tests) - Information Bottleneck filtering unit tests
- **`test_adaptive_reasoning_depth.py`** (7 tests) - Adaptive reasoning depth unit tests
- **`test_resource_triple_metrics.py`** (5 tests) - Resource triple metrics unit tests
- **`test_ssh_property_based.py`** (8 tests) - SSH features property-based tests
- **`test_ssh_metamorphic.py`** (4 tests) - SSH features metamorphic tests
- **`test_ssh_evaluation_dataset.py`** (6 tests) - SSH features evaluation using structured dataset

### Integration Tests (5 tests)
- **`test_integration_quality_systems.py`** - Integration between quality feedback, adaptive learning, semantic eval, hierarchical sessions

### Performance Tests (5 tests)
- **`test_performance_quality_systems.py`** - Latency, throughput, memory usage, concurrency, large response handling

### Safety Tests (5 tests)
- **`test_safety_quality_systems.py`** - Prompt injection, harmful content, jailbreaking, adversarial inputs

### Benchmark Tests (5 tests)
- **`test_benchmark_quality_metrics.py`** - HELM, Chatbot Arena, MT-Bench metrics

### Regression Tests (5 tests)
- **`test_regression_quality_systems.py`** - Backward compatibility, consistency, data migration, stability

### Framework Tests (8 tests)
- **`test_comprehensive_evaluation_frameworks.py`** - HELM, Chatbot Arena, MT-Bench, Ragas, DeepEval

### Hierarchical Session Tests
- **`test_session_manager.py`** - Core session management functionality
- **`test_session_manager_edge_cases.py`** - Edge cases for session management
- **`test_hierarchical_system_interplay.py`** - Nuanced interactions between hierarchical memory and other systems
- **`test_hierarchical_critical_gaps.py`** - Critical gaps and weaknesses
- **`test_hierarchical_deep_analysis.py`** - Deep analysis of hierarchical system behavior
- **`test_hierarchical_hidden_failures.py`** - Hidden failures and subtle bugs
- **`test_hierarchical_data_loss_scenarios.py`** - Data loss scenarios

### Multi-Turn & Conversation Tests
- **`test_multi_turn_sessions.py`** - Multi-turn conversations and session mapping

### Adversarial Tests
- **`test_adversarial_mcp_driven.py`** - Adversarial testing using MCP tools

### Core System Tests
- **`test_agent_integration.py`** - Agent integration tests
- **`test_quality_feedback.py`** - Quality feedback loop tests
- **`test_semantic_eval.py`** - Semantic evaluation tests
- **`test_semantic_realistic.py`** - Realistic semantic evaluation scenarios
- **`test_mutation_agent.py`** - Mutation testing focused tests for agent

### Mutation Testing
- **`test_mutation_agent.py`** - Comprehensive tests designed to catch mutations in agent code
- See [MUTATION_TESTING.md](MUTATION_TESTING.md) for guide on using mutation testing

## Running Tests

### Run All Tests
```bash
pytest tests/ -v
```

### Run by Category
```bash
# Quality & semantic tests
pytest tests/test_grice_maxims.py tests/test_semantic_properties.py tests/test_behavioral_properties.py tests/test_llm_agent_behavior.py -v

# Property-based tests
pytest tests/test_quality_property_based.py tests/test_grice_property_based.py tests/test_behavioral_property_based.py -v

# Integration tests
pytest tests/test_integration_quality_systems.py -v

# Performance tests
pytest tests/test_performance_quality_systems.py -v

# Safety tests
pytest tests/test_safety_quality_systems.py -v

# Benchmark tests
pytest tests/test_benchmark_quality_metrics.py -v

# Regression tests
pytest tests/test_regression_quality_systems.py -v

# Framework tests
pytest tests/test_comprehensive_evaluation_frameworks.py -v
```

### Run by Pattern
```bash
# All quality tests
pytest tests/ -k "quality" -v

# All integration tests
pytest tests/ -k "integration" -v

# All performance tests
pytest tests/ -k "performance" -v

# All safety tests
pytest tests/ -k "safety" -v

# All benchmark tests
pytest tests/ -k "benchmark" -v

# All regression tests
pytest tests/ -k "regression" -v

# All framework tests
pytest tests/ -k "framework" -v

# All hierarchical tests
pytest tests/ -k "hierarchical or session" -v

# All property-based tests
pytest tests/ -k "property" -v

# All SSH tests
pytest tests/test_ssh_*.py tests/test_information_bottleneck.py tests/test_adaptive_reasoning_depth.py tests/test_resource_triple_metrics.py -v
```

### Run with Markers
```bash
# LLM-judged tests (may require LLM service)
pytest tests/ -m "llm_judge" -v

# Fast tests (skip slow ones)
pytest tests/ -m "not slow" -v
```

## Test Annotations

All tests are annotated with:
- **Pattern**: Testing pattern (e.g., `integration_testing`, `property_based`, `llm_judge`)
- **Opinion**: Hypothesis being tested
- **Category**: Test category (e.g., `integration_quality`, `performance_quality`)
- **Hypothesis**: What the test validates

Query annotations:
```bash
# Export annotations
pytest tests/ --co -q

# View annotation report
cat tests/TEST_ANNOTATIONS.json
```

## Evaluation Files

### Semantic Evaluation
- **`src/bop/semantic_eval.py`** - Core semantic evaluation framework
- **`src/bop/eval.py`** - Evaluation utilities

### Quality Feedback
- **`src/bop/quality_feedback.py`** - Quality feedback loop
- **`src/bop/adaptive_quality.py`** - Adaptive quality management

## Run Files

### Test Runners
- **`pytest`** - Main test runner (configured in `pyproject.toml`)
- **`tests/conftest.py`** - Pytest configuration and fixtures

### Evaluation Scripts
- **`tests/annotate_tests.py`** - Test annotation management

## Documentation

### Test Documentation
- **`tests/TEST_ANNOTATION_SUMMARY.md`** - Test annotation system overview
- **`tests/MULTI_TURN_TESTING_SUMMARY.md`** - Multi-turn testing summary
- **`tests/HIERARCHICAL_NUANCE_TESTING.md`** - Hierarchical nuance testing
- **`tests/DISTRUST_ANALYSIS.md`** - Critical gap analysis
- **`tests/ADVERSARIAL_ANALYSIS.md`** - Adversarial testing analysis
- **`tests/PROPERTY_BASED_TESTING_SUMMARY.md`** - Property-based testing summary
- **`tests/MCP_DRIVEN_QUALITY_TESTING_SUMMARY.md`** - MCP-driven quality testing
- **`tests/MCP_FINAL_COMPREHENSIVE_REPORT.md`** - Final comprehensive MCP report

### Framework Documentation
- **`tests/ANNOTATION_GUIDE.md`** - Guide for using test annotation system

## Test Statistics

- **Total Tests**: 92+ comprehensive tests
- **LLM-Judged**: 25 tests
- **Property-Based**: 32 tests
- **Integration**: 5 tests
- **Performance**: 5 tests
- **Safety**: 5 tests
- **Benchmark**: 5 tests
- **Regression**: 5 tests
- **Framework**: 8 tests
- **Hierarchical**: 7+ test files
- **Other**: 10+ test files

## Quick Reference

### Most Important Tests
1. **Integration**: `test_integration_quality_systems.py`
2. **Quality**: `test_quality_property_based.py`, `test_grice_maxims.py`
3. **Performance**: `test_performance_quality_systems.py`
4. **Safety**: `test_safety_quality_systems.py`
5. **Benchmark**: `test_benchmark_quality_metrics.py`

### Test Coverage
- ✅ Quality evaluation (Grice's maxims, semantic, behavioral)
- ✅ Property-based testing (invariants, metamorphic)
- ✅ Integration testing (component interactions)
- ✅ Performance testing (latency, throughput, memory)
- ✅ Safety testing (injection, jailbreaking, harmful content)
- ✅ Benchmark testing (HELM, Chatbot Arena, MT-Bench)
- ✅ Regression testing (backward compatibility, stability)
- ✅ Framework testing (HELM, Chatbot Arena, MT-Bench, Ragas, DeepEval)
- ✅ Hierarchical session management
- ✅ Multi-turn conversations

