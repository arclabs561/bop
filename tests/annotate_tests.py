#!/usr/bin/env python3
"""Helper script to annotate tests with patterns, opinions, and categories."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_annotations import (
    TEST_ANNOTATIONS_REGISTRY,
    export_annotations,
    generate_annotation_report,
    get_tests_by_category,
    get_tests_by_opinion,
    get_tests_by_pattern,
)


def main():
    """Interactive annotation helper."""
    if len(sys.argv) < 2:
        print("Usage: python annotate_tests.py <command> [args]")
        print("\nCommands:")
        print("  list                    - List all annotations")
        print("  report                  - Generate annotation report")
        print("  by-pattern <pattern>    - List tests for pattern")
        print("  by-opinion <opinion>    - List tests for opinion")
        print("  by-category <category>  - List tests for category")
        print("  export                  - Export annotations to JSON")
        return

    command = sys.argv[1]

    if command == "list":
        print(f"Total Annotated Tests: {len(TEST_ANNOTATIONS_REGISTRY)}")
        for name, ann in sorted(TEST_ANNOTATIONS_REGISTRY.items()):
            print(f"\n{name}:")
            print(f"  Pattern: {ann.pattern}")
            print(f"  Opinion: {ann.opinion}")
            print(f"  Category: {ann.category}")
            if ann.hypothesis:
                print(f"  Hypothesis: {ann.hypothesis}")

    elif command == "report":
        print(generate_annotation_report())

    elif command == "by-pattern":
        if len(sys.argv) < 3:
            print("Usage: annotate_tests.py by-pattern <pattern>")
            return
        pattern = sys.argv[2]
        tests = get_tests_by_pattern(pattern)
        print(f"Tests for pattern '{pattern}': {len(tests)}")
        for test in tests:
            print(f"  - {test}")

    elif command == "by-opinion":
        if len(sys.argv) < 3:
            print("Usage: annotate_tests.py by-opinion <opinion>")
            return
        opinion = sys.argv[2]
        tests = get_tests_by_opinion(opinion)
        print(f"Tests for opinion '{opinion}': {len(tests)}")
        for test in tests:
            print(f"  - {test}")

    elif command == "by-category":
        if len(sys.argv) < 3:
            print("Usage: annotate_tests.py by-category <category>")
            return
        category = sys.argv[2]
        tests = get_tests_by_category(category)
        print(f"Tests for category '{category}': {len(tests)}")
        for test in tests:
            print(f"  - {test}")

    elif command == "export":
        output_path = Path("tests/test_annotations.json")
        export_annotations(output_path)
        print(f"Exported {len(TEST_ANNOTATIONS_REGISTRY)} annotations to {output_path}")

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()

