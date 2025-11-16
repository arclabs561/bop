/**
 * Python-specific code quality rules for BOP
 * 
 * Complements hookwise's JS-focused checks with Python patterns.
 */

import { readFileSync, existsSync } from 'fs';
import { join } from 'path';
import { execSync } from 'child_process';

// Find repo root (git rev-parse --show-toplevel)
function findRepoRoot() {
  try {
    const output = execSync(['git', 'rev-parse', '--show-toplevel'], {
      encoding: 'utf8',
      cwd: process.cwd()
    });
    return output.trim();
  } catch (error) {
    return process.cwd();
  }
}

const REPO_ROOT = findRepoRoot();

/**
 * Check for print statements (Python equivalent of console.log)
 */
export function checkPrintStatements(files) {
  const issues = [];
  const pythonFiles = files.filter(f => f.endsWith('.py') && !f.includes('node_modules'));
  
  for (const file of pythonFiles) {
    try {
      const filePath = join(REPO_ROOT, file);
      if (!existsSync(filePath)) continue;
      
      const content = readFileSync(filePath, 'utf8');
      const lines = content.split('\n');
      
      lines.forEach((line, index) => {
        // Check for print() statements (but allow in test files and __main__ blocks)
        if (line.includes('print(') && !line.trim().startsWith('#') && !line.trim().startsWith('"""')) {
          const isTestFile = file.includes('test_') || file.includes('/test');
          const isMainBlock = content.includes('if __name__') && content.indexOf('if __name__') < content.indexOf(line);
          
          if (!isTestFile && !isMainBlock) {
            issues.push({
              file,
              line: index + 1,
              issue: 'print() statement found - consider using logging or removing for production',
              code: line.trim().substring(0, 80),
              severity: 'warning'
            });
          }
        }
      });
    } catch (error) {
      // Skip files that can't be read
    }
  }
  
  return issues;
}

/**
 * Check for TODO/FIXME without context (Python-specific)
 */
export function checkTODOs(files) {
  const issues = [];
  const pythonFiles = files.filter(f => f.endsWith('.py') && !f.includes('node_modules'));
  
  for (const file of pythonFiles) {
    try {
      const filePath = join(REPO_ROOT, file);
      if (!existsSync(filePath)) continue;
      
      const content = readFileSync(filePath, 'utf8');
      const lines = content.split('\n');
      
      lines.forEach((line, index) => {
        const upperLine = line.toUpperCase();
        if ((upperLine.includes('TODO') || upperLine.includes('FIXME') || upperLine.includes('XXX') || upperLine.includes('HACK')) &&
            !line.trim().startsWith('#') &&
            !line.trim().startsWith('"""')) {
          const match = line.match(/(TODO|FIXME|XXX|HACK):?\s*:?\s*(.+)/i);
          const context = match ? match[2].trim() : '';
          
          // If TODO/FIXME has minimal context (less than 10 chars), flag it
          if (context.length < 10) {
            issues.push({
              file,
              line: index + 1,
              issue: 'TODO/FIXME/XXX/HACK without sufficient context - add description or issue reference',
              code: line.trim().substring(0, 80),
              severity: 'warning'
            });
          }
        }
      });
    } catch (error) {
      // Skip files that can't be read
    }
  }
  
  return issues;
}

/**
 * Check for test anti-patterns (Python-specific)
 */
export function checkTestPatterns(files) {
  const issues = [];
  const testFiles = files.filter(f => 
    (f.includes('test_') || f.includes('/test') || f.includes('tests/')) &&
    f.endsWith('.py') &&
    !f.includes('node_modules')
  );
  
  for (const file of testFiles) {
    try {
      const filePath = join(REPO_ROOT, file);
      if (!existsSync(filePath)) continue;
      
      const content = readFileSync(filePath, 'utf8');
      const lines = content.split('\n');
      
      lines.forEach((line, index) => {
        // Check for pytest.skip() without reason
        if (line.includes('pytest.skip()') && !line.includes('reason=') && !line.trim().startsWith('#')) {
          issues.push({
            file,
            line: index + 1,
            issue: 'pytest.skip() without reason - add reason parameter',
            code: line.trim().substring(0, 80),
            severity: 'error'
          });
        }
        
        // Check for time.sleep() in tests (anti-pattern)
        if (line.includes('time.sleep(') && !line.trim().startsWith('#')) {
          issues.push({
            file,
            line: index + 1,
            issue: 'time.sleep() in test - use proper async/await or test utilities instead',
            code: line.trim().substring(0, 80),
            severity: 'warning'
          });
        }
        
        // Check for bare except (bad practice)
        if (line.match(/^\s*except\s*:/) && !line.trim().startsWith('#')) {
          issues.push({
            file,
            line: index + 1,
            issue: 'Bare except clause - specify exception type',
            code: line.trim().substring(0, 80),
            severity: 'warning'
          });
        }
      });
    } catch (error) {
      // Skip files that can't be read
    }
  }
  
  return issues;
}

/**
 * Main Python quality check function
 */
export async function checkPythonQuality(stagedFiles) {
  const allIssues = {
    printStatements: checkPrintStatements(stagedFiles),
    todos: checkTODOs(stagedFiles),
    testPatterns: checkTestPatterns(stagedFiles)
  };
  
  const errors = [
    ...allIssues.testPatterns.filter(i => i.severity === 'error')
  ];
  
  const warnings = [
    ...allIssues.printStatements,
    ...allIssues.todos,
    ...allIssues.testPatterns.filter(i => i.severity === 'warning')
  ];
  
  return { errors, warnings };
}

