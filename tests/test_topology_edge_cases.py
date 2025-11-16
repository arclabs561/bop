"""Test edge cases and error handling in topology."""

import pytest

from bop.context_topology import ContextTopology, ContextNode


def test_add_edge_without_nodes():
    """Test that adding edge without nodes raises error."""
    topology = ContextTopology()
    with pytest.raises(ValueError, match="does not exist"):
        topology.add_edge("nonexistent1", "nonexistent2")


def test_add_edge_self_loop():
    """Test that self-loops are rejected."""
    topology = ContextTopology()
    node = ContextNode(id="node1", content="test", source="test")
    topology.add_node(node)
    with pytest.raises(ValueError, match="self-loop"):
        topology.add_edge("node1", "node1")


def test_compute_cliques_empty_graph():
    """Test clique computation on empty graph."""
    topology = ContextTopology()
    cliques = topology.compute_cliques()
    assert cliques == []


def test_compute_cliques_single_node():
    """Test clique computation with single node."""
    topology = ContextTopology()
    node = ContextNode(id="node1", content="test", source="test")
    topology.add_node(node)
    # With min_size=1, single node could be considered a 0-simplex
    # But our implementation requires at least 2 nodes for a clique
    cliques_size_2 = topology.compute_cliques(min_size=2)
    # Should return empty since no edges exist
    assert cliques_size_2 == []


def test_compute_betti_numbers_empty():
    """Test Betti numbers on empty graph."""
    topology = ContextTopology()
    betti = topology.compute_betti_numbers()
    assert betti == {0: 0, 1: 0}


def test_analyze_d_separation_invalid_conditioning():
    """Test d-separation with invalid conditioning set."""
    topology = ContextTopology()
    node1 = ContextNode(id="node1", content="test1", source="test")
    node2 = ContextNode(id="node2", content="test2", source="test")
    topology.add_node(node1)
    topology.add_node(node2)
    topology.add_edge("node1", "node2")

    with pytest.raises(ValueError, match="invalid nodes"):
        topology.analyze_d_separation("node1", "node2", {"nonexistent"})


def test_analyze_d_separation_same_node():
    """Test d-separation with same node."""
    topology = ContextTopology()
    node1 = ContextNode(id="node1", content="test1", source="test")
    topology.add_node(node1)
    # Node is always dependent on itself
    assert topology.analyze_d_separation("node1", "node1", set()) is False


def test_analyze_context_injection_impact_empty():
    """Test impact analysis with empty node list."""
    topology = ContextTopology()
    impact = topology.analyze_context_injection_impact([])
    assert impact["new_cliques"] == 0
    assert impact["topology_changed"] is False


def test_analyze_context_injection_impact_duplicate_nodes():
    """Test impact analysis with duplicate node IDs."""
    topology = ContextTopology()
    node1 = ContextNode(id="node1", content="test1", source="test")
    node2 = ContextNode(id="node1", content="test2", source="test")  # Duplicate ID
    topology.add_node(node1)

    # Adding duplicate should be idempotent (node already exists)
    # The node content won't be updated, but should not crash
    impact = topology.analyze_context_injection_impact([node2])
    # Should not crash - node2 won't be added (already exists)
    assert "new_cliques" in impact
    # With only 1 node, no cliques can form (need at least 2 nodes)
    assert impact["new_cliques"] == 0


def test_find_paths_max_paths_limit():
    """Test that path finding respects max_paths limit."""
    topology = ContextTopology()
    # Create a highly connected graph that could generate many paths
    for i in range(5):
        node = ContextNode(id=f"node{i}", content=f"test{i}", source="test")
        topology.add_node(node)

    # Create a complete graph (all nodes connected)
    for i in range(5):
        for j in range(i + 1, 5):
            topology.add_edge(f"node{i}", f"node{j}")

    paths = topology._find_paths("node0", "node4", max_length=10)
    # Should be limited to prevent exponential explosion
    assert len(paths) <= 100  # max_paths limit


def test_compute_euler_characteristic_no_cliques():
    """Test Euler characteristic when no cliques computed."""
    topology = ContextTopology()
    # Should handle gracefully
    chi = topology.compute_euler_characteristic()
    assert chi == 0  # No simplices = 0


def test_get_attractor_basins_auto_compute():
    """Test that attractor basins auto-computes cliques if needed."""
    topology = ContextTopology()
    node1 = ContextNode(id="node1", content="test1", source="test")
    node2 = ContextNode(id="node2", content="test2", source="test")
    topology.add_node(node1)
    topology.add_node(node2)
    topology.add_edge("node1", "node2")

    # Should auto-compute cliques
    basins = topology.get_attractor_basins()
    assert isinstance(basins, list)

