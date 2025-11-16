# Agent Architecture Guide

## Overview

BOP implements a multi-agent architecture for knowledge structure research and reasoning. This document describes the agent components, their interactions, and usage patterns.

## Core Agents

### KnowledgeAgent (`src/bop/agent.py`)

**Purpose**: Main orchestrating agent that coordinates research, reasoning, and quality feedback.

**Components**:
- `ResearchAgent`: Deep research via MCP tools
- `StructuredOrchestrator`: Tool orchestration with structured reasoning
- `LLMService`: LLM interactions and schema hydration
- `QualityFeedbackLoop`: Continuous quality evaluation and learning
- `AdaptiveQualityManager`: Adaptive strategy selection based on feedback

**State Management**:
- `conversation_history`: Tracks conversation context
- `prior_beliefs`: Tracks user's stated beliefs for evidence alignment
- `recent_queries`: Tracks recent queries for context-dependent adaptation

**Key Methods**:
- `chat()`: Process user messages with optional schema and research
- `_generate_response()`: Generate LLM responses with context and length adaptation
- `_extract_prior_beliefs()`: Extract beliefs from user messages
- `_track_recent_query()`: Track queries for context adaptation
- `_compute_topic_similarity()`: Compute similarity for exploration/extraction mode detection
- `_create_response_tiers()`: Create progressive disclosure tiers (summary → detailed)
- `_add_source_references()`: Add source citations to response text
- `_extract_expected_concepts()`: Extract concepts for evaluation
- `_get_relevant_context()`: Retrieve relevant knowledge base context

**Usage**:
```python
from bop.agent import KnowledgeAgent

agent = KnowledgeAgent(enable_quality_feedback=True)
response = await agent.chat(
    message="What is the shape of ideas?",
    use_schema="decompose_and_synthesize",
    use_research=True,
)

# Access progressive disclosure tiers
summary = response["response_tiers"]["summary"]
full_details = response["response_tiers"]["detailed"]

# Access trust metrics (if research conducted)
if response.get("research"):
    topology = response["research"]["topology"]
    trust_summary = topology["trust_summary"]
    source_cred = topology["source_credibility"]
    cliques = topology["cliques"]

# Access source agreement matrix
source_matrix = response["research"]["source_matrix"]

# Access extracted beliefs (if any)
prior_beliefs = response.get("prior_beliefs", [])
```

**Response Structure**:
```python
{
    "message": str,                    # Original user message
    "response": str,                    # Main response (includes source references)
    "response_tiers": {                 # Progressive disclosure tiers
        "summary": str,                 # 1-2 sentence summary
        "structured": str,              # Organized breakdown
        "detailed": str,                # Full response
        "evidence": str,                # Full research synthesis
    },
    "prior_beliefs": [                  # Extracted user beliefs (if any)
        {"text": str, "source": str}
    ],
    "schema_used": Optional[str],       # Schema that was used
    "research_conducted": bool,         # Whether research was performed
    "research": {                       # Research results (if conducted)
        "query": str,
        "subsolutions": List[Dict],
        "final_synthesis": str,
        "source_matrix": Dict,          # Source agreement/disagreement matrix
        "topology": {
            "trust_summary": Dict,      # Trust metrics
            "source_credibility": Dict, # Per-source credibility
            "verification_info": Dict,  # Verification counts per source
            "cliques": List[Dict],      # Source agreement clusters
        },
    },
    "quality": {                       # Quality evaluation (if enabled)
        "score": float,
        "flags": List[str],
        "suggestions": List[Dict],
    },
}
```

### ResearchAgent (`src/bop/research.py`)

**Purpose**: Conducts deep research using MCP tools (Perplexity, Firecrawl, Tavily, etc.).

**Capabilities**:
- Multi-tool research orchestration
- Query decomposition and synthesis
- Context aggregation from multiple sources
- Tool selection based on query characteristics

**MCP Tools Integrated**:
- **Perplexity**: Deep research, reasoning, search
- **Firecrawl**: Web scraping, extraction, search
- **Tavily**: Search and content extraction
- **arXiv**: Academic paper search
- **Kagi**: Web search and summarization

**Usage**:
```python
from bop.research import ResearchAgent

research_agent = ResearchAgent()
result = await research_agent.deep_research("What is d-separation?")
```

### StructuredOrchestrator (`src/bop/orchestrator.py`)

**Purpose**: Orchestrates MCP tools using structured reasoning schemas while preserving causal structure.

**Theoretical Foundation**:
- **MCP Lazy Evaluation**: Preserves d-separation by avoiding collider bias
- **Context Topology**: Clique complexes for coherent context sets
- **Attractor Basins**: Maximal cliques as stable knowledge structures
- **Information Geometry**: Fisher Information for structure quality
- **Serial Scaling**: Dependent reasoning chains with depth constraints

