#!/usr/bin/env python3
"""
Automated Real Data Analysis Pipeline
=====================================

This script automatically:
1. Runs real BOP queries with research enabled
2. Collects real trust metrics, source matrices, topology data
3. Performs rigorous statistical analysis
4. Outputs comprehensive analysis report

Can be run:
- As part of CI/CD pipeline
- Scheduled (cron, GitHub Actions)
- After evaluation runs
- On-demand for analysis
"""

import asyncio
import json
import math
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pran.agent import KnowledgeAgent
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

# Real queries that produce interesting research results
DEFAULT_QUERIES = [
    "What is d-separation and how does it relate to causal inference?",
    "Explain information geometry and its applications to knowledge structures.",
    "How do trust metrics work in knowledge systems?",
    "What are the latest approaches to multi-document comprehension?",
    "How does ColBERT's late interaction improve semantic search?",
]


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


async def run_real_query(agent: KnowledgeAgent, query: str) -> Optional[Dict[str, Any]]:
    """Run a real BOP query with research and return the response."""
    try:
        response = await agent.chat(
            message=query,
            use_research=True,
            use_schema="decompose_and_synthesize",
        )
        return response
    except Exception as e:
        console.print(f"[red]Error running query '{query[:50]}...': {e}[/red]")
        return None


