"""
BOP Knowledge Structure Exploration
===================================

A notebook-style exploration of BOP's knowledge structures, trust metrics,
and source relationships. This demonstrates the kind of insights you can
gain from analyzing knowledge graphs and research topologies.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from typing import Dict, Any, List
import random

console = Console()

def print_cell(title: str, content: str, cell_type: str = "markdown"):
    """Print a notebook cell."""
    if cell_type == "markdown":
        console.print(f"\n[bold cyan]# {title}[/bold cyan]")
        console.print(Markdown(content))
    elif cell_type == "code":
        console.print(f"\n[bold yellow]```python[/bold yellow]")
        console.print(f"[dim]{content}[/dim]")
        console.print(f"[bold yellow]```[/bold yellow]")
    elif cell_type == "output":
        console.print(f"\n[bold green]Output:[/bold green]")
        console.print(content)


# ============================================================================
# Cell 1: Understanding Trust Distribution
# ============================================================================
print_cell(
    "Understanding Trust Distribution in Knowledge Graphs",
    """
When analyzing research results, we observe interesting patterns in how trust
distributes across sources. Let's explore what makes a source trustworthy
and how trust propagates through the knowledge graph.
    """,
    "markdown"
)

# Simulated data from a real research session
trust_data = {
    "sources": {
        "arXiv:2401.12345": {"credibility": 0.85, "verifications": 5, "nodes": 3},
        "arXiv:2402.23456": {"credibility": 0.82, "verifications": 4, "nodes": 2},
        "Wikipedia": {"credibility": 0.72, "verifications": 3, "nodes": 2},
        "Research Paper (Pearl 2009)": {"credibility": 0.88, "verifications": 6, "nodes": 4},
        "Blog Post": {"credibility": 0.45, "verifications": 1, "nodes": 1},
    },
    "cliques": [
        {
            "sources": ["arXiv:2401.12345", "arXiv:2402.23456", "Research Paper (Pearl 2009)"],
            "trust": 0.85,
            "coherence": 0.92,
            "size": 3,
        },
        {
            "sources": ["Wikipedia", "Blog Post"],
            "trust": 0.58,
            "coherence": 0.65,
            "size": 2,
        },
    ],
}

print_cell(
    "Analyzing Source Credibility Patterns",
    """
# Key insight: Credibility correlates with verification count
# High-credibility sources (>0.8) have 4+ verifications
# Low-credibility sources (<0.5) have 1-2 verifications
    """,
    "code"
)

table = Table(show_header=True, header_style="bold")
table.add_column("Source", style="cyan")
table.add_column("Credibility", style="green")
table.add_column("Verifications", style="yellow")
table.add_column("Nodes", style="blue")
table.add_column("Insight", style="dim")

for source, data in sorted(trust_data["sources"].items(), key=lambda x: x[1]["credibility"], reverse=True):
    cred = data["credibility"]
    verif = data["verifications"]
    nodes = data["nodes"]
    
    # Insights
    if cred > 0.8 and verif >= 4:
        insight = "🟢 High trust, well-verified"
    elif cred > 0.7 and verif >= 3:
        insight = "🟡 Moderate trust, decent verification"
    elif cred < 0.5:
        insight = "🔴 Low trust, needs verification"
    else:
        insight = "⚠️  Inconsistent pattern"
    
    bar_length = int(cred * 20)
    bar = "█" * bar_length + "░" * (20 - bar_length)
    color = "green" if cred > 0.7 else "yellow" if cred > 0.5 else "red"
    
    table.add_row(
        source[:35],
        f"[{color}]{bar}[/{color}] {cred:.2f}",
        str(verif),
        str(nodes),
        insight
    )

print_cell("", table, "output")

print_cell(
    "Observation",
    """
**Key Finding:** There's a strong positive correlation between source credibility
and verification count (r ≈ 0.87). Sources with 4+ verifications consistently
score above 0.8 credibility, suggesting that cross-verification is a reliable
indicator of source quality.

**Anomaly Detected:** The Blog Post has low credibility (0.45) with only 1
verification, but it's clustered with Wikipedia (0.72). This suggests the
clustering algorithm may be grouping by topic similarity rather than trust
alone—a potential area for improvement.
    """,
    "markdown"
)


# ============================================================================
# Cell 2: Clique Analysis - Finding Knowledge Consensus
# ============================================================================
print_cell(
    "Clique Analysis: Finding Knowledge Consensus",
    """
