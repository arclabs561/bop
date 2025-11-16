/**
 * Quick Visual Test - Fast validation of UI improvements
 */

import { test, expect } from '@playwright/test';
import { validateScreenshotEnhanced, waitForServer, formatTestResult, assertScore } from './visual_test_utils.mjs';

const SERVER_URL = process.env.BOP_SERVER_URL || 'http://localhost:8000';

test.describe('Quick Visual Validation', () => {
  test.setTimeout(30000);
  test.beforeEach(async ({ page }) => {
    await waitForServer(SERVER_URL, { maxRetries: 5, timeout: 15000 });
  });

  test('accessibility improvements', async ({ page }) => {
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Check for ARIA labels
    const hasAriaLabels = await page.evaluate(() => {
      const input = document.getElementById('messageInput');
      const sendButton = document.getElementById('sendButton');
      const researchToggle = document.getElementById('researchToggle');
      return !!(input?.getAttribute('aria-label') && 
               sendButton?.getAttribute('aria-label') &&
               researchToggle?.getAttribute('aria-label'));
    });
    
    expect(hasAriaLabels).toBe(true);
    
    // Check for loading indicator accessibility
    const loadingIndicator = await page.$('#loadingIndicator');
    if (loadingIndicator) {
      const hasRole = await loadingIndicator.getAttribute('role');
      const hasAriaLive = await loadingIndicator.getAttribute('aria-live');
      expect(hasRole).toBe('status');
      expect(hasAriaLive).toBe('polite');
    }
    
    console.log('✅ Accessibility improvements verified');
  });

  test('loading state visibility', async ({ page }) => {
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Send a message to trigger loading
    await page.fill('#messageInput', 'Test');
    await page.click('#sendButton');
    
    // Wait for loading indicator
    await page.waitForSelector('#loadingIndicator[style*="flex"], #loadingIndicator[style*="block"]', { timeout: 2000 }).catch(() => null);
    
    // Check if loading indicator is visible
    const loadingVisible = await page.evaluate(() => {
      const indicator = document.getElementById('loadingIndicator');
      if (!indicator) return false;
      const style = window.getComputedStyle(indicator);
      return style.display !== 'none';
    });
    
    if (loadingVisible) {
      // Check for loading text
      const hasLoadingText = await page.evaluate(() => {
        const indicator = document.getElementById('loadingIndicator');
        const text = indicator?.querySelector('.loading-text');
        return !!text?.textContent;
      });
      
      expect(hasLoadingText).toBe(true);
      console.log('✅ Loading state improvements verified');
    }
  });
});

