# Validation and Introspection Infrastructure

## Overview

This document describes the validation and introspection system that automatically detects bugs and inconsistencies, making them visible through tests, diagnostics, and debuggable information.

## Architecture

### 1. Response Validator (`src/bop/validation.py`)

Validates response consistency and correctness:

- **`validate_source_references`**: Detects when sources are matched to synthesis instead of response text (CRITICAL bug)
- **`validate_belief_extraction`**: Detects when only first belief is extracted (MEDIUM bug)
- **`validate_topic_similarity_inputs`**: Detects empty strings, wrong data structures (LOW bug)
- **`validate_response_tiers`**: Detects length issues, empty tiers (LOW bug)
- **`validate_belief_alignment`**: Detects contradiction detection issues (MEDIUM bug)

### 2. Introspection Logger

Logs validation issues with appropriate severity:
- **Critical**: Logged as errors, visible in error logs
- **Warning**: Logged as warnings, visible in warning logs
- **Info**: Logged as info, visible in debug logs

Also adds validation metadata to response objects for programmatic access.

### 3. Integration in Agent

Validation runs automatically after each response generation:

```python
# In KnowledgeAgent.chat()
validation_issues = validate_response(response, message, self)
if validation_issues:
    IntrospectionLogger.log_validation_issues(validation_issues)
    IntrospectionLogger.log_response_metadata(response, validation_issues)
```

## How It Catches Bugs

### Bug #1: Source References Match Wrong Text

**Detection**: `validate_source_references` checks if source reference claims appear in response text. If a claim from synthesis is cited but doesn't appear in response (with semantic similarity), flags as CRITICAL.

**Test**: `test_property_source_references_match_response` - Property-based test that generates different response/synthesis pairs and validates consistency.

**Metamorphic Test**: `test_metamorphic_source_references_consistency` - Checks that paraphrased responses have consistent source attribution.

**Visibility**:
- Logged as ERROR: `[CRITICAL] source_references: Source reference cites claim from synthesis that doesn't appear in response text`
- Added to `response["metadata"]["validation_issues"]`
- Test failures in CI/CD

### Bug #2: Belief Extraction Only Gets First Belief

**Detection**: `validate_belief_extraction` counts belief indicators in message vs. extracted beliefs. If multiple indicators but only one belief, flags as WARNING.

**Test**: `test_property_belief_extraction_all_beliefs` - Property-based test with messages containing multiple belief indicators.

**Metamorphic Test**: `test_metamorphic_belief_extraction_order_independence` - Checks that belief extraction is order-independent.

**Visibility**:
- Logged as WARNING: `[WARNING] belief_extraction: Message contains 2 belief indicators but only 1 belief(s) extracted`
- Added to response metadata
- Test failures

### Bug #3: Topic Similarity Empty Strings

**Detection**: `validate_topic_similarity_inputs` checks for empty strings in recent_topics list.

**Test**: `test_property_topic_similarity_no_empty_strings` - Property-based test that validates empty string handling.

**Visibility**:
- Logged as INFO: `[INFO] topic_similarity: 1 empty topic(s) in recent_topics list`
- Added to response metadata

## Test Infrastructure

### Property-Based Tests (`tests/test_validation_auto_detection.py`)

Automatically generate test cases that would catch bugs:

1. **`test_property_source_references_match_response`**: Generates random response/synthesis pairs, validates consistency
2. **`test_property_belief_extraction_all_beliefs`**: Generates messages with multiple belief indicators
3. **`test_property_topic_similarity_no_empty_strings`**: Generates topic lists with empty strings

### Metamorphic Tests

Test that transformations preserve properties:

1. **`test_metamorphic_source_references_consistency`**: Paraphrased responses should have consistent sources
2. **`test_metamorphic_belief_extraction_order_independence`**: Belief extraction should be order-independent

### Unit Tests (`tests/test_validation_introspection.py`)

Direct tests of validation logic:

1. **`test_validate_source_references_mismatch`**: Directly tests synthesis/response mismatch detection
2. **`test_validate_belief_extraction_multiple`**: Directly tests multiple belief detection
3. **`test_validate_topic_similarity_empty_strings`**: Directly tests empty string detection
4. **`test_validate_response_tiers_length`**: Directly tests tier length validation
5. **`test_validate_belief_alignment_contradiction`**: Directly tests contradiction detection

