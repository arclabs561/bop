/**
 * Visual Improvement Tracker
 * Tracks improvements over time and generates reports
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';

const TRACKER_FILE = 'test-results/visual-improvements-tracker.json';

function loadTracker() {
  if (existsSync(TRACKER_FILE)) {
    try {
      return JSON.parse(readFileSync(TRACKER_FILE, 'utf-8'));
    } catch (error) {
      console.warn('Failed to load tracker, starting fresh');
    }
  }
  return {
    improvements: [],
    testRuns: [],
    metrics: {
      totalImprovements: 0,
      accessibilityScore: 0,
      loadingStateScore: 0,
      contrastScore: 0,
    },
  };
}

function saveTracker(tracker) {
  const dir = dirname(TRACKER_FILE);
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }
  writeFileSync(TRACKER_FILE, JSON.stringify(tracker, null, 2));
}

function recordImprovement(category, issue, fix, files) {
  const tracker = loadTracker();
  const improvement = {
    id: Date.now(),
    timestamp: new Date().toISOString(),
    category,
    issue,
    fix,
    files,
    validated: false,
  };
  
  tracker.improvements.push(improvement);
  tracker.metrics.totalImprovements++;
  saveTracker(tracker);
  
  return improvement;
}

function recordTestRun(suite, passed, failed, duration, issues) {
  const tracker = loadTracker();
  const run = {
    timestamp: new Date().toISOString(),
    suite,
    passed,
    failed,
    duration,
    issues,
  };
  
  tracker.testRuns.push(run);
  saveTracker(tracker);
  
  return run;
}

function generateReport() {
  const tracker = loadTracker();
  
  const report = {
    summary: {
      totalImprovements: tracker.metrics.totalImprovements,
      recentImprovements: tracker.improvements.slice(-10),
      testRunHistory: tracker.testRuns.slice(-5),
    },
    categories: {
      accessibility: tracker.improvements.filter(i => i.category === 'accessibility'),
      loading: tracker.improvements.filter(i => i.category === 'loading'),
      contrast: tracker.improvements.filter(i => i.category === 'contrast'),
      structure: tracker.improvements.filter(i => i.category === 'structure'),
    },
    trends: {
      improvementRate: tracker.improvements.length / Math.max(1, (Date.now() - (tracker.improvements[0]?.id || Date.now())) / (1000 * 60 * 60 * 24)),
      testPassRate: tracker.testRuns.length > 0 
        ? tracker.testRuns.reduce((sum, r) => sum + (r.passed / (r.passed + r.failed)), 0) / tracker.testRuns.length
        : 0,
    },
  };
  
  return report;
}

// Record current improvements
const improvements = [
  {
    category: 'accessibility',
    issue: 'Missing ARIA labels on interactive elements',
    fix: 'Added aria-label and aria-describedby to all interactive elements',
    files: ['templates/chat.html'],
  },
  {
    category: 'accessibility',
    issue: 'No screen reader support',
    fix: 'Added sr-only class and help text for screen readers',
    files: ['templates/chat.html', 'static/css/chat.css'],
  },
  {
    category: 'loading',
    issue: 'Loading indicator not accessible',
    fix: 'Added role, aria-live, aria-busy, and loading text',
    files: ['templates/chat.html', 'static/js/chat.js'],
  },
  {
    category: 'loading',
    issue: 'Loading state UX unclear',
    fix: 'Added loading text with dynamic content based on research state',
    files: ['static/js/chat.js', 'static/css/chat.css'],
  },
  {
    category: 'contrast',
    issue: 'Light mode accent color below WCAG AA (3.2:1)',
    fix: 'Changed accent from #10a37f to #0d8f6e for better contrast',
    files: ['static/css/chat.css'],
  },
  {
    category: 'structure',
    issue: 'Invalid HTML (span inside select)',
    fix: 'Moved schema-help span outside select element',
    files: ['templates/chat.html'],
  },
  {
    category: 'accessibility',
    issue: 'No visible focus indicators',
    fix: 'Added :focus-visible styles with outline and border-color',
    files: ['static/css/chat.css'],
  },
];

console.log('📊 Recording improvements...');
improvements.forEach(imp => {
  recordImprovement(imp.category, imp.issue, imp.fix, imp.files);
});

const report = generateReport();
console.log('\n📈 Improvement Report:');
console.log(`  Total improvements: ${report.summary.totalImprovements}`);
console.log(`  Categories: ${Object.keys(report.categories).join(', ')}`);
console.log(`  Recent: ${report.summary.recentImprovements.length} improvements`);

export { recordImprovement, recordTestRun, generateReport, loadTracker };
