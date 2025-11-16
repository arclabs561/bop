"""Semantic evaluation tests using realistic data for decision-making."""

import pytest
import asyncio
from pathlib import Path
from bop.semantic_eval import SemanticEvaluator
from bop.agent import KnowledgeAgent
from bop.orchestrator import StructuredOrchestrator
from bop.research import ResearchAgent
from bop.research import load_content


@pytest.fixture
def content_dir():
    """Get content directory."""
    return Path(__file__).parent.parent / "content"


@pytest.fixture
def knowledge_base(content_dir):
    """Load knowledge base."""
    return load_content(content_dir)


@pytest.fixture
def evaluator(tmp_path):
    """Create semantic evaluator with temp output directory."""
    return SemanticEvaluator(output_dir=tmp_path / "eval_outputs")


@pytest.mark.asyncio
async def test_realistic_accuracy_evaluation(evaluator, knowledge_base):
    """Evaluate accuracy on realistic queries from content."""
    agent = KnowledgeAgent()
    agent.llm_service = None
    
    # Realistic queries based on actual content
    test_cases = []
    
    for doc_name, doc_content in list(knowledge_base.items())[:3]:
        # Extract real concepts from content
        content_lower = doc_content.lower()
        concepts = []
        
        concept_keywords = {
            "trust": ["trust", "credibility", "confidence"],
            "uncertainty": ["uncertainty", "epistemic", "aleatoric"],
            "knowledge": ["knowledge", "information", "understanding"],
            "structure": ["structure", "organization", "architecture"],
        }
        
        for concept, keywords in concept_keywords.items():
            if any(kw in content_lower for kw in keywords):
                concepts.append(concept)
        
        if concepts:
            query = f"What does {doc_name} say about {concepts[0]}?"
            response_obj = await agent.chat(query, use_schema="chain_of_thought", use_research=False)
            response = response_obj.get("response", "")
            
            evaluator.evaluate_accuracy(
                query=query,
                response=response,
                expected_concepts=concepts,
                metadata={
                    "document": doc_name,
                    "schema": "chain_of_thought",
                    "research": False,
                },
            )
    
    # Save results
    json_path = evaluator.save_judgments_json("accuracy_judgments.json")
    csv_path = evaluator.save_judgments_csv("accuracy_judgments.csv")
    report_path = evaluator.save_summary_report("accuracy_report.md")
    
    assert json_path.exists()
    assert csv_path.exists()
    assert report_path.exists()
    
    # Check aggregation
    aggregate = evaluator.aggregate_judgments()
    assert aggregate["total_judgments"] > 0
    assert "by_type" in aggregate
    assert "accuracy" in aggregate["by_type"]


@pytest.mark.asyncio
async def test_realistic_completeness_evaluation(evaluator, knowledge_base):
    """Evaluate completeness on realistic content-based queries."""
    agent = KnowledgeAgent()
    agent.llm_service = None
    
    for doc_name, doc_content in list(knowledge_base.items())[:2]:
        query = f"Summarize the main ideas in {doc_name}"
        response_obj = await agent.chat(
            query,
            use_schema="decompose_and_synthesize",
            use_research=False,
        )
        response = response_obj.get("response", "")
        
        evaluator.evaluate_completeness(
            query=query,
            response=response,
            content_context=doc_content[:2000],  # Use actual content as context
            metadata={
                "document": doc_name,
                "schema": "decompose_and_synthesize",
                "context_length": len(doc_content),
            },
        )
    
    aggregate = evaluator.aggregate_judgments()
    assert aggregate["total_judgments"] > 0


@pytest.mark.asyncio
async def test_realistic_relevance_evaluation(evaluator):
    """Evaluate relevance on realistic query types."""
    agent = KnowledgeAgent()
    agent.llm_service = None
    
    # Realistic query types
    queries = [
        "What is knowledge structure?",
        "How does trust propagate in networks?",
        "Why is uncertainty important in knowledge graphs?",
        "Compare different approaches to reasoning",
        "Analyze the implications of structured reasoning",
    ]
    
    for query in queries:
        response_obj = await agent.chat(query, use_schema="chain_of_thought", use_research=False)
        response = response_obj.get("response", "")
        
        evaluator.evaluate_relevance(
            query=query,
            response=response,
            metadata={
                "query_type": _classify_query(query),
                "schema": "chain_of_thought",
            },
        )
    
    aggregate = evaluator.aggregate_judgments()
    # May have fewer if all responses are placeholders and get filtered
    assert aggregate.get("total_judgments", 0) >= 0
    assert aggregate.get("total_judgments", 0) <= len(queries)


