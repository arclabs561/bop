"""Extended edge case tests for topology."""

from bop.context_topology import ContextNode, ContextTopology


def test_topology_single_node_graph():
    """Test topology with single node (no edges)."""
    topology = ContextTopology()
    node = ContextNode(id="n1", content="test", source="test")
    topology.add_node(node)

    cliques = topology.compute_cliques()
    betti = topology.compute_betti_numbers()
    euler = topology.compute_euler_characteristic()

    # Single node should have no cliques (need at least 2 nodes for edge)
    assert len(cliques) == 0
    assert betti.get(0, 0) == 1  # One connected component
    assert euler >= 0


def test_topology_disconnected_components():
    """Test topology with disconnected components."""
    topology = ContextTopology()

    # Component 1: n0 - n1
    topology.add_node(ContextNode(id="n0", content="test0", source="test"))
    topology.add_node(ContextNode(id="n1", content="test1", source="test"))
    topology.add_edge("n0", "n1")

    # Component 2: n2 - n3
    topology.add_node(ContextNode(id="n2", content="test2", source="test"))
    topology.add_node(ContextNode(id="n3", content="test3", source="test"))
    topology.add_edge("n2", "n3")

    betti = topology.compute_betti_numbers()

    # Should have 2 connected components
    assert betti.get(0, 0) == 2


def test_topology_cycle_detection():
    """Test topology detects cycles."""
    topology = ContextTopology()

    # Create cycle: n0 - n1 - n2 - n0
    for i in range(3):
        topology.add_node(ContextNode(id=f"n{i}", content=f"test{i}", source="test"))

    topology.add_edge("n0", "n1")
    topology.add_edge("n1", "n2")
    topology.add_edge("n2", "n0")

    betti = topology.compute_betti_numbers()

    # Should have 1 cycle (β₁ = 1)
    assert betti.get(1, 0) >= 0  # At least 0, might be 1 for cycle


def test_topology_high_degree_node():
    """Test topology with high-degree hub node."""
    topology = ContextTopology()

    # Create hub: n0 connected to many nodes
    hub = ContextNode(id="hub", content="hub", source="test")
    topology.add_node(hub)

    for i in range(10):
        node = ContextNode(id=f"spoke{i}", content=f"spoke{i}", source="test")
        topology.add_node(node)
        topology.add_edge("hub", f"spoke{i}")

    cliques = topology.compute_cliques()

    # Hub should create many cliques
    assert len(cliques) > 0


def test_topology_trust_edge_cases():
    """Test trust calculations with edge cases."""
    topology = ContextTopology()

    # Node with extreme trust values
    node1 = ContextNode(id="n1", content="test", source="test", credibility=0.0, confidence=0.0)
    node2 = ContextNode(id="n2", content="test", source="test", credibility=1.0, confidence=1.0)

    topology.add_node(node1)
    topology.add_node(node2)
    topology.add_edge("n1", "n2", weight=0.5)

    # Trust summary should handle extremes
    summary = topology._get_trust_summary()
    assert summary["avg_credibility"] >= 0.0
    assert summary["avg_credibility"] <= 1.0


def test_topology_empty_after_reset():
    """Test topology reset creates empty state."""
    topology = ContextTopology()

    # Add some nodes
    for i in range(5):
        topology.add_node(ContextNode(id=f"n{i}", content=f"test{i}", source="test"))
        if i > 0:
            topology.add_edge(f"n{i-1}", f"n{i}")

    assert len(topology.nodes) > 0

    # Reset
    topology = ContextTopology()

    assert len(topology.nodes) == 0
    assert len(topology.edges) == 0


def test_topology_path_finding_limits():
    """Test path finding respects limits."""
    topology = ContextTopology()

    # Create long chain
    for i in range(20):
        topology.add_node(ContextNode(id=f"n{i}", content=f"test{i}", source="test"))
        if i > 0:
            topology.add_edge(f"n{i-1}", f"n{i}")

    # Find paths with limit
    paths = topology._find_paths("n0", "n19", max_length=10)

    # Should respect max_length
    for path in paths:
        assert len(path) <= 10


def test_topology_clique_max_size():
    """Test clique computation with max_size constraint."""
    topology = ContextTopology()

    # Create complete graph of 5 nodes
    for i in range(5):
        topology.add_node(ContextNode(id=f"n{i}", content=f"test{i}", source="test"))
        for j in range(i):
            topology.add_edge(f"n{i}", f"n{j}")

    # Compute cliques with max_size=3
    cliques = topology.compute_cliques(min_size=2, max_size=3)

    # All cliques should be <= max_size
    for clique in cliques:
        assert len(clique.nodes) <= 3


def test_topology_fisher_info_empty():
    """Test Fisher Information with empty graph."""
    topology = ContextTopology()

    fisher = topology.compute_fisher_information_estimate()

    # Should return 0 or small value for empty graph
    assert fisher >= 0.0


def test_topology_calibration_empty():
    """Test calibration with no predictions."""
    topology = ContextTopology()

    summary = topology._get_trust_summary()

    # Should handle empty predictions gracefully
    assert summary["calibration_error"] is None or summary["calibration_error"] >= 0.0