**Key Features**:
- Dynamic tool selection based on subproblem characteristics
- Optional constraint solver for optimal tool selection
- Topological analysis of context relationships
- Schema-guided decomposition and synthesis

**Usage**:
```python
from bop.orchestrator import StructuredOrchestrator
from bop.research import ResearchAgent
from bop.llm import LLMService

orchestrator = StructuredOrchestrator(
    research_agent=ResearchAgent(),
    llm_service=LLMService(),
    use_constraints=True,  # Optional constraint solver
)

result = await orchestrator.research_with_schema(
    query="Explain information geometry",
    schema_name="decompose_and_synthesize",
    max_tools_per_subproblem=2,
    preserve_d_separation=True,
    prior_beliefs=[  # Optional: Pass user's prior beliefs for alignment
        {"text": "I think trust is important for systems", "source": "user_statement"}
    ],
)
```

**New Features**:
- **Belief-Evidence Alignment**: Computes alignment between evidence and user's prior beliefs
- **Source Relationship Matrix**: Builds agreement/disagreement matrix across sources
- **Enhanced Topology Metrics**: Includes source credibility, verification counts, and clique details

### QualityFeedbackLoop (`src/bop/quality_feedback.py`)

**Purpose**: Evaluates response quality and enables continuous learning.

**Evaluation Dimensions**:
- **Relevance**: How well the response addresses the query
- **Accuracy**: Factual correctness and consistency
- **Completeness**: Coverage of expected concepts
- **Semantic Quality**: Coherence, clarity, and structure

**Features**:
- Hierarchical session management
- Quality flag detection (placeholders, errors, repetition)
- Concept extraction and matching
- Adaptive learning integration

**Usage**:
```python
from bop.quality_feedback import QualityFeedbackLoop

feedback = QualityFeedbackLoop(use_sessions=True)
result = feedback.evaluate_and_learn(
    query="What is d-separation?",
    response="D-separation is...",
    schema="decompose_and_synthesize",
    research=True,
)
```

### AdaptiveQualityManager (`src/bop/adaptive_quality.py`)

**Purpose**: Adapts system behavior based on quality feedback and cross-session learning.

**Adaptive Strategies**:
- **Schema Selection**: Chooses optimal reasoning schema for query type
- **Response Length**: Determines optimal response length
- **Research Decision**: Decides when research helps vs. hurts
- **Tool Preferences**: Learns which tools work best for different query types

**Learning Data**:
- Persists to `adaptive_learning.json`
- Hierarchical session structure
- Cross-session pattern recognition

**Usage**:
```python
from bop.adaptive_quality import AdaptiveQualityManager
from bop.quality_feedback import QualityFeedbackLoop

feedback = QualityFeedbackLoop()
adaptive = AdaptiveQualityManager(quality_feedback=feedback)

strategy = adaptive.get_adaptive_strategy(
    query="What is information geometry?",
    current_session=None,
)

# Use strategy.schema, strategy.expected_length, strategy.use_research, etc.
```

## Agent Interactions

### Chat Flow

```
User Message
    ↓
KnowledgeAgent.chat()
    ↓
├─→ Extract Prior Beliefs (_extract_prior_beliefs)
├─→ Track Recent Query (_track_recent_query)
├─→ Schema Selection (AdaptiveQualityManager)
├─→ Context-Dependent Adaptation (topic similarity → exploration/extraction mode)
├─→ Research (ResearchAgent / StructuredOrchestrator)
│   ├─→ Belief Alignment Computation
│   ├─→ Source Matrix Building
│   └─→ Enhanced Topology Analysis
├─→ LLM Response Generation (LLMService with length adaptation)
├─→ Add Source References (_add_source_references)
├─→ Create Response Tiers (_create_response_tiers)
└─→ Quality Evaluation (QualityFeedbackLoop)
    ↓
    └─→ Adaptive Learning (AdaptiveQualityManager)
```

### Research Flow

```
Query
    ↓
StructuredOrchestrator.research_with_schema()
    ↓
├─→ Schema Decomposition (LLMService)
├─→ Tool Selection (ToolSelector / ConstraintSolver)
├─→ MCP Tool Calls (ResearchAgent)
│   ├─→ Compute Belief Alignment (if prior_beliefs provided)
│   └─→ Create Context Nodes with trust/uncertainty
├─→ Context Topology Analysis
│   ├─→ Compute Cliques (source agreement clusters)
│   ├─→ Calculate Source Credibility
│   ├─→ Track Verification Counts
│   └─→ Build Source Relationship Matrix
└─→ Synthesis (LLMService)
```

### Quality Feedback Flow

```
Response
    ↓
QualityFeedbackLoop.evaluate_and_learn()
    ↓
├─→ Semantic Evaluation (SemanticEvaluator)
├─→ Quality Flag Detection
├─→ Session Management (HierarchicalSessionManager)
└─→ Adaptive Learning Update (AdaptiveQualityManager)
```

## Agent Configuration

