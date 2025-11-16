/**
 * Hookwise Configuration for BOP (Python Research Project)
 * 
 * Customized for:
 * - Python project (not Node.js)
 * - Research/academic documentation
 * - Theoretical work requiring clear commit messages
 */
export default {
  commitMessage: {
    enabled: true,
    blocking: false,  // Start non-blocking to avoid friction
    tier: 'advanced', // Use advanced tier for better analysis
    minScore: 6,      // Raised from 5 - higher quality threshold
    timeout: 30000,   // 30s timeout for agentic mode
    agentic: true,    // Enable agentic loop with tool calling for thorough analysis
    // Enhanced checks
    requireScope: true,  // Require scope for feat/fix/refactor commits
    maxSubjectLength: 72, // Enforce conventional commit subject length
    checkCoherence: true, // Check if commit message matches changed files
  },
  documentation: {
    enabled: true,  // Re-enabled - helps steer toward clean documentation structure
    maxRootFiles: 10,  // Reduced after cleanup - root is now clean (8 markdown files)
    archivePatterns: [
      // Implementation/Summary patterns
      'FINAL_',
      'COMPLETE_',
      'IMPLEMENTATION_',
      'VALIDATION_',
      'INTEGRATION_',
      'SESSION_',
      '_SUMMARY.md',
      '_STATUS.md',
      '_REPORT.md',
      '_NOTES.md',
      '_RESULTS.md',
      // Analysis patterns
      'ANALYSIS_',
      'CRITICAL_',
      'DEEP_',
      'CRITIQUE_',
      'AMBIENT_',
      'EXECUTION_',
      '_ANALYSIS.md',
      '_REVIEW.md',
      '_CRITIQUE.md',
      '_DESIGN.md',
      '_RESEARCH_SYNTHESIS.md',
      // Planning/Recommendation patterns
      '_PLAN.md',
      '_RECOMMENDATIONS.md',
      '_IMPROVEMENTS.md',
      '_NEXT_STEPS.md',
      '_ENHANCEMENT.md',
      // Theory/Research patterns
      'TRUST_',
      'THEORY_',
      '_THEORY.md',
      '_RESEARCH.md',
      // Deployment/Setup patterns
      '_DEPLOY.md',
      '_SETUP.md',
      '_COMMANDS.md',
      '_DEPLOYMENT.md',
      // External analysis (should be in docs/archive/external-analysis/)
      'KUMORFM_',
      'DOCUMENTATION_HARMONIZATION',
    ],
    // Archive directories to check for learning patterns
    archiveDirs: [
      'docs/archive/',
      'docs/archive/external-analysis/',
      'docs/archive/analysis-docs/',
    ],
  },
  codeQuality: {
    enabled: false,  // Disable JS-specific checks (console.log, etc.)
    // Python quality checks are handled via config/rules/python-quality.mjs
    // and can be enabled in .hookwise.hooks.mjs if needed
  },
  // Additional BOP-specific settings
  bop: {
    // Research project allowances
    allowResearchDocs: true,  // Allow more documentation for research projects
    // Commit message enhancements
    requireScopeForTypes: ['feat', 'fix', 'refactor'],  // Require scope for major changes
    // Documentation organization
    coreDocs: [
      'README.md',
      'ARCHITECTURE.md',
      'AGENTS.md',
      'CONTRIBUTING.md',
      'CODE_STYLE.md',
    ],
    userGuides: [
      'KNOWLEDGE_DISPLAY_GUIDE.md',
      'TRUST_AND_UNCERTAINTY_USER_GUIDE.md',
      'MIGRATION_GUIDE.md',
      'DEPLOYMENT.md',
      'SEMANTIC_EVALUATION_GUIDE.md',
      'TESTING_AND_SECURITY_GUIDE.md',
    ],
  },
};

