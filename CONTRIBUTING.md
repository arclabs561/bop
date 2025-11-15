# Contributing to BOP

## Development Setup

```bash
# Clone the repository
git clone <repo-url>
cd bop

# Install Python dependencies
uv sync --dev

# Install Node.js dependencies (for git hooks)
npm install

# Initialize git hooks (hookwise)
npx husky install
npx hookwise install

# Run tests
uv run pytest

# Run linting
uv run ruff check src/
```

## Git Hooks (Hookwise)

BOP uses [hookwise](https://github.com/arclabs561/hookwise) for commit message validation and documentation bloat detection.

### Commit Messages

Commit messages must follow [Conventional Commits](https://www.conventionalcommits.org/) format:

```
type(scope): subject

Examples:
  feat: add new feature
  fix(judge): handle API errors
  docs: update README
```

### Testing Hooks

**Hookwise now auto-loads `.env`** (built into hookwise):

```bash
# Auto-loads .env automatically - no wrapper needed
npx hookwise test-commit "feat: your message"
npx hookwise test-docs
npx hookwise garden
```

**Or use justfile commands**:

```bash
just hook-test-commit "feat: your message"
just hook-test-docs
just hook-garden
```

**Note**: Both git hooks and CLI commands automatically load `.env` from repo root.

### Configuration

Hooks are configured in `.hookwise.config.mjs`. See `HOOKWISE_DEV_EXPERIENCE_CRITIQUE.md` for details.

## Project Structure

- `src/bop/` - Main package code
  - `cli.py` - CLI interface
  - `agent.py` - Main knowledge agent
  - `schemas.py` - Structured reasoning schemas
  - `research.py` - Deep research integration
  - `eval.py` - Evaluation framework
- `content/` - Knowledge base markdown files
- `tests/` - Test suite

## Adding New Features

1. **Structured Reasoning Schemas**: Add new schemas to `schemas.py`
2. **Research Tools**: Extend `research.py` to integrate new MCP tools
3. **Evaluation Metrics**: Add new evaluation methods to `eval.py`
4. **Constraint-Based Tool Selection**: Extend `constraints.py` to add new tool constraints or optimization objectives
5. **Display Helpers**: Add new formatting functions to `display_helpers.py` for knowledge display
6. **Trust Metrics**: Extend `ContextTopology` in `context_topology.py` for new trust/uncertainty metrics

## Testing

All new features should include tests in `tests/`. Run tests with:

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test suites
uv run pytest tests/test_constraints*.py -v  # Constraint solver tests
uv run pytest tests/test_orchestrator*.py -v  # Orchestrator tests
uv run pytest tests/test_eval*.py -v  # Evaluation tests

# Run E2E tests
uv run pytest tests/test_constraints_e2e.py -v  # Constraint solver E2E
uv run pytest tests/test_integration_full_workflow.py -v  # Full workflow E2E

# Run security/red team tests
uv run pytest tests/test_security_redteam.py -v  # Security tests
./scripts/redteam_quick.sh  # Quick security check
./scripts/redteam_test.sh  # Basic security tests
./scripts/redteam_comprehensive.sh  # Comprehensive security tests
```

## Code Style

- Use `ruff` for linting
- Follow type hints where possible
- Keep functions focused and well-documented

