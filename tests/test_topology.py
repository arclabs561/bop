"""Tests for context topology analysis."""

import pytest

from bop.context_topology import ContextTopology, ContextNode, CliqueStructure


def test_add_node():
    """Test adding nodes to topology."""
    topology = ContextTopology()
    node = ContextNode(id="node1", content="test", source="test")
    topology.add_node(node)
    
    # Verify node was added correctly
    assert "node1" in topology.nodes
    assert topology.nodes["node1"] == node
    assert topology.nodes["node1"].content == "test"
    assert topology.nodes["node1"].source == "test"


def test_add_edge():
    """Test adding edges between nodes."""
    topology = ContextTopology()
    node1 = ContextNode(id="node1", content="test1", source="test")
    node2 = ContextNode(id="node2", content="test2", source="test")
    topology.add_node(node1)
    topology.add_node(node2)
    topology.add_edge("node1", "node2", weight=0.8)
    assert ("node1", "node2") in topology.edges or ("node2", "node1") in topology.edges


def test_compute_cliques():
    """Test clique computation."""
    topology = ContextTopology()
    # Create a triangle (3-clique)
    for i in range(3):
        node = ContextNode(id=f"node{i}", content=f"test{i}", source="test")
        topology.add_node(node)
    topology.add_edge("node0", "node1")
    topology.add_edge("node1", "node2")
    topology.add_edge("node0", "node2")

    cliques = topology.compute_cliques()
    
    # Should find exactly one clique of size 3 (triangle)
    assert len(cliques) > 0
    clique_sizes = [len(c.nodes) for c in cliques]
    assert 3 in clique_sizes  # Should have a 3-clique
    # Verify the clique contains all three nodes
    three_clique = next((c for c in cliques if len(c.nodes) == 3), None)
    assert three_clique is not None
    assert {"node0", "node1", "node2"}.issubset(three_clique.nodes)


def test_compute_betti_numbers():
    """Test Betti number computation."""
    topology = ContextTopology()
    # Create connected graph
    for i in range(3):
        node = ContextNode(id=f"node{i}", content=f"test{i}", source="test")
        topology.add_node(node)
    topology.add_edge("node0", "node1")
    topology.add_edge("node1", "node2")

    betti = topology.compute_betti_numbers()
    assert 0 in betti
    assert betti[0] == 1  # One connected component


def test_euler_characteristic():
    """Test Euler characteristic computation."""
    topology = ContextTopology()
    # Create simple graph
    for i in range(3):
        node = ContextNode(id=f"node{i}", content=f"test{i}", source="test")
        topology.add_node(node)
    topology.add_edge("node0", "node1")
    topology.compute_cliques()

    chi = topology.compute_euler_characteristic()
    assert isinstance(chi, int)


def test_analyze_context_injection_impact():
    """Test analyzing impact of adding new context nodes."""
    topology = ContextTopology()
    # Add initial node
    node1 = ContextNode(id="node1", content="initial", source="test")
    topology.add_node(node1)

    # Add new nodes
    new_nodes = [
        ContextNode(id="node2", content="new1", source="test", dependencies={"node1"}),
        ContextNode(id="node3", content="new2", source="test", dependencies={"node1"}),
    ]

    impact = topology.analyze_context_injection_impact(new_nodes)
    assert "new_cliques" in impact
    assert "betti_delta" in impact
    assert "fisher_delta" in impact

