# Mutation Testing Guide

Mutation testing evaluates test quality by introducing small changes (mutations) to the code and checking if tests catch them. If a mutation survives (tests still pass), it indicates a gap in test coverage.

**Category**: `mutation`  
**Test File**: `test_mutation_agent.py` (17 tests)  
**Target Code**: `src/bop/agent.py`

## Quick Start

```bash
# Install dependencies (includes mutmut)
uv sync --dev

# Run mutation testing on agent
just test-mutate

# Run with HTML report
just test-mutate-html

# Quick test (first 10 mutations)
just test-mutate-quick
```

## Understanding Results

### Mutation Score

The mutation score is the percentage of mutations that were killed (caught by tests):

```
Mutation score: 75%
- Killed: 45
- Survived: 15
- Timeout: 0
- Suspicious: 0
```

**Interpretation:**
- **75% score**: Good, but 15 mutations survived
- **>90% score**: Excellent test coverage
- **<50% score**: Tests need improvement

### Surviving Mutations

Surviving mutations indicate test gaps. Common patterns:

1. **Missing edge cases**: Tests don't cover boundary conditions
2. **Insufficient assertions**: Tests pass but don't verify behavior
3. **Mocked dependencies**: Tests mock too much, missing real behavior
4. **Incomplete coverage**: Some code paths aren't tested

### Example: Fixing a Surviving Mutation

```bash
# Show details of a surviving mutation
just test-mutate-show-id 42

# Apply the mutation to see what changed
just test-mutate-apply 42

# Run tests to see if they catch it
pytest tests/test_agent.py -v

# If tests pass, add a test that catches this mutation
```

## Commands

### Basic Commands

- `just test-mutate` - Run full mutation testing
- `just test-mutate-html` - Generate HTML report
- `just test-mutate-show` - Show summary of results
- `just test-mutate-quick` - Quick test (10 mutations)

### Advanced Commands

- `just test-mutate-cov` - Use coverage to focus mutations
- `just test-mutate-function FUNCTION` - Test specific function
- `just test-mutate-show-id ID` - Show specific mutation
- `just test-mutate-apply ID` - Apply mutation for debugging

## Best Practices

### 1. Focus on Critical Code

Start with core agent methods:
- `chat()` - Main interaction method
- `_generate_response()` - Response generation
- `_extract_prior_beliefs()` - Belief extraction
- `_compute_topic_similarity()` - Similarity computation

### 2. Improve Tests Based on Results

When mutations survive:

1. **Identify the pattern**: What type of mutation survived?
2. **Add targeted test**: Write a test that catches this mutation
3. **Verify**: Re-run mutation testing to confirm it's killed

### 3. Use Coverage to Guide Testing

```bash
# Run with coverage to see which mutations are in tested code
just test-mutate-cov
```

This focuses mutations on code that's actually executed by tests.

### 4. Incremental Improvement

Don't aim for 100% mutation score immediately:

1. Run mutation testing
2. Fix the easiest surviving mutations (add missing assertions)
3. Re-run to see improvement
4. Iterate on harder cases

### 5. CI Integration

Mutation testing can be slow. Consider:

- Run on pull requests (limited mutations)
- Run full suite nightly
- Focus on changed modules

## Common Mutation Types

MutMut introduces these types of mutations:

1. **Arithmetic operators**: `+` → `-`, `*` → `/`
2. **Comparison operators**: `==` → `!=`, `<` → `>`
3. **Logical operators**: `and` → `or`, `not` removal
4. **Conditional statements**: `if` → `if not`
5. **Return values**: `return True` → `return False`
6. **Method calls**: Remove or change arguments

## Example: Improving Test Coverage

**Before:**
```python
def test_agent_chat():
    agent = KnowledgeAgent()
    response = await agent.chat("Hello")
    assert "response" in response  # Too weak!
```

**After (mutation testing revealed missing assertions):**
```python
def test_agent_chat():
    agent = KnowledgeAgent()
    response = await agent.chat("Hello")
    assert "response" in response
    assert response["message"] == "Hello"  # Catches message mutation
    assert response["schema_used"] is None  # Catches schema mutation
    assert response["research_conducted"] is False  # Catches research flag mutation
    assert len(agent.conversation_history) == 2  # Catches history mutation
```

## Troubleshooting

### Mutations Timing Out

If many mutations timeout:
- Tests may be too slow
- Consider faster test doubles
- Use `--max-mutations` to limit scope

### False Positives

Some mutations may be equivalent (same behavior):
- Review surviving mutations manually
- Mark equivalent mutations as such
- Focus on meaningful differences

### Slow Execution

Mutation testing is inherently slow:
- Use `test-mutate-quick` for fast feedback
- Run full suite periodically
- Focus on critical paths first

## Integration with Existing Tests

The mutation tests work with your existing test suite:

- `tests/test_agent.py` - Basic agent tests
- `tests/test_agent_integration.py` - Integration tests
- `tests/test_agent_comprehensive.py` - Comprehensive tests
- `tests/test_mutation_agent.py` - Mutation-focused tests

All tests are run when checking if mutations are killed.

## Further Reading

- [MutMut Documentation](https://mutmut.readthedocs.io/)
- [Mutation Testing Explained](https://en.wikipedia.org/wiki/Mutation_testing)
- [Property-Based Testing](https://hypothesis.works/) - Complementary approach

