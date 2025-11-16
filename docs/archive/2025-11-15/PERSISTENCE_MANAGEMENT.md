# Persistence Management

## Overview

The quality feedback system uses file-based persistence to maintain learning across sessions. This document explains where data is stored, how it's managed, and what gets persisted.

## Persistence Locations

### 1. Quality Feedback History

**File**: `quality_history.json` (in project root by default)

**Managed by**: `QualityFeedbackLoop` class

**Location Control**:
```python
# Default location (project root)
feedback = QualityFeedbackLoop()
# quality_history.json in current directory

# Custom location
feedback = QualityFeedbackLoop(evaluation_history_path=Path("data/quality.json"))
# data/quality.json
```

**What's Stored**:
- All evaluation judgments (last 1000, rolling window)
- Performance summary (aggregated statistics)
- Schema performance scores
- Query type performance scores
- Quality issue frequency counts

**File Structure**:
```json
{
  "history": [
    {
      "query": "What is trust?",
      "score": 0.723,
      "judgment_type": "relevance",
      "quality_flags": [],
      "reasoning": "...",
      "metadata": {
        "schema": "chain_of_thought",
        "research": false
      },
      "timestamp": "2025-11-14T13:20:12.211362"
    }
  ],
  "summary": {
    "total_evaluations": 50,
    "recent_mean_score": 0.723,
    "schema_performance": {
      "chain_of_thought": 0.689,
      "decompose_and_synthesize": 0.756
    },
    "quality_issue_frequency": {
      "placeholder": 5,
      "error": 2
    },
    "trend": "improving"
  }
}
```

### 2. Semantic Evaluation Outputs

**Directory**: `eval_outputs/` or custom via `output_dir` parameter

**Managed by**: `SemanticEvaluator` class

**Location Control**:
```python
# Default location
evaluator = SemanticEvaluator()
# eval_outputs/ directory

# Custom location
evaluator = SemanticEvaluator(output_dir=Path("results/semantic"))
# results/semantic/ directory
```

**What's Stored**:
- `semantic_judgments.json`: All judgments with full details
- `semantic_judgments.csv`: Tabular format for analysis
- `semantic_eval_report.md`: Human-readable summary report

**Files Created**:
- `semantic_judgments.json`: Complete judgment data
- `semantic_judgments.csv`: CSV format for spreadsheet analysis
- `semantic_eval_report.md`: Markdown report with statistics

### 3. Adaptive Quality Learning

**File**: `adaptive_learning.json` (in same directory as quality_history.json)

**Managed by**: `AdaptiveQualityManager` class

**Current Behavior**:
- Learning data is persisted to disk
- Auto-saves every 10 evaluations
- Loads on initialization if file exists
- Falls back to rebuilding from `quality_history.json` if file missing

**Data Structures** (persisted):
- `query_type_to_schema`: Dict mapping query types to schema performance
- `query_type_to_length`: Dict mapping query types to length preferences
- `research_impact`: Dict tracking research effectiveness
- `tool_performance`: Dict tracking tool performance

**Save Process**:
```python
def _save_learning(self):
    """Save learning data to disk."""
    data = {
        "version": "1.0",
        "query_type_to_schema": {...},
        "query_type_to_length": {...},
        "research_impact": {...},
        "tool_performance": {...},
    }
    self.learning_data_path.write_text(json.dumps(data, indent=2))
```

**Load Process**:
```python
def _load_learning(self) -> bool:
    """Load persisted learning data."""
    if not self.learning_data_path.exists():
        return False  # Fall back to rebuilding from history
    
    data = json.loads(self.learning_data_path.read_text())
    # Rebuild learning structures from persisted data
    ...
    return True
```

**Auto-Save Trigger**:
- Every 10 evaluations (in `update_from_evaluation`)
- Can be manually triggered with `save_learning()`

## Persistence Mechanisms

### Quality Feedback Loop

**Save Trigger**:
- Automatically after every `evaluate_and_learn()` call
- Can be manually triggered with `_save_history()`

**Save Process**:
```python
def _save_history(self):
    """Save evaluation history to disk."""
    data = {
        "history": self.history[-1000:],  # Keep last 1000 evaluations
        "summary": self.get_performance_summary(),
    }
    self.evaluation_history_path.parent.mkdir(parents=True, exist_ok=True)
    self.evaluation_history_path.write_text(json.dumps(data, indent=2))
```

**Load Process**:
```python
def _load_history(self):
    """Load evaluation history from disk."""
    if self.evaluation_history_path.exists():
        try:
            data = json.loads(self.evaluation_history_path.read_text())
            self.history = data.get("history", [])
            # Rebuild performance tracking from history
            for entry in self.history:
                schema = entry.get("metadata", {}).get("schema")
                if schema:
                    self.schema_scores[schema].append(entry.get("score", 0))
                # ... rebuild other tracking structures
        except Exception:
            self.history = []  # Graceful failure
```

**Rolling Window**:
- Only last 1000 evaluations kept in file
- Prevents unbounded growth
- Older evaluations still contribute to aggregated statistics

### Semantic Evaluator

