# Visual E2E Testing with ai-visual-test

This directory contains visual E2E tests using `@arclabs561/ai-visual-test` and Playwright to validate the BOP web UI.

## Overview

Visual tests use AI-powered vision language models (VLLMs) to evaluate screenshots semantically rather than pixel-diffing. This makes tests more robust to content changes and layout shifts.

## Setup

### 1. Link ai-visual-test Package

```bash
npm link ../../dev/ai-visual-test
```

### 2. Install Playwright

```bash
npx playwright install
```

Or use the justfile command:

```bash
just test-visual-install
```

### 3. Configure Environment

Ensure you have a VLLM API key in `.env`:

```bash
# Choose one or more VLLM providers
GEMINI_API_KEY=your-key-here
# or
OPENAI_API_KEY=your-key-here
# or
ANTHROPIC_API_KEY=your-key-here

# Optional: Set VLLM provider explicitly
VLM_PROVIDER=gemini

# Optional: Enable debug logging
DEBUG_VLLM=true
```

### 4. Start the Server

Visual tests require the BOP server to be running:

```bash
# In one terminal
uv run bop serve

# Or with justfile
just serve
```

## Running Tests

### Run All Visual Tests

```bash
just test-visual
```

Or directly:

```bash
npx playwright test tests/test_e2e_visual.mjs
```

### Run with UI

```bash
just test-visual-ui
```

Or directly:

```bash
npx playwright test tests/test_e2e_visual.mjs --ui
```

### Run Specific Test

```bash
npx playwright test tests/test_e2e_visual.mjs -g "chat interface"
```

### Run in Python Test Suite

The Python wrapper (`test_e2e_visual.py`) can be run with pytest:

```bash
pytest tests/test_e2e_visual.py -v
```

Or via the test runner:

```bash
python tests/run_all_tests.py --category visual
```

## Test Coverage

The visual tests cover:

1. **Chat Interface Rendering** - Basic layout, structure, and design quality
2. **Mobile Responsive Layout** - Mobile viewport optimization (375x667)
3. **Dark Mode Rendering** - Dark mode styling and contrast
4. **Message Flow** - Message rendering and chat history
5. **Multi-Modal Validation** - Screenshot + HTML + CSS evaluation with multiple personas
6. **Loading States** - Loading indicators and animations
7. **Error States** - Error message rendering (if applicable)

## Test Structure

### Main Test File

- `test_e2e_visual.mjs` - Playwright tests using ai-visual-test

### Python Wrapper

- `test_e2e_visual.py` - Python wrapper for integration with pytest

## Configuration

### Playwright Config

See `playwright.config.mjs` for:
- Browser configurations (Chromium, Firefox, WebKit, Mobile)
- Timeout settings
- Reporter configuration
- Screenshot/video on failure

### Server URL

Tests use `BOP_SERVER_URL` environment variable (defaults to `http://localhost:8000`):

```bash
BOP_SERVER_URL=http://localhost:8000 npx playwright test tests/test_e2e_visual.mjs
```

## Understanding Results

### Score Interpretation

- **0-10 scale**: Higher is better
- **≥7**: Acceptable quality
- **<7**: Issues detected

### Issues Array

The `issues` array contains specific problems found:
- Accessibility issues (contrast, ARIA labels)
- Design problems (spacing, hierarchy)
- Mobile UX issues (touch targets, responsive layout)

### Multi-Perspective Evaluation

Some tests use multiple personas:
- **Accessibility Advocate**: WCAG compliance, contrast, keyboard navigation
- **Modern UI Designer**: Clean design, spacing, visual hierarchy
- **Mobile UX Expert**: Touch targets, responsive layout, mobile-first design

## Troubleshooting

### Server Not Ready

If tests fail with "Server not ready":
1. Ensure server is running: `uv run bop serve`
2. Check server URL: `BOP_SERVER_URL=http://localhost:8000`
3. Verify health endpoint: `curl http://localhost:8000/health`

### Playwright Not Found

```bash
npx playwright install
```

### ai-visual-test Not Found

```bash
npm link ../../dev/ai-visual-test
```

### VLLM API Errors

1. Check API key in `.env`
2. Verify provider: `VLM_PROVIDER=gemini`
3. Check API quota/limits
4. Enable debug: `DEBUG_VLLM=true`

## Integration with CI/CD

Visual tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Install Playwright
  run: npx playwright install --with-deps

- name: Run Visual Tests
  run: npx playwright test tests/test_e2e_visual.mjs
  env:
    GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
    BOP_SERVER_URL: http://localhost:8000
```

## Best Practices

1. **Run visual tests before UI changes** - Catch regressions early
2. **Review screenshots on failure** - Check `test-results/` directory
3. **Use multi-perspective evaluation** - Get comprehensive feedback
4. **Test on multiple browsers** - Ensure cross-browser compatibility
5. **Test mobile viewports** - Validate responsive design

## Related Documentation

- [ai-visual-test README](../../dev/ai-visual-test/README.md)
- [Playwright Documentation](https://playwright.dev)
- [BOP Server Documentation](../DEPLOYMENT.md)

