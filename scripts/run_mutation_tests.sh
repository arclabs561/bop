#!/bin/bash
# Wrapper script for mutmut to handle Python path correctly
# Mutmut changes to mutants/ directory, so we need to adjust paths
set -e

# Get the project root directory (parent of mutants/)
if [ -d "mutants" ]; then
    # We're in the mutants directory
    PROJECT_ROOT="$(cd .. && pwd)"
    cd "$PROJECT_ROOT"
else
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    cd "$PROJECT_ROOT"
fi

# Set PYTHONPATH to include project root and src
export PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/src:$PYTHONPATH"

# Run pytest with specific test files only
# Use --ignore to skip mutants directory and problematic test files
exec uv run pytest \
    "$PROJECT_ROOT/tests/test_agent.py" \
    "$PROJECT_ROOT/tests/test_agent_integration.py" \
    "$PROJECT_ROOT/tests/test_agent_comprehensive.py" \
    "$PROJECT_ROOT/tests/test_mutation_agent.py" \
    --ignore="$PROJECT_ROOT/mutants" \
    --ignore-glob="*/test_adaptive_quality.py" \
    -x \
    "$@"

