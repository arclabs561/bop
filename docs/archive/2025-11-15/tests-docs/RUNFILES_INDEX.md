# Run Files Index

Index of all run files, scripts, and execution utilities.

## Test Runners

### Unified Test Runner
- **`tests/run_all_tests.py`** - Unified test runner with category/pattern support
  - Category-based execution
  - Pattern-based filtering
  - File-specific execution
  - List all categories

### Pytest Configuration
- **`pyproject.toml`** - Pytest configuration
  - Test paths
  - Markers
  - Python file patterns

### Test Configuration
- **`tests/conftest.py`** - Pytest fixtures and hooks
  - Custom fixtures
  - Test annotations export
  - Session hooks

## Evaluation Scripts

### Semantic Evaluation
- **`scripts/run_semantic_evaluation.py`** - Run semantic evaluation
- **`scripts/run_semantic_evaluation_v2.py`** - Enhanced semantic evaluation

## Usage

### Run All Tests
```bash
# Using pytest
pytest tests/ -v

# Using unified runner
python tests/run_all_tests.py
```

### Run by Category
```bash
python tests/run_all_tests.py --category quality
python tests/run_all_tests.py --category integration
python tests/run_all_tests.py --category performance
```

### Run by Pattern
```bash
python tests/run_all_tests.py --pattern integration
python tests/run_all_tests.py --pattern safety
```

### Run Specific Files
```bash
python tests/run_all_tests.py --files test_grice_maxims.py
```

### List Categories
```bash
python tests/run_all_tests.py --list
```

### Run Evaluations
```bash
python scripts/run_semantic_evaluation.py
python scripts/run_semantic_evaluation_v2.py
```

## Test Annotations

### Annotation Management
- **`tests/annotate_tests.py`** - Interactive test annotation management
- **`tests/test_annotations.py`** - Test annotation utilities
- **`tests/test_annotations.json`** - Stored annotations

### Export Annotations
```bash
# Automatic export after test run
pytest tests/ -v

# Manual export
python tests/annotate_tests.py export
```

## Integration

All run files integrate with:
- **Test Suite** - Comprehensive test coverage
- **Evaluation Framework** - Semantic and quality evaluation
- **Documentation** - Test index and guides

