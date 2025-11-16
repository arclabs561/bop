/**
 * Playwright configuration for visual E2E tests
 */

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  testMatch: [
    '**/test_e2e_visual*.mjs', 
    '**/validate_improvements.mjs', 
    '**/quick_visual_test.mjs',
    '**/test_visual_comprehensive.mjs',
    '**/accessibility_audit.mjs',
    '**/skeptical_audit.mjs',
    '**/real_world_validation.mjs',
  ],
  
  // Timeout for each test
  timeout: 60000,
  
  // Retry failed tests
  retries: process.env.CI ? 2 : 0,
  
  // Parallel execution (can be overridden with --workers flag)
  workers: process.env.CI ? 1 : process.env.VISUAL_TEST_WORKERS ? parseInt(process.env.VISUAL_TEST_WORKERS) : 2,
  
  // Reporter configuration
  reporter: [
    ['list'],
    ['html', { outputFolder: 'test-results/playwright-report' }],
  ],
  
  // Shared settings for all projects
  use: {
    // Base URL for tests
    baseURL: process.env.BOP_SERVER_URL || 'http://localhost:8000',
    
    // Screenshot on failure
    screenshot: 'only-on-failure',
    
    // Video on failure
    video: 'retain-on-failure',
    
    // Trace on failure
    trace: 'retain-on-failure',
  },
  
  // Projects for different browsers
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],
  
  // Web server configuration (optional - can start server here)
  // webServer: {
  //   command: 'uv run bop serve',
  //   url: 'http://localhost:8000/health',
  //   reuseExistingServer: !process.env.CI,
  // },
});

