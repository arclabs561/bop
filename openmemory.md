# BOP Project Memory Guide

## Overview

BOP (Knowledge Structure Research Agent) is a Python CLI/chat interface for deep research and interaction with knowledge structure concepts, LLM reasoning dynamics, and structured reasoning schemas.

## Architecture

### Core Components

- **CLI** (`src/bop/cli.py`) - Main CLI interface using Typer
- **Agent** (`src/bop/agent.py`) - Knowledge agent for research and reasoning
- **Orchestrator** (`src/bop/orchestrator.py`) - Orchestrates MCP tools with structured reasoning
- **Context Topology** (`src/bop/context_topology.py`) - Topological analysis of context (clique complexes, d-separation)
- **Research** (`src/bop/research.py`) - Deep research integration with MCP tools
- **Schemas** (`src/bop/schemas.py`) - Structured reasoning schemas
- **Evaluation** (`src/bop/eval.py`) - Evaluation framework

### Theoretical Foundation

- **Information Geometry**: Fisher Information, attention dilution, statistical manifolds
- **Topological Structure**: Clique complexes, Betti numbers, Euler characteristic
- **Causal Inference**: D-separation, conditional independence, collider bias
- **Dynamical Systems**: Attractor basins, edge-of-chaos dynamics
- **Serial Scaling**: Dependent reasoning chains, computational depth constraints

## Development Tools

### Python Tooling
- **Package Manager**: `uv` (Astral)
- **Linting**: `ruff`
- **Type Checking**: `mypy`
- **Testing**: `pytest`

### Git Hooks (Hookwise)
- **Tool**: `@arclabs561/hookwise` (Node.js)
- **Purpose**: Commit message validation, documentation bloat detection
- **Configuration**: `.hookwise.config.mjs`
- **Setup**: `npm install && npx husky install && npx hookwise install`

### Commit Messages
- **Format**: Conventional Commits
- **Validation**: Automatic via hookwise
- **Testing**: `npx hookwise test-commit "message"`

## User Defined Namespaces

- [Leave blank - user populates]

## Patterns

### Documentation Organization
- Mbopmum 5 markdown files in root directory
- Temporary analysis documents should be archived to `archive/analysis-docs/`
- Archive patterns: `FINAL_*`, `COMPLETE_*`, `ANALYSIS_*`, `CRITIQUE_*`, `INTEGRATION_*`, `TRUST_*`, `*_REVIEW.md`, `*_ANALYSIS.md`, etc.

### Development Workflow
1. Install dependencies: `uv sync --dev` and `npm install`
2. Initialize hooks: `npx husky install && npx hookwise install`
3. Run tests: `uv run pytest`
4. Run linting: `uv run ruff check src/`

## Components

### ContextTopology
- **Location**: `src/bop/context_topology.py`
- **Purpose**: Topological analysis of context structures
- **Key Features**: Clique complexes, d-separation analysis, attractor basin identification
- **Services**: `build_clique_complex()`, `check_d_separation()`, `identify_attractor_basins()`

### StructuredOrchestrator
- **Location**: `src/bop/orchestrator.py`
- **Purpose**: Orchestrates MCP tools with structured reasoning schemas
- **Key Features**: Lazy evaluation, d-separation preservation, topological impact analysis
- **Services**: `research_with_schema()`, `synthesize_results()`

## Implementations

### Hookwise Integration
- **Purpose**: Integrate hookwise for commit validation and doc bloat detection
- **Steps**: 
  1. Create `package.json` with hookwise dependency
  2. Install dependencies: `npm install`
  3. Initialize Husky: `npx husky install`
  4. Install hooks: `npx hookwise install`
  5. Configure: `.hookwise.config.mjs`
- **Key Decisions**: 
  - Use absolute paths in hooks for reliable resolution
  - Remove Husky v8 deprecated lines (husky.sh sourcing)
  - Improve error messages to show actual issues
  - Fix git repository detection to check `.git` directory first
- **Files Modified**: 
  - `hookwise/src/cli.mjs` - Fixed hook installation
  - `hookwise/src/hooks/pre-commit.mjs` - Improved error messages
  - `hookwise/src/hooks/doc-bloat.mjs` - Fixed git detection, improved error output
  - `hookwise/src/cli.mjs` - Improved test-docs output

