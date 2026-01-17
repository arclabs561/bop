#!/usr/bin/env python3
"""Run comprehensive semantic evaluation with diverse data and scenarios."""

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


async def run_diverse_evaluation(
    content_dir: Path,
    output_dir: Path,
) -> None:
    """Run diverse semantic evaluation with varied scenarios."""
    
    evaluator = SemanticEvaluator(output_dir=output_dir)
    knowledge_base = load_content(content_dir)
    
    agent = KnowledgeAgent()
    agent.llm_service = None
    
    print("=" * 70)
    print("DIVERSE SEMANTIC EVALUATION - ITERATION 2")
    print("=" * 70)
    print(f"Content: {len(knowledge_base)} documents")
    print(f"Output: {output_dir}\n")
    
    # 1. Diverse query types and complexities
    print("[1/8] Evaluating diverse query types...")
    diverse_queries = [
        # Simple factual
        ("What is trust?", "simple_factual"),
        ("Define uncertainty", "definition"),
        
        # Complex multi-part
        ("How does trust relate to uncertainty in knowledge graphs?", "complex_relationship"),
        ("Compare and contrast trust propagation with uncertainty quantification", "comparison"),
        
        # Analytical
        ("Analyze the implications of low trust scores on knowledge graph reliability", "analysis"),
        ("What are the trade-offs between epistemic and aleatoric uncertainty?", "tradeoff"),
        
        # Procedural
        ("Explain how to calculate trust scores", "procedural"),
        ("Describe the steps for uncertainty quantification", "procedural"),
        
        # Abstract/conceptual
        ("What is the philosophical basis of knowledge structure?", "abstract"),
        ("How do different traditions view knowledge organization?", "abstract"),
    ]
    
    for query, q_type in diverse_queries:
        response_obj = await agent.chat(query, use_schema="chain_of_thought", use_research=False)
        response = response_obj.get("response", "")
        
        evaluator.evaluate_relevance(
            query=query,
            response=response,
            metadata={
                "query_type": q_type,
                "complexity": "simple" if len(query.split()) < 5 else "complex",
                "schema": "chain_of_thought",
                "evaluation_round": 1,
            },
        )
    
    # 2. Schema comparison with same queries
    print("[2/8] Comparing schemas on identical queries...")
    test_queries = [
        "What is knowledge structure?",
        "How does trust work?",
        "Why is uncertainty important?",
    ]
    
    for query in test_queries:
        responses_by_schema = {}
        for schema in ["chain_of_thought", "decompose_and_synthesize", "hypothesize_and_test"]:
            response_obj = await agent.chat(query, use_schema=schema, use_research=False)
            responses_by_schema[schema] = response_obj.get("response", "")
        
        # Evaluate consistency
        evaluator.evaluate_consistency(
            query=query,
            responses=list(responses_by_schema.values()),
            metadata={
                "schemas": ",".join(responses_by_schema.keys()),
                "evaluation_round": 2,
            },
        )
        
        # Also evaluate each individually for comparison
        for schema, response in responses_by_schema.items():
            evaluator.evaluate_relevance(
                query=query,
                response=response,
                metadata={
                    "schema": schema,
                    "comparison_group": "schema_comparison",
                    "evaluation_round": 2,
                },
            )
    
    # 3. Content-based accuracy with varied concepts
    print("[3/8] Evaluating accuracy with varied concept types...")
    concept_tests = []
    
    for doc_name, doc_content in list(knowledge_base.items())[:3]:
        content_lower = doc_content.lower()
        
        # Extract different types of concepts
        simple_concepts = []
        complex_concepts = []
        technical_concepts = []
        
        # Simple: single words
        if "trust" in content_lower:
            simple_concepts.append("trust")
        if "uncertainty" in content_lower:
            simple_concepts.append("uncertainty")
        
        # Complex: multi-word or technical
        if "knowledge structure" in content_lower:
            complex_concepts.append("knowledge structure")
        if "epistemic uncertainty" in content_lower:
            technical_concepts.append("epistemic uncertainty")
        if "aleatoric uncertainty" in content_lower:
            technical_concepts.append("aleatoric uncertainty")
        
        # Test with different concept sets
        if simple_concepts:
            query = f"What does {doc_name} say about {simple_concepts[0]}?"
            response_obj = await agent.chat(query, use_schema="chain_of_thought", use_research=False)
            response = response_obj.get("response", "")
            
            evaluator.evaluate_accuracy(
                query=query,
                response=response,
                expected_concepts=simple_concepts,
                metadata={
                    "document": doc_name,
                    "concept_type": "simple",
                    "evaluation_round": 3,
                },
            )
        
        if complex_concepts:
            query = f"Explain {complex_concepts[0]} from {doc_name}"
            response_obj = await agent.chat(query, use_schema="decompose_and_synthesize", use_research=False)
            response = response_obj.get("response", "")
            
            evaluator.evaluate_accuracy(
                query=query,
                response=response,
                expected_concepts=complex_concepts,
                metadata={
                    "document": doc_name,
                    "concept_type": "complex",
                    "evaluation_round": 3,
                },
            )
    
    # 4. Completeness with different context sizes
    print("[4/8] Evaluating completeness with varied context...")
    for doc_name, doc_content in list(knowledge_base.items())[:2]:
        # Small context (first 500 chars)
        query = f"Summarize {doc_name}"
        response_obj = await agent.chat(query, use_schema="decompose_and_synthesize", use_research=False)
        response = response_obj.get("response", "")
        
        evaluator.evaluate_completeness(
            query=query,
            response=response,
            content_context=doc_content[:500],
            metadata={
                "document": doc_name,
                "context_size": "small",
                "evaluation_round": 4,
            },
        )
        
        # Large context (first 3000 chars)
        evaluator.evaluate_completeness(
            query=query,
            response=response,
            content_context=doc_content[:3000],
            metadata={
                "document": doc_name,
                "context_size": "large",
                "evaluation_round": 4,
            },
        )
    
    # 5. Research vs non-research comparison
    print("[5/8] Comparing research vs non-research responses...")
    research_queries = [
        "What are recent developments in trust and uncertainty?",
        "How do knowledge graphs handle uncertainty?",
    ]
    
    for query in research_queries:
        # Without research
        response_obj = await agent.chat(query, use_schema="chain_of_thought", use_research=False)
        response_no_research = response_obj.get("response", "")
        
        evaluator.evaluate_relevance(
            query=query,
            response=response_no_research,
            metadata={
                "research": False,
                "comparison_group": "research_comparison",
                "evaluation_round": 5,
            },
        )
        
        # With research (if available)
        try:
            research_agent = ResearchAgent()
            orchestrator = StructuredOrchestrator(research_agent)
            result = await orchestrator.research_with_schema(query, schema_name="decompose_and_synthesize")
            response_research = result.get("final_synthesis", "")
            
            evaluator.evaluate_relevance(
                query=query,
                response=response_research,
                metadata={
                    "research": True,
                    "comparison_group": "research_comparison",
                    "tools_called": result.get("tools_called", 0),
                    "evaluation_round": 5,
                },
            )
        except Exception as e:
            print(f"  Research failed for '{query}': {e}")
    
    # 6. Edge cases: very short, very long, ambiguous queries
    print("[6/8] Testing edge cases...")
    edge_cases = [
        ("?", "ambiguous"),  # Very ambiguous
        ("trust", "single_word"),  # Single word
        ("What is the comprehensive theoretical framework underlying the relationship between trust, uncertainty, and knowledge structure in complex information systems?", "very_long"),  # Very long
        ("", "empty"),  # Empty (should handle gracefully)
    ]
    
    for query, case_type in edge_cases:
        if not query:  # Skip empty
            continue
        response_obj = await agent.chat(query, use_schema="chain_of_thought", use_research=False)
        response = response_obj.get("response", "")
        
        evaluator.evaluate_relevance(
            query=query,
            response=response,
            metadata={
                "edge_case": case_type,
                "evaluation_round": 6,
            },
        )
    
    # 7. Multi-hop reasoning queries
    print("[7/8] Testing multi-hop reasoning...")
    multi_hop_queries = [
        "If trust is low and uncertainty is high, what does that imply about knowledge graph quality?",
        "How does the relationship between trust and uncertainty affect knowledge structure?",
        "What happens when epistemic uncertainty increases while aleatoric uncertainty decreases?",
    ]
    
    for query in multi_hop_queries:
        response_obj = await agent.chat(query, use_schema="hypothesize_and_test", use_research=False)
        response = response_obj.get("response", "")
        
        evaluator.evaluate_relevance(
            query=query,
            response=response,
            metadata={
                "reasoning_type": "multi_hop",
                "evaluation_round": 7,
            },
        )
    
    # 8. Temporal and comparative queries
    print("[8/8] Testing temporal and comparative queries...")
    temporal_queries = [
        "How has the understanding of trust evolved?",
        "What are the differences between traditional and modern approaches to uncertainty?",
        "Compare Bayesian and frequentist views on uncertainty",
    ]
    
    for query in temporal_queries:
        response_obj = await agent.chat(query, use_schema="chain_of_thought", use_research=False)
        response = response_obj.get("response", "")
        
        evaluator.evaluate_relevance(
            query=query,
            response=response,
            metadata={
                "query_category": "temporal_comparative",
                "evaluation_round": 8,
            },
        )
    
    # Save all results
    print("\n" + "=" * 70)
    print("SAVING RESULTS")
    print("=" * 70)
    
    json_path = evaluator.save_judgments_json("diverse_judgments.json")
    csv_path = evaluator.save_judgments_csv("diverse_judgments.csv")
    report_path = evaluator.save_summary_report("diverse_report.md")
    
    print(f"✓ JSON: {json_path}")
    print(f"✓ CSV: {csv_path}")
    print(f"✓ Report: {report_path}")
    
    # Print summary
    aggregate = evaluator.aggregate_judgments()
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total Judgments: {aggregate['total_judgments']}")
    print(f"Overall Mean Score: {aggregate['overall']['mean_score']:.3f}")
    print(f"Score Range: {aggregate['overall']['min_score']:.3f} - {aggregate['overall']['max_score']:.3f}")
    
    # Quality breakdown
    quality = aggregate.get('quality', {})
    with_issues = quality.get('with_issues', 0)
    total = aggregate.get('total_judgments', 0)
    print(f"Quality Issues: {with_issues}/{total} ({with_issues/total*100:.1f}%)")
    
    print(f"\nBy Type:")
    for j_type, stats in aggregate['by_type'].items():
        print(f"  {j_type}: {stats['mean']:.3f} (n={stats['count']}, std={stats['std']:.3f})")
    
    # Metadata insights
    print(f"\nMetadata Insights:")
    metadata = aggregate.get('metadata_summary', {})
    if 'query_type' in metadata:
        print(f"  Query types tested: {metadata['query_type']['unique_values']}")
    if 'evaluation_round' in metadata:
        print(f"  Evaluation rounds: {metadata['evaluation_round']['unique_values']}")
    
    print(f"\nResults saved to: {output_dir}")
    print("=" * 70)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run diverse semantic evaluation")
    parser.add_argument(
        "--content-dir",
        type=Path,
        default=Path(__file__).parent.parent / "content",
        help="Content directory",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("semantic_eval_diverse"),
        help="Output directory",
    )
    
    args = parser.parse_args()
    
    asyncio.run(run_diverse_evaluation(args.content_dir, args.output_dir))

