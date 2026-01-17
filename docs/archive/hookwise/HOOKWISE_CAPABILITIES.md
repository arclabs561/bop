# Hookwise Capabilities Overview

Comprehensive guide to what Hookwise can do, based on documentation review.

## Core Features

### 1. Commit Message Validation

**What it does**:
- Validates commit messages follow Conventional Commits format
- Optional LLM-powered quality scoring (0-10 scale)
- Provides suggestions for improvement
- **Agentic mode**: LLM can use tools to investigate commits thoroughly

**Configuration**:
```javascript
{
  commitMessage: {
    enabled: true,
    blocking: false,  // Warn vs. block
    tier: 'advanced', // 'simple' or 'advanced'
    minScore: 5,      // Minimum LLM score (0-10)
    timeout: 30000,   // Timeout in ms
    agentic: true,    // Enable tool-calling agentic loop
  }
}
```

**Agentic Tools Available**:
- `read_staged_file` - Read specific staged file
- `read_staged_files` - Read multiple staged files (with pattern filtering)
- `git_diff` - Get diff of staged changes
- `git_log` - Get recent commit history
- `ast_grep_scan` - Scan code for patterns (requires ast-grep)
- `analyze_file_structure` - Analyze code structure
- `count_lines` - Count LOC, comments, blank lines

**Performance**:
- Format validation: <100ms (cached: <50ms)
- LLM analysis: 1-2s (first time), <50ms (cached)
- Agentic mode: 5-30s (depending on tool calls)

### 2. Code Quality Checks

**What it checks**:
- `console.log()` usage (warning, non-blocking)
- TODO/FIXME without context (warning)
- Test anti-patterns (blocking):
  - `waitForTimeout()` usage
  - `test.skip()` without reason

**Configuration**:
```javascript
{
  codeQuality: {
    enabled: true,  // Enable/disable checks
  }
}
```

**Note**: Currently JavaScript-focused. Can be disabled for Python projects.

### 3. Documentation Bloat Detection

**What it detects**:
- Too many markdown files in root directory
- Temporary analysis documents (FINAL_*, COMPLETE_*, etc.)
- Old files (>30 days, >90 days)
- Similar/redundant content (optional LLM analysis)
- Archive pattern matching (learns from `archive/` directory)

**Configuration**:
```javascript
{
  documentation: {
    enabled: true,
    maxRootFiles: 25,  // Mbopmum markdown files in root
    archivePatterns: [
      'FINAL_', 'COMPLETE_', 'SESSION_', 'ANALYSIS_',
      '_REVIEW.md', '_ANALYSIS.md', '_PLAN.md',
      // ... more patterns
    ],
  }
}
```

**Temporal Learning**:
- Scans `archive/analysis-docs/` directory
- Extracts patterns (prefixes, suffixes, keywords)
- Counts pattern frequency
- Uses frequency to score confidence
- Applies learned patterns to new files

### 4. Garden Mode (Adhoc Validation)

**What it is**: Run all enabled checks without committing

**Usage**:
```bash
npx hookwise garden
```

**Why use it**:
- Test before committing (no need to create a commit)
- CI/CD integration (run in pipelines)
- IDE integration (trigger on save)
- Development-time validation

**What it checks**:
- Code quality (console.log, TODOs, test patterns)
- Documentation bloat
- Commit message format (if testing with `test-commit`)

### 5. Metrics and Analytics

**What it tracks**:
- **Performance**: Execution times, cache hit rates, pass/fail rates
- **Quality**: Commit message scores, validation rates, issue counts
- **Behavior**: Success rates, bypass rates, fix times
- **Health**: Cache utilization, error rates, timeouts

**Commands**:
```bash
# View metrics summary
npx hookwise metrics

# Export metrics for analysis
npx hookwise export-metrics > metrics.json

# Get recommended configuration adjustments
npx hookwise recommend
```

**Adaptive Features**:
- Adjusts `minScore` based on historical performance
- Recommends configuration changes based on metrics
- Tracks bypass rates to suggest non-blocking mode

### 6. Q&A System

**What it does**: Ask questions about your repository

**Usage**:
```bash
npx hookwise ask "What are the main components of this codebase?"
npx hookwise ask "How does authentication work?"
```

**Requirements**: LLM API key (GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY)

## Customization

### Custom Prompts

