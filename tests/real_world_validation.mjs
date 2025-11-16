/**
 * Real-World Validation
 * 
 * Tests that actually matter for users, not just for compliance.
 */

import { test, expect } from '@playwright/test';

const SERVER_URL = process.env.BOP_SERVER_URL || 'http://localhost:8000';

test.describe('Real-World Validation - What Actually Matters', () => {
  test.setTimeout(60000);
  
  test('can a user actually have a conversation?', async ({ page }) => {
    // This is the ONLY test that actually matters
    // Everything else is secondary
    
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Can user type a message?
    await page.fill('#messageInput', 'What is d-separation?');
    const canType = await page.locator('#messageInput').inputValue() === 'What is d-separation?';
    
    // Can user send it?
    await page.click('#sendButton');
    await page.waitForTimeout(2000); // Wait for response
    
    // Did they get a response?
    const messages = page.locator('.message');
    const messageCount = await messages.count();
    const hasResponse = messageCount >= 2; // User message + response
    
    // Can they see the response?
    const lastMessage = messages.last();
    const lastMessageText = await lastMessage.textContent();
    const responseVisible = lastMessageText && lastMessageText.length > 10;
    
    console.log('\n📊 Real-World Functionality:');
    console.log(`  Can type: ${canType}`);
    console.log(`  Has response: ${hasResponse}`);
    console.log(`  Response visible: ${responseVisible}`);
    console.log(`  Response length: ${lastMessageText?.length || 0}`);
    
    // This is what actually matters
    expect(canType).toBe(true);
    expect(hasResponse).toBe(true);
    expect(responseVisible).toBe(true);
    
    // Everything else is nice-to-have, but this is essential
  });

  test('does it work on mobile?', async ({ page }) => {
    // Mobile is where most users are
    // Desktop testing is nice, but mobile is critical
    
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Can user see the interface?
    const header = page.locator('.header');
    const input = page.locator('#messageInput');
    const sendButton = page.locator('#sendButton');
    
    const headerVisible = await header.isVisible();
    const inputVisible = await input.isVisible();
    const buttonVisible = await sendButton.isVisible();
    
    // Can user interact?
    const inputSize = await input.boundingBox();
    const buttonSize = await sendButton.boundingBox();
    
    const inputBigEnough = inputSize && inputSize.height >= 44; // Touch target size
    const buttonBigEnough = buttonSize && buttonSize.width >= 44 && buttonSize.height >= 44;
    
    console.log('\n📱 Mobile Functionality:');
    console.log(`  Header visible: ${headerVisible}`);
    console.log(`  Input visible: ${inputVisible}`);
    console.log(`  Button visible: ${buttonVisible}`);
    console.log(`  Input size: ${inputSize ? `${inputSize.width}x${inputSize.height}` : 'unknown'}`);
    console.log(`  Button size: ${buttonSize ? `${buttonSize.width}x${buttonSize.height}` : 'unknown'}`);
    console.log(`  Input big enough: ${inputBigEnough}`);
    console.log(`  Button big enough: ${buttonBigEnough}`);
    
    // Mobile usability is critical
    expect(headerVisible).toBe(true);
    expect(inputVisible).toBe(true);
    expect(buttonVisible).toBe(true);
    expect(buttonBigEnough).toBe(true); // Button must be touchable
  });

  test('does it handle errors gracefully?', async ({ page }) => {
    // What happens when things go wrong?
    // This is where frameworks often fail
    
    await page.goto(`${SERVER_URL}/`);
    await page.waitForLoadState('networkidle');
    
    // Simulate network error
    await page.route('**/chat', route => route.abort());
    
    await page.fill('#messageInput', 'Test message');
    await page.click('#sendButton');
    
    await page.waitForTimeout(3000);
    
    // Does it show an error?
    const errorMessage = await page.locator('.message.error, .message:has-text("Error")').count();
    const hasError = errorMessage > 0;
    
    // Is the interface still usable?
    const inputEnabled = await page.locator('#messageInput').isEnabled();
    const canRetry = inputEnabled;
    
    console.log('\n❌ Error Handling:');
    console.log(`  Shows error: ${hasError}`);
    console.log(`  Still usable: ${canRetry}`);
    
    // Error handling is critical
    expect(hasError).toBe(true);
    expect(canRetry).toBe(true);
  });

  test('is it actually fast enough?', async ({ page }) => {
    // Performance matters more than most tests check
    
    await page.goto(`${SERVER_URL}/`);
    
    const loadStart = Date.now();
    await page.waitForLoadState('networkidle');
    const loadTime = Date.now() - loadStart;
    
    // Can user interact quickly?
    await page.fill('#messageInput', 'Test');
    const fillStart = Date.now();
    await page.click('#sendButton');
    await page.waitForTimeout(100); // Wait for UI update
    const interactionTime = Date.now() - fillStart;
    
    console.log('\n⚡ Performance:');
    console.log(`  Load time: ${loadTime}ms`);
    console.log(`  Interaction time: ${interactionTime}ms`);
    
    // These are the real metrics
    expect(loadTime).toBeLessThan(3000); // Should load in < 3s
    expect(interactionTime).toBeLessThan(500); // Should respond in < 500ms
  });

  test('are we testing what users care about?', async ({ page }) => {
    // The meta-question: are our tests aligned with user needs?
    
    const userNeeds = {
      canUseInterface: false,
      getsHelpfulResponses: false,
      canUseOnMobile: false,
      handlesErrors: false,
      isFastEnough: false,
    };
    
    // This is a summary test - if the above tests pass, this passes
    // But it makes the point: are we testing user needs?
    
    console.log('\n👤 User Needs Alignment:');
    console.log('  Question: Do our tests validate what users actually need?');
    console.log('  Question: Or are we testing what\'s easy to test?');
    console.log('  Question: Are we optimizing for users or for test coverage?');
    
    // The real test: do our tests align with user needs?
    // This is a philosophical question, not a technical one
  });
});

