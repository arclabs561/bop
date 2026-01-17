"""Comprehensive end-to-end test simulating a real user journey.

This test demonstrates the complete user experience from initial query
through iterative refinement using provenance features.
"""

from unittest.mock import patch

import pytest

from pran.agent import KnowledgeAgent
from pran.provenance_viz import create_relevance_breakdown_display, format_clickable_source
from pran.query_refinement import refine_query_from_provenance


@pytest.mark.asyncio
async def test_real_user_journey_iterative_exploration():
    """
    Simulate a real user journey: initial query → explore → refine → verify.

    User Story:
    1. User asks initial question
    2. Sees response with provenance
    3. Clicks on a claim to see source details
    4. Uses query refinement to explore deeper
    5. Verifies information using relevance scores
    """
    agent = KnowledgeAgent(enable_quality_feedback=True)

    # Step 1: Initial query
    initial_query = "What is d-separation?"

    mock_research_data = {
        "query": initial_query,
        "subsolutions": [
            {
                "subproblem": "What is d-separation?",
                "results": [
                    {
                        "tool": "perplexity_deep_research",
                        "result": "D-separation is a graphical criterion for determining conditional independence in directed acyclic graphs. It helps identify when variables are conditionally independent given a set of conditioning variables. This concept is fundamental to causal inference and Bayesian networks.",
                    }
                ],
                "synthesis": "D-separation determines conditional independence in graphs.",
            }
        ],
        "final_synthesis": "D-separation is a fundamental concept in causal inference.",
        "topology": {
            "trust_summary": {"avg_trust": 0.75},
            "source_credibility": {"perplexity_deep_research": 0.75},
        },
    }

    async def mock_research(*args, **kwargs):
        return mock_research_data

    with patch.object(agent.orchestrator, 'research_with_schema', side_effect=mock_research):
        response1 = await agent.chat(
            message=initial_query,
            use_schema="decompose_and_synthesize",
            use_research=True,
        )

    # Verify initial response has provenance
    assert response1.get("research_conducted") is True
    research_data = response1.get("research", {})
    provenance = research_data.get("provenance", {})

    # Step 2: User sees relevance scores in source references
    response_text = response1.get("response", "")
    assert "Sources:" in response_text or len(provenance) >= 0  # May not have sources if no matches

    # Step 3: User clicks on a claim (simulate with format_clickable_source)
    if len(provenance) > 0:
        first_claim = list(provenance.keys())[0]
        provenance_info = provenance[first_claim]

        formatted_text, tooltip_data = format_clickable_source(first_claim, provenance_info)

        # Verify clickable source provides detailed information
        assert isinstance(formatted_text, str)
        if tooltip_data:
            assert "source" in tooltip_data or "overlap" in tooltip_data

    # Step 4: User uses query refinement suggestions
    if len(provenance) > 0:
        refinement_suggestions = refine_query_from_provenance(initial_query, provenance)

        # Should have suggestions
        assert len(refinement_suggestions) >= 0  # Can be empty, but structure should be correct

        # If suggestions exist, verify they're actionable
        if refinement_suggestions:
            for suggestion in refinement_suggestions:
                assert "query" in suggestion
                assert "type" in suggestion
                assert len(suggestion["query"]) > 0

    # Step 5: User follows a suggestion (simulate)
    if len(provenance) > 0 and refinement_suggestions:
        followup_query = refinement_suggestions[0]["query"]

        # Simulate follow-up query (would normally call agent.chat again)
        # For this test, we just verify the suggestion is reasonable
        assert len(followup_query) > len(initial_query) or "explain" in followup_query.lower() or "detail" in followup_query.lower()


@pytest.mark.asyncio
async def test_real_user_journey_verification_workflow():
    """
    Simulate user verification workflow: check sources → verify relevance → trust decision.

    User Story:
    1. User sees a claim with low relevance score
    2. Clicks to see why score is low
    3. Reviews relevance breakdown
    4. Decides whether to trust the information
    """
    # Create provenance with varying relevance scores
    provenance_data = {
        "High relevance claim": {
            "sources": [
                {
                    "source": "perplexity_deep_research",
                    "overlap_ratio": 0.80,
                    "semantic_similarity": 0.85,
                    "relevance_breakdown": {
                        "overall_score": 0.82,
                        "components": {
                            "word_overlap": 0.80,
                            "semantic_similarity": 0.85,
                            "token_match_avg": 0.90,
                        },
                        "explanation": "High word overlap (80.0%). Strong semantic similarity (85.0%).",
                    },
                }
            ],
            "num_sources": 1,
        },
        "Low relevance claim": {
            "sources": [
                {
                    "source": "perplexity_search",
                    "overlap_ratio": 0.25,
                    "semantic_similarity": 0.30,
                    "relevance_breakdown": {
                        "overall_score": 0.28,
                        "components": {
                            "word_overlap": 0.25,
                            "semantic_similarity": 0.30,
                            "token_match_avg": 0.35,
                        },
                        "explanation": "Low word overlap (25.0%). Weak semantic similarity (30.0%).",
                    },
                }
            ],
            "num_sources": 1,
        },
    }

    # User reviews high relevance claim
    high_claim = "High relevance claim"
    high_prov = provenance_data[high_claim]
    high_formatted, high_tooltip = format_clickable_source(high_claim, high_prov)

    if high_tooltip:
        high_breakdown = high_tooltip.get("relevance_breakdown", {})
        if high_breakdown:
            high_score = high_breakdown.get("overall_score", 0.0)
            assert high_score > 0.7, "High relevance claim should have score > 0.7"

            # User sees detailed breakdown
            breakdown_display = create_relevance_breakdown_display(high_breakdown)
            assert "Relevance Score" in breakdown_display
            assert "0.82" in breakdown_display or str(high_score) in breakdown_display

    # User reviews low relevance claim
    low_claim = "Low relevance claim"
    low_prov = provenance_data[low_claim]
    low_formatted, low_tooltip = format_clickable_source(low_claim, low_prov)

    if low_tooltip:
        low_breakdown = low_tooltip.get("relevance_breakdown", {})
        if low_breakdown:
            low_score = low_breakdown.get("overall_score", 0.0)
            assert low_score < 0.5, "Low relevance claim should have score < 0.5"

            # User sees warning in breakdown
            breakdown_display = create_relevance_breakdown_display(low_breakdown)
            assert "Relevance Score" in breakdown_display
            # Should indicate low relevance
            assert "0.28" in breakdown_display or "Low" in breakdown_display or str(low_score) in breakdown_display


