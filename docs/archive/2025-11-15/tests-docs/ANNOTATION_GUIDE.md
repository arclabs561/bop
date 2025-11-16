# Test Annotation Guide

## Purpose

Test annotations allow us to categorize tests by:
- **Patterns**: What behavior/pattern is being tested
- **Opinions**: What hypothesis/opinion is being validated
- **Categories**: How to group related tests

This helps us:
1. Find all tests for a specific pattern
2. Validate opinions/hypotheses systematically
3. Understand test coverage by category
4. Generate reports of what we're testing

## Usage

### Basic Annotation

```python
from tests.test_annotations import annotate_test

# In your test file
annotate_test(
    "test_multi_turn_conversation",
    pattern="multi_turn_conversation",
    opinion="multi_turn_approximates_session",
    category="conversation_modeling",
    hypothesis="Multi-turn conversations map to sessions",
    description="Each conversation turn adds an evaluation to the session",
)
```

### Querying Annotations

```python
from tests.test_annotations import (
    get_tests_by_pattern,
    get_tests_by_opinion,
    get_tests_by_category,
)

# Find all tests for a pattern
tests = get_tests_by_pattern("multi_turn_conversation")

# Find all tests validating an opinion
tests = get_tests_by_opinion("multi_turn_approximates_session")

# Find all tests in a category
tests = get_tests_by_category("conversation_modeling")
```

## Common Patterns

### Conversation Patterns
- `multi_turn_conversation`: Multi-turn dialogue
- `session_lifecycle`: Session creation, use, closure
- `context_accumulation`: Context building across turns

### Performance Patterns
- `write_buffering`: Batching writes
- `lazy_loading`: On-demand loading
- `indexing`: Fast queries

### Learning Patterns
- `adaptive_learning`: Strategy improvement
- `cross_session_learning`: Learning across sessions
- `experience_replay`: Replaying past interactions

## Common Opinions

### Conversation Modeling
- `multi_turn_approximates_session`: Conversations ≈ sessions
- `context_accumulates`: Context builds across turns
- `quality_improves_across_turns`: Later turns benefit from earlier

### Performance
- `buffering_reduces_io`: Write buffering reduces I/O
- `indexing_speeds_queries`: Indexing makes queries faster
- `lazy_loading_scales`: Lazy loading scales to many sessions

### Learning
- `learning_transfers_across_sessions`: Patterns transfer
- `adaptive_strategies_improve`: Strategies get better over time
- `replay_consolidates_learning`: Replay helps learning

## Categories

- `conversation_modeling`: How conversations map to sessions
- `performance`: Performance optimizations
- `scalability`: Scaling to large data
- `error_handling`: Error recovery
- `adaptive_learning`: Learning and adaptation
- `edge_cases`: Edge cases and boundaries
- `lifecycle_management`: Session lifecycle
- `data_integrity`: Data validation and checksums

## Example: Multi-Turn Conversation

```python
@pytest.mark.asyncio
async def test_multi_turn_conversation_as_session():
    """
    Test that multi-turn conversations map to sessions.
    
    Pattern: Multi-turn conversation
    Opinion: Each conversation turn ≈ session evaluation
    Category: Conversation modeling
    """
    # Test implementation...
    pass

# Annotate it
annotate_test(
    "test_multi_turn_conversation_as_session",
    pattern="multi_turn_conversation",
    opinion="multi_turn_approximates_session",
    category="conversation_modeling",
    hypothesis="Multi-turn conversations map to sessions",
)
```

## Generating Reports

After running tests, annotations are automatically exported to:
- `test_annotations.json`: Machine-readable format
- `TEST_ANNOTATIONS_REPORT.md`: Human-readable report

You can also generate reports manually:

```python
from tests.test_annotations import generate_annotation_report
print(generate_annotation_report())
```

## Running Tests by Annotation

```bash
# Run all tests for a pattern (requires pytest markers)
pytest -m pattern=multi_turn_conversation

# Run all tests for an opinion
pytest -m opinion=multi_turn_approximates_session

# Run all tests in a category
pytest -m category=conversation_modeling
```

