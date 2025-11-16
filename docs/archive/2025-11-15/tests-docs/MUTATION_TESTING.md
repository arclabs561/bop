# Mutation Testing Guide

Mutation testing evaluates test quality by introducing small changes (mutations) to the code and checking if tests catch them. If a mutation survives (tests still pass), it indicates a gap in test coverage.

**Category**: `mutation`  
**Test File**: `test_mutation_agent.py` (26 tests)  
**Target Code**: `src/bop/agent.py` (913 lines)

**Quick Links:**
- [Critique & Analysis](MUTATION_TESTING_CRITIQUE.md) - Deep dive into issues and improvements
- [Implementation Summary](MUTATION_TESTING_SUMMARY.md) - What was built and why

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
- **>90% score**: Excellent test coverage (most mutations caught)
- **75-90% score**: Good coverage (some gaps to address)
- **50-75% score**: Moderate coverage (significant gaps)
- **<50% score**: Tests need substantial improvement

**For Agent Code:**
- **Target**: >80% mutation score (complex logic, many conditionals)
- **Baseline**: TBD (run full test to establish)
- **Focus**: Threshold logic and boundary conditions are most critical

### Surviving Mutations

Surviving mutations indicate test gaps. Common patterns in agent code:

1. **Missing threshold tests**: Comparison operators (`<`, `>`, `==`) not explicitly tested
   - Example: `if quality < 0.5:` mutation to `if quality <= 0.5:` survives
   - Fix: Add test that verifies exact threshold behavior

2. **Missing boundary tests**: Edge cases at limits not covered
   - Example: `len(text) > 10` mutation to `len(text) >= 10` survives
   - Fix: Test with exactly 10 characters

3. **Insufficient assertions**: Tests pass but don't verify specific behavior
   - Example: Test checks `response is not None` but doesn't verify field values
   - Fix: Add specific assertions for each field

4. **Incomplete path coverage**: Some conditional branches not exercised
   - Example: Quality feedback disabled path not tested
   - Fix: Test both enabled and disabled paths

5. **Equivalent mutations**: Some mutations produce same behavior (not a bug)
   - Example: `x * 1.2` vs `x + (x * 0.2)` (mathematically equivalent)
   - Action: Document as equivalent, focus on meaningful differences

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
- `just test-mutate-quick` - Quick test (limited mutations, see config)

### Advanced Commands

- `just test-mutate-cov` - Use coverage to focus mutations
- `just test-mutate-function FUNCTION` - Test specific function
- `just test-mutate-show-id ID` - Show specific mutation
- `just test-mutate-apply ID` - Apply mutation for debugging

## Best Practices

### 1. Focus on Critical Code

Start with core agent methods and their critical logic:

**High Priority (Threshold Logic):**
- `chat()` line 308: Quality threshold (`< 0.5`) for auto-retry
- `chat()` line 171: Topic similarity threshold (`> 0.5`) for exploration/extraction mode
- `chat()` line 321: Confidence threshold (`> 0.6`) for schema selection

**Medium Priority (Boundary Conditions):**
- `_extract_prior_beliefs()` line 656: Minimum length check (`> 10`)
- `_create_response_tiers()` line 760: Summary length limit (`<= 150`)
- `_compute_topic_similarity()` line 732: Jaccard similarity calculation

**Lower Priority (But Still Important):**
- `_generate_response()` line 175: Response length multipliers (`* 1.2`, `* 0.8`)
- List management: `[-3:]`, `[-10:]` limits for beliefs and queries

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

MutMut introduces these types of mutations. Here are examples from the agent code:

### 1. Comparison Operators (Most Critical for Agent)
```python
# Original (line 171)
if topic_similarity > 0.5:  # Exploration mode

# Mutations that would break behavior:
if topic_similarity >= 0.5:  # Changes boundary behavior
if topic_similarity < 0.5:   # Inverts logic completely
if topic_similarity == 0.5:  # Only matches exact value
```

### 2. Threshold Values
```python
# Original (line 308)
if quality_result["relevance"] < 0.5:  # Auto-retry threshold

# Mutations:
if quality_result["relevance"] <= 0.5:  # Includes 0.5 (different behavior)
if quality_result["relevance"] < 0.6:   # Different threshold
```

