"""Structured reasoning schemas for LLM interactions."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ReasoningSchema(BaseModel):
    """Base class for structured reasoning schemas."""

    model_config = ConfigDict(populate_by_name=True)

    name: str
    description: str
    schema_def: Dict[str, Any] = Field(alias="schema")
    examples: List[Dict[str, Any]] = Field(default_factory=list)


# Common reasoning schemas
CHAIN_OF_THOUGHT = ReasoningSchema(
    name="chain_of_thought",
    description="Step-by-step reasoning through a problem",
    schema_def={
        "input_analysis": "Identify key components or requirements",
        "steps": "Ordered list of reasoning steps",
        "intermediate_results": "Outputs from each step",
        "final_result": "Summary or solution",
    },
    examples=[
        {
            "input": "Solve 2x + 3 = 7",
            "hydrated": {
                "input_analysis": "Equation to solve: 2x + 3 = 7",
                "steps": ["Subtract 3 from both sides", "Divide both sides by 2"],
                "intermediate_results": ["2x = 4", "x = 2"],
                "final_result": "x = 2",
            },
        }
    ],
)

ITERATIVE_ELABORATION = ReasoningSchema(
    name="iterative_elaboration",
    description="Generate reasoning by iteratively refining and expanding",
    schema_def={
        "initial_idea": "First pass at addressing the input",
        "refinements": [
            {
                "iteration": "Number or label for the refinement step",
                "changes": "Details of what was improved",
                "reasoning": "Why these changes were made",
            }
        ],
        "final_result": "Consolidated output after iterations",
    },
)

HYPOTHESIZE_AND_TEST = ReasoningSchema(
    name="hypothesize_and_test",
    description="Reasoning where hypotheses are evaluated against criteria",
    schema_def={
        "hypothesis": "Initial assumption or proposed explanation",
        "evidence": "Relevant facts, data, or observations",
        "tests": "Checks or validations for the hypothesis",
        "outcome": "Results of testing",
        "revision": "New hypothesis if original fails",
    },
)

DECOMPOSE_AND_SYNTHESIZE = ReasoningSchema(
    name="decompose_and_synthesize",
    description="Break problem into components, address each, then synthesize",
    schema_def={
        "decomposition": "Break the problem into smaller parts",
        "subsolutions": "Solutions for each component",
        "synthesis": "Combine subsolutions into cohesive answer",
    },
)

SCENARIO_ANALYSIS = ReasoningSchema(
    name="scenario_analysis",
    description="Construct multiple plausible scenarios to explore problem space",
    schema_def={
        "problem": "Description of the issue or challenge",
        "scenarios": [
            {
                "name": "Name of the scenario",
                "assumptions": "Key assumptions",
                "outcome": "Expected results",
            }
        ],
        "recommended_action": "Best action considering all scenarios",
    },
)

# Registry of all schemas
SCHEMA_REGISTRY: Dict[str, ReasoningSchema] = {
    schema.name: schema
    for schema in [
        CHAIN_OF_THOUGHT,
        ITERATIVE_ELABORATION,
        HYPOTHESIZE_AND_TEST,
        DECOMPOSE_AND_SYNTHESIZE,
        SCENARIO_ANALYSIS,
    ]
}


def get_schema(name: str) -> Optional[ReasoningSchema]:
    """Get a schema by name."""
    return SCHEMA_REGISTRY.get(name)


def list_schemas() -> List[str]:
    """List all available schema names."""
    return list(SCHEMA_REGISTRY.keys())


def hydrate_schema(schema: ReasoningSchema, user_input: str) -> Dict[str, Any]:
    """Create a hydrated schema instance from user input."""
    # This is a placeholder - in practice, this would use an LLM
    # to fill in the schema based on the user input
    hydrated = {}
    for key, description in schema.schema_def.items():
        if isinstance(description, str):
            hydrated[key] = f"[{description}] - to be filled based on: {user_input}"
        elif isinstance(description, list) and description:
            # Handle nested structures
            hydrated[key] = []
    return hydrated

