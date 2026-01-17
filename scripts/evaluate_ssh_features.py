"""
Evaluate SSH features (IB filtering, adaptive depth, resource triple, logical depth).

Measures impact of SSH integration on:
- Token reduction (IB filtering)
- Compute savings (adaptive depth)
- Resource tradeoffs (resource triple)
- Knowledge quality (logical depth)
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pran.agent import KnowledgeAgent
from pran.orchestrator import StructuredOrchestrator
from pran.research import ResearchAgent
from pran.adaptive_quality import AdaptiveQualityManager
from pran.quality_feedback import QualityFeedbackLoop
from pran.information_bottleneck import filter_with_information_bottleneck
import tempfile

console = Console()


async def evaluate_ib_filtering_impact(
    agent: KnowledgeAgent,
    queries: List[str],
) -> Dict[str, Any]:
    """Evaluate IB filtering impact on token reduction."""
    console.print("[bold]Evaluating IB Filtering Impact...[/bold]")
    
    total_original = 0
    total_filtered = 0
    compression_ratios = []
    
    for query in queries[:5]:  # Test on 5 queries
        try:
            response = await agent.chat(
                query,
                use_research=True,
                use_schema="decompose_and_synthesize",
            )
            
            research = response.get("research", {})
            subsolutions = research.get("subsolutions", [])
            
            # Count tokens in results (approximate)
            # CRITICAL: Verify structure matches what orchestrator returns
            for subsolution in subsolutions:
                if not isinstance(subsolution, dict):
                    continue
                
                results = subsolution.get("results", [])
                if not isinstance(results, list):
                    continue
                
                if len(results) > 2:
                    # Apply IB filtering to measure impact
                    # Note: This simulates what happens during synthesis
                    filtered, metadata = filter_with_information_bottleneck(
                        results, subsolution.get("subproblem", query), min_mi=0.3, max_results=5
                    )
                    compression_ratios.append(metadata["compression_ratio"])
                    total_original += len(results)
                    total_filtered += len(filtered)
        except Exception as e:
            console.print(f"[yellow]Query failed: {e}[/yellow]")
            continue
    
    avg_compression = sum(compression_ratios) / len(compression_ratios) if compression_ratios else 1.0
    token_reduction = (1.0 - avg_compression) * 100
    
    return {
        "avg_compression_ratio": avg_compression,
        "token_reduction_percent": token_reduction,
        "total_original_results": total_original,
        "total_filtered_results": total_filtered,
        "queries_tested": len(queries[:5]),
    }


async def evaluate_adaptive_depth_impact(
    agent: KnowledgeAgent,
    queries: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Evaluate adaptive reasoning depth impact on compute savings."""
    console.print("[bold]Evaluating Adaptive Reasoning Depth Impact...[/bold]")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        history_path = Path(tmpdir) / "test_history.json"
        feedback = QualityFeedbackLoop(evaluation_history_path=history_path)
        manager = AdaptiveQualityManager(feedback)
        agent.adaptive_manager = manager
        
        depth_estimates = []
        early_stops = 0
        total_subproblems = 0
        
        for item in queries[:5]:
            query = item.get("query", item) if isinstance(item, dict) else item
            expected_depth = item.get("expected_depth", 3) if isinstance(item, dict) else 3
            
            try:
                # Get strategy
                strategy = manager.get_adaptive_strategy(query)
                depth_estimates.append(strategy.reasoning_depth)
                
                # Conduct research
                response = await agent.chat(
                    query,
                    use_research=True,
                    use_schema="decompose_and_synthesize",
                )
                
                research = response.get("research", {})
                subsolutions = research.get("subsolutions", [])
                total_subproblems += len(subsolutions)
                
                # Learn from this query
                manager.update_from_evaluation(
                    query=query,
                    schema="decompose_and_synthesize",
                    used_research=True,
                    response_length=len(response.get("response", "")),
                    quality_score=0.8,
                    num_subproblems=len(subsolutions),
                )
                
                # Check if early stop would have happened
                if len(subsolutions) < expected_depth:
                    early_stops += 1
            except Exception as e:
                console.print(f"[yellow]Query failed: {e}[/yellow]")
                continue
        
        avg_depth = sum(depth_estimates) / len(depth_estimates) if depth_estimates else 3.0
        compute_savings = (1.0 - (total_subproblems / (expected_depth * len(queries[:5])))) * 100 if queries else 0.0
        
        return {
            "avg_estimated_depth": avg_depth,
            "early_stops": early_stops,
            "total_subproblems": total_subproblems,
            "compute_savings_percent": compute_savings,
            "queries_tested": len(queries[:5]),
        }