Create `config/prompts/commit-message.mjs`:
```javascript
export const COMMIT_MESSAGE_PROMPT = `You are analyzing a commit message for a security-focused project.

Commit message: "{{message}}"
Staged files: {{stagedFiles}}

Focus on:
1. Security implications of changes
2. Whether sensitive data might be exposed
3. If the message clearly describes security-related changes

Return JSON: { "score": 0-10, "issues": [...], "suggestions": [...] }`;

export function formatCommitMessagePrompt(data) {
  return COMMIT_MESSAGE_PROMPT
    .replace('{{message}}', data.message)
    .replace('{{stagedFiles}}', data.stagedFiles.join('\n'));
}
```

### Custom Rules

Create `config/rules/conventional-commits.mjs`:
```javascript
export const CONVENTIONAL_TYPES = [
  'feat', 'fix', 'docs', 'style', 'refactor',
  'perf', 'test', 'chore', 'security', 'hotfix'
];

export function validateFormat(message) {
  // Custom validation logic
  if (!message || message.trim().length === 0) {
    return { valid: false, error: 'Commit message cannot be empty' };
  }
  
  const typeMatch = message.match(/^(\w+)(?:\(([^)]+)\))?:/);
  if (!typeMatch) {
    return { valid: false, error: 'Must follow format: type(scope): subject' };
  }
  
  const type = typeMatch[1];
  if (!CONVENTIONAL_TYPES.includes(type)) {
    return { 
      valid: false, 
      error: `Type must be one of: ${CONVENTIONAL_TYPES.join(', ')}` 
    };
  }
  
  return { valid: true };
}
```

### Control Which Checks Run

Create `.hookwise.hooks.mjs`:
```javascript
export default {
  commitMsg: {
    enabled: true,
    checks: ['format', 'llm']  // Enable both format and LLM checks
  },
  preCommit: {
    enabled: true,
    checks: ['code-quality', 'doc-bloat']  // Enable both checks
  }
};
```

## Configuration Priority

Hookwise loads configuration in this order (later overrides earlier):

1. **Environment variables** (highest priority)
   ```bash
   HOOKWISE_COMMIT_MESSAGE_ENABLED=false
   HOOKWISE_COMMIT_MESSAGE_MIN_SCORE=7
   ```

2. **Repository config** (`.hookwise.config.mjs`)
   ```javascript
   export default {
     commitMessage: { enabled: true, minScore: 7 }
   };
   ```

3. **Global config** (`~/.hookwise.config.mjs` or git config)
   ```javascript
   export default {
     commitMessage: { blocking: false }  // Personal default
   };
   ```

4. **Defaults** (lowest priority)

## CLI Commands

### Installation & Setup
```bash
# Install hooks
npx hookwise install

# Validate configuration
npx hookwise validate-config

# Show current configuration
npx hookwise config
```

### Testing
```bash
# Test commit message
npx hookwise test-commit "feat: add new feature"

# Test documentation bloat
npx hookwise test-docs

# Test code quality
npx hookwise test-quality

# Run all checks (garden mode)
npx hookwise garden
```

### Analytics
```bash
# View metrics summary
npx hookwise metrics

# Export metrics
npx hookwise export-metrics > metrics.json

# Get recommendations
npx hookwise recommend
```

### Q&A
```bash
# Ask questions about repository
npx hookwise ask "What are the main components?"
npx hookwise ask "How does authentication work?"
```

## Architecture Features

### Fast Interaction Design
- **Fast path**: Format validation first (<100ms)
- **Slow path**: LLM analysis only if format valid
- **Caching**: Results cached 10 minutes (LLM), 1-60s (git commands)
- **Timeout protection**: Prevents hanging (default 10s, 30s for agentic)
- **Graceful degradation**: If LLM fails, format validation still passes

### Temporal Learning
- **Archive pattern learning**: Learns from `archive/` directory
- **Recent commit history**: Uses last 5 commits for context
- **Metrics aggregation**: Tracks up to 1000 events
- **Adaptive thresholds**: Adjusts based on historical performance

### Human Alignment
- **Bypass rate tracking**: If humans bypass often, recommend non-blocking
- **Pass rate tracking**: If humans pass easily, can raise standards
- **Recommendations**: System suggests, human decides
- **Configurable**: Humans can customize everything

