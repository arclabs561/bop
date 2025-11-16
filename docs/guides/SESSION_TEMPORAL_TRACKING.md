# Session-Level Temporal Knowledge Tracking

## Overview

BOP now tracks how knowledge evolves **across sessions**, not just within a single query. This enables understanding of how concepts are learned, refined, and developed over time through multiple conversations.

## What This Adds

### Before (Query-Level Only)
- Timestamps for individual responses
- Source access times
- Temporal evolution within a single research session

### After (Session-Level + Query-Level)
- **Concept learning tracking**: When concepts were first introduced
- **Concept refinement tracking**: When existing concepts were refined
- **Cross-session evolution**: How understanding of concepts evolved across multiple sessions
- **Session knowledge summary**: What was learned/refined in each session
- **Concept timeline**: When concepts first appeared and when they were last updated

## Features

### 1. Concept Extraction

**Automatic concept detection** from queries and responses:
- Recognizes key concepts: d-separation, trust, uncertainty, knowledge, structure, causality, information_geometry, topology, reasoning, belief
- Extracts concepts from both query text and response text
- Tracks when concepts appear together

### 2. Concept Learning vs. Refinement

**Learning**: First time a concept appears in any session
- Tracked as "new" concept
- Records first_learned_at timestamp
- Shows in session as "concepts_learned"

**Refinement**: Concept that was already known appears again
- Tracked as "refined" concept
- Updates last_updated_at timestamp
- Shows in session as "concepts_refined"

### 3. Cross-Session Evolution

**Tracks**:
- When each concept was first learned
- When each concept was last updated
- How many sessions each concept appeared in
- Average confidence scores when concept appeared
- Query count per concept

**Example**:
```json
{
  "concept": "d-separation",
  "first_learned_at": "2025-01-10T10:00:00Z",
  "last_updated_at": "2025-01-15T14:30:00Z",
  "session_count": 5,
  "query_count": 12,
  "average_confidence": 0.82
}
```

### 4. Session Knowledge Summary

**Per-session tracking**:
- Concepts learned (new in this session)
- Concepts refined (already known, refined in this session)
- Query count
- Session start/end times

## Implementation

### KnowledgeTracker (`src/bop/knowledge_tracking.py`)

**Core Component**:
- `ConceptLearning`: Tracks individual concept evolution
- `SessionKnowledge`: Tracks knowledge per session
- `KnowledgeTracker`: Main tracking class

**Key Methods**:
- `extract_concepts(text)`: Extract concepts from text
- `track_query(session_id, query, response, timestamp, ...)`: Track concepts from query-response pair
- `get_concept_evolution(concept)`: Get evolution of specific concept
- `get_session_evolution(session_id)`: Get knowledge evolution for session
- `get_cross_session_evolution(limit)`: Get evolution across all sessions
- `get_concepts_by_session(session_id)`: Get all concepts in a session

### Agent Integration (`src/bop/agent.py`)

**Automatic Tracking**:
- Every `chat()` call automatically tracks concepts
- Extracts concepts from query and response
- Associates with current session
- Includes confidence scores from quality feedback

**Response Fields Added**:
- `session_knowledge`: Knowledge learned in this session
- `cross_session_evolution`: How concepts evolved across sessions
- `session_concepts`: Concepts that appeared in this session

### UI Integration (`static/js/chat.js`)

**Visualization**:
- **Session Knowledge**: Shows concepts learned/refined, query count
- **Cross-Session Evolution**: Timeline showing when concepts were first learned, last updated, session count
- **Session Concepts**: List of concepts in current session with status (new/refined)

## Usage Examples

### Example: Learning d-separation

**Session 1** (Day 1):
```python
response1 = await agent.chat("What is d-separation?")
# session_knowledge: {"concepts_learned": ["d-separation"], "concepts_refined": []}
```

**Session 2** (Day 3):
```python
response2 = await agent.chat("How does d-separation relate to causality?")
# session_knowledge: {"concepts_learned": ["causality"], "concepts_refined": ["d-separation"]}
# cross_session_evolution: [{"concept": "d-separation", "first_learned_at": "Day 1", "last_updated_at": "Day 3", "session_count": 2}]
```

**Session 3** (Day 5):
```python
response3 = await agent.chat("Explain d-separation in detail")
# session_knowledge: {"concepts_learned": [], "concepts_refined": ["d-separation"]}
# cross_session_evolution: [{"concept": "d-separation", "first_learned_at": "Day 1", "last_updated_at": "Day 5", "session_count": 3}]
```

### UI Display

**Session Knowledge Section**:
```
📚 Concepts learned: 2
🔄 Concepts refined: 1
💬 Queries: 3

✨ d-separation
✨ causality
```

**Cross-Session Evolution**:
```
Knowledge Evolution Across Sessions:
  d-separation
    First learned: 5 days ago
    Last updated: 1 day ago
    Across 3 sessions
    Avg confidence: 82%
```

**Session Concepts**:
```
Concepts in This Session:
  d-separation 🔄 Refined
    First learned: 5 days ago
    Appeared in 3 sessions
```

## Benefits

1. **Learning Trajectory**: See how understanding develops over time
2. **Concept Mastery**: Track which concepts are being refined vs. newly learned
3. **Session Context**: Understand what was learned in each session
4. **Knowledge Gaps**: Identify concepts that haven't been refined (may need more attention)
5. **Temporal Reasoning**: Answer questions like "When did we first learn about X?"

## Alignment with BOP's Purpose

**BOP is about knowledge structure research**:
- ✅ Tracks how knowledge structures evolve
- ✅ Shows relationships between concepts across sessions
- ✅ Provides temporal context for understanding
- ✅ Aligns with "shape of ideas" exploration

**Theoretical Foundation**:
- **Temporal Evolution**: How understanding changes over time
- **Knowledge Graphs**: Concepts as nodes, sessions as edges
- **Learning Trajectories**: Paths through knowledge space
- **Information Geometry**: Temporal manifolds of understanding

## Future Enhancements

1. **Persistence**: Save knowledge tracker state to disk
2. **Concept Relationships**: Track which concepts appear together
3. **Learning Velocity**: How quickly concepts are refined
4. **Forgetting Curves**: Track concept staleness
5. **Knowledge Maps**: Visualize concept evolution over time
6. **Query Suggestions**: Suggest queries based on learning gaps

## Testing

See `tests/test_session_temporal_tracking.py` for comprehensive tests covering:
- Concept extraction
- Learning vs. refinement tracking
- Cross-session evolution
- Agent integration
- UI display

## References

- `TEMPORAL_FEATURES.md` - Query-level temporal features
- `HIERARCHICAL_SESSIONS.md` - Session management
- `KNOWLEDGE_DISPLAY_IMPLEMENTATION.md` - Knowledge display features

