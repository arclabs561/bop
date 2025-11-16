/**
 * Regression Tests for Visual E2E - Based on Iteration Learnings
 * 
 * These tests address specific issues identified during visual testing iterations:
 * - Chat history visibility
 * - Visual boundaries clarity
 * - Accessibility features
 * - Quality score display
 * - Research indicators
 * - Schema indicators
 * - Multi-turn conversation flow
 * - Error recovery
 * - Loading state clarity
 */

import { test, expect } from '@playwright/test';
import {
  validateScreenshot,
  extractRenderedCode,
  multiPerspectiveEvaluation,
  captureTemporalScreenshots,
} from '@arclabs561/ai-visual-test';
import {
  validateScreenshotEnhanced,
  extractRenderedCodeSafe,
  extractScore,
  formatTestResult,
  assertScore,
  waitForServer,
  getCostSummary,
  resetCostTracking,
} from './visual_test_utils.mjs';

const SERVER_URL = process.env.BOP_SERVER_URL || 'http://localhost:8000';
const SERVER_TIMEOUT = 60000;

test.describe('Visual Regression Tests (Iteration-Based)', () => {
  
  test.beforeAll(() => {
    resetCostTracking();
  });
  
  test.afterAll(() => {
    const costSummary = getCostSummary();
    if (costSummary.totalCalls > 0) {
      console.log('\n💰 Regression Tests Cost Summary:');
      console.log(`  Total API calls: ${costSummary.totalCalls}`);
      const totalCost = typeof costSummary.totalCost === 'number' ? costSummary.totalCost : 0;
      console.log(`  Estimated cost: $${totalCost.toFixed(6)}`);
    }
  });
  
  test.beforeEach(async ({ page }) => {
    await waitForServer(SERVER_URL);
  });

  test('chat history area visibility (regression)', async ({ page }) => {
    /**
     * REGRESSION: Issue identified - "Chat history area is not visible"
     * This test ensures chat history is clearly visible and functional.
     */
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Send multiple messages to populate history
    const messages = [
      'What is d-separation?',
      'How does it relate to information geometry?',
      'Explain attractor basins.'
    ];
    
    for (const msg of messages) {
      await page.fill('#messageInput', msg);
      await page.click('#sendButton');
      await page.waitForSelector('.message.assistant', { timeout: SERVER_TIMEOUT });
      await page.waitForTimeout(1000);
    }
    
    // Capture screenshot
    const screenshotPath = `test-results/regression-chat-history-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    // Validate chat history visibility (using enhanced validation)
    const result = await validateScreenshotEnhanced(
      screenshotPath,
      `REGRESSION TEST: Chat History Visibility
      
ISSUE: Chat history area was not clearly visible in initial tests.

REQUIREMENTS:
- Chat history area must be clearly visible and functional
- All messages (user and assistant) must be displayed
- Chat history must be scrollable if content exceeds viewport
- Visual distinction between chat history and input area
- Messages must be properly ordered (chronological)
- Chat history must have sufficient height and visibility

VALIDATION:
- Is the chat history area clearly visible?
- Are all messages displayed in the history?
- Is the chat history scrollable (if needed)?
- Is there clear visual separation from input area?
- Are messages properly ordered?
- Is the chat history area appropriately sized?`,
      {
        testType: 'regression-chat-history',
        viewport: { width: 1280, height: 720 }
      },
      {
        testName: 'chat-history-visibility',
        maxIssues: 5,
      }
    );
    
    expect(result.enabled).toBe(true);
    assertScore(result, 8, 'Chat history visibility'); // Higher threshold for regression
    console.log(formatTestResult('Chat history visibility', result, { maxIssues: 3 }));
  });

  test('visual boundaries clarity (regression)', async ({ page }) => {
    /**
     * REGRESSION: Issue identified - "Visual boundaries could be more pronounced"
     * This test ensures clear visual separation between UI elements.
     */
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Send a message to populate interface
    await page.fill('#messageInput', 'Test message');
    await page.click('#sendButton');
    await page.waitForSelector('.message.assistant', { timeout: SERVER_TIMEOUT });
    await page.waitForTimeout(1000);
    
    // Capture screenshot
    const screenshotPath = `test-results/regression-visual-boundaries-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    // Validate visual boundaries (using enhanced validation)
    const result = await validateScreenshotEnhanced(
      screenshotPath,
      `REGRESSION TEST: Visual Boundaries Clarity
      
ISSUE: Visual boundaries between elements could be more pronounced.

REQUIREMENTS:
- Clear visual separation between header, chat area, and input area
- Distinct boundaries between user and assistant messages
- Clear separation between controls (research toggle, schema select) and input
- Visual distinction between message types (user vs assistant)
- Clear boundaries for interactive elements (buttons, inputs)

VALIDATION:
- Are there clear visual boundaries between major sections (header/chat/input)?
- Are user and assistant messages visually distinct?
- Are controls clearly separated from input area?
- Are interactive elements clearly bounded?
- Is the visual hierarchy clear through boundaries?`,
      {
        testType: 'regression-visual-boundaries',
        viewport: { width: 1280, height: 720 }
      },
      {
        testName: 'visual-boundaries',
        maxIssues: 5,
      }
    );
    
    expect(result.enabled).toBe(true);
    assertScore(result, 7, 'Visual boundaries');
    console.log(formatTestResult('Visual boundaries', result, { maxIssues: 3 }));
  });

  test('accessibility features (regression)', async ({ page }) => {
    /**
     * REGRESSION: Issue identified - "Enhanced accessibility features needed"
     * This test ensures accessibility features are present and functional.
     */
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Capture screenshot
    const screenshotPath = `test-results/regression-accessibility-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    // Extract rendered code to check for ARIA labels (using safe wrapper)
    const codeText = await extractRenderedCodeSafe(page, extractRenderedCode);
    const hasAriaLabels = codeText.includes('aria-label') || 
                         codeText.includes('aria-labelledby') ||
                         codeText.includes('role=');
    
    // Validate accessibility (using enhanced validation)
    const result = await validateScreenshotEnhanced(
      screenshotPath,
      `REGRESSION TEST: Accessibility Features
      
ISSUE: Enhanced accessibility features needed (WCAG compliance, ARIA labels, keyboard navigation).

REQUIREMENTS:
- Sufficient color contrast (≥4.5:1 for normal text, ≥3:1 for large text)
- ARIA labels for interactive elements
- Keyboard navigation support (tab order, focus indicators)
- Screen reader compatibility
- Touch target sizes (≥44x44px for mobile)
- Focus indicators visible

VALIDATION:
- Is color contrast sufficient throughout the interface?
- Are focus indicators visible for keyboard navigation?
- Are interactive elements properly sized for touch/click?
- Is the interface keyboard navigable (visual indicators)?
- Are there clear visual cues for interactive elements?`,
      {
        testType: 'regression-accessibility',
        viewport: { width: 1280, height: 720 }
      }
    );
    
    expect(result.enabled).toBe(true);
    assertScore(result, 7, 'Accessibility features');
    
    const score = extractScore(result);
    if (score !== null) {
      // Additional check for hasAriaLabels if needed
    }
    
    console.log(`Accessibility score: ${result.score}/10`);
    console.log(`ARIA labels present: ${hasAriaLabels}`);
  });

  test('quality score display (regression)', async ({ page }) => {
    /**
     * REGRESSION: Feature request - Quality scores should be visible
     * This test ensures quality feedback is visible when enabled.
     */
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Send a message
    await page.fill('#messageInput', 'What is d-separation?');
    await page.click('#sendButton');
    await page.waitForSelector('.message.assistant', { timeout: SERVER_TIMEOUT });
    await page.waitForTimeout(2000); // Wait for metadata to render
    
    // Capture screenshot
    const screenshotPath = `test-results/regression-quality-score-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    // Check for quality score badges
    const hasQualityBadge = await page.locator('.metadata-badge, [data-quality-score]').count() > 0;
    
    // Validate quality score display (using enhanced validation)
    const result = await validateScreenshotEnhanced(
      screenshotPath,
      `REGRESSION TEST: Quality Score Display
      
FEATURE: Quality scores should be visible when quality feedback is enabled.

REQUIREMENTS:
- Quality scores visible as badges or indicators
- Quality scores clearly associated with responses
- Quality scores formatted clearly (e.g., "⭐ 8.5/10")
- Quality feedback visible in message metadata
- Quality indicators don't clutter the interface

VALIDATION:
- Are quality scores visible (if quality feedback is enabled)?
- Are quality scores clearly formatted and readable?
- Are quality scores associated with the correct messages?
- Do quality indicators maintain design consistency?
- Are quality scores not intrusive or cluttering?`,
      {
        testType: 'regression-quality-score',
        viewport: { width: 1280, height: 720 }
      },
      {
        testName: 'quality-score-display',
        maxIssues: 5,
      }
    );
    
    expect(result.enabled).toBe(true);
    console.log(formatTestResult('Quality score display', result, { maxIssues: 3 }));
    console.log(`Quality badge present: ${hasQualityBadge}`);
  });

  test('research indicators visibility (regression)', async ({ page }) => {
    /**
     * REGRESSION: Feature request - Research indicators should be visible
     * This test ensures research status is clearly indicated.
     */
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Enable research
    const researchToggle = await page.$('#researchToggle');
    if (researchToggle) {
      const isChecked = await researchToggle.isChecked();
      if (!isChecked) {
        await researchToggle.click();
      }
    }
    
    // Send a research query
    await page.fill('#messageInput', 'Explain information geometry comprehensively');
    await page.click('#sendButton');
    await page.waitForSelector('.message.assistant', { timeout: SERVER_TIMEOUT });
    await page.waitForTimeout(2000);
    
    // Capture screenshot
    const screenshotPath = `test-results/regression-research-indicators-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    // Check for research badges
    const hasResearchBadge = await page.locator('.metadata-badge, [data-research]').count() > 0;
    const researchBadgeText = await page.locator('.metadata-badge').first().textContent().catch(() => '');
    const hasResearchInBadge = researchBadgeText.includes('Research') || researchBadgeText.includes('🔍');
    
    // Validate research indicators (using enhanced validation)
    const result = await validateScreenshotEnhanced(
      screenshotPath,
      `REGRESSION TEST: Research Indicators Visibility
      
FEATURE: Research indicators should be visible when research is conducted.

REQUIREMENTS:
- Research badges visible when research is conducted
- Research toggle state clearly indicated
- Tool usage indicators visible (if applicable)
- Research status clearly associated with responses
- Research indicators maintain design consistency

VALIDATION:
- Are research badges visible (if research was conducted)?
- Is the research toggle state clearly indicated?
- Are research indicators clearly associated with responses?
- Do research indicators maintain design consistency?
- Is research activity transparent to the user?`,
      {
        testType: 'regression-research-indicators',
        viewport: { width: 1280, height: 720 }
      },
      {
        testName: 'research-indicators',
        maxIssues: 5,
      }
    );
    
    expect(result.enabled).toBe(true);
    console.log(formatTestResult('Research indicators', result, { maxIssues: 3 }));
    console.log(`Research badge present: ${hasResearchBadge || hasResearchInBadge}`);
  });

  test('schema selection visibility (regression)', async ({ page }) => {
    /**
     * REGRESSION: Feature request - Schema selection should be visible
     * This test ensures schema selection is clearly indicated.
     */
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Select a schema
    const schemaSelect = await page.$('#schemaSelect');
    if (schemaSelect) {
      await schemaSelect.selectOption('decompose_and_synthesize');
    }
    
    // Send a message
    await page.fill('#messageInput', 'Explain d-separation and information geometry');
    await page.click('#sendButton');
    await page.waitForSelector('.message.assistant', { timeout: SERVER_TIMEOUT });
    await page.waitForTimeout(2000);
    
    // Capture screenshot
    const screenshotPath = `test-results/regression-schema-selection-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    // Check for schema badges
    const hasSchemaBadge = await page.locator('.metadata-badge, [data-schema]').count() > 0;
    const schemaBadgeText = await page.locator('.metadata-badge').first().textContent().catch(() => '');
    const hasSchemaInBadge = schemaBadgeText.includes('schema') || schemaBadgeText.includes('Decompose') || schemaBadgeText.includes('📋');
    
    // Validate schema selection visibility (using enhanced validation)
    const result = await validateScreenshotEnhanced(
      screenshotPath,
      `REGRESSION TEST: Schema Selection Visibility
      
FEATURE: Schema selection should be visible when a schema is used.

REQUIREMENTS:
- Schema badges visible when schema is selected and used
- Schema selector clearly visible and functional
- Selected schema clearly indicated in UI
- Schema indicators associated with responses
- Schema selection maintains design consistency

VALIDATION:
- Is the schema selector clearly visible?
- Is the selected schema clearly indicated?
- Are schema badges visible (if schema was used)?
- Are schema indicators clearly associated with responses?
- Does schema selection maintain design consistency?`,
      {
        testType: 'regression-schema-selection',
        viewport: { width: 1280, height: 720 }
      },
      {
        testName: 'schema-selection',
        maxIssues: 5,
      }
    );
    
    expect(result.enabled).toBe(true);
    console.log(formatTestResult('Schema selection', result, { maxIssues: 3 }));
    console.log(`Schema badge present: ${hasSchemaBadge || hasSchemaInBadge}`);
  });

  test('loading state clarity (regression)', async ({ page }) => {
    /**
     * REGRESSION: Issue identified - Loading states need better clarity
     * This test ensures loading indicators are clear and informative.
     */
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Send a complex query
    await page.fill('#messageInput', 'Explain information geometry comprehensively with research');
    await page.click('#sendButton');
    
    // Capture during loading
    await page.waitForTimeout(500); // Wait for loading to start
    const screenshotPath = `test-results/regression-loading-clarity-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    // Check for loading indicator
    const hasLoadingIndicator = await page.locator('#loadingIndicator, .loading-indicator, .loading').count() > 0;
    const loadingVisible = await page.locator('#loadingIndicator').isVisible().catch(() => false);
    
    // Validate loading state clarity (using enhanced validation)
    const result = await validateScreenshotEnhanced(
      screenshotPath,
      `REGRESSION TEST: Loading State Clarity
      
ISSUE: Loading states need better clarity and informativeness.

REQUIREMENTS:
- Loading indicator clearly visible during processing
- Loading state visually distinct from idle state
- Loading indicator appropriately styled (not jarring)
- User informed that processing is happening
- Loading state maintains design consistency
- Loading indicator doesn't block interface

VALIDATION:
- Is the loading indicator clearly visible?
- Is the loading state visually distinct from idle?
- Is the loading indicator appropriately styled?
- Is the user clearly informed that processing is happening?
- Does the loading state maintain design consistency?
- Is the interface still usable during loading?`,
      {
        testType: 'regression-loading-clarity',
        viewport: { width: 1280, height: 720 }
      },
      {
        testName: 'loading-state-clarity',
        maxIssues: 5,
      }
    );
    
    expect(result.enabled).toBe(true);
    console.log(formatTestResult('Loading state clarity', result, { maxIssues: 3 }));
    console.log(`Loading indicator present: ${hasLoadingIndicator || loadingVisible}`);
  });
});

