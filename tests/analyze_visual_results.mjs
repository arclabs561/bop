/**
 * Analyze Visual Test Results
 * Extracts insights from test runs and suggests improvements
 */

import { readFileSync, existsSync, readdirSync, statSync } from 'fs';
import { join } from 'path';

function analyzeTestResults() {
  const results = {
    testFiles: [],
    screenshots: [],
    issues: [],
    recommendations: [],
  };
  
  // Find test result files (simple recursive search)
  function findFiles(dir, ext) {
    const files = [];
    try {
      const entries = readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        const fullPath = join(dir, entry.name);
        if (entry.isDirectory()) {
          files.push(...findFiles(fullPath, ext));
        } else if (entry.name.endsWith(ext)) {
          files.push(fullPath);
        }
      }
    } catch (error) {
      // Directory doesn't exist or can't be read
    }
    return files;
  }
  
  const testResultFiles = existsSync('test-results') ? findFiles('test-results', '.json') : [];
  const screenshotFiles = existsSync('test-results') ? findFiles('test-results', '.png') : [];
  
  results.screenshots = screenshotFiles;
  
  // Analyze tracker if exists
  const trackerFile = 'test-results/visual-improvements-tracker.json';
  if (existsSync(trackerFile)) {
    try {
      const tracker = JSON.parse(readFileSync(trackerFile, 'utf-8'));
      results.improvements = tracker.improvements;
      results.metrics = tracker.metrics;
    } catch (error) {
      console.warn('Failed to load tracker:', error.message);
    }
  }
  
  // Generate recommendations
  if (results.improvements && results.improvements.length > 0) {
    const categories = {};
    results.improvements.forEach(imp => {
      if (!categories[imp.category]) {
        categories[imp.category] = [];
      }
      categories[imp.category].push(imp);
    });
    
    results.recommendations.push({
      type: 'category_analysis',
      message: `Improvements by category: ${Object.keys(categories).map(c => `${c} (${categories[c].length})`).join(', ')}`,
      categories,
    });
  }
  
  // Check for unvalidated improvements
  if (results.improvements) {
    const unvalidated = results.improvements.filter(i => !i.validated);
    if (unvalidated.length > 0) {
      results.recommendations.push({
        type: 'validation',
        message: `${unvalidated.length} improvements need validation`,
        improvements: unvalidated,
      });
    }
  }
  
  return results;
}

const results = analyzeTestResults();

console.log('\n📊 Visual Test Results Analysis');
console.log('='.repeat(60));
console.log(`\nScreenshots captured: ${results.screenshots.length}`);
console.log(`Improvements tracked: ${results.improvements?.length || 0}`);
console.log(`Recommendations: ${results.recommendations.length}`);

if (results.recommendations.length > 0) {
  console.log('\n💡 Recommendations:');
  results.recommendations.forEach((rec, idx) => {
    console.log(`\n${idx + 1}. ${rec.type.toUpperCase()}:`);
    console.log(`   ${rec.message}`);
  });
}

if (results.metrics) {
  console.log('\n📈 Metrics:');
  console.log(`   Total improvements: ${results.metrics.totalImprovements}`);
  console.log(`   Accessibility score: ${results.metrics.accessibilityScore}`);
  console.log(`   Loading state score: ${results.metrics.loadingStateScore}`);
  console.log(`   Contrast score: ${results.metrics.contrastScore}`);
}

export { analyzeTestResults };
