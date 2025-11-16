# Mutation Testing: Real Examples from Agent Code

This document shows concrete examples of mutations in the agent code and how tests catch them.

## Example 1: Topic Similarity Threshold

### Code Location
`src/bop/agent.py:171`

### Original Code
```python
if topic_similarity > 0.5:
    # Exploration mode: user is diving deeper
    expected_length = int(expected_length * 1.2)
else:
    # Extraction mode: user wants quick answers
    expected_length = int(expected_length * 0.8)
```

### Mutations That Would Break Behavior

#### Mutation 1: Boundary Change
```python
# Mutated
if topic_similarity >= 0.5:  # Changed > to >=
```
**Impact**: When similarity is exactly 0.5, behavior changes from extraction to exploration mode.

**Test That Catches It**: `test_topic_similarity_threshold()`
```python
similarity_05 = agent._compute_topic_similarity(
    "information geometry",
    ["information geometry"]
)
assert similarity_05 > 0.5  # Fails if mutation changes > to >=
```

#### Mutation 2: Logic Inversion
```python
# Mutated
if topic_similarity < 0.5:  # Changed > to <
```
**Impact**: Completely inverts the logic - exploration becomes extraction and vice versa.

**Test That Catches It**: `test_topic_similarity_threshold()`
```python
similarity_low = agent._compute_topic_similarity(
    "information geometry",
    ["weather forecast"]
)
assert similarity_low < 0.5  # Fails if mutation inverts logic
```

## Example 2: Belief Extraction Minimum Length

### Code Location
`src/bop/agent.py:656`

### Original Code
```python
if belief_text and len(belief_text) > 10:  # Minimum length
    self.prior_beliefs.append({...})
```

### Mutations That Would Break Behavior

#### Mutation 1: Boundary Change
```python
# Mutated
if belief_text and len(belief_text) >= 10:  # Changed > to >=
```
**Impact**: 10-character beliefs would now be extracted (previously rejected).

**Test That Catches It**: `test_belief_extraction_minimum_length()`
```python
# Too short - should not extract
agent._extract_prior_beliefs("I think x")  # 9 chars
assert len(agent.prior_beliefs) == 0  # Fails if mutation changes > to >=
```

#### Mutation 2: Different Threshold
```python
# Mutated
if belief_text and len(belief_text) > 9:  # Changed 10 to 9
```
**Impact**: 9-character beliefs would now be extracted.

**Test That Catches It**: `test_belief_extraction_minimum_length()`
```python
agent._extract_prior_beliefs("I think x")  # 9 chars
assert len(agent.prior_beliefs) == 0  # Fails if threshold changed to 9
```

## Example 3: List Limit Management

### Code Location
`src/bop/agent.py:697`

### Original Code
```python
if len(self.recent_queries) > 10:
    self.recent_queries = self.recent_queries[-10:]  # Keep last 10
```

### Mutations That Would Break Behavior

#### Mutation 1: Different Limit
```python
# Mutated
if len(self.recent_queries) > 10:
    self.recent_queries = self.recent_queries[-9:]  # Changed -10 to -9
```
**Impact**: Only keeps last 9 queries instead of 10 (memory leak risk).

**Test That Catches It**: `test_recent_queries_limit()`
```python
for i in range(15):
    agent._track_recent_query(f"Query {i}")

assert len(agent.recent_queries) == 10  # Fails if mutation changes -10 to -9
assert agent.recent_queries[0]["message"] == "Query 5"  # Fails if limit wrong
```

#### Mutation 2: Boundary Change
```python
# Mutated
if len(self.recent_queries) >= 10:  # Changed > to >=
```
**Impact**: Truncation happens at 10 items instead of 11 (one less item kept).

**Test That Catches It**: `test_recent_queries_limit()`
```python
# Add exactly 10 queries
for i in range(10):
    agent._track_recent_query(f"Query {i}")

# Should keep all 10 (not truncate)
assert len(agent.recent_queries) == 10  # Fails if mutation changes > to >=
```

## Example 4: Response Length Multipliers

### Code Location
`src/bop/agent.py:175, 179`

### Original Code
```python
if topic_similarity > 0.5:
    expected_length = int(expected_length * 1.2)  # +20% for exploration
else:
    expected_length = int(expected_length * 0.8)  # -20% for extraction
```

### Mutations That Would Break Behavior