### Security
- **Path traversal protection**: Validates all file paths
- **Symlink detection**: Prevents symlink attacks
- **File size limits**: Commit messages (10KB), config files (1MB), content (5MB)
- **Error sanitization**: Removes sensitive information from errors
- **Safe command execution**: Uses array form for execSync (prevents injection)

## Performance Characteristics

### Pre-Commit (Fast)
- Hookwise doc-bloat: ~100ms
- Code quality checks: ~200-500ms
- **Total**: <1 second

### Commit Message (Fast)
- Format validation: <100ms (cached: <50ms)
- LLM analysis: 1-2s (first time), <50ms (cached)
- Agentic mode: 5-30s (depending on tool calls)
- **Total**: <2s (simple), 5-30s (agentic)

### Caching Strategy
- **Git commands**: Short TTL (1-60s) - data changes frequently
- **LLM analysis**: Long TTL (10min) - idempotent, expensive
- **LRU eviction**: Prevents memory leaks (max 100 entries)

## Integration Points

### Git Hooks
- `commit-msg` - Commit message validation
- `pre-commit` - Code quality and documentation checks

### CI/CD
- Run `npx hookwise garden` in pipelines
- Export metrics for analysis
- Validate commits before merging

### IDE Integration
- Call `npx hookwise garden` on save
- Trigger specific hooks (e.g., `commitMsgHook`)
- Use Hookwise API directly

### External Tools
- Can call external tools from custom rules
- Supports any tool that can be executed via Node.js
- Example: Call eslint, pylint, etc. from rules

## Limitations

### Current Limitations
1. **JavaScript-only**: Requires Node.js/ES modules (but can call external tools)
2. **No explicit batching**: Files processed sequentially (can be parallelized)
3. **Shallow temporal analysis**: Only last 5 commits, archive patterns
4. **No explicit feedback loops**: Doesn't learn from human corrections
5. **Limited Python support**: Code quality checks are JS-focused

### Workarounds
- **Multi-language**: Call external tools (eslint, pylint, etc.) from rules
- **Batching**: Can be added via custom rules
- **Feedback**: Can be added via metrics and recommendations
- **Python**: Disable code quality checks, use external tools

## Best Practices

### Configuration
1. **Start non-blocking**: Set `blocking: false` initially
2. **Use appropriate tier**: `simple` for speed, `advanced` for thoroughness
3. **Set reasonable timeouts**: 10s for simple, 30s for agentic
4. **Customize for your project**: Adjust `maxRootFiles`, `archivePatterns`

### Usage
1. **Use garden mode**: Test before committing
2. **Monitor metrics**: Check `npx hookwise metrics` regularly
3. **Follow recommendations**: Use `npx hookwise recommend`
4. **Customize prompts**: Tailor LLM analysis to your project

### Performance
1. **Use caching**: Results are cached automatically
2. **Skip when needed**: Use `HOOKWISE_SKIP=true` for emergency commits
3. **Optimize timeouts**: Adjust based on your LLM provider speed
4. **Monitor performance**: Track execution times via metrics

## Future Enhancements

### Planned Features
1. **Plugin System**: Allow custom checks
2. **TypeScript Support**: Better type safety
3. **Performance Monitoring**: Track hook execution times
4. **More Checks**: Additional code quality patterns
5. **CI/CD Integration**: Native GitHub Actions, GitLab CI support

### Potential Features
1. **Deep Temporal Analysis**: Trend detection, pattern clustering
2. **Explicit Batching**: Parallel file processing, batch LLM calls
3. **Human Feedback Loops**: Learn from human corrections
4. **Semantic Analysis**: Understand meaning, not just syntax
5. **Rule Marketplace**: Share rules across projects

## Summary

Hookwise is a comprehensive git hooks system that provides:

✅ **Commit Message Validation**: Format + LLM quality scoring with agentic tool-calling
✅ **Code Quality Checks**: Static analysis for common issues
✅ **Documentation Management**: Bloat detection with temporal learning
✅ **Garden Mode**: Adhoc validation without committing
✅ **Metrics & Analytics**: Track performance, quality, behavior, health
✅ **Adaptive System**: Self-tuning based on metrics
✅ **Extensive Customization**: Prompts, rules, configuration
✅ **Fast Performance**: Caching, timeouts, graceful degradation
✅ **Security**: Path validation, symlink detection, error sanitization

**Best for**: JavaScript/TypeScript projects wanting structured validation with LLM-powered analysis and extensive customization options.

