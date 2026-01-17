"""
Real BOP Analysis - Running Actual Queries
============================================

This script runs REAL BOP queries and analyzes the ACTUAL results with
rigorous methodology. No simulations, no mock data—just real research
sessions with real trust metrics, real source matrices, and real topology.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List
import math
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

# Import BOP components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from pran.agent import KnowledgeAgent
from pran.quality_feedback import QualityFeedbackLoop

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


async def run_real_query(query: str, use_research: bool = True):
    """Run a real BOP query and return the actual response."""
    agent = KnowledgeAgent(enable_quality_feedback=True)
    
    try:
        response = await agent.chat(
            message=query,
            use_research=use_research,
            use_schema="decompose_and_synthesize",
        )
        return response
    except Exception as e:
        console.print(f"[red]Error running query: {e}[/red]")
        return None


def analyze_real_trust_distribution(response: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze real trust data from actual BOP response."""
    if not response or not response.get("research"):
        return None
    
    research = response["research"]
    topology = research.get("topology", {})
    
    if not topology:
        return None
    
    trust_summary = topology.get("trust_summary", {})
    source_credibility = topology.get("source_credibility", {})
    verification_info = topology.get("verification_info", {})
    
    if not source_credibility:
        return None
    
    # Compute correlation
    credibilities = list(source_credibility.values())
    verifications = [
        verification_info.get(source, {}).get("verification_count", 0)
        for source in source_credibility.keys()
    ]
    
    if len(credibilities) < 2:
        return None
    
    mean_cred = sum(credibilities) / len(credibilities)
    mean_verif = sum(verifications) / len(verifications) if verifications else 0
    
    covariance = sum((c - mean_cred) * (v - mean_verif) 
                     for c, v in zip(credibilities, verifications))
    std_cred = math.sqrt(sum((c - mean_cred)**2 for c in credibilities))
    std_verif = math.sqrt(sum((v - mean_verif)**2 for v in verifications)) if verifications else 1
    
    r = covariance / (std_cred * std_verif) if (std_cred * std_verif) > 0 else 0
    
    return {
        "source_credibility": source_credibility,
        "verification_info": verification_info,
        "trust_summary": trust_summary,
        "correlation": r,
        "mean_credibility": mean_cred,
        "mean_verifications": mean_verif,
    }


