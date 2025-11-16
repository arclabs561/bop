# Knowledge Display Implementation

## Overview

BOP's web UI has been enhanced with sophisticated knowledge display features based on research principles from "How to display knowledge well?". This implementation transforms BOP from a simple chat interface into a comprehensive knowledge visualization system.

## Principles Applied

### 1. Progressive Disclosure
**From Document**: "Start with the big picture to establish context, then progressively introduce foundational concepts before adding depth"

**Implementation**:
- Response tiers: `summary` → `structured` → `detailed` → `evidence`
- UI shows summary first, with "Show more details" button to expand
- Reduces cognitive load by avoiding information overload
- Users can choose their depth level

### 2. Visual Communication
**From Document**: "Visual aids condense layers of information into intuitive representations"

**Implementation**:
- **Source Matrix Heatmap**: Claims × Sources table with color-coded cells
  - Green (✓) = supports
  - Red (✗) = contradicts  
  - Gray (○) = neutral
- **Trust Metrics**: Visual bars showing source credibility scores
- **Token Importance**: Bar charts showing key terms that influenced responses
- **Source Agreement Clusters**: Visual representation of cliques

### 3. Trust and Credibility
**From Document**: "Viewers assess trustworthiness through multiple lenses: source credibility, design professionalism, transparency about methodology"

**Implementation**:
- Source credibility scores with visual bars (top 5 sources)
- Source agreement clusters (cliques) showing which sources agree
- Trust metrics from topology analysis
- Provenance traces showing which sources support which claims

### 4. Transparency and Provenance
**From Document**: "Provenance traces—not just citations, but highlighting which tokens in retrieved documents matched which parts of the query"

**Implementation**:
- **Provenance Traces**: Matches claims from source matrix to response text
- Shows supporting vs contradicting sources for each claim
- Links source agreement data to actual response content
- Enables users to understand *why* information was retrieved

### 5. Cognitive Load Management
**From Document**: "Reducing extraneous load through controlled element interactivity—limiting both the number of visual elements and the relationships between them"

**Implementation**:
- Visualizations are collapsible/expandable
- Progressive disclosure reduces initial information density
- Clear visual hierarchy (headers, sections, cards)
- Responsive design for mobile devices

### 6. Multi-Document Synthesis
**From Document**: "Source matrix method provides visual organization: create a grid with sources on one axis and key themes on the other"

**Implementation**:
- Source matrix visualization (claims × sources)
- Shows agreement/disagreement patterns
- Highlights consensus and conflicts
- Supports building intertext models

## Features

### Progressive Disclosure Tiers

```javascript
// Response tiers structure
{
  summary: "1-2 sentence direct answer",
  structured: "Organized breakdown with subproblems",
  detailed: "Full response with all details",
  evidence: "Research synthesis and source breakdown"
}
```

**UI Behavior**:
- Initially displays `summary`
- "Show more details" button expands to `detailed`
- Toggle between summary and detailed views

### Source Matrix Visualization

Heatmap-style table showing:
- **Rows**: Key claims/themes (top 8 by source count)
- **Columns**: Sources (top 6 for readability)
- **Cells**: Color-coded position (supports/contradicts/neutral)

**Visual Encoding**:
- Green background = supports
- Red background = contradicts
- Gray background = neutral
- Empty = no data

### Trust & Credibility Display

**Source Credibility**:
- Top 5 sources by credibility score
- Visual bars showing relative credibility
- Scores from 0.0 to 1.0

**Source Agreement Clusters**:
- Top 3 cliques (maximal agreement groups)
- Shows which sources agree
- Displays trust score for each cluster

### Token Importance Visualization

- Top 10 key terms that influenced the response
- Visual bars showing relative importance
- Helps users understand what drove the answer
- Useful for debugging and transparency

### Belief-Evidence Alignment

- Displays user's stated beliefs (extracted from conversation)
- Shows how evidence aligns with beliefs
- Supports transparency and trust
- Helps users see if their prior beliefs are supported

### Provenance Traces

- Matches claims from source matrix to response text
- Shows which sources support which claims
- Highlights supporting vs contradicting sources
- Links source agreement data to actual response content

## Technical Implementation

### JavaScript (`static/js/chat.js`)

**New Functions**:
- `toggleTierExpansion()` - Progressive disclosure toggle
- `createSourceMatrixVisualization()` - Source matrix heatmap
- `createTrustVisualization()` - Trust/credibility display
- `createTokenImportanceVisualization()` - Token importance bars
- `createBeliefAlignmentVisualization()` - Belief display
- `createProvenanceTraces()` - Provenance trace matching
- `formatMarkdown()` - Basic markdown support

