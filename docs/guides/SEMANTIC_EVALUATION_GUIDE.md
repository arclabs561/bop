# Semantic Evaluation Guide

## Overview

The semantic evaluation framework produces **transparent, aggregatable judgments** on realistic data, enabling data-driven decision-making about system quality.

## Key Features

### 1. Semantic Judgments (Not Just Pass/Fail)

Each evaluation produces a `SemanticJudgment` with:
- **Score**: 0.0 to 1.0 (semantic quality measure)
- **Reasoning**: Transparent explanation of the score
- **Evidence**: Specific evidence supporting the judgment
- **Confidence**: How confident we are in the judgment
- **Metadata**: Context (schema used, research conducted, etc.)

### 2. Multiple Evaluation Types

- **Accuracy**: Does response contain expected concepts?
- **Completeness**: Does response cover the context adequately?
- **Relevance**: Is response semantically relevant to query?
- **Consistency**: Are responses consistent across methods?

### 3. Transparent Output Formats

#### JSON (`semantic_judgments.json`)
- Complete judgment data
- Aggregated statistics
- Machine-readable for further analysis

#### CSV (`semantic_judgments.csv`)
- Tabular format for spreadsheet analysis
- Easy filtering and sorting
- Metadata as columns

#### Markdown Report (`semantic_eval_report.md`)
- Human-readable summary
- Statistics by judgment type
- Actionable recommendations

## Usage

### Command Line

```bash
# Basic semantic evaluation
uv run bop semantic-eval --content-dir content --output-dir eval_outputs

# Comprehensive evaluation
uv run python scripts/run_semantic_evaluation.py \
    --content-dir content \
    --output-dir semantic_eval_outputs
```

### Programmatic

```python
from bop.semantic_eval import SemanticEvaluator
from bop.agent import KnowledgeAgent

evaluator = SemanticEvaluator(output_dir="eval_outputs")
agent = KnowledgeAgent()

# Evaluate accuracy
response = await agent.chat("What is trust?", use_schema="chain_of_thought")
judgment = evaluator.evaluate_accuracy(
    query="What is trust?",
    response=response["response"],
    expected_concepts=["trust", "confidence", "reliability"],
    metadata={"schema": "chain_of_thought"},
)

# Save results
evaluator.save_judgments_json()
evaluator.save_judgments_csv()
evaluator.save_summary_report()

# Get aggregate statistics
aggregate = evaluator.aggregate_judgments()
print(f"Mean score: {aggregate['overall']['mean_score']:.3f}")
```

## Making Decisions from Results

### 1. View Aggregate Statistics

```bash
cat semantic_eval_outputs/comprehensive_report.md
```

Look for:
- **Overall mean score**: System-wide quality
- **By judgment type**: Which aspects need improvement
- **Score range**: Consistency of quality
- **Standard deviation**: Variability

### 2. Analyze CSV in Spreadsheet

```bash
# Open in Excel/Google Sheets
open semantic_eval_outputs/comprehensive_judgments.csv
```

Filter by:
- `judgment_type` - Which evaluation type
- `schema` - Which schema performs best
- `research` - Does research improve quality?
- `score` - Identify low performers

### 3. Review Individual Judgments

```bash
cat semantic_eval_outputs/comprehensive_judgments.json | jq '.judgments[] | select(.score < 0.6)'
```

Find low-scoring judgments and review:
- `reasoning` - Why the score is low
- `evidence` - What was found/missing
- `metadata` - Context (schema, research, etc.)

### 4. Decision-Making Workflow

1. **Run evaluation** on realistic data
2. **Review aggregate report** for overall trends
3. **Analyze CSV** to identify patterns
4. **Examine low performers** to understand issues
5. **Make informed decisions**:
   - Which schemas work best?
   - Does research improve quality?
   - What concepts are being missed?
   - Where is consistency lacking?

## Example Analysis

### Question: "Which schema performs best?"

```python
import pandas as pd

df = pd.read_csv("semantic_eval_outputs/comprehensive_judgments.csv")
schema_scores = df.groupby("schema")["score"].mean()
print(schema_scores.sort_values(ascending=False))
```

### Question: "Does research improve quality?"

```python
research_scores = df[df["research"] == True]["score"].mean()
no_research_scores = df[df["research"] == False]["score"].mean()
print(f"With research: {research_scores:.3f}")
print(f"Without research: {no_research_scores:.3f}")
```

### Question: "What concepts are being missed?"

```python
low_scores = df[df["score"] < 0.6]
# Review reasoning and evidence for these
for _, row in low_scores.iterrows():
    print(f"Query: {row['query']}")
    print(f"Reasoning: {row['reasoning']}")
    print()
```

## Best Practices

1. **Use realistic data**: Evaluate on actual content, not synthetic
2. **Track metadata**: Include schema, research, document info
3. **Review reasoning**: Understand why scores are what they are
4. **Aggregate transparently**: Use provided aggregation methods
5. **Make data-driven decisions**: Base improvements on evidence

## Output Structure

```
semantic_eval_outputs/
├── comprehensive_judgments.json    # Complete data
├── comprehensive_judgments.csv     # Analysis-friendly
└── comprehensive_report.md         # Human-readable summary
```

## Integration with Tests

Semantic evaluation tests are in:
- `tests/test_semantic_evaluation.py` - Basic semantic evaluation
- `tests/test_semantic_realistic.py` - Realistic data evaluation
- `tests/test_semantic_aggregation.py` - Aggregation and transparency

Run with:
```bash
uv run pytest tests/test_semantic_*.py -v
```

