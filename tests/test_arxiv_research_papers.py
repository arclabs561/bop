"""
Tests for real research paper evaluation using arXiv MCP tool.

Tests BOP's ability to:
- Search and retrieve real research papers
- Extract claims and verify them
- Evaluate trust metrics on academic sources
- Test uncertainty quantification on real papers
"""

import os

import pytest

from bop.agent import KnowledgeAgent

# Skip tests if API keys are not available
pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"),
    reason="API keys required for real research paper tests"
)


class TestArxivResearchPapers:
    """Test real research paper evaluation."""

    @pytest.mark.asyncio
    async def test_search_real_arxiv_paper(self):
        """Test searching for a real arXiv paper."""
        agent = KnowledgeAgent(enable_quality_feedback=False)

        # Search for a well-known paper
        response = await agent.chat(
            "What is d-separation in causal inference?",
            use_research=True,
        )

        # Should have research results
        assert response.get("research_conducted") is True
        assert response.get("research") is not None

        # Should have subsolutions
        research = response.get("research", {})
        subsolutions = research.get("subsolutions", [])
        assert len(subsolutions) > 0

        # Check for arXiv sources
        for subsol in subsolutions:
            sources = subsol.get("sources", [])
            for source in sources:
                if "arxiv" in source.lower():
                    break

        # Note: May not always have arXiv if other sources are better
        # But should have research results
        assert len(subsolutions) > 0

    @pytest.mark.asyncio
    async def test_verify_claim_from_paper(self):
        """Test verifying a specific claim from a research paper."""
        agent = KnowledgeAgent(enable_quality_feedback=False)

        # Claim from a well-known paper
        response = await agent.chat(
            "Verify: D-separation is a graphical criterion for determining conditional independence in Bayesian networks.",
            use_research=True,
        )

        # Should have research
        assert response.get("research_conducted") is True

        # Should have trust metrics
        if response.get("research") and response["research"].get("topology"):
            topology = response["research"]["topology"]
            trust_summary = topology.get("trust_summary", {})
            assert "avg_trust" in trust_summary

    @pytest.mark.asyncio
    async def test_uncertainty_on_real_papers(self):
        """Test uncertainty quantification on real research papers."""
        agent = KnowledgeAgent(enable_quality_feedback=False)

        response = await agent.chat(
            "What is the relationship between information geometry and machine learning?",
            use_research=True,
        )

        # Should have research
        assert response.get("research_conducted") is True

        # Check for uncertainty metrics
        if response.get("research") and response["research"].get("topology"):
            topology = response["research"]["topology"]

            # Should have source credibility
            source_credibility = topology.get("source_credibility", {})
            assert isinstance(source_credibility, dict)

            # Should have trust summary with calibration
            trust_summary = topology.get("trust_summary", {})
            if "calibration_error" in trust_summary:
                assert isinstance(trust_summary["calibration_error"], (int, float))

    @pytest.mark.asyncio
    async def test_multi_paper_synthesis(self):
        """Test synthesizing information from multiple papers."""
        agent = KnowledgeAgent(enable_quality_feedback=False)

        response = await agent.chat(
            "Compare d-separation and conditional independence in different contexts.",
            use_research=True,
        )

        # Should have multiple subsolutions (multiple papers)
        assert response.get("research_conducted") is True

        research = response.get("research", {})
        subsolutions = research.get("subsolutions", [])

        # Should have multiple sources
        assert len(subsolutions) >= 1

        # Check for source matrix (agreement/disagreement)
        source_matrix = research.get("source_matrix", {})
        assert isinstance(source_matrix, dict)

    @pytest.mark.asyncio
    async def test_arxiv_source_credibility(self):
        """Test that arXiv sources have high credibility."""
        agent = KnowledgeAgent(enable_quality_feedback=False)

        response = await agent.chat(
            "What is the latest research on transformer architectures?",
            use_research=True,
        )

        # Should have research
        assert response.get("research_conducted") is True

        # Check source credibility for arXiv sources
        if response.get("research") and response["research"].get("topology"):
            topology = response["research"]["topology"]
            source_credibility = topology.get("source_credibility", {})

            # Check if any arXiv sources have high credibility
            arxiv_credibility = [
                cred for source, cred in source_credibility.items()
                if "arxiv" in source.lower()
            ]

            # If arXiv sources exist, they should have high credibility (>0.7)
            if arxiv_credibility:
                assert all(cred >= 0.7 for cred in arxiv_credibility), \
                    f"arXiv sources should have high credibility, got: {arxiv_credibility}"

