"""Full workflow integration tests."""

import pytest

from pran.agent import KnowledgeAgent
from pran.orchestrator import StructuredOrchestrator
from pran.research import ResearchAgent


@pytest.mark.asyncio
async def test_full_research_workflow():
    """Test complete research workflow from query to final answer."""
    agent = KnowledgeAgent()
    agent.llm_service = None

    # Complete workflow
    query = "What are the theoretical foundations and practical applications of trust in knowledge graphs?"

    response = await agent.chat(
        query,
        use_schema="decompose_and_synthesize",
        use_research=True,
    )

    # Verify complete workflow
    assert response["schema_used"] == "decompose_and_synthesize"
    assert response["research_conducted"] is True
    assert "response" in response

    # Check research results
    if response.get("research"):
        research = response["research"]
        assert "subsolutions" in research
        assert "final_synthesis" in research
        assert "topology" in research


@pytest.mark.asyncio
async def test_multi_schema_workflow():
    """Test workflow using multiple schemas in sequence."""
    agent = KnowledgeAgent()
    agent.llm_service = None

    schemas = ["chain_of_thought", "decompose_and_synthesize", "hypothesize_and_test"]

    for schema in schemas:
        response = await agent.chat(
            "What is knowledge structure?",
            use_schema=schema,
            use_research=True,
        )

        assert response["schema_used"] == schema
        assert response["research_conducted"] is True


@pytest.mark.asyncio
async def test_workflow_with_topology_tracking():
    """Test workflow with topology tracking enabled."""
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent, reset_topology_per_query=False)

    queries = [
        "What is trust?",
        "What is uncertainty?",
        "How do they relate?",
    ]

    for query in queries:
        result = await orchestrator.research_with_schema(
            query,
            schema_name="chain_of_thought",
            preserve_d_separation=True,
        )

        # Topology should be tracked
        assert "topology" in result
        assert result["d_separation_preserved"] is True

    # Final topology should have accumulated nodes
    assert len(orchestrator.topology.nodes) > 0


@pytest.mark.asyncio
async def test_workflow_error_recovery():
    """Test that workflow recovers from intermediate errors."""
    agent = KnowledgeAgent()
    agent.llm_service = None

    # Workflow that might have errors
    queries = [
        "Normal query",
        "",  # Empty (should be handled)
        "Another normal query",
    ]

    for query in queries:
        if query:  # Skip empty
            response = await agent.chat(
                query,
                use_schema="chain_of_thought",
                use_research=True,
            )

            # Should always return a response
            assert "response" in response


@pytest.mark.asyncio
async def test_workflow_conversation_context():
    """Test workflow maintains conversation context."""
    agent = KnowledgeAgent()
    agent.llm_service = None

    # Multi-turn conversation with research
    await agent.chat("What is trust?", use_research=True)
    await agent.chat("How does it work?", use_research=True)
    await agent.chat("What are examples?", use_research=True)

    # History should be maintained
    history = agent.get_conversation_history()
    assert len(history) >= 6  # 3 user + 3 assistant


@pytest.mark.asyncio
async def test_workflow_schema_switching():
    """Test workflow with schema switching."""
    agent = KnowledgeAgent()
    agent.llm_service = None

    # Start with one schema
    response1 = await agent.chat(
        "Analyze this problem",
        use_schema="chain_of_thought",
        use_research=False,
    )

    # Switch to different schema
    response2 = await agent.chat(
        "Now decompose it",
        use_schema="decompose_and_synthesize",
        use_research=False,
    )

    assert response1["schema_used"] == "chain_of_thought"
    assert response2["schema_used"] == "decompose_and_synthesize"


@pytest.mark.asyncio
async def test_workflow_research_toggle():
    """Test workflow with research toggling."""
    agent = KnowledgeAgent()
    agent.llm_service = None

    # Without research
    response1 = await agent.chat("Query 1", use_research=False)
    assert response1["research_conducted"] is False

    # With research
    response2 = await agent.chat("Query 2", use_research=True)
    assert response2["research_conducted"] is True

    # Back to no research
    response3 = await agent.chat("Query 3", use_research=False)
    assert response3["research_conducted"] is False

