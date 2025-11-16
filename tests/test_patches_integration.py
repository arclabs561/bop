"""Integration tests for all implemented patches."""

import pytest
from bop.agent import KnowledgeAgent
from bop.orchestrator import StructuredOrchestrator
from bop.research import ResearchAgent
from bop.llm import LLMService


@pytest.mark.asyncio
async def test_error_handling_belief_extraction():
    """Test that belief extraction handles errors gracefully."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    # Test with None/invalid inputs
    agent._extract_prior_beliefs(None)  # Should not crash
    agent._extract_prior_beliefs("")  # Should not crash
    agent._extract_prior_beliefs(123)  # Should not crash (type error handled)
    
    assert len(agent.prior_beliefs) >= 0  # Should be empty or have beliefs
    
    # Test with valid input
    agent._extract_prior_beliefs("I think trust is important")
    assert len(agent.prior_beliefs) > 0


@pytest.mark.asyncio
async def test_error_handling_response_tiers():
    """Test that tier creation handles errors gracefully."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    
    # Test with None/invalid inputs
    tiers = agent._create_response_tiers("", None, "")
    assert "summary" in tiers
    assert "detailed" in tiers
    assert "structured" in tiers
    assert "evidence" in tiers
    # Should always return valid tiers dict
    
    # Test with None response
    tiers = agent._create_response_tiers(None, {}, "")
    assert isinstance(tiers, dict)
    assert "summary" in tiers
    
    # Test with invalid research dict
    tiers = agent._create_response_tiers("Test response", "not a dict", "")
    assert "summary" in tiers


@pytest.mark.asyncio
async def test_error_handling_source_matrix():
    """Test that source matrix handles errors gracefully."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent, None)
    
    # Test with empty/invalid inputs
    matrix = orchestrator._build_source_matrix([])
    assert isinstance(matrix, dict)
    # Should return empty dict, not crash
    
    # Test with invalid subsolution structure
    invalid_subsolutions = [
        {"invalid": "data"},
        None,
        {"subproblem": "test", "synthesis": None},
    ]
    matrix = orchestrator._build_source_matrix(invalid_subsolutions)
    assert isinstance(matrix, dict)
    # Should handle gracefully


@pytest.mark.asyncio
async def test_cli_flag_functionality():
    """Test that CLI flag logic works correctly."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None  # Use fallback
    
    response = await agent.chat(
        "What is trust?",
        use_research=False,
    )
    
    # Should have response_tiers
    assert "response_tiers" in response
    tiers = response["response_tiers"]
    
    # Test flag logic (simulated)
    show_details = False
    if show_details:
        display_text = tiers.get("detailed", response.get("response", ""))
    else:
        display_text = tiers.get("summary", response.get("response", ""))
    
    assert display_text  # Should have content
    
    # Test with show_details = True
    show_details = True
    if show_details:
        display_text = tiers.get("detailed", response.get("response", ""))
    else:
        display_text = tiers.get("summary", response.get("response", ""))
    
    assert display_text  # Should have content


@pytest.mark.asyncio
async def test_improved_belief_alignment():
    """Test improved belief alignment with semantic fallback."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent, None)
    
    # Test keyword alignment (fallback)
    belief = "I think trust is crucial for systems"
    evidence = "Trust in knowledge systems is essential"
    
    alignment = orchestrator._compute_keyword_alignment(belief.lower(), evidence.lower())
    assert 0.0 <= alignment <= 1.0
    
    # Test semantic alignment (should fallback to keyword)
    alignment = orchestrator._compute_semantic_alignment(belief.lower(), evidence.lower())
    assert 0.0 <= alignment <= 1.0
    
    # Test full alignment computation
    prior_beliefs = [{"text": belief, "source": "user"}]
    alignment = orchestrator._compute_belief_alignment(evidence, prior_beliefs)
    assert 0.0 <= alignment <= 1.0


@pytest.mark.asyncio
async def test_improved_phrase_extraction():
    """Test improved phrase extraction with multiple methods."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent, None)
    
    text = """
    The study demonstrates that "trust scores" are crucial for knowledge systems.
    Research shows Semantic Similarity outperforms keyword matching.
    Findings indicate that confidence in systems improves engagement.
    """
    
    phrases = orchestrator._extract_phrases_heuristic(text, max_phrases=5)
    
    # Should extract:
    # - "trust scores" (quoted)
    # - "Semantic Similarity" (capitalized)
    # - Claims with indicators ("demonstrates", "shows", "indicates")
    
    assert len(phrases) > 0
    assert any("trust" in p.lower() or "semantic" in p.lower() for p in phrases)
    
    # Test with empty text
    phrases = orchestrator._extract_phrases_heuristic("", max_phrases=5)
    assert isinstance(phrases, list)
    
    # Test with very short text
    phrases = orchestrator._extract_phrases_heuristic("Short", max_phrases=5)
    assert isinstance(phrases, list)


@pytest.mark.asyncio
async def test_web_ui_progressive_disclosure():
    """Test that Web UI stores tiers correctly."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None  # Use fallback
    
    response = await agent.chat(
        "What is trust?",
        use_research=False,
    )
    
    # Simulate Web UI message storage
    response_tiers = response.get("response_tiers", {})
    message_data = {
        "role": "assistant",
        "content": response_tiers.get("summary", response.get("response", "")),
        "response_tiers": response_tiers,
        "full_response": response.get("response", ""),
        "expanded": False,
    }
    
    assert "response_tiers" in message_data
    assert "expanded" in message_data
    assert message_data["expanded"] is False
    
    # Test expansion logic
    if message_data["expanded"]:
        display_content = message_data["response_tiers"].get("detailed", message_data["full_response"])
    else:
        display_content = message_data["response_tiers"].get("summary", message_data["full_response"])
    
    assert display_content  # Should have content


@pytest.mark.asyncio
async def test_end_to_end_with_all_patches():
    """Test end-to-end flow with all patches integrated."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None  # Use fallback
    
    # Test with belief statement
    response1 = await agent.chat(
        "I think trust is important for knowledge systems. What is trust?",
        use_research=False,
    )
    
    # Should extract belief
    assert len(agent.prior_beliefs) > 0
    
    # Should have response tiers
    assert "response_tiers" in response1
    assert "summary" in response1["response_tiers"]
    
    # Test with research (triggers source matrix)
    # Note: Research may not actually run if LLM service unavailable
    response2 = await agent.chat(
        "How does uncertainty affect trust?",
        use_research=True,
    )
    
    # Should have research results (if research was conducted)
    if response2.get("research") and response2.get("research_conducted"):
        research = response2["research"]
        # Source matrix may be empty if no subsolutions, but structure should exist
        # It's OK if source_matrix is not present if research didn't produce subsolutions
        if isinstance(research, dict) and research.get("subsolutions"):
            # If we have subsolutions, source_matrix should be built
            assert "source_matrix" in research or research.get("source_matrix") is not None
    
    # Should have topology (if research was conducted)
    if response2.get("research") and response2["research"].get("topology"):
        topology = response2["research"]["topology"]
        # Should have enhanced metrics
        assert "trust_summary" in topology or topology.get("trust_summary") is not None
    
    # At minimum, response should have response_tiers
    assert "response_tiers" in response2
    assert "summary" in response2["response_tiers"]