def analyze_real_cliques(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Analyze real clique data."""
    if not response or not response.get("research"):
        return []
    
    topology = response["research"].get("topology", {})
    cliques = topology.get("cliques", [])
    
    return cliques


def analyze_real_source_matrix(response: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze real source agreement matrix."""
    if not response or not response.get("research"):
        return {}
    
    research = response["research"]
    source_matrix = research.get("source_matrix", {})
    
    return source_matrix


def analyze_real_calibration(response: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze real calibration data if available."""
    # This would require tracking predictions vs outcomes over time
    # For now, we can analyze the trust summary for calibration error
    if not response or not response.get("research"):
        return None
    
    topology = response["research"].get("topology", {})
    trust_summary = topology.get("trust_summary", {})
    
    calibration_error = trust_summary.get("calibration_error")
    
    return {
        "calibration_error": calibration_error,
        "trust_summary": trust_summary,
    }


async def main():
    """Run real analysis on real BOP queries."""
    
    console.print(Panel.fit("[bold blue]Real BOP Analysis - Actual Data[/bold blue]", border_style="blue"))
    console.print("\nRunning REAL queries with REAL research to get REAL insights.\n")
    
    # Real queries that should produce interesting results
    queries = [
        "What is d-separation and how does it relate to causal inference?",
        "Explain information geometry and its applications to knowledge structures.",
        "How do trust metrics work in knowledge systems?",
    ]
    
    all_results = []
    
    for i, query in enumerate(queries, 1):
        console.print(f"\n[bold yellow]Query {i}:[/bold yellow] {query}")
        console.print("[dim]Running real BOP research...[/dim]")
        
        response = await run_real_query(query, use_research=True)
        
        if not response:
            console.print("[red]⚠️  Query failed or no research conducted[/red]")
            continue
        
        if not response.get("research_conducted"):
            console.print("[yellow]⚠️  Research not conducted (may need API keys)[/yellow]")
            continue
        
        console.print("[green]✅ Got real response with research data[/green]")
        
        # Store for analysis
        all_results.append({
            "query": query,
            "response": response,
        })
    
    if not all_results:
        console.print("\n[red]No successful queries. This might be because:")
        console.print("  1. API keys not set (OPENAI_API_KEY or ANTHROPIC_API_KEY)")
        console.print("  2. MCP tools not available")
        console.print("  3. Network issues[/red]")
        console.print("\n[dim]Falling back to analyzing structure of response format...[/dim]")
        
        # Even without real data, we can show what the analysis would look like
        console.print("\n[bold]Analysis Framework Ready:[/bold]")
        console.print("  - Trust distribution analysis")
        console.print("  - Clique coherence analysis")
        console.print("  - Source agreement matrix analysis")
        console.print("  - Calibration error analysis")
        console.print("  - Graph topology analysis")
        console.print("\n[dim]Run with API keys configured to get real insights![/dim]")
        return
    
    # Analyze real data
    console.print("\n" + "="*80)
    console.print("[bold cyan]📊 Analyzing Real Results[/bold cyan]")
    console.print("="*80)
    
    for result in all_results:
        query = result["query"]
        response = result["response"]
        
        console.print(f"\n[bold]Query:[/bold] {query}")
        
        # Trust distribution
        trust_data = analyze_real_trust_distribution(response)
        if trust_data:
            console.print(f"\n  [green]Trust Analysis:[/green]")
            console.print(f"    Sources: {len(trust_data['source_credibility'])}")
            console.print(f"    Correlation: {trust_data['correlation']:.3f}")
            console.print(f"    Mean Credibility: {trust_data['mean_credibility']:.3f}")
            
            # Show top sources
            sorted_sources = sorted(
                trust_data['source_credibility'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            for source, cred in sorted_sources:
                console.print(f"      {source[:40]:40s} {cred:.3f}")
        
        # Cliques
        cliques = analyze_real_cliques(response)
        if cliques:
            console.print(f"\n  [green]Clique Analysis:[/green]")
            console.print(f"    Cliques found: {len(cliques)}")
            
            trusted_cliques = [c for c in cliques if c.get("trust", 0) > 0.5]
            console.print(f"    Trusted cliques: {len(trusted_cliques)}")
            
            if trusted_cliques:
                top_clique = max(trusted_cliques, key=lambda x: x.get("trust", 0))
                console.print(f"    Top clique trust: {top_clique.get('trust', 0):.3f}")
                console.print(f"    Top clique coherence: {top_clique.get('coherence', 0):.3f}")
        
        # Source matrix
        source_matrix = analyze_real_source_matrix(response)
        if source_matrix:
            console.print(f"\n  [green]Source Agreement:[/green]")
            console.print(f"    Claims analyzed: {len(source_matrix)}")
            
            strong_agreements = sum(
                1 for c in source_matrix.values()
                if c.get("consensus") == "strong_agreement"
            )
            console.print(f"    Strong agreements: {strong_agreements}")
        
        # Calibration
        calibration = analyze_real_calibration(response)
        if calibration and calibration.get("calibration_error") is not None:
            console.print(f"\n  [green]Calibration:[/green]")
            console.print(f"    Calibration error: {calibration['calibration_error']:.3f}")
    
    console.print("\n" + "="*80)
    console.print("[bold green]✅ Real Analysis Complete[/bold green]")
    console.print("="*80)
    
    # Save results for further analysis
    output_file = Path(__file__).parent / "real_analysis_results.json"
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    
    console.print(f"\n[dim]Results saved to: {output_file}[/dim]")


if __name__ == "__main__":
    asyncio.run(main())

