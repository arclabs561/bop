# Missing Guards & Enhancements Plan

Based on guarded configuration review and Hookwise capabilities discovery.

## ✅ What We Have

### Current Guards
1. **commit-msg** - Hookwise validation (format + LLM + agentic)
2. **pre-commit** - Hookwise checks + Python linting (ruff on staged files)
3. **pre-push** - Comprehensive checks (ruff + mypy + pytest)
4. **pre-rebase** - Informational check

### Current Features
- ✅ .env loading in hooks (improved)
- ✅ Astral tools (uv, ruff, mypy) integration
- ✅ Hookwise agentic mode enabled
- ✅ Fast pre-commit, comprehensive pre-push
- ✅ Configuration documented

## ❌ What's Missing

### 1. Hookwise Features Not Enabled

#### A. Q&A System
**Status**: Not configured
**Missing**: LLM API key in .env for hookwise
**Impact**: Can't use `npx hookwise ask` command
**Fix**:
```bash
# Add to .env
GEMINI_API_KEY=...  # or OPENAI_API_KEY or ANTHROPIC_API_KEY
```

#### B. Metrics Monitoring
**Status**: Available but not used
**Missing**: Regular metrics review
**Fix**: Add to workflow
```bash
# Check metrics periodically
npx hookwise metrics
npx hookwise recommend
```

#### C. Custom Prompts
**Status**: Not customized
**Missing**: Project-specific commit message prompts
**Fix**: Create `config/prompts/commit-message.mjs`
- Focus on Python project conventions
- Emphasize research/academic documentation style
- Include BOP-specific context

#### D. Custom Rules
**Status**: Using defaults
**Missing**: Project-specific validation rules
**Fix**: Create `config/rules/conventional-commits.mjs`
- Add BOP-specific commit types (research, theory, analysis)
- Customize for Python project patterns

### 2. Guard Coverage Gaps

#### A. Pre-Push Deployment Validation
**Status**: Manual only
**Missing**: Automated deployment config validation
**What to add**:
- Validate `fly.toml` syntax
- Validate `Dockerfile` structure
- Check required secrets are documented
- Verify deployment scripts are executable

**Implementation**:
```bash
# .husky/pre-push (add before tests)
echo "🔍 Validating deployment configuration..."
uv run python scripts/validate_deployment_config.py || exit 1
```

#### B. Pre-Push Security Scanning
**Status**: Manual only
**Missing**: Automated secret scanning
**What to add**:
- Scan for hardcoded API keys
- Check for secrets in staged files
- Validate .env.example is up to date
- Check for exposed credentials

**Implementation**:
```bash
# .husky/pre-push (add before tests)
echo "🔒 Scanning for secrets..."
uv run python scripts/scan_secrets.py || exit 1
```

#### C. Pre-Commit Type Checking (Optional)
**Status**: Only in pre-push
**Missing**: Fast type checking on staged files
**What to add**:
- Quick mypy check on staged Python files only
- Skip if too slow (configurable)

**Implementation**:
```bash
# .husky/pre-commit (optional, can skip)
if [ "$SKIP_TYPE_CHECK" != "1" ]; then
  STAGED_PY=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' || true)
  if [ -n "$STAGED_PY" ]; then
    echo "$STAGED_PY" | xargs uv run mypy --no-error-summary || true
  fi
fi
```

### 3. Hookwise Integration Gaps

#### A. Documentation Bloat Detection
**Status**: Disabled
**Missing**: Active documentation management
**Fix**: Re-enable and customize
```javascript
// .hookwise.config.mjs
documentation: {
  enabled: true,  // Re-enable
  maxRootFiles: 25,  // Already set
  archivePatterns: [...],  // Already set
}
```

#### B. Code Quality Checks
**Status**: Disabled (Python project)
**Missing**: Python-specific code quality checks
**Fix**: Create custom Python checks
- Call ruff from hookwise
- Check for print statements (not console.log)
- Check for TODO patterns
- Python-specific test patterns

**Implementation**: Create `config/rules/python-quality.mjs`

#### C. Agentic Tool Integration
**Status**: Enabled but not optimized
**Missing**: Custom tools for Python project
**What to add**:
- Python AST analysis tool
- Import dependency checker
- Test coverage checker
- Documentation completeness checker

### 4. Workflow Integration Gaps

#### A. CI/CD Integration
**Status**: Not integrated
**Missing**: Hookwise garden in CI/CD
**Fix**: Add to GitHub Actions / CI
```yaml
- name: Run Hookwise Checks
  run: npx hookwise garden
```

