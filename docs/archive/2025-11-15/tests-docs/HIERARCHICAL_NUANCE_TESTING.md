# Hierarchical Memory Nuance Testing

## Overview

Tests for nuanced interplay between hierarchical memory and complex systems, including:
- Hierarchical session management interactions
- Quality feedback loop integration
- Adaptive learning across sessions
- Unified storage deduplication
- Experience replay mechanisms
- Cross-session learning patterns

## Test Categories

### 1. System Interplay Tests (10 tests)

Tests that validate interactions between different systems:

1. **`test_hierarchical_quality_feedback_integration`**
   - Validates quality feedback learns from hierarchical session structure
   - Tests group-aware quality feedback

2. **`test_cross_session_adaptive_learning_nuances`**
   - Tests adaptive manager recognizing patterns across session groups
   - Validates cross-group pattern recognition

3. **`test_unified_storage_deduplication_nuances`**
   - Tests deduplication between flat history and hierarchical sessions
   - Validates preservation of both views

4. **`test_hierarchical_replay_learning_nuances`**
   - Tests replay respecting hierarchical structure
   - Validates group-level pattern learning

5. **`test_session_group_statistics_nuances`**
   - Tests group-level statistics aggregation
   - Validates pattern revelation at group level

6. **`test_quality_feedback_session_context_nuances`**
   - Tests quality feedback using session context
   - Validates context-aware quality judgments

7. **`test_adaptive_strategy_session_awareness`**
   - Tests adaptive strategy selection based on session context
   - Validates context-aware strategy selection

8. **`test_hierarchical_learning_consolidation`**
   - Tests learning consolidation at multiple levels
   - Validates evaluation → session → group → cross-group learning

9. **`test_session_lifecycle_quality_interaction`**
   - Tests quality metrics persisting through lifecycle
   - Validates metrics accessibility after closure

10. **`test_buffer_flush_quality_persistence`**
    - Tests quality data persistence through buffering
    - Validates correct persistence despite buffering delays

### 2. LLM Judge Tests (5 tests)

Tests using LLM judges for semantic/behavioral validation:

1. **`test_llm_judge_hierarchical_learning_quality`**
   - Judges whether hierarchical learning improves quality
   - Validates adaptive strategy effectiveness

2. **`test_llm_judge_session_context_relevance`**
   - Judges whether session context improves relevance
   - Validates context-aware responses

3. **`test_llm_judge_adaptive_strategy_selection`**
   - Judges adaptive strategy appropriateness
   - Validates strategy selection quality

4. **`test_llm_judge_cross_session_learning_effectiveness`**
   - Judges cross-session learning effectiveness
   - Validates performance improvement across sessions

5. **`test_llm_judge_group_pattern_coherence`**
   - Judges coherence of patterns within groups
   - Validates group-level pattern recognition

## Key Nuances Tested

### Hierarchical Learning
- Learning at multiple levels (evaluation, session, group, cross-group)
- Pattern recognition across groups
- Consolidation of learning across hierarchy

### Quality Feedback Integration
- Group-aware quality feedback
- Session context in quality judgments
- Quality metrics through lifecycle

### Adaptive Learning
- Cross-session pattern recognition
- Context-aware strategy selection
- Group-level pattern awareness

### Storage and Persistence
- Deduplication between views
- Buffer flush persistence
- Lifecycle metric preservation

### Replay Mechanisms
- Hierarchical structure respect
- Group-level pattern learning
- Cross-group replay

## Running Tests

```bash
# Run all hierarchical nuance tests
uv run pytest tests/test_hierarchical_system_interplay.py -v
uv run pytest tests/test_llm_judge_nuances.py -v

# Run specific test
uv run pytest tests/test_hierarchical_system_interplay.py::test_hierarchical_quality_feedback_integration -v

# Run with LLM judges (requires LLM service)
uv run pytest tests/test_llm_judge_nuances.py -v
```

## Test Annotations

All tests are annotated with:
- **Pattern**: `hierarchical_memory`
- **Opinion**: Specific opinion being validated
- **Category**: `system_interplay` or `llm_judged`

Query tests:
```bash
uv run python tests/annotate_tests.py by-pattern hierarchical_memory
```

## Coverage

✅ **System Interplay**: 10 tests covering interactions
✅ **LLM Judges**: 5 tests for semantic validation
✅ **Hierarchical Learning**: Multiple levels tested
✅ **Quality Integration**: Context-aware quality feedback
✅ **Adaptive Learning**: Cross-session and group patterns
✅ **Storage Nuances**: Deduplication and persistence
✅ **Replay Mechanisms**: Hierarchical structure respect

## Future Enhancements

Potential additional nuance tests:
- Temporal pattern recognition across groups
- Multi-level learning consolidation validation
- Complex query decomposition with hierarchical context
- Quality feedback loop stability over time
- Adaptive strategy convergence patterns

