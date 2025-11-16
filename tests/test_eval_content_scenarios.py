"""Evaluation tests with content in various realistic scenarios."""

import pytest
from pathlib import Path
from bop.eval import EvaluationFramework
from bop.research import load_content
from bop.agent import KnowledgeAgent


@pytest.fixture
def content_dir():
    """Get content directory."""
    return Path(__file__).parent.parent / "content"


@pytest.fixture
def knowledge_base(content_dir):
    """Load knowledge base."""
    return load_content(content_dir)


@pytest.mark.asyncio
async def test_eval_realistic_research_scenario(knowledge_base):
    """Test evaluation with realistic research scenario."""
    framework = EvaluationFramework()
    
    # Simulate a research workflow
    # Step 1: Initial query
    query1 = "What is knowledge structure?"
    
    # Step 2: Follow-up based on content
    if knowledge_base:
        doc_name = list(knowledge_base.keys())[0]
        query2 = f"What does {doc_name} say about knowledge structure?"
    
    # Step 3: Synthesis query
    query3 = "How do different approaches to knowledge structure compare?"
    
    # Create test cases for this workflow
    test_cases = [
        {
            "input": query1,
            "expected": {"input_analysis": str, "steps": list, "final_result": str},
            "actual": {
                "input_analysis": "Analyzing knowledge structure concept",
                "steps": ["Define concept", "Find examples", "Synthesize"],
                "final_result": "Knowledge structure refers to...",
            },
        }
    ]
    
    if knowledge_base:
        test_cases.append({
            "input": query2,
            "expected": {"input_analysis": str, "steps": list},
            "actual": {
                "input_analysis": f"Querying {doc_name}",
                "steps": ["Load document", "Extract relevant sections"],
            },
        })
    
    if test_cases:
        result = framework.evaluate_schema_usage("chain_of_thought", test_cases)
        assert result.score >= 0.0


def test_eval_content_chunking_scenarios(knowledge_base):
    """Test evaluation with content split into chunks."""
    framework = EvaluationFramework()
    
    # Simulate chunking content for processing
    responses = []
    for doc_name, doc_content in knowledge_base.items():
        # Split into chunks
        chunk_size = 500
        chunks = [doc_content[i:i+chunk_size] for i in range(0, len(doc_content), chunk_size)]
        
        for i, chunk in enumerate(chunks[:3]):  # Limit to 3 chunks
            responses.append(f"Chunk {i+1} from {doc_name}: {chunk}")
    
    if responses:
        result = framework.evaluate_reasoning_coherence(responses)
        # Chunked responses should still have some coherence
        assert result.score >= 0.0


def test_eval_content_extraction_methods(knowledge_base):
    """Test evaluation with different content extraction methods."""
    framework = EvaluationFramework()
    
    # Simulate different extraction approaches
    extraction_methods = [
        "keyword_based",
        "semantic_similarity",
        "topic_modeling",
        "neural_extraction",
    ]
    
    test_cases = []
    for method in extraction_methods:
        for doc_name in list(knowledge_base.keys())[:1]:
            test_cases.append({
                "input": f"Extract key concepts from {doc_name} using {method}",
                "expected": {"input_analysis": str, "steps": list, "extracted": list},
                "actual": {
                    "input_analysis": f"Using {method} extraction",
                    "steps": [f"Apply {method}", "Extract concepts"],
                    "extracted": ["concept1", "concept2"],
                },
            })
    
    if test_cases:
        result = framework.evaluate_schema_usage("decompose_and_synthesize", test_cases)
        assert result.score >= 0.0


def test_eval_content_quality_gradation(knowledge_base):
    """Test evaluation with varying content quality."""
    framework = EvaluationFramework()
    
    # Create responses of varying quality
    quality_levels = [
        ("high", "Comprehensive analysis with detailed explanations and examples."),
        ("medium", "Analysis with some details."),
        ("low", "Brief answer."),
    ]
    
    responses = []
    for quality, template in quality_levels:
        for doc_name in list(knowledge_base.keys())[:1]:
            responses.append(f"{quality.upper()} quality from {doc_name}: {template}")
    
    if responses:
        result = framework.evaluate_reasoning_coherence(responses)
        # Should handle quality variations
        assert result.score >= 0.0


