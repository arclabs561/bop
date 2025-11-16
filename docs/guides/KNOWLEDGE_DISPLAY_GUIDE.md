# Knowledge Display Guide

## Overview

BOP provides comprehensive knowledge display features that make trust, uncertainty, and source relationships transparent. This guide explains how to interpret and use these features.

## Trust Metrics

### Trust Summary

The trust summary provides an overview of trust in the knowledge network:

```python
trust_summary = response["research"]["topology"]["trust_summary"]
```

**Metrics**:
- **avg_trust**: Average trust score across all connections (0.0 to 1.0)
- **avg_credibility**: Average source credibility (0.0 to 1.0)
- **avg_confidence**: Average structural confidence (0.0 to 1.0)
- **calibration_error**: Expected Calibration Error (ECE) - how well confidence matches accuracy
- **high_trust_edges**: Number of high-trust connections (>0.7)
- **low_trust_edges**: Number of low-trust connections (<0.3)
- **schema_violations**: Number of detected schema inconsistencies

**Interpretation**:
- **High trust (>0.7)**: Strong agreement and reliable sources
- **Medium trust (0.5-0.7)**: Moderate reliability, review carefully
- **Low trust (<0.5)**: Weak support, verify independently
- **Calibration error <0.1**: Excellent calibration
- **Calibration error 0.1-0.2**: Good calibration
- **Calibration error >0.2**: Needs improvement - trust scores may be unreliable

### Source Credibility

Per-source credibility scores indicate how trustworthy each source type is:

```python
source_cred = response["research"]["topology"]["source_credibility"]
# Example: {"perplexity_deep_research": 0.75, "tavily_search": 0.60}
```

**Interpretation**:
- **High (>0.7)**: Generally reliable source
- **Medium (0.5-0.7)**: Moderately reliable, verify important claims
- **Low (<0.5)**: Less reliable, use with caution

### Verification Counts

Verification counts show how many independent sources have verified claims:

```python
verification_info = response["research"]["topology"]["verification_info"]
# Example: {"perplexity": {"verification_count": 5, "nodes": 3}}
```

**Interpretation**:
- **High verification count**: Multiple independent verifications increase confidence
- **Low verification count**: Single source, verify independently
- **Source diversity**: Check that verifications come from different source types

## Source Agreement Clusters

Cliques represent groups of sources that agree on claims:

```python
cliques = response["research"]["topology"]["cliques"]
```

**Clique Properties**:
- **node_sources**: List of sources in the cluster
- **source_diversity**: Number of different source types
- **verification_count**: Total verifications across cluster
- **trust**: Trust score for the cluster
- **coherence**: How well sources agree
- **risk**: Adversarial risk score

**Interpretation**:
- **High trust + high diversity**: Strong consensus from diverse sources
- **High trust + low diversity**: Consensus but from similar sources (verify with different types)
- **Low trust**: Weak agreement, verify independently

## Source Agreement Matrix

The source matrix shows agreement/disagreement patterns across sources:

```python
source_matrix = response["research"]["source_matrix"]
```

**Structure**:
```python
{
    "claim_phrase": {
        "sources": {
            "perplexity_deep_research": "supports",
            "tavily_search": "contradicts",
            "firecrawl_scrape": "neutral"
        },
        "consensus": "strong_agreement" | "weak_agreement" | "disagreement" | "no_consensus",
        "conflict": bool
    }
}
```

**Interpretation**:
- **strong_agreement**: >70% of sources support the claim
- **weak_agreement**: 50-70% of sources support
- **disagreement**: Sources contradict each other
- **no_consensus**: No clear agreement pattern

## Belief-Evidence Alignment

When you state beliefs explicitly, BOP tracks and aligns evidence:

```python
# State a belief
response1 = await agent.chat("I think trust is crucial for systems")

# Check alignment in subsequent queries
response2 = await agent.chat("How does uncertainty affect trust?")
prior_beliefs = response2.get("prior_beliefs", [])
```

**Belief Alignment Scores** (in topology nodes):
- **0.7-1.0**: Strong alignment with your beliefs
- **0.5-0.7**: Weak alignment
- **0.3-0.5**: Weak contradiction
- **0.0-0.3**: Strong contradiction

**Interpretation**:
- **High alignment**: Evidence confirms your beliefs
- **Low alignment/contradiction**: Evidence challenges your beliefs - review carefully

## Progressive Disclosure

Responses are organized in tiers for progressive disclosure:

```python
tiers = response["response_tiers"]
```

**Tiers**:
1. **summary**: 1-2 sentence direct answer (quick overview)
2. **structured**: Organized breakdown by subproblem
3. **detailed**: Full response with all details
4. **evidence**: Complete research synthesis with tool results

**Usage**:
- Start with `summary` for quick answers
- Use `structured` for organized overview
- Expand to `detailed` for full information
- Use `evidence` for complete research provenance

## Context-Dependent Adaptation

BOP automatically adapts response detail based on query patterns:

**Exploration Mode** (similar topics):
- System detects you're diving deeper into a topic
- Increases detail level by ~20%
- Provides more comprehensive responses

**Extraction Mode** (different topics):
- System detects you want quick answers
- Decreases detail level by ~20%
- Provides concise, focused responses

**Manual Override**: Currently automatic, but you can access different tiers manually.

## Best Practices

1. **Review Trust Scores**: For important decisions, check trust metrics
2. **Check Source Diversity**: Prefer consensus from diverse source types
3. **Verify Conflicts**: When sources disagree, investigate further
4. **Use Progressive Disclosure**: Start with summary, expand as needed
5. **State Beliefs Explicitly**: Use "I think" or "I believe" to enable alignment
6. **Monitor Calibration**: High calibration error means trust scores may be unreliable
7. **Review Verification Counts**: More verifications = higher confidence

## Display Helpers

Use display helpers for formatted output:

```python
from bop.display_helpers import (
    format_trust_summary,
    format_source_credibility,
    format_clique_clusters,
    create_trust_table,
)

# Format trust summary with explanations
trust_text = format_trust_summary(trust_summary)

# Format source credibility
cred_text = format_source_credibility(source_credibility)

# Format clique clusters
cliques_text = format_clique_clusters(cliques)

# Create Rich table
from rich.console import Console
console = Console()
table = create_trust_table(trust_summary, source_credibility)
console.print(table)
```

## See Also

- `AGENTS.md` - Agent usage patterns
- `ARCHITECTURE.md` - Theoretical foundations
- `TRUST_UNCERTAINTY_RESEARCH_SYNTHESIS.md` - Research on trust modeling

