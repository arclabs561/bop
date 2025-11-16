"""Comprehensive evaluation tests using structured datasets."""

import pytest
from pathlib import Path
from bop.agent import KnowledgeAgent
from bop.semantic_eval import SemanticEvaluator
from datasets import load_all_datasets, get_dataset_by_domain


@pytest.fixture
def datasets_dir():
    """Get datasets directory."""
    return Path(__file__).parent.parent / "datasets"


@pytest.fixture
def all_datasets(datasets_dir):
    """Load all datasets."""
    return load_all_datasets(datasets_dir)


@pytest.fixture
def evaluator(tmp_path):
    """Create semantic evaluator."""
    return SemanticEvaluator(output_dir=tmp_path / "eval_outputs")


@pytest.mark.asyncio
async def test_evaluate_science_dataset(datasets_dir, evaluator):
    """Evaluate agent on science queries dataset."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None
    
    science_queries = get_dataset_by_domain(datasets_dir, "science")
    
    for query_item in science_queries[:5]:  # Evaluate 5 queries
        query = query_item["query"]
        if not query or len(query) < 10:
            continue
        
        response_obj = await agent.chat(
            query,
            use_research=query_item.get("requires_research", True)
        )
        response = response_obj.get("response", "")
        
        # Evaluate relevance
        evaluator.evaluate_relevance(
            query=query,
            response=response,
            metadata={
                "domain": query_item.get("domain"),
                "complexity": query_item.get("complexity"),
                "query_type": query_item.get("query_type"),
                "expected_concepts": query_item.get("expected_concepts", []),
            }
        )
    
    # Save results
    json_path = evaluator.save_judgments_json("science_evaluation.json")
    assert json_path.exists()
    
    # Check aggregation
    aggregate = evaluator.aggregate_judgments()
    assert aggregate["total_judgments"] > 0


@pytest.mark.asyncio
async def test_evaluate_philosophy_dataset(datasets_dir, evaluator):
    """Evaluate agent on philosophy queries dataset."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None
    
    philosophy_queries = get_dataset_by_domain(datasets_dir, "philosophy")
    
    for query_item in philosophy_queries[:5]:
        query = query_item["query"]
        if not query or len(query) < 10:
            continue
        
        response_obj = await agent.chat(
            query,
            use_research=query_item.get("requires_research", True)
        )
        response = response_obj.get("response", "")
        
        # Evaluate completeness (needs content_context)
        evaluator.evaluate_completeness(
            query=query,
            response=response,
            content_context=response,  # Use response as context for this test
            metadata={
                "domain": query_item.get("domain"),
                "complexity": query_item.get("complexity"),
                "expected_concepts": query_item.get("expected_concepts", []),
            }
        )
    
    aggregate = evaluator.aggregate_judgments()
    assert aggregate["total_judgments"] > 0


@pytest.mark.asyncio
async def test_evaluate_temporal_dataset(datasets_dir, evaluator):
    """Evaluate agent on temporal queries dataset."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None
    
    temporal_queries = get_dataset_by_domain(datasets_dir, "temporal")
    
    for query_item in temporal_queries[:5]:
        query = query_item["query"]
        if not query or len(query) < 10:
            continue
        
        response_obj = await agent.chat(
            query,
            use_research=query_item.get("requires_research", True)
        )
        response = response_obj.get("response", "")
        
        # Check temporal features
        assert response_obj.get("timestamp") is not None
        
        # Evaluate with temporal context
        evaluator.evaluate_relevance(
            query=query,
            response=response,
            metadata={
                "temporal_aspect": query_item.get("temporal_aspect", False),
                "query_type": query_item.get("query_type"),
                "expected_concepts": query_item.get("expected_concepts", []),
            }
        )
    
    aggregate = evaluator.aggregate_judgments()
    assert aggregate["total_judgments"] > 0


@pytest.mark.asyncio
async def test_evaluate_technical_dataset(datasets_dir, evaluator):
    """Evaluate agent on technical queries dataset."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None
    
    technical_queries = get_dataset_by_domain(datasets_dir, "technical")
    
    for query_item in technical_queries[:5]:
        query = query_item["query"]
        if not query or len(query) < 10:
            continue
        
        response_obj = await agent.chat(
            query,
            use_research=query_item.get("requires_research", True)
        )
        response = response_obj.get("response", "")
        
        # Evaluate accuracy for technical queries
        evaluator.evaluate_accuracy(
            query=query,
            response=response,
            expected_concepts=query_item.get("expected_concepts", []),
            metadata={
                "domain": query_item.get("domain"),
                "query_type": query_item.get("query_type"),
            }
        )
    
    aggregate = evaluator.aggregate_judgments()
    assert aggregate["total_judgments"] > 0