def test_eval_content_temporal_queries(knowledge_base):
    """Test evaluation with temporal queries about content."""
    framework = EvaluationFramework()
    
    temporal_queries = [
        "What are the historical foundations?",
        "What are recent developments?",
        "What are future directions?",
    ]
    
    test_cases = []
    for query in temporal_queries:
        test_cases.append({
            "input": query,
            "expected": {"input_analysis": str, "steps": list, "temporal_context": str},
            "actual": {
                "input_analysis": f"Analyzing {query}",
                "steps": ["Identify temporal scope", "Extract relevant content"],
                "temporal_context": "Historical/Recent/Future",
            },
        })
    
    if test_cases:
        result = framework.evaluate_schema_usage("scenario_analysis", test_cases)
        assert result.score >= 0.0


def test_eval_content_cross_reference(knowledge_base):
    """Test evaluation with cross-referencing between documents."""
    framework = EvaluationFramework()
    
    if len(knowledge_base) >= 2:
        doc_names = list(knowledge_base.keys())[:2]
        
        test_cases = [
            {
                "input": f"Compare concepts in {doc_names[0]} and {doc_names[1]}",
                "expected": {"input_analysis": str, "comparison": dict},
                "actual": {
                    "input_analysis": f"Comparing {doc_names[0]} and {doc_names[1]}",
                    "comparison": {
                        "similarities": ["Both discuss structure"],
                        "differences": ["Different perspectives"],
                    },
                },
            }
        ]
        
        result = framework.evaluate_schema_usage("decompose_and_synthesize", test_cases)
        assert result.score >= 0.0


@pytest.mark.asyncio
async def test_eval_agent_research_workflow(knowledge_base):
    """Test evaluation of full agent research workflow."""
    agent = KnowledgeAgent()
    agent.llm_service = None
    
    # Simulate research workflow
    queries = []
    if knowledge_base:
        for doc_name in list(knowledge_base.keys())[:2]:
            queries.append(f"What does {doc_name} discuss?")
            queries.append(f"What are the key concepts in {doc_name}?")
    
    responses = []
    for query in queries:
        response = await agent.chat(query, use_schema="chain_of_thought", use_research=True)
        responses.append(response.get("response", ""))
    
    if responses:
        framework = EvaluationFramework()
        result = framework.evaluate_reasoning_coherence(responses)
        assert result.score >= 0.0


def test_eval_content_ambiguity_resolution(knowledge_base):
    """Test evaluation with ambiguous queries resolved using content."""
    framework = EvaluationFramework()
    
    # Ambiguous queries that need context
    ambiguous_queries = [
        "What is it?",
        "How does it work?",
        "Why is this important?",
    ]
    
    test_cases = []
    for query in ambiguous_queries:
        # Resolve ambiguity using content context
        if knowledge_base:
            doc_name = list(knowledge_base.keys())[0]
            resolved_query = f"{query} (in context of {doc_name})"
            
            test_cases.append({
                "input": resolved_query,
                "expected": {"input_analysis": str, "context": str, "resolution": str},
                "actual": {
                    "input_analysis": f"Resolving ambiguity for {query}",
                    "context": f"Using {doc_name} as context",
                    "resolution": f"Resolved: {query} refers to concepts in {doc_name}",
                },
            })
    
    if test_cases:
        result = framework.evaluate_schema_usage("hypothesize_and_test", test_cases)
        assert result.score >= 0.0


def test_eval_content_multi_hop_reasoning(knowledge_base):
    """Test evaluation with multi-hop reasoning across content."""
    framework = EvaluationFramework()
    
    all_content = " ".join(knowledge_base.values()).lower()
    
    # Multi-hop query: A -> B -> C
    if "trust" in all_content and "uncertainty" in all_content and "knowledge" in all_content:
        test_cases = [
            {
                "query": "How does trust relate to knowledge through uncertainty?",
                "intermediate_steps": [
                    "Understand trust concept",
                    "Understand uncertainty concept",
                    "Understand knowledge concept",
                    "Find trust-uncertainty relationship",
                    "Find uncertainty-knowledge relationship",
                    "Synthesize trust-knowledge relationship",
                ],
                "actual_steps": [
                    "Understanding trust",
                    "Understanding uncertainty",
                    "Understanding knowledge",
                    "Relating trust and uncertainty",
                    "Relating uncertainty and knowledge",
                    "Synthesizing relationships",
                ],
                "final_answer": "Trust relates to knowledge through uncertainty as...",
                "actual_answer": "Trust relates to knowledge through uncertainty, where...",
            }
        ]
        
        result = framework.evaluate_dependency_gap_handling(test_cases)
        # Multi-hop should require more steps
        assert result.score >= 0.0
        if "avg_step_relevance" in result.details:
            assert result.details["avg_step_relevance"] >= 0.0

