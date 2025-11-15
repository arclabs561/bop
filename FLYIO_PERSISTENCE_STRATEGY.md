# Fly.io Persistence Strategy for BOP

## Current State: Ephemeral Storage

BOP currently uses **ephemeral storage** (no volumes or databases). This is acceptable because:

### Ephemeral Data in BOP
- ✅ **adaptive_learning.json** - Learning patterns (regenerate over time)
- ✅ **quality_history.json** - Quality metrics (can rebuild)
- ✅ **sessions/** - Session data (temporary, can be lost)
- ✅ **eval_results.json** - Evaluation results (can rerun)

**All data can be regenerated** - No critical data loss if ephemeral.

## When to Add Persistence

### Option 1: Fly.io Volumes (Recommended for Simple Persistence)

**Use when**:
- Want faster startup (pre-loaded learning patterns)
- Need session continuity across restarts
- Want historical quality trends

**Setup**:
```bash
# Create volume (1GB default, can extend to 500GB)
flyctl volumes create bop_data --size 1 --region iad -a bop-wispy-voice-3017

# Add to fly.toml
[[mounts]]
  source = "bop_data"
  destination = "/data"
```

**Configuration**:
```toml
# fly.toml
[[mounts]]
  source = "bop_data"
  destination = "/data"

# Update app to use /data for persistent files
```

**Pros**:
- ✅ Simple setup
- ✅ Fast (local NVMe)
- ✅ Encrypted by default
- ✅ Low cost

**Cons**:
- ⚠️ Single machine (one volume per machine)
- ⚠️ Manual backups needed
- ⚠️ No automatic replication

**Recommendation**: Use for single-machine persistence needs.

### Option 2: Fly.io Postgres (Recommended for Production)

**Use when**:
- Need multi-machine access
- Want automatic backups
- Need complex queries
- Production deployment

**Setup**:
```bash
# Create Postgres cluster
flyctl postgres create --name bop-db --region iad --vm-size shared-cpu-1x

# Attach to app
flyctl postgres attach bop-db -a bop-wispy-voice-3017
```

**Configuration**:
- Automatically sets `DATABASE_URL` secret
- Use SQLAlchemy or similar ORM
- Migrations via Alembic

**Pros**:
- ✅ Managed (backups, scaling)
- ✅ Multi-machine access
- ✅ Automatic backups
- ✅ Production-ready

**Cons**:
- ⚠️ Higher cost
- ⚠️ More complexity
- ⚠️ Overkill for simple data

**Recommendation**: Use for production with complex data needs.

### Option 3: LiteFS (Distributed SQLite)

**Use when**:
- Want SQLite compatibility
- Need multi-machine with SQLite
- Want read replicas

**Setup**:
```bash
# Install LiteFS
# Configure in fly.toml
```

**Pros**:
- ✅ SQLite compatibility
- ✅ Multi-machine
- ✅ Read replicas

**Cons**:
- ⚠️ Complexity
- ⚠️ Write to primary only
- ⚠️ Setup overhead

**Recommendation**: Use if you need SQLite with multi-machine.

## Current Recommendation: Stay Ephemeral

**For BOP's current use case**:
- ✅ Ephemeral storage is sufficient
- ✅ No critical data loss
- ✅ Simpler deployment
- ✅ Lower cost
- ✅ Stateless (easier scaling)

**If persistence is needed later**:
1. Start with Fly.io Volumes (simplest)
2. Upgrade to Postgres if multi-machine needed
3. Consider LiteFS if SQLite required

## Data Storage Locations

### Ephemeral (Current)
```
/app/adaptive_learning.json      # Ephemeral, regenerates
/app/quality_history.json       # Ephemeral, rebuilds
/app/sessions/                   # Ephemeral, temporary
/app/eval_results.json           # Ephemeral, can rerun
```

### With Volumes (Future)
```
/data/adaptive_learning.json    # Persistent on volume
/data/quality_history.json      # Persistent on volume
/data/sessions/                  # Persistent on volume
/data/eval_results.json          # Persistent on volume
```

### With Postgres (Future)
```
Database tables:
- adaptive_learning (JSONB)
- quality_history (JSONB)
- sessions (JSONB)
- eval_results (JSONB)
```

## Backup Strategy

### Ephemeral (Current)
- **No backup needed** - Data regenerates
- **Restart behavior**: All data regenerated on startup

### Volumes (If Added)
- **Daily snapshots**: Fly.io automatic (5 days retention)
- **Manual snapshots**: `flyctl volumes snapshots create`
- **Custom backups**: Script to backup `/data` directory

### Postgres (If Added)
- **Automatic backups**: Managed by Fly.io
- **Point-in-time recovery**: Available
- **Manual backups**: `flyctl postgres backup create`

## Configuration Security

### Secrets Management
- ✅ **Secrets in Fly.io**: Not in code or fly.toml
- ✅ **Rotation**: Update via `flyctl secrets set`
- ✅ **Access**: Only via flyctl or app environment

### Environment Variables
- ✅ **In fly.toml**: Non-sensitive config (BOP_USE_CONSTRAINTS, PORT)
- ✅ **Not secrets**: No API keys in fly.toml
- ✅ **Persist**: Across deployments

### Volume Encryption
- ✅ **Default**: Volumes encrypted at rest
- ✅ **No action needed**: Encryption enabled by default

## Performance Considerations

### Ephemeral Storage
- **IOPs**: Max 2000
- **Bandwidth**: Max 8MiB/s
- **Use case**: Sufficient for JSON files, small data

### Volumes
- **shared-cpu-1x**: 4000 IOPs, 16MiB/s
- **performance-1x**: 12000 IOPs, 48MiB/s
- **Use case**: Better for databases, larger files

### Postgres
- **Managed**: Performance handled by Fly.io
- **Scaling**: Can scale compute and storage
- **Use case**: Production workloads

## Migration Path

### From Ephemeral to Volumes
1. Create volume: `flyctl volumes create bop_data --size 1 -a bop-wispy-voice-3017`
2. Add mount to fly.toml
3. Update code to use `/data` directory
4. Deploy
5. Migrate existing data (if any)

### From Ephemeral to Postgres
1. Create Postgres: `flyctl postgres create --name bop-db`
2. Attach to app: `flyctl postgres attach bop-db -a bop-wispy-voice-3017`
3. Add database models
4. Run migrations
5. Update code to use database

## Testing Persistence

### Test Ephemeral Behavior
```bash
# Restart app
flyctl apps restart bop-wispy-voice-3017

# Verify data regenerates
curl ${APP_URL}/health
```

### Test Volume Persistence
```bash
# Create test file on volume
flyctl ssh console -a bop-wispy-voice-3017 -C "echo 'test' > /data/test.txt"

# Restart app
flyctl apps restart bop-wispy-voice-3017

# Verify file persists
flyctl ssh console -a bop-wispy-voice-3017 -C "cat /data/test.txt"
```

## Recommendations

### Current (Ephemeral)
- ✅ **Keep ephemeral** - Sufficient for current needs
- ✅ **No changes needed** - Works well as-is

### Future (If Persistence Needed)
1. **Start simple**: Use Fly.io Volumes
2. **Upgrade if needed**: Move to Postgres for production
3. **Backup strategy**: Implement backups if using volumes
4. **Test migration**: Test data migration before production

## Security Checklist

- ✅ Secrets stored in Fly.io (not in code)
- ✅ Volumes encrypted by default
- ✅ No sensitive data in ephemeral filesystem
- ✅ Configuration in fly.toml (non-sensitive)
- ✅ Environment variables properly managed
- ✅ Backup strategy documented (if using volumes)

