/**
 * Visual Testing Framework Utilities
 * 
 * Provides robust helpers for visual testing:
 * - Score extraction from VLLM responses (uses package's extractSemanticInfo)
 * - Output filtering and summarization
 * - Cost tracking (uses package's CostTracker)
 * - Error handling
 * - Result normalization
 * 
 * REFACTORED: Now leverages ai-visual-test package features instead of duplicating:
 * - Uses getCostTracker() from package (no duplicate tracking)
 * - Uses extractSemanticInfo() from package (no duplicate extraction)
 * - Supports hybrid validators (programmatic + VLLM)
 */

import { 
  validateScreenshot,
  extractSemanticInfo,
  getCostTracker
} from '@arclabs561/ai-visual-test';
import {
  validateAccessibilityHybrid
} from '@arclabs561/ai-visual-test/validators';

/**
 * Extract score from VLLM result using package's extractSemanticInfo
 * @param {Object} result - VLLM validation result
 * @returns {number|null} Extracted score (0-10) or null if not found
 */
export function extractScore(result) {
  // Use package's extractSemanticInfo instead of duplicating logic
  try {
    const semanticInfo = extractSemanticInfo(result);
    return semanticInfo.score;
  } catch (error) {
    // Fallback to direct score if extraction fails
    if (result.score !== null && result.score !== undefined) {
      return typeof result.score === 'number' ? result.score : parseFloat(result.score);
    }
    return null;
  }
}

/**
 * Filter and summarize verbose VLLM output
 * @param {Object} result - VLLM validation result
 * @param {Object} options - Filtering options
 * @returns {Object} Filtered result with summary
 */
export function filterOutput(result, options = {}) {
  const {
    maxIssues = 5,
    maxIssueLength = 100,
    includeScore = true,
    includeSummary = true,
  } = options;
  
  const filtered = {
    ...result,
    score: extractScore(result),
  };
  
  // Filter issues
  if (Array.isArray(result.issues)) {
    // Prioritize issues: shorter, more actionable first
    const sortedIssues = result.issues
      .map(issue => typeof issue === 'string' ? issue : String(issue))
      .sort((a, b) => {
        // Shorter issues first (usually more actionable)
        if (a.length !== b.length) return a.length - b.length;
        // Then alphabetically
        return a.localeCompare(b);
      });
    
    // Take top N and truncate long ones
    filtered.issues = sortedIssues
      .slice(0, maxIssues)
      .map(issue => {
        if (issue.length > maxIssueLength) {
          return issue.substring(0, maxIssueLength - 3) + '...';
        }
        return issue;
      });
    
    // Add summary if there are more issues
    if (result.issues.length > maxIssues) {
      filtered.issuesSummary = `${result.issues.length - maxIssues} more issues not shown`;
    }
  }
  
  // Create summary
  if (includeSummary) {
    filtered.summary = {
      score: filtered.score,
      scoreStatus: filtered.score !== null 
        ? (filtered.score >= 7 ? 'good' : filtered.score >= 5 ? 'acceptable' : 'needs_improvement')
        : 'unknown',
      issuesCount: result.issues?.length || 0,
      keyIssues: filtered.issues || [],
    };
  }
  
  return filtered;
}

/**
 * Track cost for VLLM API calls using package's CostTracker
 * Note: Package automatically tracks costs from validateScreenshot calls.
 * This function adds test name metadata if needed.
 * @param {string} testName - Name of the test
 * @param {Object} result - VLLM validation result
 */
export function trackCost(testName, result) {
  // Package automatically tracks costs, but we can add metadata
  const costTracker = getCostTracker();
  
  // Extract cost from result if available
  const cost = result.estimatedCost?.totalCost || 
               result.cost || 
               result.pricing?.estimatedCost ||
               0;
  
  // Record with test name for better tracking
  if (cost > 0) {
    costTracker.recordCost({
      provider: result.provider || 'unknown',
      cost: typeof cost === 'string' ? parseFloat(cost) : cost,
      inputTokens: result.estimatedCost?.inputTokens || 0,
      outputTokens: result.estimatedCost?.outputTokens || 0,
      testName: testName,
      timestamp: Date.now()
    });
  }
}

/**
 * Get cost summary using package's CostTracker
 * @returns {Object} Cost tracking summary
 */
export function getCostSummary() {
  const costTracker = getCostTracker();
  
  // Ensure costs are initialized (package may not have initialized yet)
  if (!costTracker.costs) {
    costTracker.costs = { history: [], totals: {}, byProvider: {}, byDate: {} };
  }
  
  const stats = costTracker.getStats();
  
  return {
    totalCalls: stats.count || 0,
    totalCost: typeof stats.total === 'number' ? stats.total : 0,
    averageCostPerCall: typeof stats.average === 'number' ? stats.average : 0,
    byProvider: stats.byProvider || {},
    byDate: stats.byDate || {},
    callsByTest: (stats.recent || []).reduce((acc, entry) => {
      const testName = entry.testName || 'unknown';
      acc[testName] = (acc[testName] || 0) + 1;
      return acc;
    }, {}),
    costsByTest: (stats.recent || []).reduce((acc, entry) => {
      const testName = entry.testName || 'unknown';
      const cost = typeof entry.cost === 'number' ? entry.cost : 0;
      acc[testName] = (acc[testName] || 0) + cost;
      return acc;
    }, {}),
  };
}

/**
 * Reset cost tracking using package's CostTracker
 */
export function resetCostTracking() {
  const costTracker = getCostTracker();
  costTracker.reset();
}

