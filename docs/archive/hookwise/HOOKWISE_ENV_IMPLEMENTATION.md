# Hookwise .env Auto-Loading Implementation

## Summary

Yes, `.env` auto-loading should be part of hookwise proper. This document outlines the implementation approach.

## Current State

- ✅ Git hooks auto-load `.env` (via shell scripts)
- ❌ CLI commands don't auto-load `.env` (requires wrapper script)

## Proposed Implementation

Add `.env` auto-loading to `src/cli.mjs` at the very beginning, before any other code runs.

### Option 1: Use `dotenv` (Recommended)

**Add to `package.json`**:
```json
{
  "optionalDependencies": {
    "dotenv": "^16.0.0"
  }
}
```

**Add to `src/cli.mjs`** (at the top, before imports):
```javascript
// Auto-load .env from repo root
import { config } from 'dotenv';
import { existsSync } from 'fs';
import { join } from 'path';
import { findRepoRoot } from './utils.mjs'; // Already exists in hookwise

const repoRoot = findRepoRoot();
const envPath = join(repoRoot, '.env');
if (existsSync(envPath)) {
  config({ path: envPath });
}
```

### Option 2: Lightweight Custom Parser

If avoiding dependencies, implement a minimal parser:

```javascript
// In src/cli.mjs
import { readFileSync, existsSync } from 'fs';
import { join } from 'path';
import { findRepoRoot } from './utils.mjs';

function loadEnvFile(filePath) {
  if (!existsSync(filePath)) return;
  
  try {
    const content = readFileSync(filePath, 'utf8');
    const lines = content.split('\n');
    
    for (const line of lines) {
      const trimmed = line.trim();
      // Skip comments and empty lines
      if (!trimmed || trimmed.startsWith('#')) continue;
      
      const match = trimmed.match(/^([^=]+)=(.*)$/);
      if (match) {
        const key = match[1].trim();
        let value = match[2].trim();
        // Remove quotes if present
        if ((value.startsWith('"') && value.endsWith('"')) ||
            (value.startsWith("'") && value.endsWith("'"))) {
          value = value.slice(1, -1);
        }
        // Only set if not already in environment (respect existing env vars)
        if (!process.env[key]) {
          process.env[key] = value;
        }
      }
    }
  } catch (error) {
    // Silently fail - don't break if .env can't be read
  }
}

// Auto-load .env from repo root
const repoRoot = findRepoRoot();
loadEnvFile(join(repoRoot, '.env'));
```

## Implementation Location

Add to `src/cli.mjs` right after the initial imports and before any CLI command logic:

```javascript
#!/usr/bin/env node
// ... existing imports ...

// ============================================================================
// Auto-load .env from repo root (before any CLI commands)
// ============================================================================
// ... .env loading code here ...

// ============================================================================
// CLI Commands
// ============================================================================
// ... rest of CLI code ...
```

## Benefits

1. **Consistency**: Same behavior as git hooks
2. **Better DX**: No wrapper scripts needed
3. **Standard**: Follows Node.js best practices
4. **Backward compatible**: Doesn't break existing usage

## Testing

After implementation, test:

```bash
# Should work without wrapper
npx hookwise garden
npx hookwise test-commit "feat: message"
npx hookwise ask "question"
```

## Migration Path

1. Add `.env` auto-loading to hookwise
2. Users can remove `scripts/hookwise` wrapper
3. Update documentation
4. Remove wrapper from justfile (use `npx hookwise` directly)

## Next Steps

1. **Propose to hookwise maintainers**: Create issue/PR on GitHub
2. **Keep wrapper as temporary solution**: Until hookwise adds the feature
3. **Document workaround**: In CONTRIBUTING.md and HOOKWISE_ENHANCEMENTS.md

## Repository

Hookwise is at: `https://github.com/arclabs561/hookwise`

We should propose this as a feature request or PR.

