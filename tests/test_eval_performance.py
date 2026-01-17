"""Performance and scale tests for evaluation framework."""

import time

from pran.context_topology import ContextNode, ContextTopology
from pran.eval import EvaluationFramework


def test_eval_large_test_case_set():
    """Test evaluation with large number of test cases."""
    framework = EvaluationFramework()

    # Create many test cases
    test_cases = []
    for i in range(100):
        test_cases.append({
            "input": f"Test query {i}",
            "expected": {"input_analysis": str, "steps": list, "final_result": str},
            "actual": {
                "input_analysis": f"Analyzing query {i}",
                "steps": [f"Step 1 for {i}", f"Step 2 for {i}"],
                "final_result": f"Result for {i}",
            },
        })

    start_time = time.time()
    result = framework.evaluate_schema_usage("chain_of_thought", test_cases)
    elapsed = time.time() - start_time

    # Should complete in reasonable time (< 5 seconds)
    assert elapsed < 5.0
    assert result.score >= 0.0


def test_eval_large_response_set():
    """Test evaluation with large number of responses."""
    framework = EvaluationFramework()

    # Create many responses
    responses = [f"Response {i} with some content and keywords." for i in range(200)]

    start_time = time.time()
    result = framework.evaluate_reasoning_coherence(responses)
    elapsed = time.time() - start_time

    # Should complete in reasonable time (< 10 seconds)
    assert elapsed < 10.0
    assert result.score >= 0.0


def test_topology_large_graph_performance():
    """Test topology performance with large graph."""
    topology = ContextTopology()

    # Create large graph (100 nodes)
    node_count = 100
    for i in range(node_count):
        node = ContextNode(
            id=f"n{i}",
            content=f"Content {i}",
            source="test",
            credibility=0.7,
        )
        topology.add_node(node)
        # Connect to a few neighbors
        if i > 0:
            topology.add_edge(f"n{i-1}", f"n{i}")
        if i > 2:
            topology.add_edge(f"n{i-3}", f"n{i}")

    start_time = time.time()
    cliques = topology.compute_cliques()
    elapsed = time.time() - start_time

    # Should complete in reasonable time (< 2 seconds)
    assert elapsed < 2.0
    assert isinstance(cliques, list)


def test_eval_concurrent_scenarios():
    """Test evaluation handles multiple scenarios concurrently."""
    framework = EvaluationFramework()

    # Run multiple evaluations
    results = []

    # Schema evaluation
    schema_result = framework.evaluate_schema_usage(
        "chain_of_thought",
        [{"input": "Test", "expected": {}, "actual": {}}]
    )
    results.append(schema_result)

    # Coherence evaluation
    coherence_result = framework.evaluate_reasoning_coherence(
        ["Response 1", "Response 2", "Response 3"]
    )
    results.append(coherence_result)

    # Dependency gap evaluation
    gap_result = framework.evaluate_dependency_gap_handling(
        [{"query": "Test", "intermediate_steps": [], "actual_steps": [],
          "final_answer": "", "actual_answer": ""}]
    )
    results.append(gap_result)

    # All should complete successfully
    assert len(results) == 3
    assert all(r.score >= 0.0 for r in results)

