# Repository Analysis Skill

**Purpose:** Guide BOP in analyzing repository structure, organization, and quality.

## Best Practices

### Root Directory Structure
- **Target:** ≤10 markdown files in root
- **Core Docs:** README.md, ARCHITECTURE.md, AGENTS.md, CONTRIBUTING.md, CODE_STYLE.md
- **User Guides:** Should be in `docs/guides/`
- **Archive:** Historical docs in `docs/archive/YYYY-MM-DD/`

### Directory Organization
- **Source Code:** `src/` - All application code
- **Tests:** `tests/` - Test code only (no documentation)
- **Scripts:** `scripts/` - Utility and automation scripts
- **Examples:** `examples/` - Demo scripts and examples
- **Data:** `data/` - Results, evaluation outputs, generated data
- **Documentation:** `docs/` - Guides and archived documentation
- **Config:** `config/` - Configuration files
- **Docker:** `docker/` - Docker-related files

### Git Commit Quality

**Conventional Commits Format:**
```
type(scope): subject

body (optional)

footer (optional)
```

**Rules:**
- **Types:** feat, fix, docs, chore, refactor, test, perf, style
- **Scopes:** Required for feat/fix/refactor (e.g., `feat(agent): ...`)
- **Subject:** ≤72 characters, imperative mood
- **Body:** Explain what and why, not how
- **Consolidation:** Group related docs commits

**Common Scopes:**
- `agent`, `orchestrator`, `research`, `topology`, `constraints`, `eval`, `cli`, `web`, `deploy`, `paths`, `hookwise`

### Code Quality

**Python:**
- No `print()` statements in production code (use logging)
- No bare `except:` clauses
- TODO/FIXME should have context (≥10 chars)
- Tests should not use `time.sleep()` (use async/await)

**File Organization:**
- No Python cache files (`__pycache__/`, `*.pyc`) in repo
- No temporary files (`.tmp`, `.backup`, `.old`)
- Proper `.gitignore` configuration

### Documentation Organization

**Structure:**
```
docs/
├── guides/          # User-facing guides (18 files)
├── archive/         # Historical documentation (251 files)
│   └── YYYY-MM-DD/  # Dated archives
└── [future sections]
```

**Archive Patterns:**
- Implementation summaries: `*_COMPLETE.md`, `*_SUMMARY.md`
- Analysis docs: `*_ANALYSIS.md`, `*_REVIEW.md`
- Status docs: `*_STATUS.md`, `*_REPORT.md`
- Deployment docs: `DEPLOYMENT_*.md`

## Analysis Checklist

When analyzing a repository, check:

1. **Root Cleanliness**
   - [ ] ≤10 markdown files
   - [ ] Core docs present
   - [ ] No temporary/backup files

2. **Directory Organization**
   - [ ] Source code in `src/`
   - [ ] Tests in `tests/` (no docs)
   - [ ] Scripts in `scripts/`
   - [ ] Examples in `examples/`
   - [ ] Data in `data/`

3. **Git History**
   - [ ] Commits follow conventional format
   - [ ] Scopes used for feat/fix/refactor
   - [ ] Subjects ≤72 characters
   - [ ] Related commits consolidated

4. **Code Quality**
   - [ ] No cache files committed
   - [ ] No print statements
   - [ ] Proper error handling
   - [ ] Tests organized

5. **Documentation**
   - [ ] Guides in `docs/guides/`
   - [ ] Archive organized by date
   - [ ] No documentation in `tests/`

## Red Flags

**Immediate Issues:**
- 100+ markdown files in root
- Documentation mixed with code
- Cache files committed
- No `.gitignore` or incomplete

**Quality Issues:**
- Commits without scopes
- Very long commit subjects (>100 chars)
- Many sequential docs commits
- Print statements in production code

## Recommendations Template

When providing recommendations:

1. **Prioritize:** High/Medium/Low
2. **Be Specific:** Exact file paths, line numbers
3. **Provide Examples:** Show before/after
4. **Explain Why:** Context for recommendations
5. **Actionable:** Clear steps to fix

## Usage

This skill should be loaded when:
- Analyzing repository structure
- Reviewing git history
- Evaluating code organization
- Providing repository improvement recommendations

