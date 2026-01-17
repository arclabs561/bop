# BOP: Knowledge Structure Research Agent
# Command runner using just (https://github.com/casey/just)
#
# Note: .env is automatically loaded by Python code (cli.py, server.py)
# using python-dotenv. No need to manually source it in justfile.

# Default recipe (show available commands)
default:
    @just --list

# ============================================================================
# Development Setup
# ============================================================================

# Install dependencies
install:
    uv sync --dev

# Install with LLM backends
install-llm:
    uv sync --dev --extra llm-all

# Install with constraint solver
install-constraints:
    uv sync --dev --extra constraints

# Install everything
install-all:
    uv sync --dev --extra llm-all --extra constraints

# ============================================================================
# Code Quality
# ============================================================================

# Run linting
lint:
    uv run ruff check src/ tests/ || echo "Note: Install dev dependencies with 'uv sync --dev'"

# Fix linting issues
lint-fix:
    uv run ruff check --fix src/ tests/ || echo "Note: Install dev dependencies with 'uv sync --dev'"

# Type checking
typecheck:
    uv run mypy src/ || echo "Note: Install dev dependencies with 'uv sync --dev'"

# Format code
format:
    uv run ruff format src/ tests/ || echo "Note: Install dev dependencies with 'uv sync --dev'"

# All quality checks
quality: lint typecheck
    @echo "✅ All quality checks passed"

# ============================================================================
# Testing
# ============================================================================

# Run all tests
test:
    uv run pytest tests/ -v

# Run deployment tests (unit tests)
test-deployment:
    uv run pytest tests/test_server_deployment.py tests/test_deployment_scripts.py tests/test_deployment_flow.py -v

# Run deployment e2e tests (requires TEST_DEPLOYMENT=1)
test-deployment-e2e:
    @echo "⚠️  E2E tests require TEST_DEPLOYMENT=1 and flyctl authentication"
    TEST_DEPLOYMENT=1 uv run pytest tests/test_deployment_e2e.py -v -m e2e

# Run server tests
test-server:
    uv run pytest tests/test_server_deployment.py -v

# Run security tests (red team)
test-security:
    uv run pytest tests/test_security_redteam.py -v

# Run Fly.io security tests (requires TEST_DEPLOYMENT=1)
test-security-flyio:
    @echo "⚠️  Requires TEST_DEPLOYMENT=1 and flyctl authentication"
    TEST_DEPLOYMENT=1 uv run pytest tests/test_security_flyio.py -v

# Run persistence tests (requires TEST_DEPLOYMENT=1)
test-persistence:
    @echo "⚠️  Requires TEST_DEPLOYMENT=1 and flyctl authentication"
    TEST_DEPLOYMENT=1 uv run pytest tests/test_persistence_flyio.py -v

# Run comprehensive security tests (shell script)
test-security-comprehensive:
    ./scripts/test_security_comprehensive.sh

# Run all security tests
test-security-all:
    uv run pytest tests/test_security_redteam.py -v
    TEST_DEPLOYMENT=1 uv run pytest tests/test_security_flyio.py -v
    TEST_DEPLOYMENT=1 uv run pytest tests/test_persistence_flyio.py -v

# Run cache tests
test-cache:
    uv run pytest tests/test_cache.py -v

# Setup cache volume (Fly.io)
setup-cache-volume:
    ./scripts/setup_cache_volume.sh

# Run tests by category
test-category CATEGORY:
    uv run python tests/run_all_tests.py --category {{CATEGORY}}

# Run tests by pattern
test-pattern PATTERN:
    uv run python tests/run_all_tests.py --pattern {{PATTERN}}

# Run specific test file
test-file FILE:
    uv run pytest tests/{{FILE}} -v

# List test categories
test-list:
    uv run python tests/run_all_tests.py --list

# Run tests with coverage
test-cov:
    uv run pytest tests/ --cov=src/pran --cov-report=html --cov-report=term

# ============================================================================
# Mutation Testing
# ============================================================================

# Run mutation testing on agent (full run)
# Configuration in pyproject.toml [tool.mutmut]
test-mutate:
    @echo "🧬 Running mutation testing on agent..."
    @echo "⚠️  This may take several minutes"
    uv run mutmut run

