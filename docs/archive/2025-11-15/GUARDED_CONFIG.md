# Guarded Configuration

This document lists all guarded configurations and git hooks that protect code quality, security, and deployment.

## Current Guards

### 1. Commit Message Guard (`.husky/commit-msg`)
**Purpose**: Validates commit messages follow Conventional Commits format

**Configuration**: `.hookwise.config.mjs`
- `commitMessage.enabled: true`
- `commitMessage.blocking: false` (non-blocking to avoid friction)
- `commitMessage.tier: 'advanced'` (advanced LLM analysis)
- `commitMessage.agentic: true` (agentic loop with tool calling)

**What it checks**:
- Commit message format (Conventional Commits)
- Message quality via LLM analysis
- Minimum score threshold: 5

**How to test**:
```bash
npx hookwise test-commit "feat: your message"
```

### 2. Pre-Commit Guard (`.husky/pre-commit`)
**Purpose**: Fast checks before committing

**What it checks**:
- Documentation bloat (via hookwise)
- Python linting on staged files (ruff)
- Auto-fixes linting issues where possible

**Configuration**: `.hookwise.config.mjs`
- `documentation.enabled: false` (temporarily disabled)
- `codeQuality.enabled: false` (Python project, JS checks disabled)

**How to test**:
```bash
npx hookwise test-docs
npx hookwise garden
```

### 3. Pre-Push Guard (`.husky/pre-push`) ⭐ NEW
**Purpose**: Comprehensive checks before pushing to remote

**What it checks**:
- Code linting (ruff check)
- Type checking (mypy, optional, can skip with `SKIP_TYPE_CHECK=1`)
- Fast unit tests (skips e2e and slow tests)

**Why pre-push instead of pre-commit**:
- Pre-commit: Fast checks only (linting, formatting)
- Pre-push: Comprehensive checks (tests, type checking)
- Prevents pushing broken code while keeping commits fast

**How to skip** (not recommended):
```bash
SKIP_TYPE_CHECK=1 git push  # Skip type checking only
git push --no-verify        # Skip all pre-push checks (dangerous)
```

### 4. Pre-Rebase Guard (`.husky/pre-rebase`) ⭐ NEW
**Purpose**: Informational check (git already handles uncommitted changes by default)

**What it checks**:
- Reports rebase.autoStash configuration
- Informs about uncommitted changes (non-blocking)

**Note**: Git prevents rebasing with uncommitted changes by default unless `rebase.autoStash` is enabled. This guard is informational only.

## Guarded Areas

### Code Quality (Astral Tools)
- ✅ **Linting**: ruff via `uv run ruff` (pre-commit on staged files, pre-push on all)
- ✅ **Type Checking**: mypy via `uv run mypy` (pre-push, optional)
- ✅ **Formatting**: ruff format via `uv run ruff format` (manual via `just format`)
- ✅ **Package Management**: uv (Astral) for all Python tool execution

### Testing
- ✅ **Unit Tests**: pytest (pre-push, fast tests only)
- ⚠️ **E2E Tests**: Manual or CI/CD (too slow for hooks)
- ⚠️ **Slow Tests**: Manual or CI/CD (marked with `@pytest.mark.slow`)

### Documentation
- ✅ **Bloat Detection**: hookwise (pre-commit, currently disabled)
- ✅ **Archive Patterns**: Defined in `.hookwise.config.mjs`

### Deployment
- ⚠️ **Deployment Validation**: Manual via `./scripts/validate_secrets.sh`
- ⚠️ **Deployment Verification**: Manual via `./scripts/verify_deployment.sh`
- 💡 **Future**: Could add pre-push check for deployment config validity

### Security
- ⚠️ **Secrets Scanning**: Manual via `./scripts/redteam_test.sh`
- ⚠️ **Security Tests**: Manual or CI/CD
- 💡 **Future**: Could add pre-push secret scanning

## Missing Guards (Potential Additions)

### High Priority
1. **Pre-Push Test Guard** ✅ ADDED
   - Run fast tests before pushing
   - Prevents pushing broken code

2. **Pre-Push Linting Guard** ✅ ADDED
   - Comprehensive linting before push
   - Pre-commit does staged files only

