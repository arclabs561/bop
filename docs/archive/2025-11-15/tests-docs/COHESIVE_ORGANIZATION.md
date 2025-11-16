# Cohesive Test Suite Organization

## Overview

All tests, evaluations, and run files are now organized for discoverability and usability.

## Key Files

### Discovery & Navigation
1. **`TEST_INDEX.md`** - Complete test index with all categories
2. **`DISCOVERY_GUIDE.md`** - Quick discovery guide
3. **`README.md`** - Quick reference
4. **`ORGANIZATION.md`** - Complete organization structure
5. **`EVALUATION_INDEX.md`** - Evaluation files index
6. **`RUNFILES_INDEX.md`** - Run files index

### Execution
1. **`run_all_tests.py`** - Unified test runner
2. **`annotate_tests.py`** - Test annotation management
3. **`conftest.py`** - Pytest configuration

## Quick Start

### Discover Tests
```bash
# List all categories
python tests/run_all_tests.py --list

# View test index
cat tests/TEST_INDEX.md

# View discovery guide
cat tests/DISCOVERY_GUIDE.md
```

### Run Tests
```bash
# All tests
pytest tests/ -v

# By category
python tests/run_all_tests.py --category quality

# By pattern
python tests/run_all_tests.py --pattern integration
```

### Run Evaluations
```bash
python scripts/run_semantic_evaluation.py
```

## Test Statistics

- **Total Tests**: 92+ comprehensive tests
- **Test Files**: 89+ test files
- **Categories**: 12 test categories
- **Frameworks**: 5 evaluation frameworks (HELM, Chatbot Arena, MT-Bench, Ragas, DeepEval)

## Organization Benefits

1. **Discoverable** - Clear index and guides
2. **Usable** - Multiple execution methods
3. **Organized** - Clear categorization
4. **Documented** - Comprehensive documentation
5. **Annotated** - Rich metadata for querying
