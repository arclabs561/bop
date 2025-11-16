#!/usr/bin/env python3
"""Test script to experience the system firsthand."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bop.agent import KnowledgeAgent
from bop.context_topology import ContextTopology, ContextNode
from bop.orchestrator import StructuredOrchestrator, ToolType
from bop.schemas import get_schema


async def test_basic_topology():
    """Test topology features."""
    print("\n=== Testing Topology ===")
    topology = ContextTopology()
    
    # Add some nodes
    node1 = ContextNode(
        id="n1",
        content="Trust and uncertainty in knowledge graphs",
        source="arxiv",
        credibility=0.8,
        confidence=0.7,
    )
    node2 = ContextNode(
        id="n2",
        content="Conformal prediction for uncertainty quantification",
        source="arxiv",
        credibility=0.9,
        confidence=0.8,
    )
    node3 = ContextNode(
        id="n3",
        content="Low-trust claim",
        source="unknown",
        credibility=0.2,
        confidence=0.3,
    )
    
    topology.add_node(node1)
    topology.add_node(node2)
    topology.add_node(node3)
    
    # Connect high-trust nodes
    topology.add_edge("n1", "n2")
    
    # Check schema
    violations = topology.check_schema_consistency(node1)
    print(f"Schema violations: {len(violations)}")
    
    # Update confidence
    topology.update_confidence_from_evidence("n1", new_evidence=True, evidence_quality=0.8)
    print(f"Node1 confidence after evidence: {topology.nodes['n1'].confidence}")
    
    # Compute cliques
    cliques = topology.compute_cliques()
    print(f"Found {len(cliques)} cliques")
    
    # Get attractor basins
    basins = topology.get_attractor_basins(min_trust=0.6)
    print(f"High-trust basins: {len(basins)}")
    
    # Get trust summary
    summary = topology._get_trust_summary()
    print(f"Trust summary: {summary}")
    
    return topology


async def test_orchestrator():
    """Test orchestrator with a real query."""
    print("\n=== Testing Orchestrator ===")
    
    from bop.research import ResearchAgent
    
    research_agent = ResearchAgent()
    orchestrator = StructuredOrchestrator(research_agent)
    
    # Get a schema
    schema = get_schema("chain_of_thought")
    if not schema:
        print("No schema found, skipping")
        return
    
    # Test query
    query = "What are the latest approaches to trust and uncertainty in knowledge graphs?"
    
    print(f"Query: {query}")
    print("Running research_with_schema...")
    
    try:
        result = await orchestrator.research_with_schema(
            query,
            schema_name="chain_of_thought",
        )
        
        print(f"\nResult keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        
        if isinstance(result, dict):
            if "subsolutions" in result:
                print(f"Subsolutions: {len(result['subsolutions'])}")
            if "final_synthesis" in result:
                print(f"Final synthesis length: {len(str(result['final_synthesis']))}")
            if "topology_metrics" in result:
                print(f"Topology metrics: {result['topology_metrics']}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


async def test_agent_chat():
    """Test the full agent chat interface."""
    print("\n=== Testing Agent Chat ===")
    
    agent = KnowledgeAgent()
    
    # Simple query
    query = "What is structured reasoning?"
    print(f"Query: {query}")
    
    try:
        response = await agent.chat(query, use_schema=None, use_research=False)
        print(f"\nResponse type: {type(response)}")
        print(f"Response keys: {response.keys() if isinstance(response, dict) else 'Not a dict'}")
        if isinstance(response, dict):
            print(f"Response text: {response.get('response', 'No response')[:200]}...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


async def test_agent_with_research():
    """Test agent with research enabled."""
    print("\n=== Testing Agent with Research ===")
    
    agent = KnowledgeAgent()
    
    query = "What are recent developments in knowledge graph reasoning?"
    print(f"Query: {query}")
    
    try:
        response = await agent.chat(query, use_schema="chain_of_thought", use_research=True)
        print(f"\nResearch conducted: {response.get('research_conducted', False)}")
        if response.get('research_error'):
            print(f"Research error: {response['research_error']}")
        if response.get('research'):
            print(f"Research result type: {type(response['research'])}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


async def test_topology_impact():
    """Test topology impact analysis."""
    print("\n=== Testing Topology Impact ===")
    
    topology = ContextTopology()
    
    # Add initial nodes
    for i in range(3):
        node = ContextNode(
            id=f"initial_{i}",
            content=f"Initial knowledge {i}",
            source="test",
            credibility=0.7,
        )
        topology.add_node(node)
        if i > 0:
            topology.add_edge(f"initial_{i-1}", f"initial_{i}")
    
    # Add new nodes
    new_nodes = [
        ContextNode(
            id="new_1",
            content="New knowledge that connects",
            source="test",
            credibility=0.8,
            dependencies={"initial_1"},
        ),
        ContextNode(
            id="new_2",
            content="Isolated new knowledge",
            source="test",
            credibility=0.6,
        ),
    ]
    
    impact = topology.analyze_context_injection_impact(new_nodes)
    print(f"Impact: {impact}")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("EXPERIENCING THE SYSTEM")
    print("=" * 60)
    
    # Test 1: Basic topology
    await test_basic_topology()
    
    # Test 2: Topology impact
    await test_topology_impact()
    
    # Test 3: Orchestrator
    await test_orchestrator()
    
    # Test 4: Agent chat (no research)
    await test_agent_chat()
    
    # Test 5: Agent with research
    await test_agent_with_research()
    
    print("\n" + "=" * 60)
    print("EXPERIENCE COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

