# Trust and Uncertainty User Guide

## Overview

This guide explains how to interpret trust scores, uncertainty metrics, and source credibility in BOP's responses. Understanding these metrics helps you make informed decisions about the reliability of information.

## Understanding Trust Scores

### What is Trust?

Trust in BOP represents the reliability of information based on:
- **Source credibility**: How trustworthy the source is
- **Structural confidence**: How well-supported the claim is by the knowledge network
- **Verification count**: How many independent sources confirm it
- **Belief alignment**: How well it aligns with your stated beliefs

### Trust Score Ranges

**High Trust (0.7 - 1.0)**:
- Strong agreement from reliable sources
- Multiple independent verifications
- Well-supported by network structure
- **Action**: You can generally rely on this information

**Medium Trust (0.5 - 0.7)**:
- Moderate agreement or support
- Some verification but limited
- **Action**: Review carefully, verify important claims independently

**Low Trust (0.0 - 0.5)**:
- Weak support or disagreement
- Limited verification
- May contradict trusted sources
- **Action**: Verify independently before relying on this

## Calibration Error

### What is Calibration Error?

Calibration error (ECE - Expected Calibration Error) measures how well confidence scores match actual accuracy. It's the difference between what the system thinks it knows and what it actually knows.

### Interpreting Calibration Error

**Excellent (< 0.1)**:
- Trust scores are highly reliable
- System confidence matches reality
- **Action**: You can trust the trust scores

**Good (0.1 - 0.2)**:
- Trust scores are generally reliable
- Minor discrepancies possible
- **Action**: Trust scores are mostly reliable, but be slightly cautious

**Needs Improvement (> 0.2)**:
- Trust scores may be unreliable
- System may be overconfident or underconfident
- **Action**: Don't rely solely on trust scores, verify independently

### Why Calibration Matters

If calibration error is high:
- **Overconfidence**: System says "high trust" but information is actually unreliable
- **Underconfidence**: System says "low trust" but information is actually reliable
- Either way, you can't trust the trust scores themselves

## Source Credibility

### What is Source Credibility?

Source credibility is a score (0.0 to 1.0) indicating how trustworthy each source type is based on:
- Historical reliability
- Source type characteristics
- Verification patterns

### Source Types and Typical Credibility

**High Credibility (>0.7)**:
- Academic papers (arXiv)
- Deep research tools (Perplexity deep research)
- **Interpretation**: Generally reliable, but still verify critical claims

**Medium Credibility (0.5-0.7)**:
- General search tools (Tavily, Firecrawl)
- Web scraping
- **Interpretation**: Moderately reliable, verify important information

**Low Credibility (<0.5)**:
- Unverified sources
- Low-quality sources
- **Interpretation**: Use with caution, always verify

### Important Notes

- Credibility is per source type, not per individual result
- A high-credibility source can still produce unreliable information
- A low-credibility source can still produce reliable information
- Always consider context and verification count

## Verification Counts

### What is Verification?

Verification means multiple independent sources confirm the same claim. Higher verification counts increase confidence.

### Interpreting Verification Counts

**High Verification (3+)**:
- Multiple independent sources agree
- Strong consensus
- **Action**: High confidence in accuracy

**Medium Verification (1-2)**:
- Some agreement
- Limited consensus
- **Action**: Moderate confidence, verify if important

**No Verification (0)**:
- Single source
- No independent confirmation
- **Action**: Low confidence, verify independently

### Source Diversity

**High Diversity**:
- Verifications come from different source types (academic, news, technical)
- Stronger consensus
- **Action**: Higher confidence

**Low Diversity**:
- Verifications come from similar source types
- Weaker consensus (may be echo chamber)
- **Action**: Verify with different source types

## Belief-Evidence Alignment

### What is Belief Alignment?

Belief alignment measures how well new evidence aligns with your stated beliefs. When you say "I think X", the system tracks this and compares new evidence to it.

### Alignment Scores

**Strong Alignment (0.7-1.0)**:
- Evidence confirms your beliefs
- Consistent with what you think
- **Note**: High alignment can reduce trust if uncertainty is high (you may be overconfident)

