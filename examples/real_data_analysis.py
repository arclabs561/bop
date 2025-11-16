"""
Real BOP Data Analysis - Using Actual Evaluation Results
=========================================================

This script analyzes REAL BOP evaluation results from actual research sessions.
No simulations—just real data from real queries with real trust metrics.
"""

import json
import math
from pathlib import Path
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

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


def load_real_data() -> Dict[str, Any]:
    """Load real evaluation results."""
    eval_file = Path(__file__).parent.parent / "eval_results.json"
    
    if not eval_file.exists():
        return {}
    
    with open(eval_file) as f:
        return json.load(f)


def compute_correlation(x: List[float], y: List[float]) -> float:
    """Compute Pearson correlation coefficient."""
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    
    mean_x = sum(x) / len(x)
    mean_y = sum(y) / len(y)
    
    covariance = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    std_x = math.sqrt(sum((xi - mean_x)**2 for xi in x))
    std_y = math.sqrt(sum((yi - mean_y)**2 for yi in y))
    
    if (std_x * std_y) == 0:
        return 0.0
    
    return covariance / (std_x * std_y)


def analyze_real_trust_distribution(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Analyze real trust data from actual BOP responses."""
    results_with_research = [
        (query, result) for query, result in data.items()
        if result.get("research") and result["research"].get("topology")
    ]
    
    if not results_with_research:
        return None
    
    # Aggregate across all queries
    all_sources = {}
    all_verifications = {}
    
    for query, result in results_with_research:
        topology = result["research"]["topology"]
        source_cred = topology.get("source_credibility", {})
        verification_info = topology.get("verification_info", {})
        
        for source, cred in source_cred.items():
            if source not in all_sources:
                all_sources[source] = []
            all_sources[source].append(cred)
        
        for source, info in verification_info.items():
            if source not in all_verifications:
                all_verifications[source] = []
            all_verifications[source].append(info.get("verification_count", 0))
    
    # Average credibility per source
    avg_credibility = {
        source: sum(creds) / len(creds)
        for source, creds in all_sources.items()
    }
    
    # Average verifications per source
    avg_verifications = {
        source: sum(verifs) / len(verifs) if verifs else 0
        for source, verifs in all_verifications.items()
    }
    
    # Compute correlation
    sources = list(avg_credibility.keys())
    credibilities = [avg_credibility[s] for s in sources]
    verifications = [avg_verifications.get(s, 0) for s in sources]
    
    if len(credibilities) >= 2:
        r = compute_correlation(credibilities, verifications)
    else:
        r = 0.0
    
    return {
        "source_credibility": avg_credibility,
        "verification_info": avg_verifications,
        "correlation": r,
        "num_sources": len(sources),
        "num_queries": len(results_with_research),
    }


def analyze_real_cliques(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Analyze real clique data across all queries."""
    all_cliques = []
    
    for query, result in data.items():
        if result.get("research") and result["research"].get("topology"):
            topology = result["research"]["topology"]
            cliques = topology.get("cliques", [])
            for clique in cliques:
                clique["query"] = query
                all_cliques.append(clique)
    
    return all_cliques


def analyze_real_source_matrix(data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze real source agreement matrices."""
    all_matrices = {}
    
    for query, result in data.items():
        if result.get("research"):
            source_matrix = result["research"].get("source_matrix", {})
            if source_matrix:
                all_matrices[query] = source_matrix
    
    return all_matrices


def analyze_real_calibration(data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze real calibration data."""
    calibration_errors = []
    trust_summaries = []
    
    for query, result in data.items():
        if result.get("research") and result["research"].get("topology"):
            topology = result["research"]["topology"]
            trust_summary = topology.get("trust_summary", {})
            
            if trust_summary:
                trust_summaries.append(trust_summary)
                cal_error = trust_summary.get("calibration_error")
                if cal_error is not None:
                    calibration_errors.append(cal_error)
    
    return {
        "calibration_errors": calibration_errors,
        "avg_calibration_error": sum(calibration_errors) / len(calibration_errors) if calibration_errors else None,
        "trust_summaries": trust_summaries,
    }


def main():
    """Run real analysis on real BOP data."""
    
    console.print(Panel.fit("[bold blue]Real BOP Data Analysis[/bold blue]", border_style="blue"))
    console.print("\nAnalyzing REAL evaluation results from actual BOP research sessions.\n")
    
    # Load real data
    data = load_real_data()
    
    if not data:
        console.print("[red]❌ No evaluation results found (eval_results.json)[/red]")
        console.print("\n[dim]To generate real data, run evaluation scripts or use BOP with research enabled.[/dim]")
        return
    
    console.print(f"[green]✅ Loaded {len(data)} real evaluation results[/green]")
    
    # Show sample queries
    sample_queries = list(data.keys())[:5]
    console.print(f"\n[bold]Sample Queries:[/bold]")
    for i, query in enumerate(sample_queries, 1):
        console.print(f"  {i}. {query[:60]}...")
    
    # ============================================================================
    # Cell 1: Real Trust Distribution Analysis
    # ============================================================================
    print_cell(
        "Real Trust Distribution Analysis",
        """
## Methodology

We analyze **actual** trust metrics from real BOP research sessions. This
includes:
- Real source credibility scores computed from actual research
- Real verification counts from actual cross-source validation
- Real correlation computed from actual data

## Data Source

We use evaluation results from `eval_results.json`, which contains responses
from actual BOP queries with research enabled. Each response includes:
- Topology metrics (trust summary, source credibility, verification info)
- Source agreement matrices
- Clique structures
- Calibration errors

**This is NOT simulated data—these are real metrics from real research.**
        """,
        "markdown"
    )
    
    trust_data = analyze_real_trust_distribution(data)
    
    if trust_data:
        print_cell(
            "Computing Real Correlation",
            """
# Pearson correlation on REAL data
# r = Σ((x_i - x̄)(y_i - ȳ)) / √(Σ(x_i - x̄)² · Σ(y_i - ȳ)²)

# Using actual source credibility and verification counts from real research
sources = trust_data["source_credibility"]
credibilities = [s["credibility"] for s in sources.values()]
verifications = [s["verifications"] for s in sources.values()]

r = compute_correlation(credibilities, verifications)
# This is the REAL correlation from REAL data
            """,
            "code"
        )
        
        table = Table(show_header=True, header_style="bold")
        table.add_column("Source", style="cyan")
        table.add_column("Credibility", style="green")
        table.add_column("Verifications", style="yellow")
        table.add_column("Data Points", style="dim")
        
        sorted_sources = sorted(
            trust_data["source_credibility"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        for source, cred in sorted_sources:
            verif = trust_data["verification_info"].get(source, 0)
            bar_length = int(cred * 20)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            color = "green" if cred > 0.7 else "yellow" if cred > 0.5 else "red"
            
            table.add_row(
                source[:40],
                f"[{color}]{bar}[/{color}] {cred:.3f}",
                f"{verif:.1f}",
                f"{trust_data['num_queries']} queries"
            )
        
        print_cell("", table, "output")
        
        print_cell(
            "Real Statistical Analysis",
            f"""
## Real Correlation from Real Data

**Pearson Correlation Coefficient:** r = {trust_data['correlation']:.3f}

**Data:**
- Number of sources: {trust_data['num_sources']}
- Number of queries analyzed: {trust_data['num_queries']}
- This correlation is computed from **actual** credibility and verification
  scores from **real** research sessions

**Interpretation:**
- r > 0.7: Strong positive correlation
- r = {trust_data['correlation']:.3f}: {'Strong' if trust_data['correlation'] > 0.7 else 'Moderate' if trust_data['correlation'] > 0.5 else 'Weak'} correlation

**Statistical Significance:**
With n = {trust_data['num_sources']} sources:
```
t = r × √((n-2) / (1-r²))
t = {trust_data['correlation']:.3f} × √({trust_data['num_sources']-2} / (1-{trust_data['correlation']**2:.3f}))
t ≈ {trust_data['correlation'] * math.sqrt((trust_data['num_sources']-2) / (1-trust_data['correlation']**2)):.2f}
```

For n-2 = {trust_data['num_sources']-2} degrees of freedom, t > 2.35 indicates
significance at p < 0.05.

**Key Finding:** This correlation is computed from **real** data, not simulations.
It tells us how credibility and verification actually relate in practice.
            """,
            "markdown"
        )
    else:
        print_cell(
            "No Trust Data Available",
            """
**Note:** No trust distribution data found in evaluation results. This could mean:
1. Research was not conducted (no API keys or MCP tools unavailable)
2. Research was conducted but didn't produce topology metrics
3. Evaluation results don't include research data

**To get real trust data:**
- Ensure API keys are set (OPENAI_API_KEY or ANTHROPIC_API_KEY)
- Run BOP with `--research` flag
- Or run evaluation scripts that include research
            """,
            "markdown"
        )
    
    # ============================================================================
    # Cell 2: Real Clique Analysis
    # ============================================================================
    cliques = analyze_real_cliques(data)
    
    if cliques:
        print_cell(
            "Real Clique Analysis",
            """
## Real Clique Data from Real Research

These cliques are computed from **actual** source agreements in **real** research
sessions. Each clique represents sources that actually agreed on claims in
real queries.
            """,
            "markdown"
        )
        
        # Group by query
        cliques_by_query = {}
        for clique in cliques:
            query = clique.get("query", "unknown")
            if query not in cliques_by_query:
                cliques_by_query[query] = []
            cliques_by_query[query].append(clique)
        
        for query, query_cliques in list(cliques_by_query.items())[:3]:
            print_cell(
                f"Cliques from: {query[:50]}...",
                f"""
# Real cliques from this query
# These are actual source agreement clusters from real research
                """,
                "code"
            )
            
            table = Table(show_header=True, header_style="bold")
            table.add_column("Clique", style="cyan")
            table.add_column("Trust", style="green")
            table.add_column("Coherence", style="blue")
            table.add_column("Size", style="yellow")
            table.add_column("Sources", style="dim")
            
            for i, clique in enumerate(query_cliques[:5], 1):
                trust = clique.get("trust", 0)
                coherence = clique.get("coherence", 0)
                size = clique.get("size", 0)
                sources = clique.get("node_sources", [])
                
                trust_emoji = "🟢" if trust > 0.7 else "🟡" if trust > 0.5 else "🔴"
                coherence_emoji = "🟢" if coherence > 0.8 else "🟡" if coherence > 0.6 else "🔴"
                
                sources_str = ", ".join([s[:15] for s in sources[:2]])
                if len(sources) > 2:
                    sources_str += f" (+{len(sources)-2})"
                
                table.add_row(
                    f"Cluster {i}",
                    f"{trust_emoji} {trust:.2f}",
                    f"{coherence_emoji} {coherence:.2f}",
                    str(size),
                    sources_str
                )
            
            print_cell("", table, "output")
    else:
        print_cell(
            "No Clique Data",
            "No clique data found in evaluation results.",
            "markdown"
        )
    
    # ============================================================================
    # Cell 3: Real Source Agreement Matrix
    # ============================================================================
    source_matrices = analyze_real_source_matrix(data)
    
    if source_matrices:
        print_cell(
            "Real Source Agreement Analysis",
            """
## Real Agreement Matrices from Real Research

These agreement matrices are computed from **actual** claims and **actual** source
positions in **real** research sessions. They show real consensus and
real disagreements.
            """,
            "markdown"
        )
        
        total_claims = sum(len(matrix) for matrix in source_matrices.values())
        total_strong = sum(
            sum(1 for c in matrix.values() if c.get("consensus") == "strong_agreement")
            for matrix in source_matrices.values()
        )
        
        print_cell(
            "Aggregate Agreement Statistics",
            f"""
# Real agreement data across all queries
total_claims = {total_claims}
strong_agreements = {total_strong}
strong_agreement_rate = {total_strong/total_claims:.1%} if total_claims > 0 else 0
            """,
            "code"
        )
        
        console.print(f"\n[bold green]Real Agreement Statistics:[/bold green]")
        console.print(f"  Total claims analyzed: {total_claims}")
        console.print(f"  Strong agreements: {total_strong} ({total_strong/total_claims:.1%})" if total_claims > 0 else "  No claims")
        console.print(f"  Queries with agreement data: {len(source_matrices)}")
    
    # ============================================================================
    # Cell 4: Real Calibration Analysis
    # ============================================================================
    calibration = analyze_real_calibration(data)
    
    if calibration and calibration.get("avg_calibration_error") is not None:
        print_cell(
            "Real Calibration Error Analysis",
            """
## Real Calibration from Real Trust Metrics

These calibration errors are computed from **actual** trust summaries in **real**
research sessions. They measure how well our confidence scores match reality.
            """,
            "markdown"
        )
        
        avg_ece = calibration["avg_calibration_error"]
        num_errors = len(calibration["calibration_errors"])
        
        print_cell(
            "Calibration Error Statistics",
            f"""
# Real calibration errors from real research
calibration_errors = {calibration['calibration_errors']}
avg_ece = {avg_ece:.3f}
num_measurements = {num_errors}
            """,
            "code"
        )
        
        console.print(f"\n[bold green]Real Calibration Analysis:[/bold green]")
        console.print(f"  Average ECE: {avg_ece:.3f}")
        console.print(f"  Measurements: {num_errors}")
        console.print(f"  Interpretation: {'Excellent' if avg_ece < 0.05 else 'Good' if avg_ece < 0.15 else 'Moderate' if avg_ece < 0.25 else 'Poor'}")
    
    # Summary
    console.print("\n" + "="*80)
    console.print("[bold cyan]📊 Real Data Analysis Summary[/bold cyan]")
    console.print("="*80)
    
    console.print(f"\n[bold]Data Analyzed:[/bold]")
    console.print(f"  Queries: {len(data)}")
    console.print(f"  Queries with research: {sum(1 for r in data.values() if r.get('research_conducted'))}")
    
    if trust_data:
        console.print(f"\n[bold]Trust Distribution:[/bold]")
        console.print(f"  Sources: {trust_data['num_sources']}")
        console.print(f"  Correlation: {trust_data['correlation']:.3f}")
    
    if cliques:
        console.print(f"\n[bold]Cliques:[/bold]")
        console.print(f"  Total cliques: {len(cliques)}")
        console.print(f"  Queries with cliques: {len(set(c.get('query') for c in cliques))}")
    
    if source_matrices:
        console.print(f"\n[bold]Source Agreement:[/bold]")
        console.print(f"  Queries with matrices: {len(source_matrices)}")
        total_claims = sum(len(m) for m in source_matrices.values())
        console.print(f"  Total claims: {total_claims}")
    
    console.print("\n" + "="*80)
    console.print("[bold green]✅ Real Data Analysis Complete[/bold green]")
    console.print("="*80)
    console.print("\n[dim]This analysis used REAL data from REAL BOP research sessions.[/dim]")


if __name__ == "__main__":
    main()