/**
 * Enhanced validateScreenshot with robust error handling and output filtering
 * @param {string} screenshotPath - Path to screenshot
 * @param {string} prompt - Evaluation prompt
 * @param {Object} context - Validation context
 * @param {Object} options - Additional options
 * @returns {Promise<Object>} Enhanced validation result
 */
export async function validateScreenshotEnhanced(
  screenshotPath,
  prompt,
  context = {},
  options = {}
) {
  const {
    testName = 'unknown',
    filterOutput: shouldFilter = true,
    trackCost: shouldTrack = true,
    maxRetries = 2,
    retryDelay = 1000,
  } = options;
  
  let lastError = null;
  let attempts = 0;
  
  while (attempts <= maxRetries) {
    try {
      const result = await validateScreenshot(screenshotPath, prompt, context);
      
      // Track cost
      if (shouldTrack) {
        trackCost(testName, result);
      }
      
      // Filter output
      if (shouldFilter) {
        return filterOutput(result, options);
      }
      
      return result;
    } catch (error) {
      lastError = error;
      attempts++;
      
      // Don't retry on certain errors
      if (error.message?.includes('not found') || 
          error.message?.includes('invalid') ||
          attempts > maxRetries) {
        throw error;
      }
      
      // Wait before retry
      if (attempts <= maxRetries) {
        await new Promise(resolve => setTimeout(resolve, retryDelay * attempts));
      }
    }
  }
  
  throw lastError || new Error('Validation failed after retries');
}

/**
 * Format test result for console output
 * @param {string} testName - Name of the test
 * @param {Object} result - Validation result
 * @param {Object} options - Formatting options
 * @returns {string} Formatted output string
 */
export function formatTestResult(testName, result, options = {}) {
  const {
    verbose = false,
    showIssues = true,
    maxIssues = 3,
  } = options;
  
  const score = extractScore(result);
  const scoreStr = score !== null ? `${score}/10` : 'N/A';
  const scoreStatus = score !== null
    ? (score >= 7 ? '✅' : score >= 5 ? '⚠️' : '❌')
    : '❓';
  
  let output = `${scoreStatus} ${testName}: ${scoreStr}`;
  
  if (verbose) {
    output += `\n  Provider: ${result.provider || 'unknown'}`;
    output += `\n  Cached: ${result.cached ? 'yes' : 'no'}`;
    if (result.estimatedCost) {
      output += `\n  Cost: $${result.estimatedCost.totalCost?.toFixed(6) || '0.000000'}`;
    }
  }
  
  if (showIssues && result.issues && result.issues.length > 0) {
    const issuesToShow = result.issues.slice(0, maxIssues);
    output += `\n  Issues (${result.issues.length}): ${issuesToShow.join('; ')}`;
    if (result.issues.length > maxIssues) {
      output += ` ... (+${result.issues.length - maxIssues} more)`;
    }
  }
  
  return output;
}

/**
 * Assert score with better error messages
 * @param {Object} result - Validation result
 * @param {number} minScore - Minimum acceptable score
 * @param {string} testName - Name of the test (for error message)
 */
export function assertScore(result, minScore, testName = 'Test') {
  const score = extractScore(result);
  
  if (score === null) {
    // CRITICAL: Null scores mean we can't validate - this is a test failure
    // Don't silently pass - this indicates a problem with the test or VLLM
    throw new Error(
      `${testName} failed: Score is null - cannot verify threshold ${minScore}/10.\n` +
      `This indicates the VLLM validation failed or returned invalid data.\n` +
      `Check: VLLM API availability, screenshot quality, prompt clarity.`
    );
  }
  
  if (score < minScore) {
    const issues = result.issues?.slice(0, 3).join('; ') || 'No issues listed';
    throw new Error(
      `${testName} failed: Score ${score}/10 is below threshold ${minScore}/10.\n` +
      `Key issues: ${issues}`
    );
  }
}

/**
 * Wait for server to be ready with better error handling
 * @param {string} url - Server URL
 * @param {Object} options - Wait options
 * @returns {Promise<void>}
 */
export async function waitForServer(url, options = {}) {
  const {
    maxRetries = 10,
    retryDelay = 1000,
    timeout = 30000,
  } = options;
  
  const startTime = Date.now();
  let retries = 0;
  
  while (retries < maxRetries) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      
      const response = await fetch(`${url}/health`, {
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        return;
      }
    } catch (error) {
      // Continue retrying
    }
    
    // Check overall timeout
    if (Date.now() - startTime > timeout) {
      throw new Error(`Server not ready at ${url} after ${timeout}ms`);
    }
    
    await new Promise(resolve => setTimeout(resolve, retryDelay));
    retries++;
  }
  
  throw new Error(`Server not ready at ${url} after ${maxRetries} retries`);
}

/**
 * Extract rendered code safely (handles both string and object)
 * @param {Page} page - Playwright page object
 * @returns {Promise<string>} Rendered code as string
 */
export async function extractRenderedCodeSafe(page) {
  const renderedCode = await extractRenderedCode(page);
  
  if (typeof renderedCode === 'string') {
    return renderedCode;
  }
  
  if (typeof renderedCode === 'object' && renderedCode !== null) {
    // Try to extract HTML from object
    if (renderedCode.html) {
      return renderedCode.html;
    }
    if (renderedCode.content) {
      return renderedCode.content;
    }
    // Fallback to JSON string
    return JSON.stringify(renderedCode, null, 2);
  }
  
  return String(renderedCode);
}

// Note: extractRenderedCode should be imported directly from '@arclabs561/ai-visual-test'
// This utility provides a safe wrapper

