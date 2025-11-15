# Guarded Configuration - Complete Implementation

## Steering Perspective

The hooks and guards in this project serve as **steering mechanisms** - they provide feedback that guides behavior toward a desired fixed point. When the Cursor agent (or any developer) makes commits or changes, the text output from hooks acts as corrective signals that shape the work toward:

- **Code Quality**: Clean, linted, type-checked code
- **Documentation**: Well-organized, non-bloated documentation
- **Security**: No exposed secrets, secure practices
- **Deployment**: Valid, consistent deployment configuration
- **Commit Messages**: Clear, conventional, research-focused messages

## ✅ Complete Implementation

### 1. Enhanced .env Loading
- **Location**: `.husky/commit-msg`, `.husky/pre-commit`
- **Features**:
  - Finds repo root (works from subdirectories)
  - Handles quoted values
  - Skips comments and empty lines
  - Fallback for different shells
- **Purpose**: Ensures LLM API keys are available for hookwise

### 2. Documentation Bloat Detection
- **Status**: ✅ Re-enabled
- **Configuration**: `.hookwise.config.mjs`
- **Steering**: Guides toward clean documentation structure
- **Features**:
  - Max 25 root markdown files (research project allowance)
  - Archive pattern detection
  - Temporal learning from `archive/` directory

### 3. Custom Commit Message Prompt
- **Location**: `config/prompts/commit-message.mjs`
- **Steering**: Guides commits toward research-focused, clear messages
- **Features**:
  - BOP-specific context (research, theory, agents, MCP tools)
  - Conventional commits format
  - Quality scoring with BOP considerations
  - Research clarity emphasis

### 4. Custom Commit Rules
- **Location**: `config/rules/conventional-commits.mjs`
- **Steering**: Guides toward BOP-specific commit types
- **Features**:
  - Standard types: feat, fix, docs, etc.
  - BOP-specific types: research, theory, analysis, agent, mcp
  - WIP commit support
  - Subject length validation

### 5. Configuration Validation
- **Location**: `.husky/pre-commit`
- **Steering**: Ensures hookwise config is valid
- **Command**: `npx hookwise validate-config`

### 6. Deployment Config Validation
- **Location**: `scripts/validate_deployment_config.py`
- **Hook**: `.husky/pre-push`
- **Steering**: Guides toward correct deployment setup
- **Checks**:
  - `fly.toml` structure and required fields
  - `Dockerfile` structure and health checks
  - Deployment scripts existence and executability

### 7. Secret Scanning
- **Location**: `scripts/scan_secrets.py`
- **Hook**: `.husky/pre-push`
- **Steering**: Guides toward secure code practices
- **Checks**:
  - Hardcoded API keys
  - Exposed secrets
  - Common secret patterns
  - Ignores .env files (expected to have secrets)

### 8. Hook Testing Script
- **Location**: `scripts/test_hooks.sh`
- **Purpose**: Test all hooks and hookwise functionality
- **Tests**:
  - Config validation
  - Commit message validation
  - Documentation checks
  - Garden mode
  - Q&A system (if API keys available)
  - Metrics and recommendations

## Complete Guard Flow

### Pre-Commit (Fast Steering)
```
1. Load .env (for LLM API keys)
2. Validate hookwise config
3. Run hookwise checks (doc bloat, code quality)
4. Lint staged Python files (ruff)
5. Auto-fix and re-stage
```

**Steering Signals**:
- "📝 Linting staged Python files..."
- "❌ Linting failed. Run 'just lint-fix' to fix issues"
- Documentation bloat warnings
- Config validation errors

### Pre-Push (Comprehensive Steering)
```
1. Validate deployment configuration
2. Scan for secrets
3. Lint all code (ruff)
4. Type check (mypy, optional)
5. Run fast unit tests (pytest)
```

**Steering Signals**:
- "🔍 Validating deployment configuration..."
- "🔒 Scanning for potential secrets..."
- "📝 Checking code quality (ruff)..."
- "🔍 Running type checks (mypy)..."
- "🧪 Running fast tests (pytest via uv)..."
- "❌ Tests failed. Fix issues before pushing"

### Commit Message (Quality Steering)
```
1. Load .env (for LLM API keys)
2. Validate format (conventional commits)
3. LLM analysis with agentic tools (if enabled)
4. Score and provide suggestions
```

**Steering Signals**:
- Format validation errors
- LLM quality score and suggestions
- Improved message suggestions
- Research context recommendations

## API Keys Available

All required API keys are in `.env`:
- ✅ `OPENAI_API_KEY` - For hookwise LLM operations
- ✅ `ANTHROPIC_API_KEY` - For hookwise LLM operations
- ✅ `GEMINI_API_KEY` - For hookwise LLM operations
- ✅ Plus MCP tool keys (Perplexity, Firecrawl, Tavily, etc.)

## Testing

Run comprehensive hook testing:
```bash
./scripts/test_hooks.sh
```

This tests:
- Configuration validation
- Commit message validation
- Documentation checks
- Garden mode
- Q&A system (requires API keys in environment)
- Metrics
- Recommendations
- Hook scripts directly

**Note**: For direct CLI usage (e.g., `npx hookwise ask`), ensure API keys are in your environment:
```bash
# Load .env first
export $(grep -v '^#' .env | grep -v '^$' | xargs)
npx hookwise ask "question"
```

The hooks automatically load `.env`, so they work without manual export.

## Steering in Action

### Example 1: Poor Commit Message
```
Input: "fix stuff"
Steering: "Must follow format: type(scope): subject"
Result: Developer fixes to "fix(agent): handle API errors"
```

### Example 2: Hardcoded Secret
```
Input: Code with `api_key = "sk-123..."`
Steering: "⚠️ Found potential secret: API key pattern"
Result: Developer moves to environment variable
```

### Example 3: Documentation Bloat
```
Input: 30 markdown files in root
Steering: "Too many markdown files (30, max 25)"
Result: Developer archives 5 files to archive/analysis-docs/
```

### Example 4: Deployment Config Error
```
Input: Missing health check in fly.toml
Steering: "⚠️ No /health endpoint check found"
Result: Developer adds health check configuration
```

## Fixed Points (Desired States)

The guards steer toward these fixed points:

1. **Code Quality Fixed Point**:
   - All code linted (ruff)
   - Type-checked (mypy)
   - Tests passing
   - No hardcoded secrets

2. **Documentation Fixed Point**:
   - ≤25 root markdown files
   - Temporary docs archived
   - Clear organization

3. **Deployment Fixed Point**:
   - Valid fly.toml
   - Valid Dockerfile
   - Health checks configured
   - Scripts executable

4. **Commit Message Fixed Point**:
   - Conventional commits format
   - Research-focused clarity
   - Quality score ≥5
   - BOP-specific context

5. **Security Fixed Point**:
   - No hardcoded secrets
   - Environment variables used
   - .env.example documented

## Continuous Steering

The guards provide **continuous steering** - not just blocking, but guiding:

- **Non-blocking warnings**: Inform without stopping work
- **Actionable feedback**: Tell what to fix and how
- **Progressive enhancement**: Start lenient, tighten over time
- **Adaptive thresholds**: Adjust based on team performance
- **Context-aware**: BOP-specific guidance

## Next Steps

1. **Monitor Metrics**: `npx hookwise metrics`
2. **Get Recommendations**: `npx hookwise recommend`
3. **Test Q&A**: `npx hookwise ask "question"`
4. **Run Tests**: `./scripts/test_hooks.sh`
5. **Review Steering**: Observe how hooks guide behavior

The system is now fully configured to steer development toward quality, security, and proper practices.

