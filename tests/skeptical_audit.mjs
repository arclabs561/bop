/**
 * Skeptical Audit of Visual Testing Framework
 * 
 * Questions everything. Finds what's broken, what's overhyped, what doesn't work.
 */

import { test, expect } from '@playwright/test';
import { readFileSync, existsSync } from 'fs';

const SERVER_URL = process.env.BOP_SERVER_URL || 'http://localhost:8000';

test.describe('Skeptical Framework Audit', () => {
  test.setTimeout(30000);
  
  test('do the utilities actually work?', async ({ page }) => {
    // Let's see if the utilities are even importable
    let utilsImported = false;
    try {
      const utils = await import('./visual_test_utils.mjs');
      utilsImported = true;
      console.log('✅ Utilities imported');
      
      // But do they actually do anything useful?
      const functions = Object.keys(utils);
      console.log(`Found ${functions.length} exported functions:`, functions);
      
      // Test extractScore with various inputs
      const testCases = [
        { score: 7, expected: 7 },
        { score: null, issues: ['Score: 8/10'], expected: 8 },
        { score: undefined, issues: ['Rating 5/10'], expected: 5 },
        { issues: [], expected: null },
        { issues: ['No score here'], expected: null },
      ];
      
      let passed = 0;
      let failed = 0;
      for (const testCase of testCases) {
        const result = utils.extractScore(testCase);
        if (result === testCase.expected) {
          passed++;
        } else {
          failed++;
          console.log(`❌ Failed: expected ${testCase.expected}, got ${result}`, testCase);
        }
      }
      
      console.log(`Score extraction: ${passed} passed, ${failed} failed`);
      expect(failed).toBe(0);
      
    } catch (error) {
      console.error('❌ Utilities import failed:', error.message);
      throw error;
    }
    
    expect(utilsImported).toBe(true);
  });

  test('are the tests actually testing anything meaningful?', async ({ page }) => {
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Let's check if the tests are just checking for existence
    // or actually validating quality
    
    const checks = {
      ariaLabelsExist: false,
      ariaLabelsMeaningful: false,
      focusIndicatorsVisible: false,
      loadingStateAccessible: false,
      helpTextPresent: false,
      helpTextUseful: false,
    };
    
    // Check ARIA labels exist
    const input = page.locator('#messageInput');
    const inputAria = await input.getAttribute('aria-label');
    checks.ariaLabelsExist = !!inputAria;
    
    // But are they meaningful? Or just placeholder text?
    if (inputAria) {
      checks.ariaLabelsMeaningful = inputAria.length > 5 && 
                                    !inputAria.includes('TODO') &&
                                    !inputAria.includes('placeholder');
    }
    
    // Check focus indicators
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    const focusStyle = await page.evaluate(() => {
      const active = document.activeElement;
      if (!active) return null;
      const style = window.getComputedStyle(active, ':focus-visible');
      return {
        outline: style.outline,
        outlineWidth: style.outlineWidth,
        boxShadow: style.boxShadow,
      };
    });
    
    checks.focusIndicatorsVisible = focusStyle && (
      focusStyle.outline !== 'none' ||
      focusStyle.outlineWidth !== '0px'
    );
    
    // Check loading state
    const loadingIndicator = page.locator('#loadingIndicator');
    const loadingRole = await loadingIndicator.getAttribute('role');
    checks.loadingStateAccessible = loadingRole === 'status';
    
    // Check help text
    const helpText = page.locator('#input-help');
    checks.helpTextPresent = (await helpText.count()) > 0;
    
    if (checks.helpTextPresent) {
      const helpContent = await helpText.textContent();
      checks.helpTextUseful = helpContent && 
                              helpContent.length > 20 &&
                              !helpContent.includes('TODO');
    }
    
    console.log('\n📊 Meaningful Checks:');
    console.log(JSON.stringify(checks, null, 2));
    
    // Are we just checking boxes or actually validating quality?
    const meaningfulChecks = Object.values(checks).filter(v => v === true).length;
    const totalChecks = Object.keys(checks).length;
    
    console.log(`\nMeaningful checks: ${meaningfulChecks}/${totalChecks}`);
    
    // This is the real question: are we testing quality or just presence?
    expect(meaningfulChecks).toBeGreaterThan(totalChecks * 0.7); // At least 70% should be meaningful
  });

  test('is the improvement tracker actually tracking anything useful?', async () => {
    const trackerFile = 'test-results/visual-improvements-tracker.json';
    
    if (!existsSync(trackerFile)) {
      console.log('⚠️  Tracker file does not exist - improvements not being tracked');
      return; // Not a failure, just not set up
    }
    
    const tracker = JSON.parse(readFileSync(trackerFile, 'utf-8'));
    
    // Are improvements actually validated?
    const improvements = tracker.improvements || [];
    const validated = improvements.filter(i => i.validated).length;
    const unvalidated = improvements.filter(i => !i.validated).length;
    
    console.log(`\n📊 Improvement Tracking:`);
    console.log(`  Total: ${improvements.length}`);
    console.log(`  Validated: ${validated}`);
    console.log(`  Unvalidated: ${unvalidated}`);
    
    // Are we just collecting data or actually using it?
    if (unvalidated > validated) {
      console.log('⚠️  More unvalidated than validated - tracking without action?');
    }
    
    // Do improvements have actionable fixes?
    const actionable = improvements.filter(i => 
      i.fix && 
      i.fix.length > 10 && 
      !i.fix.includes('TODO') &&
      i.files && 
      i.files.length > 0
    ).length;
    
    console.log(`  Actionable: ${actionable}/${improvements.length}`);
    
    // This is the real test: are improvements actually being used?
    expect(actionable).toBeGreaterThan(improvements.length * 0.8); // 80% should be actionable
  });

  test('are the VLLM calls actually providing value or just costing money?', async ({ page }) => {
    // This is the critical question: are we getting value from expensive VLLM calls?
    
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    const screenshotPath = `test-results/skeptical-test-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    // Let's see what a VLLM call actually returns
    // But first, let's check if we can validate without VLLM
    
    const basicChecks = await page.evaluate(() => {
      return {
        hasInput: !!document.getElementById('messageInput'),
        hasSendButton: !!document.getElementById('sendButton'),
        hasLoadingIndicator: !!document.getElementById('loadingIndicator'),
        inputHasAriaLabel: !!document.getElementById('messageInput')?.getAttribute('aria-label'),
        sendButtonHasAriaLabel: !!document.getElementById('sendButton')?.getAttribute('aria-label'),
        loadingHasRole: document.getElementById('loadingIndicator')?.getAttribute('role') === 'status',
      };
    });
    
    console.log('\n📊 Basic Checks (No VLLM needed):');
    console.log(JSON.stringify(basicChecks, null, 2));
    
    const basicChecksPassed = Object.values(basicChecks).filter(v => v === true).length;
    const totalBasicChecks = Object.keys(basicChecks).length;
    
    console.log(`Basic checks passed: ${basicChecksPassed}/${totalBasicChecks}`);
    
    // The real question: do we need VLLM for these checks?
    // Or are we just spending money on things we could check programmatically?
    
    if (basicChecksPassed === totalBasicChecks) {
      console.log('✅ All basic checks pass - VLLM might be overkill for these');
    } else {
      console.log('❌ Basic checks fail - VLLM might catch more, but should fix basics first');
    }
    
    // The framework should prioritize free checks over expensive ones
    expect(basicChecksPassed).toBe(totalBasicChecks);
  });

  test('is the framework actually preventing regressions or just documenting them?', async ({ page }) => {
    // The real test: if we break something, does the framework catch it?
    
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Let's simulate a regression: remove an ARIA label
    await page.evaluate(() => {
      const input = document.getElementById('messageInput');
      if (input) {
        input.removeAttribute('aria-label');
      }
    });
    
    // Now check if our tests would catch this
    const input = page.locator('#messageInput');
    const ariaLabel = await input.getAttribute('aria-label');
    
    console.log('\n📊 Regression Test:');
    console.log(`  ARIA label after removal: ${ariaLabel || 'MISSING'}`);
    
    // This is the critical question: would our tests fail?
    // Or would they just document that it's missing?
    
    if (!ariaLabel) {
      console.log('✅ Regression detected - ARIA label missing');
      // This should fail the test
      expect(ariaLabel).toBeTruthy();
    } else {
      console.log('❌ Regression NOT detected - test might be too lenient');
    }
  });

  test('are we testing the right things or just testing what we can?', async ({ page }) => {
    // The philosophical question: are we testing what matters?
    
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // What actually matters for a chat interface?
    const criticalChecks = {
      canUserType: false,
      canUserSend: false,
      canUserSeeResponse: false,
      canUserNavigateKeyboard: false,
      canUserUnderstandUI: false,
    };
    
    // Can user type?
    await page.fill('#messageInput', 'Test message');
    const inputValue = await page.locator('#messageInput').inputValue();
    criticalChecks.canUserType = inputValue === 'Test message';
    
    // Can user send?
    const sendButton = page.locator('#sendButton');
    const sendButtonEnabled = await sendButton.isEnabled();
    criticalChecks.canUserSend = sendButtonEnabled;
    
    // Can user see response area?
    const messagesDiv = page.locator('#messages');
    const messagesVisible = await messagesDiv.isVisible();
    criticalChecks.canUserSeeResponse = messagesVisible;
    
    // Can user navigate with keyboard?
    await page.keyboard.press('Tab');
    const firstFocused = await page.evaluate(() => document.activeElement?.id);
    criticalChecks.canUserNavigateKeyboard = !!firstFocused;
    
    // Can user understand UI? (subjective, but check for obvious issues)
    const title = await page.locator('.app-title').textContent();
    const subtitle = await page.locator('.app-subtitle').textContent();
    criticalChecks.canUserUnderstandUI = !!(title && subtitle && title.length > 0);
    
    console.log('\n📊 Critical Functionality Checks:');
    console.log(JSON.stringify(criticalChecks, null, 2));
    
    const criticalPassed = Object.values(criticalChecks).filter(v => v === true).length;
    const totalCritical = Object.keys(criticalChecks).length;
    
    console.log(`Critical checks passed: ${criticalPassed}/${totalCritical}`);
    
    // Are we testing critical functionality or just accessibility?
    // Both matter, but critical functionality matters more
    
    expect(criticalPassed).toBe(totalCritical);
  });

  test('is the cost tracking actually preventing waste?', async () => {
    // The financial question: are we spending money wisely?
    
    const trackerFile = 'test-results/visual-improvements-tracker.json';
    
    if (!existsSync(trackerFile)) {
      console.log('⚠️  No tracker file - can\'t check costs');
      return;
    }
    
    // Check if we're tracking costs
    // But more importantly: are we using that data?
    
    console.log('\n💰 Cost Tracking:');
    console.log('  Question: Are we tracking costs but not acting on them?');
    console.log('  Question: Are expensive tests providing proportional value?');
    console.log('  Question: Could we get 80% of value with 20% of the cost?');
    
    // The real test: if costs are high, are we optimizing?
    // Or just documenting that we're spending money?
    
    console.log('  ⚠️  Cost tracking exists, but is it being used to optimize?');
  });
});

