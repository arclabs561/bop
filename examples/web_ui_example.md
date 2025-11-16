# Web UI Enhancement Examples

## Before vs After

### Before (Basic Display)
```
### BOP
D-separation is a graphical criterion...

*🔍 Research • 📋 decompose_and_synthesize • ⭐ 0.75*
```

### After (Enhanced Display)
```
### 🧠 BOP

D-separation is a graphical criterion...

---

**🟢 Quality Score:** 0.75

**🟢 Average Trust:** 0.82

**🔑 Key Terms Driving Retrieval:**
`d-separation`, `bayesian`, `independence`, `graph`, `causal`, `networks`, `conditional`, `variables`

**📊 Source Agreement:** 5 claims analyzed (3 with strong agreement)

*💡 Full details available - click to expand*
```

## Enhanced Metadata Display

### Quality Score with Color Coding
- 🟢 **High Quality** (≥0.7): Green indicator
- 🟡 **Medium Quality** (0.5-0.7): Yellow indicator  
- 🔴 **Low Quality** (<0.5): Red indicator

### Trust Metrics
- **Average Trust**: Visual indicator with color coding
- **Source Credibility**: Per-source breakdown
- **Verification Counts**: Number of verifications per source

### Visualization Summaries
When `Show Visualizations` is enabled:

```
**🔑 Key Terms Driving Retrieval:**
`d-separation`, `bayesian`, `independence`, `graph`, `causal`

**📊 Source Agreement:** 5 claims analyzed (3 with strong agreement)
```

## Progressive Disclosure

### Summary View (Default)
```
### 🧠 BOP

D-separation is a graphical criterion for determining conditional 
independence in Bayesian networks...

---

*💡 Full details available - click to expand*
```

### Detailed View (Expanded)
```
### 🧠 BOP

# D-Separation

D-separation is a fundamental concept in causal inference...

[Full detailed response with all sections]

---

**🟢 Quality Score:** 0.85
**🟢 Average Trust:** 0.82
**🔑 Key Terms:** d-separation, bayesian, independence...
**📊 Source Agreement:** 5 claims analyzed
```

## Panel Layout

### Settings Section
```
### ⚙️ Settings

[Enable Research] [Show Visualizations] [Exploration Mode]

[Reasoning Schema: Auto (Adaptive ▼]
```

### Ask a Question Section
```
### 💭 Ask a Question

[Text area for input...] [Send Button]
```

## Enhanced Message Display

### User Message
```
### 👤 You

What is d-separation?

---
```

### Assistant Response
```
### 🧠 BOP

[Response content with progressive disclosure]

---

🔍 **Research** • 📋 **Decompose And Synthesize** • 🟢 **Quality: 0.85**

*💡 Full details available - click to expand*
```

## Visualization Data Storage

When visualizations are enabled, the system stores:
- `source_matrix`: Source agreement/disagreement data
- `token_importance`: Key terms and importance scores
- `topology`: Trust metrics, cliques, credibility

This data is available for interactive exploration in the UI.