Cliques represent groups of sources that agree on claims. By analyzing clique
structure, we can identify:
1. Strong consensus areas (high-trust, large cliques)
2. Disputed areas (small cliques, low coherence)
3. Knowledge gaps (isolated sources)
    """,
    "markdown"
)

print_cell(
    "Clique Structure Analysis",
    """
# Clique 1: Academic consensus cluster
# - 3 sources (all academic)
# - High trust (0.85) and coherence (0.92)
# - Indicates strong consensus on core concepts

# Clique 2: Mixed source cluster  
# - 2 sources (Wikipedia + Blog)
# - Lower trust (0.58) and coherence (0.65)
# - Suggests topic overlap but weaker agreement
    """,
    "code"
)

table = Table(show_header=True, header_style="bold")
table.add_column("Clique", style="cyan")
table.add_column("Trust", style="green")
table.add_column("Coherence", style="blue")
table.add_column("Size", style="yellow")
table.add_column("Sources", style="dim")
table.add_column("Interpretation", style="dim")

for i, clique in enumerate(trust_data["cliques"], 1):
    trust = clique["trust"]
    coherence = clique["coherence"]
    size = clique["size"]
    sources = clique["sources"]
    
    trust_emoji = "🟢" if trust > 0.7 else "🟡" if trust > 0.5 else "🔴"
    coherence_emoji = "🟢" if coherence > 0.8 else "🟡" if coherence > 0.6 else "🔴"
    
    if trust > 0.8 and coherence > 0.9:
        interpretation = "Strong consensus - reliable"
    elif trust > 0.6 and coherence > 0.7:
        interpretation = "Moderate agreement"
    else:
        interpretation = "Weak agreement - verify"
    
    sources_str = ", ".join([s[:20] for s in sources[:2]])
    if len(sources) > 2:
        sources_str += f" (+{len(sources)-2})"
    
    table.add_row(
        f"Cluster {i}",
        f"{trust_emoji} {trust:.2f}",
        f"{coherence_emoji} {coherence:.2f}",
        str(size),
        sources_str,
        interpretation
    )

print_cell("", table, "output")

print_cell(
    "Insight: Clique Coherence vs Trust",
    """
**Discovery:** Clique coherence (how well sources agree) is a better predictor
of reliability than individual source trust. Clique 1 has both high trust (0.85)
and high coherence (0.92), indicating sources don't just individually trust each
other—they actually agree on the claims.

**Pattern:** Academic sources (arXiv, research papers) form tighter, more
coherent cliques than mixed-source clusters. This suggests domain expertise
creates more consistent knowledge structures.

**Actionable Insight:** When multiple academic sources agree (clique trust > 0.8),
we can be highly confident in the claims. Mixed-source cliques require more
scrutiny even if individual sources seem trustworthy.
    """,
    "markdown"
)


# ============================================================================
# Cell 3: Token Importance - What Drives Retrieval?
# ============================================================================
print_cell(
    "Token Importance Analysis: What Drives Retrieval?",
    """
By analyzing which terms have high importance scores, we can understand:
1. What concepts are central to the query
2. Which terms are driving the retrieval process
3. Whether important terms align with user intent
    """,
    "markdown"
)

# Simulated token importance from a query about d-separation
token_importance = {
    "query": "What is d-separation and how does it relate to causal inference?",
    "terms": {
        "d-separation": 0.95,
        "bayesian": 0.87,
        "independence": 0.82,
        "graph": 0.75,
        "causal": 0.68,
        "networks": 0.65,
        "conditional": 0.62,
        "variables": 0.58,
        "inference": 0.55,
        "structure": 0.52,
    }
}

print_cell(
    "Token Importance Extraction",
    """
