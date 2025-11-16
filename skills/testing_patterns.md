# Testing Patterns Skill

**Purpose:** Guide BOP in writing effective tests and testing strategies.

**Tags:** testing, pytest, quality, best-practices

## Test Organization

### Structure
- **Test files:** `test_*.py` or `*_test.py`
- **Test directory:** `tests/` separate from `src/`
- **Test modules:** Mirror source structure
- **Fixtures:** Shared in `conftest.py`

### Test Types
- **Unit tests:** Test individual functions/classes
- **Integration tests:** Test component interactions
- **E2E tests:** Test full workflows
- **Property-based tests:** Test invariants
- **Metamorphic tests:** Test transformations

## Python Testing Best Practices

### pytest Patterns
- **Use fixtures:** For setup/teardown
- **Parametrize:** For multiple test cases
- **Markers:** `@pytest.mark.slow`, `@pytest.mark.e2e`
- **Skip with reason:** `pytest.skip(reason="...")`

### Async Testing
- **Use `pytest-asyncio`:** For async functions
- **Use `async def`:** For async test functions
- **Proper fixtures:** Use async fixtures when needed
- **No `time.sleep()`:** Use async/await instead

### Test Quality
- **Clear names:** `test_function_name_scenario`
- **One assertion per concept:** Multiple assertions OK
- **Arrange-Act-Assert:** Clear structure
- **Test edge cases:** Not just happy path

## Anti-Patterns

### ❌ Don't Do This
```python
# Bare except
try:
    do_something()
except:  # BAD
    pass

# time.sleep in tests
time.sleep(1)  # BAD - use async/await

# pytest.skip without reason
pytest.skip()  # BAD - add reason
```

### ✅ Do This Instead
```python
# Specific exception
try:
    do_something()
except ValueError:  # GOOD
    pass

# Async/await
await asyncio.sleep(0.1)  # GOOD

# Skip with reason
pytest.skip(reason="Feature not implemented")  # GOOD
```

## Test Coverage

### What to Test
- **Public APIs:** All public functions
- **Edge cases:** Boundary conditions
- **Error paths:** Exception handling
- **Integration points:** Component boundaries

### What Not to Test
- **Private methods:** Test via public API
- **Third-party code:** Assume it works
- **Trivial code:** Simple getters/setters
- **Implementation details:** Test behavior, not implementation

## Test Patterns

### Fixture Pattern
```python
@pytest.fixture
def sample_data():
    return {"key": "value"}

def test_function(sample_data):
    result = process(sample_data)
    assert result is not None
```

### Parametrization Pattern
```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input, expected):
    assert double(input) == expected
```

### Async Pattern
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

## Usage

This skill should be loaded when:
- Writing or reviewing tests
- Analyzing test coverage
- Providing testing recommendations
- Debugging test failures

