export default {
  commitMsg: {
    enabled: true,
    checks: ['format', 'llm']  // Enable both format and LLM checks
  },
  preCommit: {
    enabled: true,
    checks: ['doc-bloat']  // Only doc-bloat, code-quality disabled for Python
  }
};
