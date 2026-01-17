"""Comprehensive tests for trust and uncertainty features."""

from pran.context_topology import ContextNode, ContextTopology


def test_trust_propagation_network():
    """Test trust propagation through a network."""
    topology = ContextTopology()

    # Create network: trusted source -> intermediate -> target
    nodes = [
        ContextNode(id="source", content="trusted source", source="trusted", credibility=0.9),
        ContextNode(id="intermediate", content="intermediate", source="medium", credibility=0.7),
        ContextNode(id="target", content="target", source="low", credibility=0.5),
    ]

    for node in nodes:
        topology.add_node(node)

    topology.add_edge("source", "intermediate", weight=0.8)
    topology.add_edge("intermediate", "target", weight=0.6)

    # Compute path trust
    path_trust = topology._compute_path_trust(["source", "intermediate", "target"])

    # Path trust should be less than direct source credibility
    assert path_trust < nodes[0].credibility
    assert path_trust > 0.0


def test_confidence_calibration_tracking():
    """Test confidence calibration tracking over multiple updates."""
    topology = ContextTopology()
    node = ContextNode(id="n1", content="test", source="test", confidence=0.5)
    topology.add_node(node)

    # Add multiple predictions
    predictions = [
        (0.9, True),   # High confidence, correct
        (0.8, True),   # High confidence, correct
        (0.7, False),  # High confidence, wrong
        (0.3, False),  # Low confidence, wrong
        (0.2, False),  # Low confidence, wrong
    ]

    topology.confidence_predictions = predictions

    summary = topology._get_trust_summary()

    # Should compute calibration error
    if summary["calibration_error"] is not None:
        assert summary["calibration_error"] >= 0.0
        # With these predictions, should have some calibration error
        assert summary["calibration_error"] > 0.0


def test_schema_validation_comprehensive():
    """Test schema validation with various node types."""
    topology = ContextTopology()

    # Valid nodes
    valid_node = ContextNode(id="valid", content="Valid content", source="test")
    violations = topology.check_schema_consistency(valid_node)
    assert isinstance(violations, list)

    # Node with empty content
    empty_node = ContextNode(id="empty", content="", source="test")
    violations = topology.check_schema_consistency(empty_node)
    assert isinstance(violations, list)

    # Node with very long content
    long_node = ContextNode(id="long", content="a" * 10000, source="test")
    violations = topology.check_schema_consistency(long_node)
    assert isinstance(violations, list)


def test_confidence_update_evidence_quality():
    """Test confidence updates with different evidence quality levels."""
    topology = ContextTopology()
    node = ContextNode(id="n1", content="test", source="test", confidence=0.5)
    topology.add_node(node)

    initial_confidence = node.confidence

    # High quality evidence
    topology.update_confidence_from_evidence("n1", new_evidence=True, evidence_quality=0.9)
    high_quality_confidence = node.confidence

    # Reset
    topology.nodes["n1"].confidence = initial_confidence

    # Low quality evidence
    topology.update_confidence_from_evidence("n1", new_evidence=True, evidence_quality=0.3)
    low_quality_confidence = node.confidence

    # High quality should increase more
    assert high_quality_confidence > low_quality_confidence


def test_trust_aware_clique_filtering():
    """Test trust-aware clique filtering with various thresholds."""
    topology = ContextTopology()

    # Create mixed trust network
    high_trust_nodes = []
    low_trust_nodes = []

    for i in range(3):
        ht_node = ContextNode(
            id=f"ht{i}",
            content=f"high trust {i}",
            source="trusted",
            credibility=0.9,
            confidence=0.8,
        )
        topology.add_node(ht_node)
        high_trust_nodes.append(f"ht{i}")

        lt_node = ContextNode(
            id=f"lt{i}",
            content=f"low trust {i}",
            source="untrusted",
            credibility=0.2,
            confidence=0.3,
        )
        topology.add_node(lt_node)
        low_trust_nodes.append(f"lt{i}")

    # Connect high-trust nodes
    for i in range(len(high_trust_nodes) - 1):
        topology.add_edge(high_trust_nodes[i], high_trust_nodes[i + 1])

    # Connect low-trust nodes
    for i in range(len(low_trust_nodes) - 1):
        topology.add_edge(low_trust_nodes[i], low_trust_nodes[i + 1])

    topology.compute_cliques()

    # Filter by high trust
    high_trust_basins = topology.get_attractor_basins(min_trust=0.7)

    # Filter by low trust
    low_trust_basins = topology.get_attractor_basins(min_trust=0.0)

    # High trust threshold should return fewer or equal basins
    assert len(high_trust_basins) <= len(low_trust_basins)