**Save Trigger**:
- Manual: `save_judgments_json()`, `save_judgments_csv()`, `save_summary_report()`
- Typically called after evaluation batch completes

**Save Process**:
```python
def save_judgments_json(self, filename: str = "semantic_judgments.json") -> Path:
    """Save all judgments as JSON."""
    output_path = self.output_dir / filename
    data = {
        "judgments": [asdict(j) for j in self.judgments],
        "aggregate": self.aggregate_judgments(),
    }
    output_path.write_text(json.dumps(data, indent=2))
    return output_path
```

**No Auto-Load**:
- Semantic evaluator doesn't auto-load previous judgments
- Each evaluation session starts fresh
- Judgments are append-only within a session

## Data Lifecycle

### Quality Feedback History

```
Session 1:
  - Evaluate response → Store in memory → Save to quality_history.json
  - Next evaluation → Append to memory → Save (overwrites file)
  
Session 2:
  - Initialize → Load from quality_history.json → Rebuild tracking structures
  - Evaluate response → Store in memory → Save to quality_history.json
```

### Adaptive Quality Learning

```
Session 1:
  - Initialize → Load quality_history.json → Rebuild learning structures
  - Evaluate → Update learning structures (in-memory)
  - Process ends → Learning structures lost
  
Session 2:
  - Initialize → Load quality_history.json → Rebuild learning structures
  - Learning structures rebuilt from persisted history
```

## Persistence Gaps

### Current Limitations

1. **Adaptive Learning Not Persisted**
   - Learning structures are rebuilt from history each time
   - No explicit persistence of learned patterns
   - Works but may be slower on large histories

2. **No Incremental Updates**
   - Quality history file is rewritten entirely on each save
   - Could be optimized with append-only log + periodic compaction

3. **No Versioning**
   - No schema versioning for history format
   - Could break if format changes

4. **No Backup/Recovery**
   - No automatic backups
   - No recovery mechanism if file is corrupted

## Recommendations

### Short-term Improvements

1. **Persist Adaptive Learning**
   ```python
   # Add to adaptive_quality.py
   def save_learning(self, path: Path):
       """Save learned patterns to disk."""
       data = {
           "query_type_to_schema": self.query_type_to_schema,
           "query_type_to_length": self.query_type_to_length,
           "research_impact": self.research_impact,
           "tool_performance": self.tool_performance,
       }
       path.write_text(json.dumps(data, indent=2))
   ```

2. **Incremental History Updates**
   - Use append-only log for new evaluations
   - Periodic compaction to maintain 1000-item window
   - Faster writes, better for high-frequency evaluation

3. **Configuration for Paths**
   - Environment variable for default paths
   - Config file for custom paths
   - Better organization of persisted data

### Long-term Improvements

1. **Database Backend**
   - SQLite for structured queries
   - Better performance for large histories
   - Easier analytics and reporting

2. **Versioning**
   - Schema version in persisted files
   - Migration scripts for format changes
   - Backward compatibility

3. **Backup/Recovery**
   - Automatic backups (daily/weekly)
   - Corruption detection and recovery
   - Export/import functionality

## Current File Locations

**Default Locations** (project root):
- `quality_history.json`: Quality feedback history
- `eval_outputs/`: Semantic evaluation outputs
- `semantic_eval_diverse/`: Diverse evaluation outputs (if run)
- `semantic_eval_v2/`: Iteration 2 outputs (if run)

**Customizable**:
- Quality history: `QualityFeedbackLoop(evaluation_history_path=...)`
- Evaluation outputs: `SemanticEvaluator(output_dir=...)`

## Accessing Persisted Data

### Programmatic Access

```python
from pathlib import Path
import json
from bop.quality_feedback import QualityFeedbackLoop

# Load history
feedback = QualityFeedbackLoop()
history = feedback.history  # Already loaded

# Or load directly
history_path = Path("quality_history.json")
if history_path.exists():
    data = json.loads(history_path.read_text())
    history = data["history"]
    summary = data["summary"]
```

### CLI Access

```bash
# View quality history summary
bop quality

# View with history details
bop quality --history

# View adaptive insights (rebuilds from history)
bop quality --adaptive
```

## Summary

**Persisted**:
- ✅ Quality feedback history (`quality_history.json`)
- ✅ Semantic evaluation outputs (JSON, CSV, Markdown reports)

**Persisted** (with auto-save):
- ✅ Adaptive learning structures (`adaptive_learning.json`) - auto-saves every 10 evaluations
- ✅ Performance tracking structures (in quality_history.json)

**Rebuilt from History** (if learning file missing):
- ⚠️ Adaptive learning structures (fallback: rebuilt from quality history)

**Persistence Model**:
- Quality feedback: Auto-save after each evaluation
- Semantic evaluation: Manual save after batch
- Adaptive learning: Rebuilt from quality history on init

The system maintains continuity through the quality history file, which serves as the single source of truth for all learning and adaptation.

## Current Implementation Details

### Quality Feedback Persistence

**File**: `quality_history.json` (default: project root)

**Save Trigger**: After every `evaluate_and_learn()` call

