# Quick Start Guide

Fastest way to discover and use all tests, evaluations, and run files.

## Discover Tests (30 seconds)

```bash
# List all test categories
python tests/run_all_tests.py --list

# View complete test index
cat tests/TEST_INDEX.md

# View quick reference
cat tests/README.md
```

## Run Tests (1 minute)

```bash
# All tests
pytest tests/ -v

# By category (quality, integration, performance, etc.)
python tests/run_all_tests.py --category quality

# By pattern (integration, safety, benchmark, etc.)
python tests/run_all_tests.py --pattern integration

# Specific files
python tests/run_all_tests.py --files test_grice_maxims.py
```

## Run Evaluations (1 minute)

```bash
# Semantic evaluation
python scripts/run_semantic_evaluation.py

# Enhanced semantic evaluation
python scripts/run_semantic_evaluation_v2.py

# Mutation testing (evaluate test quality)
just test-mutate-quick
```

## Key Files

- **`tests/TEST_INDEX.md`** - Complete test catalog
- **`tests/DISCOVERY_GUIDE.md`** - Discovery guide
- **`tests/README.md`** - Quick reference
- **`tests/run_all_tests.py`** - Unified test runner

## Test Categories

- `quality` - Quality tests (42 tests)
- `property` - Property-based tests (13 tests)
- `integration` - Integration tests (5 tests)
- `performance` - Performance tests (5 tests)
- `safety` - Safety tests (5 tests)
- `benchmark` - Benchmark tests (5 tests)
- `regression` - Regression tests (5 tests)
- `framework` - Framework tests (8 tests)
- `hierarchical` - Session management (7+ files)
- `multi_turn` - Multi-turn conversations (1 file)
- `adversarial` - Adversarial testing (1 file)
- `core` - Core system (4 files)
- `mutation` - Mutation testing (1 file)

## Quick Commands

```bash
# List categories
python tests/run_all_tests.py --list

# Run quality tests
python tests/run_all_tests.py --category quality

# Run integration tests
python tests/run_all_tests.py --category integration

# Run all tests
pytest tests/ -v
```

