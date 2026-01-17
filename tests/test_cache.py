"""Tests for persistent caching system."""

import shutil
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from pran.cache import (
    CacheEntry,
    PersistentCache,
    cache_llm_response,
    cache_token_context,
    cache_tool_result,
    get_cached_llm_response,
    get_cached_token_context,
    get_cached_tool_result,
)


class TestCacheEntry:
    """Test CacheEntry dataclass."""

    def test_cache_entry_creation(self):
        """Test creating a cache entry."""
        entry = CacheEntry(
            key="test_key",
            value={"test": "data"},
            created_at=datetime.utcnow().isoformat(),
        )
        assert entry.key == "test_key"
        assert entry.value == {"test": "data"}
        assert entry.access_count == 0

    def test_cache_entry_expiration(self):
        """Test cache entry expiration."""
        # Not expired
        entry = CacheEntry(
            key="test",
            value="data",
            created_at=datetime.utcnow().isoformat(),
            expires_at=None,
        )
        assert not entry.is_expired()

        # Expired
        expired_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        entry = CacheEntry(
            key="test",
            value="data",
            created_at=expired_time,
            expires_at=(datetime.utcnow() - timedelta(minutes=1)).isoformat(),
        )
        assert entry.is_expired()

    def test_cache_entry_touch(self):
        """Test updating access metadata."""
        entry = CacheEntry(
            key="test",
            value="data",
            created_at=datetime.utcnow().isoformat(),
        )
        initial_count = entry.access_count
        entry.touch()
        assert entry.access_count == initial_count + 1
        assert entry.last_accessed is not None

    def test_cache_entry_serialization(self):
        """Test cache entry serialization."""
        entry = CacheEntry(
            key="test",
            value={"nested": "data"},
            created_at=datetime.utcnow().isoformat(),
            expires_at=(datetime.utcnow() + timedelta(hours=1)).isoformat(),
        )

        # Convert to dict and back
        data = entry.to_dict()
        restored = CacheEntry.from_dict(data)

        assert restored.key == entry.key
        assert restored.value == entry.value
        assert restored.created_at == entry.created_at
        assert restored.expires_at == entry.expires_at


