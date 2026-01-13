"""Tests for reasoning schemas."""


from bop.schemas import (
    CHAIN_OF_THOUGHT,
    get_schema,
    hydrate_schema,
    list_schemas,
)


def test_list_schemas():
    """Test listing available schemas."""
    schemas = list_schemas()
    assert len(schemas) > 0
    assert "chain_of_thought" in schemas


def test_get_schema():
    """Test getting a schema by name."""
    schema = get_schema("chain_of_thought")
    assert schema is not None
    assert schema.name == "chain_of_thought"


def test_get_nonexistent_schema():
    """Test getting a nonexistent schema."""
    schema = get_schema("nonexistent")
    assert schema is None


def test_hydrate_schema():
    """Test hydrating a schema with user input."""
    user_input = "Solve 2x + 3 = 7"
    hydrated = hydrate_schema(CHAIN_OF_THOUGHT, user_input)
    assert isinstance(hydrated, dict)
    assert "input_analysis" in hydrated


def test_chain_of_thought_schema():
    """Test chain of thought schema structure."""
    assert CHAIN_OF_THOUGHT.name == "chain_of_thought"
    assert "input_analysis" in CHAIN_OF_THOUGHT.schema_def
    assert len(CHAIN_OF_THOUGHT.examples) > 0

