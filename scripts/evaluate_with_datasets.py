"""
Evaluate BOP with external datasets.

Tests BOP's performance on:
- FEVER: Fact verification with conflicting sources
- HotpotQA: Multi-document question answering
- SciFact: Scientific fact checking
- Calibration Ground Truth: Known calibration scenarios
- Source Credibility Ground Truth: Known credibility scores
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bop.agent import KnowledgeAgent
from datasets.load_external_datasets import (
    load_fever,
    load_hotpotqa,
    load_scifact,
    get_dataset_summary,
    DATASETS_AVAILABLE,
)
from datasets import load_dataset as load_internal_dataset_func

console = Console()


async def evaluate_fever(
    agent: KnowledgeAgent,
    max_samples: int = 10,
    split: str = "dev",
) -> Dict[str, Any]:
    """Evaluate BOP on FEVER fact verification dataset."""
    console.print("\n[bold cyan]Evaluating on FEVER Dataset[/bold cyan]")
    console.print("─" * 80)
    
    if not DATASETS_AVAILABLE:
        return {"error": "HuggingFace datasets not available"}
    
    try:
        fever_data = load_fever(split=split, max_samples=max_samples)
    except Exception as e:
        return {"error": f"Failed to load FEVER: {e}"}
    
    results = {
        "total": len(fever_data),
        "supported": 0,
        "refuted": 0,
        "not_enough_info": 0,
        "correct_predictions": 0,
        "trust_scores": [],
        "uncertainty_scores": [],
    }
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Processing FEVER claims...", total=len(fever_data))
        
        for claim_data in fever_data:
            claim = claim_data["claim"]
            label = claim_data["label"]
            
            try:
                response = await agent.chat(
                    f"Verify this claim: {claim}",
                    use_research=True,
                )
                
                # Extract trust metrics
                if response.get("research") and response["research"].get("topology"):
                    topology = response["research"]["topology"]
                    trust_summary = topology.get("trust_summary", {})
                    avg_trust = trust_summary.get("avg_trust", 0.5)
                    results["trust_scores"].append(avg_trust)
                    
                    # Check if prediction matches label
                    if label == "SUPPORTS" and avg_trust > 0.7:
                        results["correct_predictions"] += 1
                    elif label == "REFUTES" and avg_trust < 0.5:
                        results["correct_predictions"] += 1
                    elif label == "NOT ENOUGH INFO" and 0.4 <= avg_trust <= 0.6:
                        results["correct_predictions"] += 1
                
                # Count labels
                if label == "SUPPORTS":
                    results["supported"] += 1
                elif label == "REFUTES":
                    results["refuted"] += 1
                else:
                    results["not_enough_info"] += 1
                    
            except Exception as e:
                console.print(f"[red]Error processing claim: {e}[/red]")
            
            progress.update(task, advance=1)
    
    results["accuracy"] = results["correct_predictions"] / results["total"] if results["total"] > 0 else 0.0
    results["avg_trust"] = sum(results["trust_scores"]) / len(results["trust_scores"]) if results["trust_scores"] else 0.0
    
    return results


async def evaluate_hotpotqa(
    agent: KnowledgeAgent,
    max_samples: int = 10,
    split: str = "dev",
) -> Dict[str, Any]:
    """Evaluate BOP on HotpotQA multi-document question answering."""
    console.print("\n[bold cyan]Evaluating on HotpotQA Dataset[/bold cyan]")
    console.print("─" * 80)
    
    if not DATASETS_AVAILABLE:
        return {"error": "HuggingFace datasets not available"}
    
    try:
        hotpot_data = load_hotpotqa(split=split, max_samples=max_samples)
    except Exception as e:
        return {"error": f"Failed to load HotpotQA: {e}"}
    
    results = {
        "total": len(hotpot_data),
        "correct_answers": 0,
        "multi_hop_count": 0,
        "detected_multi_hop": 0,
        "synthesis_quality": [],
    }
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Processing HotpotQA questions...", total=len(hotpot_data))
        
        for question_data in hotpot_data:
            question = question_data["question"]
            expected_answer = question_data.get("answer", "")
            
            try:
                response = await agent.chat(
                    question,
                    use_research=True,
                )
                
                # Check if answer is correct (simple string matching)
                response_text = response.get("response", "").lower()
                if expected_answer.lower() in response_text:
                    results["correct_answers"] += 1
                
                # Detect multi-hop questions (require multiple documents/entities)
                is_multi_hop = _detect_multi_hop_question(question)
                
                # Check if multi-hop reasoning was used
                if response.get("research") and response["research"].get("subsolutions"):
                    subsolutions = response["research"]["subsolutions"]
                    if len(subsolutions) >= 2:
                        results["multi_hop_count"] += 1
                
                # Track if question was detected as multi-hop
                if is_multi_hop:
                    results["detected_multi_hop"] = results.get("detected_multi_hop", 0) + 1
                
            except Exception as e:
                console.print(f"[red]Error processing question: {e}[/red]")
            
            progress.update(task, advance=1)
    
    results["accuracy"] = results["correct_answers"] / results["total"] if results["total"] > 0 else 0.0
    results["multi_hop_rate"] = results["multi_hop_count"] / results["total"] if results["total"] > 0 else 0.0
    results["multi_hop_detection_rate"] = (
        results["detected_multi_hop"] / results["total"] if results["total"] > 0 else 0.0
    ) * 100.0  # Percentage
    
    return results


def _detect_multi_hop_question(question: str) -> bool:
    """
    Detect if a question requires multi-hop reasoning.
    
    Multi-hop questions typically:
    - Ask about relationships between multiple entities
    - Use words like "both", "and", "compare", "relationship"
    - Ask "which" questions with multiple options
    - Require information from multiple documents
    """
    question_lower = question.lower()
    
    # Multi-hop indicators
    multi_hop_keywords = [
        "both", "and", "compare", "relationship", "between",
        "which", "either", "or", "together", "combined",
        "difference", "similarity", "connection", "link",
    ]
    
    # Count entities (proper nouns, capitalized words)
    words = question.split()
    capitalized_words = [w for w in words if w[0].isupper() and len(w) > 1]
    
    # Multi-hop if:
    # 1. Contains multi-hop keywords
    # 2. Has multiple entities (2+ capitalized words)
    # 3. Contains "and" with entities
    has_keywords = any(keyword in question_lower for keyword in multi_hop_keywords)
    has_multiple_entities = len(capitalized_words) >= 2
    has_and_with_entities = "and" in question_lower and len(capitalized_words) >= 2
    
    return has_keywords or has_multiple_entities or has_and_with_entities


async def evaluate_scifact(
    agent: KnowledgeAgent,
    max_samples: int = 10,
) -> Dict[str, Any]:
    """Evaluate BOP on SciFact scientific fact checking."""
    console.print("\n[bold cyan]Evaluating on SciFact Dataset[/bold cyan]")
    console.print("─" * 80)
    
    if not DATASETS_AVAILABLE:
        return {"error": "HuggingFace datasets not available"}
    
    try:
        scifact_data = load_scifact(max_samples=max_samples)
    except Exception as e:
        return {"error": f"Failed to load SciFact: {e}"}
    
    results = {
        "total": len(scifact_data),
        "supported": 0,
        "contradicted": 0,
        "correct_predictions": 0,
        "trust_scores": [],
    }
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Processing SciFact claims...", total=len(scifact_data))
        
        for claim_data in scifact_data:
            claim = claim_data["claim"]
            label = claim_data.get("label", "")
            
            try:
                response = await agent.chat(
                    f"Verify this scientific claim: {claim}",
                    use_research=True,
                )
                
                # Extract trust metrics
                if response.get("research") and response["research"].get("topology"):
                    topology = response["research"]["topology"]
                    trust_summary = topology.get("trust_summary", {})
                    avg_trust = trust_summary.get("avg_trust", 0.5)
                    results["trust_scores"].append(avg_trust)
                    
                    # Check if prediction matches label
                    if label == "SUPPORT" and avg_trust > 0.7:
                        results["correct_predictions"] += 1
                    elif label == "CONTRADICT" and avg_trust < 0.5:
                        results["correct_predictions"] += 1
                
                # Count labels
                if label == "SUPPORT":
                    results["supported"] += 1
                elif label == "CONTRADICT":
                    results["contradicted"] += 1
                    
            except Exception as e:
                console.print(f"[red]Error processing claim: {e}[/red]")
            
            progress.update(task, advance=1)
    
    results["accuracy"] = results["correct_predictions"] / results["total"] if results["total"] > 0 else 0.0
    results["avg_trust"] = sum(results["trust_scores"]) / len(results["trust_scores"]) if results["trust_scores"] else 0.0
    
    return results


def evaluate_calibration_ground_truth() -> Dict[str, Any]:
    """Evaluate calibration improvement with known ground truth."""
    console.print("\n[bold cyan]Evaluating Calibration Ground Truth[/bold cyan]")
    console.print("─" * 80)
    
    try:
        from pathlib import Path
        calibration_path = Path(__file__).parent.parent / "datasets" / "calibration_ground_truth.json"
        with open(calibration_path, "r") as f:
            calibration_data = json.load(f)
    except Exception as e:
        return {"error": f"Failed to load calibration data: {e}"}
    
    from bop.calibration_improvement import improve_calibration_with_uncertainty
    import numpy as np
    
    results = {
        "total_scenarios": len(calibration_data),
        "scenarios_tested": 0,
        "ece_reductions": [],
    }
    
    for scenario in calibration_data:
        scenario_name = scenario.get("scenario", "unknown")
        predictions = scenario.get("predictions", [])
        actual_outcomes = scenario.get("actual_outcomes", [])
        
        # Convert to numpy arrays
        pred_arrays = [np.array([p, 1-p]) for p in predictions]
        confidence_scores = predictions
        
        try:
            result = improve_calibration_with_uncertainty(
                pred_arrays,
                confidence_scores,
                actual_outcomes,
                use_aleatoric_weighting=True,
            )
            
            if result.get("calibration_improvement"):
                ece_reduction = result["calibration_improvement"].get("ece_reduction", 0.0)
                results["ece_reductions"].append(ece_reduction)
                results["scenarios_tested"] += 1
                
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to test {scenario_name}: {e}[/yellow]")
    
    results["avg_ece_reduction"] = (
        sum(results["ece_reductions"]) / len(results["ece_reductions"])
        if results["ece_reductions"] else 0.0
    )
    
    return results


def evaluate_source_credibility_ground_truth() -> Dict[str, Any]:
    """Evaluate source credibility with known ground truth."""
    console.print("\n[bold cyan]Evaluating Source Credibility Ground Truth[/bold cyan]")
    console.print("─" * 80)
    
    try:
        from pathlib import Path
        credibility_path = Path(__file__).parent.parent / "datasets" / "source_credibility_ground_truth.json"
        with open(credibility_path, "r") as f:
            credibility_data = json.load(f)
    except Exception as e:
        return {"error": f"Failed to load credibility data: {e}"}
    
    from bop.uncertainty_tool_selection import select_tools_with_muse
    
    results = {
        "total_sources": len(credibility_data),
        "sources_tested": 0,
        "filtering_accuracy": 0,
    }
    
    # Test MUSE selection with known credibility
    candidate_tools = [item["source"] for item in credibility_data]
    tool_metadata = [
        {"credibility": item["credibility"]}
        for item in credibility_data
    ]
    
    try:
        selected, metadata = select_tools_with_muse(
            candidate_tools,
            tool_metadata,
            "test query",
            min_credibility=0.5,  # Filter sources below 0.5
            max_tools=10,  # Allow all high-credibility sources
        )
        
        # Check if filtering is correct
        # Sources with credibility >= 0.5 should be selected (or at least not filtered)
        # Sources with credibility < 0.5 should be filtered out
        expected_selected = [
            item["source"]
            for item in credibility_data
            if item["credibility"] >= 0.5
        ]
        expected_filtered = [
            item["source"]
            for item in credibility_data
            if item["credibility"] < 0.5
        ]
        
        # Calculate accuracy: 
        # 1. All selected sources should have credibility >= 0.5 (correct selections)
        # 2. All filtered sources should have credibility < 0.5 (correct filters)
        # 3. MUSE may select fewer than all high-credibility sources (that's OK)
        
        # Check if all selected sources are high-credibility
        selected_credibilities = [
            item["credibility"] for item in credibility_data
            if item["source"] in selected
        ]
        correct_selections = sum(1 for cred in selected_credibilities if cred >= 0.5)
        incorrect_selections = sum(1 for cred in selected_credibilities if cred < 0.5)
        
        # Check if all filtered sources are low-credibility
        filtered_sources = set(candidate_tools) - set(selected)
        filtered_credibilities = [
            item["credibility"] for item in credibility_data
            if item["source"] in filtered_sources
        ]
        correct_filters = sum(1 for cred in filtered_credibilities if cred < 0.5)
        incorrect_filters = sum(1 for cred in filtered_credibilities if cred >= 0.5)
        
        # Total accuracy: (correct selections + correct filters) / total
        total_correct = correct_selections + correct_filters
        total_sources = len(credibility_data)
        
        results["sources_tested"] = len(selected)
        results["expected_selected_count"] = len(expected_selected)
        results["expected_filtered_count"] = len(expected_filtered)
        results["correct_selections"] = correct_selections
        results["incorrect_selections"] = incorrect_selections
        results["correct_filters"] = correct_filters
        results["incorrect_filters"] = incorrect_filters
        results["filtering_accuracy"] = (
            total_correct / total_sources if total_sources > 0 else 0.0
        ) * 100.0  # Convert to percentage
        
    except Exception as e:
        return {"error": f"Failed to test credibility: {e}"}
    
    return results


def print_results_table(results: Dict[str, Dict[str, Any]]):
    """Print evaluation results in a table."""
    table = Table(title="Dataset Evaluation Results")
    table.add_column("Dataset", style="cyan")
    table.add_column("Metric", style="magenta")
    table.add_column("Value", style="green")
    
    for dataset_name, dataset_results in results.items():
        if "error" in dataset_results:
            table.add_row(dataset_name, "Status", f"[red]Error: {dataset_results['error']}[/red]")
            continue
        
        if dataset_name == "fever":
            table.add_row("FEVER", "Total Claims", str(dataset_results.get("total", 0)))
            table.add_row("FEVER", "Accuracy", f"{dataset_results.get('accuracy', 0.0):.2%}")
            table.add_row("FEVER", "Avg Trust", f"{dataset_results.get('avg_trust', 0.0):.3f}")
        elif dataset_name == "hotpotqa":
            table.add_row("HotpotQA", "Total Questions", str(dataset_results.get("total", 0)))
            table.add_row("HotpotQA", "Accuracy", f"{dataset_results.get('accuracy', 0.0):.2%}")
            table.add_row("HotpotQA", "Multi-hop Rate", f"{dataset_results.get('multi_hop_rate', 0.0):.2%}")
            table.add_row("HotpotQA", "Multi-hop Detection", f"{dataset_results.get('multi_hop_detection_rate', 0.0):.1f}%")
        elif dataset_name == "scifact":
            table.add_row("SciFact", "Total Claims", str(dataset_results.get("total", 0)))
            table.add_row("SciFact", "Accuracy", f"{dataset_results.get('accuracy', 0.0):.2%}")
            table.add_row("SciFact", "Avg Trust", f"{dataset_results.get('avg_trust', 0.0):.3f}")
        elif dataset_name == "calibration":
            table.add_row("Calibration", "Scenarios Tested", str(dataset_results.get("scenarios_tested", 0)))
            table.add_row("Calibration", "Avg ECE Reduction", f"{dataset_results.get('avg_ece_reduction', 0.0):.4f}")
        elif dataset_name == "credibility":
            table.add_row("Credibility", "Sources Tested", str(dataset_results.get("sources_tested", 0)))
            table.add_row("Credibility", "Expected Selected", str(dataset_results.get("expected_selected_count", 0)))
            table.add_row("Credibility", "Correct Selections", str(dataset_results.get("correct_selections", 0)))
            table.add_row("Credibility", "Correct Filters", str(dataset_results.get("correct_filters", 0)))
            table.add_row("Credibility", "Filtering Accuracy", f"{dataset_results.get('filtering_accuracy', 0.0):.2f}%")
    
    console.print(table)


async def main():
    """Run all dataset evaluations."""
    console.print(Panel.fit(
        "[bold cyan]BOP Dataset Evaluation[/bold cyan]\n"
        "Evaluating BOP on external and internal datasets",
        border_style="cyan"
    ))
    
    # Check dataset availability
    summary = get_dataset_summary()
    if not summary["datasets_available"]:
        console.print("[red]HuggingFace datasets not available. Install with: pip install datasets[/red]")
        return
    
    # Initialize agent
    agent = KnowledgeAgent()
    
    # Run evaluations
    results = {}
    
    # FEVER evaluation
    console.print("\n[bold]Starting FEVER evaluation...[/bold]")
    results["fever"] = await evaluate_fever(agent, max_samples=10, split="dev")
    
    # HotpotQA evaluation
    console.print("\n[bold]Starting HotpotQA evaluation...[/bold]")
    results["hotpotqa"] = await evaluate_hotpotqa(agent, max_samples=10, split="dev")
    
    # SciFact evaluation
    console.print("\n[bold]Starting SciFact evaluation...[/bold]")
    results["scifact"] = await evaluate_scifact(agent, max_samples=10)
    
    # Calibration ground truth
    console.print("\n[bold]Starting Calibration evaluation...[/bold]")
    results["calibration"] = evaluate_calibration_ground_truth()
    
    # Source credibility ground truth
    console.print("\n[bold]Starting Credibility evaluation...[/bold]")
    results["credibility"] = evaluate_source_credibility_ground_truth()
    
    # Print results
    console.print("\n")
    print_results_table(results)
    
    # Save results
    output_path = Path(__file__).parent.parent / "evaluation_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    console.print(f"\n[green]Results saved to {output_path}[/green]")


if __name__ == "__main__":
    asyncio.run(main())

