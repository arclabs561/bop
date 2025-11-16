# Meta-Learning Validation

This document describes the validation approach for BOP's meta-learning capabilities: self-reflection, tool meta-learning, and dynamic context engineering.

## Test Coverage

### Unit Tests (`tests/test_meta_learning.py`) - 14 tests

**ExperienceStore Tests:**
- ✅ Initialization
- ✅ Add and retrieve experiences
- ✅ Persistence across instances
- ✅ Experience limit (50 per query type)
- ✅ Context formatting

**MetaLearner Tests:**
- ✅ Initialization
- ✅ Context experience retrieval
- ✅ Context injection enable/disable
- ✅ Reflection on completion
- ✅ Reflection enable/disable
- ✅ Graceful handling of missing LLM
- ✅ Verified reflection with ground truth

**Integration Tests:**
- ✅ Experience injection into research queries
- ✅ Automatic reflection after quality evaluation

### End-to-End Tests (`tests/test_meta_learning_e2e.py`) - 3 tests

- ✅ Full workflow: query → reflection → experience storage → context injection
- ✅ Cross-query-type learning
- ✅ Graceful degradation (failures don't break system)

### Comprehensive Tests (`tests/test_meta_learning_comprehensive.py`) - 26 tests

**Edge Cases:**
- ✅ Empty query type handling
- ✅ Very long reflection text (truncation)
- ✅ Special characters in queries/responses
- ✅ Concurrent access
- ✅ No storage path (in-memory only)
- ✅ Empty tools list
- ✅ None quality score

**Performance Tests:**
- ✅ Large dataset (100 experiences)
- ✅ Context formatting performance

**Adversarial Tests:**
- ✅ Malformed JSON data
- ✅ Corrupted file handling
- ✅ Invalid query type
- ✅ LLM failure during reflection
- ✅ LLM timeout handling

**Property-Based Tests:**
- ✅ Idempotency (adding same experience)
- ✅ Ordering (verified > self, recent > old)
- ✅ Limit property (always respected)

**Integration Tests:**
- ✅ Multi-turn conversations
- ✅ Research with experience injection
- ✅ Adaptive learning integration
- ✅ Cross-session persistence

**Real-World Scenarios:**
- ✅ Realistic workflow
- ✅ Different query types

**LLM-as-Judge Tests:**
- ✅ Reflection generalizability
- ✅ Experience ranking
- ✅ Meta-learning improvement

### Multi-Turn & Fuzzing Tests (`tests/test_meta_learning_multiturn_judges.py`) - 13 tests

**Multi-Turn LLM Judge Tests:**
- ⏭️ Multi-turn conversation quality (requires LLM)
- ⏭️ Experience accumulation (requires LLM)
- ⏭️ Context injection effectiveness (requires LLM)
- ⏭️ Reflection quality progression (requires LLM)

**Fuzzing Tests:**
- ✅ Random/malformed inputs to experience store
- ✅ Random inputs to reflection
- ✅ Random queries to agent
- ✅ Concurrent fuzzing
- ✅ Edge case context injection
- ✅ Prompt injection attempts
- ✅ File operation fuzzing

**Property-Based Tests (Hypothesis):**
- ✅ Experience store with any text inputs
- ✅ Limit property with varying sizes

### LLM-as-Judge Tests

For hard-to-test semantic properties, we use LLM-as-judge evaluation:

1. **Reflection Quality** (`test_llm_judge_reflection_quality`):
   - Evaluates if reflections identify what worked well
   - Checks for generalizable insights
   - Validates actionability

2. **Experience Relevance** (`test_llm_judge_experience_relevance`):
   - Evaluates if experiences are relevant to new queries
   - Checks if insights would help improve responses
   - Validates tool recommendations

3. **Context Injection Effectiveness** (`test_llm_judge_context_injection_effectiveness`):
   - Compares responses with/without experience context
   - Evaluates accuracy, completeness, and best practices
   - Validates that experience context helps (or at least doesn't hurt)

## Running Tests

```bash
# Run all meta-learning tests
uv run pytest tests/test_meta_learning*.py -v

# Run only unit tests
uv run pytest tests/test_meta_learning.py -v

# Run only E2E tests
uv run pytest tests/test_meta_learning_e2e.py -v

# Run comprehensive tests
uv run pytest tests/test_meta_learning_comprehensive.py -v

# Run multi-turn and fuzzing tests
uv run pytest tests/test_meta_learning_multiturn_judges.py -v

# Run only fuzzing tests
uv run pytest tests/test_meta_learning_multiturn_judges.py -k fuzz -v

# Run LLM-as-judge tests (requires LLM service)
uv run pytest tests/test_meta_learning*.py -k "llm_judge" -v

# Run property-based tests
uv run pytest tests/test_meta_learning_multiturn_judges.py -k "property_based" -v

# Run with coverage
uv run pytest tests/test_meta_learning*.py --cov=bop.meta_learning --cov-report=html
```

## Validation Results

### Current Status

- ✅ **90+ non-LLM tests passing**
- ⏭️ **12+ LLM-as-judge tests** (skipped if LLM service unavailable)
- ✅ **Total: 102+ tests** across 8 test files

### Test Breakdown

- **Unit Tests**: 14/14 passing
- **E2E Tests**: 3/3 passing
- **Comprehensive Tests**: 23/26 passing (3 LLM judge tests skipped)
- **Multi-Turn & Fuzzing**: 9/13 passing (4 LLM judge tests skipped)
- **Advanced Tests**: 13/16 passing (3 LLM judge tests skipped)
- **Metamorphic Tests**: 11/11 passing
- **Scaled Tests**: 10/10 passing
- **BOP-Integrated Tests**: 4/6 passing (2 require external datasets)

### Test Files

1. `test_meta_learning.py` - Core unit and integration (17 tests)
2. `test_meta_learning_e2e.py` - End-to-end workflows (3 tests)
3. `test_meta_learning_comprehensive.py` - Edge cases, performance (26 tests)
4. `test_meta_learning_multiturn_judges.py` - Multi-turn and fuzzing (13 tests)
5. `test_meta_learning_advanced.py` - Stress, performance, deep integration (16 tests)
6. `test_meta_learning_metamorphic.py` - Invariants and relations (11 tests)
7. `test_meta_learning_scaled.py` - Real datasets and augmentation (10 tests)
8. `test_meta_learning_bop_integrated.py` - BOP self-evaluation (6 tests)

See `docs/guides/META_LEARNING_SCALED_TESTING.md` for comprehensive details.

### Key Validations

1. **Experience Storage**: Experiences are stored, persisted, and retrieved correctly
2. **Context Injection**: Experience context is injected before research and response generation
3. **Reflection**: Automatic reflection happens after quality evaluation
4. **Graceful Degradation**: System continues working even if meta-learning components fail
5. **Query Type Classification**: Experiences are organized by query type for relevance

## Manual Validation

To manually validate meta-learning:

1. **Check Experience Storage**:
   ```python
   from bop.agent import KnowledgeAgent
   
   agent = KnowledgeAgent(enable_quality_feedback=True)
   response = await agent.chat("What is d-separation?", use_research=True)
   
   # Check if reflection happened
   if "meta_reflection" in response:
       print("Reflection stored:", response["meta_reflection"][:100])
   
   # Check experiences
   experiences = agent.meta_learner.experience_store.get_relevant_experiences("factual", limit=5)
   print(f"Stored {len(experiences)} experiences")
   ```

2. **Verify Context Injection**:
   ```python
   # First query stores experience
   await agent.chat("What is trust?", use_research=True)
   
   # Second similar query should use experience
   # Check logs for "Injecting X chars of experience context"
   response = await agent.chat("What is d-separation?", use_research=True)
   ```

3. **Inspect Experience File**:
   ```bash
   cat data/results/experiences.json
   ```

## Future Enhancements

- [ ] Add property-based tests for experience relevance
- [ ] Add metamorphic tests (similar queries should get similar experiences)
- [ ] Add performance tests (experience retrieval should be fast)
- [ ] Add adversarial tests (malformed experiences shouldn't break system)
- [ ] Add cross-session learning tests (experiences should persist across sessions)