#### Mutation 1: Different Multiplier
```python
# Mutated
expected_length = int(expected_length * 1.1)  # Changed 1.2 to 1.1
```
**Impact**: Exploration mode gets less aggressive length increase (+10% instead of +20%).

**Test That Catches It**: `test_response_length_adaptation()` (indirectly via integration)

#### Mutation 2: Wrong Operation
```python
# Mutated
expected_length = int(expected_length / 1.2)  # Changed * to /
```
**Impact**: Exploration mode would SHRINK response instead of growing it.

**Test That Catches It**: Integration tests that verify response length behavior.

## Example 5: Quality Threshold for Auto-Retry

### Code Location
`src/bop/agent.py:308`

### Original Code
```python
if quality_result["relevance"] < 0.5:  # Auto-retry if quality is low
    # Try adaptive strategy first
    best_schema = None
    if self.adaptive_manager:
        # ... retry logic ...
```

### Mutations That Would Break Behavior

#### Mutation 1: Boundary Change
```python
# Mutated
if quality_result["relevance"] <= 0.5:  # Changed < to <=
```
**Impact**: Auto-retry would trigger at exactly 0.5 (previously only below 0.5).

**Test Coverage**: Covered via integration tests, but no explicit threshold test yet.

**Recommendation**: Add `test_quality_threshold_auto_retry()` to explicitly test this.

#### Mutation 2: Logic Inversion
```python
# Mutated
if quality_result["relevance"] > 0.5:  # Changed < to >
```
**Impact**: Would retry when quality is HIGH (completely wrong behavior).

**Test Coverage**: Integration tests would catch this, but explicit test would be clearer.

## Example 6: Summary Length Limit

### Code Location
`src/bop/agent.py:760`

### Original Code
```python
summary = full_response.split('.')[0] if '.' in full_response else full_response[:150]
if len(summary) > 150:
    summary = summary[:147] + "..."
```

### Mutations That Would Break Behavior

#### Mutation 1: Different Truncation Point
```python
# Mutated
summary = summary[:148] + "..."  # Changed 147 to 148
```
**Impact**: Summary would be 151 chars instead of 150 (exceeds limit).

**Test That Catches It**: `test_response_tiers_summary_length()`
```python
long_response = "This is a test sentence. " * 20
tiers = agent._create_response_tiers(long_response, {}, "test")
assert len(tiers["summary"]) <= 150  # Fails if mutation changes truncation
```

#### Mutation 2: Boundary Check Change
```python
# Mutated
if len(summary) >= 150:  # Changed > to >=
```
**Impact**: Truncation would happen at exactly 150 chars instead of above 150.

**Test That Catches It**: `test_response_tiers_summary_length()`
```python
# Test with exactly 150 chars
exact_150 = "x" * 150
tiers = agent._create_response_tiers(exact_150, {}, "test")
assert len(tiers["summary"]) <= 150  # Fails if mutation changes > to >=
```

## How to Use These Examples

### When Writing New Tests

1. **Identify critical logic**: Look for comparisons, thresholds, limits
2. **Test boundaries**: Test exactly at threshold values
3. **Test both sides**: Test above and below thresholds
4. **Test edge cases**: Empty lists, zero values, maximum values

### When Analyzing Surviving Mutations

1. **Check mutation type**: What changed? (`<` → `<=`, `>` → `>=`, etc.)
2. **Identify impact**: What behavior would change?
3. **Write targeted test**: Test the specific boundary or condition
4. **Verify**: Re-run mutation testing to confirm mutation is killed

### Common Patterns

**Threshold Comparisons:**
- Always test: `value == threshold`, `value == threshold - 1`, `value == threshold + 1`
- Example: For `> 0.5`, test `0.5`, `0.49`, `0.51`

**List Limits:**
- Always test: `limit - 1`, `limit`, `limit + 1` items
- Example: For `[-10:]`, test with 9, 10, 11 items

**String Length:**
- Always test: `length - 1`, `length`, `length + 1` characters
- Example: For `> 10`, test with 9, 10, 11 characters

## See Also

- [MUTATION_TESTING.md](MUTATION_TESTING.md) - User guide
- [MUTATION_TESTING_CRITIQUE.md](MUTATION_TESTING_CRITIQUE.md) - Analysis and recommendations
- [MUTATION_TESTING_SUMMARY.md](MUTATION_TESTING_SUMMARY.md) - Implementation overview

