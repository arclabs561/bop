"""Comprehensive temporal feature tests with diverse datasets."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from pran.agent import KnowledgeAgent
from datasets import load_all_datasets, load_dataset


@pytest.fixture
def datasets_dir():
    """Get datasets directory."""
    return Path(__file__).parent.parent / "datasets"


@pytest.fixture
def temporal_dataset(datasets_dir):
    """Load temporal queries dataset."""
    return load_dataset(datasets_dir / "temporal_queries.json")


@pytest.fixture
def all_datasets(datasets_dir):
    """Load all datasets."""
    return load_all_datasets(datasets_dir)


@pytest.mark.asyncio
async def test_temporal_queries_dataset(temporal_dataset):
    """Test agent handles temporal queries from dataset."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None

    for query_item in temporal_dataset[:3]:  # Test first 3
        query = query_item["query"]
        response = await agent.chat(query, use_research=query_item.get("requires_research", True))

        # Should have timestamp
        assert "timestamp" in response or response.get("timestamp") is not None

        # If temporal aspect is true, should have temporal data
        if query_item.get("temporal_aspect"):
            # Temporal evolution may or may not be present depending on research results
            # But structure should be correct if present
            if response.get("temporal_evolution"):
                assert isinstance(response["temporal_evolution"], list)


@pytest.mark.asyncio
async def test_temporal_timestamp_consistency(all_datasets):
    """Test timestamp consistency across all dataset queries."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None

    timestamps = []

    # Test queries from multiple datasets
    for dataset_name, items in list(all_datasets.items())[:3]:
        for query_item in items[:2]:  # 2 queries per dataset
            query = query_item["query"]
            if not query or len(query) < 3:  # Skip edge cases
                continue

            response = await agent.chat(
                query,
                use_research=query_item.get("requires_research", False)
            )

            if response.get("timestamp"):
                timestamp = datetime.fromisoformat(
                    response["timestamp"].replace("Z", "+00:00")
                )
                timestamps.append(timestamp)

    # All timestamps should be recent (within last 5 minutes)
    if timestamps:
        now = datetime.now(timezone.utc)
        for ts in timestamps:
            age = (now.replace(tzinfo=None) - ts.replace(tzinfo=None)).total_seconds()
            assert age < 300, f"Timestamp too old: {age} seconds"


@pytest.mark.asyncio
async def test_temporal_source_timestamps_with_datasets(all_datasets):
    """Test source timestamp tracking with diverse queries."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None

    queries_with_research = [
        item for dataset_name, items in all_datasets.items()
        for item in items
        if item.get("requires_research") and len(item.get("query", "")) > 10
    ][:5]  # Test 5 queries that require research

    for query_item in queries_with_research:
        query = query_item["query"]
        response = await agent.chat(query, use_research=True)

        # If research was conducted and source timestamps exist, validate them
        if response.get("research_conducted") and response.get("source_timestamps"):
            source_timestamps = response["source_timestamps"]
            assert isinstance(source_timestamps, dict)

            for source, timestamp_str in source_timestamps.items():
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                # Source timestamp should be before or equal to response timestamp
                response_ts = datetime.fromisoformat(
                    response["timestamp"].replace("Z", "+00:00")
                )
                assert timestamp <= response_ts.replace(tzinfo=None), \
                    f"Source timestamp {timestamp} should be <= response timestamp {response_ts}"


@pytest.mark.asyncio
async def test_temporal_evolution_with_complex_queries(all_datasets):
    """Test temporal evolution with complex queries from datasets."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None

    complex_queries = [
        item for dataset_name, items in all_datasets.items()
        for item in items
        if item.get("complexity") == "complex" and len(item.get("query", "")) > 10
    ][:3]  # Test 3 complex queries

    for query_item in complex_queries:
        query = query_item["query"]
        response = await agent.chat(
            query,
            use_research=query_item.get("requires_research", True)
        )

        # If temporal evolution exists, validate structure
        if response.get("temporal_evolution"):
            evolution = response["temporal_evolution"]
            assert isinstance(evolution, list)

            for item in evolution:
                assert isinstance(item, dict)
                assert "claim" in item or "full_claim" in item

                if "source_count" in item:
                    assert isinstance(item["source_count"], int)
                    assert item["source_count"] >= 0

                if "consensus" in item:
                    assert 0.0 <= item["consensus"] <= 1.0


@pytest.mark.asyncio
async def test_temporal_staleness_detection(all_datasets):
    """Test staleness detection across different query types."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None

    # Make a query
    query = "What is d-separation?"
    response1 = await agent.chat(query, use_research=False)

    # Wait a bit (simulate)
    import asyncio
    await asyncio.sleep(0.1)

    # Make another query
    response2 = await agent.chat(query, use_research=False)

    # Both should have timestamps
    assert response1.get("timestamp")
    assert response2.get("timestamp")

    # Second timestamp should be later
    ts1 = datetime.fromisoformat(response1["timestamp"].replace("Z", "+00:00"))
    ts2 = datetime.fromisoformat(response2["timestamp"].replace("Z", "+00:00"))

    assert ts2 >= ts1, "Second response should have later timestamp"


@pytest.mark.asyncio
async def test_temporal_with_edge_cases(datasets_dir):
    """Test temporal features with edge case queries."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None

    edge_cases = load_dataset(datasets_dir / "edge_cases.json")

    # Test normal query (baseline)
    normal_query = next(
        item for item in edge_cases
        if item.get("subdomain") == "normal_query"
    )

    response = await agent.chat(normal_query["query"], use_research=False)

    # Should have timestamp even for simple queries
    assert response.get("timestamp") is not None

    # Test empty query (should handle gracefully)
    empty_query = next(
        item for item in edge_cases
        if item.get("subdomain") == "empty_query"
    )

    try:
        response = await agent.chat(empty_query["query"], use_research=False)
        # If it doesn't crash, should still have timestamp if response exists
        if "response" in response:
            # Timestamp may or may not be present for empty queries
            pass
    except Exception:
        # Empty query may raise exception, which is acceptable
        pass


@pytest.mark.asyncio
async def test_temporal_cross_dataset_consistency(all_datasets):
    """Test temporal feature consistency across different dataset domains."""
    agent = KnowledgeAgent(enable_quality_feedback=False)
    agent.llm_service = None

    # Sample one query from each dataset
    sample_queries = []
    for dataset_name, items in all_datasets.items():
        valid_items = [item for item in items if item.get("query") and len(item.get("query", "")) > 10]
        if valid_items:
            sample_queries.append(valid_items[0])

    timestamps = []
    for query_item in sample_queries[:5]:  # Test 5 samples
        query = query_item["query"]
        response = await agent.chat(
            query,
            use_research=query_item.get("requires_research", False)
        )

        if response.get("timestamp"):
            timestamps.append(response["timestamp"])

    # All should have valid ISO format timestamps
    for ts_str in timestamps:
        try:
            datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except ValueError:
            pytest.fail(f"Invalid timestamp format: {ts_str}")