async def evaluate_resource_triple_metrics(
    orchestrator: StructuredOrchestrator,
    queries: List[str],
) -> Dict[str, Any]:
    """Evaluate resource triple and degradation triple metrics."""
    console.print("[bold]Evaluating Resource Triple Metrics...[/bold]")
    
    resource_triples = []
    degradation_triples = []
    
    for query in queries[:5]:
        try:
            result = await orchestrator.research_with_schema(
                query,
                schema_name="decompose_and_synthesize",
            )
            
            rt = result.get("resource_triple", {})
            dt = result.get("degradation_triple", {})
            
            if rt:
                resource_triples.append(rt)
            if dt:
                degradation_triples.append(dt)
        except Exception as e:
            console.print(f"[yellow]Query failed: {e}[/yellow]")
            continue
    
    # Aggregate metrics
    avg_depth = sum(rt["depth"] for rt in resource_triples) / len(resource_triples) if resource_triples else 0.0
    avg_width = sum(rt["width"] for rt in resource_triples) / len(resource_triples) if resource_triples else 0.0
    avg_coordination = sum(rt["coordination"] for rt in resource_triples) / len(resource_triples) if resource_triples else 0.0
    
    avg_noise = sum(dt["noise"] for dt in degradation_triples) / len(degradation_triples) if degradation_triples else 0.0
    avg_loss = sum(dt["loss"] for dt in degradation_triples) / len(degradation_triples) if degradation_triples else 0.0
    avg_waste = sum(dt["waste"] for dt in degradation_triples) / len(degradation_triples) if degradation_triples else 0.0
    
    return {
        "resource_triple": {
            "avg_depth": avg_depth,
            "avg_width": avg_width,
            "avg_coordination": avg_coordination,
        },
        "degradation_triple": {
            "avg_noise": avg_noise,
            "avg_loss": avg_loss,
            "avg_waste": avg_waste,
        },
        "queries_tested": len(queries[:5]),
    }


async def evaluate_logical_depth_metrics(
    orchestrator: StructuredOrchestrator,
    queries: List[str],
) -> Dict[str, Any]:
    """Evaluate logical depth computation."""
    console.print("[bold]Evaluating Logical Depth Metrics...[/bold]")
    
    logical_depths = []
    
    for query in queries[:5]:
        try:
            result = await orchestrator.research_with_schema(
                query,
                schema_name="decompose_and_synthesize",
            )
            
            topology = result.get("topology", {})
            avg_depth = topology.get("avg_logical_depth", 0.0)
            
            if avg_depth > 0:
                logical_depths.append(avg_depth)
        except Exception as e:
            console.print(f"[yellow]Query failed: {e}[/yellow]")
            continue
    
    avg_logical_depth = sum(logical_depths) / len(logical_depths) if logical_depths else 0.0
    
    return {
        "avg_logical_depth": avg_logical_depth,
        "queries_tested": len(queries[:5]),
        "nodes_with_depth": len(logical_depths),
    }