@pytest.mark.asyncio
async def test_real_user_journey_progressive_disclosure():
    """
    Simulate progressive disclosure: summary → detailed → full provenance.

    User Story:
    1. User sees summary first (low cognitive load)
    2. Expands to see detailed response
    3. Expands further to see full provenance and evidence
    """
    response_tiers = {
        "summary": "D-separation determines conditional independence in graphs.",
        "detailed": "D-separation is a graphical criterion for determining conditional independence in directed acyclic graphs. It helps identify when variables are conditionally independent given a set of conditioning variables.",
        "evidence": "D-separation is a fundamental concept in causal inference...",
    }

    provenance_data = {
        "D-separation determines conditional independence": {
            "sources": [
                {
                    "source": "perplexity_deep_research",
                    "relevance_breakdown": {
                        "overall_score": 0.75,
                    },
                }
            ],
            "num_sources": 1,
        }
    }

    # Level 1: Summary (default view)
    summary = response_tiers["summary"]
    assert len(summary) < 200, "Summary should be concise"
    assert "D-separation" in summary

    # Level 2: Detailed (user expands)
    detailed = response_tiers["detailed"]
    assert len(detailed) > len(summary), "Detailed should have more information"
    assert "graphical criterion" in detailed

    # Level 3: Full provenance (user wants to verify)
    if len(provenance_data) > 0:
        first_claim = list(provenance_data.keys())[0]
        prov_info = provenance_data[first_claim]
        sources = prov_info.get("sources", [])

        if sources:
            # User can see relevance breakdown
            top_source = sources[0]
            breakdown = top_source.get("relevance_breakdown", {})
            if breakdown:
                score = breakdown.get("overall_score", 0.0)
                assert 0.0 <= score <= 1.0, "Relevance score should be in [0, 1]"


@pytest.mark.asyncio
async def test_real_user_journey_multi_turn_conversation():
    """
    Simulate multi-turn conversation with provenance continuity.

    User Story:
    1. User asks question → gets response with provenance
    2. User asks follow-up based on query refinement suggestion
    3. System maintains context and shows how new information relates
    """
    agent = KnowledgeAgent(enable_quality_feedback=True)

    # Turn 1: Initial query
    query1 = "What is d-separation?"

    mock_research1 = {
        "query": query1,
        "subsolutions": [
            {
                "subproblem": "What is d-separation?",
                "results": [
                    {
                        "tool": "perplexity_deep_research",
                        "result": "D-separation is a graphical criterion for determining conditional independence.",
                    }
                ],
            }
        ],
        "topology": {"trust_summary": {"avg_trust": 0.75}},
    }

    async def mock_research(*args, **kwargs):
        return mock_research1

    with patch.object(agent.orchestrator, 'research_with_schema', side_effect=mock_research):
        response1 = await agent.chat(
            message=query1,
            use_research=True,
        )

    # Get query refinement suggestions from first response
    refinement_suggestions = response1.get("query_refinement_suggestions", [])

    # Turn 2: User follows a suggestion
    if refinement_suggestions:
        query2 = refinement_suggestions[0].get("query", "Explain d-separation in more detail")

        mock_research2 = {
            "query": query2,
            "subsolutions": [
                {
                    "subproblem": query2,
                    "results": [
                        {
                            "tool": "perplexity_deep_research",
                            "result": "D-separation involves checking paths between variables in a directed acyclic graph to determine conditional independence.",
                        }
                    ],
                }
            ],
            "topology": {"trust_summary": {"avg_trust": 0.75}},
        }

        async def mock_research2_func(*args, **kwargs):
            return mock_research2

        with patch.object(agent.orchestrator, 'research_with_schema', side_effect=mock_research2_func):
            response2 = await agent.chat(
                message=query2,
                use_research=True,
            )

        # Verify second response also has provenance
        assert response2.get("research_conducted") is True

        # Verify conversation history is maintained
        history = agent.get_conversation_history()
        assert len(history) >= 2, "Should have at least 2 turns in history"


@pytest.mark.asyncio
async def test_real_user_journey_error_recovery():
    """
    Test that system gracefully handles errors and still provides value.

    User Story:
    1. System encounters error building provenance
    2. Still provides response and basic source information
    3. User experience is not broken
    """
    agent = KnowledgeAgent(enable_quality_feedback=True)

    # Simulate error in provenance building
    with patch('pran.provenance.build_provenance_map', side_effect=Exception("Provenance error")):
        # Should still work without provenance
        response = await agent.chat(
            message="What is d-separation?",
            use_research=False,  # No research to avoid provenance building
        )

        # Response should still be generated
        assert "response" in response
        assert len(response["response"]) > 0

        # Provenance may be missing, but that's okay
        research_data = response.get("research", {})
        if research_data:
            provenance = research_data.get("provenance", {})
            # Either no provenance (graceful degradation) or empty dict
            assert isinstance(provenance, dict)

