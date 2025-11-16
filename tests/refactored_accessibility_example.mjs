/**
 * REFACTORED: Accessibility Tests Using Package Features
 * 
 * This shows how to properly use ai-visual-test package features:
 * 1. Programmatic validators FIRST (free, fast)
 * 2. Hybrid validators (best of both worlds)
 * 3. Built-in cost tracking
 * 4. Built-in caching
 */

import { test, expect } from '@playwright/test';
import {
  // Programmatic validators (FREE, FAST)
  checkElementContrast,
  checkAllTextContrast,
  checkKeyboardNavigation,
  // Hybrid validators (programmatic + VLLM)
  validateAccessibilityHybrid,
  // Built-in cost tracking
  getCostTracker,
  // Built-in utilities
  extractSemanticInfo
} from '@arclabs561/ai-visual-test/validators';
import { getCostTracker as getGlobalCostTracker } from '@arclabs561/ai-visual-test';

const SERVER_URL = process.env.BOP_SERVER_URL || 'http://localhost:8000';

test.describe('Accessibility Audit (Refactored)', () => {
  test.setTimeout(30000);
  
  let page;
  
  test.beforeEach(async ({ page: testPage }) => {
    // Wait for server
    let retries = 0;
    while (retries < 15) {
      try {
        const response = await fetch(`${SERVER_URL}/health`);
        if (response.ok) break;
      } catch (error) {
        // Server not ready yet
      }
      await new Promise(resolve => setTimeout(resolve, 1000));
      retries++;
    }
    
    page = testPage;
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
  });

  test('accessibility with programmatic checks first (FREE)', async () => {
    // STEP 1: Run FREE programmatic checks first (<100ms, $0.00)
    const contrastCheck = await checkAllTextContrast(page, 4.5);
    const keyboardCheck = await checkKeyboardNavigation(page);
    
    console.log('\n📊 Programmatic Checks (FREE):');
    console.log(`  Contrast: ${contrastCheck.passing}/${contrastCheck.total} pass`);
    console.log(`  Violations: ${contrastCheck.failing}`);
    console.log(`  Keyboard: ${keyboardCheck.focusableElements} focusable elements`);
    console.log(`  Keyboard violations: ${keyboardCheck.violations.length}`);
    
    // Assert on programmatic data (fast, free)
    expect(contrastCheck.failing).toBe(0);
    expect(keyboardCheck.violations.length).toBe(0);
    
    // STEP 2: Only use VLLM if needed for semantic evaluation
    // (In this case, we pass, so we might skip VLLM entirely)
    // Or use VLLM to evaluate context and criticality
  });

  test('accessibility with hybrid validator (BEST APPROACH)', async () => {
    // Capture screenshot
    const screenshotPath = `test-results/accessibility-hybrid-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    // Use hybrid validator: runs programmatic FIRST, then VLLM for semantic evaluation
    const result = await validateAccessibilityHybrid(
      page,
      screenshotPath,
      4.5, // minContrast
      {
        testType: 'accessibility-hybrid',
        // Add BOP principles to prompt
        prompt: `BOP Principles:
- Information geometry: Uses Fisher Information for structure quality
- Quality feedback: Continuous evaluation and adaptive learning

Evaluate accessibility with these principles in mind.`
      }
    );
    
    // Result includes BOTH programmatic data and VLLM evaluation
    console.log('\n📊 Hybrid Validation Results:');
    console.log(`  Programmatic contrast: ${result.programmaticData.contrast.passing}/${result.programmaticData.contrast.total} pass`);
    console.log(`  VLLM semantic score: ${result.score}/10`);
    console.log(`  Issues: ${result.issues.length}`);
    
    // Assert on both
    expect(result.programmaticData.contrast.failing).toBe(0);
    expect(result.score).toBeGreaterThanOrEqual(7);
  });

  test('cost tracking using package (NO DUPLICATE)', async () => {
    // Use package's built-in cost tracking
    const costTracker = getGlobalCostTracker();
    
    // Package automatically tracks costs from validateScreenshot calls
    // We can also manually record if needed
    costTracker.recordCost({
      provider: 'gemini',
      cost: 0.001,
      testName: 'accessibility-test',
      inputTokens: 1000,
      outputTokens: 500
    });
    
    // Get stats
    const stats = costTracker.getStats();
    console.log('\n💰 Cost Stats (from package):');
    console.log(`  Total: $${stats.total.toFixed(6)}`);
    console.log(`  Calls: ${stats.count}`);
    console.log(`  Average: $${stats.average.toFixed(6)}`);
    console.log(`  By provider:`, stats.byProvider);
    
    // No need for our own cost tracking!
  });

  test('accessibility with smart validator (AUTO-DETECT)', async () => {
    // Package has validateAccessibilitySmart that auto-detects method
    // But for now, we'll use hybrid which is more explicit
    
    const screenshotPath = `test-results/accessibility-smart-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    // For now, use hybrid (we can migrate to smart later)
    const result = await validateAccessibilityHybrid(page, screenshotPath, 4.5);
    
    expect(result.score).toBeGreaterThanOrEqual(7);
  });
});

