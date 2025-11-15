export default {
  commitMsg: {
    enabled: true,
    checks: ['format', 'llm']  // Enable both format and LLM checks
  },
  preCommit: {
    enabled: true,
    checks: ['doc-bloat']  // doc-bloat enabled
    // Python quality checks available via config/rules/python-quality.mjs
    // Enable with: checks: ['doc-bloat', 'python-quality']
    // Note: python-quality requires custom integration in hookwise
  },
  prePush: {
    enabled: false,  // Can enable for comprehensive pre-push checks
    // Would include: secret scanning, full linting, type checking
  }
};