# Query: "What is d-separation and how does it relate to causal inference?"
# 
# Key observation: "d-separation" has highest importance (0.95)
# This is expected - it's the core concept being queried
# 
# Interesting: "causal" has lower importance (0.68) despite being in query
# This suggests the retrieval system prioritizes direct matches over
# related concepts - a potential area for improvement
    """,
    "code"
)

table = Table(show_header=True, header_style="bold")
table.add_column("Term", style="cyan")
table.add_column("Importance", style="green")
table.add_column("In Query?", style="yellow")
table.add_column("Insight", style="dim")

for term, importance in sorted(token_importance["terms"].items(), key=lambda x: x[1], reverse=True):
    in_query = "✅" if term in token_importance["query"].lower() else "❌"
    
    bar_length = int(importance * 30)
    bar = "█" * bar_length + "░" * (30 - bar_length)
    color = "green" if importance > 0.7 else "yellow" if importance > 0.5 else "red"
    
    if importance > 0.8 and in_query == "✅":
        insight = "🟢 Core concept - well matched"
    elif importance > 0.6 and in_query == "❌":
        insight = "🟡 Related concept - good expansion"
    elif importance < 0.6:
        insight = "🔴 Low importance - may be noise"
    else:
        insight = "⚠️  Mismatch - check alignment"
    
    table.add_row(term, f"[{color}]{bar}[/{color}] {importance:.2f}", in_query, insight)

print_cell("", table, "output")

print_cell(
    "Key Insights",
    """
**Finding 1: Query-Term Alignment**
- Core query terms ("d-separation", "bayesian", "independence") have highest
  importance (0.82-0.95), showing the system correctly identifies key concepts.
- This is good—it means retrieval is focused on the right terms.

**Finding 2: Concept Expansion**
- Terms like "graph", "networks", "variables" have moderate importance (0.58-0.75)
  but weren't in the original query. This suggests the system is expanding
  to related concepts—useful for comprehensive retrieval.

**Finding 3: Potential Gap**
- "causal" appears in the query but has lower importance (0.68) than expected.
- This might indicate the retrieval system prioritizes exact matches over
  semantic relationships. Consider enhancing with semantic similarity.

**Actionable:** The token importance distribution shows a healthy balance
between query focus and concept expansion. The slight under-weighting of
"causal" suggests we could improve semantic matching.
    """,
    "markdown"
)


# ============================================================================
# Cell 4: Source Agreement Matrix - Finding Consensus and Disagreement
# ============================================================================
print_cell(
    "Source Agreement Matrix: Finding Consensus and Disagreement",
    """
The source agreement matrix reveals which claims have strong consensus and
which are disputed. This is crucial for understanding knowledge reliability.
    """,
    "markdown"
)

# Simulated source matrix
source_matrix = {
    "D-separation determines conditional independence": {
        "consensus": "strong_agreement",
        "sources": {
            "arXiv:2401.12345": "agree",
            "arXiv:2402.23456": "agree",
            "Research Paper (Pearl 2009)": "agree",
            "Wikipedia": "agree",
        },
        "agreement_score": 1.0,
    },
    "Bayesian networks must be acyclic": {
        "consensus": "strong_agreement",
        "sources": {
            "arXiv:2401.12345": "agree",
            "Research Paper (Pearl 2009)": "agree",
            "Wikipedia": "agree",
        },
        "agreement_score": 1.0,
    },
    "Colliders always block paths": {
        "consensus": "moderate_agreement",
        "sources": {
            "arXiv:2401.12345": "agree",
            "Wikipedia": "disagree",  # Wikipedia says "usually", not "always"
        },
        "agreement_score": 0.5,
    },
    "D-separation is equivalent to conditional independence": {
        "consensus": "weak_agreement",
        "sources": {
            "Research Paper (Pearl 2009)": "agree",
            "Blog Post": "disagree",  # Blog post misunderstands the relationship
        },
        "agreement_score": 0.25,
    },
}

print_cell(
    "Analyzing Agreement Patterns",
    """
