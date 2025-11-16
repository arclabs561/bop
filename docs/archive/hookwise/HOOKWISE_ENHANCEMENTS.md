# Hookwise Configuration Enhancements

## Summary

Enhanced Hookwise configuration and rules to better align with BOP's research project needs and improve commit message quality guidance.

## Changes Made

### 1. Enhanced Archive Patterns (`.hookwise.config.mjs`)

**Added comprehensive archive patterns**:
- **Implementation/Summary**: `_NOTES.md`, `_RESULTS.md`, `_STATUS.md`
- **Analysis**: `AMBIENT_`, `_CRITIQUE.md`, `_DESIGN.md`
- **Planning**: `_NEXT_STEPS.md`, `_ENHANCEMENT.md`
- **Theory/Research**: `THEORY_`, `_RESEARCH.md`
- **Deployment**: `_DEPLOY.md`, `_SETUP.md`, `_COMMANDS.md`, `_DEPLOYMENT.md`
- **External Analysis**: `KUMORFM_`, `DOCUMENTATION_HARMONIZATION`

**Added archive directory tracking**:
- `docs/archive/`
- `docs/archive/external-analysis/`
- `docs/archive/analysis-docs/`

This helps Hookwise learn from existing archive patterns and suggest better organization.

### 2. BOP-Specific Configuration Section

**Added `bop` configuration section**:
```javascript
bop: {
  allowResearchDocs: true,  // Allow more documentation for research projects
  requireScopeForTypes: ['feat', 'fix', 'refactor'],  // Require scope for major changes
  coreDocs: [...],  // List of core documentation files
  userGuides: [...],  // List of user guide files
}
```

This provides:
- Research project allowances
- Scope requirements for better commit organization
- Documentation categorization

### 3. Enhanced Commit Message Validation (`config/rules/conventional-commits.mjs`)

**Added scope recommendations**:
- Suggests adding scope for `feat`, `fix`, `refactor` types
- Provides common scopes: `agent`, `orchestrator`, `research`, `topology`, `constraints`, `eval`, `cli`, `web`

**Enhanced BOP-specific guidance**:
- `agent` type: Suggests scope or component mention
- `analysis` type: Suggests mentioning what's being analyzed
- Better suggestions for all BOP-specific types

### 4. Enhanced Commit Message Prompt (`config/prompts/commit-message.mjs`)

**Updated type list**: Added `agent` and `mcp` to the type list

**Enhanced scope guidance**: 
- Recommends scope for `feat/fix/refactor`
- Lists common scopes: `agent`, `orchestrator`, `research`, `topology`, `constraints`, `eval`, `cli`, `web`, `mcp`

**Added BOP-specific considerations**:
- Topology/trust changes should mention metrics
- Constraint solver changes should note optimization impact
- Quality feedback changes should mention evaluation dimensions

### 5. Enhanced Hooks Configuration (`.hookwise.hooks.mjs`)

**Added prePush option** (disabled by default):
- Can enable for comprehensive pre-push checks
- Would include secret scanning, full linting, type checking

**Documented Python quality checks**:
- Notes that Python quality checks are available via `config/rules/python-quality.mjs`
- Can be enabled by adding `'python-quality'` to preCommit checks

## Benefits

### Better Documentation Organization
- More comprehensive archive pattern recognition
- Archive directory learning for better suggestions
- External analysis tracking (KumoRFM, etc.)

### Improved Commit Messages
- Scope recommendations for better organization
- BOP-specific guidance for research/theory commits
- Enhanced LLM prompt with more context

### Research Project Support
- Explicit research project allowances
- Core docs vs. user guides categorization
- Better handling of theoretical work

## Usage

### Auto-Load .env for CLI Commands

**New**: Use the wrapper script to auto-load `.env`:

```bash
# Auto-loads .env automatically
./scripts/hookwise garden
./scripts/hookwise test-commit "feat(agent): add belief-evidence alignment"
./scripts/hookwise test-docs
./scripts/hookwise ask "What are the main components?"
```

**Or manually load .env** (if not using wrapper):

```bash
# Load .env first
source scripts/setup_hookwise_env.sh
# Then run hookwise commands
npx hookwise garden
```

**Note**: Git hooks automatically load `.env`, so commits work without manual setup.

### Test Enhanced Configuration

```bash
# Using wrapper (auto-loads .env)
./scripts/hookwise test-commit "feat(agent): add belief-evidence alignment"
./scripts/hookwise test-docs
./scripts/hookwise garden

# Or manually (requires .env export first)
npx hookwise test-commit "feat(agent): add belief-evidence alignment"
```

### Enable Python Quality Checks (Optional)

Edit `.hookwise.hooks.mjs`:
```javascript
preCommit: {
  enabled: true,
  checks: ['doc-bloat', 'python-quality']  // Add python-quality
}
```

Note: This requires custom integration in hookwise to call `config/rules/python-quality.mjs`.

## Configuration Files Updated

1. `.hookwise.config.mjs` - Main configuration with enhanced archive patterns and BOP settings
2. `config/rules/conventional-commits.mjs` - Enhanced validation with scope recommendations
3. `config/prompts/commit-message.mjs` - Enhanced LLM prompt with more BOP context
4. `.hookwise.hooks.mjs` - Documented Python quality option

## Next Steps (Optional)

1. **Enable Python Quality Checks**: Integrate `python-quality.mjs` into hookwise's pre-commit hook
2. **Pre-Push Checks**: Enable pre-push hook for comprehensive validation before pushing
3. **Metrics Tracking**: Review `npx hookwise metrics` to see impact of enhancements
4. **Archive Learning**: Let Hookwise learn from `docs/archive/` patterns over time

## Related Documentation

- `HOOKWISE_INTEGRATION.md` - Complete integration guide
- `HOOKWISE_CAPABILITIES.md` - Full capabilities documentation
- `HOOKWISE_DEV_EXPERIENCE_CRITIQUE.md` - Dev experience notes
- `CONTRIBUTING.md` - Git hooks section

