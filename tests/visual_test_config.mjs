/**
 * Visual Testing Configuration
 * 
 * Centralized configuration for visual tests with environment-based overrides
 */

// Default configuration
const defaultConfig = {
  // Server
  serverUrl: process.env.BOP_SERVER_URL || 'http://localhost:8000',
  serverTimeout: 30000,
  serverMaxRetries: 10,
  
  // VLLM
  vllmProvider: process.env.VLM_PROVIDER || 'gemini',
  vllmCacheEnabled: true,
  vllmVerbose: process.env.DEBUG_VLLM === 'true',
  
  // Test execution
  testTimeout: 60000,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : 2,
  
  // Output filtering
  maxIssues: 5,
  maxIssueLength: 100,
  verboseOutput: process.env.VISUAL_TEST_VERBOSE === 'true',
  
  // Cost tracking
  trackCosts: true,
  costWarningThreshold: 1.0, // Warn if cost exceeds $1.00
  
  // Score thresholds
  minScoreAcceptable: 7,
  minScoreWarning: 5,
  
  // Screenshot settings
  screenshotDir: 'test-results',
  screenshotOnFailure: true,
  videoOnFailure: true,
  traceOnFailure: true,
};

// Environment-specific overrides
const envConfig = {
  development: {
    workers: 2,
    retries: 0,
    verboseOutput: true,
  },
  ci: {
    workers: 1,
    retries: 2,
    verboseOutput: false,
    trackCosts: true,
  },
  production: {
    workers: 1,
    retries: 1,
    verboseOutput: false,
    trackCosts: true,
    costWarningThreshold: 0.5,
  },
};

/**
 * Get configuration for current environment
 */
export function getConfig() {
  const env = process.env.NODE_ENV || 'development';
  const envOverrides = envConfig[env] || envConfig.development;
  
  return {
    ...defaultConfig,
    ...envOverrides,
    env,
  };
}

/**
 * Get Playwright configuration
 */
export function getPlaywrightConfig() {
  const config = getConfig();
  
  return {
    timeout: config.testTimeout,
    retries: config.retries,
    workers: config.workers,
    reporter: [
      ['list'],
      ['html', { outputFolder: `${config.screenshotDir}/playwright-report` }],
      ...(config.verboseOutput ? [['json', { outputFile: `${config.screenshotDir}/results.json` }]] : []),
    ],
    use: {
      baseURL: config.serverUrl,
      screenshot: config.screenshotOnFailure ? 'only-on-failure' : 'off',
      video: config.videoOnFailure ? 'retain-on-failure' : 'off',
      trace: config.traceOnFailure ? 'retain-on-failure' : 'off',
    },
  };
}

export default getConfig();

