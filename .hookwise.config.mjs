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
    minScore: 5,      // Reasonable threshold for research work
    timeout: 30000,   // 30s timeout for agentic mode
    agentic: true,    // Enable agentic loop with tool calling for thorough analysis
  },
  documentation: {
    enabled: false,  // Temporarily disabled to test agentic commit analysis
    maxRootFiles: 25,  // BOP is a research project with many docs - allow more
    archivePatterns: [
      'FINAL_',
      'COMPLETE_',
      'SESSION_',
      'ANALYSIS_',
      'CRITICAL_',
      'DEEP_',
      'EXECUTION_',
      'IMPLEMENTATION_',
      'VALIDATION_',
      'CRITIQUE_',
      'INTEGRATION_',
      'TRUST_',
      '_REVIEW.md',
      '_ANALYSIS.md',
      '_PLAN.md',
      '_SUMMARY.md',
      '_RECOMMENDATIONS.md',
      '_IMPROVEMENTS.md',
      '_STATUS.md',
      '_REPORT.md',
      '_DESIGN.md',
      '_THEORY.md',
      '_RESEARCH_SYNTHESIS.md',
    ],
  },
  codeQuality: {
    enabled: false,  // Disable JS-specific checks (console.log, etc.)
  },
};