### Environment Variables

Environment variables are automatically loaded from `.env` file. See `.env.example` for all available options.

```bash
# LLM Backends
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...

# Constraint Solver
BOP_USE_CONSTRAINTS=true

# Quality Feedback
BOP_QUALITY_FEEDBACK=true
```

**Setup**:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

### Initialization Options

```python
# Basic agent
agent = KnowledgeAgent()

# With custom content directory
agent = KnowledgeAgent(content_dir=Path("./custom_content"))

# With custom LLM service
from bop.llm import LLMService
llm = LLMService(model="claude-3-5-sonnet-20241022")
agent = KnowledgeAgent(llm_service=llm)

# Without quality feedback
agent = KnowledgeAgent(enable_quality_feedback=False)
```

## Agent Patterns

### Pattern 1: Simple Chat

```python
agent = KnowledgeAgent()
response = await agent.chat("What is d-separation?")
print(response["response"])
```

### Pattern 2: Schema-Guided Research

```python
agent = KnowledgeAgent()
response = await agent.chat(
    message="Explain information geometry comprehensively",
    use_schema="decompose_and_synthesize",
    use_research=True,
)

# Access trust metrics
if response.get("research"):
    topology = response["research"]["topology"]
    print(f"Average trust: {topology['trust_summary']['avg_trust']:.2f}")
    print(f"Source credibility: {topology['source_credibility']}")
    
    # View source agreement clusters
    for clique in topology["cliques"][:3]:
        print(f"Sources agree: {clique['node_sources']}, Trust: {clique['trust']:.2f}")
```

### Pattern 2.5: Belief-Aware Research

```python
agent = KnowledgeAgent()

# User states a belief
response1 = await agent.chat(
    "I think trust is crucial for knowledge systems",
    use_research=True,
)

# Subsequent queries use belief alignment
response2 = await agent.chat(
    "How does uncertainty affect trust?",
    use_research=True,
)

# Check if beliefs were extracted
if response2.get("prior_beliefs"):
    print("Your beliefs:", response2["prior_beliefs"])
```

### Pattern 3: Adaptive Learning with Context Awareness

```python
agent = KnowledgeAgent(enable_quality_feedback=True)

# First query - system learns
response1 = await agent.chat("What is d-separation?")

# Similar topic query - system detects exploration mode, increases detail
response2 = await agent.chat("How does d-separation relate to causality?")

# Different topic - system detects extraction mode, provides concise answer
response3 = await agent.chat("What is the weather today?")

# Access progressive disclosure tiers
summary = response2["response_tiers"]["summary"]  # Quick overview
details = response2["response_tiers"]["detailed"]  # Full response
evidence = response2["response_tiers"]["evidence"]  # Research synthesis
```

### Pattern 4: Constraint-Based Tool Selection

```python
import os
os.environ["BOP_USE_CONSTRAINTS"] = "true"

agent = KnowledgeAgent()
response = await agent.chat(
    message="Research the latest papers on information geometry",
    use_research=True,
)
```

## Agent Extensibility

### Adding New MCP Tools

1. Add tool type to `ToolType` enum in `orchestrator.py`
2. Implement tool call in `research.py`
3. Add tool selection heuristics in `ToolSelector`
4. Update constraint definitions if using constraint solver

### Adding New Schemas

1. Define schema in `schemas.py`
2. Add schema hydration logic if needed
3. Update `AdaptiveQualityManager` to learn schema effectiveness

### Custom Quality Metrics

1. Extend `SemanticEvaluator` in `semantic_eval.py`
2. Add evaluation dimensions
3. Update `QualityFeedbackLoop` to use new metrics

## Best Practices

1. **Enable Quality Feedback**: Always enable for production use
2. **Use Appropriate Schemas**: Match schema to query complexity
3. **Research When Needed**: Use research for complex, open-ended queries
4. **Monitor Adaptive Learning**: Review `adaptive_learning.json` periodically
5. **Session Management**: Use hierarchical sessions for multi-turn conversations
6. **Trust Metrics**: Review trust scores and source credibility for important decisions
7. **Progressive Disclosure**: Use `response_tiers["summary"]` for quick overviews, expand to `detailed` or `evidence` when needed
8. **Belief Alignment**: State your beliefs explicitly (e.g., "I think X") to enable better evidence alignment
9. **Source Diversity**: Check source agreement matrices to identify consensus vs. conflicts
10. **Context Adaptation**: System automatically adapts detail level based on query patterns

## See Also

- `ARCHITECTURE.md` - Theoretical foundations
- `README.md` - Quick start guide
- `CONTRIBUTING.md` - Development guidelines
- `KNOWLEDGE_DISPLAY_GUIDE.md` - Knowledge display features guide
- `TRUST_AND_UNCERTAINTY_USER_GUIDE.md` - Trust metrics interpretation guide
- `MIGRATION_GUIDE.md` - Migration guide for new features