class TestPersistentCache:
    """Test PersistentCache class."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def cache(self, temp_cache_dir):
        """Create cache instance."""
        return PersistentCache(cache_dir=temp_cache_dir, max_size_mb=10)

    def test_cache_initialization(self, cache):
        """Test cache initialization."""
        assert cache.cache_dir.exists()
        assert (cache.cache_dir / "tools").exists()
        assert (cache.cache_dir / "llm").exists()
        assert (cache.cache_dir / "tokens").exists()
        assert (cache.cache_dir / "sessions").exists()

    def test_cache_set_get(self, cache):
        """Test setting and getting cache values."""
        # Set value
        success = cache.set("tools", "test_key", {"result": "data"})
        assert success

        # Get value
        value = cache.get("tools", "test_key")
        assert value == {"result": "data"}

    def test_cache_miss(self, cache):
        """Test cache miss returns default."""
        value = cache.get("tools", "nonexistent", default="default")
        assert value == "default"

    def test_cache_expiration(self, cache):
        """Test cache expiration."""
        # Set with short TTL
        cache.set("tools", "expiring", {"data": "test"}, ttl_hours=0.0001)  # ~0.36 seconds

        # Should be available immediately
        assert cache.get("tools", "expiring") is not None

        # Wait for expiration
        time.sleep(1)

        # Should be expired
        assert cache.get("tools", "expiring") is None

    def test_cache_key_generation(self, cache):
        """Test cache key generation."""
        key1 = cache._make_key("tool", "perplexity", "query1", param1="value1")
        key2 = cache._make_key("tool", "perplexity", "query1", param1="value1")
        key3 = cache._make_key("tool", "perplexity", "query2", param1="value1")

        # Same inputs should generate same key
        assert key1 == key2

        # Different inputs should generate different keys
        assert key1 != key3

    def test_cache_eviction(self, cache):
        """Test cache eviction when size limit reached."""
        # Set max size to small value
        cache.max_size_bytes = 1024  # 1KB

        # Add entries until eviction
        for i in range(10):
            large_data = {"data": "x" * 200}  # ~200 bytes each
            cache.set("tools", f"key_{i}", large_data)

        # Should have evicted some entries
        stats = cache.get_stats()
        assert stats["total_size_bytes"] <= cache.max_size_bytes

    def test_cache_clear_category(self, cache):
        """Test clearing a cache category."""
        # Add entries to multiple categories
        cache.set("tools", "key1", {"data": "test1"})
        cache.set("llm", "key2", {"data": "test2"})

        # Clear one category
        cache.clear_category("tools")

        # Tools should be empty, llm should still have data
        assert cache.get("tools", "key1") is None
        assert cache.get("llm", "key2") == {"data": "test2"}

    def test_cache_stats(self, cache):
        """Test cache statistics."""
        # Add some entries
        cache.set("tools", "key1", {"data": "test1"})
        cache.set("llm", "key2", {"data": "test2"})

        stats = cache.get_stats()
        assert "cache_dir" in stats
        assert "total_size_bytes" in stats
        assert "max_size_bytes" in stats
        assert "categories" in stats
        assert "tools" in stats["categories"]
        assert "llm" in stats["categories"]


class TestCacheHelpers:
    """Test cache helper functions."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_cache_tool_result(self, temp_cache_dir, monkeypatch):
        """Test caching tool results."""
        # Override global cache instance
        cache = PersistentCache(cache_dir=temp_cache_dir)
        monkeypatch.setattr("pran.cache._cache_instance", cache)

        # Cache a tool result
        result = {"tool": "perplexity", "query": "test", "result": "data"}
        success = cache_tool_result("perplexity_search", "test query", {"limit": 5}, result)
        assert success

        # Retrieve cached result
        cached = get_cached_tool_result("perplexity_search", "test query", {"limit": 5})
        assert cached == result

    def test_cache_llm_response(self, temp_cache_dir, monkeypatch):
        """Test caching LLM responses."""
        cache = PersistentCache(cache_dir=temp_cache_dir)
        monkeypatch.setattr("pran.cache._cache_instance", cache)

        # Cache LLM response
        response = "This is a test response"
        success = cache_llm_response("test prompt", "anthropic", response)
        assert success

        # Retrieve cached response
        cached = get_cached_llm_response("test prompt", "anthropic")
        assert cached == response

    def test_cache_token_context(self, temp_cache_dir, monkeypatch):
        """Test caching token contexts."""
        cache = PersistentCache(cache_dir=temp_cache_dir)
        monkeypatch.setattr("pran.cache._cache_instance", cache)

        # Cache token context
        context = {"tokens": ["test", "context"], "importance": [0.5, 0.3]}
        success = cache_token_context("test text", context)
        assert success

        # Retrieve cached context
        cached = get_cached_token_context("test text")
        assert cached == context


class TestCacheIntegration:
    """Integration tests for cache with real scenarios."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_tool_result_caching_workflow(self, temp_cache_dir):
        """Test complete workflow for tool result caching."""
        cache = PersistentCache(cache_dir=temp_cache_dir)

        # Simulate tool call
        tool = "perplexity_search"
        query = "What is d-separation?"
        params = {"max_results": 5}
        result = {
            "tool": tool,
            "query": query,
            "result": "D-separation is a criterion...",
            "sources": ["source1", "source2"],
        }

        # Cache result
        cache.set("tools", cache._make_key("tool", tool, query, **params), result)

        # Retrieve cached result
        cached = cache.get("tools", cache._make_key("tool", tool, query, **params))
        assert cached == result
        assert cached["sources"] == ["source1", "source2"]

    def test_llm_response_caching_workflow(self, temp_cache_dir):
        """Test complete workflow for LLM response caching."""
        cache = PersistentCache(cache_dir=temp_cache_dir)

        # Simulate LLM call
        prompt = "Explain d-separation in causal inference."
        backend = "anthropic"
        response = "D-separation is a criterion for determining..."

        # Cache response
        cache.set("llm", cache._make_key("llm", prompt, backend), response)

        # Retrieve cached response
        cached = cache.get("llm", cache._make_key("llm", prompt, backend))
        assert cached == response

    def test_cache_persistence(self, temp_cache_dir):
        """Test that cache persists across instances."""
        # Create first cache instance and add data
        cache1 = PersistentCache(cache_dir=temp_cache_dir)
        cache1.set("tools", "test_key", {"data": "persistent"})

        # Create second cache instance (simulating restart)
        cache2 = PersistentCache(cache_dir=temp_cache_dir)

        # Should be able to retrieve data
        value = cache2.get("tools", "test_key")
        assert value == {"data": "persistent"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

