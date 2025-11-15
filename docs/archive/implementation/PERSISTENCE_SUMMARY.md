# Persistence Summary

## Quick Reference

### Where Data is Stored

1. **Quality Feedback History**
   - **File**: `quality_history.json` (project root)
   - **Auto-saves**: After every evaluation
   - **Contains**: Query, response (truncated), response_length, score, quality flags, metadata, timestamp
   - **Rolling window**: Last 1000 evaluations

2. **Adaptive Learning Data**
   - **File**: `adaptive_learning.json` (project root)
   - **Auto-saves**: Every 10 evaluations
   - **Contains**: Learned patterns (query_type_to_schema, query_type_to_length, research_impact, tool_performance)
   - **Fallback**: Rebuilds from quality_history.json if file missing

3. **Semantic Evaluation Outputs**
   - **Directory**: `eval_outputs/` (default) or custom
   - **Manual save**: After evaluation batch
   - **Files**: JSON, CSV, Markdown reports

### How It's Managed

**Quality Feedback**:
- `QualityFeedbackLoop` manages persistence
- `_load_history()` on init
- `_save_history()` after each evaluation
- Custom path via `evaluation_history_path` parameter

**Adaptive Learning**:
- `AdaptiveQualityManager` manages persistence
- `_load_learning()` on init (tries file first, falls back to rebuilding)
- `_save_learning()` every 10 evaluations
- Custom path via `learning_data_path` parameter

**Semantic Evaluation**:
- `SemanticEvaluator` manages outputs
- Manual save via `save_judgments_json()`, `save_judgments_csv()`, `save_summary_report()`
- Custom directory via `output_dir` parameter

### Data Flow

```
Evaluation → Quality Feedback → History Entry → Save to quality_history.json
                ↓
         Adaptive Manager → Update Learning → Auto-save every 10 (adaptive_learning.json)
```

### File Locations

```
project_root/
├── quality_history.json          # Auto-saved after each evaluation
├── adaptive_learning.json        # Auto-saved every 10 evaluations
└── eval_outputs/                 # Manual save
    ├── semantic_judgments.json
    ├── semantic_judgments.csv
    └── semantic_eval_report.md
```

### Customization

```python
# Custom quality history path
feedback = QualityFeedbackLoop(
    evaluation_history_path=Path("data/quality.json")
)

# Custom adaptive learning path
manager = AdaptiveQualityManager(
    quality_feedback,
    learning_data_path=Path("data/learning.json")
)

# Custom evaluation output directory
evaluator = SemanticEvaluator(
    output_dir=Path("results/semantic")
)
```

### Key Features

- ✅ **Automatic persistence**: Quality feedback and adaptive learning auto-save
- ✅ **Response length tracking**: Explicit `response_length` field for better learning
- ✅ **Rolling window**: Quality history keeps last 1000 evaluations
- ✅ **Graceful fallback**: Adaptive learning rebuilds from history if file missing
- ✅ **Versioning**: Adaptive learning file includes version field