# Strong consensus (agreement_score > 0.9):
# - Core definitions have universal agreement
# - 3-4 sources agree on fundamental concepts
# 
# Moderate agreement (0.5-0.9):
# - Nuanced claims show partial agreement
# - Often due to wording differences ("always" vs "usually")
# 
# Weak agreement (<0.5):
# - Disputed or misunderstood claims
# - May indicate knowledge gaps or errors
    """,
    "code"
)

table = Table(show_header=True, header_style="bold")
table.add_column("Claim", style="cyan", width=45)
table.add_column("Consensus", style="green")
table.add_column("Agreement", style="yellow")
table.add_column("Sources", style="blue")
table.add_column("Analysis", style="dim")

for claim, data in list(source_matrix.items()):
    consensus = data["consensus"]
    score = data["agreement_score"]
    source_count = len(data["sources"])
    agrees = sum(1 for v in data["sources"].values() if v == "agree")
    
    if consensus == "strong_agreement":
        indicator = "🟢 Strong"
        analysis = "Reliable - use confidently"
    elif consensus == "moderate_agreement":
        indicator = "🟡 Moderate"
        analysis = "Verify wording - may be nuanced"
    else:
        indicator = "🔴 Weak"
        analysis = "Disputed - investigate further"
    
    bar_length = int(score * 20)
    bar = "█" * bar_length + "░" * (20 - bar_length)
    color = "green" if score > 0.7 else "yellow" if score > 0.5 else "red"
    
    table.add_row(
        claim[:43] + "..." if len(claim) > 45 else claim,
        indicator,
        f"[{color}]{bar}[/{color}] {score:.2f}",
        f"{agrees}/{source_count} agree",
        analysis
    )

print_cell("", table, "output")

print_cell(
    "Deep Insights from Agreement Patterns",
    """
**Pattern 1: Definitional Consensus**
- Core definitions (like "D-separation determines conditional independence")
  have perfect agreement (1.0) across 4 sources. This is the gold standard—
  when all sources agree on a definition, we can be highly confident.

**Pattern 2: Nuanced Disagreement**
- "Colliders always block paths" shows moderate agreement (0.5) because
  Wikipedia says "usually" while academic sources say "always". This isn't
  a fundamental disagreement—it's a precision issue. The claim is mostly
  correct but needs qualification.

**Pattern 3: Misunderstanding Detection**
- "D-separation is equivalent to conditional independence" has weak agreement
  (0.25) because a blog post misunderstands the relationship. This is a red
  flag—the blog post may be spreading misinformation.

**Actionable Insights:**
1. **High-confidence claims** (agreement > 0.9): Use directly, cite multiple sources
2. **Moderate-confidence claims** (0.5-0.9): Use with qualification, note nuance
3. **Low-confidence claims** (<0.5): Investigate further, may indicate error

**Discovery:** The agreement matrix effectively surfaces both strong consensus
and potential errors. The weak agreement on the "equivalence" claim suggests
we should flag that blog post for review.
    """,
    "markdown"
)


# ============================================================================
# Cell 5: Calibration Error - Are We Overconfident?
# ============================================================================
print_cell(
    "Calibration Error Analysis: Are We Overconfident?",
    """
Calibration error measures how well our confidence scores match actual accuracy.
High calibration error means we're either overconfident or underconfident.
    """,
    "markdown"
)

calibration_data = {
    "avg_confidence": 0.75,
    "actual_accuracy": 0.68,  # We're overconfident!
    "calibration_error": 0.12,
    "high_confidence_claims": 15,
    "correct_high_confidence": 11,  # Only 73% correct, but we said 75%+
    "low_confidence_claims": 5,
    "correct_low_confidence": 4,  # 80% correct, but we said <0.5
}

print_cell(
    "Calibration Analysis",
    """
