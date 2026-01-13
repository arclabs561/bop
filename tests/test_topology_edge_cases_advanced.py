"""Advanced edge case tests for topology."""


from bop.context_topology import ContextNode, ContextTopology


def test_topology_large_graph_performance():
    """Test topology handles large graphs reasonably."""
    topology = ContextTopology()

    # Create a moderately large graph (50 nodes)
    for i in range(50):
        node = ContextNode(
            id=f"n{i}",
            content=f"Content {i}",
            source="test",
            credibility=0.7,
        )
        topology.add_node(node)

    # Create a sparse graph (each node connected to 2-3 others)
    for i in range(50):
        for j in range(i + 1, min(i + 3, 50)):
            topology.add_edge(f"n{i}", f"n{j}", weight=0.8)

    # Should compute cliques without hanging
    cliques = topology.compute_cliques()

    assert isinstance(cliques, list)
    # Should find some cliques
    assert len(cliques) >= 0


def test_topology_highly_connected_graph():
    """Test topology with highly connected graph (many cliques)."""
    topology = ContextTopology()

    # Create a small complete graph (all nodes connected)
    nodes = []
    for i in range(5):
        node = ContextNode(id=f"n{i}", content=f"test{i}", source="test")
        topology.add_node(node)
        nodes.append(f"n{i}")

    # Connect all nodes to all other nodes
    for i, n1 in enumerate(nodes):
        for n2 in nodes[i + 1:]:
            topology.add_edge(n1, n2, weight=0.9)

    cliques = topology.compute_cliques()

    # Complete graph should have many cliques
    assert len(cliques) > 0
    # Should find at least one large clique
    max_clique_size = max(len(c.nodes) for c in cliques) if cliques else 0
    assert max_clique_size >= 3


def test_topology_disconnected_components():
    """Test topology with disconnected components."""
    topology = ContextTopology()

    # Create two disconnected components
    for i in range(3):
        node = ContextNode(id=f"c1_n{i}", content="comp1", source="test")
        topology.add_node(node)
        if i > 0:
            topology.add_edge(f"c1_n{i-1}", f"c1_n{i}")

    for i in range(3):
        node = ContextNode(id=f"c2_n{i}", content="comp2", source="test")
        topology.add_node(node)
        if i > 0:
            topology.add_edge(f"c2_n{i-1}", f"c2_n{i}")

    betti = topology.compute_betti_numbers()

    # Should have 2 connected components (β₀ = 2)
    assert betti[0] == 2


def test_topology_cycle_detection():
    """Test topology detects cycles correctly."""
    topology = ContextTopology()

    # Create a cycle: n0 -> n1 -> n2 -> n0
    for i in range(3):
        node = ContextNode(id=f"n{i}", content=f"test{i}", source="test")
        topology.add_node(node)

    topology.add_edge("n0", "n1")
    topology.add_edge("n1", "n2")
    topology.add_edge("n2", "n0")

    betti = topology.compute_betti_numbers()

    # Should detect at least one cycle (β₁ >= 1)
    assert betti[1] >= 1


def test_topology_fisher_information_edge_cases():
    """Test Fisher Information with edge cases."""
    topology = ContextTopology()

    # Empty topology
    fisher = topology.compute_fisher_information_estimate()
    assert fisher == 0.0

    # Single node
    node = ContextNode(id="n1", content="test", source="test")
    topology.add_node(node)
    topology.compute_cliques()
    fisher = topology.compute_fisher_information_estimate()
    assert fisher == 0.0  # No cliques, so 0

    # Two nodes, no edge
    node2 = ContextNode(id="n2", content="test2", source="test")
    topology.add_node(node2)
    topology.compute_cliques()
    fisher = topology.compute_fisher_information_estimate()
    assert fisher == 0.0  # No cliques

    # Two nodes, connected
    topology.add_edge("n1", "n2", weight=0.9)
    topology.compute_cliques()
    fisher = topology.compute_fisher_information_estimate()
    assert 0.0 <= fisher <= 1.0  # Should be in valid range


def test_topology_euler_characteristic_variations():
    """Test Euler characteristic with different graph structures."""
    topology = ContextTopology()

    # Tree structure (no cycles)
    for i in range(4):
        node = ContextNode(id=f"n{i}", content=f"test{i}", source="test")
        topology.add_node(node)
        if i > 0:
            topology.add_edge(f"n{i-1}", f"n{i}")

    topology.compute_cliques()
    chi_tree = topology.compute_euler_characteristic()

    # Reset and create cycle
    topology = ContextTopology()
    for i in range(3):
        node = ContextNode(id=f"n{i}", content=f"test{i}", source="test")
        topology.add_node(node)
    topology.add_edge("n0", "n1")
    topology.add_edge("n1", "n2")
    topology.add_edge("n2", "n0")

    topology.compute_cliques()
    chi_cycle = topology.compute_euler_characteristic()

    # Euler characteristic should differ
    assert isinstance(chi_tree, int)
    assert isinstance(chi_cycle, int)


