"""Comprehensive tests for all schemas."""

import pytest
from bop.schemas import (
    list_schemas,
    get_schema,
    hydrate_schema,
    CHAIN_OF_THOUGHT,
    ITERATIVE_ELABORATION,
    HYPOTHESIZE_AND_TEST,
    DECOMPOSE_AND_SYNTHESIZE,
    SCENARIO_ANALYSIS,
)


def test_all_schemas_listed():
    """Test that all schemas are in the list."""
    schemas = list_schemas()
    
    expected = [
        "chain_of_thought",
        "iterative_elaboration",
        "hypothesize_and_test",
        "decompose_and_synthesize",
        "scenario_analysis",
    ]
    
    for schema_name in expected:
        assert schema_name in schemas


def test_all_schemas_retrievable():
    """Test that all schemas can be retrieved."""
    schemas = list_schemas()
    
    for schema_name in schemas:
        schema = get_schema(schema_name)
        assert schema is not None
        assert schema.name == schema_name
        assert schema.description is not None
        assert schema.schema_def is not None


def test_all_schemas_hydratable():
    """Test that all schemas can be hydrated."""
    schemas = list_schemas()
    test_input = "What is knowledge structure?"
    
    for schema_name in schemas:
        schema = get_schema(schema_name)
        hydrated = hydrate_schema(schema, test_input)
        
        assert hydrated is not None
        assert isinstance(hydrated, dict)


def test_schema_structure_consistency():
    """Test that all schemas have consistent structure."""
    schemas = list_schemas()
    
    for schema_name in schemas:
        schema = get_schema(schema_name)
        
        # All should have required fields
        assert hasattr(schema, "name")
        assert hasattr(schema, "description")
        assert hasattr(schema, "schema_def")
        
        # Schema def should be a dict
        assert isinstance(schema.schema_def, dict)
        assert len(schema.schema_def) > 0


def test_schema_examples():
    """Test that schemas with examples work correctly."""
    # Chain of thought should have examples
    schema = get_schema("chain_of_thought")
    assert schema is not None
    
    # Check if examples are in schema_def
    if "examples" in schema.schema_def:
        examples = schema.schema_def["examples"]
        assert isinstance(examples, list)


def test_schema_edge_cases():
    """Test schemas with edge case inputs."""
    schemas = list_schemas()
    
    edge_inputs = [
        "",  # Empty
        "a" * 1000,  # Very long
        "!@#$%^&*()",  # Special characters
    ]
    
    for schema_name in schemas:
        schema = get_schema(schema_name)
        for edge_input in edge_inputs:
            # Should not crash
            hydrated = hydrate_schema(schema, edge_input)
            assert hydrated is not None


def test_schema_comparison():
    """Test comparing different schemas."""
    cot = get_schema("chain_of_thought")
    das = get_schema("decompose_and_synthesize")
    
    assert cot.name != das.name
    assert cot.description != das.description
    
    # Schema defs should be different
    assert cot.schema_def != das.schema_def


def test_schema_immutability():
    """Test that schema objects are not accidentally modified."""
    schema = get_schema("chain_of_thought")
    original_def = schema.schema_def.copy()
    
    # Try to modify (should not affect original)
    hydrated = hydrate_schema(schema, "test")
    
    # Schema def should be unchanged
    assert schema.schema_def == original_def

