# Evaluation Index

Index of all evaluation files, scripts, and utilities.

## Core Evaluation Modules

### Semantic Evaluation
- **`src/bop/semantic_eval.py`** - Core semantic evaluation framework
  - `SemanticEvaluator` - Main evaluation class
  - `SemanticJudgment` - Evaluation result model
  - Methods: `evaluate_relevance`, `evaluate_completeness`, `evaluate_consistency`

### Evaluation Utilities
- **`src/bop/eval.py`** - Evaluation utilities and helpers

## Quality Management

### Quality Feedback
- **`src/bop/quality_feedback.py`** - Quality feedback loop
  - `QualityFeedbackLoop` - Main feedback loop class
  - `QualityInsights` - Insights from evaluations
  - Method: `evaluate_and_learn`

### Adaptive Quality
- **`src/bop/adaptive_quality.py`** - Adaptive quality management
  - `AdaptiveQualityManager` - Adaptive learning manager
  - `AdaptiveStrategy` - Strategy recommendations
  - Method: `get_adaptive_strategy`

## Evaluation Scripts

### Semantic Evaluation Scripts
- **`scripts/run_semantic_evaluation.py`** - Run semantic evaluation
- **`scripts/run_semantic_evaluation_v2.py`** - Enhanced semantic evaluation

## Test Evaluation Files

### Semantic Evaluation Tests
- **`tests/test_semantic_eval.py`** - Core semantic evaluation tests
- **`tests/test_semantic_evaluation.py`** - Semantic evaluation test suite
- **`tests/test_semantic_realistic.py`** - Realistic semantic evaluation scenarios
- **`tests/test_semantic_properties.py`** - Semantic property tests
- **`tests/test_semantic_aggregation.py`** - Semantic aggregation tests

### Evaluation Framework Tests
- **`tests/test_comprehensive_evaluation_frameworks.py`** - Framework tests (HELM, Chatbot Arena, MT-Bench, Ragas, DeepEval)
- **`tests/test_benchmark_quality_metrics.py`** - Benchmark metric tests
- **`tests/test_constraints_eval_framework.py`** - Constraint evaluation framework
- **`tests/test_constraints_evaluation.py`** - Constraint evaluation tests

### Comprehensive Evaluation Tests
- **`tests/test_eval_comprehensive.py`** - Comprehensive evaluation tests
- **`tests/test_eval_advanced_validation.py`** - Advanced validation tests
- **`tests/test_eval_content_diverse.py`** - Diverse content evaluation
- **`tests/test_eval_content_scenarios.py`** - Content scenario evaluation
- **`tests/test_eval_edge_cases.py`** - Edge case evaluation
- **`tests/test_eval_enhancements.py`** - Evaluation enhancements
- **`tests/test_eval_performance.py`** - Evaluation performance tests
- **`tests/test_eval_real.py`** - Real-world evaluation scenarios
- **`tests/test_eval_strengthened.py`** - Strengthened evaluation tests
- **`tests/test_eval_with_content.py`** - Content-based evaluation

## Usage

### Run Evaluations
```bash
# Semantic evaluation
python scripts/run_semantic_evaluation.py

# Enhanced semantic evaluation
python scripts/run_semantic_evaluation_v2.py
```

### Test Evaluations
```bash
# All evaluation tests
pytest tests/ -k "eval" -v

# Semantic evaluation tests
pytest tests/test_semantic_eval.py tests/test_semantic_evaluation.py -v

# Framework tests
pytest tests/test_comprehensive_evaluation_frameworks.py -v
```

## Evaluation Metrics

### Semantic Metrics
- **Relevance** - Query-response relevance
- **Completeness** - Response completeness
- **Consistency** - Consistency across responses
- **Accuracy** - Factual accuracy
- **Coherence** - Logical coherence

### Quality Metrics
- **Grice's Mbopms** - Quality, Quantity, Relation, Manner, Benevolence, Transparency
- **Semantic Properties** - Consistency, Coherence, Correctness, Appropriateness
- **Behavioral Properties** - Flow, Turn-taking, Context, Intent

### Framework Metrics
- **HELM** - Groundedness, Coherence, Fluency
- **Chatbot Arena** - Helpfulness, Elo ratings
- **MT-Bench** - Multi-turn consistency
- **Ragas** - Relevance, Faithfulness
- **DeepEval** - G-Eval, custom metrics

## Integration

Evaluations integrate with:
- **Quality Feedback Loop** - Continuous improvement
- **Adaptive Quality Manager** - Learning from evaluations
- **Hierarchical Session Manager** - Session-based tracking
- **Test Suite** - Automated validation