# Run mutation testing with HTML report
test-mutate-html:
    @echo "🧬 Running mutation testing with HTML report..."
    uv run mutmut run
    uv run mutmut html
    @echo "📊 HTML report generated in html/mutmut/index.html"

# Show mutation testing results
test-mutate-show:
    uv run mutmut show

# Show specific mutation
test-mutate-show-id ID:
    uv run mutmut show {{ID}}

# Apply specific mutation (for debugging)
test-mutate-apply ID:
    uv run mutmut apply {{ID}}

# Run mutation testing on specific function/method
test-mutate-function FUNCTION:
    @echo "🧬 Running mutation testing on {{FUNCTION}}..."
    uv run mutmut run --function {{FUNCTION}}

# Run mutation testing with coverage (shows which mutations are covered)
test-mutate-cov:
    @echo "🧬 Running mutation testing with coverage analysis..."
    uv run mutmut run --use-coverage
    uv run mutmut html
    @echo "📊 HTML report with coverage in html/mutmut/index.html"

# Quick mutation test (limited mutations)
# Note: Edit max_mutations in pyproject.toml [tool.mutmut] to change limit
test-mutate-quick:
    @echo "🧬 Running quick mutation test (limited mutations)..."
    @echo "⚠️  Edit pyproject.toml [tool.mutmut].max_mutations to change limit (currently 100)"
    uv run mutmut run

# Run visual E2E tests (requires server running)
test-visual:
    npx playwright test tests/test_e2e_visual.mjs

# Run enhanced visual tests with BOP principles
test-visual-enhanced:
    npx playwright test tests/test_e2e_visual_enhanced.mjs

# Run visual regression tests
test-visual-regression:
    npx playwright test tests/test_e2e_visual_regression.mjs

# Run all visual tests (includes visualization tests)
test-visual-all:
    #!/usr/bin/env bash
    set -e
    echo "🧪 Running all visual tests..."
    echo "⚠️  Note: Requires server running on http://localhost:8000"
    npx playwright test tests/test_e2e_visual*.mjs tests/test_visual_comprehensive.mjs tests/accessibility_audit.mjs tests/validate_improvements.mjs tests/test_visualizations_visual.mjs --project=chromium

# Run automated real data analysis
analyze-real-data:
    #!/usr/bin/env bash
    set -e
    echo "📊 Running automated real data analysis..."
    echo "⚠️  Note: Requires API keys (OPENAI_API_KEY or ANTHROPIC_API_KEY) and MCP tools"
    uv run python scripts/run_automated_analysis.py

# Run analysis and generate markdown report
analyze-real-data-report:
    #!/usr/bin/env bash
    set -e
    echo "📊 Running automated analysis with markdown report..."
    uv run python scripts/run_automated_analysis.py --format markdown

# Run visualization feature visual tests
test-visual-viz:
    #!/usr/bin/env bash
    set -e
    echo "🎨 Running visualization feature visual tests..."
    echo "⚠️  Note: Requires server running on http://localhost:8000"
    npx playwright test tests/test_visualizations_visual.mjs --project=chromium

# Run visual tests with UI
test-visual-ui:
    npx playwright test tests/test_e2e_visual.mjs --ui

# Install Playwright browsers
test-visual-install:
    npx playwright install

# ============================================================================
# Running the Agent
# ============================================================================

# Start interactive chat
chat:
    uv run pran chat

# Start chat with research
chat-research:
    uv run pran chat --research

# Start chat with schema
chat-schema SCHEMA:
    uv run pran chat --schema {{SCHEMA}}

# Start chat with constraints
chat-constraints:
    uv run pran chat --constraints

# Start HTTP server
serve:
    uv run pran serve

# Start server with constraints
serve-constraints:
    uv run pran serve --constraints

# ============================================================================
# Evaluation
# ============================================================================

# Run semantic evaluation
eval:
    uv run python scripts/run_semantic_evaluation.py

# Run enhanced semantic evaluation
eval-v2:
    uv run python scripts/run_semantic_evaluation_v2.py

# Run evaluation framework
eval-framework:
    uv run pran eval

# ============================================================================
# Documentation
# ============================================================================

# View test index
docs-test-index:
    @cat tests/TEST_INDEX.md

# View quick start
docs-quick-start:
    @cat tests/QUICK_START.md

