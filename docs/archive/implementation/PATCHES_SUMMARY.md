# Patches Summary: Concrete Implementation Fixes

## Overview

Based on MCP tool research and codebase analysis, here are 5 concrete patches to fix critical gaps:

## Patch 1: CLI --show-details Flag ✅
**File**: `src/bop/cli.py`
**Status**: Ready to implement
**Changes**: Add `show_details` flag parameter, update display logic
**Testing**: Add integration test
**Priority**: **HIGH** (non-functional feature)

## Patch 2: Web UI Expansion ✅
**File**: `src/bop/web.py`
**Status**: Ready to implement
**Changes**: Use Marimo accordion or reactive checkbox for expansion
**Testing**: Add integration test
**Priority**: **HIGH** (non-functional feature)

## Patch 3: Error Handling ✅
**Files**: `src/bop/agent.py`, `src/bop/orchestrator.py`
**Status**: Ready to implement
**Changes**: Add try/except blocks with fallback values
**Testing**: Add error handling tests
**Priority**: **HIGH** (prevents crashes)

## Patch 4: Improved Belief Alignment ✅
**File**: `src/bop/orchestrator.py`
**Status**: Ready to implement (with optional LLM enhancement)
**Changes**: Add semantic similarity with keyword fallback
**Testing**: Add semantic alignment tests
**Priority**: **MEDIUM** (accuracy improvement)

## Patch 5: Improved Source Matrix ✅
**File**: `src/bop/orchestrator.py`
**Status**: Ready to implement (with optional LLM enhancement)
**Changes**: Add LLM-based claim extraction with improved heuristic fallback
**Testing**: Add phrase extraction tests
**Priority**: **MEDIUM** (accuracy improvement)

## Implementation Order

1. **Patch 3** (Error Handling) - Prevents crashes, enables safe testing
2. **Patch 1** (CLI Flag) - Quick win, non-functional feature
3. **Patch 2** (Web UI) - Quick win, non-functional feature
4. **Patch 4** (Belief Alignment) - Accuracy improvement
5. **Patch 5** (Source Matrix) - Accuracy improvement

## Testing Strategy

Each patch includes:
- Unit tests for new methods
- Integration tests for feature interactions
- Error path tests
- Edge case tests

## Notes

- All patches are backwards compatible
- Graceful degradation patterns used throughout
- Research-based solutions (not ad-hoc)
- Production-ready error handling
- Optional enhancements (LLM-based) can be added later

## Next Steps

1. Review patches for codebase-specific adjustments
2. Implement patches in order
3. Add tests as patches are implemented
4. Validate backwards compatibility
5. Update documentation

