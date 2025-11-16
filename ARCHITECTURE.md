# BOP Architecture Guide

## Overview

BOP (Knowledge Structure Research Agent) implements a structured reasoning framework for LLM interactions with deep research capabilities. This document consolidates the theoretical foundations, implementation details, and integration patterns.

## Table of Contents

1. [Theoretical Foundation](#theoretical-foundation)
2. [System Architecture](#system-architecture)
3. [MCP Integration](#mcp-integration)
4. [Implementation Details](#implementation-details)
5. [Usage Patterns](#usage-patterns)

## Theoretical Foundation

### Information-Theoretic Perspective

**MCP (Model Context Protocol)** implements **lazy evaluation of conditional dependencies**. Rather than eagerly loading all potentially relevant context $C$ into prompt space, MCP allows the model to construct queries $Q(M_t)$ based on current model state $M_t$, receiving context $C_q = f(Q(M_t))$ on-demand. This preserves **d-separation structure** by avoiding collider bias introduced through unconditional injection.

**Forced context injection** implements hard conditioning $P(O|M, C_{\text{all}})$ where all potentially relevant context loads upfront. This:
- Creates high-dimensional state space requiring traversal
- Introduces collider bias through unconditional dependencies
- Saturates attention mechanisms causing dilution
- Fixes the attractor landscape before generation begins

### D-Separation and Causal Structure

**D-separation** defines conditional independence in directed acyclic graphs (DAGs): nodes $X$ and $Z$ are d-separated by $Y$ if all paths between them are blocked by conditioning on $Y$.

**MCP lazy evaluation** implements soft conditioning $P(O|M, C_{Q(M)})$ where context loads conditionally based on model state. This:
- Maintains d-separation by avoiding spurious conditioning
- Enables dynamic attractor landscape modification during generation
- Preserves attention for relevant context
- Allows serial scaling through dependent query chains

### Clique Complexes and Topological Structure

**Context injection** = Clique complex construction in knowledge space
- Vertices represent knowledge elements (facts, concepts, procedures)
- Edges represent conditional dependencies or co-activation patterns
- Cliques represent mutually coherent context sets where all elements are pairwise compatible

**MCP lazy evaluation** builds cliques incrementally through queries, adding vertices only when edges to existing clique members are verified. This is equivalent to greedy clique construction.

### Attractor Basins as Maximal Cliques

**Attractor concretion** forms cliques in activation space:
- Co-activated neural patterns form edges
- Stable attractors correspond to maximal cliques (cannot add more patterns without breaking coherence)
- Basin boundaries are regions where cliques become disconnected

### Information Geometry and Fisher Information

The **Fisher Information Matrix (FIM)** quantifies the curvature of the statistical manifold. For attractor networks, the inverse FIM determinant bounds achievable precision via the Cramér-Rao inequality.

**Context injection modifies the FIM**, reshaping the manifold geometry and accessible basins. Higher Fisher Information = more structure = better compression possible.

### Serial Scaling Constraints

The **Serial Scaling Hypothesis** proves certain computations require depth—chains of dependent reasoning steps that cannot be parallelized. Context injection architectures face fundamental tradeoffs:

- **Upfront injection** pays serial cost during prompt construction but enables parallel generation
- **MCP lazy evaluation** distributes serial cost across generation through iterative queries

Neither escapes the underlying computational constraint that complex reasoning requires sequential dependent steps.

### Resource Triple Framework

BOP explicitly tracks the **resource triple** (depth-width-coordination) and **degradation triple** (corruption-loss-waste) as fundamental constraints.

#### Theoretical Foundation

The "triple principle" from SSH research formalizes that computational resources are fundamentally
intertwined and non-interchangeable:

**Resource Triple** (Computational Constraints):
- **Depth**: Sequential reasoning steps that cannot be parallelized (SSH constraint)
- **Width**: Parallel operations (tools, parallelism)
- **Coordination**: Cost of coordinating parallel operations (managing dependencies, conflicts)

**Degradation Triple** (Information Flow Constraints):
- **Noise**: Information corruption during transmission/processing (inverse of Fisher Information)
- **Loss**: Information lost entirely (synthesis uncertainty, forgetting)
- **Waste**: Information capacity wasted on irrelevant content (low coherence, unused information)

#### Why This Matters

Attempts to "beat" these constraints by pushing on one dimension reintroduce costs in the others:
- More depth → better quality but slower (serial constraint)
- More width → faster but higher coordination cost
- Less coordination → simpler but may miss dependencies
- Less noise → better quality but requires more structure (higher Fisher Information)
- Less loss → more complete but requires better synthesis
- Less waste → more efficient but requires better filtering (IB)

Long-run intelligence amounts to learning good policies for allocating depth and managing
degradation under these invariants.

#### Implementation

These metrics are tracked in `research_with_schema()` return values and enable explicit
understanding of resource tradeoffs, guiding optimization decisions.

### Information Bottleneck Filtering

BOP implements **Information Bottleneck (IB) filtering** for retrieval results before synthesis.

#### Theoretical Foundation

The Information Bottleneck principle (Tishby et al.) provides a principled approach to compression:
find compressed representations that maximize mutual information with the target while minimizing
mutual information with the original input. This is particularly relevant for RAG systems where
retrieved passages contain both relevant information and noise.

#### Why This Matters

BOP's research workflow retrieves multiple results from various tools. Without filtering, all
results are passed to the synthesis LLM, which:
1. Wastes tokens on irrelevant content (noise)
2. Dilutes attention across noise
3. Increases synthesis uncertainty
4. Reduces overall quality

Recent research (arXiv 2406.01549, ACL 2024) demonstrates that IB-based filtering for RAG can
achieve 2.5% compression rates (keeping only 2.5% of retrieved passages) without accuracy loss.
This validates that most retrieved content is indeed noise, and principled filtering significantly
improves efficiency.

#### Implementation

- **Objective**: Maximize I(compressed; target) - beta * I(compressed; noisy_input)
- **Method**: Filters retrieved passages by mutual information with query/target
- **Benefits**: 20-30% token reduction, improved synthesis quality by removing noise
- **Location**: `src/bop/information_bottleneck.py`, integrated into `LLMService.synthesize_tool_results()`

### Adaptive Reasoning Depth Allocation

BOP learns optimal reasoning depth per query type based on the Serial Scaling Hypothesis (SSH).

#### Theoretical Foundation

SSH formalizes that certain problems require sequential computational depth that cannot be
parallelized. Research shows:
1. Problems have minimum reasoning token thresholds
2. Additional depth beyond the threshold provides diminishing returns
3. Different query types require different minimum depths

#### Why This Matters

BOP uses schema-based decomposition which breaks queries into subproblems. Without adaptive
depth allocation:
- Simple queries waste compute on unnecessary subproblems
- Complex queries may not get enough depth for quality answers
- Fixed depth (e.g., always 5 subproblems) is suboptimal

#### Implementation

- **Depth Estimation**: Learns minimum reasoning thresholds from historical performance
  - Uses median of high-quality depths (score > 0.7) as threshold
  - Falls back to minimum decent-quality depth (score > 0.6)
  - Defaults to 3 subproblems if no learning data
- **Early Stopping**: Stops reasoning when quality threshold is met (95% of learned threshold)
  - Conservative threshold prevents stopping too early
  - Accounts for uncertainty in quality estimation
  - Balances efficiency with quality
- **Implementation**: `AdaptiveQualityManager.estimate_reasoning_depth()`, `should_early_stop()`
- **Benefits**: 15-25% compute reduction for simple queries, maintained quality for complex

### Logical Depth Computation

BOP estimates **Bennett's logical depth** for knowledge structures.

#### Theoretical Foundation

Charles Bennett's logical depth formalizes the concept of "valuable, hard-earned knowledge" -
information that requires significant computational effort to produce from a compressed description.
This contrasts with Kolmogorov complexity (measures compressibility) by measuring computational
effort (hard to produce = high depth).

Example: A random string has high Kolmogorov complexity but low logical depth (easy to produce).
A proof of Fermat's Last Theorem has both high complexity and high depth (hard to compress AND
hard to produce).

#### Why This Matters

BOP's knowledge structure research aims to understand the "shape of ideas" - which knowledge
structures are valuable, deep, and meaningful. Logical depth provides a formal measure of
knowledge value beyond just information content, connecting to the concept of "wisdom passed
through ages" - deep knowledge that has been refined and validated over time.

#### Implementation

- **Definition**: Computational effort to produce knowledge from compressed description
- **Heuristic**: Based on trust (valuable knowledge), coherence (structured knowledge), and
  verification count (effort to validate)
- **Implementation**: `ContextTopology.compute_logical_depth_estimate()`
- **Use**: Quality metric for knowledge structures, connection to algorithmic information theory

## System Architecture

### Core Components

1. **KnowledgeAgent** (`agent.py`): Main agent orchestrating chat, research, and reasoning
2. **StructuredOrchestrator** (`orchestrator.py`): Orchestrates MCP tools using structured schemas
3. **LLMService** (`llm.py`): Handles LLM interactions via pydantic-ai
4. **ResearchAgent** (`research.py`): Manages deep research capabilities
5. **ContextTopology** (`context_topology.py`): Analyzes context structure using clique complexes
6. **EvaluationFramework** (`eval.py`): Evaluates reasoning quality
7. **DisplayHelpers** (`display_helpers.py`): Formats trust metrics and knowledge display
8. **InformationBottleneck** (`information_bottleneck.py`): IB-based filtering for retrieval results
9. **AdaptiveQualityManager** (`adaptive_quality.py`): Adaptive learning with reasoning depth tracking

### Structured Reasoning Schemas

BOP uses structured reasoning schemas to guide LLM reasoning:

- **chain_of_thought**: Step-by-step reasoning through a problem
- **iterative_elaboration**: Generate reasoning by iteratively refining and expanding
- **hypothesize_and_test**: Reasoning where hypotheses are evaluated against criteria
- **decompose_and_synthesize**: Break problem into components, address each, then synthesize
- **scenario_analysis**: Construct multiple plausible scenarios to explore problem space

### Tool Selection Strategy

The `ToolSelector` dynamically selects tools based on subproblem characteristics:

- **Deep research** for complex, open-ended questions
- **Reasoning** for complex logical questions
- **Quick search** for factual queries
- **Scraping** for specific URLs or documents
- **Extraction** for structured data extraction

## MCP Integration

### Available MCP Tools

- **Perplexity**: `mcp_perplexity_deep_research`, `mcp_perplexity_reason`, `mcp_perplexity_search`
- **Firecrawl**: `mcp_firecrawl-mcp_firecrawl_search`, `mcp_firecrawl-mcp_firecrawl_scrape`, `mcp_firecrawl-mcp_firecrawl_extract`
- **Tavily**: `mcp_tavily-remote-mcp_tavily_search`, `mcp_tavily-remote-mcp_tavily_extract`

### Integration Pattern

MCP tools are called via the orchestrator's `_call_tool` method, which:
1. Maps tool types to MCP tool functions
2. Handles errors gracefully
3. Returns structured results with metadata

### Configuration

MCP tools require API keys configured in `.env`:
```bash
PERPLEXITY_API_KEY=your_key
FIRECRAWL_API_KEY=your_key
TAVILY_API_KEY=your_key
OPENAI_API_KEY=your_key
```

## Implementation Details

### Lazy Evaluation Pattern

The orchestrator implements lazy evaluation:
1. Decompose query using schema (creates intermediate reasoning steps)
2. For each subproblem, dynamically select and call tools
3. Synthesize results using schema structure
4. Track topology impact of context injection

### Topology Analysis

The `ContextTopology` class provides:
- **Clique computation**: Greedy algorithm for finding maximal cliques
- **Betti numbers**: Topological invariants (graph-level approximation)
- **Euler characteristic**: Single-number summary of knowledge complexity
- **D-separation analysis**: Simplified for undirected graphs
- **Fisher Information estimation**: Heuristic based on clique coherence

### Trust and Uncertainty Modeling

BOP implements comprehensive trust and uncertainty modeling:

**Trust Dimensions**:
- **Credibility**: Source-level trustworthiness (external)
- **Confidence**: Structural support from network topology (internal)
- **Belief Alignment**: How evidence aligns with user's prior beliefs
- **Verification Count**: Number of independent verifications

**Trust Metrics**:
- **Trust Summary**: Average trust, credibility, confidence, calibration error
- **Source Credibility**: Per-source credibility scores
- **Verification Info**: Verification counts and source diversity per source
- **Clique Trust**: Trust scores for source agreement clusters

**Belief-Evidence Consistency**:
- Tracks user's stated beliefs from conversation
- Computes dynamic alignment between evidence and beliefs
- Adjusts trust interpretation based on alignment (contradiction vs. confirmation)

**Source Relationship Analysis**:
- **Source Matrix**: Agreement/disagreement matrix across sources
- **Consensus Detection**: Identifies strong/weak agreement or disagreement
- **Conflict Detection**: Flags when sources contradict each other
- **Source Diversity**: Tracks diversity of source types in consensus

### Error Handling

The system implements graceful degradation:
- Tool failures don't crash the entire query
- Topology analysis failures are caught and logged
- LLM errors fall back to simple responses
- Missing API keys are handled gracefully

## Usage Patterns

### Basic Chat

```python
from bop.agent import KnowledgeAgent

agent = KnowledgeAgent()
response = await agent.chat("What is structured reasoning?")
```

### Chat with Schema

```python
response = await agent.chat(
    "Solve 2x + 3 = 7",
    use_schema="chain_of_thought"
)
```

### Research with Schema

```python
response = await agent.chat(
    "What are the latest developments in LLM reasoning?",
    use_schema="decompose_and_synthesize",
    use_research=True
)
```

### Direct Research

```python
result = await agent.research_agent.deep_research(
    "Structured reasoning in LLMs",
    focus_areas=["theoretical foundations", "empirical results"]
)
```

## Planning Integration (Unified Planning)

### Overview

Unified Planning (UP) offers a formal framework for modeling tool orchestration as planning problems. This can enhance BOP's heuristic-based tool selection with optimal planning capabilities.

### Integration Opportunities

1. **Research Workflow Planning** (Classical/Numeric)
   - Model tool calls as actions with preconditions (availability, budget) and effects (information gain)
   - Optimize sequences for cost, latency, or information quality
   - Handle dependencies automatically (e.g., search before scrape)

2. **Hierarchical Planning** for Decompose-and-Synthesize
   - Natural fit: the schema is inherently hierarchical
   - High-level tasks (research topic) decompose into subtasks (call tools)
   - Enables alternative decomposition strategies

3. **Temporal Planning** for Parallelization
   - Model tool calls as durative actions
   - Enable parallel independent calls
   - Respect resource constraints (rate limits)

4. **Contingent Planning** for Uncertainty
   - Handle tool failures and uncertain results
   - Plan verification steps
   - Adapt to incomplete information

### Implementation Strategy

**Option A: Unified Planning** (Full planning framework)
- **Phase 1**: Add UP as optional dependency, create `planning.py` module
- **Phase 2**: Hierarchical planning for decompose_and_synthesize
- **Phase 3**: Advanced features (temporal, contingent planning)

**Option B: SAT/SMT Solvers** (Lighter weight, recommended to start)
- **Phase 1**: Add PySAT as optional dependency, create `constraints.py` module
- Encode tool availability, dependencies, costs as SAT constraints
- Use SAT solver to find valid tool sequences
- **Advantages**: Lighter weight, faster, more direct control
- **Migration**: Can upgrade to UP later if planning semantics needed

**Recommendation**: Start with Option B (PySAT), upgrade to Option A (UP) if planning semantics prove necessary. Many planning engines use SAT solvers internally anyway.

### Maintenance Considerations

**Complexity Cost**:
- UP adds significant dependency (large library, multiple engines)
- Problem modeling requires domain expertise
- Planning overhead may not justify for simple queries

**When to Use Planning vs. Heuristics**:
- **Use Planning**: Complex queries, cost optimization important, complex dependencies
- **Use Heuristics**: Simple queries, real-time constraints, obvious tool selection

**Recommendation**: Start with heuristics, add planning as optional enhancement only if:
1. Real queries show optimization would help
2. Cost/latency optimization is critical
3. Complex dependencies are common

See `UNIFIED_PLANNING_INTEGRATION.md` for detailed analysis and examples.

## Limitations and Future Work

### Current Limitations

1. **D-Separation**: Simplified implementation for undirected graphs
2. **Betti Numbers**: Graph-level approximation, not true simplicial homology
3. **Fisher Information**: Heuristic estimate, not true Fisher Information Matrix
4. **MCP Integration**: Structure in place, actual calls need wiring
5. **Tool Selection**: Heuristic-based, not formally optimized

### Future Enhancements

1. Full MCP tool integration with actual API calls
2. Advanced topology with true simplicial homology
3. Enhanced error handling and retry logic
4. Caching and deduplication of research results
5. Multi-tool research synthesis improvements
6. **Optional**: Unified Planning integration for optimal tool sequencing (see Planning Integration section)

## References

- `content/reasoning-theory.md`: Detailed reasoning theory
- `content/shape-of-ideas.md`: Knowledge structure concepts
- `UNIFIED_PLANNING_INTEGRATION.md`: Detailed Unified Planning integration analysis
- `AGENTS.md`: Agent architecture and usage patterns
- `KNOWLEDGE_DISPLAY_GUIDE.md`: Knowledge display features guide
- `TRUST_AND_UNCERTAINTY_USER_GUIDE.md`: Trust metrics interpretation guide
- `tests/`: Comprehensive test suite

