# Scripts Directory

Evaluation and utility scripts for the BOP system.

## Evaluation Scripts

### Semantic Evaluation
- **`run_semantic_evaluation.py`** - Run semantic evaluation on test data
- **`run_semantic_evaluation_v2.py`** - Enhanced semantic evaluation runner

### Automated Real Data Analysis
- **`run_automated_analysis.py`** - Automated pipeline for real data analysis
  - Runs real BOP queries with research enabled
  - Collects trust metrics, source matrices, topology data
  - Performs rigorous statistical analysis
  - Outputs comprehensive reports (JSON and Markdown)

### Mutation Testing
- **`run_mutation_tests.sh`** - Mutation testing runner for agent code
  - Handles Python path configuration for mutmut
  - Runs focused agent tests to evaluate mutation coverage
  - Used by mutmut to test if mutations are caught by tests

## Usage

### Run Semantic Evaluation
```bash
python scripts/run_semantic_evaluation.py
python scripts/run_semantic_evaluation_v2.py
```

### Run Automated Analysis
```bash
# Using justfile (recommended)
just analyze-real-data
just analyze-real-data-report

# Direct execution
uv run python scripts/run_automated_analysis.py
uv run python scripts/run_automated_analysis.py --format markdown
uv run python scripts/run_automated_analysis.py --queries-file scripts/queries_for_analysis.json
```

### Run Mutation Testing
```bash
# Using justfile (recommended)
just test-mutate-quick
just test-mutate-html

# Direct execution (script is called by mutmut automatically)
# See tests/MUTATION_TESTING.md for details
```

## Integration with Tests

These scripts complement the test suite:
- Tests validate functionality
- Scripts provide interactive evaluation and analysis

## Automated Analysis Pipeline

The automated analysis pipeline (`run_automated_analysis.py`) can be:
- **Run on-demand**: `just analyze-real-data`
- **Scheduled**: Via GitHub Actions (see `.github/workflows/automated_analysis.yml`)
- **Integrated**: After evaluation runs or as part of CI/CD

Reports are saved to `analysis_output/` with timestamps for tracking over time.

