# Adaptive Quality Enhancement

## Overview

Extended the quality feedback loop with adaptive learning that automatically improves system behavior based on patterns learned from evaluations.

## New Components

### 1. Adaptive Quality Manager (`src/bop/adaptive_quality.py`)

**Purpose**: Learn patterns from quality feedback and adapt system behavior automatically.

**Key Features**:
- **Query Type Classification**: Automatically classifies queries (factual, procedural, analytical, comparative, evaluative)
- **Schema Learning**: Learns which schemas work best for each query type
- **Length Optimization**: Learns optimal response lengths for different query types
- **Research Impact Analysis**: Determines when research helps vs hurts quality
- **Tool Performance Tracking**: Tracks which tools improve quality (future enhancement)

**Key Methods**:
- `get_adaptive_strategy(query)`: Get recommended strategy for a query
- `update_from_evaluation(...)`: Learn from each evaluation
- `get_improvement_suggestions(query, score)`: Get specific, actionable suggestions
- `get_performance_insights()`: Get aggregated insights about patterns

### 2. Enhanced Agent Integration

**Changes**:
- Agent now uses `AdaptiveQualityManager` alongside `QualityFeedbackLoop`
- Adaptive manager learns from every evaluation
- Auto-retry uses adaptive strategy recommendations (higher confidence)
- Response includes adaptive strategy information

**Flow**:
```
Query → Generate Response → Evaluate → Learn → Adapt Strategy → (Auto-retry if needed)
```

### 3. Enhanced CLI

**New Command Options**:
- `bop quality --adaptive`: Show adaptive learning insights
  - Query type performance
  - Schema recommendations by query type
  - Research effectiveness analysis
  - Optimal response lengths

## Adaptive Learning

### Query Type Classification

Automatically classifies queries into types:
- **Factual**: "What is...", "Define..."
- **Procedural**: "How...", "Explain process..."
- **Analytical**: "Why...", "Reason..."
- **Comparative**: "Compare...", "Contrast..."
- **Evaluative**: "Analyze...", "Evaluate..."

### Schema Learning

Tracks schema performance by query type:
```python
# Learns: "For factual queries, chain_of_thought performs best"
# Learns: "For comparative queries, decompose_and_synthesize performs best"
```

### Length Optimization

Learns optimal response lengths:
```python
# Learns: "High-quality factual responses are typically 150 characters"
# Learns: "High-quality analytical responses are typically 300 characters"
```

### Research Impact

Determines when research helps:
```python
# Learns: "Research improves quality for evaluative queries by 0.15"
# Learns: "Research doesn't help for factual queries"
```

## Usage Examples

### Programmatic

```python
from bop.agent import KnowledgeAgent

agent = KnowledgeAgent(enable_quality_feedback=True)

# First query - system learns
response1 = await agent.chat("What is trust?", use_schema="chain_of_thought")
# Adaptive manager learns: factual query, chain_of_thought, score 0.7

# Second query - system adapts
response2 = await agent.chat("What is uncertainty?")
# Adaptive manager suggests: use chain_of_thought for factual queries
# System automatically uses learned best schema

# View adaptive insights
insights = agent.adaptive_manager.get_performance_insights()
print(insights["schema_recommendations"])
# {"factual": {"schema": "chain_of_thought", "score": 0.75, "samples": 5}}
```

### CLI

```bash
# View adaptive learning insights
$ bop quality --adaptive

Adaptive Learning Insights

Query Type Performance:
┏━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━┓
┃ Query Type ┃ Mean Score ┃ Samples ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━┩
│ factual    │ 0.723      │ 15      │
│ procedural │ 0.689      │ 8       │
└────────────┴────────────┴─────────┘

Schema Recommendations by Query Type:
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━┓
┃ Query Type ┃ Best Schema                 ┃ Score ┃ Samples ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━┩
│ factual    │ chain_of_thought            │ 0.756 │ 10      │
│ comparative│ decompose_and_synthesize    │ 0.789 │ 5       │
└────────────┴────────────────────────────┴───────┴─────────┘

Research Effectiveness:
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Query Type ┃ With Research ┃ Without Research ┃ Improvement ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ evaluative │ 0.823         │ 0.678            │ +0.145      │
│ factual    │ 0.712         │ 0.745            │ -0.033      │
└────────────┴───────────────┴──────────────────┴─────────────┘
```

## Benefits

1. **Automatic Optimization**: System learns and adapts without manual tuning
2. **Query-Specific Strategies**: Different approaches for different query types
3. **Data-Driven Decisions**: All adaptations based on actual performance data
4. **Continuous Improvement**: Gets better with each evaluation
5. **Transparent Learning**: Can view what the system has learned

## Integration Status

✅ **Completed**:
- Adaptive quality manager implementation
- Query type classification
- Schema learning by query type
- Length optimization learning
- Research impact analysis
- Agent integration
- CLI integration with `--adaptive` flag
- Performance insights generation

✅ **Testing**:
- Unit tests for adaptive manager
- Integration tests with agent
- All tests passing

## Future Enhancements

Potential future improvements:
- Tool performance learning (which tools improve quality)
- Multi-turn conversation quality tracking
- Context-aware adaptations (adapt based on conversation history)
- User preference learning (learn user-specific preferences)
- A/B testing framework (test different strategies)

The system now not only evaluates quality but actively learns and adapts to improve quality automatically.