### Medium Priority
3. **Deployment Config Validation**
   - Validate `fly.toml` syntax
   - Validate `Dockerfile` structure
   - Check required secrets are documented

4. **Security Scanning**
   - Scan for hardcoded secrets
   - Check dependency vulnerabilities
   - Validate API key patterns

5. **Type Checking Guard** ✅ ADDED (optional)
   - mypy type checking
   - Can be skipped with `SKIP_TYPE_CHECK=1`

### Low Priority
6. **Documentation Guard**
   - Ensure README is updated
   - Check for TODO comments
   - Validate code examples

7. **Test Coverage Guard**
   - Ensure new code has tests
   - Check coverage doesn't decrease
   - Validate test quality

## Configuration Files

### `.hookwise.config.mjs`
Main hookwise configuration:
- Commit message validation settings
- Documentation bloat detection
- Code quality checks (disabled for Python)

### `.hookwise.hooks.mjs`
Hook-specific configuration:
- `commitMsg`: Format and LLM checks
- `preCommit`: Doc-bloat checks

### Git Hooks (`.husky/`)
- `commit-msg`: Commit message validation
- `pre-commit`: Fast pre-commit checks
- `pre-push`: Comprehensive pre-push checks ⭐ NEW
- `pre-rebase`: Rebase safety checks ⭐ NEW

## Bypassing Guards

### When to Bypass
- Emergency hotfixes (use `--no-verify` sparingly)
- WIP commits (use `--no-verify` for draft commits)
- Experimental branches (acceptable to skip some checks)

### How to Bypass
```bash
# Skip pre-commit
git commit --no-verify

# Skip pre-push
git push --no-verify

# Skip type checking only (pre-push)
SKIP_TYPE_CHECK=1 git push
```

### Best Practices
1. **Never bypass in main/master branch**
2. **Document why you bypassed** (in commit message or PR)
3. **Fix issues before merging** (don't merge broken code)
4. **Use feature branches** for experimental work

## Testing Guards

### Test All Guards
```bash
# Test commit message
npx hookwise test-commit "feat: test message"

# Test documentation
npx hookwise test-docs

# Test all hookwise checks
npx hookwise garden

# Test pre-push (simulate)
git push --dry-run  # Won't actually push, but runs hooks
```

### Manual Guard Execution
```bash
# Run pre-commit checks manually
.husky/pre-commit

# Run pre-push checks manually
.husky/pre-push

# Run commit-msg check manually
.husky/commit-msg "$(git log -1 --pretty=%B)"
```

## Guard Performance

### Pre-Commit (Fast)
- Hookwise doc-bloat: ~100ms
- Ruff linting via uv (staged files): ~200-500ms
- **Total**: <1 second

### Pre-Push (Comprehensive)
- Ruff linting via uv (all files): ~1-2s
- Type checking via uv (mypy): ~5-10s (optional, can skip)
- Fast unit tests via uv (pytest): ~10-30s
- **Total**: ~15-45 seconds

**Note**: All tools run via `uv run` (Astral's fast package manager), ensuring consistent environment and fast execution.

### Commit Message (Fast)
- Format validation: <100ms
- LLM analysis: ~2-5s (cached, agentic mode)
- **Total**: <5 seconds

## Troubleshooting

### Guards Failing
1. **Read the error message** - Usually tells you what to fix
2. **Run fixes manually**:
   ```bash
   just lint-fix      # Fix linting
   just format        # Format code
   just test          # Run tests
   ```
3. **Check guard configuration** - Review `.hookwise.config.mjs`

### Guards Too Slow
1. **Skip type checking**: `SKIP_TYPE_CHECK=1 git push`
2. **Run tests locally first**: `just test` before pushing
3. **Use feature branches**: Push to feature branch, fix in PR

### Guards Not Running
1. **Check hooks are installed**: `npx husky install`
2. **Check hooks are executable**: `ls -la .husky/`
3. **Check hookwise is installed**: `npx hookwise --version`

## Future Enhancements

1. **CI/CD Integration**: Run comprehensive checks in CI
2. **Guard Metrics**: Track guard effectiveness
3. **Guard Recommendations**: Suggest guard improvements
4. **Guard Bypass Tracking**: Log when guards are bypassed
5. **Guard Performance Monitoring**: Track guard execution times

