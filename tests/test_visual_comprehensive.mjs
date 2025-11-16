/**
 * Comprehensive Visual Test Suite
 * Runs all visual tests in one suite for complete validation
 */

import { test, expect } from '@playwright/test';
import { 
  validateScreenshotEnhanced, 
  waitForServer, 
  formatTestResult, 
  assertScore,
  resetCostTracking,
  getCostSummary 
} from './visual_test_utils.mjs';

const SERVER_URL = process.env.BOP_SERVER_URL || 'http://localhost:8000';

test.describe('Comprehensive Visual Test Suite', () => {
  test.setTimeout(120000);
  
  test.beforeAll(() => {
    resetCostTracking();
  });
  
  test.beforeEach(async ({ page }) => {
    await waitForServer(SERVER_URL, {
      maxRetries: 15,
      retryDelay: 1000,
      timeout: 30000,
    });
  });
  
  test.afterAll(async () => {
    const costSummary = getCostSummary();
    console.log('\n💰 Cost Summary:');
    console.log(`  Total calls: ${costSummary.totalCalls}`);
    const totalCost = typeof costSummary.totalCost === 'number' ? costSummary.totalCost : 0;
    console.log(`  Total cost: $${totalCost.toFixed(4)}`);
    if (Object.keys(costSummary.costsByTest).length > 0) {
      console.log('\n  Costs by test:');
      Object.entries(costSummary.costsByTest)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .forEach(([test, cost]) => {
          console.log(`    ${test}: $${cost.toFixed(4)}`);
        });
    }
  });

  test('complete UI validation', async ({ page }) => {
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    const screenshotPath = `test-results/comprehensive-ui-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    const result = await validateScreenshotEnhanced(
      screenshotPath,
      `Comprehensive UI Validation - BOP Knowledge Structure Research Agent

Evaluate the complete user interface for:

ACCESSIBILITY (WCAG 2.1 AA):
- ARIA labels on all interactive elements
- Keyboard navigation support
- Screen reader compatibility
- Focus indicators visible
- Color contrast (≥4.5:1 for normal text)
- Touch target sizes (≥44x44px)

DESIGN QUALITY:
- Modern, clean design (inspired by manus.im/marimo)
- Consistent spacing and typography
- Clear visual hierarchy
- Responsive layout
- Dark mode support

FUNCTIONALITY:
- Chat interface clearly visible
- Input field accessible
- Send button functional
- Controls (research toggle, schema select) visible
- Loading states handled
- Error states handled

USER EXPERIENCE:
- Intuitive layout
- Clear call-to-action
- Helpful example queries
- Smooth interactions
- Professional appearance

Rate the interface comprehensively across all these dimensions.`,
      {
        testType: 'comprehensive-ui',
        viewport: { width: 1280, height: 720 }
      },
      {
        testName: 'comprehensive-ui',
        filterOutput: true,
        trackCost: true,
        maxIssues: 10,
      }
    );
    
    expect(result.enabled).toBe(true);
    assertScore(result, 7, 'Comprehensive UI');
    console.log(formatTestResult('Comprehensive UI', result, { verbose: true, maxIssues: 5 }));
  });

  test('accessibility compliance check', async ({ page }) => {
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Check ARIA labels
    const ariaChecks = await page.evaluate(() => {
      const checks = {};
      const elements = {
        input: document.getElementById('messageInput'),
        sendButton: document.getElementById('sendButton'),
        researchToggle: document.getElementById('researchToggle'),
        schemaSelect: document.getElementById('schemaSelect'),
      };
      
      for (const [name, el] of Object.entries(elements)) {
        checks[name] = {
          hasAriaLabel: !!el?.getAttribute('aria-label'),
          hasAriaDescribedBy: !!el?.getAttribute('aria-describedby'),
        };
      }
      
      // Check example queries
      const exampleButtons = document.querySelectorAll('.example-query');
      checks.exampleQueries = Array.from(exampleButtons).map(btn => ({
        hasAriaLabel: !!btn.getAttribute('aria-label'),
      }));
      
      // Check loading indicator
      const loadingIndicator = document.getElementById('loadingIndicator');
      checks.loadingIndicator = {
        hasRole: loadingIndicator?.getAttribute('role') === 'status',
        hasAriaLive: loadingIndicator?.getAttribute('aria-live') === 'polite',
        hasAriaLabel: !!loadingIndicator?.getAttribute('aria-label'),
      };
      
      return checks;
    });
    
    console.log('\n📊 Accessibility Checks:');
    console.log(JSON.stringify(ariaChecks, null, 2));
    
    // Verify all checks pass
    expect(ariaChecks.input.hasAriaLabel).toBe(true);
    expect(ariaChecks.sendButton.hasAriaLabel).toBe(true);
    expect(ariaChecks.researchToggle.hasAriaLabel).toBe(true);
    expect(ariaChecks.schemaSelect.hasAriaLabel).toBe(true);
    expect(ariaChecks.loadingIndicator.hasRole).toBe(true);
    expect(ariaChecks.loadingIndicator.hasAriaLive).toBe(true);
    
    console.log('✅ Accessibility compliance verified');
  });

  test('keyboard navigation flow', async ({ page }) => {
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Tab through elements
    const tabOrder = [];
    for (let i = 0; i < 10; i++) {
      await page.keyboard.press('Tab');
      const focused = await page.evaluate(() => {
        const active = document.activeElement;
        return active ? {
          id: active.id,
          tagName: active.tagName,
          className: active.className,
        } : null;
      });
      
      if (focused) {
        tabOrder.push(focused);
        // Check for focus indicator
        const hasFocusIndicator = await page.evaluate(() => {
          const active = document.activeElement;
          if (!active) return false;
          const style = window.getComputedStyle(active, ':focus-visible');
          return style.outline !== 'none' || style.outlineWidth !== '0px';
        });
        
        if (!hasFocusIndicator && focused.tagName !== 'BODY') {
          console.log(`⚠️  No focus indicator on: ${focused.id || focused.tagName}`);
        }
      }
      
      // Stop if we've cycled back
      if (tabOrder.length > 1 && tabOrder[tabOrder.length - 1].id === tabOrder[0].id) {
        break;
      }
    }
    
    console.log('\n⌨️  Tab Order:');
    tabOrder.forEach((el, idx) => {
      console.log(`  ${idx + 1}. ${el.tagName}${el.id ? `#${el.id}` : ''}${el.className ? `.${el.className.split(' ')[0]}` : ''}`);
    });
    
    expect(tabOrder.length).toBeGreaterThan(0);
    console.log('✅ Keyboard navigation working');
  });

  test('loading state validation', async ({ page }) => {
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Trigger loading
    await page.fill('#messageInput', 'Test message for loading state');
    await page.click('#sendButton');
    
    // Wait for loading indicator
    await page.waitForTimeout(500);
    
    const loadingState = await page.evaluate(() => {
      const indicator = document.getElementById('loadingIndicator');
      if (!indicator) return null;
      
      const style = window.getComputedStyle(indicator);
      return {
        visible: style.display !== 'none',
        hasText: !!indicator.querySelector('.loading-text')?.textContent,
        role: indicator.getAttribute('role'),
        ariaLive: indicator.getAttribute('aria-live'),
        ariaBusy: indicator.getAttribute('aria-busy'),
      };
    });
    
    if (loadingState && loadingState.visible) {
      console.log('\n⏳ Loading State:');
      console.log(JSON.stringify(loadingState, null, 2));
      
      expect(loadingState.role).toBe('status');
      expect(loadingState.ariaLive).toBe('polite');
      expect(loadingState.hasText).toBe(true);
      console.log('✅ Loading state validated');
    } else {
      console.log('⚠️  Loading indicator not visible (may have completed quickly)');
    }
  });

  test('responsive design check', async ({ page }) => {
    const viewports = [
      { name: 'Mobile', width: 375, height: 667 },
      { name: 'Tablet', width: 768, height: 1024 },
      { name: 'Desktop', width: 1280, height: 720 },
    ];
    
    for (const viewport of viewports) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto(`${SERVER_URL}/`);
      await page.waitForLoadState('networkidle');
      
      const screenshotPath = `test-results/responsive-${viewport.name.toLowerCase()}-${Date.now()}.png`;
      await page.screenshot({ path: screenshotPath, fullPage: true });
      
      const result = await validateScreenshotEnhanced(
        screenshotPath,
        `Responsive Design Check - ${viewport.name} (${viewport.width}x${viewport.height})

Evaluate the interface at this viewport size:

LAYOUT:
- Does the layout adapt appropriately?
- Are elements properly sized for the viewport?
- Is content readable without zooming?
- Are touch targets appropriately sized (≥44x44px for mobile)?

FUNCTIONALITY:
- Are all interactive elements accessible?
- Is the chat interface usable?
- Can users input messages easily?
- Are controls visible and functional?

DESIGN:
- Is the design consistent across viewports?
- Are spacing and typography appropriate?
- Is the visual hierarchy maintained?
- Does it look professional?`,
        {
          testType: 'responsive',
          viewport: { width: viewport.width, height: viewport.height }
        },
        {
          testName: `responsive-${viewport.name.toLowerCase()}`,
          filterOutput: true,
          trackCost: true,
          maxIssues: 5,
        }
      );
      
      expect(result.enabled).toBe(true);
      assertScore(result, 6, `${viewport.name} responsive`);
      console.log(formatTestResult(`${viewport.name} Responsive`, result, { verbose: false, maxIssues: 3 }));
    }
  });
});

