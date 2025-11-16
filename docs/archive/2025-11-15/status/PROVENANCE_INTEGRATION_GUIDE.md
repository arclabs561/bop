# Provenance Features Integration Guide

## Overview

This guide documents how provenance features are integrated throughout BOP and how they improve the user experience.

## Features Integrated

### 1. Relevance Score Breakdowns

**What it does**: Explains why sources were selected with detailed component scores.

**Integration Points**:
- `src/bop/provenance.py`: `_compute_relevance_breakdown()` calculates scores
- `src/bop/provenance_viz.py`: `create_relevance_breakdown_display()` formats for display
- `src/bop/cli.py`: Shows breakdowns in terminal output
- `src/bop/web.py`: Displays in web UI with tooltips
- `src/bop/agent.py`: Includes relevance scores in source references

**User Experience**:
```
Before: "Source: perplexity_deep_research"
After:  "Source: perplexity_deep_research (Relevance: 0.78)
        - Word Overlap: 0.65
        - Semantic Similarity: 0.72
        - Token Match Average: 0.85"
```

### 2. Query Refinement

**What it does**: Suggests follow-up queries based on provenance data.

**Integration Points**:
- `src/bop/query_refinement.py`: Core refinement logic
- `src/bop/agent.py`: Generates suggestions automatically
- `src/bop/cli.py`: Displays suggestions in terminal
- `src/bop/web.py`: Shows suggestions in web UI
- `src/bop/server.py`: Includes in API response

**User Experience**:
```
User asks: "What is d-separation?"
System suggests:
1. "Explain d-separation, graphical, criterion in detail" (deep_dive)
2. "What do other sources say about d-separation?" (alternative)
3. "What concepts are related to d-separation?" (related)
```

### 3. Clickable Sources

**What it does**: Makes source references interactive with detailed tooltips.

**Integration Points**:
- `src/bop/provenance_viz.py`: `format_clickable_source()` creates interactive format
- `src/bop/web.py`: Processes sources section to make clickable
- `src/bop/agent.py`: Includes relevance scores in source references

**User Experience**:
```
Click on: "D-separation is a graphical criterion [perplexity_deep_research]"
See tooltip:
- Source: perplexity_deep_research
- Matching Passage: "D-separation is a graphical criterion for..."
- Overlap: 0.65
- Semantic Similarity: 0.72
- Token Matches: d-separation(0.95), graphical(0.90)
- Relevance Score: 0.78
```

## Data Flow

```
User Query
    ↓
KnowledgeAgent.chat()
    ↓
StructuredOrchestrator.research_with_schema()
    ↓
Research Results
    ↓
build_provenance_map() → Provenance Map
    ↓
├─→ match_claim_to_sources() → Source Matches
│   └─→ _compute_relevance_breakdown() → Relevance Breakdowns
│
├─→ refine_query_from_provenance() → Query Refinement Suggestions
│
└─→ format_clickable_source() → Clickable Source Format
    └─→ create_relevance_breakdown_display() → Formatted Breakdown
```

## Error Handling

All provenance features degrade gracefully:

1. **Missing Provenance**: System still works, just without provenance data
2. **Missing Relevance Breakdown**: Falls back to overlap_ratio
3. **Missing Query Refinement**: Returns empty list or fallback suggestions
4. **Provenance Building Errors**: Logged but don't break response generation

## Testing

### Unit Tests
- `tests/test_provenance.py`: Core provenance functions
- `tests/test_provenance_viz.py`: Visualization functions
- `tests/test_relevance_breakdowns.py`: Relevance score calculations
- `tests/test_query_refinement.py`: Query refinement logic

### Integration Tests
- `tests/test_integration_provenance_complete.py`: Complete pipeline
- `tests/test_e2e_provenance_workflow.py`: End-to-end workflows
- `tests/test_e2e_real_user_journey.py`: Real user scenarios

### Validation
- `scripts/validate_provenance_e2e.py`: Real query validation

## Usage Examples

### CLI Usage

```bash
# Run with research to see provenance
bop chat "What is d-separation?" --research

# Output includes:
# - Token-Level Provenance heatmap
# - Relevance Score Breakdowns
# - Query Refinement Suggestions
```

### Web UI Usage

1. Enable "Show Visualizations" toggle
2. Ask a question with research enabled
3. Click on source references to see details
4. Use query refinement suggestions for follow-ups

### API Usage

```python
response = await agent.chat(
    message="What is d-separation?",
    use_research=True,
)

# Access provenance
provenance = response["research"]["provenance"]

# Access query refinement
suggestions = response["query_refinement_suggestions"]
```

## Qualitative Improvements

### Before Provenance Features

- ❌ No explanation of why sources were selected
- ❌ Can't verify if sources actually support claims
- ❌ No way to explore related concepts
- ❌ No transparency into matching logic

### After Provenance Features

- ✅ Relevance scores show WHY sources were selected
- ✅ Clickable sources show exact matching passages
- ✅ Query refinement suggests next steps
- ✅ Token-level transparency shows matching logic
- ✅ Progressive disclosure reduces cognitive load

## Performance Considerations

- Provenance building is fast (heuristic-based, no LLM calls)
- Relevance breakdowns use efficient similarity calculations
- Query refinement is lightweight (pattern-based suggestions)
- All features degrade gracefully if data is missing

## Future Enhancements

1. **LLM-based Semantic Similarity**: Use embeddings for better matching
2. **Interactive Query Refinement**: Click suggestions to auto-execute
3. **Provenance History**: Track how understanding evolves over time
4. **Collaborative Annotation**: Users can annotate sources and claims