@pytest.mark.asyncio
async def test_evaluate_edge_cases_dataset(datasets_dir, evaluator):
    """Evaluate agent on edge case queries."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None
    
    from datasets import load_dataset
    edge_cases = load_dataset(datasets_dir / "edge_cases.json")
    
    # Test normal query first (baseline)
    normal_query = next(
        item for item in edge_cases
        if item.get("subdomain") == "normal_query"
    )
    
    response_obj = await agent.chat(normal_query["query"], use_research=False)
    response = response_obj.get("response", "")
    
    evaluator.evaluate_relevance(
        query=normal_query["query"],
        response=response,
        metadata={
            "edge_case_type": "normal",
            "expected_concepts": normal_query.get("expected_concepts", []),
        }
    )
    
    # Test other edge cases (skip empty/minimal)
    for query_item in edge_cases:
        if query_item.get("subdomain") in ["empty_query", "minimal_query"]:
            continue
        
        query = query_item["query"]
        if not query or len(query) < 3:
            continue
        
        try:
            response_obj = await agent.chat(query, use_research=False)
            response = response_obj.get("response", "")
            
            evaluator.evaluate_relevance(
                query=query,
                response=response,
                metadata={
                    "edge_case_type": query_item.get("subdomain"),
                    "expected_concepts": query_item.get("expected_concepts", []),
                }
            )
        except Exception:
            # Edge cases may fail, which is acceptable
            pass
    
    aggregate = evaluator.aggregate_judgments()
    assert aggregate["total_judgments"] > 0


@pytest.mark.asyncio
async def test_cross_dataset_comparison(all_datasets, evaluator):
    """Compare agent performance across different dataset domains."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None
    
    domain_results = {}
    
    for dataset_name, items in all_datasets.items():
        domain = items[0].get("domain") if items else "unknown"
        domain_results[domain] = {"total": 0, "evaluated": 0}
        
        for query_item in items[:3]:  # 3 queries per dataset
            query = query_item["query"]
            if not query or len(query) < 10:
                continue
            
            domain_results[domain]["total"] += 1
            
            try:
                response_obj = await agent.chat(
                    query,
                    use_research=query_item.get("requires_research", False)
                )
                response = response_obj.get("response", "")
                
                evaluator.evaluate_relevance(
                    query=query,
                    response=response,
                    metadata={
                        "domain": domain,
                        "dataset": dataset_name,
                        "expected_concepts": query_item.get("expected_concepts", []),
                    }
                )
                
                domain_results[domain]["evaluated"] += 1
            except Exception:
                pass
    
    # All domains should have some evaluations
    for domain, results in domain_results.items():
        if results["total"] > 0:
            assert results["evaluated"] > 0, f"No evaluations for domain {domain}"


@pytest.mark.asyncio
async def test_dataset_complexity_analysis(all_datasets, evaluator):
    """Analyze agent performance by query complexity."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None
    
    complexity_results = {"simple": 0, "moderate": 0, "complex": 0}
    
    for dataset_name, items in all_datasets.items():
        for query_item in items[:2]:  # 2 queries per dataset
            query = query_item["query"]
            if not query or len(query) < 10:
                continue
            
            complexity = query_item.get("complexity", "moderate")
            
            try:
                response_obj = await agent.chat(
                    query,
                    use_research=query_item.get("requires_research", False)
                )
                response = response_obj.get("response", "")
                
                evaluator.evaluate_relevance(
                    query=query,
                    response=response,
                    metadata={
                        "complexity": complexity,
                        "expected_concepts": query_item.get("expected_concepts", []),
                    }
                )
                
                complexity_results[complexity] += 1
            except Exception:
                pass
    
    # Should have evaluated queries of different complexities
    total_evaluated = sum(complexity_results.values())
    assert total_evaluated > 0

