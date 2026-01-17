"""
Tests for MUSE-based tool selection and aleatoric-aware aggregation.
"""

import pytest

from pran.context_topology import ContextNode
from pran.uncertainty_tool_selection import (
    aggregate_results_with_aleatoric_weighting,
    select_tools_with_muse,
)


class TestMUSEToolSelection:
    """Test MUSE-based tool selection."""

    def test_select_tools_greedy_strategy(self):
        """Should select tools using greedy strategy (maximize diversity)."""
        candidate_tools = ["perplexity_search", "firecrawl_search", "tavily_search"]
        tool_metadata = [
            {"credibility": 0.9, "confidence": 0.9, "epistemic_uncertainty": 0.2},
            {"credibility": 0.7, "confidence": 0.7, "epistemic_uncertainty": 0.4},
            {"credibility": 0.8, "confidence": 0.8, "epistemic_uncertainty": 0.3},
        ]

        selected, metadata = select_tools_with_muse(
            candidate_tools,
            tool_metadata,
            "test subproblem",
            max_tools=2,
            strategy="greedy",
        )

        assert len(selected) <= 2
        assert len(selected) > 0
        assert all(tool in candidate_tools for tool in selected)
        assert "epistemic_uncertainty" in metadata
        assert "total_uncertainty" in metadata
        assert metadata["selection_reason"].startswith("muse_")

    def test_select_tools_conservative_strategy(self):
        """Should select tools using conservative strategy (minimize uncertainty)."""
        candidate_tools = ["perplexity_search", "firecrawl_search"]
        tool_metadata = [
            {"credibility": 0.9, "confidence": 0.9, "epistemic_uncertainty": 0.1},
            {"credibility": 0.6, "confidence": 0.6, "epistemic_uncertainty": 0.5},
        ]

        selected, metadata = select_tools_with_muse(
            candidate_tools,
            tool_metadata,
            "test subproblem",
            max_tools=2,
            strategy="conservative",
        )

        assert len(selected) <= 2
        assert len(selected) > 0
        assert metadata["selection_reason"].startswith("muse_")

    def test_select_tools_empty_candidates(self):
        """Should handle empty candidate list."""
        selected, metadata = select_tools_with_muse(
            [],
            [],
            "test subproblem",
        )

        assert selected == []
        assert metadata["selection_reason"] == "no_candidates"

    def test_select_tools_mismatched_lengths(self):
        """Should handle mismatched tool and metadata lengths."""
        candidate_tools = ["tool1", "tool2", "tool3"]
        tool_metadata = [
            {"credibility": 0.8},
            {"credibility": 0.7},
        ]

        selected, metadata = select_tools_with_muse(
            candidate_tools,
            tool_metadata,
            "test subproblem",
        )

        # Should truncate to minimum length
        assert len(selected) <= min(len(candidate_tools), len(tool_metadata))

    def test_select_tools_respects_max_tools(self):
        """Should respect max_tools limit."""
        candidate_tools = ["tool1", "tool2", "tool3", "tool4", "tool5"]
        tool_metadata = [
            {"credibility": 0.9 - i * 0.1, "confidence": 0.9 - i * 0.1}
            for i in range(5)
        ]

        selected, metadata = select_tools_with_muse(
            candidate_tools,
            tool_metadata,
            "test subproblem",
            max_tools=2,
        )

        assert len(selected) <= 2


class TestAleatoricAwareAggregation:
    """Test aleatoric-aware result aggregation."""

    def test_aggregate_results_basic(self):
        """Should aggregate results with aleatoric weighting."""
        results = [
            {"result": "Result 1", "source": "source1"},
            {"result": "Result 2", "source": "source2"},
        ]
        nodes = [
            ContextNode(
                id="n1",
                content="Result 1",
                source="source1",
                confidence=0.9,
                aleatoric_uncertainty=0.1,  # Low entropy = high weight
            ),
            ContextNode(
                id="n2",
                content="Result 2",
                source="source2",
                confidence=0.6,
                aleatoric_uncertainty=0.4,  # Higher entropy = lower weight
            ),
        ]

        aggregated = aggregate_results_with_aleatoric_weighting(results, nodes)

        assert "aggregated" in aggregated
        assert "weights" in aggregated
        assert len(aggregated["weights"]) == 2
        assert sum(aggregated["weights"]) == pytest.approx(1.0, abs=0.01)
        # Lower entropy should have higher weight
        assert aggregated["weights"][0] > aggregated["weights"][1]

    def test_aggregate_results_empty(self):
        """Should handle empty results."""
        aggregated = aggregate_results_with_aleatoric_weighting([], [])

        assert aggregated["aggregated"] == ""
        assert aggregated["weights"] == []

    def test_aggregate_results_mismatched_lengths(self):
        """Should handle mismatched result and node lengths."""
        results = [{"result": "Result 1"}]
        nodes = [
            ContextNode(id="n1", content="Result 1", source="s1", confidence=0.8),
            ContextNode(id="n2", content="Result 2", source="s2", confidence=0.7),
        ]

        aggregated = aggregate_results_with_aleatoric_weighting(results, nodes)

        # Should use uniform weighting
        assert "aggregated" in aggregated
        assert len(aggregated["weights"]) == len(results)

    def test_aggregate_results_single_result(self):
        """Should handle single result."""
        results = [{"result": "Single result"}]
        nodes = [
            ContextNode(
                id="n1",
                content="Single result",
                source="source1",
                confidence=0.8,
            ),
        ]

        aggregated = aggregate_results_with_aleatoric_weighting(results, nodes)

        assert aggregated["weights"] == [1.0]
        assert "Single result" in aggregated["aggregated"]

    def test_aggregate_results_weights_normalized(self):
        """Weights should sum to 1.0."""
        results = [
            {"result": f"Result {i}"} for i in range(3)
        ]
        nodes = [
            ContextNode(
                id=f"n{i}",
                content=f"Result {i}",
                source=f"source{i}",
                confidence=0.5 + i * 0.1,
                aleatoric_uncertainty=0.3 - i * 0.1,
            )
            for i in range(3)
        ]

        aggregated = aggregate_results_with_aleatoric_weighting(results, nodes)

        assert sum(aggregated["weights"]) == pytest.approx(1.0, abs=0.01)
        assert all(0.0 <= w <= 1.0 for w in aggregated["weights"])