def print_evaluation_results(results: Dict[str, Dict[str, Any]]):
    """Print evaluation results in a formatted table."""
    table = Table(title="SSH Features Evaluation Results")
    
    table.add_column("Feature", style="cyan")
    table.add_column("Metric", style="magenta")
    table.add_column("Value", style="green")
    
    # IB Filtering
    ib = results.get("ib_filtering", {})
    table.add_row("IB Filtering", "Avg Compression Ratio", f"{ib.get('avg_compression_ratio', 0.0):.2%}")
    table.add_row("IB Filtering", "Token Reduction", f"{ib.get('token_reduction_percent', 0.0):.1f}%")
    
    # Adaptive Depth
    depth = results.get("adaptive_depth", {})
    table.add_row("Adaptive Depth", "Avg Estimated Depth", f"{depth.get('avg_estimated_depth', 0.0):.1f}")
    table.add_row("Adaptive Depth", "Early Stops", str(depth.get('early_stops', 0)))
    table.add_row("Adaptive Depth", "Compute Savings", f"{depth.get('compute_savings_percent', 0.0):.1f}%")
    
    # Resource Triple
    rt = results.get("resource_triple", {})
    rt_data = rt.get("resource_triple", {})
    table.add_row("Resource Triple", "Avg Depth", f"{rt_data.get('avg_depth', 0.0):.1f}")
    table.add_row("Resource Triple", "Avg Width", f"{rt_data.get('avg_width', 0.0):.1f}")
    table.add_row("Resource Triple", "Avg Coordination", f"{rt_data.get('avg_coordination', 0.0):.1f}")
    
    # Degradation Triple
    dt_data = rt.get("degradation_triple", {})
    table.add_row("Degradation Triple", "Avg Noise", f"{dt_data.get('avg_noise', 0.0):.3f}")
    table.add_row("Degradation Triple", "Avg Loss", f"{dt_data.get('avg_loss', 0.0):.3f}")
    table.add_row("Degradation Triple", "Avg Waste", f"{dt_data.get('avg_waste', 0.0):.3f}")
    
    # Logical Depth
    ld = results.get("logical_depth", {})
    table.add_row("Logical Depth", "Avg Logical Depth", f"{ld.get('avg_logical_depth', 0.0):.3f}")
    table.add_row("Logical Depth", "Nodes with Depth", str(ld.get('nodes_with_depth', 0)))
    
    console.print(table)


async def main():
    """Run SSH features evaluation."""
    console.print(Panel.fit(
        "[bold cyan]SSH Features Evaluation[/bold cyan]\n"
        "Evaluating IB filtering, adaptive depth, resource triple, and logical depth",
        border_style="cyan"
    ))
    
    # Load SSH evaluation dataset
    dataset_path = Path(__file__).parent.parent / "datasets" / "ssh_evaluation_dataset.json"
    if dataset_path.exists():
        with open(dataset_path, 'r') as f:
            dataset = json.load(f)
        queries = [item["query"] for item in dataset]
        query_items = dataset
    else:
        # Fallback queries
        queries = [
            "What is d-separation?",
            "What is trust?",
            "How does d-separation relate to causal inference?",
        ]
        query_items = [{"query": q, "expected_depth": 3} for q in queries]
    
    # Initialize components
    agent = KnowledgeAgent(enable_quality_feedback=True)
    orchestrator = StructuredOrchestrator(
        research_agent=ResearchAgent(use_mcp=False),
    )
    
    results = {}
    
    # Evaluate IB filtering
    results["ib_filtering"] = await evaluate_ib_filtering_impact(agent, queries)
    
    # Evaluate adaptive depth
    results["adaptive_depth"] = await evaluate_adaptive_depth_impact(agent, query_items)
    
    # Evaluate resource triple
    results["resource_triple"] = await evaluate_resource_triple_metrics(orchestrator, queries)
    
    # Evaluate logical depth
    results["logical_depth"] = await evaluate_logical_depth_metrics(orchestrator, queries)
    
    # Print results
    console.print("\n")
    print_evaluation_results(results)
    
    # Save results
    output_path = Path(__file__).parent.parent / "evaluation_results_ssh.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    console.print(f"\n[green]Results saved to {output_path}[/green]")


if __name__ == "__main__":
    import tempfile
    asyncio.run(main())

