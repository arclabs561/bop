"""Persistent caching layer for BOP using Fly.io Volumes.

Caches:
- Tool results (MCP tool calls) - keyed by tool + query/params hash
- LLM responses - keyed by prompt hash
- Token contexts - keyed by text hash
- Session data - already persisted, but uses cache directory
"""

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import threading

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A cache entry with metadata."""
    key: str
    value: Any
    created_at: str
    expires_at: Optional[str] = None
    access_count: int = 0
    last_accessed: Optional[str] = None
    size_bytes: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "key": self.key,
            "value": self.value,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed,
            "size_bytes": self.size_bytes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEntry":
        """Create from dictionary."""
        return cls(
            key=data["key"],
            value=data["value"],
            created_at=data["created_at"],
            expires_at=data.get("expires_at"),
            access_count=data.get("access_count", 0),
            last_accessed=data.get("last_accessed"),
            size_bytes=data.get("size_bytes", 0),
        )
    
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.expires_at is None:
            return False
        try:
            expires = datetime.fromisoformat(self.expires_at)
            return datetime.now(expires.tzinfo) > expires
        except Exception:
            return False
    
    def touch(self):
        """Update access metadata."""
        self.access_count += 1
        self.last_accessed = datetime.utcnow().isoformat()


class PersistentCache:
    """
    Persistent cache using Fly.io Volumes or local filesystem.
    
    Automatically uses /data directory if available (Fly.io Volumes),
    falls back to local cache directory otherwise.
    """
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        default_ttl_hours: int = 24 * 7,  # 7 days default
        max_size_mb: int = 1000,  # 1GB max cache size
    ):
        """
        Initialize persistent cache.
        
        Args:
            cache_dir: Cache directory (defaults to /data/cache or ./cache)
            default_ttl_hours: Default TTL in hours
            max_size_mb: Maximum cache size in MB
        """
        # Determine cache directory
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        elif Path("/data").exists():
            # Fly.io Volume mounted
            self.cache_dir = Path("/data/cache")
            logger.info("Using Fly.io Volume for cache: /data/cache")
        else:
            # Local development
            self.cache_dir = Path("./cache")
            logger.info("Using local cache directory: ./cache")
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.cache_dir / "tools").mkdir(exist_ok=True)
        (self.cache_dir / "llm").mkdir(exist_ok=True)
        (self.cache_dir / "tokens").mkdir(exist_ok=True)
        (self.cache_dir / "sessions").mkdir(exist_ok=True)
        
        self.default_ttl_hours = default_ttl_hours
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self._lock = threading.RLock()
        
        # In-memory index for fast lookups
        self._index: Dict[str, str] = {}  # key -> file path
        self._load_index()
        
        logger.info(f"Persistent cache initialized: {self.cache_dir}")
    
    def _load_index(self):
        """Load cache index from disk."""
        index_file = self.cache_dir / "index.json"
        if index_file.exists():
            try:
                with open(index_file, "r") as f:
                    self._index = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache index: {e}")
                self._index = {}
    
    def _save_index(self):
        """Save cache index to disk."""
        index_file = self.cache_dir / "index.json"
        try:
            with open(index_file, "w") as f:
                json.dump(self._index, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache index: {e}")
    
    def _get_cache_file(self, category: str, key: str) -> Path:
        """Get cache file path for a key."""
        # Use first 2 chars of hash for directory structure
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        subdir = key_hash[:2]
        (self.cache_dir / category / subdir).mkdir(exist_ok=True)
        return self.cache_dir / category / subdir / f"{key_hash}.json"
    
    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """Create a cache key from arguments."""
        # Sort kwargs for consistent keys
        sorted_kwargs = sorted(kwargs.items())
        key_data = {
            "prefix": prefix,
            "args": args,
            "kwargs": sorted_kwargs,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def get(
        self,
        category: str,
        key: str,
        default: Any = None,
    ) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            category: Cache category (tools, llm, tokens, sessions)
            key: Cache key
            default: Default value if not found
            
        Returns:
            Cached value or default
        """
        with self._lock:
            cache_file = self._get_cache_file(category, key)
            
            if not cache_file.exists():
                return default
            
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)
                
                entry = CacheEntry.from_dict(data)
                
                # Check expiration
                if entry.is_expired():
                    cache_file.unlink()
                    if key in self._index:
                        del self._index[key]
                    self._save_index()
                    return default
                
                # Update access metadata
                entry.touch()
                
                # Save updated metadata
                with open(cache_file, "w") as f:
                    json.dump(entry.to_dict(), f, indent=2)
                
                return entry.value
            except Exception as e:
                logger.warning(f"Failed to read cache entry {key}: {e}")
                return default
    
    def set(
        self,
        category: str,
        key: str,
        value: Any,
        ttl_hours: Optional[int] = None,
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            category: Cache category (tools, llm, tokens, sessions)
            key: Cache key
            value: Value to cache
            ttl_hours: TTL in hours (defaults to default_ttl_hours)
            
        Returns:
            True if successful
        """
        with self._lock:
            if ttl_hours is None:
                ttl_hours = self.default_ttl_hours
            
            expires_at = None
            if ttl_hours > 0:
                expires_at = (datetime.utcnow() + timedelta(hours=ttl_hours)).isoformat()
            
            # Estimate size
            value_json = json.dumps(value)
            size_bytes = len(value_json.encode())
            
            # Check cache size limit
            current_size = self._get_cache_size()
            if current_size + size_bytes > self.max_size_bytes:
                # Evict oldest entries
                self._evict_oldest(size_bytes)
            
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.utcnow().isoformat(),
                expires_at=expires_at,
                access_count=0,
                size_bytes=size_bytes,
            )
            
            cache_file = self._get_cache_file(category, key)
            
            try:
                with open(cache_file, "w") as f:
                    json.dump(entry.to_dict(), f, indent=2)
                
                self._index[key] = str(cache_file)
                self._save_index()
                
                return True
            except Exception as e:
                logger.warning(f"Failed to write cache entry {key}: {e}")
                return False
    
    def _get_cache_size(self) -> int:
        """Get total cache size in bytes."""
        total = 0
        for category_dir in ["tools", "llm", "tokens", "sessions"]:
            cat_path = self.cache_dir / category_dir
            if cat_path.exists():
                for file_path in cat_path.rglob("*.json"):
                    try:
                        total += file_path.stat().st_size
                    except Exception:
                        pass
        return total
    
    def _evict_oldest(self, needed_bytes: int):
        """Evict oldest cache entries to free space."""
        # Collect all entries with metadata
        entries = []
        for category_dir in ["tools", "llm", "tokens", "sessions"]:
            cat_path = self.cache_dir / category_dir
            if cat_path.exists():
                for file_path in cat_path.rglob("*.json"):
                    try:
                        with open(file_path, "r") as f:
                            data = json.load(f)
                        entry = CacheEntry.from_dict(data)
                        entry.size_bytes = file_path.stat().st_size
                        entries.append((file_path, entry))
                    except Exception:
                        pass
        
        # Sort by last accessed (oldest first), then by created_at
        entries.sort(key=lambda x: (
            x[1].last_accessed or x[1].created_at,
            x[1].created_at
        ))
        
        # Evict until we have enough space
        freed = 0
        for file_path, entry in entries:
            if freed >= needed_bytes:
                break
            try:
                freed += entry.size_bytes
                file_path.unlink()
                if entry.key in self._index:
                    del self._index[entry.key]
            except Exception:
                pass
        
        self._save_index()
        logger.info(f"Evicted {freed} bytes from cache")
    
    def clear_category(self, category: str):
        """Clear all entries in a category."""
        with self._lock:
            cat_path = self.cache_dir / category
            if cat_path.exists():
                for file_path in cat_path.rglob("*.json"):
                    try:
                        file_path.unlink()
                    except Exception:
                        pass
            
            # Remove from index
            keys_to_remove = [k for k, v in self._index.items() if category in v]
            for key in keys_to_remove:
                del self._index[key]
            
            self._save_index()
    
    def clear_expired(self):
        """Clear all expired entries."""
        with self._lock:
            cleared = 0
            for category_dir in ["tools", "llm", "tokens", "sessions"]:
                cat_path = self.cache_dir / category_dir
                if cat_path.exists():
                    for file_path in cat_path.rglob("*.json"):
                        try:
                            with open(file_path, "r") as f:
                                data = json.load(f)
                            entry = CacheEntry.from_dict(data)
                            if entry.is_expired():
                                file_path.unlink()
                                if entry.key in self._index:
                                    del self._index[entry.key]
                                cleared += 1
                        except Exception:
                            pass
            
            self._save_index()
            if cleared > 0:
                logger.info(f"Cleared {cleared} expired cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            stats = {
                "cache_dir": str(self.cache_dir),
                "total_size_bytes": self._get_cache_size(),
                "max_size_bytes": self.max_size_bytes,
                "categories": {},
            }
            
            for category in ["tools", "llm", "tokens", "sessions"]:
                cat_path = self.cache_dir / category
                if cat_path.exists():
                    count = len(list(cat_path.rglob("*.json")))
                    size = sum(
                        f.stat().st_size
                        for f in cat_path.rglob("*.json")
                        if f.is_file()
                    )
                    stats["categories"][category] = {
                        "count": count,
                        "size_bytes": size,
                    }
            
            return stats


# Global cache instance
_cache_instance: Optional[PersistentCache] = None


def get_cache() -> PersistentCache:
    """Get global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = PersistentCache()
    return _cache_instance


def cache_tool_result(
    tool: str,
    query: str,
    params: Dict[str, Any],
    result: Any,
    ttl_hours: int = 24 * 7,  # 7 days for tool results
) -> bool:
    """Cache a tool result."""
    cache = get_cache()
    key = cache._make_key("tool", tool, query, **params)
    return cache.set("tools", key, result, ttl_hours=ttl_hours)


def get_cached_tool_result(
    tool: str,
    query: str,
    params: Dict[str, Any],
) -> Optional[Any]:
    """Get cached tool result."""
    cache = get_cache()
    key = cache._make_key("tool", tool, query, **params)
    return cache.get("tools", key)


def cache_llm_response(
    prompt: str,
    model: str,
    response: Any,
    ttl_hours: int = 24 * 3,  # 3 days for LLM responses
) -> bool:
    """Cache an LLM response."""
    cache = get_cache()
    key = cache._make_key("llm", prompt, model)
    return cache.set("llm", key, response, ttl_hours=ttl_hours)


def get_cached_llm_response(
    prompt: str,
    model: str,
) -> Optional[Any]:
    """Get cached LLM response."""
    cache = get_cache()
    key = cache._make_key("llm", prompt, model)
    return cache.get("llm", key)


def cache_token_context(
    text: str,
    context: Any,
    ttl_hours: int = 24 * 7,  # 7 days for token contexts
) -> bool:
    """Cache a token context."""
    cache = get_cache()
    key = cache._make_key("tokens", text)
    return cache.set("tokens", key, context, ttl_hours=ttl_hours)


def get_cached_token_context(
    text: str,
) -> Optional[Any]:
    """Get cached token context."""
    cache = get_cache()
    key = cache._make_key("tokens", text)
    return cache.get("tokens", key)