**Enhanced Functions**:
- `updateMessage()` - Now uses response_tiers and creates visualizations
- `sendMessage()` - Passes enhanced metadata to updateMessage

### CSS (`static/css/chat.css`)

**New Styles**:
- `.knowledge-visualization` - Base visualization container
- `.source-matrix-table` - Heatmap table styling
- `.trust-metrics-grid` - Trust metrics layout
- `.term-list` - Token importance bars
- `.provenance-list` - Provenance traces
- `.tier-controls` - Progressive disclosure controls

### Server (`src/bop/server.py`)

**Already Provides** (no changes needed):
- `response_tiers` - Progressive disclosure data
- `source_matrix` - Source agreement/disagreement matrix
- `topology_metrics` - Trust, credibility, cliques
- `token_importance` - Term importance scores
- `prior_beliefs` - User belief alignment

## Alignment with Research Document

### What We Implemented

✅ **Progressive Disclosure Architecture** - Response tiers with expandable sections
✅ **Source Matrix Visualization** - Heatmap showing agreement/disagreement
✅ **Trust Indicators** - Credibility scores and agreement clusters
✅ **Provenance Traces** - Which sources support which claims
✅ **Token Importance** - Key terms that influenced responses
✅ **Belief Alignment** - User beliefs and evidence alignment
✅ **Cognitive Load Management** - Collapsible visualizations

### What Could Be Enhanced (Future Work)

⏳ **Context-Adaptive Presentation** - Exploration vs extraction modes
⏳ **Interactive Filtering** - Filter sources, claims, or time periods
⏳ **Temporal Evolution** - How understanding changed over time
⏳ **Collaborative Annotation** - Team annotations and disagreements
⏳ **Fatigue-Aware Degradation** - Simplify when user shows fatigue signals
⏳ **Better Claim-to-Source Matching** - Semantic similarity instead of keyword matching

## Usage

### For Users

1. **Progressive Disclosure**: Start with summary, expand when needed
2. **Source Matrix**: Review which sources agree/disagree on claims
3. **Trust Metrics**: Check source credibility before trusting information
4. **Provenance Traces**: See which sources support specific claims
5. **Token Importance**: Understand what drove the response

### For Developers

All visualizations are automatically created when:
- `response_tiers` is provided (progressive disclosure)
- `source_matrix` is provided (source matrix + provenance traces)
- `topology_metrics` is provided (trust/credibility)
- `token_importance` is provided (token importance)
- `prior_beliefs` is provided (belief alignment)

## Examples

### Example Response with All Features

```json
{
  "response": "D-separation is a graphical criterion...",
  "response_tiers": {
    "summary": "D-separation determines conditional independence in Bayesian networks.",
    "detailed": "D-separation is a graphical criterion... [full response]",
    "evidence": "[research synthesis]"
  },
  "source_matrix": {
    "d-separation determines independence": {
      "sources": {
        "perplexity_deep_research": "supports",
        "arxiv_search": "supports"
      }
    }
  },
  "topology_metrics": {
    "source_credibility": {
      "perplexity_deep_research": 0.85,
      "arxiv_search": 0.90
    },
    "cliques": [
      {
        "node_sources": ["perplexity", "arxiv"],
        "trust": 0.88
      }
    ]
  }
}
```

**UI Displays**:
1. Summary text with "Show more details" button
2. Source matrix heatmap (2 claims × 2 sources)
3. Trust metrics (credibility bars + clique)
4. Provenance traces (claims matched to response)

## Benefits

1. **Reduced Cognitive Load**: Progressive disclosure prevents overwhelm
2. **Increased Trust**: Transparency about sources and credibility
3. **Better Understanding**: Visualizations make relationships clear
4. **Provenance**: Users can verify claims against sources
5. **Accessibility**: Clear visual hierarchy and keyboard navigation

## Future Enhancements

Based on the research document, potential improvements:

1. **Context-Adaptive Modes**: Detect exploration vs extraction and adapt UI
2. **Interactive Filtering**: Filter by source, time, or credibility
3. **Temporal Evolution**: Show how understanding changed over time
4. **Better Matching**: Use semantic similarity for claim-to-source matching
5. **Fatigue Detection**: Simplify UI when user shows fatigue signals
6. **Collaborative Features**: Team annotations and disagreement tracking

## References

- "How to display knowledge well?" - Research document with principles
- BOP Architecture Guide (`AGENTS.md`) - System architecture
- Knowledge Display Guide (`KNOWLEDGE_DISPLAY_GUIDE.md`) - User guide