### 3. Arithmetic Operations
```python
# Original (line 175)
expected_length = int(expected_length * 1.2)  # Exploration mode multiplier

# Mutations:
expected_length = int(expected_length * 1.1)  # Different multiplier
expected_length = int(expected_length / 1.2)   # Division instead
expected_length = int(expected_length + 1.2)   # Addition instead
```

### 4. List Slicing
```python
# Original (line 250)
for b in self.prior_beliefs[-3:]:  # Last 3 beliefs

# Mutations:
for b in self.prior_beliefs[-2:]:  # Last 2 (different count)
for b in self.prior_beliefs[:3]:   # First 3 (wrong direction)
```

### 5. String Length Checks
```python
# Original (line 656)
if belief_text and len(belief_text) > 10:  # Minimum length

# Mutations:
if belief_text and len(belief_text) >= 10:  # Includes 10
if belief_text and len(belief_text) > 9:    # Different threshold
```

### 6. Conditional Logic
```python
# Original (line 321)
if strategy.confidence > 0.6:  # Schema selection confidence

# Mutations:
if strategy.confidence >= 0.6:  # Boundary change
if not strategy.confidence > 0.6:  # Inverted logic
```

## Examples: Improving Test Coverage

### Example 1: Threshold Logic

**Before (weak test):**
```python
def test_topic_similarity():
    agent = KnowledgeAgent()
    similarity = agent._compute_topic_similarity("test", ["test"])
    assert similarity > 0  # Too weak - doesn't catch threshold mutations!
```

**After (mutation testing revealed threshold needs explicit testing):**
```python
def test_topic_similarity_threshold():
    """Test topic similarity threshold (0.5) for exploration/extraction mode."""
    agent = KnowledgeAgent()
    
    # Test exactly at threshold - should be > 0.5 (exploration mode)
    similarity_high = agent._compute_topic_similarity(
        "information geometry",
        ["information geometry"]
    )
    assert similarity_high > 0.5  # Catches mutations: >=, <, ==
    
    # Test below threshold - should be < 0.5 (extraction mode)
    similarity_low = agent._compute_topic_similarity(
        "information geometry",
        ["weather forecast"]
    )
    assert similarity_low < 0.5  # Catches mutations: <=, >, ==
```

### Example 2: Boundary Conditions

**Before:**
```python
def test_belief_extraction():
    agent = KnowledgeAgent()
    agent._extract_prior_beliefs("I think trust is important")
    assert len(agent.prior_beliefs) > 0  # Doesn't test minimum length!
```

**After:**
```python
def test_belief_extraction_minimum_length():
    """Test belief extraction minimum length threshold (10 chars)."""
    agent = KnowledgeAgent()
    
    # Too short - should not extract (catches > 10 → >= 10 mutation)
    agent._extract_prior_beliefs("I think x")
    assert len(agent.prior_beliefs) == 0
    
    # Long enough - should extract (catches > 10 → > 9 mutation)
    agent.prior_beliefs = []
    agent._extract_prior_beliefs("I think trust is important for systems")
    assert len(agent.prior_beliefs) > 0
    assert len(agent.prior_beliefs[0]["text"]) > 10
```

### Example 3: List Limits

**Before:**
```python
def test_recent_queries():
    agent = KnowledgeAgent()
    agent._track_recent_query("test")
    assert len(agent.recent_queries) > 0  # Doesn't test limit!
```

**After:**
```python
def test_recent_queries_limit():
    """Test recent queries limit (10 items)."""
    agent = KnowledgeAgent()
    
    # Add 15 queries
    for i in range(15):
        agent._track_recent_query(f"Query {i}")
    
    # Should only keep last 10 (catches [-10:] → [-9:] or [-11:] mutations)
    assert len(agent.recent_queries) == 10
    assert agent.recent_queries[0]["message"] == "Query 5"  # First of last 10
    assert agent.recent_queries[-1]["message"] == "Query 14"  # Last
```

## Troubleshooting

### Stats Collection Errors

**Symptom**: Import errors during stats collection phase
```
ERROR collecting tests/test_adaptive_quality.py
ModuleNotFoundError: No module named 'bop.quality_feedback'
```

