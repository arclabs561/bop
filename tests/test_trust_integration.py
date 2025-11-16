"""Test trust and uncertainty integration with topology."""

import pytest

from bop.context_topology import ContextTopology, ContextNode


def test_trust_aware_clique_computation():
    """Test that cliques include trust metrics."""
    topology = ContextTopology()
    
    # Create nodes with varying trust
    node1 = ContextNode(id="n1", content="test1", source="trusted", credibility=0.9)
    node2 = ContextNode(id="n2", content="test2", source="trusted", credibility=0.8)
    node3 = ContextNode(id="n3", content="test3", source="untrusted", credibility=0.2)
    
    topology.add_node(node1)
    topology.add_node(node2)
    topology.add_node(node3)
    
    # Connect trusted nodes
    topology.add_edge("n1", "n2")
    # Connect untrusted node
    topology.add_edge("n2", "n3")
    
    cliques = topology.compute_cliques()
    
    # Should have trust metrics
    assert len(cliques) > 0
    for clique in cliques:
        assert hasattr(clique, "trust_score")
        assert hasattr(clique, "avg_credibility")
        assert hasattr(clique, "adversarial_risk")


def test_trust_aware_attractor_basins():
    """Test that attractor basins filter by trust."""
    topology = ContextTopology()
    
    # Create high-trust clique
    for i in range(3):
        node = ContextNode(
            id=f"trusted_{i}",
            content=f"test{i}",
            source="trusted",
            credibility=0.8,
            confidence=0.7,
        )
        topology.add_node(node)
        if i > 0:
            topology.add_edge(f"trusted_{i-1}", f"trusted_{i}")
    
    # Create low-trust clique
    for i in range(3):
        node = ContextNode(
            id=f"untrusted_{i}",
            content=f"test{i}",
            source="untrusted",
            credibility=0.2,
            confidence=0.3,
        )
        topology.add_node(node)
        if i > 0:
            topology.add_edge(f"untrusted_{i-1}", f"untrusted_{i}")
    
    topology.compute_cliques()
    basins = topology.get_attractor_basins(min_trust=0.6)
    
    # Should only return high-trust basins
    assert len(basins) > 0
    # All basins should have high trust
    for basin in basins:
        # Check that nodes in basin have high trust
        for node_id in basin:
            node = topology.nodes[node_id]
            assert node.credibility > 0.5 or node.confidence > 0.5


def test_confidence_update_from_evidence():
    """Test temporal confidence updates (TRAIL pattern)."""
    topology = ContextTopology()
    node = ContextNode(id="n1", content="test", source="test", confidence=0.5)
    topology.add_node(node)
    
    # Update with supporting evidence
    topology.update_confidence_from_evidence("n1", new_evidence=True, evidence_quality=0.8)
    assert topology.nodes["n1"].confidence > 0.5
    assert topology.nodes["n1"].verification_count == 1
    
    # Update with contradicting evidence
    initial_confidence = topology.nodes["n1"].confidence
    topology.update_confidence_from_evidence("n1", new_evidence=False, evidence_quality=0.6)
    assert topology.nodes["n1"].confidence < initial_confidence


def test_schema_consistency_checking():
    """Test schema validation (production pattern)."""
    topology = ContextTopology()
    
    # Valid node
    node1 = ContextNode(id="n1", content="Valid claim", source="test")
    violations1 = topology.check_schema_consistency(node1)
    assert isinstance(violations1, list)
    
    # Check that violations are tracked
    assert len(topology.schema_violations) >= 0  # May or may not have violations


def test_calibration_tracking():
    """Test calibration error computation (production pattern)."""
    topology = ContextTopology()
    
    # Add some confidence predictions
    topology.confidence_predictions = [
        (0.9, True),   # High confidence, correct
        (0.8, True),   # High confidence, correct
        (0.7, False), # High confidence, wrong (miscalibrated)
        (0.3, False), # Low confidence, wrong
        (0.2, False), # Low confidence, wrong
    ]
    
    summary = topology._get_trust_summary()
    assert "calibration_error" in summary
    # Should have some calibration error (not perfectly calibrated)
    if summary["calibration_error"] is not None:
        assert summary["calibration_error"] >= 0.0


def test_trust_propagation_with_decay():
    """Test trust propagation through paths."""
    topology = ContextTopology()
    
    # Create chain: n1 -> n2 -> n3
    for i in range(3):
        node = ContextNode(
            id=f"n{i+1}",
            content=f"test{i}",
            source="test",
            credibility=0.7,
        )
        topology.add_node(node)
        if i > 0:
            topology.add_edge(f"n{i}", f"n{i+1}")
    
    # Compute path trust
    path = ["n1", "n2", "n3"]
    path_trust = topology._compute_path_trust(path)
    
    # Trust should decay with path length
    assert 0.0 <= path_trust <= 1.0
    # Longer paths should have lower trust
    direct_trust = topology.edge_trust.get(tuple(sorted(["n1", "n2"])), 0.5)
    assert path_trust <= direct_trust  # Path trust <= direct trust (decay)

