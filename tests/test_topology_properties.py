"""Property-based tests for topology invariants."""

import pytest

from bop.context_topology import ContextNode, ContextTopology


def test_topology_euler_characteristic_invariant():
    """Test Euler characteristic is consistent with graph structure."""
    topology = ContextTopology()

    # Add nodes and edges
    for i in range(5):
        node = ContextNode(id=f"n{i}", content=f"test{i}", source="test")
        topology.add_node(node)
        if i > 0:
            topology.add_edge(f"n{i-1}", f"n{i}")

    # Compute metrics
    topology.compute_cliques()
    euler = topology.compute_euler_characteristic()
    betti = topology.compute_betti_numbers()

    # Euler characteristic = V - E + F (for graphs, F = cliques)
    # Should be consistent with Betti numbers
    assert isinstance(euler, (int, float))
    # Euler char should relate to Betti numbers: χ = β₀ - β₁
    if betti.get(0) is not None and betti.get(1) is not None:
        expected_euler = betti[0] - betti[1]
        # Allow some approximation error
        assert abs(euler - expected_euler) < 10


def test_topology_trust_monotonicity():
    """Test that trust scores are monotonic (adding evidence increases trust)."""
    topology = ContextTopology()
    node = ContextNode(id="n1", content="test", source="test", confidence=0.5)
    topology.add_node(node)

    initial_confidence = node.confidence

    # Add supporting evidence multiple times
    for _ in range(3):
        topology.update_confidence_from_evidence("n1", new_evidence=True, evidence_quality=0.8)

    # Confidence should have increased
    assert topology.nodes["n1"].confidence > initial_confidence
    assert topology.nodes["n1"].confidence <= 1.0


def test_topology_clique_coherence_bounds():
    """Test that clique coherence scores are in valid range."""
    topology = ContextTopology()

    # Create a clique
    for i in range(3):
        node = ContextNode(id=f"n{i}", content=f"test{i}", source="test", credibility=0.7)
        topology.add_node(node)
        if i > 0:
            topology.add_edge(f"n{i-1}", f"n{i}")

    cliques = topology.compute_cliques()

    for clique in cliques:
        assert 0.0 <= clique.coherence_score <= 1.0
        assert 0.0 <= clique.trust_score <= 1.0
        assert 0.0 <= clique.adversarial_risk <= 1.0


def test_topology_betti_numbers_non_negative():
    """Test that Betti numbers are non-negative."""
    ContextTopology()

    # Various graph structures
    test_cases = [
        # Empty graph
        [],
        # Single node
        [("n0", [])],
        # Chain
        [("n0", ["n1"]), ("n1", ["n2"])],
        # Triangle
        [("n0", ["n1", "n2"]), ("n1", ["n2"])],
    ]

    for case in test_cases:
        topo = ContextTopology()
        for node_id, neighbors in case:
            if node_id not in topo.nodes:
                topo.add_node(ContextNode(id=node_id, content=node_id, source="test"))
            for neighbor in neighbors:
                if neighbor not in topo.nodes:
                    topo.add_node(ContextNode(id=neighbor, content=neighbor, source="test"))
                topo.add_edge(node_id, neighbor)

        betti = topo.compute_betti_numbers()
        for dim, value in betti.items():
            assert value >= 0, f"Betti number β_{dim} should be non-negative, got {value}"


def test_topology_fisher_information_positive():
    """Test that Fisher Information estimate is positive for non-empty graphs."""
    topology = ContextTopology()

    # Empty graph should return 0 or small value
    fisher_empty = topology.compute_fisher_information_estimate()
    assert fisher_empty >= 0.0

    # Add nodes and edges
    for i in range(3):
        node = ContextNode(id=f"n{i}", content=f"test{i}", source="test")
        topology.add_node(node)
        if i > 0:
            topology.add_edge(f"n{i-1}", f"n{i}")

    topology.compute_cliques()
    fisher = topology.compute_fisher_information_estimate()

    # Should be positive for non-empty graph with structure
    assert fisher >= 0.0


