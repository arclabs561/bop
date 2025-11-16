/**
 * Visual Test Runner with Continuous Improvement
 * 
 * Runs visual tests and generates actionable improvement reports
 */

import { execSync } from 'child_process';
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';

const TEST_SUITES = [
  'tests/test_e2e_visual.mjs',
  'tests/test_e2e_visual_enhanced.mjs',
  'tests/test_e2e_visual_regression.mjs',
];

const RESULTS_DIR = 'test-results/visual-improvements';

function ensureDir(dir) {
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }
}

function runTestSuite(suite) {
  console.log(`\n🧪 Running ${suite}...`);
  try {
    const output = execSync(
      `npx playwright test ${suite} --project=chromium --reporter=json`,
      { encoding: 'utf-8', stdio: 'pipe', timeout: 120000 }
    );
    return JSON.parse(output);
  } catch (error) {
    console.error(`❌ Test suite ${suite} failed:`, error.message);
    return null;
  }
}

function extractIssues(results) {
  const issues = [];
  
  if (!results || !results.suites) return issues;
  
  for (const suite of results.suites) {
    for (const spec of suite.specs || []) {
      for (const test of spec.tests || []) {
        if (test.status === 'failed' || test.status === 'skipped') {
          issues.push({
            test: test.title,
            status: test.status,
            errors: test.results?.map(r => r.error?.message).filter(Boolean) || [],
          });
        }
      }
    }
  }
  
  return issues;
}

function generateImprovementReport(allResults) {
  const timestamp = new Date().toISOString();
  const report = {
    timestamp,
    summary: {
      totalSuites: allResults.length,
      passedSuites: allResults.filter(r => r && r.status === 'passed').length,
      totalIssues: allResults.reduce((sum, r) => sum + extractIssues(r).length, 0),
    },
    suites: allResults.map((result, idx) => ({
      suite: TEST_SUITES[idx],
      status: result?.status || 'failed',
      issues: extractIssues(result),
    })),
    recommendations: [],
  };
  
  // Generate recommendations based on common issues
  const allIssues = report.suites.flatMap(s => s.issues);
  const errorMessages = allIssues.flatMap(i => i.errors).join(' ').toLowerCase();
  
  if (errorMessages.includes('aria') || errorMessages.includes('accessibility')) {
    report.recommendations.push({
      priority: 'high',
      category: 'accessibility',
      issue: 'Missing ARIA labels and accessibility features',
      fix: 'Add aria-label attributes to interactive elements, ensure keyboard navigation',
      files: ['templates/chat.html', 'static/js/chat.js'],
    });
  }
  
  if (errorMessages.includes('contrast') || errorMessages.includes('readability')) {
    report.recommendations.push({
      priority: 'high',
      category: 'design',
      issue: 'Color contrast may not meet WCAG standards',
      fix: 'Verify contrast ratios (≥4.5:1 for normal text, ≥3:1 for large text)',
      files: ['static/css/chat.css'],
    });
  }
  
  if (errorMessages.includes('loading') || errorMessages.includes('indicator')) {
    report.recommendations.push({
      priority: 'medium',
      category: 'ux',
      issue: 'Loading states need improvement',
      fix: 'Add clear loading indicators with better visibility and styling',
      files: ['templates/chat.html', 'static/js/chat.js', 'static/css/chat.css'],
    });
  }
  
  return report;
}

function main() {
  console.log('🚀 Starting Visual Test Runner with Continuous Improvement\n');
  
  ensureDir(RESULTS_DIR);
  
  const allResults = TEST_SUITES.map(runTestSuite);
  const report = generateImprovementReport(allResults);
  
  const reportPath = join(RESULTS_DIR, `improvement-report-${Date.now()}.json`);
  writeFileSync(reportPath, JSON.stringify(report, null, 2));
  
  console.log('\n📊 Test Summary:');
  console.log(`  Total suites: ${report.summary.totalSuites}`);
  console.log(`  Passed: ${report.summary.passedSuites}`);
  console.log(`  Issues found: ${report.summary.totalIssues}`);
  
  if (report.recommendations.length > 0) {
    console.log('\n💡 Recommendations:');
    report.recommendations.forEach((rec, idx) => {
      console.log(`  ${idx + 1}. [${rec.priority.toUpperCase()}] ${rec.category}: ${rec.issue}`);
      console.log(`     Fix: ${rec.fix}`);
      console.log(`     Files: ${rec.files.join(', ')}`);
    });
  }
  
  console.log(`\n📄 Full report saved to: ${reportPath}`);
  
  return report;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export { main, runTestSuite, extractIssues, generateImprovementReport };
