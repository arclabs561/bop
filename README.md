# BOP: Knowledge Structure Research Agent

A CLI/chat interface for deep research and interaction with knowledge structure concepts, LLM reasoning dynamics, and structured reasoning schemas.

## What BOP Does

BOP helps you explore the "shape of ideas" by conducting deep research, analyzing knowledge structures, and providing transparent, evidence-based answers with trust metrics and source provenance.

**By using BOP, you can**:
- ✅ **Conduct deep research** across multiple sources with automatic synthesis
- ✅ **Understand knowledge structures** through topological analysis (cliques, d-separation, attractor basins)
- ✅ **Get transparent answers** with trust scores, source credibility, and provenance traces
- ✅ **Track belief-evidence alignment** when you state your prior beliefs
- ✅ **Adaptive responses** that adjust detail level based on your query patterns

**Example output**:
```
📋 Summary: Trust in knowledge systems depends on source credibility...

📊 Trust & Uncertainty Metrics
Average Trust: 0.73 | Calibration Error: 0.12
Source Credibility: [arxiv.org: 0.85, wikipedia.org: 0.72, ...]

🔗 Source Agreement Clusters
Cluster 1: 5 sources agree (trust: 0.78)
```

**Time to value**: ~2 minutes from installation to first research query.

---

## Overview

This project explores the "shape of ideas" across philosophical traditions and implements structured reasoning frameworks for LLM interactions. It provides:

- **Deep research capabilities** via MCP tools (Perplexity, Firecrawl, etc.)
- **Structured reasoning schemas** for improved LLM reasoning
- **Evaluation framework** for reasoning quality assessment
- **CLI/chat interface** for interactive exploration

## Automated Analysis

BOP includes an automated real data analysis pipeline that runs real queries with research enabled and performs rigorous statistical analysis on trust metrics, source matrices, and topology data.

### Run Analysis

```bash
# Run with default queries
just analyze-real-data

# Run with custom queries file
uv run python scripts/run_automated_analysis.py --queries-file scripts/queries_for_analysis.json

# Generate markdown report
uv run python scripts/run_automated_analysis.py --format markdown
```

### Analysis Output

Reports are saved to `analysis_output/` with:
- Trust distribution analysis (correlation between credibility and verifications)
- Clique analysis (coherent source clusters)
- Source agreement matrices (consensus vs. disagreement)
- Calibration error analysis (confidence calibration)

The analysis runs automatically:
- Daily via GitHub Actions (if configured)
- On-demand via `just analyze-real-data`
- After evaluation runs

## Quick Start (2 minutes)

### Minimal Setup

```bash
# 1. Install dependencies
uv sync --extra llm-anthropic  # Or llm-openai, llm-google, or llm-all

# 2. Configure API keys
cp .env.example .env
# Edit .env and add at least one: OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY

# 3. Start chatting
uv run bop chat
```

**What this does**: Starts an interactive chat where you can ask questions and get research-backed answers with trust metrics.

### First Query

Once in the chat, try:
```
> What is the shape of ideas?
```

BOP will:
1. Conduct research across multiple sources
2. Synthesize findings with trust metrics
3. Show source credibility and agreement clusters
4. Provide progressive disclosure (summary → detailed → evidence)

### Choose Your Path