**Cause**: Mutmut copies files to `mutants/` directory and tries to import all tests during discovery.

**Solution**: 
- The `--ignore` flag in runner command helps but isn't perfect
- This is a known mutmut limitation
- **Workaround**: The actual mutation testing still works; stats collection may fail but mutations are tested correctly

**Status**: Known issue, workaround applied. See [MUTATION_TESTING_CRITIQUE.md](MUTATION_TESTING_CRITIQUE.md) for details.

### Mutations Timing Out

If many mutations timeout:
- Tests may be too slow
- Consider faster test doubles
- Use `max_mutations` in `pyproject.toml` to limit scope
- Focus on specific functions: `just test-mutate-function FUNCTION`

### False Positives (Equivalent Mutations)

Some mutations may be equivalent (same behavior):
- Example: `len(x) > 10` vs `len(x) >= 11` (same behavior for integers)
- Review surviving mutations manually: `just test-mutate-show-id ID`
- Apply mutation to inspect: `just test-mutate-apply ID`
- Document equivalent mutations for future reference

### Slow Execution

Mutation testing is inherently slow:
- **Generating mutants**: ~10 seconds for agent.py
- **Testing each mutation**: Depends on test suite speed (~1-2 seconds per mutation)
- **Full run (50 mutations)**: ~1-2 minutes
- **Recommendation**: 
  - Use `just test-mutate-quick` for fast feedback (limited mutations)
  - Run full suite before releases
  - Focus on critical paths first

## Integration with Existing Tests

The mutation tests work with your existing test suite. When mutmut runs, it executes:

- `tests/test_agent.py` - Basic agent tests (6 tests)
- `tests/test_agent_integration.py` - Integration tests
- `tests/test_agent_comprehensive.py` - Comprehensive tests
- `tests/test_mutation_agent.py` - Mutation-focused tests (26 tests)

**All tests are run** when checking if mutations are killed. This ensures comprehensive coverage.

### Running Mutation Tests Directly

You can also run mutation tests directly (without mutmut):

```bash
# Run mutation tests only
pytest tests/test_mutation_agent.py -v

# Run via test runner
python tests/run_all_tests.py --category mutation
```

This is useful for:
- Quick validation that mutation tests pass
- Debugging specific mutation test failures
- Understanding what the mutation tests cover

## Configuration

Mutation testing is configured in `pyproject.toml`:

```toml
[tool.mutmut]
paths_to_mutate = ["src/bop/agent.py"]
backup = false
runner = "PYTHONPATH=.:src uv run pytest tests/test_agent.py ... -x --ignore=tests/test_adaptive_quality.py"
tests_dir = ["tests"]
max_mutations = 50
debug = false
```

**Key Settings:**
- `max_mutations = 50`: Limits mutations for faster iteration (edit to change)
- `paths_to_mutate`: Currently targets agent.py only
- `runner`: Direct pytest command with PYTHONPATH and ignore flags
- `backup = false`: Don't create backups (mutmut restores automatically)

## Related Documentation

- **[MUTATION_TESTING_CRITIQUE.md](MUTATION_TESTING_CRITIQUE.md)** - Deep analysis:
  - Current state and issues identified
  - Refinements made and remaining problems
  - Critical logic paths with line numbers
  - Value assessment (high/medium/low priority areas)
  - Test suite breakdown (26 tests by category)

- **[MUTATION_TESTING_SUMMARY.md](MUTATION_TESTING_SUMMARY.md)** - Implementation overview:
  - What was built and why
  - Key insights from critique
  - Practical recommendations by use case
  - Known limitations and workarounds
  - Success metrics and next phase goals

## Real Examples

See [MUTATION_TESTING_EXAMPLES.md](MUTATION_TESTING_EXAMPLES.md) for:
- Concrete mutation examples from agent code
- How tests catch specific mutations
- Patterns for writing mutation-resistant tests
- Common mutation types and their impacts

## Further Reading

- [MutMut Documentation](https://mutmut.readthedocs.io/)
- [Mutation Testing Explained](https://en.wikipedia.org/wiki/Mutation_testing)
- [Property-Based Testing](https://hypothesis.works/) - Complementary approach

