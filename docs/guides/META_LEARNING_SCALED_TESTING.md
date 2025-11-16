# Meta-Learning Scaled Testing

Comprehensive test suite for meta-learning using real datasets, augmented data, BOP self-evaluation, and intelligent hard evaluations.

## Test Suite Overview

**Total Tests**: 102+ tests across 6 test files

### Test Files

1. **`test_meta_learning.py`** (17 tests)
   - Core unit and integration tests
   - LLM-as-judge semantic evaluations

2. **`test_meta_learning_e2e.py`** (3 tests)
   - End-to-end workflow validation

3. **`test_meta_learning_comprehensive.py`** (26 tests)
   - Edge cases, performance, adversarial, property-based
   - Real-world scenarios

4. **`test_meta_learning_multiturn_judges.py`** (13 tests)
   - Multi-turn LLM judge evaluations
   - Fuzzing and property-based tests

5. **`test_meta_learning_advanced.py`** (16 tests)
   - Stress tests
   - Sophisticated multi-turn scenarios
   - Advanced fuzzing
   - Performance benchmarks
   - Deep integration tests

6. **`test_meta_learning_metamorphic.py`** (11 tests)
   - Metamorphic relations
   - Invariant tests
   - Cross-component invariants

7. **`test_meta_learning_scaled.py`** (10 tests)
   - Real dataset integration (philosophy, science, technical)
   - Augmented query testing
   - BOP-based evaluation agents
   - Multi-turn evaluation
   - Cross-domain meta-learning
   - Hard evaluations (adversarial, edge cases, consistency)

8. **`test_meta_learning_bop_integrated.py`** (6 tests)
   - BOP self-evaluation framework
   - External dataset integration (HotpotQA, FEVER)
   - Complete self-evaluation workflows
   - Multi-component evaluation
   - Research integration
   - Adaptive + meta-learning synergy

## Key Features

### 1. Real Dataset Integration

- **Philosophy Queries**: Tests on philosophical questions
- **Science Queries**: Tests on scientific questions
- **Technical Queries**: Tests on technical questions
- **HotpotQA**: Multi-hop question answering
- **FEVER**: Fact verification
- **SciFact**: Scientific fact checking

### 2. Data Augmentation

- **Rephrasing**: "What is X?" → "Can you explain X?"
- **Context Addition**: "What is X? I'm new to this topic."
- **Constraint Addition**: "What is X? Please be concise."
- **Multi-part**: "What is X? Also, what are the key concepts?"

### 3. BOP Self-Evaluation

BOP evaluates its own meta-learning capabilities:

- **`BOPSelfEvaluator`**: Uses BOP's research to evaluate meta-learning
- **`BOPEvaluationAgent`**: Uses BOP to evaluate response quality
- **Self-evaluation workflows**: Complete cycles of self-assessment

### 4. Intelligent Hard Evaluations

- **Adversarial**: Prompt injection, noise, null bytes
- **Edge Cases**: Empty queries, very long queries, repetitive queries
- **Consistency**: Similar queries should get consistent responses
- **Multi-turn**: Learning across conversation turns

### 5. Multi-Turn Evaluation Agents

- **Conversation Quality**: Evaluate improvement across turns
- **Experience Accumulation**: Track learning over time
- **Context Effectiveness**: Measure context injection impact
- **Reflection Progression**: Evaluate reflection quality over time

## Running Tests

```bash
# All meta-learning tests
uv run pytest tests/test_meta_learning*.py -v

# Scaled tests with datasets
uv run pytest tests/test_meta_learning_scaled.py -v

# BOP-integrated tests
uv run pytest tests/test_meta_learning_bop_integrated.py -v

# Advanced tests (stress, performance, deep integration)
uv run pytest tests/test_meta_learning_advanced.py -v

# Metamorphic tests (invariants)
uv run pytest tests/test_meta_learning_metamorphic.py -v

# Multi-turn and fuzzing
uv run pytest tests/test_meta_learning_multiturn_judges.py -v

# With external datasets (requires datasets package)
uv run pytest tests/test_meta_learning_bop_integrated.py::test_bop_integrated_hotpotqa_meta_learning -v
uv run pytest tests/test_meta_learning_bop_integrated.py::test_bop_integrated_fever_meta_learning -v
```

## Test Categories

### Unit Tests (14)
Core component functionality

### Integration Tests (15)
Component interactions

### E2E Tests (3)
Complete workflows

### Edge Cases (7)
Boundary conditions

### Performance Tests (2)
Speed and scalability

### Adversarial Tests (6)
Resilience to attacks

### Property-Based Tests (6)
Invariants that always hold

### Multi-Turn Tests (8)
Learning across conversations

### Fuzzing Tests (7)
Random/generated inputs

### LLM-as-Judge Tests (14)
Semantic evaluations

### Scaled Tests (10)
Real datasets and augmentation

### BOP-Integrated Tests (6)
Self-evaluation and deep integration

### Metamorphic Tests (11)
Invariant relations

### Stress Tests (3)
High load scenarios

### Deep Integration Tests (3)
Cross-component synergy

## Integration Points

### BOP Components Used in Testing

1. **KnowledgeAgent**: Main agent for all tests
2. **MetaLearner**: Core meta-learning component
3. **ResearchAgent**: For self-evaluation research
4. **StructuredOrchestrator**: For research orchestration
5. **QualityFeedbackLoop**: For quality evaluation
6. **AdaptiveQualityManager**: For adaptive learning
7. **LLMService**: For LLM-as-judge evaluations

### External Datasets

- **HotpotQA**: Multi-hop QA (via HuggingFace)
- **FEVER**: Fact verification (via HuggingFace)
- **SciFact**: Scientific fact checking (via HuggingFace)
- **Internal datasets**: Philosophy, science, technical queries

## Validation Approach

### 1. Structural Validation
- Unit tests verify components work correctly
- Integration tests verify components work together
- E2E tests verify complete workflows

### 2. Semantic Validation
- LLM-as-judge evaluates semantic properties
- BOP self-evaluation uses research capabilities
- Multi-turn agents evaluate learning progression

### 3. Robustness Validation
- Adversarial tests check resilience
- Edge case tests check boundary handling
- Fuzzing tests check random input handling

### 4. Performance Validation
- Stress tests check scalability
- Benchmarks measure speed
- Large dataset tests check efficiency

### 5. Invariant Validation
- Metamorphic tests check relations
- Property-based tests check invariants
- Cross-component tests check integration

## Success Criteria

### Functional
- ✅ All components work correctly
- ✅ Components integrate properly
- ✅ Complete workflows function

### Semantic
- ✅ Meta-learning improves responses
- ✅ Experiences accumulate correctly
- ✅ Reflection extracts insights

### Robustness
- ✅ Handles adversarial inputs
- ✅ Handles edge cases
- ✅ Handles failures gracefully

### Performance
- ✅ Scales to large datasets
- ✅ Meets latency requirements
- ✅ Efficient resource usage

### Integration
- ✅ Works with research
- ✅ Works with quality feedback
- ✅ Works with adaptive learning
- ✅ BOP evaluates itself

## Future Enhancements

- [ ] Add more external datasets (MMLU, HellaSwag, etc.)
- [ ] Add distributed testing
- [ ] Add continuous evaluation pipeline
- [ ] Add test result visualization
- [ ] Add regression detection
- [ ] Add performance regression tests

