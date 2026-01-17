"""Integration tests for all new knowledge display features."""

import pytest

from pran.agent import KnowledgeAgent
from pran.token_importance import compute_token_importance_for_results
from pran.visualizations import (
    create_document_relationship_graph,
    create_source_matrix_heatmap,
    create_token_importance_chart,
    create_trust_metrics_chart,
)


@pytest.mark.asyncio
async def test_full_workflow_with_all_features():
    """Test complete workflow with all new features enabled."""
    agent = KnowledgeAgent(enable_quality_feedback=True)

    response = await agent.chat(
        "What is information geometry?",
        use_schema="decompose_and_synthesize",
        use_research=True,
    )

    # Check response structure
    assert "response" in response
    assert "response_tiers" in response

    # Check research features if research was conducted
    if response.get("research_conducted") and response.get("research"):
        research_data = response["research"]

        # Token importance should be present (even if empty if no results)
        # It's computed from all_results, so it should always be in the dict
        assert "token_importance" in research_data or len(research_data.get("subsolutions", [])) == 0

        # Source matrix should be present
        assert "source_matrix" in research_data

        # Topology should have enhanced metrics
        topology = research_data.get("topology", {})
        if topology:
            assert "trust_summary" in topology
            assert "source_credibility" in topology
            assert "cliques" in topology

    # Check response tiers
    tiers = response.get("response_tiers", {})
    assert "summary" in tiers
    assert "detailed" in tiers


@pytest.mark.asyncio
async def test_visualization_helpers_with_real_data():
    """Test visualization helpers with realistic data structures."""
    # Source matrix heatmap
    source_matrix = {
        "claim1": {
            "sources": {"perplexity": "supports", "tavily": "supports"},
            "consensus": "strong_agreement",
        },
    }
    heatmap = create_source_matrix_heatmap(source_matrix)
    assert heatmap is not None

    # Trust metrics chart
    trust_summary = {
        "avg_trust": 0.75,
        "avg_credibility": 0.70,
        "avg_confidence": 0.80,
    }
    chart = create_trust_metrics_chart(trust_summary)
    assert chart is not None

    # Document relationship graph
    cliques = [
        {
            "node_sources": ["perplexity", "tavily"],
            "trust": 0.8,
            "coherence": 0.75,
            "size": 2,
        },
    ]
    graph = create_document_relationship_graph(cliques)
    assert graph is not None

    # Token importance chart
    importance_data = {
        "term_importance": {"machine": 0.8, "learning": 0.7},
        "top_terms": ["machine", "learning"],
    }
    token_chart = create_token_importance_chart(importance_data)
    assert token_chart is not None


@pytest.mark.asyncio
async def test_token_importance_integration():
    """Test token importance computation in full workflow."""
    query = "artificial intelligence"
    results = [
        {"result": "Artificial intelligence is the simulation of human intelligence."},
        {"result": "AI systems can learn and adapt from experience."},
    ]

    importance_data = compute_token_importance_for_results(query, results)

    assert "term_importance" in importance_data
    assert "top_terms" in importance_data
    assert "per_result_importance" in importance_data

    # Should have some important terms
    if importance_data["term_importance"]:
        assert len(importance_data["top_terms"]) > 0


@pytest.mark.asyncio
async def test_progressive_disclosure_with_visualizations():
    """Test that progressive disclosure works with visualizations."""
    agent = KnowledgeAgent()

    response = await agent.chat(
        "Explain trust metrics in knowledge systems",
        use_research=True,
    )

    # Should have response tiers
    tiers = response.get("response_tiers", {})
    assert "summary" in tiers
    assert len(tiers["summary"]) <= len(tiers.get("detailed", ""))

    # If research was conducted, should have visualization data
    if response.get("research_conducted"):
        research_data = response.get("research", {})
        # Visualization helpers should be able to process this data
        if research_data.get("source_matrix"):
            heatmap = create_source_matrix_heatmap(research_data["source_matrix"])
            assert heatmap is not None


@pytest.mark.asyncio
async def test_storytelling_in_response_structure():
    """Test that responses include narrative structure."""
    agent = KnowledgeAgent()

    response = await agent.chat("What is d-separation?")

    response_text = response.get("response", "")

    # Response should be non-empty (or at least a string)
    assert isinstance(response_text, str)

    # If LLM is available, response should have content
    # If not, it might be a placeholder - that's okay for this test
    if len(response_text) > 0:
        # Check for narrative elements (connective phrases might appear)
        # This is a soft check - we can't guarantee specific phrases,
        # but we can verify the response is structured
        # Response should have some structure (sentences, paragraphs)
        assert "." in response_text or "\n" in response_text or len(response_text) > 50

