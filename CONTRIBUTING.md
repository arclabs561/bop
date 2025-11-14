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

```bash
# Test commit message validation
npx hookwise test-commit "feat: your message"

# Test documentation bloat detection
npx hookwise test-docs

# Run all checks (adhoc)
npx hookwise garden
```

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

## Testing

All new features should include tests in `tests/`. Run tests with:

```bash
uv run pytest tests/ -v
```

## Code Style

- Use `ruff` for linting
- Follow type hints where possible
- Keep functions focused and well-documented

