/**
 * Enhanced E2E Visual Tests with BOP Principles, Wisdom, and Constraints
 * 
 * Tests the BOP web UI visually using AI-powered visual testing, incorporating:
 * - BOP theoretical principles (d-separation, information geometry, topological structure)
 * - Grice's maxims (Quality, Quantity, Relation, Manner, Benevolence, Transparency)
 * - Semantic properties (consistency, coherence, correctness, appropriateness)
 * - Behavioral properties (conversational flow, context maintenance)
 * - Knowledge structure research principles
 * - Quality feedback visibility
 * - Research capabilities visibility
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
  formatTestResult,
  assertScore,
  waitForServer,
  getCostSummary,
  resetCostTracking,
} from './visual_test_utils.mjs';

// Server configuration
const SERVER_URL = process.env.BOP_SERVER_URL || 'http://localhost:8000';
const SERVER_TIMEOUT = 60000; // 60 seconds for research queries

// Configure VLLM (auto-detects from env vars)
const config = createConfig({
  provider: process.env.VLM_PROVIDER || 'gemini',
  cacheEnabled: true,
  verbose: process.env.DEBUG_VLLM === 'true'
});

// BOP Principles Context for Prompts
const BOP_PRINCIPLES = `
BOP (Knowledge Structure Research Agent) Principles:
- D-separation preservation: Maintains causal structure in knowledge representation
- Information geometry: Uses Fisher Information for structure quality assessment
- Topological structure: Clique complexes for coherent context sets
- Serial scaling: Dependent reasoning chains with depth constraints
- Quality feedback: Continuous evaluation and adaptive learning
- Structured reasoning: Schema-guided decomposition and synthesis
- MCP lazy evaluation: On-demand context loading to preserve attention
- Research transparency: Clear indication of research conducted and tools used
`;

const GRICE_MAXIMS = `
Grice's Cooperative Principles (augmented for AI):
- Quality: Truthful, evidence-based responses (no hallucinations)
- Quantity: Right amount of information (not too brief, not too verbose)
- Relation: Relevant to the query and context
- Manner: Clear, organized, unambiguous communication
- Benevolence: No harmful content, ethical considerations
- Transparency: Acknowledge knowledge boundaries and limitations
`;

test.describe('BOP Web UI Visual Tests (Enhanced with Principles)', () => {
  
  test.beforeAll(() => {
    resetCostTracking();
  });
  
  test.afterAll(() => {
    const costSummary = getCostSummary();
    if (costSummary.totalCalls > 0) {
      console.log('\n💰 Enhanced Tests Cost Summary:');
      console.log(`  Total API calls: ${costSummary.totalCalls}`);
      const totalCost = typeof costSummary.totalCost === 'number' ? costSummary.totalCost : 0;
      const avgCost = typeof costSummary.averageCostPerCall === 'number' ? costSummary.averageCostPerCall : 0;
      console.log(`  Estimated cost: $${totalCost.toFixed(6)}`);
      console.log(`  Average per call: $${avgCost.toFixed(6)}`);
    }
  });
  
  test.beforeEach(async ({ page }) => {
    await waitForServer(SERVER_URL);
  });

  test('chat interface with BOP principles', async ({ page }) => {
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Capture screenshot
    const screenshotPath = `test-results/chat-interface-principles-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    // Validate with VLLM incorporating BOP principles (using enhanced validation)
    const result = await validateScreenshotEnhanced(
      screenshotPath,
      `${BOP_PRINCIPLES}

Evaluate the chat interface comprehensively, ensuring it embodies BOP principles:

LAYOUT & STRUCTURE (Knowledge Structure Principles):
- Is the chat interface clearly visible and well-organized (coherent structure)?
- Is the input field prominently displayed (clear entry point)?
- Is the chat history area properly sized and scrollable (context preservation)?
- Are there clear visual boundaries between elements (topological separation)?
- Does the layout support serial scaling (sequential conversation flow)?

DESIGN QUALITY (Information Geometry):
- Is the design modern and clean (inspired by manus.im/marimo)?
- Is contrast sufficient for readability (≥4.5:1 for normal text, ≥21:1 for brutalist)?
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
        testType: 'chat-interface-principles',
        viewport: { width: 1280, height: 720 }
      },
      {
        testName: 'chat-interface-principles',
        maxIssues: 5,
      }
    );
    
    // Assertions with enhanced utilities
    expect(result.enabled).toBe(true);
    assertScore(result, 7, 'Chat interface (principles)');
    expect(result.issues).toBeInstanceOf(Array);
    
    console.log(formatTestResult('Chat interface (principles)', result, { maxIssues: 3 }));
  });

  test('message flow with Grice maxims validation', async ({ page }) => {
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Send a test message
    const testMessage = 'What is d-separation in causal inference?';
    await page.fill('#messageInput', testMessage);
    await page.click('#sendButton');
    
    // Wait for response
    await page.waitForSelector('.message.assistant', { 
      timeout: SERVER_TIMEOUT 
    });
    
    // Wait for message to fully render
    await page.waitForTimeout(2000);
    
    // Capture screenshot
    const screenshotPath = `test-results/message-flow-grice-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    // Extract message text for semantic validation
    const messages = await page.$$eval('.message', (els) => 
      els.map(el => ({
        role: el.classList.contains('user') ? 'user' : 'assistant',
        text: el.textContent || ''
      }))
    );
    
    // Validate message rendering with Grice's maxims
    const result = await validateScreenshotEnhanced(
      screenshotPath,
      `${GRICE_MAXIMS}

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
        testType: 'message-flow-grice',
        viewport: { width: 1280, height: 720 }
      },
      {
        testName: 'message-flow-grice',
        maxIssues: 5,
      }
    );
    
    expect(result.enabled).toBe(true);
    assertScore(result, 7, 'Message flow (Grice)');
    
    console.log(formatTestResult('Message flow (Grice)', result, { maxIssues: 3 }));
    console.log(`Messages captured: ${messages.length}`);
  });

  test('research capabilities visibility', async ({ page }) => {
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Enable research toggle
    const researchToggle = await page.$('#researchToggle');
    if (researchToggle) {
      const isChecked = await researchToggle.isChecked();
      if (!isChecked) {
        await researchToggle.click();
      }
    }
    
    // Send a research query
    const testMessage = 'Explain information geometry comprehensively';
    await page.fill('#messageInput', testMessage);
    await page.click('#sendButton');
    
    // Wait for response
    await page.waitForSelector('.message.assistant', { 
      timeout: SERVER_TIMEOUT 
    });
    
    // Wait for metadata to render
    await page.waitForTimeout(2000);
    
    // Capture screenshot
    const screenshotPath = `test-results/research-capabilities-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    // Validate research capabilities visibility
    const result = await validateScreenshotEnhanced(
      screenshotPath,
      `${BOP_PRINCIPLES}

Evaluate research capabilities visibility and transparency:

RESEARCH TOGGLE (MCP Lazy Evaluation Principle):
- Is the research toggle clearly visible and accessible?
- Is the research state clearly indicated (on/off)?
- Is the toggle properly styled and functional?

RESEARCH INDICATORS (Transparency Principle):
- Are research badges visible when research is conducted?
- Is tool usage indicated (Perplexity, Firecrawl, Tavily, arXiv, Kagi)?
- Are research results integrated clearly into the response?
- Is the research process transparent to the user?

SCHEMA SELECTION (Structured Reasoning Principle):
- Is schema selection visible (if applicable)?
- Are schema options clearly presented?
- Is the selected schema indicated in the response?

QUALITY FEEDBACK (Adaptive Learning Principle):
- Are quality scores visible (if quality feedback is enabled)?
- Is adaptive learning indicated (if applicable)?
- Are quality improvements visible over time?`,
      {
        testType: 'research-capabilities',
        viewport: { width: 1280, height: 720 }
      },
      {
        testName: 'research-capabilities',
        maxIssues: 5,
      }
    );
    
    expect(result.enabled).toBe(true);
    // Research may not always trigger, so lower threshold
    const score = extractScore(result);
    if (score !== null) {
      assertScore(result, 6, 'Research capabilities');
    }
    
    console.log(formatTestResult('Research capabilities', result, { maxIssues: 3 }));
  });

  test('multi-turn conversation flow', async ({ page }) => {
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // First message
    await page.fill('#messageInput', 'What is d-separation?');
    await page.click('#sendButton');
    await page.waitForSelector('.message.assistant', { timeout: SERVER_TIMEOUT });
    await page.waitForTimeout(1000);
    
    // Second message (follow-up)
    await page.fill('#messageInput', 'How does it relate to information geometry?');
    await page.click('#sendButton');
    await page.waitForSelector('.message.assistant:nth-of-type(2)', { timeout: SERVER_TIMEOUT });
    await page.waitForTimeout(1000);
    
    // Capture screenshot
    const screenshotPath = `test-results/multi-turn-flow-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    // Validate multi-turn flow
    const result = await validateScreenshotEnhanced(
      screenshotPath,
      `${GRICE_MAXIMS}
${BOP_PRINCIPLES}

Evaluate multi-turn conversation flow:

CONVERSATION HISTORY (Context Preservation):
- Are all messages visible in the chat history?
- Is the conversation flow clear (user → assistant → user → assistant)?
- Is context maintained visually (related messages grouped)?
- Can users scroll through the full conversation?

CONTEXT MAINTENANCE (D-Separation Principle):
- Does the interface show context continuity?
- Are follow-up questions clearly related to previous messages?
- Is the conversation thread visually coherent?

TURN-TAKING (Behavioral Property):
- Are messages properly sequenced?
- Is there clear visual distinction between turns?
- Is the conversation flow natural and intuitive?

RESPONSE CONSISTENCY (Semantic Property):
- Do responses appear consistent with previous context?
- Is there visual coherence across the conversation?
- Are quality indicators consistent?`,
      {
        testType: 'multi-turn-flow',
        viewport: { width: 1280, height: 720 }
      },
      {
        testName: 'multi-turn-flow',
        maxIssues: 5,
      }
    );
    
    expect(result.enabled).toBe(true);
    assertScore(result, 7, 'Multi-turn flow');
    
    console.log(formatTestResult('Multi-turn flow', result, { maxIssues: 3 }));
  });

  test('error handling and recovery', async ({ page }) => {
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Try to trigger an error (very long message or invalid input)
    const longMessage = 'a'.repeat(5000); // Exceeds maxlength
    await page.fill('#messageInput', longMessage);
    
    // Check if input is truncated or error is shown
    const inputValue = await page.$eval('#messageInput', el => el.value);
    
    // Try to send (may fail or be truncated)
    await page.click('#sendButton');
    
    // Wait a bit to see if error appears
    await page.waitForTimeout(2000);
    
    // Capture screenshot
    const screenshotPath = `test-results/error-handling-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    // Validate error handling
    const result = await validateScreenshotEnhanced(
      screenshotPath,
      `${GRICE_MAXIMS}

Evaluate error handling and recovery:

ERROR DISPLAY (Grice's Transparency Maxim):
- Are error messages clearly visible if errors occur?
- Are error messages user-friendly and actionable?
- Is error styling appropriate (not alarming but clear)?
- Do errors acknowledge knowledge boundaries (Transparency maxim)?

ERROR RECOVERY (Behavioral Property):
- Can users recover from error states?
- Is there a way to dismiss or retry?
- Is the interface still usable after errors?
- Are errors handled gracefully (no broken UI)?

INPUT VALIDATION (Quality Maxim):
- Are input constraints clearly indicated (maxlength, etc.)?
- Is validation feedback immediate and clear?
- Are invalid inputs prevented or clearly marked?`,
      {
        testType: 'error-handling',
        viewport: { width: 1280, height: 720 }
      }
    );
    
    expect(result.enabled).toBe(true);
    console.log(`Error handling score: ${result.score || 'N/A'}/10`);
    console.log(`Input value length: ${inputValue.length}`);
  });

  test('loading states with quality principles', async ({ page }) => {
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Send a complex query that will take time
    const testMessage = 'Explain information geometry, d-separation, and attractor basins comprehensively';
    await page.fill('#messageInput', testMessage);
    await page.click('#sendButton');
    
    // Capture temporal screenshots during loading
    const screenshots = await captureTemporalScreenshots(page, 2, 10000); // 2 fps, 10 seconds
    
    expect(screenshots.length).toBeGreaterThan(0);
    
    // Validate loading states
    if (screenshots.length > 0) {
      const loadingScreenshot = screenshots[0];
      const result = await validateScreenshotEnhanced(
        loadingScreenshot.path,
        `${BOP_PRINCIPLES}

Evaluate loading state with BOP principles:

LOADING INDICATOR (Transparency Principle):
- Is there a clear loading indicator when processing?
- Is the loading state visually distinct from idle state?
- Is the user informed that processing is happening?
- Does the loading indicator reflect research activity (if research enabled)?

ANIMATION QUALITY (Information Geometry):
- Are animations smooth and not jarring (preserves attention)?
- Is the loading indicator appropriately styled (minimal distraction)?
- Does the loading state maintain design consistency (coherent structure)?

PROCESS TRANSPARENCY (MCP Lazy Evaluation):
- Is research activity indicated during loading (if research enabled)?
- Are tool calls visible (if tool usage is shown)?
- Is the processing state clear (thinking, researching, synthesizing)?`,
        {
          testType: 'loading-state-principles',
          viewport: { width: 1280, height: 720 }
        }
      );
      
      expect(result.enabled).toBe(true);
      console.log(`Loading state (principles) score: ${result.score || 'N/A'}/10`);
    }
    
    console.log(`Captured ${screenshots.length} temporal screenshots`);
  });

  test('comprehensive multi-perspective evaluation', async ({ page }) => {
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Send a query
    const testMessage = 'What is d-separation?';
    await page.fill('#messageInput', testMessage);
    await page.click('#sendButton');
    
    await page.waitForSelector('.message.assistant', { timeout: SERVER_TIMEOUT });
    await page.waitForTimeout(2000);
    
    // Extract rendered code
    const renderedCode = await extractRenderedCode(page);
    
    // Capture screenshot
    const screenshotPath = `test-results/comprehensive-multimodal-${Date.now()}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    
    // Multi-perspective evaluation with BOP principles
    const validateFn = (path, prompt, context) => 
      validateScreenshot(path, prompt, context);
    
    const evaluations = await multiPerspectiveEvaluation(
      validateFn,
      screenshotPath,
      renderedCode,
      {},
      [
        {
          name: 'BOP Knowledge Structure Expert',
          perspective: `Evaluate from BOP knowledge structure perspective: ${BOP_PRINCIPLES}
- D-separation preservation in UI structure
- Information geometry (clarity, structure quality)
- Topological coherence (visual organization)
- Research transparency (MCP lazy evaluation indicators)
- Quality feedback visibility (adaptive learning)`,
          focus: ['knowledge_structure', 'd_separation', 'information_geometry', 'research_transparency']
        },
        {
          name: 'Grice Maxims Evaluator',
          perspective: `Evaluate from Grice's maxims perspective: ${GRICE_MAXIMS}
- Quality: Truthful, evidence-based (no hallucinations visible)
- Quantity: Right amount of information (appropriate length)
- Relation: Relevant to query (contextual appropriateness)
- Manner: Clear, organized (visual clarity)
- Benevolence: No harmful content (ethical considerations)
- Transparency: Knowledge boundaries acknowledged`,
          focus: ['grice_maxims', 'quality', 'quantity', 'relation', 'manner', 'transparency']
        },
        {
          name: 'Semantic Properties Analyst',
          perspective: `Evaluate semantic properties:
- Semantic consistency (coherent terminology, stable definitions)
- Logical coherence (reasoning soundness visible)
- Factual correctness (evidence-based claims)
- Contextual appropriateness (tone, level, intent matching)`,
          focus: ['semantic_consistency', 'logical_coherence', 'factual_correctness', 'contextual_appropriateness']
        },
        {
          name: 'Behavioral Properties Specialist',
          perspective: `Evaluate behavioral properties:
- Conversational flow (natural transitions, turn-taking)
- Context maintenance (conversation history visibility)
- User intent understanding (query-response matching)
- Error handling (graceful degradation, recovery)`,
          focus: ['conversational_flow', 'context_maintenance', 'intent_understanding', 'error_handling']
        },
        {
          name: 'Accessibility & Usability Expert',
          perspective: `Evaluate accessibility and usability:
- WCAG compliance (contrast, ARIA labels, keyboard navigation)
- Mobile responsiveness (touch targets, viewport adaptation)
- Visual clarity (readability, hierarchy, spacing)
- Error recovery (clear error messages, retry mechanisms)`,
          focus: ['accessibility', 'wcag', 'mobile', 'usability', 'error_recovery']
        }
      ]
    );
    
    // Assertions
    expect(evaluations.length).toBeGreaterThan(0);
    evaluations.forEach(evaluation => {
      expect(evaluation.persona).toBeDefined();
      expect(evaluation.evaluation).toBeDefined();
    });
    
    console.log(`Comprehensive multi-modal evaluations: ${evaluations.length} perspectives`);
    evaluations.forEach(evaluation => {
      console.log(`  ${evaluation.persona}: ${evaluation.evaluation.score || 'N/A'}/10`);
    });
    
    // Check for consistent high scores across perspectives
    const scores = evaluations
      .map(e => e.evaluation.score)
      .filter(s => s !== null && s !== undefined);
    
    if (scores.length > 0) {
      const avgScore = scores.reduce((a, b) => a + b, 0) / scores.length;
      console.log(`Average score across perspectives: ${avgScore.toFixed(2)}/10`);
      expect(avgScore).toBeGreaterThanOrEqual(6); // Minimum acceptable average
    }
  });
});