# View architecture
docs-arch:
    @cat ARCHITECTURE.md

# View agents guide
docs-agents:
    @cat AGENTS.md

# ============================================================================
# Git Hooks
# ============================================================================

# Test commit message (now auto-loads .env in hookwise)
hook-test-commit MESSAGE:
    npx hookwise test-commit "{{MESSAGE}}"

# Test documentation bloat (now auto-loads .env in hookwise)
hook-test-docs:
    npx hookwise test-docs

# Run all hook checks (now auto-loads .env in hookwise)
hook-garden:
    npx hookwise garden

# ============================================================================
# Deployment
# ============================================================================

# Deploy to Fly.io (includes validation and verification)
deploy:
    ./scripts/deploy_fly.sh

# Validate secrets before deployment
deploy-validate:
    ./scripts/validate_secrets.sh

# Verify deployment after deploy
deploy-verify:
    ./scripts/verify_deployment.sh

# Set Fly.io secrets
deploy-secrets:
    @echo "Setting Fly.io secrets..."
    @echo "Edit this recipe to set your API keys:"
    @echo "flyctl secrets set OPENAI_API_KEY=... -a pran-wispy-voice-3017"
    @echo "flyctl secrets set ANTHROPIC_API_KEY=... -a pran-wispy-voice-3017"
    @echo "flyctl secrets set PERPLEXITY_API_KEY=... -a pran-wispy-voice-3017"
    @echo "flyctl secrets set FIRECRAWL_API_KEY=... -a pran-wispy-voice-3017"
    @echo "flyctl secrets set TAILSCALE_AUTHKEY=... -a pran-wispy-voice-3017"

# View Fly.io logs
deploy-logs:
    flyctl logs -a pran-wispy-voice-3017 --no-tail

# Follow Fly.io logs
deploy-logs-follow:
    flyctl logs -a pran-wispy-voice-3017 -f

# Open Fly.io app
deploy-open:
    flyctl apps open -a pran-wispy-voice-3017

# Check Fly.io status
deploy-status:
    flyctl status -a pran-wispy-voice-3017

# Open Fly.io dashboard
deploy-dashboard:
    flyctl dashboard -a pran-wispy-voice-3017

# Make app private (remove public IPs)
deploy-private:
    ./scripts/make_private.sh

# Test Tailscale setup
test-tailscale:
    ./scripts/test_tailscale.sh

# Test locally
test-local:
    ./scripts/test_local.sh

# Test deployed service
test-deployed:
    ./scripts/test_deployed.sh

# ============================================================================
# Cleanup
# ============================================================================

# Clean Python cache
clean:
    find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
    find . -type d -name ".mypy_cache" -exec rm -r {} + 2>/dev/null || true
    find . -type d -name ".ruff_cache" -exec rm -r {} + 2>/dev/null || true
    @echo "✅ Cleaned Python cache files"

# Clean test artifacts
clean-tests:
    rm -rf .pytest_cache .coverage htmlcov/ 2>/dev/null || true
    @echo "✅ Cleaned test artifacts"

# Clean everything
clean-all: clean clean-tests
    @echo "✅ Cleaned all artifacts"


# Visual Testing
# Note: test-visual-all and test-visual-viz are defined earlier
# This section contains additional visual test commands

test-visual-quick:
    #!/usr/bin/env bash
    set -e
    echo "🧪 Running quick visual validation..."
    echo "⚠️  Note: Requires server running on http://localhost:8000"
    npx playwright test tests/validate_improvements.mjs --project=chromium

test-visual-accessibility:
    #!/usr/bin/env bash
    set -e
    echo "🧪 Running accessibility audit..."
    echo "⚠️  Note: Requires server running on http://localhost:8000"
    npx playwright test tests/accessibility_audit.mjs --project=chromium

visual-improvements:
    #!/usr/bin/env bash
    set -e
    echo "📊 Tracking visual improvements..."
    node tests/visual_improvement_tracker.mjs

visual-analyze:
    #!/usr/bin/env bash
    set -e
    echo "📈 Analyzing visual test results..."
    node tests/analyze_visual_results.mjs

visual-cycle:
    #!/usr/bin/env bash
    set -e
    echo "🔄 Running improvement cycle..."
    ./tests/run_improvement_cycle.sh
