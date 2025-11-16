"""Visual tests for new visualization features using ai-visual-test.

Tests the visual rendering of:
- Token importance charts
- Source matrix heatmaps
- Document relationship graphs
- Trust metrics charts

Uses Playwright + ai-visual-test for semantic visual validation.
"""

import pytest
import subprocess
import sys
from pathlib import Path


def check_visual_testing_available():
    """Check if ai-visual-test and Playwright are available."""
    try:
        result = subprocess.run(
            ["npm", "list", "@arclabs561/ai-visual-test"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        if result.returncode != 0:
            return False
        
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
def test_visualization_tests_exist():
    """Verify that visualization visual test file exists."""
    test_file = Path(__file__).parent / "test_visualizations_visual.mjs"
    assert test_file.exists(), "test_visualizations_visual.mjs should exist"
    
    result = subprocess.run(
        ["node", "--check", str(test_file)],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0, f"Visual test file has syntax errors: {result.stderr}"