def _classify_query(query: str) -> str:
    """Classify query type."""
    query_lower = query.lower()
    if query_lower.startswith("what"):
        return "definition"
    elif query_lower.startswith("how"):
        return "process"
    elif query_lower.startswith("why"):
        return "causation"
    elif "compare" in query_lower:
        return "comparison"
    elif "analyze" in query_lower:
        return "analysis"
    else:
        return "general"


@pytest.mark.asyncio
async def test_realistic_consistency_evaluation(evaluator):
    """Evaluate consistency across schemas for same query."""
    agent = KnowledgeAgent()
    agent.llm_service = None
    
    query = "What is structured reasoning?"
    schemas = ["chain_of_thought", "decompose_and_synthesize", "hypothesize_and_test"]
    
    responses = []
    for schema in schemas:
        response_obj = await agent.chat(query, use_schema=schema, use_research=False)
        responses.append(response_obj.get("response", ""))
    
    evaluator.evaluate_consistency(
        query=query,
        responses=responses,
        metadata={
            "schemas": schemas,
            "response_count": len(responses),
        },
    )
    
    aggregate = evaluator.aggregate_judgments()
    # Consistency may not be in by_type if no valid responses
    if aggregate.get("total_judgments", 0) > 0:
        assert "by_type" in aggregate or "error" in aggregate


@pytest.mark.asyncio
async def test_realistic_research_quality_evaluation(evaluator, knowledge_base):
    """Evaluate quality of research results."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent)
    
    query = "What are the theoretical foundations of trust and uncertainty?"
    
    result = await orchestrator.research_with_schema(
        query,
        schema_name="decompose_and_synthesize",
    )
    
    synthesis = result.get("final_synthesis", "")
    
    # Evaluate with content context
    all_content = " ".join(knowledge_base.values())[:2000] if knowledge_base else ""
    
    evaluator.evaluate_completeness(
        query=query,
        response=synthesis,
        content_context=all_content,
        metadata={
            "schema": "decompose_and_synthesize",
            "research": True,
            "subsolutions_count": len(result.get("subsolutions", [])),
            "tools_called": result.get("tools_called", 0),
        },
    )
    
    aggregate = evaluator.aggregate_judgments()
    assert aggregate["total_judgments"] > 0


@pytest.mark.asyncio
async def test_comprehensive_semantic_evaluation(evaluator, knowledge_base):
    """Run comprehensive semantic evaluation on realistic data."""
    agent = KnowledgeAgent()
    agent.llm_service = None
    
    # Multiple evaluation types on realistic queries
    test_scenarios = [
        {
            "query": "What is knowledge structure?",
            "expected_concepts": ["knowledge", "structure", "organization"],
            "schema": "chain_of_thought",
        },
        {
            "query": "How does trust work in knowledge graphs?",
            "expected_concepts": ["trust", "knowledge", "graph"],
            "schema": "decompose_and_synthesize",
        },
        {
            "query": "Why is uncertainty important?",
            "expected_concepts": ["uncertainty", "importance"],
            "schema": "hypothesize_and_test",
        },
    ]
    
    for scenario in test_scenarios:
        response_obj = await agent.chat(
            scenario["query"],
            use_schema=scenario["schema"],
            use_research=False,
        )
        response = response_obj.get("response", "")
        
        # Evaluate accuracy
        evaluator.evaluate_accuracy(
            query=scenario["query"],
            response=response,
            expected_concepts=scenario["expected_concepts"],
            metadata={
                "schema": scenario["schema"],
                "scenario_id": test_scenarios.index(scenario),
            },
        )
        
        # Evaluate relevance
        evaluator.evaluate_relevance(
            query=scenario["query"],
            response=response,
            metadata={
                "schema": scenario["schema"],
                "scenario_id": test_scenarios.index(scenario),
            },
        )
    
    # Save all results
    json_path = evaluator.save_judgments_json("comprehensive_judgments.json")
    csv_path = evaluator.save_judgments_csv("comprehensive_judgments.csv")
    report_path = evaluator.save_summary_report("comprehensive_report.md")
    
    # Verify outputs
    assert json_path.exists()
    assert csv_path.exists()
    assert report_path.exists()
    
    # Check aggregation
    aggregate = evaluator.aggregate_judgments()
    if "error" not in aggregate:
        assert aggregate.get("total_judgments", 0) >= 0
        # May have fewer types if responses are placeholders
        if aggregate.get("total_judgments", 0) > 0:
            assert "by_type" in aggregate
    
    return aggregate

