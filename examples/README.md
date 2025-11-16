# BOP Enhancement Examples

This directory contains concrete examples demonstrating all the improvements made to BOP.

## Examples

### 1. CLI Output Examples (`cli_output_example.py`)
Demonstrates the enhanced TUI features:
- Visual separators (═, ─)
- Emoji indicators (🟢🟡🔴)
- Progress bars for metrics
- Enhanced color coding
- Better section organization

**Run:**
```bash
uv run python examples/cli_output_example.py
```

**Shows:**
- Trust & Uncertainty Metrics with progress bars
- Progressive disclosure (summary vs full)
- Quality score visualization
- Knowledge visualizations section
- Belief-evidence alignment

### 2. NLTK Integration Examples (`nltk_integration_example.py`)
Demonstrates enhanced token extraction:
- NLTK-based tokenization
- POS tagging for better term selection
- Stop word filtering
- Fallback behavior

**Run:**
```bash
uv run python examples/nltk_integration_example.py
```

**Shows:**
- Basic key term extraction
- NLTK vs fallback comparison
- Domain-specific terminology extraction
- POS tagging benefits

### 3. Visualization Examples (`visualization_examples.py`)
Demonstrates visualization features:
- Source matrix heatmaps
- Token importance charts
- Document relationship graphs
- Trust metrics charts

**Run:**
```bash
uv run python examples/visualization_examples.py
```

**Shows:**
- Source agreement matrix with consensus indicators
- Token importance with visual bars
- Document clusters with trust scores
- Trust metrics with progress bars

### 4. Web UI Examples (`web_ui_example.md`)
Markdown documentation showing:
- Before/after comparisons
- Enhanced metadata display
- Progressive disclosure
- Panel layout
- Visualization summaries

**View:**
```bash
cat examples/web_ui_example.md
```

## Quick Start

Run all examples:
```bash
# CLI examples
uv run python examples/cli_output_example.py

# NLTK examples
uv run python examples/nltk_integration_example.py

# Visualization examples
uv run python examples/visualization_examples.py

# View Web UI examples
cat examples/web_ui_example.md
```

## Key Improvements Demonstrated

### Visual Hierarchy
- Clear section separation
- Emoji indicators for quick scanning
- Progress bars for quantitative metrics
- Color-coded status indicators

### Enhanced Functionality
- NLTK-enhanced token extraction
- Better visualization displays
- Progressive disclosure
- Improved metadata presentation

### Better Organization
- Clear section headers
- Logical grouping of information
- Improved readability
- Enhanced user experience

