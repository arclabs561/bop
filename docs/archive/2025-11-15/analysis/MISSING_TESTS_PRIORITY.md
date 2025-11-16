# Missing Tests Priority List

## Critical (Must Add Before Production)

### 1. Source References (`_add_source_references`)
**Status**: ❌ ZERO TESTS
**Impact**: HIGH - Used in production, affects user experience
**Tests Needed**:
- `test_add_source_references_format` - Validate citation format
- `test_add_source_references_with_research` - Test with research results
- `test_add_source_references_without_research` - Test without research
- `test_add_source_references_multiple_sources` - Test multiple sources

### 2. Topic Similarity (`_compute_topic_similarity`)
**Status**: ⚠️ EDGE CASES ONLY
**Impact**: HIGH - Affects context-dependent adaptation
**Tests Needed**:
- `test_topic_similarity_computation` - Test Jaccard similarity
- `test_topic_similarity_exploration_mode` - Test exploration mode trigger
- `test_topic_similarity_extraction_mode` - Test extraction mode trigger
- `test_topic_similarity_with_recent_queries` - Test with query history

### 3. CLI Integration Tests
**Status**: ⚠️ LOGIC ONLY
**Impact**: HIGH - User-facing feature
**Tests Needed**:
- `test_cli_show_details_flag_execution` - Test actual CLI command
- `test_cli_show_details_output_format` - Validate output
- `test_cli_show_details_with_research` - Test with research

### 4. Web UI Component Tests
**Status**: ⚠️ STATE ONLY
**Impact**: HIGH - User-facing feature
**Tests Needed**:
- `test_web_ui_accordion_creation` - Test accordion component
- `test_web_ui_accordion_fallback` - Test fallback behavior
- `test_web_ui_expansion_state` - Test expansion/collapse

## High Priority (Add Soon)

### 5. End-to-End Evaluation
**Status**: ❌ ZERO TESTS
**Impact**: MEDIUM - Quality assurance
**Tests Needed**:
- `test_eval_full_workflow_new_features` - Complete workflow
- `test_eval_progressive_disclosure_quality` - Tier quality
- `test_eval_belief_alignment_accuracy` - Alignment accuracy
- `test_eval_source_matrix_quality` - Matrix quality

### 6. Response Length Adaptation
**Status**: ⚠️ BASIC TEST ONLY
**Impact**: MEDIUM - Affects user experience
**Tests Needed**:
- `test_response_length_adaptation_logic` - Test length adjustment
- `test_response_length_with_adaptive_manager` - Integration test
- `test_response_length_edge_cases` - Boundary tests

### 7. Trust Metrics Integration
**Status**: ⚠️ FORMATTING ONLY
**Impact**: MEDIUM - User-facing metrics
**Tests Needed**:
- `test_trust_metrics_cli_display` - CLI integration
- `test_trust_metrics_web_ui_display` - Web UI integration
- `test_trust_metrics_with_research` - With research results

## Medium Priority (Nice to Have)

### 8. LLM Service Integration
**Status**: ⚠️ PLACEHOLDERS NOT TESTED
**Impact**: LOW - Future enhancement
**Tests Needed**:
- `test_belief_alignment_with_llm_service` - When LLM available
- `test_source_matrix_llm_extraction` - LLM claim extraction

### 9. Error Recovery
**Status**: ⚠️ ERROR HANDLING TESTED, NOT RECOVERY
**Impact**: LOW - Edge case
**Tests Needed**:
- `test_error_recovery_after_failure` - Recovery tests
- `test_error_logging_verification` - Logging tests

## Summary

**Total Missing Tests**: ~25-30 tests
**Critical**: 4 features (15-20 tests)
**High Priority**: 3 features (10-12 tests)
**Medium Priority**: 2 features (5-8 tests)

**Recommendation**: Add critical tests before production release.