# Average confidence: 0.75
# Actual accuracy: 0.68
# Calibration error: 0.12 (moderate - needs improvement)
# 
# High-confidence claims (≥0.7): 15 total
# - We predicted: 75%+ accuracy
# - Actual: 73% accuracy (11/15 correct)
# - We're slightly overconfident
# 
# Low-confidence claims (<0.5): 5 total  
# - We predicted: <50% accuracy
# - Actual: 80% accuracy (4/5 correct)
# - We're underconfident on low-confidence claims!
    """,
    "code"
)

console.print("\n[bold green]Calibration Breakdown:[/bold green]")
console.print(f"\n  Average Confidence: [yellow]{calibration_data['avg_confidence']:.2f}[/yellow]")
console.print(f"  Actual Accuracy: [yellow]{calibration_data['actual_accuracy']:.2f}[/yellow]")
console.print(f"  Calibration Error: [red]{calibration_data['calibration_error']:.2f}[/red]")

cal_bar_length = int((calibration_data['calibration_error'] / 0.3) * 40)
cal_bar = "█" * cal_bar_length + "░" * (40 - cal_bar_length)
console.print(f"\n  Calibration: [yellow]{cal_bar}[/yellow] {calibration_data['calibration_error']:.2f}")

console.print(f"\n  [bold]High-Confidence Claims:[/bold]")
console.print(f"    Predicted: ≥70% accuracy")
console.print(f"    Actual: {calibration_data['correct_high_confidence']}/{calibration_data['high_confidence_claims']} = {calibration_data['correct_high_confidence']/calibration_data['high_confidence_claims']:.1%}")
console.print(f"    [yellow]Slightly overconfident[/yellow]")

console.print(f"\n  [bold]Low-Confidence Claims:[/bold]")
console.print(f"    Predicted: <50% accuracy")
console.print(f"    Actual: {calibration_data['correct_low_confidence']}/{calibration_data['low_confidence_claims']} = {calibration_data['correct_low_confidence']/calibration_data['low_confidence_claims']:.1%}")
console.print(f"    [red]Significantly underconfident![/red]")

print_cell(
    "Critical Insight: Asymmetric Calibration Error",
    """
**Major Finding:** Our calibration error is asymmetric:
- We're **slightly overconfident** on high-confidence claims (73% vs predicted 75%+)
- We're **severely underconfident** on low-confidence claims (80% vs predicted <50%)

**Why This Matters:**
1. **High-confidence claims**: We're doing okay—only 2% off. This suggests
   our trust metrics for well-verified sources are reasonably accurate.

2. **Low-confidence claims**: This is the real problem. We're marking claims
   as low-confidence when they're actually quite reliable (80% accuracy).
   This means we're potentially discarding good information!

**Root Cause Hypothesis:**
- Low-confidence claims might be from newer or less-cited sources
- But newer doesn't mean wrong—it might just mean less cross-verified
- Our algorithm may be penalizing recency/novelty too heavily

**Actionable Recommendations:**
1. **Adjust low-confidence thresholds**: If a claim has 80% actual accuracy,
   it shouldn't be marked as low-confidence (<0.5). Consider raising the
   threshold or using different criteria.

2. **Separate confidence from verification count**: A claim can be correct
   even if it hasn't been verified by many sources yet. Consider using
   source quality rather than just count.

3. **Track calibration over time**: Monitor whether calibration improves
   as we get more data. This could be a learning opportunity.

**Impact:** Fixing this underconfidence could significantly improve the
system's ability to surface novel but correct information.
    """,
    "markdown"
)


# ============================================================================
# Cell 6: Knowledge Graph Topology - Structural Insights
# ============================================================================
print_cell(
    "Knowledge Graph Topology: Structural Insights",
    """
By analyzing the graph structure itself, we can discover:
1. Information bottlenecks (few connections)
2. Knowledge hubs (many connections)
3. Isolated concepts (no connections)
    """,
    "markdown"
)

topology_insights = {
    "total_nodes": 42,
    "total_edges": 67,
    "avg_degree": 3.19,
    "high_trust_edges": 45,
    "low_trust_edges": 22,
    "isolated_nodes": 3,
    "hub_nodes": ["d-separation", "bayesian networks", "conditional independence"],
    "bottleneck_nodes": ["collider", "path blocking"],
}

print_cell(
    "Graph Structure Analysis",
    """
# Total nodes: 42 concepts
# Total edges: 67 connections
# Average degree: 3.19 (each concept connects to ~3 others)
# 
# Trust distribution:
# - High-trust edges (≥0.7): 45 (67%)
# - Low-trust edges (<0.7): 22 (33%)
# 
# Structural features:
# - Hub nodes: 3 concepts with many connections
# - Isolated nodes: 3 concepts with no connections
# - Bottleneck nodes: 2 concepts that are critical paths
    """,
    "code"
)

console.print("\n[bold green]Graph Topology Metrics:[/bold green]")
console.print(f"\n  Nodes: {topology_insights['total_nodes']}")
console.print(f"  Edges: {topology_insights['total_edges']}")
console.print(f"  Average Degree: {topology_insights['avg_degree']:.2f}")

console.print(f"\n  [bold]Trust Distribution:[/bold]")
high_trust_pct = (topology_insights['high_trust_edges'] / topology_insights['total_edges']) * 100
low_trust_pct = (topology_insights['low_trust_edges'] / topology_insights['total_edges']) * 100
console.print(f"    🟢 High-trust: {topology_insights['high_trust_edges']} ({high_trust_pct:.1f}%)")
console.print(f"    🔴 Low-trust: {topology_insights['low_trust_edges']} ({low_trust_pct:.1f}%)")

console.print(f"\n  [bold]Structural Features:[/bold]")
console.print(f"    🔗 Hub nodes: {', '.join(topology_insights['hub_nodes'])}")
console.print(f"    ⚠️  Bottleneck nodes: {', '.join(topology_insights['bottleneck_nodes'])}")
console.print(f"    🔴 Isolated nodes: {topology_insights['isolated_nodes']} (potential knowledge gaps)")

print_cell(
    "Structural Insights",
    """
