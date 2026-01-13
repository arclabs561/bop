#!/usr/bin/env python3
"""
Test runner script for discoverable and organized test execution.

Usage:
    python tests/run_all_tests.py                    # Run all tests
    python tests/run_all_tests.py --category quality # Run quality tests
    python tests/run_all_tests.py --pattern integration # Run integration tests
    python tests/run_all_tests.py --list             # List all test categories
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Test categories mapping
TEST_CATEGORIES: Dict[str, List[str]] = {
    "quality": [
        "test_grice_maxims.py",
        "test_semantic_properties.py",
        "test_behavioral_properties.py",
        "test_llm_agent_behavior.py",
        "test_additional_quality_properties.py",
        "test_quality_property_based.py",
        "test_grice_property_based.py",
        "test_behavioral_property_based.py",
    ],
    "property": [
        "test_quality_property_based.py",
        "test_grice_property_based.py",
        "test_behavioral_property_based.py",
        "test_advanced_property_invariants.py",
        "test_custom_property_strategies.py",
        "test_metamorphic_properties.py",
    ],
    "integration": [
        "test_integration_quality_systems.py",
    ],
    "performance": [
        "test_performance_quality_systems.py",
    ],
    "safety": [
        "test_safety_quality_systems.py",
    ],
    "benchmark": [
        "test_benchmark_quality_metrics.py",
    ],
    "regression": [
        "test_regression_quality_systems.py",
    ],
    "framework": [
        "test_comprehensive_evaluation_frameworks.py",
    ],
    "hierarchical": [
        "test_session_manager.py",
        "test_session_manager_edge_cases.py",
        "test_hierarchical_system_interplay.py",
        "test_hierarchical_critical_gaps.py",
        "test_hierarchical_deep_analysis.py",
        "test_hierarchical_hidden_failures.py",
        "test_hierarchical_data_loss_scenarios.py",
    ],
    "multi_turn": [
        "test_multi_turn_sessions.py",
    ],
    "adversarial": [
        "test_adversarial_mcp_driven.py",
    ],
    "core": [
        "test_agent_integration.py",
        "test_quality_feedback.py",
        "test_semantic_eval.py",
        "test_semantic_realistic.py",
    ],
    "mutation": [
        "test_mutation_agent.py",
    ],
    "visual": [
        "test_e2e_visual.py",
    ],
    "visual_viz": [
        "test_visualizations_visual.py",
    ],
    "visual_enhanced": [
        "test_e2e_visual_enhanced.mjs",
    ],
    "visual_regression": [
        "test_e2e_visual_regression.mjs",
    ],
    "visual_comprehensive": [
        "test_visual_comprehensive.mjs",
    ],
    "visual_accessibility": [
        "accessibility_audit.mjs",
    ],
    "visual_validation": [
        "validate_improvements.mjs",
    ],
    "deployment": [
        "test_server_deployment.py",
        "test_deployment_scripts.py",
        "test_deployment_flow.py",
    ],
    "deployment_e2e": [
        "test_deployment_e2e.py",
    ],
    "server": [
        "test_server_deployment.py",
    ],
}

# Test patterns for filtering
TEST_PATTERNS: Dict[str, str] = {
    "quality": "quality",
    "integration": "integration",
    "performance": "performance",
    "safety": "safety",
    "benchmark": "benchmark",
    "regression": "regression",
    "framework": "framework",
    "hierarchical": "hierarchical or session",
    "property": "property",
    "llm_judge": "grice or semantic_properties or behavioral_properties or llm_agent_behavior",
    "mutation": "mutation",
}


def list_categories():
    """List all available test categories."""
    print("Available test categories:")
    print()
    for category, files in TEST_CATEGORIES.items():
        print(f"  {category:15} - {len(files)} test file(s)")
        for file in files:
            print(f"    - {file}")
    print()
    print("Available test patterns:")
    for pattern, keyword in TEST_PATTERNS.items():
        print(f"  {pattern:15} - pytest -k '{keyword}'")


def run_tests(
    category: Optional[str] = None,
    pattern: Optional[str] = None,
    files: Optional[List[str]] = None,
    verbose: bool = True,
    markers: Optional[str] = None,
) -> int:
    """Run tests based on category, pattern, or specific files."""
    tests_dir = Path(__file__).parent

    cmd = ["pytest"]

    if files:
        # Run specific files
        test_files = [str(tests_dir / f) for f in files if (tests_dir / f).exists()]
        if not test_files:
            print(f"Error: No test files found: {files}")
            return 1
        cmd.extend(test_files)
    elif category:
        # Run category
        if category not in TEST_CATEGORIES:
            print(f"Error: Unknown category '{category}'")
            print(f"Available categories: {', '.join(TEST_CATEGORIES.keys())}")
            return 1
        test_files = [str(tests_dir / f) for f in TEST_CATEGORIES[category] if (tests_dir / f).exists()]
        if not test_files:
            print(f"Warning: No test files found for category '{category}'")
            return 1
        cmd.extend(test_files)
    elif pattern:
        # Run pattern
        if pattern not in TEST_PATTERNS:
            print(f"Error: Unknown pattern '{pattern}'")
            print(f"Available patterns: {', '.join(TEST_PATTERNS.keys())}")
            return 1
        cmd.extend(["-k", TEST_PATTERNS[pattern]])
        cmd.append(str(tests_dir))
    else:
        # Run all tests
        cmd.append(str(tests_dir))

    if verbose:
        cmd.append("-v")

    if markers:
        cmd.extend(["-m", markers])

    print(f"Running: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd)
    return result.returncode


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run tests by category, pattern, or specific files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/run_all_tests.py
  python tests/run_all_tests.py --category quality
  python tests/run_all_tests.py --pattern integration
  python tests/run_all_tests.py --files test_grice_maxims.py test_semantic_properties.py
  python tests/run_all_tests.py --list
        """,
    )

    parser.add_argument(
        "--category",
        choices=list(TEST_CATEGORIES.keys()),
        help="Run tests in a specific category",
    )
    parser.add_argument(
        "--pattern",
        choices=list(TEST_PATTERNS.keys()),
        help="Run tests matching a pattern",
    )
    parser.add_argument(
        "--files",
        nargs="+",
        help="Run specific test files",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available test categories and patterns",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Run tests in quiet mode",
    )
    parser.add_argument(
        "--markers",
        help="Run tests with specific markers (e.g., 'llm_judge', 'not slow')",
    )

    args = parser.parse_args()

    if args.list:
        list_categories()
        return 0

    return run_tests(
        category=args.category,
        pattern=args.pattern,
        files=args.files,
        verbose=not args.quiet,
        markers=args.markers,
    )


if __name__ == "__main__":
    sys.exit(main())

