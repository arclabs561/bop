# Quality Feedback Integration - Complete

## Overview

The semantic evaluation framework is now fully integrated into the system so that insights and suggestions automatically flow back to improve responses in real-time, rather than being one-off evaluations.

## Integration Architecture

### 1. Quality Feedback Loop (`src/bop/quality_feedback.py`)

**Purpose**: Continuous learning and improvement system

**Features**:
- Evaluates every response automatically
- Tracks performance over time (schema, query type, quality issues)
- Suggests best schema based on historical performance
- Identifies common quality issues
- Persists history to disk for cross-session learning
- Generates actionable suggestions

**Key Methods**:
- `evaluate_and_learn()`: Evaluate response and learn from it
- `get_best_schema_for_query()`: Suggest best performing schema
- `should_retry_with_different_schema()`: Determine if retry needed
- `get_performance_summary()`: Get aggregated insights

### 2. Agent Integration (`src/bop/agent.py`)

**Changes**:
- Added `enable_quality_feedback` parameter (default: True)
- Every `chat()` call automatically evaluates response
- Auto-retries with better schema if quality < 0.5
- Quality information included in response
- Extracts expected concepts from query/knowledge base
- Gets relevant context for completeness evaluation

**Flow**:
```
User Query
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
```

### 3. CLI Integration (`src/bop/cli.py`)

**Changes**:
- Quality score displayed after each response (color-coded)
- High-priority suggestions shown automatically
- New `quality` command to view performance summary
- Quality feedback can be enabled/disabled with `--quality-feedback` flag
- `quality` command in chat shows summary

**Usage**:
```bash
# Chat with quality feedback (default)
bop chat

# View quality performance
bop quality

# View with history
bop quality --history

# Disable quality feedback
bop chat --no-quality-feedback
```

## Automatic Improvements

### 1. Schema Auto-Selection

**How it works**:
- Tracks performance of each schema over time
- When quality < 0.5, automatically retries with best performing schema
- Learns which schemas work best for different query types

**Example**:
```python
# First attempt with chain_of_thought (score: 0.3)
response = await agent.chat("complex query", use_schema="chain_of_thought")

# System detects low quality, automatically retries with decompose_and_synthesize
# Final response uses better schema (score: 0.7)
```

### 2. Quality Issue Detection & Suggestions

**Detected Issues**:
- Placeholders (LLM service not configured)
- Errors (system configuration problems)
- Too short (response insufficient for query complexity)
- Repetitive (low quality content)

**Automatic Suggestions**:
- High priority: Configuration issues (must fix)
- Medium priority: Schema selection, response length
- Low priority: Query handling optimizations

### 3. Performance Tracking

**Tracked Metrics**:
- Schema performance (average score per schema)
- Query type performance (by complexity, type)
- Quality issue frequency
- Trends over time (improving/stable/degrading)

**Persistent Learning**:
- History saved to `quality_history.json`
- Last 1000 evaluations kept (rolling window)
- Performance tracking persists across sessions
- System learns and improves over time

## Usage Examples

### Basic Usage

```python
from bop.agent import KnowledgeAgent

# Initialize with quality feedback (default)
agent = KnowledgeAgent(enable_quality_feedback=True)

# Chat - automatically evaluated and improved
response = await agent.chat("What is trust?", use_schema="chain_of_thought")

# Quality information included
quality = response.get("quality")
print(f"Score: {quality['score']}")
print(f"Suggestions: {quality['suggestions']}")
```

### CLI Usage

```bash
# Start chat - quality feedback enabled by default
$ bop chat

You: What is trust?
Using schema: chain_of_thought
Quality: 0.45
⚠ LLM service not configured - responses are placeholders

# View performance summary
$ bop quality

Quality Performance Summary
Total evaluations: 25
Recent mean score: 0.723
Trend: improving

Schema Performance:
  decompose_and_synthesize: 0.756
  chain_of_thought: 0.689
  hypothesize_and_test: 0.634

Common Quality Issues:
  placeholder: 5 occurrences
```

### Programmatic Access

```python
# Get performance summary
summary = agent.quality_feedback.get_performance_summary()
print(f"Best schema: {max(summary['schema_performance'].items(), key=lambda x: x[1])[0]}")

# Get best schema for query
best_schema = agent.quality_feedback.get_best_schema_for_query("complex query")
print(f"Recommended schema: {best_schema}")

# Check if retry needed
should_retry = agent.quality_feedback.should_retry_with_different_schema(
    "query", "current_schema", 0.3
)
```

## Feedback Flow Diagram

```
┌─────────────┐
│ User Query  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Agent.chat()   │
└──────┬──────────┘
       │
       ├─→ Generate Response
       │
       ▼
┌──────────────────────────┐
│ QualityFeedbackLoop      │
│ .evaluate_and_learn()    │
└──────┬───────────────────┘
       │
       ├─→ Evaluate (relevance, accuracy, completeness)
       ├─→ Store in history
       ├─→ Update performance tracking
       └─→ Generate insights & suggestions
       │
       ▼
┌──────────────────────────┐
│ Quality < 0.5?           │
└──────┬───────────────────┘
       │
       ├─→ Yes: Auto-retry with best schema
       └─→ No: Continue
       │
       ▼
┌──────────────────────────┐
│ Return Response          │
│ + Quality Info           │
│ + Suggestions            │
└──────────────────────────┘
```

## Benefits

1. **Automatic Improvement**: System learns and improves over time
2. **Transparent Quality**: Users see quality scores and suggestions
3. **Data-Driven Decisions**: Schema selection based on actual performance
4. **Issue Detection**: Automatically identifies and suggests fixes
5. **Persistent Learning**: History persists across sessions
6. **Real-Time Adaptation**: Auto-retries with better approaches

## Integration Status

✅ **Completed**:
- Quality feedback loop implementation
- Agent integration with auto-retry
- CLI integration with quality display
- History persistence
- Performance tracking
- Suggestion generation
- Schema auto-selection

✅ **Testing**:
- Unit tests for quality feedback
- Integration tests for agent
- All tests passing

## Next Steps

The system now continuously learns and improves. Future enhancements could include:
- Learning query-to-schema mappings
- Adaptive response length based on query complexity
- Quality-based research triggering
- Multi-turn conversation quality tracking

The semantic evaluation framework is no longer a one-off tool - it's an integral part of the system that drives continuous improvement.

