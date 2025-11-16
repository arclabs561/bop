#!/usr/bin/env node
/**
 * Python-specific code quality checks
 * Integrates with hookwise pre-commit hook
 */

import { execSync } from 'child_process';
import { readFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Import Python quality check functions
import { checkPythonQuality } from '../config/rules/python-quality.mjs';

// Get staged Python files
function getStagedFiles() {
  try {
    const output = execSync(
      ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACMR'],
      { encoding: 'utf8', cwd: process.cwd() }
    );
    return output.split('\n').filter(Boolean);
  } catch (error) {
    return [];
  }
}

// Main execution
async function main() {
  const stagedFiles = getStagedFiles();
  const pythonFiles = stagedFiles.filter(f => f.endsWith('.py'));
  
  if (pythonFiles.length === 0) {
    // No Python files staged, skip
    process.exit(0);
  }
  
  console.log(`🔍 Checking ${pythonFiles.length} Python file(s)...`);
  
  const result = await checkPythonQuality(stagedFiles);
  
  let hasErrors = false;
  let hasWarnings = false;
  
  // Report errors (blocking)
  if (result.errors.length > 0) {
    hasErrors = true;
    console.log('\n❌ Python quality errors (blocking):');
    result.errors.forEach(issue => {
      console.log(`   ${issue.file}:${issue.line}`);
      console.log(`   ${issue.issue}`);
      console.log(`   Code: ${issue.code}`);
      console.log('');
    });
  }
  
  // Report warnings (non-blocking)
  if (result.warnings.length > 0) {
    hasWarnings = true;
    console.log('\n⚠️  Python quality warnings (non-blocking):');
    result.warnings.forEach(issue => {
      console.log(`   ${issue.file}:${issue.line}`);
      console.log(`   ${issue.issue}`);
      console.log(`   Code: ${issue.code}`);
      console.log('');
    });
  }
  
  if (hasErrors) {
    console.log('💡 Fix errors before committing');
    process.exit(1);
  }
  
  if (hasWarnings) {
    console.log('💡 Consider addressing warnings');
    // Don't exit - warnings are non-blocking
  }
  
  if (!hasErrors && !hasWarnings) {
    console.log('✅ Python quality checks passed');
  }
  
  process.exit(0);
}

main().catch(error => {
  console.error('Error running Python quality checks:', error);
  process.exit(1);
});

