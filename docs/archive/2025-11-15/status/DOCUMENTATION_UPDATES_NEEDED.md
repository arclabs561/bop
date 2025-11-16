# Documentation Updates Needed

## Overview

This document lists all documentation that needs updating after implementing knowledge display improvements, trust metrics, belief-evidence consistency, and context-dependent adaptation features.

## Critical Documentation Updates

### 1. `AGENTS.md` - Agent Architecture Guide

**Status**: Needs major update

**What to Add**:

#### KnowledgeAgent Section Updates

**New State Variables**:
```python
- prior_beliefs: List[Dict[str, Any]]  # Track user's stated beliefs
- recent_queries: List[Dict[str, Any]]  # Track recent queries for context adaptation
```

**New Methods**:
- `_extract_prior_beliefs(message)`: Extracts beliefs from user messages
- `_track_recent_query(message)`: Tracks queries for context adaptation
- `_compute_topic_similarity(current, recent_topics)`: Computes topic similarity
- `_create_response_tiers(response, research, query)`: Creates progressive disclosure tiers
- `_add_source_references(response_text, research)`: Adds source citations

**Updated Response Structure**:
```python
response = {
    # Existing fields
    "message": str,
    "response": str,  # Now includes source references
    "schema_used": Optional[str],
    "research_conducted": bool,
    "research": Dict[str, Any],  # Enhanced with new fields
    "quality": Dict[str, Any],
    
    # NEW FIELDS
    "response_tiers": {
        "summary": str,      # 1-2 sentence summary
        "structured": str,   # Organized breakdown
        "detailed": str,     # Full response
        "evidence": str,     # Full research synthesis
    },
    "prior_beliefs": [      # If beliefs were extracted
        {
            "text": str,
            "source": str,
        }
    ],
}
```

**Enhanced Research Response Structure**:
```python
research = {
    # Existing fields
    "query": str,
    "schema_used": str,
    "subsolutions": List[Dict],
    "final_synthesis": str,
    "tools_called": int,
    "topology": {
        # Existing
        "trust_summary": Dict,
        "betti_numbers": Dict,
        # NEW
        "source_credibility": Dict[str, float],  # Per-source credibility
        "verification_info": Dict[str, Dict],    # Verification counts per source
        "cliques": List[Dict],                   # Clique details for visualization
    },
    # NEW
    "source_matrix": Dict[str, Dict],  # Agreement/disagreement matrix
}
```

#### StructuredOrchestrator Section Updates

**New Method Signature**:
```python
async def research_with_schema(
    query: str,
    schema_name: str = "decompose_and_synthesize",
    max_tools_per_subproblem: int = 2,
    preserve_d_separation: bool = True,
    prior_beliefs: Optional[List[Dict[str, Any]]] = None,  # NEW PARAMETER
) -> Dict[str, Any]:
```

**New Methods**:
- `_compute_belief_alignment(evidence_text, prior_beliefs)`: Computes belief-evidence alignment
- `_build_source_matrix(subsolutions)`: Builds source agreement/disagreement matrix
- `_extract_key_phrases(text)`: Extracts key phrases for matrix building

**Usage Example Update**:
```python
result = await orchestrator.research_with_schema(
    query="Explain information geometry",
    schema_name="decompose_and_synthesize",
    max_tools_per_subproblem=2,
    preserve_d_separation=True,
    prior_beliefs=[  # NEW: Pass user's prior beliefs
        {"text": "I think trust is important", "source": "user_statement"}
    ],
)
```

#### New Display Helpers Section

Add section documenting `display_helpers.py`:

```python
from bop.display_helpers import (
    format_trust_summary,
    format_source_credibility,
    format_clique_clusters,
    create_trust_table,
)
```

### 2. `ARCHITECTURE.md` - Architecture Guide

**Status**: Needs updates to topology section

**What to Add**:

#### ContextTopology Enhancements

**New Trust Metrics**:
- `source_credibility`: Per-source credibility scores
- `verification_info`: Verification counts and source diversity
- `cliques`: Detailed clique information with source diversity

**Belief-Evidence Consistency**:
- `ContextNode.belief_alignment`: Now computed dynamically (not hardcoded)
- Alignment computation based on prior beliefs vs evidence

**Source Relationship Analysis**:
- Source agreement/disagreement matrix
- Consensus detection (strong/weak agreement, disagreement)
- Conflict detection

