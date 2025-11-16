# Refactoring Plan: Better Use of ai-visual-test Package

## Current Problems

1. **Duplicating Cost Tracking**
   - We have our own `costTracker` object
   - Package has `CostTracker` class and `getCostTracker()` singleton
   - We're maintaining duplicate code

2. **Not Using Programmatic Validators**
   - Package has FREE, FAST validators:
     - `checkElementContrast()` - Free contrast check
     - `checkKeyboardNavigation()` - Free keyboard nav check
     - `checkAllTextContrast()` - Free text contrast check
   - We're using expensive VLLM for things we could check programmatically

3. **Not Using Hybrid Validators**
   - Package has `validateAccessibilityHybrid()` which:
     - Runs programmatic checks FIRST (free, fast)
     - Only uses VLLM for semantic understanding
   - We're always using VLLM, even for basic checks

4. **Not Using Built-in Caching**
   - Package has file-based cache (7-day TTL)
   - We're not leveraging it

5. **Duplicating Score Extraction**
   - Package has `extractSemanticInfo()` 
   - We have our own `extractScore()` with similar logic

## What We Should Do

### Phase 1: Use Programmatic Validators First (Immediate, High Value)

**For accessibility tests:**
```javascript
import { 
  checkElementContrast,
  checkKeyboardNavigation,
  checkAllTextContrast
} from '@arclabs561/ai-visual-test/validators';

// Run FREE checks first
const contrastCheck = await checkAllTextContrast(page, 4.5);
const keyboardCheck = await checkKeyboardNavigation(page);

// Only use VLLM if programmatic checks pass or for semantic evaluation
if (contrastCheck.failing > 0 || keyboardCheck.violations.length > 0) {
  // Use VLLM to understand context and criticality
  const result = await validateScreenshot(...);
}
```

**Benefits:**
- FREE checks catch basic issues immediately
- VLLM only used for semantic understanding
- Faster tests (programmatic checks are <100ms)
- Lower costs (fewer VLLM calls)

### Phase 2: Use Hybrid Validators (High Value, Medium Effort)

**Replace our accessibility tests with:**
```javascript
import { validateAccessibilityHybrid } from '@arclabs561/ai-visual-test/validators';

// This runs programmatic checks FIRST, then VLLM for semantic evaluation
const result = await validateAccessibilityHybrid(
  page,
  screenshotPath,
  4.5, // minContrast
  {
    testType: 'accessibility',
    prompt: 'Evaluate accessibility with BOP principles...'
  }
);

// Result includes both programmatic data and VLLM evaluation
console.log(result.programmaticData.contrast); // Free check results
console.log(result.score); // VLLM semantic score
```

**Benefits:**
- Best of both worlds (free + semantic)
- Less code to maintain
- Package handles the logic

### Phase 3: Use Built-in Cost Tracking (Low Effort, High Value)

**Replace our cost tracking with:**
```javascript
import { getCostTracker, recordCost } from '@arclabs561/ai-visual-test';

// Package already tracks costs automatically
// But we can also record manually if needed
recordCost({
  provider: 'gemini',
  cost: 0.001,
  testName: 'accessibility-test'
});

// Get stats
const stats = getCostTracker().getStats();
console.log(stats.total, stats.byProvider);
```

**Benefits:**
- Remove duplicate code
- Use package's proven implementation
- Better cost analysis (by provider, by date, projections)

### Phase 4: Refactor Wrapper to Leverage Package Features

**Keep wrapper for BOP-specific needs, but use package features:**
```javascript
import { 
  validateScreenshot,
  validateAccessibilityHybrid,
  getCostTracker,
  extractSemanticInfo
} from '@arclabs561/ai-visual-test';

export async function validateScreenshotEnhanced(
  screenshotPath,
  prompt,
  context = {},
  options = {}
) {
  // Use hybrid validator for accessibility tests
  if (context.testType?.includes('accessibility') && options.useHybrid !== false) {
    const page = context.page; // Need page for hybrid validator
    if (page) {
      return await validateAccessibilityHybrid(
        page,
        screenshotPath,
        4.5,
        { ...context, ...options }
      );
    }
  }
  
  // For other tests, use regular validateScreenshot
  // Package already handles caching, cost tracking, retries
  const result = await validateScreenshot(screenshotPath, prompt, context);
  
  // Use package's cost tracking
  if (options.trackCost !== false) {
    // Package already tracks automatically, but we can add test name
    const costTracker = getCostTracker();
    // Cost is already tracked by package, just add metadata
  }
  
  // Use package's semantic extraction
  const semanticInfo = extractSemanticInfo(result);
  
  // Keep our BOP-specific filtering and formatting
  return filterOutput(result, options);
}
```

## Implementation Steps

### Step 1: Add Programmatic Checks to Accessibility Tests
- Import programmatic validators
- Run checks before VLLM
- Only use VLLM if needed

### Step 2: Replace Cost Tracking
- Remove our `costTracker` object
- Use `getCostTracker()` from package
- Update all cost tracking calls

### Step 3: Use Hybrid Validators
- Replace accessibility tests with `validateAccessibilityHybrid`
- Keep BOP principles in prompts
- Remove duplicate validation logic

### Step 4: Clean Up Wrapper
- Keep wrapper for BOP-specific needs
- But leverage package features
- Remove duplicate functionality

## Expected Benefits

1. **Cost Reduction**
   - Free programmatic checks catch basic issues
   - VLLM only for semantic understanding
   - Estimated: 50-70% cost reduction

2. **Performance Improvement**
   - Programmatic checks are <100ms
   - VLLM calls only when needed
   - Estimated: 2-3x faster tests

3. **Code Simplification**
   - Remove duplicate cost tracking (~50 lines)
   - Remove duplicate score extraction (~30 lines)
   - Use package's proven implementations
   - Estimated: 100+ lines removed

4. **Better Reliability**
   - Package's implementations are tested
   - Less code to maintain
   - Better error handling

## Migration Strategy

1. **Start with accessibility tests** (highest value)
   - Add programmatic checks first
   - Then migrate to hybrid validators
   - Keep existing tests working

2. **Then cost tracking** (easy win)
   - Replace our tracker with package's
   - Update all references
   - Verify cost stats still work

3. **Finally wrapper refactor** (polish)
   - Keep BOP-specific features
   - Leverage package features
   - Remove duplicates

## Questions to Answer

1. Should we keep our wrapper or use package directly?
   - **Answer:** Keep wrapper for BOP principles, but use package features

2. Should we use hybrid validators for all tests?
   - **Answer:** Yes for accessibility, maybe for others

3. Should we remove our cost tracking entirely?
   - **Answer:** Yes, use package's built-in tracking

4. Should we use sub-modules for tree-shaking?
   - **Answer:** Yes, but not critical for now