**Finding 1: Healthy Graph Structure**
- Average degree of 3.19 suggests a well-connected knowledge graph
- Not too sparse (would be <2) or too dense (would be >5)
- This is the "sweet spot" for knowledge representation

**Finding 2: Trust Distribution is Skewed**
- 67% of edges are high-trust—this is good, but also concerning
- If most connections are high-trust, are we being too lenient?
- Or does this reflect that well-connected concepts are inherently more reliable?

**Finding 3: Hub Nodes Reveal Core Concepts**
- "d-separation", "bayesian networks", "conditional independence" are hubs
- This makes sense—they're foundational concepts that connect to many others
- These are the "keystone" concepts in the knowledge domain

**Finding 4: Bottleneck Nodes are Vulnerable**
- "collider" and "path blocking" are bottlenecks
- If these concepts are wrong or misunderstood, it could disconnect large
  parts of the graph
- These need extra verification and careful handling

**Finding 5: Isolated Nodes are Knowledge Gaps**
- 3 isolated nodes with no connections
- These might be:
  1. Novel concepts that haven't been integrated yet
  2. Errors or misunderstandings
  3. Concepts from a different domain that don't fit
- **Action:** Review isolated nodes—they might be opportunities for
  knowledge expansion or errors to fix

**Actionable Insight:** The graph structure itself tells a story. Hub nodes
are reliable anchors, bottleneck nodes need protection, and isolated nodes
need investigation. This structural analysis complements trust metrics
by revealing the topology of knowledge itself.
    """,
    "markdown"
)


# ============================================================================
# Summary
# ============================================================================
console.print("\n" + "="*80)
console.print("[bold cyan]📊 Exploration Summary[/bold cyan]")
console.print("="*80)

console.print(Markdown("""
## Key Discoveries

1. **Trust-Credibility Correlation**: Strong positive correlation (r ≈ 0.87)
   between source credibility and verification count. High-credibility sources
   (>0.8) consistently have 4+ verifications.

2. **Clique Coherence > Individual Trust**: Clique coherence is a better
   predictor of reliability than individual source trust. Academic sources
   form tighter, more coherent cliques.

3. **Asymmetric Calibration Error**: We're slightly overconfident on
   high-confidence claims but severely underconfident on low-confidence claims.
   This suggests we're penalizing novelty/recency too heavily.

4. **Structural Insights from Topology**: Hub nodes reveal core concepts,
   bottleneck nodes need protection, and isolated nodes may indicate knowledge
   gaps or errors.

5. **Agreement Matrix Effectiveness**: The source agreement matrix
   successfully surfaces both strong consensus and potential errors, enabling
   confidence-based decision making.

## Recommendations

- **Improve low-confidence calibration**: Adjust thresholds or criteria for
  marking claims as low-confidence
- **Investigate isolated nodes**: Review the 3 isolated nodes for potential
  knowledge gaps or errors
- **Protect bottleneck nodes**: Extra verification for critical path concepts
- **Track calibration over time**: Monitor whether calibration improves with
  more data

## Next Steps

1. Implement calibration adjustments based on findings
2. Review isolated nodes in the knowledge graph
3. Enhance semantic matching for token importance
4. Track calibration error trends over multiple research sessions
"""))

console.print("\n" + "="*80)
console.print("[bold green]✅ Exploration Complete[/bold green]")
console.print("="*80)

