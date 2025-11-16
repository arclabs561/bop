# Project Organization

## Documentation Structure

### Core Documentation (Root)

These files should remain in the root directory:

- **`README.md`** - Main project documentation and quick start
- **`ARCHITECTURE.md`** - Architecture and theoretical foundations
- **`AGENTS.md`** - Agent architecture and usage guide
- **`CONTRIBUTING.md`** - Development guidelines
- **`CODE_STYLE.md`** - Code style and comment conventions

### Optional Documentation

- **`QUICKSTART.md`** - Alternative quick start guide (consider consolidating with README)
- **`START_HERE.md`** - Entry point guide (consider consolidating with README)

### Archive Recommendations

Many markdown files in the root are temporary analysis, summaries, or implementation notes. Consider archiving to `docs/archive/`:

**Implementation/Summary Files**:
- `*_SUMMARY.md`
- `*_COMPLETE.md`
- `*_STATUS.md`
- `*_RESULTS.md`
- `*_NOTES.md`
- `*_GUIDE.md` (if not core)

**Analysis Files**:
- `*_ANALYSIS.md`
- `*_CRITIQUE.md`
- `*_DESIGN.md`
- `*_RESEARCH_SYNTHESIS.md`

**Deployment Files**:
- `*_DEPLOY.md`
- `*_SETUP.md`
- `*_COMMANDS.md`

## File Organization Strategy

### Option 1: Archive by Type

```
docs/
├── archive/
│   ├── implementation/    # Implementation summaries
│   ├── analysis/          # Analysis documents
│   ├── deployment/        # Deployment guides
│   └── research/         # Research synthesis
```

### Option 2: Archive by Date

```
docs/
├── archive/
│   └── 2025-01/          # All docs from January 2025
```

### Option 3: Keep Recent, Archive Old

Keep the 5-10 most recent/relevant docs in root, archive the rest.

## Current Status

- **84 untracked files** (many markdown files)
- **59 markdown files in root** (should be ~5-10)
- **Core docs**: README, ARCHITECTURE, AGENTS, CONTRIBUTING, CODE_STYLE

## Recommendations

1. **Keep in root**: README, ARCHITECTURE, AGENTS, CONTRIBUTING, CODE_STYLE
2. **Archive**: All `*_SUMMARY.md`, `*_COMPLETE.md`, `*_STATUS.md` files
3. **Consolidate**: Multiple quick start guides into README
4. **Organize**: Create `docs/archive/` structure

## Tools

Use the justfile for common operations:

```bash
just clean          # Clean Python cache
just test           # Run tests
just lint           # Run linting
just docs-arch      # View architecture
just docs-agents    # View agents guide
```