## How Cursor/AI Agents Will See Issues

### 1. Test Failures

When bugs exist, property-based and metamorphic tests will fail:

```bash
pytest tests/test_validation_auto_detection.py -v
# FAILED test_property_source_references_match_response
# FAILED test_property_belief_extraction_all_beliefs
```

### 2. Log Messages

During execution, validation issues are logged:

```
ERROR bop.validation: [CRITICAL] source_references: Source reference cites claim from synthesis that doesn't appear in response text (in _add_source_references) | Suggestion: Match sources to actual response text, not synthesis.
```

### 3. Response Metadata

Response objects include validation issues:

```python
response["metadata"]["validation_issues"] = [
    {
        "severity": "critical",
        "category": "source_references",
        "message": "...",
        "suggestion": "Match sources to actual response text, not synthesis.",
    }
]
```

### 4. Debuggable Information

Validation issues include:
- **Location**: Which function/method has the issue
- **Suggestion**: How to fix it
- **Metadata**: Additional context (claim text, counts, etc.)

## Making Bugs Naturally Visible

### For Development

1. **Run tests regularly**: `pytest tests/test_validation_auto_detection.py`
2. **Check logs**: Look for ERROR/WARNING messages
3. **Inspect response metadata**: Check `response["metadata"]["validation_issues"]`

### For CI/CD

1. **Add to test suite**: Validation tests run automatically
2. **Fail on critical issues**: Configure pytest to fail on critical validation issues
3. **Report in PRs**: Show validation issues in PR comments

### For AI Agents (Cursor, etc.)

1. **Test failures trigger investigation**: When tests fail, agent sees the failure and can investigate
2. **Log messages provide context**: Error logs include suggestions for fixes
3. **Metadata provides structured info**: Response metadata gives programmatic access to issues
4. **Property tests generate edge cases**: Hypothesis automatically finds edge cases that trigger bugs

## Example: How Bug #1 Would Be Caught

### Scenario

1. Developer/AI makes change that breaks source reference matching
2. Property-based test runs: `test_property_source_references_match_response`
3. Test generates response="Trust is X" and synthesis="Trust is Y"
4. Validation detects mismatch
5. Test fails with clear error message
6. Log shows: `[CRITICAL] source_references: ...`
7. Response metadata includes issue with suggestion

### What Cursor Sees

```
FAILED tests/test_validation_auto_detection.py::test_property_source_references_match_response
AssertionError: Validation should catch source/reponse mismatch

ERROR logs show:
[CRITICAL] source_references: Source reference cites claim from synthesis that doesn't appear in response text
Suggestion: Match sources to actual response text, not synthesis.
```

Cursor can then:
1. Read the suggestion
2. Look at the validation code
3. Fix the bug in `_add_source_references`

## Future Enhancements

1. **Automatic Fixes**: For simple issues, automatically apply fixes
2. **Regression Detection**: Track validation issues over time, alert on regressions
3. **Integration with Quality Feedback**: Use validation issues to improve quality scores
4. **Visual Indicators**: Show validation issues in UI (CLI, web)
5. **Metrics Dashboard**: Track validation issue rates over time

## Usage

### Enable Validation (Default)

Validation runs automatically in `KnowledgeAgent.chat()`. No configuration needed.

### Disable Validation (For Testing)

```python
# In tests, you can mock validation if needed
with patch('bop.agent.validate_response', return_value=[]):
    response = await agent.chat("test")
```

### Access Validation Issues

```python
response = await agent.chat("test")
issues = response.get("metadata", {}).get("validation_issues", [])
critical_issues = [i for i in issues if i["severity"] == "critical"]
```

## Summary

The validation infrastructure makes bugs naturally visible through:

1. **Automatic detection**: Runs after every response
2. **Test coverage**: Property-based and metamorphic tests catch edge cases
3. **Clear diagnostics**: Logs, metadata, suggestions
4. **Debuggable info**: Location, context, metadata for each issue

This ensures that bugs like source reference mismatches, incomplete belief extraction, and empty string issues are caught automatically and made visible to developers and AI agents.

