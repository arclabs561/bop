# Hookwise .env Auto-Loading

## Summary

Created a wrapper script that automatically loads `.env` for hookwise CLI commands, so you don't need to manually export environment variables.

## Problem

- **Git hooks** (commit-msg, pre-commit) already auto-load `.env` ✅
- **CLI commands** (`npx hookwise garden`, `npx hookwise test-commit`) did NOT auto-load `.env` ❌

This meant you had to manually export API keys:
```bash
export $(grep -v '^#' .env | grep -v '^$' | xargs)
npx hookwise garden
```

## Solution

**✅ Implemented in hookwise**: Added `.env` auto-loading directly to hookwise's `src/cli.mjs`:
1. Automatically finds repository root using `findRepoRoot()`
2. Looks for `.env` file in repo root
3. Parses and loads environment variables
4. Respects existing environment variables (doesn't override)
5. Silently fails if `.env` doesn't exist (non-breaking)

**Legacy**: The `scripts/hookwise` wrapper script is no longer needed but kept for backward compatibility.

## Usage

### Using the Wrapper Script

```bash
# Auto-loads .env automatically
./scripts/hookwise garden
./scripts/hookwise test-commit "feat(agent): message"
./scripts/hookwise test-docs
./scripts/hookwise ask "What are the main components?"
```

### Using Justfile Commands

The justfile has been updated to use the wrapper:

```bash
# All these now auto-load .env
just hook-garden
just hook-test-docs
just hook-test-commit "feat: message"
```

### Manual Usage (if needed)

If you prefer to use `npx hookwise` directly:

```bash
# Load .env first
source scripts/setup_hookwise_env.sh

# Then run hookwise
npx hookwise garden
```

## How It Works

The wrapper script (`scripts/hookwise`):
1. Finds repo root using `git rev-parse --show-toplevel`
2. Looks for `.env` file in repo root
3. Loads `.env` using shell sourcing (with fallback parsing)
4. Exports all variables
5. Runs `npx hookwise` with all passed arguments

## Files Updated

1. **`scripts/hookwise`** - New wrapper script (executable)
2. **`justfile`** - Updated to use wrapper for hookwise commands
3. **`CONTRIBUTING.md`** - Updated with wrapper usage instructions
4. **`HOOKWISE_ENHANCEMENTS.md`** - Added auto-load section

## Verification

Test that it works:

```bash
# Should auto-load .env and run without "Tip: Set API key" message
./scripts/hookwise test-commit "feat(agent): test"

# Or via justfile
just hook-garden
```

## Notes

- **Git hooks** continue to auto-load `.env` (no changes needed)
- **CLI commands** now auto-load via wrapper script
- **Backward compatible**: You can still use `npx hookwise` directly if you export `.env` manually
- **Justfile integration**: All hookwise commands in justfile now use the wrapper

## Related

- `.husky/commit-msg` - Auto-loads .env for commit hooks
- `.husky/pre-commit` - Auto-loads .env for pre-commit hooks
- `scripts/setup_hookwise_env.sh` - Manual .env loading script (for reference)
- `HOOKWISE_ENV_FEATURE_PROPOSAL.md` - Proposal to add this to hookwise proper
- `HOOKWISE_ENV_IMPLEMENTATION.md` - Implementation details for hookwise maintainers

## Status

✅ **Implemented**: `.env` auto-loading is now built into hookwise (added to `src/cli.mjs`)

The wrapper script (`scripts/hookwise`) is no longer needed but kept for backward compatibility. You can now use:

```bash
# Works directly - no wrapper needed
npx hookwise garden
npx hookwise test-commit "feat: message"
npx hookwise ask "question"
```

The justfile can be updated to use `npx hookwise` directly instead of the wrapper.

