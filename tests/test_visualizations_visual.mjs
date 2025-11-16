/**
 * Visual Tests for BOP Visualization Features
 * 
 * Tests the visual rendering of:
 * - Token importance charts
 * - Source matrix heatmaps  
 * - Document relationship graphs
 * - Trust metrics charts
 * 
 * Uses Playwright + ai-visual-test for semantic visual validation.
 */

import { test, expect } from '@playwright/test';
import {
  validateScreenshot,
  extractRenderedCode,
  multiPerspectiveEvaluation,
  createConfig
} from '@arclabs561/ai-visual-test';
import {
  validateScreenshotEnhanced,
  extractScore,
  filterOutput,
  formatTestResult,
  assertScore,
  waitForServer,
  getCostSummary,
  resetCostTracking,
} from './visual_test_utils.mjs';

// Server configuration
const SERVER_URL = process.env.BOP_SERVER_URL || 'http://localhost:8000';
const SERVER_TIMEOUT = 30000;

// Configure VLLM
const config = createConfig({
  provider: process.env.VLM_PROVIDER || 'gemini',
  cacheEnabled: true,
  verbose: process.env.DEBUG_VLLM === 'true'
});

test.describe('BOP Visualization Features Visual Tests', () => {
  
  test.beforeAll(() => {
    resetCostTracking();
  });
  
  test.afterAll(() => {
    const costSummary = getCostSummary();
    if (costSummary.totalCalls > 0) {
      console.log('\n💰 Visualization Tests Cost Summary:');
      console.log(`  Total API calls: ${costSummary.totalCalls}`);
      const totalCost = typeof costSummary.totalCost === 'number' ? costSummary.totalCost : 0;
      console.log(`  Estimated cost: $${totalCost.toFixed(6)}`);
    }
  });
  
  test.beforeEach(async ({ page }) => {
    await waitForServer(SERVER_URL, {
      maxRetries: 10,
      retryDelay: 1000,
      timeout: 30000,
    });
  });

  test('token importance chart renders correctly', async ({ page }) => {
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Send a query that will trigger research and token importance
    const input = page.locator('input[type="text"], textarea').first();
    await input.fill('What is d-separation in causal inference?');
    
    const sendButton = page.locator('button:has-text("Send"), button[type="submit"]').first();
    await sendButton.click();
    
    // Wait for response
    await page.waitForTimeout(5000);
    await page.waitForLoadState('networkidle');
    
    // Capture screenshot
    const screenshotPath = `test-results/token-importance-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    // Validate with VLLM
    const result = await validateScreenshotEnhanced(
      screenshotPath,
      `Evaluate the token importance visualization:

VISUALIZATION QUALITY:
- Is there a table or chart showing token/term importance?
- Are terms displayed with visual bars or indicators?
- Is the importance score clearly visible?
- Are terms ranked by importance (highest first)?
- Is the visualization readable and well-formatted?

DESIGN PRINCIPLES:
- Visual hierarchy: Most important terms should stand out
- Clarity: Scores and rankings should be easy to understand
- Consistency: Formatting should be consistent across terms
- Accessibility: Colors should have sufficient contrast

Rate the visualization quality (0-10) and provide specific feedback.`
    );
    
    const score = extractScore(result);
    console.log(`Token Importance Chart Score: ${score}/10`);
    console.log(filterOutput(result));
    
    // Assert minimum quality threshold
    assertScore(score, 6, 'Token importance chart visualization quality');
  });

  test('source matrix heatmap renders correctly', async ({ page }) => {
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Send a query that will trigger research with multiple sources
    const input = page.locator('input[type="text"], textarea').first();
    await input.fill('How does trust propagate in knowledge systems?');
    
    const sendButton = page.locator('button:has-text("Send"), button[type="submit"]').first();
    await sendButton.click();
    
    // Wait for response
    await page.waitForTimeout(5000);
    await page.waitForLoadState('networkidle');
    
    // Scroll to find source matrix
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(2000);
    
    // Capture screenshot
    const screenshotPath = `test-results/source-matrix-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    // Validate with VLLM
    const result = await validateScreenshotEnhanced(
      screenshotPath,
      `Evaluate the source matrix heatmap visualization:

VISUALIZATION QUALITY:
- Is there a table showing source agreement/disagreement?
- Are claims clearly listed with source positions?
- Is consensus status visible (agreement/disagreement)?
- Are visual indicators used (✓, ✗, ○) for source positions?
- Is the heatmap readable and well-organized?

DESIGN PRINCIPLES:
- Clarity: Source positions should be immediately clear
- Color coding: Agreement (green), disagreement (red), neutral (yellow)
- Organization: Claims should be logically ordered
- Completeness: All relevant sources should be shown

Rate the visualization quality (0-10) and provide specific feedback.`
    );
    
    const score = extractScore(result);
    console.log(`Source Matrix Heatmap Score: ${score}/10`);
    console.log(filterOutput(result));
    
    assertScore(score, 6, 'Source matrix heatmap visualization quality');
  });

  test('document relationship graph renders correctly', async ({ page }) => {
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Send a query that will trigger research
    const input = page.locator('input[type="text"], textarea').first();
    await input.fill('What are the relationships between trust, uncertainty, and knowledge?');
    
    const sendButton = page.locator('button:has-text("Send"), button[type="submit"]').first();
    await sendButton.click();
    
    // Wait for response
    await page.waitForTimeout(5000);
    await page.waitForLoadState('networkidle');
    
    // Scroll to find relationship graph
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(2000);
    
    // Capture screenshot
    const screenshotPath = `test-results/document-relationships-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    // Validate with VLLM
    const result = await validateScreenshotEnhanced(
      screenshotPath,
      `Evaluate the document relationship graph visualization:

VISUALIZATION QUALITY:
- Is there a table or graph showing document clusters?
- Are source clusters clearly identified?
- Are trust scores and coherence metrics visible?
- Is the cluster size (number of sources) shown?
- Is the visualization readable and informative?

DESIGN PRINCIPLES:
- Clarity: Clusters should be clearly distinguished
- Metrics: Trust, coherence, and size should be visible
- Organization: Clusters should be ordered by trust/quality
- Completeness: All relevant clusters should be shown

Rate the visualization quality (0-10) and provide specific feedback.`
    );
    
    const score = extractScore(result);
    console.log(`Document Relationship Graph Score: ${score}/10`);
    console.log(filterOutput(result));
    
    assertScore(score, 6, 'Document relationship graph visualization quality');
  });

  test('trust metrics chart renders correctly', async ({ page }) => {
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Send a query that will trigger research
    const input = page.locator('input[type="text"], textarea').first();
    await input.fill('Explain information geometry and trust metrics');
    
    const sendButton = page.locator('button:has-text("Send"), button[type="submit"]').first();
    await sendButton.click();
    
    // Wait for response
    await page.waitForTimeout(5000);
    await page.waitForLoadState('networkidle');
    
    // Scroll to find trust metrics
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight / 2));
    await page.waitForTimeout(2000);
    
    // Capture screenshot
    const screenshotPath = `test-results/trust-metrics-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    // Validate with VLLM
    const result = await validateScreenshotEnhanced(
      screenshotPath,
      `Evaluate the trust metrics chart visualization:

VISUALIZATION QUALITY:
- Is there a panel or chart showing trust metrics?
- Are average trust, credibility, and confidence visible?
- Is calibration error displayed?
- Are visual bars used to represent metric values?
- Is per-source credibility breakdown shown?

DESIGN PRINCIPLES:
- Visual bars: Metrics should use character-based bars (█, ░)
- Color coding: High (green), medium (yellow), low (red)
- Clarity: All metrics should be clearly labeled
- Completeness: All relevant trust metrics should be shown

Rate the visualization quality (0-10) and provide specific feedback.`
    );
    
    const score = extractScore(result);
    console.log(`Trust Metrics Chart Score: ${score}/10`);
    console.log(filterOutput(result));
    
    assertScore(score, 6, 'Trust metrics chart visualization quality');
  });

  test('all visualizations work together', async ({ page }) => {
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Enable visualizations toggle if present
    const vizToggle = page.locator('input[type="checkbox"], button').filter({ hasText: /visual/i }).first();
    if (await vizToggle.count() > 0) {
      await vizToggle.click();
    }
    
    // Send a comprehensive query
    const input = page.locator('input[type="text"], textarea').first();
    await input.fill('Research the latest developments in causal inference and d-separation');
    
    const sendButton = page.locator('button:has-text("Send"), button[type="submit"]').first();
    await sendButton.click();
    
    // Wait for response
    await page.waitForTimeout(8000);
    await page.waitForLoadState('networkidle');
    
    // Scroll through entire response
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(1000);
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(2000);
    
    // Capture full page screenshot
    const screenshotPath = `test-results/all-visualizations-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    // Validate with VLLM
    const result = await validateScreenshotEnhanced(
      screenshotPath,
      `Evaluate the integration of all visualization features:

INTEGRATION QUALITY:
- Are multiple visualizations present (token importance, source matrix, relationships, trust)?
- Do visualizations complement each other without overwhelming the UI?
- Is there clear visual separation between different visualizations?
- Is the overall layout balanced and readable?

DESIGN PRINCIPLES:
- Coherence: Visualizations should work together harmoniously
- Hierarchy: Most important information should be prominent
- Spacing: Adequate spacing between visualizations
- Consistency: Similar visualizations should use consistent styling

Rate the overall integration quality (0-10) and provide specific feedback.`
    );
    
    const score = extractScore(result);
    console.log(`All Visualizations Integration Score: ${score}/10`);
    console.log(filterOutput(result));
    
    assertScore(score, 6, 'All visualizations integration quality');
  });
});

