# Hookwise Integration Guide for BOP

Complete guide to hookwise integration, customization, and usage in the BOP project.

## Overview

Hookwise provides intelligent git hooks that steer development toward quality, security, and proper practices. This guide covers BOP-specific configuration and usage.

## Capabilities Harmonization

### ✅ Fully Integrated

1. **Commit Message Validation**
   - ✅ Format validation (conventional commits)
   - ✅ LLM quality scoring (0-10 scale)
   - ✅ Agentic mode enabled (tool-calling for thorough analysis)
   - ✅ Custom BOP-specific prompt
   - ✅ Custom BOP-specific rules (research, theory, agent, mcp types)

2. **Documentation Bloat Detection**
   - ✅ Enabled and configured
   - ✅ Max 25 root files (research project allowance)
   - ✅ Archive pattern learning
   - ✅ Temporal learning from `archive/` directory

3. **Custom Prompts & Rules**
   - ✅ BOP-specific commit message prompt
   - ✅ BOP-specific commit types
   - ✅ Python-specific quality checks

4. **Configuration Management**
   - ✅ Multi-level config (env → repo → global → defaults)
   - ✅ Config validation in pre-commit
   - ✅ .env loading in all hooks

### ⚠️ Partially Integrated

1. **Code Quality Checks**
   - ✅ Python-specific checks (print, TODO, test patterns)
   - ⚠️ Hookwise's JS checks disabled (Python project)
   - ✅ Ruff linting (via pre-commit/pre-push)

2. **Metrics & Analytics**
   - ✅ Available via `npx hookwise metrics`
   - ⚠️ Not automatically reviewed
   - ✅ Recommendations available

3. **Q&A System**
   - ✅ API keys available in .env
   - ⚠️ Requires manual export for CLI usage
   - ✅ Works automatically in hooks (load .env)

### 💡 Future Enhancements

1. **CI/CD Integration**
   - ✅ GitHub Actions workflow created
   - ⚠️ Not yet active (needs testing)

2. **IDE Integration**
   - 💡 Could add on-save validation
   - 💡 Could add Cursor/VSCode extension

3. **Advanced Agentic Tools**
   - 💡 Python AST analysis
   - 💡 Import dependency checking
   - 💡 Test coverage checking

## BOP-Specific Configuration

### Commit Message Types

BOP extends conventional commits with research-focused types:

**Standard Types**:
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `refactor` - Code refactoring
- `test` - Tests
- `chore` - Maintenance

**BOP-Specific Types**:
- `research` - Research work, theoretical exploration
- `theory` - Theoretical contributions
- `analysis` - Analysis or evaluation
- `agent` - Agent-related changes
- `mcp` - MCP tool integration

**Examples**:
```
research: explore d-separation in context topology
theory(agent): add belief-evidence alignment framework
analysis(orchestrator): evaluate tool selection strategies
agent: improve KnowledgeAgent response tiers
mcp(perplexity): integrate deep research tool
```

### Custom Commit Message Prompt

The BOP-specific prompt (`config/prompts/commit-message.mjs`) emphasizes:
- Research clarity and theoretical contribution
- BOP context (agents, orchestrators, MCP tools)
- Conventional commits format
- Quality scoring with BOP considerations

### Python Quality Checks

Python-specific checks (`config/rules/python-quality.mjs`) detect:
- `print()` statements (warnings, except in tests/main)
- TODO/FIXME/XXX/HACK without context (warnings)
- Test anti-patterns:
  - `pytest.skip()` without reason (error)
  - `time.sleep()` in tests (warning)
  - Bare `except` clauses (warning)

## Usage

### Daily Workflow

1. **Before Committing**:
   ```bash
   # Test commit message
   npx hookwise test-commit "feat(agent): your message"
   
   # Run all checks (garden mode)
   npx hookwise garden
   ```

2. **During Commit**:
   - Pre-commit hook runs automatically
   - Provides feedback on:
     - Documentation bloat
     - Python quality issues
     - Linting errors
     - Config validation

3. **Before Pushing**:
   - Pre-push hook runs automatically
   - Comprehensive checks:
     - Deployment config validation
     - Secret scanning
     - Full linting
     - Type checking (optional)
     - Fast unit tests

### Monitoring

```bash
# View metrics
npx hookwise metrics

# Get recommendations
npx hookwise recommend

# Export metrics
npx hookwise export-metrics > metrics.json
```

### Q&A System

