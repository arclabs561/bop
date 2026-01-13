"""Pytest configuration and fixtures for test annotations."""

from pathlib import Path

import pytest

from tests.test_annotations import (
    TEST_ANNOTATIONS_REGISTRY,
    export_annotations,
    generate_annotation_report,
)


@pytest.fixture(scope="session", autouse=True)
def export_test_annotations():
    """Export test annotations after all tests run."""
    yield

    # Export annotations
    annotations_file = Path(__file__).parent / "test_annotations.json"
    export_annotations(annotations_file)

    # Generate report
    report_file = Path(__file__).parent / "TEST_ANNOTATIONS_REPORT.md"
    report_file.write_text(generate_annotation_report())


def pytest_collection_modifyitems(config, items):
    """Add annotations as markers to tests."""
    for item in items:
        test_name = item.name
        if test_name in TEST_ANNOTATIONS_REGISTRY:
            ann = TEST_ANNOTATIONS_REGISTRY[test_name]
            # Add markers for filtering
            item.add_marker(pytest.mark.pattern(ann.pattern))
            item.add_marker(pytest.mark.opinion(ann.opinion))
            item.add_marker(pytest.mark.category(ann.category))