def analyze_trust_distribution(responses: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Analyze real trust data aggregated across all responses."""
    all_sources = {}
    all_verifications = {}
    
    for response in responses:
        if not response or not response.get("research"):
            continue
        
        topology = response["research"].get("topology", {})
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
    
    if not all_sources:
        return None
    
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
        "num_queries": len(responses),
    }


def analyze_cliques(responses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Analyze real clique data across all responses."""
    all_cliques = []
    
    for i, response in enumerate(responses):
        if not response or not response.get("research"):
            continue
        
        topology = response["research"].get("topology", {})
        cliques = topology.get("cliques", [])
        for clique in cliques:
            clique["query_index"] = i
            all_cliques.append(clique)
    
    return all_cliques


def analyze_source_matrices(responses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze real source agreement matrices."""
    all_matrices = {}
    total_claims = 0
    total_strong_agreements = 0
    
    for i, response in enumerate(responses):
        if not response or not response.get("research"):
            continue
        
        source_matrix = response["research"].get("source_matrix", {})
        if source_matrix:
            all_matrices[f"query_{i}"] = source_matrix
            total_claims += len(source_matrix)
            total_strong_agreements += sum(
                1 for c in source_matrix.values()
                if c.get("consensus") == "strong_agreement"
            )
    
    return {
        "matrices": all_matrices,
        "total_claims": total_claims,
        "total_strong_agreements": total_strong_agreements,
        "strong_agreement_rate": total_strong_agreements / total_claims if total_claims > 0 else 0.0,
    }


def analyze_calibration(responses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze real calibration data."""
    calibration_errors = []
    trust_summaries = []
    
    for response in responses:
        if not response or not response.get("research"):
            continue
        
        topology = response["research"].get("topology", {})
        trust_summary = topology.get("trust_summary", {})
        
        if trust_summary:
            trust_summaries.append(trust_summary)
            cal_error = trust_summary.get("calibration_error")
            if cal_error is not None:
                calibration_errors.append(cal_error)
    
    return {
        "calibration_errors": calibration_errors,
        "avg_calibration_error": sum(calibration_errors) / len(calibration_errors) if calibration_errors else None,
        "num_measurements": len(calibration_errors),
        "trust_summaries": trust_summaries,
    }


def generate_analysis_report(
    responses: List[Dict[str, Any]],
    queries: List[str],
    output_file: Path,
) -> Dict[str, Any]:
    """Generate comprehensive analysis report."""
    
    # Analyze data
    trust_data = analyze_trust_distribution(responses)
    cliques = analyze_cliques(responses)
    source_matrices = analyze_source_matrices(responses)
    calibration = analyze_calibration(responses)
    
    # Build report
    report = {
        "timestamp": datetime.now().isoformat(),
        "queries": queries,
        "num_queries": len(queries),
        "num_responses": len(responses),
        "num_responses_with_research": sum(1 for r in responses if r and r.get("research_conducted")),
        "trust_distribution": trust_data,
        "cliques": {
            "total_cliques": len(cliques),
            "trusted_cliques": len([c for c in cliques if c.get("trust", 0) > 0.5]),
            "cliques": cliques[:20],  # Top 20 for report
        },
        "source_agreement": source_matrices,
        "calibration": calibration,
    }
    
    # Save report
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    return report


def print_analysis_summary(report: Dict[str, Any]):
    """Print formatted analysis summary."""
    console.print("\n" + "="*80)
    console.print("[bold cyan]📊 Automated Real Data Analysis Report[/bold cyan]")
    console.print("="*80)
    
    console.print(f"\n[bold]Data Collection:[/bold]")
    console.print(f"  Queries run: {report['num_queries']}")
    console.print(f"  Responses collected: {report['num_responses']}")
    console.print(f"  Responses with research: {report['num_responses_with_research']}")
    
    # Trust distribution
    if report.get("trust_distribution"):
        trust = report["trust_distribution"]
        console.print(f"\n[bold]Trust Distribution:[/bold]")
        console.print(f"  Sources analyzed: {trust['num_sources']}")
        console.print(f"  Correlation (credibility ↔ verifications): {trust['correlation']:.3f}")
        console.print(f"  Mean credibility: {sum(trust['source_credibility'].values()) / len(trust['source_credibility']):.3f}" if trust['source_credibility'] else "  N/A")
        
        # Top sources
        sorted_sources = sorted(
            trust['source_credibility'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        if sorted_sources:
            console.print(f"\n  [bold]Top Sources:[/bold]")
            for source, cred in sorted_sources:
                console.print(f"    {source[:50]:50s} {cred:.3f}")
    
    # Cliques
    if report.get("cliques", {}).get("total_cliques", 0) > 0:
        cliques_data = report["cliques"]
        console.print(f"\n[bold]Clique Analysis:[/bold]")
        console.print(f"  Total cliques: {cliques_data['total_cliques']}")
        console.print(f"  Trusted cliques (>0.5): {cliques_data['trusted_cliques']}")
        
        if cliques_data.get("cliques"):
            top_clique = max(cliques_data["cliques"], key=lambda x: x.get("trust", 0))
            console.print(f"  Top clique trust: {top_clique.get('trust', 0):.3f}")
            console.print(f"  Top clique coherence: {top_clique.get('coherence', 0):.3f}")
    
    # Source agreement
    if report.get("source_agreement", {}).get("total_claims", 0) > 0:
        agreement = report["source_agreement"]
        console.print(f"\n[bold]Source Agreement:[/bold]")
        console.print(f"  Total claims analyzed: {agreement['total_claims']}")
        console.print(f"  Strong agreements: {agreement['total_strong_agreements']}")
        console.print(f"  Agreement rate: {agreement['strong_agreement_rate']:.1%}")
    
    # Calibration
    if report.get("calibration", {}).get("avg_calibration_error") is not None:
        cal = report["calibration"]
        console.print(f"\n[bold]Calibration:[/bold]")
        console.print(f"  Average ECE: {cal['avg_calibration_error']:.3f}")
        console.print(f"  Measurements: {cal['num_measurements']}")
    
    console.print("\n" + "="*80)


def generate_markdown_report(report: Dict[str, Any], output_file: Path):
    """Generate markdown-formatted analysis report."""
    md_lines = [
        "# Automated Real Data Analysis Report",
        "",
        f"**Generated:** {report['timestamp']}",
        f"**Queries Analyzed:** {report['num_queries']}",
        f"**Responses Collected:** {report['num_responses']}",
        f"**Responses with Research:** {report['num_responses_with_research']}",
        "",
        "## Trust Distribution Analysis",
        "",
    ]
    
    if report.get("trust_distribution"):
        trust = report["trust_distribution"]
        md_lines.extend([
            f"- **Sources Analyzed:** {trust['num_sources']}",
            f"- **Correlation (Credibility ↔ Verifications):** {trust['correlation']:.3f}",
            "",
            "### Top Sources by Credibility",
            "",
            "| Source | Credibility | Verifications |",
            "|--------|------------|---------------|",
        ])
        
        sorted_sources = sorted(
            trust['source_credibility'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        for source, cred in sorted_sources:
            verif = trust['verification_info'].get(source, 0)
            md_lines.append(f"| {source[:50]} | {cred:.3f} | {verif:.1f} |")
    
    if report.get("cliques", {}).get("total_cliques", 0) > 0:
        cliques_data = report["cliques"]
        md_lines.extend([
            "",
            "## Clique Analysis",
            "",
            f"- **Total Cliques:** {cliques_data['total_cliques']}",
            f"- **Trusted Cliques (>0.5):** {cliques_data['trusted_cliques']}",
        ])
    
    if report.get("source_agreement", {}).get("total_claims", 0) > 0:
        agreement = report["source_agreement"]
        md_lines.extend([
            "",
            "## Source Agreement Analysis",
            "",
            f"- **Total Claims Analyzed:** {agreement['total_claims']}",
            f"- **Strong Agreements:** {agreement['total_strong_agreements']}",
            f"- **Agreement Rate:** {agreement['strong_agreement_rate']:.1%}",
        ])
    
    if report.get("calibration", {}).get("avg_calibration_error") is not None:
        cal = report["calibration"]
        md_lines.extend([
            "",
            "## Calibration Analysis",
            "",
            f"- **Average ECE:** {cal['avg_calibration_error']:.3f}",
            f"- **Measurements:** {cal['num_measurements']}",
        ])
    
    md_lines.extend([
        "",
        "---",
        "",
        "*This report was automatically generated by the BOP automated analysis pipeline.*",
    ])
    
    with open(output_file, "w") as f:
        f.write("\n".join(md_lines))


async def main():
    """Main automated analysis pipeline."""
    
    parser = argparse.ArgumentParser(description="Automated real data analysis pipeline")
    parser.add_argument(
        "--queries-file",
        type=Path,
        help="JSON file with list of queries to run (default: uses built-in queries)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory (default: analysis_output/)",
    )
    
    args = parser.parse_args()
    
    console.print(Panel.fit("[bold blue]Automated Real Data Analysis Pipeline[/bold blue]", border_style="blue"))
    console.print("\nThis script automatically runs real queries and analyzes the results.\n")
    
    # Load queries
    if args.queries_file and args.queries_file.exists():
        with open(args.queries_file) as f:
            queries = json.load(f)
        console.print(f"[dim]Loaded {len(queries)} queries from {args.queries_file}[/dim]")
    else:
        queries = DEFAULT_QUERIES
        console.print(f"[dim]Using {len(queries)} default queries[/dim]")
    
    # Output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = Path(__file__).parent.parent / "analysis_output"
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.format == "markdown":
        output_file = output_dir / f"analysis_report_{timestamp}.md"
        json_output_file = output_dir / f"analysis_report_{timestamp}.json"
    else:
        output_file = output_dir / f"analysis_report_{timestamp}.json"
        json_output_file = output_file
    
    # Initialize agent
    console.print("[dim]Initializing BOP agent...[/dim]")
    agent = KnowledgeAgent(enable_quality_feedback=True)
    
    # Run queries
    console.print(f"\n[bold]Running {len(queries)} real queries with research...[/bold]\n")
    responses = []
    
    for i, query in enumerate(queries, 1):
        console.print(f"[{i}/{len(queries)}] {query[:60]}...")
        response = await run_real_query(agent, query)
        if response:
            responses.append(response)
            if response.get("research_conducted"):
                console.print(f"  [green]✅ Research conducted[/green]")
            else:
                console.print(f"  [yellow]⚠️  Research not conducted (may need API keys)[/yellow]")
        else:
            console.print(f"  [red]❌ Query failed[/red]")
    
    # Generate analysis
    console.print(f"\n[bold]Generating analysis report...[/bold]")
    report = generate_analysis_report(responses, queries, json_output_file)
    
    # Generate markdown if requested
    if args.format == "markdown":
        generate_markdown_report(report, output_file)
        console.print(f"[dim]Markdown report: {output_file}[/dim]")
    
    # Print summary
    print_analysis_summary(report)
    
    console.print(f"\n[green]✅ Analysis complete![/green]")
    console.print(f"[dim]JSON report: {json_output_file}[/dim]")
    if args.format == "markdown":
        console.print(f"[dim]Markdown report: {output_file}[/dim]")
    
    # Return exit code based on data quality
    if report["num_responses_with_research"] == 0:
        console.print("\n[yellow]⚠️  Warning: No research data collected. Check API keys and MCP tools.[/yellow]")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

