# Temporal Information Handling in BOP

## Overview

BOP now tracks and visualizes temporal aspects of information, addressing the critical need to understand **when** information was generated, **how old** it is, and **how understanding has evolved** over time. This aligns with KumoRFM's principle: "With timestamps, we place events on a timeline."

## Features Implemented

### 1. Timestamp Tracking

**Response Timestamps**:
- Every response includes a `timestamp` field (ISO 8601 format)
- Shows when the response was generated
- Enables staleness detection

**Source Timestamps**:
- Each MCP tool call records when it was accessed
- Stored in `source_timestamps` dictionary: `{source_name: timestamp}`
- Allows tracking of information freshness per source

### 2. Temporal Evolution Visualization

**Knowledge Evolution Timeline**:
- Shows how understanding of claims evolved
- Displays consensus levels over time
- Highlights conflicts detected
- Shows source count per claim

**Evolution Data Structure**:
```json
{
  "claim": "Short claim text...",
  "full_claim": "Full claim text",
  "source_count": 3,
  "consensus": 0.8,
  "conflict": false
}
```

### 3. Staleness Indicators

**Age Calculation**:
- Automatically calculates how old information is
- Formats as "X minutes/hours/days ago"
- Helps users assess information freshness

**Visual Indicators**:
- Response timestamp with age
- Source access times
- Temporal evolution timeline

### 4. Timeline Visualization

**UI Components**:
- **Response Timestamp**: Shows when response was generated with age
- **Source Access Times**: List of when each source was accessed
- **Knowledge Evolution**: Timeline showing how claims evolved

## Implementation Details

### Server (`src/bop/server.py`)

**ChatResponse Model**:
```python
class ChatResponse(BaseModel):
    # ... existing fields ...
    timestamp: Optional[str] = None
    source_timestamps: Optional[Dict[str, str]] = None
    temporal_evolution: Optional[List[Dict[str, Any]]] = None
```

**Timestamp Extraction**:
- Extracts timestamps from research results
- Builds temporal evolution from source matrix
- Calculates current timestamp for response

### Orchestrator (`src/bop/orchestrator.py`)

**Tool Result Timestamps**:
- Every MCP tool result includes `timestamp` and `accessed_at`
- Tracks when each source was accessed
- Enables staleness detection

```python
result = {
    "tool": tool.value,
    "result": mcp_result.get("result", ""),
    "sources": mcp_result.get("sources", []),
    "timestamp": datetime.utcnow().isoformat(),
    "accessed_at": datetime.utcnow().isoformat(),
}
```

### JavaScript (`static/js/chat.js`)

**Temporal Visualization Function**:
- `createTemporalVisualization()` - Creates temporal info display
- Calculates age from timestamps
- Formats timestamps for display
- Renders evolution timeline

**Age Calculation**:
```javascript
const ageMs = now - timestamp;
const ageMinutes = Math.floor(ageMs / 60000);
const ageHours = Math.floor(ageMs / 3600000);
const ageDays = Math.floor(ageMs / 86400000);
```

### CSS (`static/css/chat.css`)

**Temporal Styles**:
- `.temporal-content` - Container for temporal info
- `.temporal-item` - Individual temporal data items
- `.source-timestamps-list` - Source timestamp list
- `.evolution-list` - Evolution timeline
- `.evolution-item` - Individual evolution entries

## Alignment with KumoRFM Concepts

### "With timestamps, we place events on a timeline"

**BOP Implementation**:
- All source accesses have timestamps
- Responses have generation timestamps
- Timeline visualization shows evolution
- Enables temporal reasoning

### Temporal Queries (Conceptual)

**Future Enhancement**:
- "What was known about X in 2020 vs 2024?"
- "How has understanding of Y changed over time?"
- "Show me the evolution of claim Z"

**Current Support**:
- Temporal evolution shows how claims changed
- Source timestamps enable time-based filtering
- Response timestamps enable staleness detection

## Usage Examples

### Example Response with Temporal Data

```json
{
  "response": "D-separation is a graphical criterion...",
  "timestamp": "2025-01-15T10:30:00.000Z",
  "source_timestamps": {
    "perplexity_deep_research": "2025-01-15T10:29:45.000Z",
    "arxiv_search": "2025-01-15T10:29:50.000Z"
  },
  "temporal_evolution": [
    {
      "claim": "d-separation determines independence",
      "full_claim": "d-separation determines conditional independence in Bayesian networks",
      "source_count": 2,
      "consensus": 0.9,
      "conflict": false
    }
  ]
}
```

**UI Displays**:
1. **Response Timestamp**: "Response generated: 1/15/2025, 10:30:00 AM (just now)"
2. **Source Access Times**: List showing when each source was accessed
3. **Knowledge Evolution**: Timeline showing claim evolution with consensus levels

## Benefits

1. **Staleness Detection**: Users can see how old information is
2. **Temporal Reasoning**: Understand how knowledge evolved
3. **Source Freshness**: Know when each source was accessed
4. **Evolution Tracking**: See how understanding changed over time
5. **Trust Assessment**: Older information may be less reliable

## Future Enhancements

Based on KumoRFM and research document:

1. **Temporal Queries**: "What was known at time X?"
2. **Historical Comparison**: Compare understanding across time periods
3. **Temporal Filtering**: Filter sources by recency
4. **Evolution Animation**: Animate how understanding changed
5. **Temporal Clustering**: Group claims by time period
6. **Staleness Warnings**: Alert when information is too old
7. **Temporal Confidence**: Adjust confidence based on information age

## Testing

Temporal features can be tested by:
1. Making queries with research enabled
2. Checking that timestamps are present in responses
3. Verifying temporal visualization renders correctly
4. Testing age calculation logic
5. Validating evolution timeline display

## References

- KumoRFM Quickstart - Temporal query concepts
- "How to display knowledge well?" - Temporal evolution tracker
- BOP Architecture Guide - System architecture
- Knowledge Display Implementation - UI enhancements

