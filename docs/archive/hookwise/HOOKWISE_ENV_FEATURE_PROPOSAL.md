# Hookwise .env Auto-Loading Feature Proposal

## Problem

Currently, hookwise CLI commands don't auto-load `.env` files, requiring users to manually export environment variables:

```bash
export $(grep -v '^#' .env | grep -v '^$' | xargs)
npx hookwise garden
```

While git hooks can load `.env` via shell scripts, the Node.js CLI doesn't have this capability.

## Proposed Solution

Add automatic `.env` file loading to hookwise's CLI entry point (`src/cli.mjs`) using a lightweight `.env` parser.

## Implementation Options

### Option 1: Use `dotenv` package (Recommended)

Add `dotenv` as an optional dependency and auto-load `.env` from repo root:

```javascript
// In src/cli.mjs, before any other imports
import { config } from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { existsSync } from 'fs';

// Find repo root
function findRepoRoot() {
  let currentDir = dirname(fileURLToPath(import.meta.url));
  while (currentDir !== '/') {
    if (existsSync(join(currentDir, '.git'))) {
      return currentDir;
    }
    currentDir = dirname(currentDir);
  }
  return process.cwd();
}

// Auto-load .env from repo root
const repoRoot = findRepoRoot();
const envPath = join(repoRoot, '.env');
if (existsSync(envPath)) {
  config({ path: envPath });
}
```

**Pros**:
- Standard approach (dotenv is widely used)
- Handles edge cases (quoted values, comments, etc.)
- Small dependency (~2KB)

**Cons**:
- Adds a dependency (though optional)

### Option 2: Lightweight custom parser

Implement a minimal `.env` parser directly in hookwise:

```javascript
// In src/cli.mjs
import { readFileSync, existsSync } from 'fs';
import { join } from 'path';

function loadEnvFile(filePath) {
  if (!existsSync(filePath)) return;
  
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
      process.env[key] = value;
    }
  }
}

// Find and load .env
function findRepoRoot() {
  // ... (same as Option 1)
}

const repoRoot = findRepoRoot();
loadEnvFile(join(repoRoot, '.env'));
```

**Pros**:
- No external dependencies
- Full control over parsing

**Cons**:
- More code to maintain
- May miss edge cases

### Option 3: Use Node.js built-in (Node 20.6+)

Node.js 20.6+ has built-in `.env` support via `--env-file` flag, but this requires users to pass the flag.

**Pros**:
- No dependencies
- Built into Node.js

**Cons**:
- Requires user to pass flag
- Not automatic

## Recommendation

**Option 1 (dotenv)** is recommended because:
1. It's the standard solution
2. Handles all edge cases
3. Small dependency footprint
4. Widely trusted and maintained

## Implementation Details

### Where to Add

Add `.env` loading at the very beginning of `src/cli.mjs`, before any other imports that might need environment variables:

```javascript
// src/cli.mjs
import { config } from 'dotenv';
// ... other imports

// Auto-load .env from repo root (before any CLI logic)
function autoLoadEnv() {
  // Find repo root
  const repoRoot = findRepoRoot();
  const envPath = join(repoRoot, '.env');
  
  if (existsSync(envPath)) {
    config({ path: envPath });
  }
}

autoLoadEnv();

// ... rest of CLI code
```

### Behavior

- **Silent**: Don't print messages if `.env` is loaded (standard behavior)
- **Non-blocking**: If `.env` doesn't exist or can't be read, continue normally
- **Repo root**: Look for `.env` in git repo root (not current directory)
- **Override**: Environment variables already set take precedence (standard dotenv behavior)

### Package.json Changes

```json
{
  "optionalDependencies": {
    "dotenv": "^16.0.0"
  }
}
```

Or make it a peer dependency that users can install if needed.

## Benefits

1. **Better DX**: Users don't need wrapper scripts or manual exports
2. **Consistency**: Same behavior as git hooks (which already load .env)
3. **Standard**: Follows common Node.js patterns
4. **Backward compatible**: Doesn't break existing usage

## Migration Path

1. Add `.env` auto-loading to hookwise
2. Users can remove wrapper scripts
3. Update documentation to show `.env` auto-loading works out of the box

## Alternative: Keep Wrapper for Now

If adding to hookwise isn't feasible immediately, we can:
1. Keep the wrapper script as a workaround
2. Document it as a temporary solution
3. Propose the feature to hookwise maintainers
4. Remove wrapper once hookwise adds the feature

## Related

- Current wrapper: `scripts/hookwise`
- Git hooks already load `.env`: `.husky/commit-msg`, `.husky/pre-commit`
- Issue: CLI commands don't auto-load `.env`

