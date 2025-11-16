# Test Annotation Examples

## Opinion: Multi-Turn Conversations ≈ Sessions

### Example Annotations

```python
from tests.test_annotations import annotate_test

# In your test file
def test_multi_turn_conversation():
    """Test that multi-turn conversations map to sessions."""
    annotate_test(
        "test_multi_turn_conversation",
        pattern="multi_turn_conversation",
        opinion="multi_turn_approximates_session",
        category="conversation_modeling",
        hypothesis="Multi-turn conversations map to sessions",
        description="Each conversation turn adds an evaluation to the session",
    )
    # ... test implementation
```

### Querying Annotations

```python
from tests.test_annotations import (
    get_tests_by_opinion,
    get_tests_by_pattern,
)

# Find all tests validating this opinion
tests = get_tests_by_opinion("multi_turn_approximates_session")
# Returns: ['test_multi_turn_conversation_as_session', ...]

# Find all multi-turn conversation tests
tests = get_tests_by_pattern("multi_turn_conversation")
# Returns: ['test_multi_turn_conversation_as_session', ...]
```

### Using the CLI

```bash
# List all annotations
python tests/annotate_tests.py list

# Find tests by opinion
python tests/annotate_tests.py by-opinion multi_turn_approximates_session

# Find tests by pattern
python tests/annotate_tests.py by-pattern multi_turn_conversation

# Generate report
python tests/annotate_tests.py report
```

## Common Patterns & Opinions

### Conversation Modeling
- **Pattern**: `multi_turn_conversation`
- **Opinion**: `multi_turn_approximates_session`
- **Tests**: 8 tests validating this opinion

### Performance
- **Pattern**: `write_buffering`
- **Opinion**: `buffering_reduces_io`
- **Tests**: Tests validating I/O reduction

### Scalability
- **Pattern**: `session_complexity`
- **Opinion**: `sessions_scale_to_many_evaluations`
- **Tests**: Tests with 100+ evaluations

### Learning
- **Pattern**: `adaptive_learning`
- **Opinion**: `learning_transfers_across_sessions`
- **Tests**: Cross-session learning tests

## Benefits

1. **Find Related Tests**: Quickly find all tests for a pattern/opinion
2. **Validate Hypotheses**: Systematically test opinions
3. **Generate Reports**: See what we're testing and why
4. **Document Decisions**: Annotations document our design opinions

