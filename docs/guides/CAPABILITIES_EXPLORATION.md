# BOP Capabilities Exploration

A comprehensive guide to understanding how BOP works, what tools it has, how it's evaluated, and what capabilities it offers.

## How It Works

### Core Architecture Flow

```
User Query
    ↓
KnowledgeAgent.chat()
    ↓
├─→ Extract Prior Beliefs (if user states "I think...")
├─→ Track Recent Query (for context adaptation)
├─→ Schema Selection (AdaptiveQualityManager recommends best schema)
├─→ Context-Dependent Adaptation (exploration vs extraction mode)
├─→ Research (if enabled)
│   ├─→ StructuredOrchestrator.research_with_schema()
│   │   ├─→ Decompose query into subproblems (LLM-based)
│   │   ├─→ For each subproblem:
│   │   │   ├─→ Tool Selection (heuristic or constraint-based)
│   │   │   ├─→ MCP Tool Calls (Perplexity, Firecrawl, Tavily, etc.)
│   │   │   ├─→ Information Bottleneck Filtering (removes noise)
│   │   │   ├─→ Create Context Nodes (with trust/uncertainty)
│   │   │   ├─→ Topology Analysis (clique computation)
│   │   │   └─→ Synthesize subsolution
│   │   └─→ Final Synthesis (combine all subsolutions)
│   └─→ Topology Metrics (trust, credibility, cliques, calibration)
├─→ LLM Response Generation (with length adaptation)
├─→ Add Source References (provenance matching)
├─→ Create Response Tiers (summary → structured → detailed → evidence)
└─→ Quality Evaluation (QualityFeedbackLoop)
    └─→ Adaptive Learning Update (AdaptiveQualityManager)
```

### Key Mechanisms

**1. Lazy Evaluation (MCP Pattern)**
- Preserves d-separation by avoiding collider bias
- Tools called conditionally based on model state, not upfront
- Enables dynamic attractor landscape modification during generation
- Prevents attention dilution from premature context injection

**2. Information Bottleneck Filtering**
- **Objective**: Maximize I(compressed; target) - beta * I(compressed; original)
- **Method**: Filters retrieved passages by mutual information with query/target
- **Implementation**: Uses semantic similarity as proxy for mutual information
- **Threshold**: min_mi=0.3 (filters out low-relevance results)
- **Deduplication**: Removes redundant results (>70% similarity)
- **Benefits**: 20-30% token reduction, improved synthesis quality
- **Research Basis**: arXiv 2406.01549, ACL 2024 - shows 2.5% compression possible
- **Location**: `src/bop/information_bottleneck.py`, integrated into `LLMService.synthesize_tool_results()`

**3. Topological Analysis**
- **Clique Complexes**: Finds coherent source clusters (maximal cliques)
  - Greedy algorithm (exact clique-finding is NP-complete)
  - Trust-aware: tracks credibility, confidence, trust scores
  - Coherence scoring: measures how well nodes fit together
- **D-Separation**: Preserves causal structure in knowledge graphs
  - Avoids collider bias through conditional independence
  - Simplified implementation for undirected graphs
  - Trust-weighted: low-trust paths considered blocked
- **Attractor Basins**: Maximal cliques as stable knowledge structures
  - Represents stable patterns in knowledge space
  - Trust-weighted: high-trust cliques are more reliable
- **Fisher Information**: Estimates structure quality (heuristic)
  - Not true FIM, but heuristic based on clique coherence
  - Higher Fisher Information = more structure = better compression
- **Euler Characteristic**: Single-number summary of knowledge complexity
  - Graph-level approximation
  - Provides topological invariant for knowledge structures

