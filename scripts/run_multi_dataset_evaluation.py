#!/usr/bin/env python3
"""Run comprehensive evaluation across multiple datasets."""

import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from bop.semantic_eval import SemanticEvaluator
from bop.agent import KnowledgeAgent
from datasets import load_all_datasets, get_dataset_by_domain

console = Console()


async def evaluate_dataset(
    dataset_name: str,
    queries: list,
    agent: KnowledgeAgent,
    evaluator: SemanticEvaluator,
    max_queries: int = 10
) -> dict:
    """Evaluate a single dataset."""
    console.print(f"[cyan]Evaluating {dataset_name}...[/cyan]")
    
    results = {
        "total": 0,
        "evaluated": 0,
        "errors": 0,
        "with_temporal": 0,
        "with_research": 0,
    }
    
    for query_item in queries[:max_queries]:
        query = query_item.get("query", "")
        if not query or len(query) < 10:
            continue
        
        results["total"] += 1
        
        try:
            response_obj = await agent.chat(
                query,
                use_research=query_item.get("requires_research", False)
            )
            response = response_obj.get("response", "")
            
            # Track temporal features
            if response_obj.get("timestamp"):
                results["with_temporal"] += 1
            
            if response_obj.get("research_conducted"):
                results["with_research"] += 1
            
            # Evaluate
            evaluator.evaluate_relevance(
                query=query,
                response=response,
                metadata={
                    "dataset": dataset_name,
                    "domain": query_item.get("domain"),
                    "complexity": query_item.get("complexity"),
                    "query_type": query_item.get("query_type"),
                    "expected_concepts": query_item.get("expected_concepts", []),
                }
            )
            
            results["evaluated"] += 1
            
        except Exception as e:
            results["errors"] += 1
            console.print(f"[yellow]Error on query: {query[:50]}... - {e}[/yellow]")
    
    return results


async def main():
    """Run multi-dataset evaluation."""
    console.print(Panel.fit(
        "[bold blue]Multi-Dataset Evaluation[/bold blue]\n\n"
        "Evaluating agent across diverse query datasets.",
        border_style="blue"
    ))
    
    # Setup
    datasets_dir = Path(__file__).parent.parent / "datasets"
    output_dir = Path(__file__).parent.parent / "eval_outputs" / "multi_dataset"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    evaluator = SemanticEvaluator(output_dir=output_dir)
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None
    
    # Load all datasets
    all_datasets = load_all_datasets(datasets_dir)
    
    console.print(f"[green]Loaded {len(all_datasets)} datasets[/green]\n")
    
    # Evaluate each dataset
    dataset_results = {}
    
    for dataset_name, queries in all_datasets.items():
        results = await evaluate_dataset(
            dataset_name,
            queries,
            agent,
            evaluator,
            max_queries=10
        )
        dataset_results[dataset_name] = results
    
    # Save evaluation results
    json_path = evaluator.save_judgments_json("multi_dataset_evaluation.json")
    csv_path = evaluator.save_judgments_csv("multi_dataset_evaluation.csv")
    report_path = evaluator.save_summary_report("multi_dataset_evaluation_report.md")
    
    console.print(f"\n[green]Results saved:[/green]")
    console.print(f"  JSON: {json_path}")
    console.print(f"  CSV: {csv_path}")
    console.print(f"  Report: {report_path}")
    
    # Aggregate results
    aggregate = evaluator.aggregate_judgments()
    
    # Display summary
    console.print("\n" + "="*80)
    console.print("[bold]Dataset Evaluation Summary[/bold]")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Dataset", style="cyan")
    table.add_column("Total", style="white")
    table.add_column("Evaluated", style="green")
    table.add_column("Errors", style="yellow")
    table.add_column("Temporal", style="blue")
    table.add_column("Research", style="magenta")
    
    for dataset_name, results in dataset_results.items():
        table.add_row(
            dataset_name,
            str(results["total"]),
            str(results["evaluated"]),
            str(results["errors"]),
            str(results["with_temporal"]),
            str(results["with_research"]),
        )
    
    console.print(table)
    
    # Overall summary
    console.print(f"\n[bold]Overall Statistics:[/bold]")
    console.print(f"  Total judgments: {aggregate['total_judgments']}")
    console.print(f"  Average relevance: {aggregate.get('by_type', {}).get('relevance', {}).get('average_score', 0):.2f}")
    
    # Domain breakdown
    if "by_metadata" in aggregate:
        console.print(f"\n[bold]By Domain:[/bold]")
        for domain, stats in aggregate["by_metadata"].get("domain", {}).items():
            console.print(f"  {domain}: {stats.get('count', 0)} queries, "
                         f"avg score: {stats.get('average_score', 0):.2f}")


if __name__ == "__main__":
    asyncio.run(main())