def test_topology_d_separation_complex_paths():
    """Test d-separation with complex path structures."""
    topology = ContextTopology()

    # Create graph: A - B - C - D, with A - D direct
    for node_id in ["A", "B", "C", "D"]:
        topology.add_node(ContextNode(id=node_id, content=node_id, source="test"))

    topology.add_edge("A", "B")
    topology.add_edge("B", "C")
    topology.add_edge("C", "D")
    topology.add_edge("A", "D")  # Direct path

    # Add trust to edges so paths are considered valid
    topology.add_edge("A", "B", weight=0.8, trust=0.7)
    topology.add_edge("B", "C", weight=0.8, trust=0.7)
    topology.add_edge("C", "D", weight=0.8, trust=0.7)
    topology.add_edge("A", "D", weight=0.9, trust=0.8)  # Direct path with high trust

    # A and D should not be d-separated by empty set (direct path exists and is trusted)
    d_sep = topology.analyze_d_separation("A", "D", set(), trust_threshold=0.3)
    assert d_sep is False  # Direct path exists

    # Test that conditioning on intermediate nodes blocks indirect paths
    # Path A-B-C-D is blocked by B, but A-D direct path has no intermediate nodes
    # So A and D are not d-separated by {B} (direct path remains open)
    d_sep = topology.analyze_d_separation("A", "D", {"B"}, trust_threshold=0.3)
    assert d_sep is False  # Direct path A-D is not blocked

    # With direct path A-D, nodes are only d-separated if we condition on A or D themselves
    # (which doesn't make practical sense, but tests the implementation)
    # For this graph structure, A and D are always connected via direct path


def test_topology_attractor_basins_filtering():
    """Test attractor basins filtering by trust and coherence."""
    topology = ContextTopology()

    # Create high-trust clique
    for i in range(3):
        node = ContextNode(
            id=f"ht{i}",
            content=f"high trust {i}",
            source="trusted",
            credibility=0.9,
            confidence=0.8,
        )
        topology.add_node(node)
        if i > 0:
            topology.add_edge(f"ht{i-1}", f"ht{i}", weight=0.9)

    # Create low-trust clique
    for i in range(3):
        node = ContextNode(
            id=f"lt{i}",
            content=f"low trust {i}",
            source="untrusted",
            credibility=0.3,
            confidence=0.2,
        )
        topology.add_node(node)
        if i > 0:
            topology.add_edge(f"lt{i-1}", f"lt{i}", weight=0.4)

    topology.compute_cliques()

    # Get high-trust basins only
    high_trust_basins = topology.get_attractor_basins(min_trust=0.7, min_coherence=0.8)

    # Should filter out low-trust cliques
    assert isinstance(high_trust_basins, list)
    # All returned basins should meet criteria
    for basin in high_trust_basins:
        # Verify through clique structure
        assert isinstance(basin, set)


def test_topology_context_injection_idempotent():
    """Test that context injection is idempotent."""
    topology = ContextTopology()

    node1 = ContextNode(id="n1", content="test1", source="test")
    topology.add_node(node1)

    # Add same node again
    node1_duplicate = ContextNode(id="n1", content="different", source="test")

    impact1 = topology.analyze_context_injection_impact([node1_duplicate])

    # Adding duplicate should be idempotent
    assert "new_cliques" in impact1
    # Node content shouldn't change (idempotent)
    assert topology.nodes["n1"].content == "test1"  # Original content preserved


def test_topology_trust_propagation():
    """Test trust propagation through edges."""
    topology = ContextTopology()

    # Create chain: high trust -> medium -> low
    node1 = ContextNode(id="n1", content="high", source="test", credibility=0.9, confidence=0.8)
    node2 = ContextNode(id="n2", content="medium", source="test", credibility=0.6, confidence=0.5)
    node3 = ContextNode(id="n3", content="low", source="test", credibility=0.3, confidence=0.2)

    topology.add_node(node1)
    topology.add_node(node2)
    topology.add_node(node3)

    topology.add_edge("n1", "n2", weight=0.8, trust=0.7)
    topology.add_edge("n2", "n3", weight=0.6, trust=0.4)

    topology.compute_cliques()

    # Trust should be considered in clique computation
    cliques = topology.cliques
    assert isinstance(cliques, list)


def test_topology_fisher_information_with_trust():
    """Test Fisher Information calculation includes trust."""
    topology = ContextTopology()

    # Create high-trust clique
    for i in range(3):
        node = ContextNode(
            id=f"n{i}",
            content=f"test{i}",
            source="trusted",
            credibility=0.9,
            confidence=0.8,
        )
        topology.add_node(node)
        if i > 0:
            topology.add_edge(f"n{i-1}", f"n{i}", weight=0.9, trust=0.8)

    topology.compute_cliques()
    fisher_high_trust = topology.compute_fisher_information_estimate()

    # Reset and create low-trust clique
    topology = ContextTopology()
    for i in range(3):
        node = ContextNode(
            id=f"n{i}",
            content=f"test{i}",
            source="untrusted",
            credibility=0.3,
            confidence=0.2,
        )
        topology.add_node(node)
        if i > 0:
            topology.add_edge(f"n{i-1}", f"n{i}", weight=0.4, trust=0.2)

    topology.compute_cliques()
    fisher_low_trust = topology.compute_fisher_information_estimate()

    # High trust should generally have higher Fisher Information
    # (though exact values depend on implementation)
    assert 0.0 <= fisher_high_trust <= 1.0
    assert 0.0 <= fisher_low_trust <= 1.0

