"""Test annotation system for categorizing tests by patterns and opinions.

This module provides utilities for annotating tests with:
- Patterns: What pattern/behavior is being tested
- Opinions: What opinion/hypothesis is being validated
- Categories: How to group related tests
- Metadata: Additional context about the test
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# Note: This is a utility module, not a test file
# Tests should import from here to annotate themselves


@dataclass
class TestAnnotation:
    """Annotation metadata for a test."""
    pattern: str  # e.g., "multi_turn_conversation", "write_buffering"
    opinion: str  # e.g., "multi_turn_approximates_session", "buffering_reduces_io"
    category: str  # e.g., "conversation_modeling", "performance"
    description: Optional[str] = None
    hypothesis: Optional[str] = None  # What we're testing
    expected_behavior: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# Registry of test annotations
TEST_ANNOTATIONS_REGISTRY: Dict[str, TestAnnotation] = {}


def annotate_test(
    test_name: str,
    pattern: str,
    opinion: str,
    category: str,
    description: Optional[str] = None,
    hypothesis: Optional[str] = None,
    expected_behavior: Optional[str] = None,
    **metadata,
) -> TestAnnotation:
    """
    Annotate a test with pattern, opinion, and category.

    Usage:
        annotation = annotate_test(
            "test_multi_turn_conversation",
            pattern="multi_turn_conversation",
            opinion="multi_turn_approximates_session",
            category="conversation_modeling",
            hypothesis="Multi-turn conversations map to sessions",
        )
    """
    annotation = TestAnnotation(
        pattern=pattern,
        opinion=opinion,
        category=category,
        description=description,
        hypothesis=hypothesis,
        expected_behavior=expected_behavior,
        metadata=metadata,
    )
    TEST_ANNOTATIONS_REGISTRY[test_name] = annotation
    return annotation


def get_tests_by_pattern(pattern: str) -> List[str]:
    """Get all test names that test a specific pattern."""
    return [
        name for name, ann in TEST_ANNOTATIONS_REGISTRY.items()
        if ann.pattern == pattern
    ]


def get_tests_by_opinion(opinion: str) -> List[str]:
    """Get all test names that validate a specific opinion."""
    return [
        name for name, ann in TEST_ANNOTATIONS_REGISTRY.items()
        if ann.opinion == opinion
    ]


def get_tests_by_category(category: str) -> List[str]:
    """Get all test names in a specific category."""
    return [
        name for name, ann in TEST_ANNOTATIONS_REGISTRY.items()
        if ann.category == category
    ]


def export_annotations(output_path: Path) -> None:
    """Export all annotations to JSON file."""
    data = {
        name: {
            "pattern": ann.pattern,
            "opinion": ann.opinion,
            "category": ann.category,
            "description": ann.description,
            "hypothesis": ann.hypothesis,
            "expected_behavior": ann.expected_behavior,
            "metadata": ann.metadata,
        }
        for name, ann in TEST_ANNOTATIONS_REGISTRY.items()
    }
    output_path.write_text(json.dumps(data, indent=2))


def load_annotations(input_path: Path) -> None:
    """Load annotations from JSON file."""
    data = json.loads(input_path.read_text())
    for name, ann_data in data.items():
        TEST_ANNOTATIONS_REGISTRY[name] = TestAnnotation(**ann_data)


def generate_annotation_report() -> str:
    """Generate a report of all annotations."""
    lines = ["# Test Annotations Report\n"]

    # Group by category
    categories = {}
    for name, ann in TEST_ANNOTATIONS_REGISTRY.items():
        if ann.category not in categories:
            categories[ann.category] = []
        categories[ann.category].append((name, ann))

    for category, tests in sorted(categories.items()):
        lines.append(f"## {category}\n")
        for name, ann in tests:
            lines.append(f"### {name}")
            lines.append(f"- **Pattern**: {ann.pattern}")
            lines.append(f"- **Opinion**: {ann.opinion}")
            if ann.hypothesis:
                lines.append(f"- **Hypothesis**: {ann.hypothesis}")
            if ann.description:
                lines.append(f"- **Description**: {ann.description}")
            lines.append("")

    return "\n".join(lines)


# Example annotations for existing patterns
annotate_test(
    "test_multi_turn_conversation_as_session",
    pattern="multi_turn_conversation",
    opinion="multi_turn_approximates_session",
    category="conversation_modeling",
    hypothesis="Multi-turn conversations map to sessions",
    description="Each conversation turn adds an evaluation to the session",
)

annotate_test(
    "test_write_buffer_failure_recovery",
    pattern="write_buffering",
    opinion="buffering_handles_failures_gracefully",
    category="error_handling",
    hypothesis="Write buffer should handle failures without crashing",
)

annotate_test(
    "test_session_with_many_evaluations",
    pattern="session_complexity",
    opinion="sessions_scale_to_many_evaluations",
    category="scalability",
    hypothesis="Sessions can handle 100+ evaluations efficiently",
)

annotate_test(
    "test_blank_slate_session",
    pattern="session_initialization",
    opinion="empty_sessions_work_correctly",
    category="edge_cases",
    hypothesis="Empty sessions should have valid statistics and state",
)

annotate_test(
    "test_cross_session_learning",
    pattern="adaptive_learning",
    opinion="learning_transfers_across_sessions",
    category="adaptive_learning",
    hypothesis="Patterns learned in one session improve next session",
)