**Save Method**: Complete file rewrite (JSON)

**Load Trigger**: On `QualityFeedbackLoop` initialization

**Rolling Window**: Last 1000 evaluations kept

**Rebuilds On Load**:
- `schema_scores`: Rebuilt from history entries
- `query_type_scores`: Rebuilt from history entries  
- `quality_issue_counts`: Rebuilt from history entries

### Adaptive Learning Persistence

**Status**: NOT directly persisted

**Rebuild Method**: `_learn_from_history()` called on init

**Data Rebuilt**:
- `query_type_to_schema`: From history entries
- `query_type_to_length`: From history entries (requires response in history)
- `research_impact`: From history entries
- `tool_performance`: From history entries (if tools tracked)

**Limitation**: Response text not stored in quality history, so length learning requires response to be in history entry

### Semantic Evaluation Persistence

**Directory**: `eval_outputs/` (default) or custom `output_dir`

**Save Methods**:
- `save_judgments_json()`: Complete judgment data
- `save_judgments_csv()`: Tabular format
- `save_summary_report()`: Markdown report

**Save Trigger**: Manual (typically after evaluation batch)

**No Auto-Load**: Each session starts fresh

## File Locations Summary

```
project_root/
├── quality_history.json          # Quality feedback history (auto-saved)
├── eval_outputs/                  # Semantic evaluation outputs (manual save)
│   ├── semantic_judgments.json
│   ├── semantic_judgments.csv
│   └── semantic_eval_report.md
├── semantic_eval_diverse/         # Custom evaluation outputs
└── semantic_eval_v2/              # Iteration 2 outputs
```

## Customization

### Custom Quality History Path

```python
from pathlib import Path
from bop.quality_feedback import QualityFeedbackLoop

# Custom location
feedback = QualityFeedbackLoop(
    evaluation_history_path=Path("data/quality.json")
)
```

### Custom Evaluation Output Directory

```python
from pathlib import Path
from bop.semantic_eval import SemanticEvaluator

# Custom output directory
evaluator = SemanticEvaluator(
    output_dir=Path("results/semantic")
)
```

### Agent with Custom Paths

```python
from pathlib import Path
from bop.agent import KnowledgeAgent
from bop.quality_feedback import QualityFeedbackLoop

# Create custom feedback loop
feedback = QualityFeedbackLoop(
    evaluation_history_path=Path("data/quality.json")
)

# Agent uses default (can't customize via agent init currently)
agent = KnowledgeAgent(enable_quality_feedback=True)
# Uses default quality_history.json
```

## Data Flow

### Quality Feedback Lifecycle

```
1. Agent.chat() called
   ↓
2. Response generated
   ↓
3. QualityFeedbackLoop.evaluate_and_learn()
   ↓
4. Evaluation performed
   ↓
5. Entry added to self.history (in-memory)
   ↓
6. Performance tracking updated (in-memory)
   ↓
7. _save_history() called automatically
   ↓
8. quality_history.json written (complete file rewrite)
```

### Adaptive Learning Lifecycle

```
1. AdaptiveQualityManager.__init__()
   ↓
2. _learn_from_history() called
   ↓
3. Iterate through quality_feedback.history
   ↓
4. Rebuild learning structures:
   - query_type_to_schema
   - query_type_to_length
   - research_impact
   - tool_performance
   ↓
5. Learning structures ready (in-memory)
   ↓
6. Process ends → Structures lost
   ↓
7. Next init → Rebuild from history again
```

## Persistence Gaps & Improvements Needed

### Current Issues

1. **Adaptive Learning Not Persisted**
   - Learning structures rebuilt from history each time
   - Slower initialization with large histories
   - No explicit persistence of learned patterns

2. **Response Text Not Always in History**
   - Quality history may not include full response text
   - Length learning requires response to be in entry
   - Current: Response truncated to 500 chars in judgment

3. **No Incremental Updates**
   - Complete file rewrite on each save
   - Could be slow with large histories
   - No append-only log option

4. **No Versioning**
   - No schema version in persisted files
   - Format changes could break loading
   - No migration path

### Recommended Improvements

1. **Persist Adaptive Learning**
   ```python
   # Add to AdaptiveQualityManager
   def save_learning(self, path: Path):
       data = {
           "version": "1.0",
           "query_type_to_schema": dict(self.query_type_to_schema),
           "query_type_to_length": dict(self.query_type_to_length),
           "research_impact": dict(self.research_impact),
           "tool_performance": dict(self.tool_performance),
       }
       path.write_text(json.dumps(data, indent=2))
   
   def load_learning(self, path: Path):
       if path.exists():
           data = json.loads(path.read_text())
           # Load structures
   ```

2. **Include Response in History**
   - Store full response (or at least enough for length analysis)
   - Or store response length explicitly in metadata

3. **Incremental History Updates**
   - Append-only log for new entries
   - Periodic compaction to maintain window
   - Faster writes, better for high-frequency evaluation

4. **Versioning & Migration**
   - Add version field to persisted files
   - Migration functions for format changes
   - Backward compatibility checks