**Weak Alignment (0.5-0.7)**:
- Evidence partially aligns
- Some consistency
- **Action**: Review carefully

**Weak Contradiction (0.3-0.5)**:
- Evidence partially contradicts
- Some inconsistency
- **Action**: This challenges your beliefs - review carefully

**Strong Contradiction (0.0-0.3)**:
- Evidence strongly contradicts
- Major inconsistency
- **Action**: This strongly challenges your beliefs - investigate thoroughly

### Why Alignment Matters

**When Evidence Aligns with Beliefs**:
- You may trust it more than you should
- Uncertainty communication becomes more important
- **Action**: Be aware of confirmation bias

**When Evidence Contradicts Beliefs**:
- You may dismiss it too quickly
- Uncertainty communication can increase trust (shows system is being careful)
- **Action**: Don't dismiss contradictory evidence - investigate it

## Source Agreement Matrix

### What is the Source Matrix?

The source matrix shows which sources agree or disagree on specific claims. It helps identify consensus vs. conflicts.

### Matrix Structure

For each claim, you'll see:
- **Sources**: Which sources support, contradict, or are neutral
- **Consensus**: Overall agreement pattern
- **Conflict**: Whether sources disagree

### Consensus Types

**Strong Agreement**:
- >70% of sources support the claim
- **Action**: High confidence, but check source diversity

**Weak Agreement**:
- 50-70% of sources support
- **Action**: Moderate confidence, review carefully

**Disagreement**:
- Sources contradict each other
- **Action**: Low confidence, investigate the conflict

**No Consensus**:
- No clear pattern
- **Action**: Very low confidence, verify independently

### Using the Matrix

1. **Check for Conflicts**: If sources disagree, investigate why
2. **Check Source Diversity**: Agreement from diverse sources is stronger
3. **Look for Patterns**: Do certain source types consistently agree/disagree?
4. **Verify Independently**: When in doubt, verify with external sources

## Best Practices

### For Important Decisions

1. **Check Trust Scores**: Review average trust and calibration error
2. **Verify Source Diversity**: Ensure consensus comes from diverse sources
3. **Review Verification Counts**: More verifications = higher confidence
4. **Check for Conflicts**: Review source agreement matrix for disagreements
5. **Consider Belief Alignment**: Be aware of confirmation bias

### For Quick Lookups

1. **Use Summary Tier**: Start with `response_tiers["summary"]`
2. **Check Trust Quickly**: High trust + high verification = likely reliable
3. **Expand if Needed**: Use `detailed` or `evidence` tiers for more info

### For Research

1. **Review Full Evidence**: Use `response_tiers["evidence"]` tier
2. **Check Source Matrix**: Identify consensus and conflicts
3. **Review Cliques**: See which sources agree
4. **Verify Independently**: Always verify critical claims

### Red Flags

Watch out for:
- **High trust but low verification**: Single source, verify independently
- **High trust but low source diversity**: Echo chamber, verify with different types
- **High calibration error**: Trust scores may be unreliable
- **Conflicts in source matrix**: Sources disagree, investigate
- **Strong contradiction with your beliefs**: Don't dismiss, investigate

## Examples

### Example 1: High Trust, High Verification

```
Trust: 0.85
Verification: 4 sources
Source Diversity: 3 different types
Calibration Error: 0.08
```

**Interpretation**: Very reliable. Multiple independent sources from diverse types agree. Trust scores are well-calibrated.

### Example 2: Medium Trust, Low Verification

```
Trust: 0.65
Verification: 1 source
Source Diversity: 1 type
Calibration Error: 0.15
```

**Interpretation**: Moderate reliability. Single source, verify if important. Trust scores are reasonably calibrated.

### Example 3: Low Trust, Conflict

```
Trust: 0.45
Verification: 2 sources
Source Agreement: Disagreement
Calibration Error: 0.25
```

**Interpretation**: Low reliability. Sources disagree, and trust scores may be unreliable. Verify independently.

## See Also

- `KNOWLEDGE_DISPLAY_GUIDE.md` - Comprehensive display features guide
- `AGENTS.md` - Agent usage patterns
- `ARCHITECTURE.md` - Theoretical foundations

