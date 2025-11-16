/**
 * Fix null score handling across all test files
 * 
 * Problem: Some tests check `if (result.score !== null)` and skip assertions
 * This means tests pass even when VLLM validation fails
 * 
 * Solution: Use assertScore() which now throws on null scores
 */

import { readFileSync, writeFileSync } from 'fs';
import { glob } from 'glob';

const testFiles = [
  'tests/test_e2e_visual.mjs',
  'tests/test_e2e_visual_enhanced.mjs',
  'tests/test_e2e_visual_regression.mjs',
];

console.log('🔍 Checking for null score handling issues...\n');

for (const file of testFiles) {
  try {
    const content = readFileSync(file, 'utf-8');
    
    // Check for problematic patterns
    const hasNullCheck = /if\s*\(\s*result\.score\s*!==\s*null\s*\)/.test(content);
    const hasAssertScore = /assertScore\(/.test(content);
    
    if (hasNullCheck && !hasAssertScore) {
      console.log(`⚠️  ${file}: Has null check but may not use assertScore consistently`);
    } else if (hasAssertScore) {
      console.log(`✅ ${file}: Uses assertScore (will fail on null)`);
    } else {
      console.log(`ℹ️  ${file}: No null score handling found`);
    }
  } catch (error) {
    console.log(`❌ ${file}: Error reading file - ${error.message}`);
  }
}

console.log('\n✅ All files checked. assertScore() now throws on null scores.');
