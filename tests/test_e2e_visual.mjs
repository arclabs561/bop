/**
 * E2E Visual Tests using ai-visual-test
 * 
 * Tests the BOP web UI visually using AI-powered visual testing.
 * Uses Playwright to interact with the server and ai-visual-test to validate.
 */

import { test, expect } from '@playwright/test';
import {
  validateScreenshot,
  extractRenderedCode,
  multiPerspectiveEvaluation,
  captureTemporalScreenshots,
  aggregateTemporalNotes,
  formatNotesForPrompt,
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
const SERVER_TIMEOUT = 30000; // 30 seconds

// Configure VLLM (auto-detects from env vars)
// Note: Package automatically handles caching, cost tracking, provider selection
const config = createConfig({
  provider: process.env.VLM_PROVIDER || 'gemini',
  cacheEnabled: true, // Package's built-in cache (7-day TTL)
  verbose: process.env.DEBUG_VLLM === 'true'
});

test.describe('BOP Web UI Visual Tests', () => {
  
  test.beforeAll(() => {
    // Reset cost tracking at start of suite
    resetCostTracking();
  });
  
  test.afterAll(() => {
    // Print cost summary
    const costSummary = getCostSummary();
    if (costSummary.totalCalls > 0) {
      console.log('\n💰 Cost Summary:');
      console.log(`  Total API calls: ${costSummary.totalCalls}`);
      const totalCost = typeof costSummary.totalCost === 'number' ? costSummary.totalCost : 0;
      const avgCost = typeof costSummary.averageCostPerCall === 'number' ? costSummary.averageCostPerCall : 0;
      console.log(`  Estimated cost: $${totalCost.toFixed(6)}`);
      console.log(`  Average per call: $${avgCost.toFixed(6)}`);
    }
  });
  
  test.beforeEach(async ({ page }) => {
    // Wait for server to be ready (using enhanced utility)
    await waitForServer(SERVER_URL, {
      maxRetries: 10,
      retryDelay: 1000,
      timeout: 30000,
    });
  });

  test('chat interface renders correctly', async ({ page }) => {
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Capture screenshot
    const screenshotPath = `test-results/chat-interface-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    // Validate with VLLM (enhanced with BOP principles and utilities)
    // Note: For accessibility tests, consider using validateAccessibilityHybrid instead
    // which runs programmatic checks first (free) before VLLM
    const result = await validateScreenshotEnhanced(
      screenshotPath,
      `BOP (Knowledge Structure Research Agent) Principles:
- D-separation preservation: Maintains causal structure in knowledge representation
- Information geometry: Uses Fisher Information for structure quality assessment
- Topological structure: Clique complexes for coherent context sets
- Quality feedback: Continuous evaluation and adaptive learning
- Research transparency: Clear indication of research conducted and tools used

Grice's Cooperative Principles (augmented for AI):
- Quality: Truthful, evidence-based responses
- Quantity: Right amount of information
- Relation: Relevant to query and context
- Manner: Clear, organized, unambiguous
- Transparency: Acknowledge knowledge boundaries

Evaluate the chat interface comprehensively, ensuring it embodies these principles:

LAYOUT & STRUCTURE (Knowledge Structure Principles):
- Is the chat interface clearly visible and well-organized (coherent structure)?
- Is the input field prominently displayed (clear entry point)?
- Is the chat history area properly sized and scrollable (context preservation)?
- Are there clear visual boundaries between elements (topological separation)?
- Does the layout support serial scaling (sequential conversation flow)?

DESIGN QUALITY (Information Geometry):
- Is the design modern and clean (inspired by manus.im/marimo)?
- Is contrast sufficient for readability (≥4.5:1 for normal text)?
- Is typography clear and readable (information clarity)?
- Are spacing and padding consistent (structural coherence)?
- Does the design minimize attention dilution (focused, uncluttered)?

MOBILE RESPONSIVENESS (Accessibility & Usability):
- Does the layout adapt well to the viewport?
- Are touch targets appropriately sized (≥44x44px)?
- Is text readable without zooming?

ACCESSIBILITY (Grice's Manner Maxim):
- Are interactive elements clearly identifiable?
- Is there sufficient color contrast?
- Is the interface keyboard navigable?
- Are ARIA labels present for screen readers?

QUALITY FEEDBACK VISIBILITY (BOP Principle):
- Are quality indicators visible (if present)?
- Is research status clearly indicated?
- Are schema selections visible (if applicable)?
- Is tool usage transparent?`,
      {
        testType: 'chat-interface',
        viewport: { width: 1280, height: 720 }
      },
      {
        testName: 'chat-interface',
        filterOutput: true,
        trackCost: true,
        maxIssues: 5,
      }
    );
    
    // Assertions with enhanced error messages
    expect(result.enabled).toBe(true);
    assertScore(result, 7, 'Chat interface');
    expect(result.issues).toBeInstanceOf(Array);
    
    // Formatted output
    console.log(formatTestResult('Chat interface', result, { verbose: false, maxIssues: 3 }));
  });

  test('mobile responsive layout', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE size
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Capture screenshot
    const screenshotPath = `test-results/mobile-layout-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    // Validate mobile layout (using enhanced utility for cost tracking and error handling)
    const result = await validateScreenshotEnhanced(
      screenshotPath,
      `Evaluate the mobile layout comprehensively:

MOBILE OPTIMIZATION:
- Is the layout optimized for mobile viewport (375x667)?
- Are touch targets appropriately sized (≥44x44px)?
- Is text readable without horizontal scrolling?
- Is the input field easily accessible?

RESPONSIVE DESIGN:
- Does the layout adapt well to narrow screens?
- Are elements properly stacked vertically?
- Is there appropriate spacing between elements?
- Is the chat history scrollable?

USABILITY:
- Can users easily type messages?
- Is the send button easily accessible?
- Is the interface intuitive on mobile?`,
      {
        testType: 'mobile-layout',
        viewport: { width: 375, height: 667 }
      },
      {
        testName: 'mobile-layout',
        filterOutput: true,
        trackCost: true,
        maxIssues: 5,
      }
    );
    
    expect(result.enabled).toBe(true);
    assertScore(result, 7, 'Mobile responsive layout');
    
    const score = extractScore(result);
    console.log(`Mobile layout score: ${score}/10`);
  });

  test('dark mode rendering', async ({ page }) => {
    // Enable dark mode
    await page.emulateMedia({ colorScheme: 'dark' });
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Wait a bit for dark mode to apply
    await page.waitForTimeout(500);
    
    // Capture screenshot
    const screenshotPath = `test-results/dark-mode-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    // Validate dark mode (using enhanced utility)
    const result = await validateScreenshotEnhanced(
      screenshotPath,
      `Evaluate dark mode rendering:

DARK MODE QUALITY:
- Is dark mode properly applied?
- Is contrast sufficient for readability (≥4.5:1 for normal text)?
- Are colors appropriate for dark backgrounds?
- Is there no harsh glare or eye strain?

VISUAL CONSISTENCY:
- Are all elements properly styled in dark mode?
- Is text readable against dark backgrounds?
- Are interactive elements clearly visible?
- Is the overall appearance cohesive?`,
      {
        testType: 'dark-mode',
        viewport: { width: 1280, height: 720 }
      },
      {
        testName: 'dark-mode',
        filterOutput: true,
        trackCost: true,
        maxIssues: 5,
      }
    );
    
    expect(result.enabled).toBe(true);
    assertScore(result, 5, 'Dark mode rendering'); // Lower threshold for dark mode
    
    const score = extractScore(result);
    console.log(`Dark mode score: ${score}/10`);
  });

  test('message flow and rendering', async ({ page }) => {
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Send a test message
    const testMessage = 'What is d-separation?';
    await page.fill('#messageInput', testMessage);
    await page.click('#sendButton');
    
    // Wait for response (with timeout)
    await page.waitForSelector('.message.assistant', { 
      timeout: SERVER_TIMEOUT 
    });
    
    // Wait a bit more for message to fully render
    await page.waitForTimeout(1000);
    
    // Capture screenshot
    const screenshotPath = `test-results/message-flow-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    // Validate message rendering (enhanced with Grice's maxims and utilities)
    const result = await validateScreenshotEnhanced(
      screenshotPath,
      `Grice's Cooperative Principles:
- Quality: Truthful, evidence-based responses (no hallucinations)
- Quantity: Right amount of information (not too brief, not too verbose)
- Relation: Relevant to the query and context
- Manner: Clear, organized, unambiguous communication
- Transparency: Acknowledge knowledge boundaries and limitations

BOP Principles:
- Research transparency: Clear indication of research conducted and tools used
- Quality feedback: Continuous evaluation and adaptive learning visibility
- Structured reasoning: Schema-guided responses with clear organization

Evaluate message flow and rendering, ensuring Grice's maxims are visually supported:

MESSAGE DISPLAY (Grice's Manner Maxim):
- Are messages clearly displayed in the chat history?
- Is the user message distinguishable from the assistant response?
- Is the message formatting readable and well-structured (clarity)?
- Are messages properly ordered (user message, then response)?
- Is the text organized logically (no ambiguity)?

VISUAL HIERARCHY (Information Structure):
- Is there clear visual distinction between message types?
- Are metadata badges visible (research, schema, quality score, tools)?
- Is the message area properly scrollable (context preservation)?
- Is the input field still accessible after messages are sent?

RESPONSE QUALITY INDICATORS (Grice's Quality & Transparency):
- Is research status clearly indicated (if research was conducted)?
- Are quality scores visible (if quality feedback is enabled)?
- Are schema selections shown (if schema was used)?
- Are tool usage indicators present (transparency)?
- Does the response appear complete (Quantity maxim: right amount)?

SEMANTIC COHERENCE (Visual Indicators):
- Does the response appear relevant to the query (Relation maxim)?
- Is the response length appropriate (Quantity maxim)?
- Are there visual indicators of response quality?
- Is error handling clear if something went wrong?`,
      {
        testType: 'message-flow',
        viewport: { width: 1280, height: 720 }
      },
      {
        testName: 'message-flow',
        filterOutput: true,
        trackCost: true,
        maxIssues: 5,
      }
    );
    
    expect(result.enabled).toBe(true);
    assertScore(result, 7, 'Message flow and rendering');
    
    const score = extractScore(result);
    console.log(`Message flow score: ${score}/10`);
  });

  test('multi-modal validation with rendered code', async ({ page }) => {
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Extract rendered code
    const renderedCode = await extractRenderedCode(page);
    
    // Capture screenshot
    const screenshotPath = `test-results/multimodal-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    // Multi-perspective evaluation
    const validateFn = (path, prompt, context) => 
      validateScreenshot(path, prompt, context);
    
    const evaluations = await multiPerspectiveEvaluation(
      validateFn,
      screenshotPath,
      renderedCode,
      {},
      [
        {
          name: 'Accessibility Advocate',
          perspective: 'Evaluate from accessibility viewpoint: WCAG compliance, contrast, keyboard navigation, screen reader support, ARIA labels.',
          focus: ['accessibility', 'wcag', 'contrast', 'aria']
        },
        {
          name: 'Modern UI Designer',
          perspective: 'Evaluate from modern UI design viewpoint: clean design inspired by manus.im/marimo, proper spacing, visual hierarchy, modern aesthetics.',
          focus: ['design', 'spacing', 'hierarchy', 'aesthetics']
        },
        {
          name: 'Mobile UX Expert',
          perspective: 'Evaluate from mobile UX viewpoint: touch targets, responsive layout, mobile-first design, usability on small screens.',
          focus: ['mobile', 'touch', 'responsive', 'usability']
        }
      ]
    );
    
    // Assertions
    expect(evaluations.length).toBeGreaterThan(0);
    evaluations.forEach(evaluation => {
      expect(evaluation.persona).toBeDefined();
      expect(evaluation.evaluation).toBeDefined();
    });
    
    console.log(`Multi-modal evaluations: ${evaluations.length} perspectives`);
    evaluations.forEach(evaluation => {
      console.log(`  ${evaluation.persona}: ${evaluation.evaluation.score || 'N/A'}/10`);
    });
  });

  test('loading states and animations', async ({ page }) => {
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Send a message that will trigger loading
    const testMessage = 'Explain information geometry comprehensively';
    await page.fill('#messageInput', testMessage);
    await page.click('#sendButton');
    
    // Capture temporal screenshots during loading/response
    const screenshots = await captureTemporalScreenshots(page, 2, 5000); // 2 fps, 5 seconds
    
    expect(screenshots.length).toBeGreaterThan(0);
    
    // Validate loading states (using enhanced utility)
    if (screenshots.length > 0) {
      const loadingScreenshot = screenshots[0];
      const result = await validateScreenshotEnhanced(
        loadingScreenshot.path,
        `Evaluate loading state:

LOADING INDICATOR:
- Is there a clear loading indicator when processing?
- Is the loading state visually distinct from idle state?
- Is the user informed that processing is happening?
- Is the interface still usable during loading?

ANIMATION QUALITY:
- Are animations smooth and not jarring?
- Is the loading indicator appropriately styled?
- Does the loading state maintain design consistency?`,
        {
          testType: 'loading-state',
          viewport: { width: 1280, height: 720 }
        },
        {
          testName: 'loading-state',
          filterOutput: true,
          trackCost: true,
          maxIssues: 5,
        }
      );
      
      expect(result.enabled).toBe(true);
      console.log(`Loading state score: ${result.score || 'N/A'}/10`);
    }
    
    console.log(`Captured ${screenshots.length} temporal screenshots`);
  });

  test('error state rendering', async ({ page }) => {
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Try to trigger an error (e.g., invalid request)
    // This might require mocking or specific error conditions
    // For now, we'll just test the error UI if it exists
    
    // Capture screenshot
    const screenshotPath = `test-results/error-state-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    // Check if error UI exists and validate it
    const hasErrorUI = await page.locator('.error, [data-error], .error-message').count() > 0;
    
    if (hasErrorUI) {
      const result = await validateScreenshotEnhanced(
        screenshotPath,
        `Evaluate error state rendering:

ERROR DISPLAY:
- Is the error message clearly visible?
- Is the error message user-friendly and actionable?
- Is the error styling appropriate (not alarming but clear)?
- Can users recover from the error state?

ERROR HANDLING:
- Is there a way to dismiss or retry?
- Is the error message informative?
- Does the error state maintain design consistency?`,
        {
          testType: 'error-state',
          viewport: { width: 1280, height: 720 }
        },
        {
          testName: 'error-state',
          filterOutput: true,
          trackCost: true,
          maxIssues: 5,
        }
      );
      
      expect(result.enabled).toBe(true);
      console.log(`Error state score: ${result.score || 'N/A'}/10`);
    } else {
      console.log('No error UI found (this is OK if errors are handled differently)');
    }
  });
});

