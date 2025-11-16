# Reasoning Through ai-visual-test Usage

## What ai-visual-test Actually Provides

### Core Functionality
1. **validateScreenshot(imagePath, prompt, context)** - Main validation function
   - Uses VLLM (Vision Language Model) to evaluate screenshots semantically
   - Returns: `{ score: 0-10, issues: [], enabled: boolean, ... }`
   - Has built-in caching (7-day TTL, file-based)
   - Has built-in cost tracking
   - Auto-detects provider from env vars

2. **Built-in Features We're Not Using**
   - **Caching**: Already built-in, we're duplicating with our own tracking
   - **Cost Tracking**: Already built-in (`CostTracker` class), we're duplicating
   - **Config Management**: `createConfig()` auto-detects provider, we're using it but not optimally
   - **Sub-modules**: Better tree-shaking available (`/validators`, `/temporal`, etc.)
   - **Programmatic Validators**: Fast, free checks (contrast, keyboard nav) before VLLM
   - **Hybrid Validators**: Combine programmatic + VLLM for best of both worlds
   - **Smart Validators**: Auto-detect when to use programmatic vs VLLM

### What We're Currently Doing

1. **Wrapping validateScreenshot** in `validateScreenshotEnhanced`
   - Adds retries (good)
   - Adds output filtering (good)
   - Adds cost tracking (DUPLICATE - package already does this)
   - Adds score extraction (good, but package has `extractSemanticInfo`)

2. **Manual Cost Tracking**
   - We have our own `costTracker` object
   - Package has `CostTracker` class and `getCostTracker()` singleton
   - We're duplicating functionality

3. **Manual Config**
   - We call `createConfig()` but don't use it optimally
   - Package auto-detects provider, we're doing it manually

4. **Not Using Programmatic Validators**
   - Package has `checkElementContrast`, `checkKeyboardNavigation`, etc.
   - These are FREE and FAST
   - We're using expensive VLLM for things we could check programmatically

5. **Not Using Hybrid Validators**
   - Package has `validateAccessibilityHybrid` which:
     - Runs programmatic checks first (free, fast)
     - Only uses VLLM if needed (semantic understanding)
   - We're always using VLLM

## What Would Be Best

### Option 1: Use Package Features Directly (Recommended)
**Pros:**
- Less code to maintain
- Leverages built-in caching, cost tracking
- Uses programmatic validators (free, fast)
- Better tree-shaking with sub-modules

**Cons:**
- Need to refactor existing tests
- Less control over exact behavior

**Implementation:**
```javascript
// Instead of our wrapper, use package directly:
import { 
  validateScreenshot,
  validateAccessibilityHybrid,  // NEW: Free checks first
  getCostTracker,               // NEW: Use built-in tracking
  getCacheStats                 // NEW: Use built-in cache
} from '@arclabs561/ai-visual-test';

// Use hybrid validator (free checks first, VLLM only if needed)
const result = await validateAccessibilityHybrid(page, {
  screenshotPath: 'screenshot.png',
  prompt: 'Check accessibility',
  useProgrammatic: true,  // Free checks first
  useVLLM: true           // VLLM for semantic understanding
});

// Use built-in cost tracking
const costStats = getCostTracker().getStats();
```

### Option 2: Keep Wrapper, But Use Package Features
**Pros:**
- Minimal changes to existing tests
- Still get benefits of package features

**Cons:**
- Still maintaining wrapper code
- May duplicate some functionality

**Implementation:**
```javascript
// Keep validateScreenshotEnhanced, but:
import { 
  validateScreenshot,
  validateAccessibilityHybrid,
  getCostTracker,
  extractSemanticInfo  // Use package's extraction
} from '@arclabs561/ai-visual-test';

// In wrapper, use hybrid validator when appropriate
export async function validateScreenshotEnhanced(...) {
  // For accessibility tests, use hybrid
  if (context.testType?.includes('accessibility')) {
    return await validateAccessibilityHybrid(page, {...});
  }
  
  // Otherwise, use regular validateScreenshot
  return await validateScreenshot(...);
}
```

### Option 3: Use Sub-modules for Better Tree-shaking
**Pros:**
- Smaller bundle size
- Only import what we need

**Cons:**
- Need to refactor imports
- May be more complex

**Implementation:**
```javascript
// Instead of importing everything:
import { validateScreenshot } from '@arclabs561/ai-visual-test';

// Import from sub-modules:
import { validateScreenshot } from '@arclabs561/ai-visual-test';
import { StateValidator } from '@arclabs561/ai-visual-test/validators';
import { getCostTracker } from '@arclabs561/ai-visual-test/utils';
```

## Recommendations

### Immediate (High Value, Low Effort)
1. **Use Built-in Cost Tracking**
   - Replace our `costTracker` with `getCostTracker()`
   - Remove duplicate cost tracking code

2. **Use Programmatic Validators First**
   - For accessibility: Use `checkElementContrast`, `checkKeyboardNavigation` first
   - Only use VLLM for semantic understanding (not basic checks)

3. **Use Hybrid Validators**
   - Replace `validateScreenshot` with `validateAccessibilityHybrid` for accessibility tests
   - Gets free checks + VLLM when needed

### Medium-Term (High Value, Medium Effort)
4. **Refactor Wrapper to Use Package Features**
   - Keep wrapper for our specific needs (BOP principles, retries)
   - But use package's built-in features (cost tracking, caching)

5. **Use Sub-modules for Tree-shaking**
   - Import from specific sub-modules
   - Reduce bundle size

### Long-Term (Nice to Have)
6. **Use Smart Validators**
   - Package has `validateAccessibilitySmart` that auto-detects method
   - Could simplify our test code

7. **Use Package's Config System**
   - Better provider selection
   - Better model tier selection

## Critical Questions

1. **Are we duplicating functionality?** YES - Cost tracking, caching
2. **Are we using expensive tools for simple checks?** YES - VLLM for basic accessibility
3. **Could we get 80% of value with 20% of cost?** YES - Use programmatic validators first
4. **Are we leveraging package features?** NO - We're wrapping but not using built-ins

## Verdict

**We should:**
1. Use built-in cost tracking (remove duplicate)
2. Use programmatic validators first (free, fast)
3. Use hybrid validators (best of both worlds)
4. Keep wrapper for BOP-specific needs (principles, retries)
5. But leverage package features instead of duplicating

**This would:**
- Reduce code complexity
- Reduce costs (free checks first)
- Improve performance (faster tests)
- Still maintain our specific needs (BOP principles, retries)
