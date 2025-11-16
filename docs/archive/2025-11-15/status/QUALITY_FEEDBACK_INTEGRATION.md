# Quality Feedback Loop Integration

## Overview

The semantic evaluation framework is now integrated into the system so that insights and suggestions automatically flow back to improve responses, rather than being one-off evaluations.

## Integration Points

### 1. Agent Integration

**Location**: `src/bop/agent.py`

**Changes**:
- `KnowledgeAgent` now has `quality_feedback` attribute
- Every `chat()` call automatically evaluates the response
- Quality insights are included in response
- Auto-retry with better schema if quality is low

**Usage**:
```python
agent = KnowledgeAgent(enable_quality_feedback=True)
response = await agent.chat("What is trust?", use_schema="chain_of_thought")

# Response includes quality information
quality = response.get("quality")
print(f"Score: {quality['score']}")
print(f"Suggestions: {quality['suggestions']}")
```

### 2. CLI Integration

**Location**: `src/bop/cli.py`

**Changes**:
- Quality score displayed after each response
- High-priority suggestions shown automatically
- New `quality` command to view performance summary
- Quality feedback can be enabled/disabled with flag

**Usage**:
```bash
# Chat with quality feedback (default)
bop chat

# View quality performance
bop quality

# View with history
bop quality --history
```

### 3. Quality Feedback Loop

**Location**: `src/bop/quality_feedback.py`

**Features**:
- Evaluates every response automatically
- Tracks performance over time
- Suggests best schema based on history
- Identifies common quality issues
- Persists history to disk

**Key Methods**:
- `evaluate_and_learn()`: Evaluate response and learn from it
- `get_best_schema_for_query()`: Suggest best schema
- `should_retry_with_different_schema()`: Determine if retry needed
- `get_performance_summary()`: Get aggregated insights

## Automatic Improvements

### 1. Schema Selection

**How it works**:
- Tracks performance of each schema
- Suggests best performing schema for queries
- Auto-retries with better schema if quality < 0.5

**Example**:
```python
# First attempt with chain_of_thought (score: 0.3)
response1 = await agent.chat("complex query", use_schema="chain_of_thought")

# System detects low quality, retries with decompose_and_synthesize (score: 0.7)
# Final response uses better schema
```

### 2. Quality Issue Detection

**How it works**:
- Detects placeholders, errors, too-short responses
- Provides actionable suggestions
- Tracks frequency of issues

**Example**:
```python
# Response with placeholder
response = await agent.chat("test")

# Quality feedback detects:
# - Quality flag: "placeholder"
# - Suggestion: "Configure LLM service (set OPENAI_API_KEY)"
# - Priority: "high"
```

### 3. Performance Tracking

**How it works**:
- Tracks scores over time
- Identifies trends (improving/stable/degrading)
- Shows schema performance comparison
- Tracks common quality issues

**Example**:
```bash
$ bop quality

Quality Performance Summary
Total evaluations: 50
Recent mean score: 0.723
Trend: improving

Schema Performance:
  decompose_and_synthesize: 0.756
  chain_of_thought: 0.689
  hypothesize_and_test: 0.634

Common Quality Issues:
  placeholder: 5 occurrences
  too_short: 2 occurrences
```

## Feedback Flow

```
User Query
    ↓
Agent.chat()
    ↓
Generate Response
    ↓
QualityFeedbackLoop.evaluate_and_learn()
    ↓
    ├─→ Evaluate (relevance, accuracy, completeness)
    ├─→ Store in history
    ├─→ Update performance tracking
    └─→ Generate insights & suggestions
    ↓
    ├─→ If quality < 0.5: Auto-retry with better schema
    └─→ Return response with quality info
    ↓
Display to user with quality score & suggestions
```

## Persistent Learning

### History Storage

**Location**: `quality_history.json`

**Contents**:
- All evaluation results
- Performance summary
- Last 1000 evaluations (rolling window)

**Format**:
```json
{
  "history": [
    {
      "query": "What is trust?",
      "score": 0.723,
      "judgment_type": "relevance",
      "quality_flags": [],
      "metadata": {"schema": "chain_of_thought"},
      "timestamp": "2025-11-14T..."
    }
  ],
  "summary": {
    "total_evaluations": 50,
    "recent_mean_score": 0.723,
    "schema_performance": {...},
    "quality_issue_frequency": {...}
  }
}
```

### Performance Tracking

**Schema Performance**:
- Tracks average score per schema
- Updates with each evaluation
- Used for schema recommendations

**Query Type Performance**:
- Tracks performance by query complexity
- Identifies which query types need improvement

**Quality Issue Frequency**:
- Counts occurrences of each quality flag
- Identifies most common problems
- Guides system improvements

## Suggestions System

### Suggestion Types

1. **Configuration** (High Priority)
   - "LLM service not configured"
   - Action: Set OPENAI_API_KEY

2. **Schema Selection** (Medium Priority)
   - "Consider using 'decompose_and_synthesize' schema"
   - Action: Switch to better performing schema

3. **Response Length** (Medium Priority)
   - "Response too short for query complexity"
   - Action: Generate longer response

4. **Query Handling** (Low Priority)
   - "Multi-part query may need decomposition"
   - Action: Use appropriate schema

### Suggestion Priority

- **High**: System configuration issues (must fix)
- **Medium**: Performance improvements (should fix)
- **Low**: Optimization suggestions (nice to have)

## CLI Commands

### `bop chat`
- Default: Quality feedback enabled
- Shows quality score after each response
- Displays high-priority suggestions
- Command: `quality` to view summary

### `bop quality`
- Shows performance summary
- Schema performance comparison
- Common quality issues
- Option: `--history` to see recent evaluations

## Benefits

1. **Automatic Improvement**: System learns and improves over time
2. **Transparent Quality**: Users see quality scores and suggestions
3. **Data-Driven Decisions**: Schema selection based on actual performance
4. **Issue Detection**: Automatically identifies and suggests fixes
5. **Persistent Learning**: History persists across sessions

## Example Workflow

```python
# Initialize agent with quality feedback
agent = KnowledgeAgent(enable_quality_feedback=True)

# First query - system learns
response1 = await agent.chat("What is trust?")
# Quality: 0.45 (low)
# Suggestion: "Consider using 'decompose_and_synthesize' schema"

# System auto-retries with better schema
# Final response quality: 0.72 (good)

# Second query - system uses learned knowledge
response2 = await agent.chat("What is uncertainty?")
# System automatically uses best performing schema
# Quality: 0.78 (excellent)

# View performance
summary = agent.quality_feedback.get_performance_summary()
print(f"Mean score: {summary['recent_mean_score']}")
print(f"Best schema: {max(summary['schema_performance'].items(), key=lambda x: x[1])[0]}")
```

## Integration Status

✅ **Completed**:
- Quality feedback loop implementation
- Agent integration
- CLI integration
- History persistence
- Performance tracking
- Auto-retry with better schema
- Suggestion generation

✅ **Testing**:
- Unit tests for quality feedback
- Integration tests for agent
- All tests passing

The system now continuously learns and improves based on semantic evaluation results, making it a true feedback loop rather than just a one-off evaluation tool.