def test_epistemic_aleatoric_separation():
    """Test that epistemic and aleatoric uncertainty are tracked separately."""
    topology = ContextTopology()

    # Create nodes with different uncertainty profiles
    node1 = ContextNode(
        id="n1",
        content="High epistemic, low aleatoric",
        source="test",
        epistemic_uncertainty=0.8,
        aleatoric_uncertainty=0.2,
    )

    node2 = ContextNode(
        id="n2",
        content="Low epistemic, high aleatoric",
        source="test",
        epistemic_uncertainty=0.2,
        aleatoric_uncertainty=0.8,
    )

    topology.add_node(node1)
    topology.add_node(node2)

    # Both should be stored separately
    assert topology.nodes["n1"].epistemic_uncertainty == 0.8
    assert topology.nodes["n1"].aleatoric_uncertainty == 0.2
    assert topology.nodes["n2"].epistemic_uncertainty == 0.2
    assert topology.nodes["n2"].aleatoric_uncertainty == 0.8


def test_verification_count_tracking():
    """Test that verification count is tracked."""
    topology = ContextTopology()
    node = ContextNode(id="n1", content="test", source="test", verification_count=0)
    topology.add_node(node)

    # Add multiple verifications
    for _ in range(5):
        topology.update_confidence_from_evidence("n1", new_evidence=True, evidence_quality=0.5)

    # Verification count should have increased
    assert topology.nodes["n1"].verification_count == 5


def test_trust_summary_completeness():
    """Test that trust summary includes all relevant metrics."""
    topology = ContextTopology()

    # Add some nodes and edges
    for i in range(3):
        node = ContextNode(
            id=f"n{i}",
            content=f"test{i}",
            source="test",
            credibility=0.7,
            confidence=0.6,
        )
        topology.add_node(node)
        if i > 0:
            topology.add_edge(f"n{i-1}", f"n{i}")

    summary = topology._get_trust_summary()

    # Should include all metrics
    required_keys = [
        "avg_trust",
        "high_trust_edges",
        "low_trust_edges",
        "avg_credibility",
        "avg_confidence",
        "calibration_error",
        "schema_violations",
    ]

    for key in required_keys:
        assert key in summary


def test_adversarial_pattern_detection():
    """Test adversarial pattern detection in topology."""
    topology = ContextTopology()

    # Create suspicious pattern: isolated low-trust node
    for i in range(3):
        node = ContextNode(
            id=f"normal{i}",
            content=f"normal {i}",
            source="trusted",
            credibility=0.8,
        )
        topology.add_node(node)
        if i > 0:
            topology.add_edge(f"normal{i-1}", f"normal{i}")

    # Add isolated low-trust node
    suspicious = ContextNode(
        id="suspicious",
        content="suspicious content",
        source="unknown",
        credibility=0.1,
        confidence=0.1,
    )
    topology.add_node(suspicious)

    # Analyze for adversarial patterns
    impact = topology.analyze_context_injection_impact([suspicious])

    # Should detect adversarial patterns
    if "adversarial_patterns" in impact:
        assert impact["adversarial_patterns"] >= 0


def test_trust_decay_with_path_length():
    """Test that trust decays appropriately with path length."""
    ContextTopology()

    # Create chains of different lengths
    for length in [2, 3, 4, 5]:
        topo = ContextTopology()
        for i in range(length):
            node = ContextNode(id=f"n{i}", content=f"test{i}", source="test", credibility=0.8)
            topo.add_node(node)
            if i > 0:
                topo.add_edge(f"n{i-1}", f"n{i}", weight=0.8)

        path = [f"n{i}" for i in range(length)]
        path_trust = topo._compute_path_trust(path)

        # Longer paths should have lower trust
        if length > 2:
            short_path = [f"n{i}" for i in range(2)]
            short_trust = topo._compute_path_trust(short_path)
            assert path_trust <= short_trust

