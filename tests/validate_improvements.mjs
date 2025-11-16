/**
 * Validate UI Improvements
 * Quick test to verify accessibility and loading state improvements
 */

import { test, expect } from '@playwright/test';

const SERVER_URL = process.env.BOP_SERVER_URL || 'http://localhost:8000';

test.describe('UI Improvements Validation', () => {
  test.setTimeout(30000);
  
  test.beforeEach(async ({ page }) => {
    // Wait for server
    let retries = 0;
    while (retries < 10) {
      try {
        const response = await fetch(`${SERVER_URL}/health`);
        if (response.ok) break;
      } catch (error) {
        // Server not ready yet
      }
      await new Promise(resolve => setTimeout(resolve, 1000));
      retries++;
    }
    
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
  });

  test('ARIA labels present', async ({ page }) => {
    const input = page.locator('#messageInput');
    const sendButton = page.locator('#sendButton');
    const researchToggle = page.locator('#researchToggle');
    const schemaSelect = page.locator('#schemaSelect');
    
    await expect(input).toHaveAttribute('aria-label', 'Message input');
    await expect(sendButton).toHaveAttribute('aria-label', 'Send message');
    await expect(researchToggle).toHaveAttribute('aria-label', 'Enable research mode');
    await expect(schemaSelect).toHaveAttribute('aria-label', 'Select reasoning schema');
    
    console.log('✅ All ARIA labels present');
  });

  test('Loading indicator accessibility', async ({ page }) => {
    const loadingIndicator = page.locator('#loadingIndicator');
    
    // Check attributes when visible
    await page.fill('#messageInput', 'Test');
    await page.click('#sendButton');
    
    // Wait a bit for loading to show
    await page.waitForTimeout(500);
    
    const role = await loadingIndicator.getAttribute('role');
    const ariaLive = await loadingIndicator.getAttribute('aria-live');
    const ariaLabel = await loadingIndicator.getAttribute('aria-label');
    
    expect(role).toBe('status');
    expect(ariaLive).toBe('polite');
    expect(ariaLabel).toBe('Processing your request');
    
    console.log('✅ Loading indicator accessibility verified');
  });

  test('Loading text present', async ({ page }) => {
    await page.fill('#messageInput', 'Test');
    await page.click('#sendButton');
    
    await page.waitForTimeout(500);
    
    const loadingText = page.locator('#loadingIndicator .loading-text');
    const textContent = await loadingText.textContent();
    
    expect(textContent).toBeTruthy();
    expect(textContent.length).toBeGreaterThan(0);
    
    console.log(`✅ Loading text: "${textContent}"`);
  });

  test('Screen reader help text present', async ({ page }) => {
    const inputHelp = page.locator('#input-help');
    const researchHelp = page.locator('#research-help');
    const schemaHelp = page.locator('#schema-help');
    
    await expect(inputHelp).toHaveClass(/sr-only/);
    await expect(researchHelp).toHaveClass(/sr-only/);
    await expect(schemaHelp).toHaveClass(/sr-only/);
    
    // Verify text content
    const inputHelpText = await inputHelp.textContent();
    const researchHelpText = await researchHelp.textContent();
    const schemaHelpText = await schemaHelp.textContent();
    
    expect(inputHelpText).toContain('Enter your question');
    expect(researchHelpText).toContain('Toggle to enable');
    expect(schemaHelpText).toContain('Choose a reasoning schema');
    
    console.log('✅ Screen reader help text present');
  });

  test('Example query buttons have ARIA labels', async ({ page }) => {
    const exampleButtons = page.locator('.example-query');
    const count = await exampleButtons.count();
    
    for (let i = 0; i < count; i++) {
      const button = exampleButtons.nth(i);
      const ariaLabel = await button.getAttribute('aria-label');
      expect(ariaLabel).toBeTruthy();
      expect(ariaLabel).toContain('Example query:');
    }
    
    console.log(`✅ ${count} example query buttons have ARIA labels`);
  });
});

