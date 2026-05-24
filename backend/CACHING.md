# Caching Implementation Guide

## Overview

FinScope AI now includes comprehensive Redis-based caching to improve performance and reduce API costs. The caching system is designed to be:
- **Transparent**: Works automatically without code changes
- **Resilient**: Gracefully handles Redis unavailability
- **Efficient**: Reduces LLM calls, API requests, and computation time

## Architecture

### Cache Components

1. **Query Classification Cache** (`agents/query_router.py`)
   - Caches classification results (IT/Pharma/Unknown)
   - TTL: 1 hour
   - Key: `classify:<hash(query)>`

2. **Document Embeddings Cache** (`rag/embeddings.py`)
   - Caches computed embeddings for documents
   - TTL: 7 days (embeddings don't change)
   - Key: `embedding:<hash(text+model)>`

3. **Research Results Cache** (`api/routes/research.py`)
   - Caches complete research reports
   - TTL: 24 hours
   - Key: `research_result:<hash(query+sector+questions)>`

4. **Future: Query Generation Cache**
   - Will cache generated research queries
   - TTL: 30 minutes

## Setup

### 1. Install Dependencies

Redis dependencies are already in `requirements.txt`:
```
redis==5.0.1
hiredis==2.2.3
```

Install:
```bash
pip install -r requirements.txt
```

### 2. Start Redis

**Option A: Docker Compose (Recommended)**
```bash
docker-compose up -d redis
```

**Option B: Local Redis**
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Windows
# Download from https://redis.io/download
```

### 3. Configure Environment

Set Redis URL in `.env`:
```bash
REDIS_URL=redis://localhost:6379/0
```

Or in Docker:
```bash
REDIS_URL=redis://redis:6379/0
```

### 4. Verify Setup

Check Redis connection:
```bash
redis-cli ping
# Should return: PONG
```

## Cache TTL Configuration

TTL values are defined in `utils/cache.py`:

```python
CACHE_TTL = {
    "classification": 3600,        # 1 hour
    "query_generation": 1800,      # 30 minutes
    "embedding": 86400 * 7,        # 7 days
    "research_result": 3600 * 24,  # 24 hours
    "financial_data": 3600,        # 1 hour
    "web_search": 1800,            # 30 minutes
    "llm_response": 3600,          # 1 hour
}
```

## Usage

### Automatic Caching

Caching works automatically. No code changes needed for:
- Query classification
- Embedding generation
- Research results

### Manual Cache Operations

```python
from utils.cache import get_cache_manager, generate_cache_key, CACHE_TTL

# Get cache manager
cache = await get_cache_manager()

# Generate cache key
key = generate_cache_key("my_prefix", "arg1", "arg2", param="value")

# Get from cache
value = await cache.get(key)

# Set in cache
await cache.set(key, value, ttl=CACHE_TTL["classification"])

# Delete from cache
await cache.delete(key)

# Clear pattern
await cache.clear_pattern("classify:*")
```

## Performance Benefits

### Expected Improvements

1. **Query Classification**
   - First call: ~500ms (LLM call)
   - Cached call: ~5ms (Redis lookup)
   - **99% faster** for repeated queries

2. **Embedding Generation**
   - First call: ~100ms per document
   - Cached call: ~5ms (Redis lookup)
   - **95% faster** for repeated documents

3. **Research Results**
   - First call: 2-5 minutes (full research)
   - Cached call: ~50ms (Redis lookup)
   - **99.9% faster** for identical queries

### Cost Savings

- **LLM Calls**: 40-60% reduction in classification calls
- **API Calls**: 30-50% reduction in repeated research
- **Computation**: 70-80% reduction in embedding computation

## Monitoring

### Cache Hit Rates

Check cache statistics:
```python
from utils.cache import get_cache_manager

cache = await get_cache_manager()

# Get all keys with pattern
keys = await cache.client.keys("classify:*")
print(f"Classification cache entries: {len(keys)}")
```

### Redis CLI Commands

```bash
# Check memory usage
redis-cli info memory

# List all cache keys
redis-cli keys "*"

# Count cache entries
redis-cli keys "classify:*" | wc -l
redis-cli keys "embedding:*" | wc -l
redis-cli keys "research_result:*" | wc -l

# Get cache size
redis-cli dbsize
```

## Troubleshooting

### Redis Connection Issues

**Problem**: `Redis connection failed`

**Solution**:
1. Check Redis is running: `redis-cli ping`
2. Verify REDIS_URL environment variable
3. Check network connectivity (if Docker)
4. System will gracefully degrade (caching disabled, but app works)

### Cache Not Working

**Problem**: No cache hits observed

**Solution**:
1. Verify Redis connection in logs
2. Check cache keys are being generated
3. Verify TTL values are appropriate
4. Check Redis memory limits

### Memory Issues

**Problem**: Redis running out of memory

**Solution**:
1. Adjust `maxmemory` in Redis config (default: 512mb)
2. Adjust `maxmemory-policy` (default: `allkeys-lru`)
3. Reduce TTL values for less critical caches
4. Clear old cache patterns manually

## Best Practices

1. **Cache Key Design**
   - Include all relevant parameters
   - Use consistent hashing
   - Include version numbers if needed

2. **TTL Selection**
   - Short TTL for frequently changing data (web search: 30 min)
   - Long TTL for stable data (embeddings: 7 days)
   - Medium TTL for moderate changes (classification: 1 hour)

3. **Cache Invalidation**
   - Use TTL for automatic expiration
   - Clear patterns when needed (e.g., sector updates)
   - Consider versioning for breaking changes

4. **Monitoring**
   - Track cache hit rates
   - Monitor Redis memory usage
   - Alert on connection failures

## Future Enhancements

1. **Cache Warming**: Pre-populate common queries
2. **Distributed Caching**: Redis Cluster for scale
3. **Cache Analytics**: Dashboard for hit rates
4. **Smart Invalidation**: Event-based cache clearing
5. **Multi-level Caching**: Memory + Redis for ultra-fast access

## Support

For issues or questions:
1. Check logs: `logs/finscope.log`
2. Review Redis logs: `redis-cli monitor`
3. Test connection: `redis-cli ping`

---

**Note**: Caching is designed to gracefully degrade. If Redis is unavailable, the system continues to function normally without caching.
