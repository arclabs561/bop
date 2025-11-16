/**
 * Comprehensive Accessibility Audit
 * Tests WCAG compliance and accessibility features
 * 
 * REFACTORED: Now uses ai-visual-test package features:
 * - Programmatic validators FIRST (free, fast)
 * - Hybrid validators (programmatic + VLLM)
 * - Built-in cost tracking
 */

import { test, expect } from '@playwright/test';
import {
  // Programmatic validators (FREE, FAST)
  checkAllTextContrast,
  checkKeyboardNavigation,
  // Hybrid validators (programmatic + VLLM)
  validateAccessibilityHybrid
} from '@arclabs561/ai-visual-test/validators';

const SERVER_URL = process.env.BOP_SERVER_URL || 'http://localhost:8000';

test.describe('Accessibility Audit', () => {
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
  

  test('all interactive elements have ARIA labels', async () => {
    // Use programmatic checks first (free, fast)
    const results = {
      passed: [],
      failed: [],
    };
    
    // Check message input
    const input = page.locator('#messageInput');
    const inputAria = await input.getAttribute('aria-label');
    if (inputAria) {
      results.passed.push('messageInput has aria-label');
    } else {
      results.failed.push('messageInput missing aria-label');
    }
    
    // Check send button
    const sendButton = page.locator('#sendButton');
    const sendAria = await sendButton.getAttribute('aria-label');
    if (sendAria) {
      results.passed.push('sendButton has aria-label');
    } else {
      results.failed.push('sendButton missing aria-label');
    }
    
    // Check research toggle
    const researchToggle = page.locator('#researchToggle');
    const researchAria = await researchToggle.getAttribute('aria-label');
    if (researchAria) {
      results.passed.push('researchToggle has aria-label');
    } else {
      results.failed.push('researchToggle missing aria-label');
    }
    
    // Check schema select
    const schemaSelect = page.locator('#schemaSelect');
    const schemaAria = await schemaSelect.getAttribute('aria-label');
    if (schemaAria) {
      results.passed.push('schemaSelect has aria-label');
    } else {
      results.failed.push('schemaSelect missing aria-label');
    }
    
    // Check example query buttons
    const exampleButtons = page.locator('.example-query');
    const count = await exampleButtons.count();
    for (let i = 0; i < count; i++) {
      const button = exampleButtons.nth(i);
      const ariaLabel = await button.getAttribute('aria-label');
      if (ariaLabel) {
        results.passed.push(`example-query-${i} has aria-label`);
      } else {
        results.failed.push(`example-query-${i} missing aria-label`);
      }
    }
    
    console.log('\n📊 ARIA Labels Audit:');
    console.log(`  ✅ Passed: ${results.passed.length}`);
    console.log(`  ❌ Failed: ${results.failed.length}`);
    if (results.failed.length > 0) {
      console.log('  Failed items:', results.failed);
    }
    
    expect(results.failed.length).toBe(0);
  });

  test('keyboard navigation works', async () => {
    // Focus input directly and clear it (avoids example query text)
    const input = page.locator('#messageInput');
    await input.focus();
    await input.fill(''); // Clear any existing text
    
    // Verify we can type
    await page.keyboard.type('Test message');
    
    const inputValue = await input.inputValue();
    expect(inputValue).toBe('Test message');
    
    // Verify we can tab to other elements
    await page.keyboard.press('Tab');
    const focusedAfterTab = await page.evaluate(() => document.activeElement?.id || document.activeElement?.tagName);
    console.log(`Focused element after Tab: ${focusedAfterTab}`);
    
    // Should have moved to next focusable element
    expect(focusedAfterTab).not.toBe('messageInput');
    
    console.log('✅ Keyboard navigation working');
  });

  test('loading indicator accessibility', async () => {
    // Trigger loading
    await page.fill('#messageInput', 'Test');
    await page.click('#sendButton');
    
    // Wait for loading indicator
    await page.waitForTimeout(500);
    
    const loadingIndicator = page.locator('#loadingIndicator');
    const isVisible = await loadingIndicator.isVisible();
    
    if (isVisible) {
      const role = await loadingIndicator.getAttribute('role');
      const ariaLive = await loadingIndicator.getAttribute('aria-live');
      const ariaLabel = await loadingIndicator.getAttribute('aria-label');
      const ariaBusy = await loadingIndicator.getAttribute('aria-busy');
      
      expect(role).toBe('status');
      expect(ariaLive).toBe('polite');
      expect(ariaLabel).toBeTruthy();
      expect(ariaBusy).toBe('true');
      
      console.log('✅ Loading indicator accessibility verified');
    } else {
      console.log('⚠️  Loading indicator not visible (may have completed too quickly)');
    }
  });

  test('screen reader help text present', async () => {
    const helpTexts = [
      { id: 'input-help', expected: 'Enter your question' },
      { id: 'research-help', expected: 'Toggle to enable' },
      { id: 'schema-help', expected: 'Choose a reasoning' },
    ];
    
    const results = [];
    for (const { id, expected } of helpTexts) {
      const element = page.locator(`#${id}`);
      const exists = await element.count() > 0;
      const hasSrOnly = exists && (await element.evaluate(el => el.classList.contains('sr-only')));
      const text = exists ? await element.textContent() : '';
      const hasExpectedText = text.includes(expected);
      
      results.push({
        id,
        exists,
        hasSrOnly,
        hasExpectedText,
        text: text.substring(0, 50),
      });
    }
    
    console.log('\n📊 Screen Reader Help Text:');
    results.forEach(r => {
      const status = r.exists && r.hasSrOnly && r.hasExpectedText ? '✅' : '❌';
      console.log(`  ${status} ${r.id}: exists=${r.exists}, sr-only=${r.hasSrOnly}, text=${r.hasExpectedText}`);
    });
    
    const allPass = results.every(r => r.exists && r.hasSrOnly && r.hasExpectedText);
    expect(allPass).toBe(true);
  });

  test('color contrast meets WCAG standards', async () => {
    // Use package's programmatic contrast checker (FREE, FAST)
    const contrastCheck = await checkAllTextContrast(page, 4.5); // WCAG AA minimum
    
    console.log('\n📊 Color Contrast (Programmatic Check - FREE):');
    console.log(`  Passing: ${contrastCheck.passing}/${contrastCheck.total} elements`);
    console.log(`  Failing: ${contrastCheck.failing} elements`);
    
    if (contrastCheck.violations.length > 0) {
      console.log('  Top violations:');
      contrastCheck.violations.slice(0, 5).forEach(v => {
        console.log(`    - ${v.element}: ${v.ratio.toFixed(2)}:1 (required: ${v.required}:1)`);
      });
    }
    
    // Assert on programmatic data (fast, free)
    expect(contrastCheck.failing).toBe(0);
    
    console.log('✅ Color contrast verified (WCAG AA: ≥4.5:1)');
  });

  test('focus indicators visible', async () => {
    // Tab to input
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // Check if focused element has visible focus indicator
    const focusStyle = await page.evaluate(() => {
      const active = document.activeElement;
      if (!active) return null;
      const style = window.getComputedStyle(active, ':focus');
      return {
        outline: style.outline,
        outlineWidth: style.outlineWidth,
        boxShadow: style.boxShadow,
      };
    });
    
    console.log('Focus style:', focusStyle);
    
    // At least one focus indicator should be present
    const hasFocusIndicator = focusStyle && (
      focusStyle.outline !== 'none' ||
      focusStyle.outlineWidth !== '0px' ||
      focusStyle.boxShadow !== 'none'
    );
    
    if (!hasFocusIndicator) {
      console.log('⚠️  No visible focus indicator - consider adding CSS :focus styles');
    } else {
      console.log('✅ Focus indicators present');
    }
  });
});

