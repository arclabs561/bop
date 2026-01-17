#!/usr/bin/env python3
"""Run comprehensive semantic evaluation on realistic data."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pran.semantic_eval import SemanticEvaluator
from pran.agent import KnowledgeAgent
from pran.orchestrator import StructuredOrchestrator
from pran.research import ResearchAgent, load_content
from pran.schemas import list_schemas


async def run_comprehensive_evaluation(
    content_dir: Path,
    output_dir: Path,
) -> None:
    """Run comprehensive semantic evaluation."""
    
    evaluator = SemanticEvaluator(output_dir=output_dir)
    knowledge_base = load_content(content_dir)
    
    agent = KnowledgeAgent()
    agent.llm_service = None
    
    print("=" * 60)
    print("COMPREHENSIVE SEMANTIC EVALUATION")
    print("=" * 60)
    print(f"Content: {len(knowledge_base)} documents")
    print(f"Output: {output_dir}\n")
    
    # 1. Accuracy evaluation on content-based queries
    print("[1/6] Evaluating semantic accuracy...")
    for doc_name, doc_content in list(knowledge_base.items())[:5]:
        content_lower = doc_content.lower()
        concepts = []
        
        if "trust" in content_lower:
            concepts.append("trust")
        if "uncertainty" in content_lower:
            concepts.append("uncertainty")
        if "knowledge" in content_lower:
            concepts.append("knowledge")
        if "structure" in content_lower:
            concepts.append("structure")
        if "reasoning" in content_lower:
            concepts.append("reasoning")
        
        if concepts:
            query = f"What does {doc_name} discuss about {concepts[0]}?"
            response_obj = await agent.chat(
                query,
                use_schema="chain_of_thought",
                use_research=False,
            )
            response = response_obj.get("response", "")
            
            evaluator.evaluate_accuracy(
                query=query,
                response=response,
                expected_concepts=concepts,
                metadata={
                    "document": doc_name,
                    "schema": "chain_of_thought",
                    "research": False,
                    "evaluation_round": 1,
                },
            )
    
    # 2. Completeness evaluation
    print("[2/6] Evaluating semantic completeness...")
    for doc_name, doc_content in list(knowledge_base.items())[:3]:
        query = f"Summarize the key concepts in {doc_name}"
        response_obj = await agent.chat(
            query,
            use_schema="decompose_and_synthesize",
            use_research=False,
        )
        response = response_obj.get("response", "")
        
        evaluator.evaluate_completeness(
            query=query,
            response=response,
            content_context=doc_content[:2000],
            metadata={
                "document": doc_name,
                "schema": "decompose_and_synthesize",
                "evaluation_round": 2,
            },
        )
    
    # 3. Relevance evaluation across query types
    print("[3/6] Evaluating semantic relevance...")
    query_types = [
        ("What is knowledge structure?", "definition"),
        ("How does trust propagate?", "process"),
        ("Why is uncertainty important?", "causation"),
        ("Compare trust and uncertainty", "comparison"),
        ("Analyze the implications", "analysis"),
    ]
    
    for query, q_type in query_types:
        response_obj = await agent.chat(query, use_schema="chain_of_thought", use_research=False)
        response = response_obj.get("response", "")
        
        evaluator.evaluate_relevance(
            query=query,
            response=response,
            metadata={
                "query_type": q_type,
                "schema": "chain_of_thought",
                "evaluation_round": 3,
            },
        )
    
    # 4. Consistency across schemas
    print("[4/6] Evaluating consistency across schemas...")
    query = "What is structured reasoning?"
    schemas = list_schemas()[:3]  # First 3 schemas
    
    responses = []
    for schema in schemas:
        response_obj = await agent.chat(query, use_schema=schema, use_research=False)
        responses.append(response_obj.get("response", ""))
    
    evaluator.evaluate_consistency(
        query=query,
        responses=responses,
        metadata={
            "schemas": ",".join(schemas),
            "evaluation_round": 4,
        },
    )
    
    # 5. Research quality evaluation
    print("[5/6] Evaluating research quality...")
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent)
    
    query = "What are the theoretical foundations of trust and uncertainty?"
    result = await orchestrator.research_with_schema(
        query,
        schema_name="decompose_and_synthesize",
    )
    
    synthesis = result.get("final_synthesis", "")
    all_content = " ".join(knowledge_base.values())[:2000] if knowledge_base else ""
    
    evaluator.evaluate_completeness(
        query=query,
        response=synthesis,
        content_context=all_content,
        metadata={
            "schema": "decompose_and_synthesize",
            "research": True,
            "subsolutions": len(result.get("subsolutions", [])),
            "tools_called": result.get("tools_called", 0),
            "evaluation_round": 5,
        },
    )
    
    # 6. Multi-schema comparison
    print("[6/6] Evaluating multi-schema comparison...")
    test_query = "Explain trust and uncertainty in knowledge graphs"
    
    for schema in schemas:
        response_obj = await agent.chat(test_query, use_schema=schema, use_research=False)
        response = response_obj.get("response", "")
        
        evaluator.evaluate_relevance(
            query=test_query,
            response=response,
            metadata={
                "schema": schema,
                "comparison_group": "multi_schema",
                "evaluation_round": 6,
            },
        )
    
    # Save all results
    print("\n" + "=" * 60)
    print("SAVING RESULTS")
    print("=" * 60)
    
    json_path = evaluator.save_judgments_json("comprehensive_judgments.json")
    csv_path = evaluator.save_judgments_csv("comprehensive_judgments.csv")
    report_path = evaluator.save_summary_report("comprehensive_report.md")
    
    print(f"✓ JSON: {json_path}")
    print(f"✓ CSV: {csv_path}")
    print(f"✓ Report: {report_path}")
    
    # Print summary
    aggregate = evaluator.aggregate_judgments()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total Judgments: {aggregate['total_judgments']}")
    print(f"Overall Mean Score: {aggregate['overall']['mean_score']:.3f}")
    print(f"Score Range: {aggregate['overall']['min_score']:.3f} - {aggregate['overall']['max_score']:.3f}")
    print(f"\nBy Type:")
    for j_type, stats in aggregate['by_type'].items():
        print(f"  {j_type}: {stats['mean']:.3f} (n={stats['count']}, std={stats['std']:.3f})")
    
    print(f"\nResults saved to: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run comprehensive semantic evaluation")
    parser.add_argument(
        "--content-dir",
        type=Path,
        default=Path(__file__).parent.parent / "content",
        help="Content directory",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("semantic_eval_outputs"),
        help="Output directory",
    )
    
    args = parser.parse_args()
    
    asyncio.run(run_comprehensive_evaluation(args.content_dir, args.output_dir))

