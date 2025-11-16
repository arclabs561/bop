# Refactoring Plan: Use ai-visual-test Package Features

## Changes to Make

### 1. Replace Cost Tracking
- Remove our `costTracker` object
- Use `getCostTracker()` from package
- Update all `trackCost()` calls
- Update `getCostSummary()` to use package
- Update `resetCostTracking()` to use package

### 2. Replace Score Extraction
- Remove our `extractScore()` function
- Use `extractSemanticInfo()` from package
- Update `assertScore()` to use package's extraction

### 3. Add Programmatic Validators
- Import `checkAllTextContrast`, `checkKeyboardNavigation`
- Run these FIRST before VLLM
- Only use VLLM for semantic evaluation

### 4. Use Hybrid Validators for Accessibility
- Replace accessibility tests with `validateAccessibilityHybrid`
- Keep BOP principles in prompts
- Get both programmatic data and VLLM evaluation

### 5. Update Wrapper
- Keep `validateScreenshotEnhanced` for BOP-specific needs
- But use package features instead of duplicating
- Use hybrid validators when appropriate

## Files to Change

1. `tests/visual_test_utils.mjs` - Main refactor
2. `tests/accessibility_audit.mjs` - Use hybrid validators
3. `tests/test_e2e_visual.mjs` - Use programmatic checks first
4. `tests/test_e2e_visual_enhanced.mjs` - Update imports
5. `tests/test_e2e_visual_regression.mjs` - Update imports
6. `tests/test_visual_comprehensive.mjs` - Update imports

## Validation Steps

1. Run accessibility tests - should use hybrid validators
2. Run visual tests - should use programmatic checks first
3. Check cost tracking - should use package's tracker
4. Verify no duplicate functionality
5. Verify tests still pass