**New to BOP?**
→ Follow [Quick Start](#quick-start-2-minutes) above
→ Then read [AGENTS.md](AGENTS.md) for detailed usage

**Familiar with research tools?**
→ Jump to [Quick Example](#quick-example) below
→ See [AGENTS.md](AGENTS.md) for advanced patterns

**Want to deploy as a service?**
→ See [QUICK_START_SERVICE.md](QUICK_START_SERVICE.md) for HTTP server setup
→ Or [PRODUCTION_SETUP.md](PRODUCTION_SETUP.md) for full deployment

---

## Installation Options

### Basic Installation

```bash
# Install dependencies
uv sync

# Install with LLM backend support (choose one or more)
uv sync --extra llm-openai      # OpenAI support
uv sync --extra llm-anthropic   # Anthropic support (best quality)
uv sync --extra llm-google      # Google/Gemini support
uv sync --extra llm-all         # All LLM backends (includes Groq for speed)

# Install with optional constraint solver (for optimal tool selection)
uv sync --extra constraints

# Configure your .env file with API keys
cp .env.example .env
# Edit .env and add your API keys
```

### Running BOP

```bash
# Interactive CLI chat
uv run bop chat

# With research enabled
uv run bop chat --research

# With specific schema
uv run bop chat --schema decompose_and_synthesize

# Start HTTP server for remote access (e.g., via Tailscale)
uv run bop serve --constraints

# Run evaluations
uv run bop eval

# View quality performance
uv run bop quality

# Manage sessions
uv run bop sessions --list
```

### Using Justfile (Recommended)

If you have [just](https://github.com/casey/just) installed:

```bash
# Show all available commands
just

# Install everything
just install-all

# Run tests
just test

# Start chat
just chat

# Run evaluations
just eval

# View documentation
just docs-arch
just docs-agents
```

See `justfile` for all available commands.


## Project Structure

```
bop/
├── src/
│   ├── bop/
│   │   ├── cli.py          # CLI interface
│   │   ├── agent.py         # Research agent
│   │   ├── schemas.py       # Reasoning schemas
│   │   ├── eval.py          # Evaluation framework
│   │   └── research.py      # Deep research integration
│   └── ...
├── content/                 # Knowledge base content
│   ├── shape-of-ideas.md
│   ├── reasoning-theory.md
│   └── schemas/
├── tests/
├── pyproject.toml
└── README.md
```

## Features

- **Structured Reasoning**: JSON-based schemas that guide LLM reasoning
- **Deep Research**: Integration with Perplexity, Firecrawl, and other research tools
- **Topological Analysis**: Clique complexes, d-separation, and information geometry
- **MCP Lazy Evaluation**: Preserves causal structure by avoiding collider bias
- **Attractor Basin Tracking**: Identifies stable knowledge structures
- **Trust Transparency**: Source credibility scores, calibration metrics, verification counts
- **Belief-Evidence Alignment**: Tracks user beliefs and aligns evidence accordingly
- **Progressive Disclosure**: Summary → structured → detailed → evidence tiers
- **Source Provenance**: Source references and agreement/disagreement matrices
- **Context-Adaptive Responses**: Adapts detail level based on query patterns
- **Evaluation**: Comprehensive evaluation framework for reasoning quality
- **Extensible**: Modular design for easy extension

## Quick Example

**Problem**: You want to understand how uncertainty affects trust in knowledge systems, and you have a prior belief that trust is crucial.

**Solution**: Use BOP to research this question with belief-evidence alignment.

```python
from bop.agent import KnowledgeAgent

agent = KnowledgeAgent(enable_quality_feedback=True)
response = await agent.chat(
    "I think trust is crucial for knowledge systems. How does uncertainty affect it?",
    use_schema="decompose_and_synthesize",
    use_research=True,
)

# Progressive disclosure: start with summary
print(response["response_tiers"]["summary"])  # 1-2 sentence overview
print(response["response_tiers"]["detailed"])   # Full response with evidence

# Access trust metrics
if response.get("research"):
    topology = response["research"]["topology"]
    print(f"Average Trust: {topology['trust_summary']['avg_trust']:.2f}")
    print(f"Source Credibility: {topology['source_credibility']}")
    
    # View source agreement clusters (which sources agree)
    for clique in topology["cliques"][:3]:
        print(f"Sources agree: {clique['node_sources']}, Trust: {clique['trust']:.2f}")

# Check if your beliefs were extracted and aligned
if response.get("prior_beliefs"):
    print("Your beliefs:", response["prior_beliefs"])
    # Belief-evidence alignment is computed automatically
```

**What you get**:
- Research synthesis from multiple sources
- Trust scores showing source credibility
- Source agreement clusters (which sources agree/disagree)
- Belief-evidence alignment (how evidence matches your stated beliefs)
- Progressive disclosure (summary → detailed → evidence tiers)

## Theoretical Foundation

BOP implements a rigorous theoretical framework combining:

- **Information Geometry**: Fisher Information, attention dilution, statistical manifolds
- **Topological Structure**: Clique complexes, Betti numbers, Euler characteristic
- **Causal Inference**: D-separation, conditional independence, collider bias
- **Dynamical Systems**: Attractor basins, edge-of-chaos dynamics, Class 4 CA
- **Serial Scaling**: Dependent reasoning chains, computational depth constraints

See `ARCHITECTURE.md` for detailed mathematical foundations and implementation details.

## Development

See `CONTRIBUTING.md` for development guidelines.

## Architecture

See `ARCHITECTURE.md` for detailed architecture documentation, theoretical foundations, and implementation details.

## Agent Architecture

See `AGENTS.md` for comprehensive documentation on the agent components, their interactions, and usage patterns.

## Knowledge Display

See `KNOWLEDGE_DISPLAY_GUIDE.md` for a guide to trust metrics, source credibility, and progressive disclosure features.

## Trust and Uncertainty

See `TRUST_AND_UNCERTAINTY_USER_GUIDE.md` for interpreting trust scores, calibration error, and source credibility.

## Testing

BOP includes comprehensive testing including visual UI testing and mutation testing:

```bash
# Run all tests
just test

# Run mutation testing (evaluate test quality)
just test-mutate-quick

# Run visual tests (requires server running)
just test-visual-all

# Run quick visual validation
just test-visual-quick

# Run accessibility audit
just test-visual-accessibility

# Track visual improvements
just visual-improvements

# Analyze visual test results
just visual-analyze

# Run improvement cycle
just visual-cycle
```

See `tests/VISUAL_TESTING_COMPLETE.md` for complete visual testing framework documentation.

## Migration

See `MIGRATION_GUIDE.md` if you're upgrading from an earlier version.

## Planning Integration (Optional)

BOP supports optional integration with Unified Planning for optimal tool orchestration. See:
- `UNIFIED_PLANNING_INTEGRATION.md` - Detailed integration analysis and examples
- `MAINTENANCE_ANALYSIS.md` - Maintenance implications and recommendations