**4. Trust and Uncertainty Modeling**
- **Credibility**: Source-level trustworthiness (external)
- **Confidence**: Structural support from network topology (internal)
- **Epistemic Uncertainty**: Reducible uncertainty (what we don't know)
- **Aleatoric Uncertainty**: Irreducible randomness
- **Belief Alignment**: How evidence aligns with user's prior beliefs
- **Calibration Error**: Measures how well confidence matches accuracy (ECE)

**5. Adaptive Learning**
- Learns optimal schemas per query type (factual, procedural, analytical, etc.)
- Learns optimal response lengths per query type
- Learns when research helps vs. hurts quality
- Learns reasoning depth thresholds (minimum subproblems needed)
- Early stopping when quality threshold is met

**6. Progressive Disclosure**
- **Summary**: 1-2 sentence overview
- **Structured**: Organized breakdown
- **Detailed**: Full response with evidence
- **Evidence**: Complete research synthesis

## Available Tools

### MCP Tools Integrated

BOP integrates with 8 MCP tools across 4 providers:

**Perplexity** (3 tools):
- `mcp_perplexity_deep_research`: Deep research with focus areas
- `mcp_perplexity_reason`: Complex reasoning queries
- `mcp_perplexity_search`: Quick factual search

**Firecrawl** (3 tools):
- `mcp_firecrawl-mcp_firecrawl_search`: Web search
- `mcp_firecrawl-mcp_firecrawl_scrape`: Scrape specific URLs
- `mcp_firecrawl-mcp_firecrawl_extract`: Structured data extraction

**Tavily** (2 tools):
- `mcp_tavily-remote-mcp_tavily_search`: Web search
- `mcp_tavily-remote-mcp_tavily_extract`: Content extraction

**Note**: arXiv and Kagi are mentioned in documentation but not currently in the `ToolType` enum. They may be available via MCP but aren't integrated into the orchestrator's tool selection yet.

### Tool Selection Strategy

**Heuristic Selection** (default):
- Deep research → `PERPLEXITY_DEEP`
- Reasoning queries → `PERPLEXITY_REASON`
- Factual queries → `PERPLEXITY_SEARCH` + `TAVILY_SEARCH`
- URLs → `FIRECRAWL_SCRAPE`
- Structured extraction → `FIRECRAWL_EXTRACT` + `TAVILY_EXTRACT`

**Constraint-Based Selection** (optional):
- Uses PySAT solver to optimize tool selection
- Minimizes cost while meeting information requirements
- Handles dependencies (e.g., search before scrape)
- Enforces budget constraints
- Falls back to heuristics if no solution found

**MUSE-Based Selection** (optional):
- Uncertainty-aware tool selection
- Maximizes diversity while minimizing epistemic uncertainty
- Uses aleatoric weighting for result aggregation

### Tool Call Flow

1. **Tool Mapping**: `ToolType` enum → MCP tool name + parameters
2. **Caching**: Check cache first (reduces API calls)
3. **MCP Call**: Call actual MCP tool function
4. **Error Handling**: Graceful fallback if tool fails
5. **Result Processing**: Extract sources, content, metadata
6. **Context Node Creation**: Convert to `ContextNode` with trust/uncertainty

## Evaluation Frameworks

### Built-in Evaluation

**1. EvaluationFramework** (`src/bop/eval.py`):
- Schema usage evaluation
- Reasoning coherence evaluation
- Response quality assessment
- Test case validation

**2. SemanticEvaluator** (`src/bop/semantic_eval.py`):
- Semantic similarity evaluation
- Concept extraction and matching
- Relevance scoring
- Quality flag detection

**3. QualityFeedbackLoop** (`src/bop/quality_feedback.py`):
- Continuous quality evaluation
- Hierarchical session management
- Quality flag detection (placeholders, errors, repetition)
- Adaptive learning integration

### External Datasets

**Working Datasets**:
- **HotpotQA**: Multi-document QA (113k questions)
- **Calibration Ground Truth**: Synthetic calibration scenarios
- **Source Credibility Ground Truth**: Expert-annotated credibility

**Internal Datasets** (`datasets/`):
- `science_queries.json`: 7 science queries
- `philosophy_queries.json`: 6 philosophy queries
- `temporal_queries.json`: 5 temporal queries
- `technical_queries.json`: 5 technical queries
- `edge_cases.json`: 7 edge case queries
- `ssh_evaluation_dataset.json`: SSH feature evaluation

**Evaluation Scripts**:
- `scripts/evaluate_with_datasets.py`: Run evaluations on external datasets
- `scripts/run_automated_analysis.py`: Automated real data analysis
- `scripts/run_semantic_evaluation.py`: Semantic evaluation pipeline

### Test Coverage

**195+ test files** covering:
- Unit tests: Individual components
- Integration tests: Component interactions
- E2E tests: Full workflows
- Property-based tests: Invariants
- Chaos engineering: Failure scenarios
- Mutation testing: Test quality
- Visual tests: UI/UX validation

**Key Test Categories**:
- Agent behavior (`test_agent*.py`)
- Orchestrator (`test_orchestrator*.py`)
- Topology analysis (`test_topology*.py`)
- Trust/uncertainty (`test_trust*.py`)
- Constraints (`test_constraints*.py`)
- Quality feedback (`test_quality_feedback*.py`)
- Adaptive learning (`test_adaptive_quality.py`)
- Provenance (`test_provenance*.py`)
- Security (`test_security*.py`)
- E2E workflows (`test_e2e_*.py`)

## Query Types and Capabilities

### Supported Query Types

**1. Factual Queries**:
- "What is X?"
- "Define Y"
- Uses: `chain_of_thought` schema, quick search tools

**2. Procedural Queries**:
- "How does X work?"
- "Explain the process of Y"
- Uses: `decompose_and_synthesize` schema, reasoning tools

**3. Analytical Queries**:
- "Why does X happen?"
- "What are the reasons for Y?"
- Uses: `hypothesize_and_test` schema, deep research

**4. Comparative Queries**:
- "Compare X and Y"
- "What's the difference between A and B?"
- Uses: `scenario_analysis` schema, multiple sources

**5. Evaluative Queries**:
- "Analyze the effectiveness of X"
- "Evaluate Y"
- Uses: `decompose_and_synthesize` schema, research enabled

**6. Temporal Queries**:
- "How has X evolved over time?"
- "What are the latest developments in Y?"
- Uses: Research with temporal focus, knowledge tracking

### Advanced Capabilities

**1. Belief-Evidence Alignment**:
- Extracts user beliefs from conversation ("I think...")
- Computes alignment between evidence and beliefs
- Adjusts trust interpretation based on alignment
- Example: "I think trust is crucial" → system aligns evidence accordingly

**2. Query Refinement**:
- Suggests follow-up queries based on provenance
- Types: deep_dive, alternative, related, verification
- Prioritizes by relevance and quality
- Example: After "What is d-separation?", suggests "Explain conditional independence in detail"

**3. Knowledge Tracking**:
- Tracks concepts learned across sessions
- Temporal evolution of understanding
- Session-aware strategy adaptation
- Example: Remembers you've asked about "trust" before, adapts detail level

**4. Provenance Visualization**:
- Token-level matching (which query tokens matched which document tokens)
- Source agreement matrices (claims × sources)
- Relevance breakdowns (semantic similarity, token overlap, concept overlap)
- Clickable source references

**5. Session Management**:
- Hierarchical sessions (group → session → evaluation)
- Write buffering (reduces I/O)
- Lazy loading with LRU cache
- Indexing for fast queries
- Experience replay (forward, reverse, prioritized)

**6. Visualizations**:
- Source matrix heatmaps (claims × sources)
- Trust metrics charts
- Document relationship graphs
- Token importance charts
- Provenance heatmaps

## CLI Commands

**Core Commands**:
- `bop chat`: Interactive chat interface
- `bop research <query>`: Direct research command
- `bop schemas`: List all reasoning schemas
- `bop eval`: Run evaluation framework
- `bop semantic-eval`: Run semantic evaluation
- `bop sessions`: Manage hierarchical sessions
- `bop quality`: Show quality performance summary
- `bop serve`: Start HTTP server

**Command Options**:
- `--schema <name>`: Use specific reasoning schema
- `--research`: Enable deep research
- `--constraints`: Use constraint solver
- `--quality-feedback`: Enable quality feedback loop
- `--show-details`: Show full response (progressive disclosure)
- `--adaptive`: Show adaptive learning insights
- `--history`: Show evaluation history

## HTTP API Endpoints

**Core Endpoints**:
- `POST /chat`: Chat endpoint with constraint solver support
- `GET /health`: Health check with constraint solver status
- `GET /metrics`: Performance metrics
- `GET /cache/stats`: Cache statistics
- `POST /evaluate/compare`: Compare constraint vs heuristic selection

**Authentication**: API key via `X-API-Key` header (configurable)

## Theoretical Foundations

**Information Geometry**:
- Fisher Information Matrix (FIM) for structure quality
- Statistical manifolds for knowledge representation
- Attention dilution prevention

**Topological Structure**:
- Clique complexes for coherent context sets
- Betti numbers (graph-level approximation)
- Euler characteristic for complexity summary

**Causal Inference**:
- D-separation for conditional independence
- Collider bias avoidance
- Causal structure preservation

**Dynamical Systems**:
- Attractor basins as maximal cliques
- Edge-of-chaos dynamics
- Class 4 CA patterns

**Serial Scaling**:
- Dependent reasoning chains
- Computational depth constraints
- Adaptive depth allocation

## Caching System

### Persistent Caching

BOP uses persistent caching to reduce API costs and improve response times:

**What's Cached**:
- **Tool results** (MCP tool calls): 7 day TTL
- **LLM responses**: 3 day TTL
- **Token contexts**: 7 day TTL
- **Sessions**: Persistent (no TTL)

**Cache Storage**:
- **Fly.io Volumes**: `/data/cache/` (persistent, encrypted)
- **Local Development**: `./cache/` (ephemeral)

**Cache Key Strategy**:
- Tool results: `SHA256(tool_name + query + params)`
- LLM responses: `SHA256(prompt + backend + model)`
- Token contexts: `SHA256(text)`
- Sessions: `session_id` (UUID)

**Cache Flow**:
1. Check cache before calling MCP tools or LLM
2. Cache hit → return immediately (instant)
3. Cache miss → call API, cache result, return
4. Automatic expiration based on TTL
5. LRU eviction when size limit reached

**Benefits**:
- Cost reduction: Fewer API calls
- Faster responses: Cache hits are instant
- Better UX: Consistent responses for similar queries
- Reduced load: Less pressure on external APIs

**API Endpoints**:
- `GET /cache/stats`: Cache statistics (protected)
- `POST /cache/clear`: Clear cache by category (protected)

## Performance Characteristics

**Latency**:
- Simple queries (no research): < 1s
- Research queries: 5-30s (depends on tool calls)
- Cache hits: < 100ms (instant)
- Constraint solver overhead: +10-50ms per subproblem

**Cost**:
- LLM calls: Primary cost driver
- MCP tools: Varies by provider
- Constraint solver: Negligible (local computation)
- Caching: Reduces costs by 20-40% for repeated queries

**Scalability**:
- Caching: Reduces redundant API calls
- Lazy loading: Scales to large session histories
- Write buffering: Reduces I/O operations
- LRU cache: Limits memory usage
- Hash-based organization: Fast lookups

## Limitations and Future Work

**Current Limitations**:
1. D-Separation: Simplified implementation for undirected graphs
2. Betti Numbers: Graph-level approximation, not true simplicial homology
3. Fisher Information: Heuristic estimate, not true FIM
4. MCP Integration: Structure in place, actual calls need wiring
5. Tool Selection: Heuristic-based (constraint solver optional)

**Future Enhancements**:
1. Full MCP tool integration with actual API calls
2. Advanced topology with true simplicial homology
3. Enhanced error handling and retry logic
4. Multi-tool research synthesis improvements
5. Optional Unified Planning integration for optimal tool sequencing

## See Also

- `ARCHITECTURE.md` - Detailed theoretical foundations
- `AGENTS.md` - Agent architecture and usage patterns
- `docs/guides/DEVELOPER_QUESTIONS_ANSWERED.md` - Common developer questions
- `docs/guides/KNOWLEDGE_DISPLAY_GUIDE.md` - Knowledge display features
- `docs/guides/TRUST_AND_UNCERTAINTY_USER_GUIDE.md` - Trust metrics interpretation