```bash
# Load .env first (for CLI usage)
export $(grep -v '^#' .env | grep -v '^$' | xargs)

# Ask questions about repository
npx hookwise ask "What are the main components of BOP?"
npx hookwise ask "How does the orchestrator work?"
```

**Note**: Hooks automatically load `.env`, so Q&A works in commit hooks without manual export.

## Configuration Files

### `.hookwise.config.mjs`
Main configuration:
- Commit message settings (agentic, tier, minScore)
- Documentation settings (maxRootFiles, archivePatterns)
- Code quality settings (enabled/disabled)

### `.hookwise.hooks.mjs`
Which checks run:
- `commitMsg`: format + llm
- `preCommit`: doc-bloat + code-quality

### `config/prompts/commit-message.mjs`
Custom commit message analysis prompt (BOP-specific)

### `config/rules/conventional-commits.mjs`
Custom commit validation rules (BOP types)

### `config/rules/python-quality.mjs`
Python-specific quality checks

## Steering Mechanisms

### Pre-Commit Steering
- **Fast feedback** on staged changes
- **Auto-fixes** linting where possible
- **Warnings** for documentation bloat
- **Errors** for blocking issues

### Pre-Push Steering
- **Comprehensive validation** before push
- **Deployment config** checks
- **Secret scanning** for security
- **Full test suite** (fast tests)

### Commit Message Steering
- **Format validation** (conventional commits)
- **Quality scoring** (LLM analysis)
- **Suggestions** for improvement
- **BOP-specific** context awareness

## Fixed Points (Desired States)

The hooks steer toward:

1. **Code Quality Fixed Point**:
   - All code linted (ruff)
   - Type-checked (mypy)
   - No print() statements
   - TODOs have context
   - Tests follow best practices

2. **Documentation Fixed Point**:
   - ≤25 root markdown files
   - Temporary docs archived
   - Clear organization

3. **Commit Message Fixed Point**:
   - Conventional commits format
   - Research-focused clarity
   - Quality score ≥5
   - BOP-specific context

4. **Security Fixed Point**:
   - No hardcoded secrets
   - Environment variables used
   - .env.example documented

5. **Deployment Fixed Point**:
   - Valid fly.toml
   - Valid Dockerfile
   - Health checks configured
   - Scripts executable

## Troubleshooting

### Hooks Not Running
```bash
# Reinstall hooks
npx husky install
npx hookwise install
```

### API Keys Not Found
```bash
# Check .env exists and has keys
cat .env | grep API_KEY

# For CLI usage, export first
export $(grep -v '^#' .env | grep -v '^$' | xargs)
```

### Config Validation Fails
```bash
# Validate config
npx hookwise validate-config

# Check config file syntax
node -e "import('./.hookwise.config.mjs').then(c => console.log('Valid'))"
```

### Python Quality Checks Fail
```bash
# Test manually
node scripts/python_quality_check.mjs

# Check staged files
git diff --cached --name-only | grep '\.py$'
```

## Best Practices

1. **Use Garden Mode**: Test before committing
   ```bash
   npx hookwise garden
   ```

2. **Monitor Metrics**: Review regularly
   ```bash
   npx hookwise metrics
   npx hookwise recommend
   ```

3. **Follow BOP Types**: Use research/theory/agent/mcp when appropriate

4. **Address Warnings**: Don't ignore steering signals

5. **Keep Docs Clean**: Archive temporary analysis docs

## Integration Status

| Feature | Status | Notes |
|---------|--------|-------|
| Commit Message Validation | ✅ Complete | Agentic mode, custom prompt/rules |
| Documentation Bloat | ✅ Complete | Enabled, temporal learning |
| Code Quality (JS) | ⚠️ Disabled | Python project |
| Code Quality (Python) | ✅ Complete | Custom checks + ruff |
| Custom Prompts | ✅ Complete | BOP-specific |
| Custom Rules | ✅ Complete | BOP types + Python quality |
| Metrics | ⚠️ Available | Not automatically reviewed |
| Q&A System | ⚠️ Partial | Works in hooks, needs export for CLI |
| CI/CD Integration | ✅ Created | GitHub Actions workflow |
| IDE Integration | 💡 Future | Could add on-save |

## Next Steps

1. **Activate CI/CD**: Test GitHub Actions workflow
2. **Monitor Metrics**: Set up regular review
3. **Enhance Agentic Tools**: Add Python-specific tools
4. **IDE Integration**: Add on-save validation
5. **Team Guidelines**: Document BOP commit conventions

The system is harmonized with hookwise's capabilities and provides comprehensive steering toward quality, security, and proper practices.

