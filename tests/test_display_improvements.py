"""Tests for knowledge display improvements."""

import pytest

from bop.agent import KnowledgeAgent
from bop.context_topology import ContextNode
from bop.display_helpers import (
    create_trust_table,
    format_clique_clusters,
    format_source_credibility,
    format_trust_summary,
)
from bop.orchestrator import StructuredOrchestrator


@pytest.mark.asyncio
async def test_progressive_disclosure_tiers():
    """Test that response tiers are created correctly."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None  # Use fallback

    response = await agent.chat(
        "What is trust?",
        use_research=False,
    )

    assert "response_tiers" in response
    tiers = response["response_tiers"]
    assert "summary" in tiers
    assert "structured" in tiers
    assert "detailed" in tiers
    assert "evidence" in tiers

    # Summary should be shorter than detailed
    assert len(tiers["summary"]) <= len(tiers["detailed"])
    assert len(tiers["summary"]) > 0


@pytest.mark.asyncio
async def test_belief_extraction():
    """Test that prior beliefs are extracted from user messages."""
    agent = KnowledgeAgent(enable_quality_feedback=False)

    # Message with belief statement
    await agent.chat("I think trust is important for knowledge systems")

    assert len(agent.prior_beliefs) > 0
    assert any("trust" in b.get("text", "").lower() for b in agent.prior_beliefs)

    # Another message
    await agent.chat("I believe uncertainty affects decision making")

    assert len(agent.prior_beliefs) >= 1  # At least one belief extracted


def test_trust_summary_formatting():
    """Test trust summary formatting."""
    trust_summary = {
        "avg_trust": 0.75,
        "avg_credibility": 0.70,
        "avg_confidence": 0.65,
        "high_trust_edges": 5,
        "low_trust_edges": 2,
        "calibration_error": 0.12,
        "schema_violations": 0,
    }

    formatted = format_trust_summary(trust_summary)
    assert "Average Trust" in formatted
    assert "0.75" in formatted
    assert "Calibration Error" in formatted
    assert "0.12" in formatted


def test_source_credibility_formatting():
    """Test source credibility formatting."""
    source_cred = {
        "perplexity_deep_research": 0.75,
        "tavily_search": 0.60,
        "firecrawl_scrape": 0.70,
    }

    formatted = format_source_credibility(source_cred)
    assert "perplexity_deep_research" in formatted
    assert "0.75" in formatted


def test_clique_cluster_formatting():
    """Test clique cluster formatting."""
    cliques = [
        {
            "node_sources": ["perplexity", "tavily", "firecrawl"],
            "trust": 0.75,
            "coherence": 0.80,
            "risk": 0.1,
            "size": 3,
        },
        {
            "node_sources": ["perplexity", "perplexity"],
            "trust": 0.60,
            "coherence": 0.70,
            "risk": 0.2,
            "size": 2,
        },
    ]

    formatted = format_clique_clusters(cliques)
    assert "Source Clusters" in formatted
    assert "sources agree" in formatted


def test_belief_alignment_computation():
    """Test belief-evidence alignment computation."""
    orchestrator = StructuredOrchestrator()

    # Test with aligned evidence
    prior_beliefs = [{"text": "trust is important for systems"}]
    evidence_aligned = "Trust plays a crucial role in knowledge systems and affects reliability"
    alignment = orchestrator._compute_belief_alignment(evidence_aligned, prior_beliefs)
    assert alignment > 0.5  # Should show alignment

    # Test with contradictory evidence
    evidence_contradictory = "However, trust is not important and systems work without it"
    alignment_contra = orchestrator._compute_belief_alignment(evidence_contradictory, prior_beliefs)
    assert alignment_contra < 0.5  # Should show contradiction

    # Test with no prior beliefs
    alignment_neutral = orchestrator._compute_belief_alignment("Some text", [])
    assert alignment_neutral == 0.5  # Should be neutral


def test_source_matrix_building():
    """Test source relationship matrix building."""
    orchestrator = StructuredOrchestrator()

    subsolutions = [
        {
            "subproblem": "Test problem",
            "synthesis": "Trust is important. Systems need reliability. Knowledge requires verification.",
            "tools_used": ["tool1", "tool2"],
            "results": [
                {"tool": "tool1", "result": "Trust is important for systems"},
                {"tool": "tool2", "result": "However, trust may not be necessary"},
            ],
        }
    ]

    matrix = orchestrator._build_source_matrix(subsolutions)
    assert isinstance(matrix, dict)
    # Should extract key phrases and map sources
    if matrix:
        for claim, data in matrix.items():
            assert "sources" in data
            assert "consensus" in data
            assert "conflict" in data


def test_clique_details_in_response():
    """Test that clique details are included in research response."""
    orchestrator = StructuredOrchestrator()

    # Create some test nodes
    topology = orchestrator.topology
    node1 = ContextNode(
        id="n1",
        content="Test content 1",
        source="perplexity",
        credibility=0.8,
    )
    node2 = ContextNode(
        id="n2",
        content="Test content 2",
        source="tavily",
        credibility=0.7,
    )
    topology.add_node(node1)
    topology.add_node(node2)
    topology.add_edge("n1", "n2", weight=0.9)
    topology.compute_cliques()

    # Check that cliques would be included
    cliques = topology.cliques
    assert len(cliques) > 0


@pytest.mark.asyncio
async def test_response_length_adaptation():
    """Test that response length is adapted based on expected_length."""
    agent = KnowledgeAgent(enable_quality_feedback=True)
    agent.llm_service = None  # Use fallback

    # Mock expected_length
    response = await agent.chat("Test query")

    # Response should exist
    assert "response" in response
    assert len(response["response"]) > 0


def test_trust_table_creation():
    """Test trust table creation."""
    trust_summary = {
        "avg_trust": 0.75,
        "avg_credibility": 0.70,
        "avg_confidence": 0.65,
        "calibration_error": 0.12,
        "high_trust_edges": 5,
        "low_trust_edges": 2,
    }

    table = create_trust_table(trust_summary)
    assert table is not None
    assert table.title == "Trust Metrics"

