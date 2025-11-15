# BOP Persistent Caching Strategy

## Overview

BOP now uses persistent caching to reduce API costs and improve response times by caching:
- **Tool results** (MCP tool calls) - 7 day TTL
- **LLM responses** - 3 day TTL
- **Token contexts** - 7 day TTL
- **Sessions** - Persistent (no TTL)

## Why Caching?

### High Overlap Scenarios
1. **Similar queries** - Users often ask similar questions
2. **Tool calls** - Same URLs, same research queries
3. **LLM prompts** - Similar prompts generate similar responses
4. **Token contexts** - Same text processed multiple times
5. **Sessions** - Session continuity across restarts

### Benefits
- ✅ **Cost reduction** - Fewer API calls (LLM, MCP tools)
- ✅ **Faster responses** - Cache hits are instant
- ✅ **Better UX** - Consistent responses for similar queries
- ✅ **Reduced load** - Less pressure on external APIs

## Cache Architecture

### Storage Location
- **Fly.io Volumes**: `/data/cache/` (persistent, encrypted)
- **Local Development**: `./cache/` (ephemeral)

### Cache Structure
```
/data/cache/
├── tools/          # MCP tool results
│   ├── 00/        # Hash-based subdirectories
│   ├── 01/
│   └── ...
├── llm/            # LLM responses
│   ├── 00/
│   └── ...
├── tokens/         # Token contexts
│   ├── 00/
│   └── ...
├── sessions/       # Session data
│   └── ...
└── index.json      # Cache index for fast lookups
```

### Cache Key Strategy
- **Tool results**: `SHA256(tool_name + query + params)`
- **LLM responses**: `SHA256(prompt + backend + model)`
- **Token contexts**: `SHA256(text)`
- **Sessions**: `session_id` (UUID)

## Cache TTLs

| Category | TTL | Reason |
|----------|-----|--------|
| Tool results | 7 days | Research results are relatively stable |
| LLM responses | 3 days | Responses may need updates for latest info |
| Token contexts | 7 days | Token analysis is stable |
| Sessions | Persistent | No TTL, manually managed |

## Cache Management

### Automatic
- **Expiration**: Entries expire based on TTL
- **Eviction**: LRU eviction when cache size limit reached (1GB default)
- **Cleanup**: Expired entries cleaned on access

### Manual
```bash
# Clear specific category
curl -X POST https://bop-wispy-voice-3017.fly.dev/cache/clear?category=tools \
  -H "X-API-Key: YOUR_KEY"

# Clear all cache
curl -X POST https://bop-wispy-voice-3017.fly.dev/cache/clear \
  -H "X-API-Key: YOUR_KEY"

# Get cache stats
curl https://bop-wispy-voice-3017.fly.dev/cache/stats \
  -H "X-API-Key: YOUR_KEY"
```

## Setup

### 1. Create Volume
```bash
# Create 1GB volume (can extend later)
flyctl volumes create bop_cache --size 1 --region iad -a bop-wispy-voice-3017

# Or use setup script
./scripts/setup_cache_volume.sh
```

### 2. Deploy
```bash
# Deploy with volume mount (already configured in fly.toml)
flyctl deploy -a bop-wispy-voice-3017
```

### 3. Verify
```bash
# Check volume is mounted
flyctl ssh console -a bop-wispy-voice-3017 -C "ls -la /data"

# Check cache directory exists
flyctl ssh console -a bop-wispy-voice-3017 -C "ls -la /data/cache"
```

## Cache Behavior

### Cache Hits
- **Tool calls**: Check cache before calling MCP tool
- **LLM calls**: Check cache before calling LLM
- **Token contexts**: Check cache before computing

### Cache Misses
- **Tool calls**: Call MCP tool, cache result
- **LLM calls**: Call LLM, cache response
- **Token contexts**: Compute, cache result

### Cache Writes
- **Atomic**: Write to temp file, then rename
- **Thread-safe**: Uses locks for concurrent access
- **Indexed**: Fast lookups via index.json

## Performance

### Cache Hit Rates (Expected)
- **Tool results**: 30-50% (similar queries, same URLs)
- **LLM responses**: 20-40% (similar prompts)
- **Token contexts**: 40-60% (same text processed)
- **Sessions**: 100% (always loaded from cache)

### Response Time Improvement
- **Cache hit**: <10ms (disk read)
- **Cache miss**: 1-30s (API call + cache write)
- **Overall**: 20-40% faster average response time

## Monitoring

### Cache Stats Endpoint
```bash
curl https://bop-wispy-voice-3017.fly.dev/cache/stats \
  -H "X-API-Key: YOUR_KEY"
```

**Response**:
```json
{
  "cache_dir": "/data/cache",
  "total_size_bytes": 52428800,
  "max_size_bytes": 1073741824,
  "categories": {
    "tools": {
      "count": 150,
      "size_bytes": 15728640
    },
    "llm": {
      "count": 200,
      "size_bytes": 31457280
    },
    "tokens": {
      "count": 50,
      "size_bytes": 5242880
    },
    "sessions": {
      "count": 10,
      "size_bytes": 1048576
    }
  }
}
```

### Metrics Endpoint
Cache stats are also included in `/metrics` endpoint.

## Troubleshooting

### Cache Not Working
1. **Check volume is mounted**:
   ```bash
   flyctl ssh console -a bop-wispy-voice-3017 -C "ls -la /data"
   ```

2. **Check cache directory**:
   ```bash
   flyctl ssh console -a bop-wispy-voice-3017 -C "ls -la /data/cache"
   ```

3. **Check permissions**:
   ```bash
   flyctl ssh console -a bop-wispy-voice-3017 -C "ls -ld /data/cache"
   ```

### Cache Size Issues
- **Too large**: Increase volume size or reduce TTL
- **Too small**: Decrease TTL or clear old entries

### Cache Performance
- **Slow writes**: Check disk I/O (volume performance)
- **Slow reads**: Check index.json (should be small)

## Best Practices

1. **Monitor cache stats** regularly
2. **Clear cache** when needed (e.g., after major updates)
3. **Adjust TTLs** based on data freshness needs
4. **Extend volume** if cache grows (up to 500GB)
5. **Backup volume** for important cached data

## Cost Savings

### Estimated Savings
- **Tool calls**: 30-50% reduction (cache hits)
- **LLM calls**: 20-40% reduction (cache hits)
- **Overall**: 25-35% reduction in API costs

### Volume Cost
- **1GB volume**: ~$0.15/month
- **10GB volume**: ~$1.50/month
- **Cost savings**: Typically 10-100x volume cost

## Migration

### From Ephemeral to Persistent
1. **Create volume**: `flyctl volumes create bop_cache --size 1 -a bop-wispy-voice-3017`
2. **Deploy**: `flyctl deploy -a bop-wispy-voice-3017`
3. **Verify**: Check `/data/cache` exists
4. **Monitor**: Watch cache stats grow

### Cache Warm-up
- Cache builds automatically as users query
- No manual warm-up needed
- First queries populate cache

## Security

- ✅ **Encrypted at rest**: Volumes encrypted by default
- ✅ **Access control**: Cache endpoints require API key
- ✅ **No sensitive data**: Only tool results, LLM responses (no secrets)
- ✅ **TTL expiration**: Old data automatically expires

## Related

- `FLYIO_PERSISTENCE_STRATEGY.md` - General persistence guide
- `TESTING_AND_SECURITY_GUIDE.md` - Testing guide
- `DEPLOYMENT.md` - Deployment guide