### 3. `README.md` - Quick Start Guide

**Status**: Needs feature highlights

**What to Add**:

#### New Features Section

Add to "Features" list:
- **Trust Transparency**: Source credibility scores, calibration metrics, verification counts
- **Belief-Evidence Alignment**: Tracks user beliefs and aligns evidence accordingly
- **Progressive Disclosure**: Summary → structured → detailed → evidence tiers
- **Source Provenance**: Source references and agreement matrices
- **Context-Adaptive Responses**: Adapts detail level based on query patterns

#### Response Structure Example

Add example showing new response structure:
```python
response = await agent.chat("What is trust?", use_research=True)

# Access progressive disclosure tiers
summary = response["response_tiers"]["summary"]
full_details = response["response_tiers"]["detailed"]

# Access trust metrics
if response.get("research"):
    topology = response["research"]["topology"]
    trust_summary = topology["trust_summary"]
    source_cred = topology["source_credibility"]
    cliques = topology["cliques"]
    
# Access source agreement matrix
source_matrix = response["research"]["source_matrix"]
```

### 4. API Documentation (`src/bop/server.py`)

**Status**: Needs ChatResponse model update

**What to Update**:

The `ChatResponse` model should include new fields:
```python
class ChatResponse(BaseModel):
    response: str
    schema_used: Optional[str] = None
    research_conducted: bool = False
    tools_called: int = 0
    constraint_solver_used: bool = False
    quality_score: Optional[float] = None
    topology_metrics: Optional[Dict[str, Any]] = None
    
    # NEW FIELDS
    response_tiers: Optional[Dict[str, str]] = None
    prior_beliefs: Optional[List[Dict[str, Any]]] = None
    source_matrix: Optional[Dict[str, Dict]] = None
```

### 5. CLI Documentation

**Status**: Needs usage examples

**What to Add**:

Document new CLI output features:
- Trust metrics table display
- Source credibility indicators
- Source agreement clusters
- Belief-evidence alignment display
- Progressive disclosure (summary first)

### 6. Web UI Documentation

**Status**: Needs feature documentation

**What to Add**:

Document web UI enhancements:
- Progressive disclosure in web interface
- Trust metrics display
- Source references
- Expandable response tiers

## Documentation Files to Create

### 7. `KNOWLEDGE_DISPLAY_GUIDE.md` (NEW)

Create comprehensive guide covering:
- Trust metrics interpretation
- Source credibility scores
- Belief-evidence alignment
- Progressive disclosure usage
- Source agreement matrices
- Context-dependent adaptation

### 8. `TRUST_AND_UNCERTAINTY_USER_GUIDE.md` (NEW)

User-facing guide explaining:
- What trust scores mean
- How to interpret calibration error
- Source credibility ratings
- Verification counts
- Belief alignment indicators

## Code Comments to Update

### 9. `src/bop/agent.py`

**Update `chat()` method docstring**:
```python
"""
Process a chat message and generate response.

Args:
    message: User message
    use_schema: Optional schema name to use for structured reasoning
    use_research: Whether to conduct deep research

Returns:
    Response dictionary with fields:
    - response: Main response text (with source references)
    - response_tiers: Progressive disclosure tiers (summary, structured, detailed, evidence)
    - prior_beliefs: Extracted user beliefs (if any)
    - research: Research results with enhanced topology metrics
    - quality: Quality evaluation results
"""
```

### 10. `src/bop/orchestrator.py`

**Update `research_with_schema()` method docstring**:
```python
"""
Conduct research using structured schema with topological analysis.

Args:
    query: Research query
    schema_name: Schema to use for decomposition
    max_tools_per_subproblem: Maximum tools per subproblem
    preserve_d_separation: Whether to preserve d-separation
    prior_beliefs: Optional list of user's prior beliefs for alignment computation

Returns:
    Research result dictionary with:
    - source_matrix: Source agreement/disagreement matrix
    - topology: Enhanced topology with source_credibility, verification_info, cliques
"""
```

## Testing Documentation

### 11. Update Test Documentation

Document new test files:
- `tests/test_display_improvements.py`: Tests for display features
- `tests/test_backwards_compatibility.py`: Backwards compatibility tests

## Migration Guide

### 12. `MIGRATION_GUIDE.md` (NEW)

Create migration guide for users upgrading:
- New response structure fields
- How to access new features
- Backwards compatibility notes
- Breaking changes (none, but document new optional fields)