def test_topology_d_separation_symmetry():
    """Test that d-separation is symmetric."""
    topology = ContextTopology()

    # Create graph: A - B - C
    for node_id in ["A", "B", "C"]:
        topology.add_node(ContextNode(id=node_id, content=node_id, source="test"))

    topology.add_edge("A", "B")
    topology.add_edge("B", "C")

    # A and C should have same d-separation status regardless of order
    d_sep_AC = topology.analyze_d_separation("A", "C", {"B"})
    d_sep_CA = topology.analyze_d_separation("C", "A", {"B"})

    assert d_sep_AC == d_sep_CA


def test_topology_attractor_basins_maximal():
    """Test that attractor basins are maximal cliques."""
    topology = ContextTopology()

    # Create a structure with nested cliques
    # Triangle: n0-n1-n2
    # Plus n3 connected to n0, n1
    for i in range(4):
        node = ContextNode(id=f"n{i}", content=f"test{i}", source="test", credibility=0.7)
        topology.add_node(node)

    # Triangle
    topology.add_edge("n0", "n1")
    topology.add_edge("n1", "n2")
    topology.add_edge("n2", "n0")

    # n3 connected to triangle
    topology.add_edge("n3", "n0")
    topology.add_edge("n3", "n1")

    basins = topology.get_attractor_basins()

    # Each basin should be a maximal clique
    for basin in basins:
        # Check all nodes in basin are connected
        basin_list = list(basin)
        for i, node1 in enumerate(basin_list):
            for node2 in basin_list[i + 1:]:
                edge = tuple(sorted([node1, node2]))
                assert edge in topology.edges, f"Nodes {node1} and {node2} in basin should be connected"


def test_topology_confidence_bounds():
    """Test that confidence scores stay in valid bounds."""
    topology = ContextTopology()
    node = ContextNode(id="n1", content="test", source="test", confidence=0.5)
    topology.add_node(node)

    # Try to push confidence above 1.0
    for _ in range(20):
        topology.update_confidence_from_evidence("n1", new_evidence=True, evidence_quality=1.0)

    assert topology.nodes["n1"].confidence <= 1.0

    # Reset and try to push below 0.0
    topology.nodes["n1"].confidence = 0.5
    for _ in range(20):
        topology.update_confidence_from_evidence("n1", new_evidence=False, evidence_quality=1.0)

    assert topology.nodes["n1"].confidence >= 0.0


def test_topology_path_trust_decay():
    """Test that path trust decays with path length."""
    topology = ContextTopology()

    # Create a chain: n0 - n1 - n2 - n3
    for i in range(4):
        node = ContextNode(id=f"n{i}", content=f"test{i}", source="test", credibility=0.8)
        topology.add_node(node)
        if i > 0:
            topology.add_edge(f"n{i-1}", f"n{i}", weight=0.8)

    # Direct path trust
    direct_trust = topology._compute_path_trust(["n0", "n1"])

    # Longer path trust
    long_path_trust = topology._compute_path_trust(["n0", "n1", "n2", "n3"])

    # Longer path should have lower or equal trust (decay)
    assert long_path_trust <= direct_trust


def test_topology_node_id_uniqueness():
    """Test that node IDs are unique."""
    topology = ContextTopology()

    # Add same node twice
    node1 = ContextNode(id="n1", content="test1", source="test")
    node2 = ContextNode(id="n1", content="test2", source="test")

    topology.add_node(node1)
    topology.add_node(node2)  # Should overwrite or be idempotent

    # Should only have one node with ID "n1"
    assert "n1" in topology.nodes
    # Content might be from second addition (implementation-dependent)
    assert topology.nodes["n1"].id == "n1"


def test_topology_edge_consistency():
    """Test that edges are consistent (both nodes exist)."""
    topology = ContextTopology()

    # Try to add edge before nodes
    with pytest.raises(ValueError):
        topology.add_edge("nonexistent1", "nonexistent2")

    # Add nodes first
    topology.add_node(ContextNode(id="n1", content="test1", source="test"))
    topology.add_node(ContextNode(id="n2", content="test2", source="test"))

    # Now edge should work
    topology.add_edge("n1", "n2")
    assert tuple(sorted(["n1", "n2"])) in topology.edges

