# Making Tests Discoverable and Usable

## Overview

This document describes the cohesive organization of all tests, evaluations, and run files for discoverability and usability.

## Structure

### 1. Test Index (`TEST_INDEX.md`)
Complete index of all tests organized by:
- Category (quality, integration, performance, etc.)
- Type (LLM-judged, property-based, functional)
- Purpose and coverage

### 2. Test Runner (`run_all_tests.py`)
Unified test runner with:
- Category-based execution
- Pattern-based filtering
- File-specific execution
- List all categories

### 3. Test Documentation (`README.md`)
Quick reference guide for:
- Running tests
- Test organization
- Test statistics

## Usage

### Discover Tests
```bash
# List all categories
python tests/run_all_tests.py --list

# View test index
cat tests/TEST_INDEX.md

# View README
cat tests/README.md
```

### Run Tests
```bash
# All tests
pytest tests/ -v

# By category
python tests/run_all_tests.py --category quality

# By pattern
python tests/run_all_tests.py --pattern integration

# Specific files
python tests/run_all_tests.py --files test_grice_mbopms.py
```

### Query Tests
```bash
# By keyword
pytest tests/ -k "quality" -v

# By marker
pytest tests/ -m "llm_judge" -v

# By annotation
cat tests/TEST_ANNOTATIONS.json | jq '.[] | select(.category == "quality")'
```

## Test Organization

### Categories
1. **Quality** - Grice's mbopms, semantic, behavioral properties
2. **Property-Based** - Hypothesis property tests
3. **Integration** - Component interaction tests
4. **Performance** - Latency, throughput, memory
5. **Safety** - Security and robustness
6. **Benchmark** - HELM, Chatbot Arena, MT-Bench
7. **Regression** - Backward compatibility
8. **Framework** - Comprehensive evaluation frameworks
9. **Hierarchical** - Session management
10. **Multi-Turn** - Conversation flow
11. **Adversarial** - Adversarial testing
12. **Core** - Core system functionality
13. **Mutation** - Mutation testing for test quality evaluation

### Files
- **Test files**: `test_*.py` - All test implementations
- **Runner**: `run_all_tests.py` - Unified test runner
- **Index**: `TEST_INDEX.md` - Complete test index
- **README**: `README.md` - Quick reference
- **Documentation**: Various `*.md` files for specific test areas

## Discoverability Features

1. **Test Index** - Complete catalog of all tests
2. **Test Runner** - Easy category/pattern-based execution
3. **Test Annotations** - Metadata for querying and filtering
4. **Documentation** - Comprehensive guides and summaries
5. **Organized Structure** - Clear categorization and naming

## Usability Features

1. **Multiple Entry Points** - pytest, custom runner, direct file execution
2. **Flexible Filtering** - Category, pattern, keyword, marker
3. **Clear Documentation** - README, index, guides
4. **Consistent Naming** - Predictable file and test names
5. **Annotation System** - Rich metadata for test discovery