#### B. IDE Integration
**Status**: Not integrated
**Missing**: Hookwise on save/format
**Fix**: Configure IDE to run `npx hookwise garden` on save

#### C. Metrics Dashboard
**Status**: CLI only
**Missing**: Visual metrics dashboard
**Fix**: Create simple HTML dashboard or integrate with existing tools

### 5. Configuration Gaps

#### A. Global Configuration
**Status**: Not set up
**Missing**: Personal defaults in `~/.hookwise.config.mjs`
**Fix**: Create global config for personal preferences

#### B. Environment Variable Documentation
**Status**: Scattered
**Missing**: Centralized .env documentation
**Fix**: Update `.env.example` with all hookwise-related vars

#### C. Configuration Validation
**Status**: Manual
**Missing**: Automated config validation
**Fix**: Run `npx hookwise validate-config` in pre-commit

### 6. Testing Gaps

#### A. Hook Testing
**Status**: Manual
**Missing**: Automated hook testing
**Fix**: Create test suite for hooks
```bash
# Test all hooks
test-hooks:
  npx hookwise test-commit "feat: test"
  npx hookwise test-docs
  npx hookwise test-quality
  npx hookwise garden
```

#### B. Guard Testing
**Status**: Manual
**Missing**: Automated guard testing
**Fix**: Create test suite for guards
- Test pre-commit with staged files
- Test pre-push with various scenarios
- Test .env loading
- Test error handling

### 7. Documentation Gaps

#### A. Guard Usage Guide
**Status**: Basic
**Missing**: Comprehensive usage guide
**Fix**: Expand `GUARDED_CONFIG.md` with:
- Common scenarios
- Troubleshooting guide
- Best practices
- Examples

#### B. Hookwise Integration Guide
**Status**: None
**Missing**: BOP-specific hookwise guide
**Fix**: Create `HOOKWISE_INTEGRATION.md` with:
- BOP-specific configuration
- Custom prompts/rules
- Workflow integration
- Team guidelines

## 🎯 Priority Implementation Plan

### Phase 1: Quick Wins (1-2 hours)
1. ✅ Improve .env loading in hooks (DONE)
2. Add LLM API key to .env for hookwise Q&A
3. Re-enable documentation bloat detection
4. Add `npx hookwise validate-config` to pre-commit
5. Create hook testing script

### Phase 2: Enhanced Guards (2-4 hours)
1. Add deployment config validation to pre-push
2. Add secret scanning to pre-push
3. Create Python-specific code quality checks
4. Add optional type checking to pre-commit

### Phase 3: Customization (4-6 hours)
1. Create custom commit message prompts
2. Create custom validation rules
3. Create Python-specific quality rules
4. Set up global configuration

### Phase 4: Integration (2-3 hours)
1. Add hookwise garden to CI/CD
2. Configure IDE integration
3. Create metrics dashboard
4. Document workflow integration

### Phase 5: Advanced Features (4-8 hours)
1. Create custom agentic tools for Python
2. Build metrics visualization
3. Create comprehensive testing suite
4. Write integration documentation

## 📋 Implementation Checklist

### Immediate (Today)
- [x] Improve .env loading in commit-msg hook
- [ ] Add LLM API key to .env
- [ ] Test hookwise Q&A: `npx hookwise ask "test"`
- [ ] Re-enable documentation bloat detection
- [ ] Run `npx hookwise metrics` and review

### Short-term (This Week)
- [ ] Create custom commit message prompt
- [ ] Add deployment config validation
- [ ] Add secret scanning
- [ ] Create hook testing script
- [ ] Document hookwise integration

### Medium-term (This Month)
- [ ] Create Python-specific quality checks
- [ ] Set up CI/CD integration
- [ ] Configure IDE integration
- [ ] Build metrics dashboard
- [ ] Write comprehensive guides

### Long-term (Ongoing)
- [ ] Create custom agentic tools
- [ ] Build advanced metrics
- [ ] Create testing suite
- [ ] Continuous refinement

## 🔍 Verification

After implementing, verify:
1. All hooks load .env correctly
2. Hookwise Q&A works with API key
3. Metrics are being collected
4. Guards catch issues before push
5. Custom prompts/rules are used
6. CI/CD runs hookwise checks
7. Documentation is up to date

## 📝 Notes

- Hookwise agentic mode is already enabled (good!)
- Most missing items are about leveraging existing capabilities
- Focus on Python-specific customizations
- Prioritize developer experience improvements
- Keep guards fast (pre-commit <1s, pre-push <45s)

