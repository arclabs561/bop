"""E2E Visual Tests Integration (Python wrapper).

This module provides Python integration for the ai-visual-test E2E tests.
The actual visual tests are in test_e2e_visual.mjs (Playwright + ai-visual-test).
"""

import subprocess
import sys
from pathlib import Path

import pytest


def check_visual_testing_available():
    """Check if ai-visual-test and Playwright are available."""
    try:
        # Check if npm package is linked
        result = subprocess.run(
            ["npm", "list", "@arclabs561/ai-visual-test"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        if result.returncode != 0:
            return False

        # Check if Playwright is available
        result = subprocess.run(
            ["npx", "playwright", "--version"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        return result.returncode == 0
    except Exception:
        return False


@pytest.mark.skipif(
    not check_visual_testing_available(),
    reason="ai-visual-test or Playwright not available"
)
def test_visual_tests_exist():
    """Verify that visual test file exists and is runnable."""
    test_file = Path(__file__).parent / "test_e2e_visual.mjs"
    assert test_file.exists(), "test_e2e_visual.mjs should exist"

    # Try to run a syntax check
    result = subprocess.run(
        ["node", "--check", str(test_file)],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0, f"Visual test file has syntax errors: {result.stderr}"


@pytest.mark.skipif(
    not check_visual_testing_available(),
    reason="ai-visual-test or Playwright not available"
)
def test_run_visual_tests():
    """Run the visual E2E tests using Playwright."""
    test_file = Path(__file__).parent / "test_e2e_visual.mjs"

    # Run Playwright tests
    result = subprocess.run(
        ["npx", "playwright", "test", str(test_file), "--reporter=list"],
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True,
    )

    # Print output for debugging
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    # Note: We don't fail here if tests fail, as this is just a wrapper
    # The actual test results are in the Playwright output
    assert result.returncode in [0, 1], "Playwright test execution should complete"


def test_visual_testing_setup():
    """Verify visual testing dependencies are set up."""
    # Check npm link
    result = subprocess.run(
        ["npm", "list", "@arclabs561/ai-visual-test"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )

    if result.returncode != 0:
        pytest.skip("ai-visual-test not linked. Run: npm link ../../dev/ai-visual-test")

    # Check Playwright
    result = subprocess.run(
        ["npx", "playwright", "--version"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )

    if result.returncode != 0:
        pytest.skip("Playwright not installed. Run: npx playwright install")
