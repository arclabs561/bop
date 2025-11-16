/**
 * REFACTORED: Visual Test Utils Using Package Features
 * 
 * This shows how to refactor our wrapper to leverage package features
 * while keeping BOP-specific needs (principles, retries, formatting).
 */

import { 
  validateScreenshot,
  validateAccessibilityHybrid,
  extractSemanticInfo,
  getCostTracker
} from '@arclabs561/ai-visual-test';
import {
  checkAllTextContrast,
  checkKeyboardNavigation
} from '@arclabs561/ai-visual-test/validators';

/**
 * Enhanced validateScreenshot with BOP-specific needs
 * BUT leverages package features instead of duplicating
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
    useHybrid = false, // NEW: Use hybrid validator for accessibility
  } = options;
  
  // For accessibility tests, use hybrid validator (programmatic + VLLM)
  if (useHybrid || context.testType?.includes('accessibility')) {
    const page = context.page;
    if (page) {
      // Use hybrid validator: runs programmatic FIRST, then VLLM
      const result = await validateAccessibilityHybrid(
        page,
        screenshotPath,
        4.5, // minContrast
        {
          ...context,
          prompt: prompt, // Add BOP principles to prompt
          testType: context.testType || 'accessibility-hybrid'
        }
      );
      
      // Package already tracks costs automatically
      // But we can add test name metadata
      if (shouldTrack) {
        const costTracker = getCostTracker();
        // Cost is already tracked, just log test name
        console.log(`[Cost] ${testName}: tracked by package`);
      }
      
      // Filter output (BOP-specific)
      if (shouldFilter) {
        return filterOutput(result, options);
      }
      
      return result;
    }
  }
  
  // For non-accessibility tests, use regular validateScreenshot
  // Package already handles caching, cost tracking, retries
  let lastError = null;
  let attempts = 0;
  
  while (attempts <= maxRetries) {
    try {
      const result = await validateScreenshot(screenshotPath, prompt, context);
      
      // Package already tracks costs automatically
      if (shouldTrack) {
        const costTracker = getCostTracker();
        // Cost is already tracked, just log test name
        console.log(`[Cost] ${testName}: tracked by package`);
      }
      
      // Use package's semantic extraction (instead of our duplicate)
      const semanticInfo = extractSemanticInfo(result);
      
      // Filter output (BOP-specific)
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
 * Extract score using package's extractSemanticInfo (instead of duplicate)
 */
export function extractScore(result) {
  const semanticInfo = extractSemanticInfo(result);
  return semanticInfo.score;
}

/**
 * Get cost summary using package's cost tracker (instead of duplicate)
 */
export function getCostSummary() {
  const costTracker = getCostTracker();
  const stats = costTracker.getStats();
  
  return {
    totalCalls: stats.count,
    totalCost: stats.total,
    averageCost: stats.average,
    byProvider: stats.byProvider,
    byDate: stats.byDate,
    recent: stats.recent
  };
}

/**
 * Reset cost tracking using package's tracker
 */
export function resetCostTracking() {
  const costTracker = getCostTracker();
  costTracker.reset();
}

/**
 * Filter output (BOP-specific, keep this)
 */
export function filterOutput(result, options = {}) {
  // Keep our BOP-specific filtering logic
  // But use package's extractSemanticInfo for score
  const semanticInfo = extractSemanticInfo(result);
  
  return {
    ...result,
    score: semanticInfo.score,
    issues: result.issues?.slice(0, options.maxIssues || 5) || []
  };
}

/**
 * Format test result (BOP-specific, keep this)
 */
export function formatTestResult(testName, result, options = {}) {
  const semanticInfo = extractSemanticInfo(result);
  const score = semanticInfo.score;
  
  // Keep our BOP-specific formatting
  // But use package's semantic info
  return `${testName}: ${score}/10 (${result.issues?.length || 0} issues)`;
}

/**
 * Assert score with better error messages (keep this, but use package's extraction)
 */
export function assertScore(result, minScore, testName = 'Test') {
  const semanticInfo = extractSemanticInfo(result);
  const score = semanticInfo.score;
  
  if (score === null) {
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

