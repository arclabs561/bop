# BOP Testing & Security Guide

## Overview

Comprehensive testing and security validation for BOP deployment on Fly.io, including persistence, configuration, and security testing.

## Test Suites

### 1. Security Tests (Red Team)

**Purpose**: Validate security controls and access restrictions

**Run**:
```bash
# Python tests (most detailed)
uv run pytest tests/test_security_redteam.py -v

# Or via justfile
just test-security
```

**Coverage**:
- ✅ Authentication & authorization
- ✅ Input validation (SQL injection, XSS, command injection)
- ✅ Information disclosure prevention
- ✅ TLS/HTTPS security
- ✅ Rate limiting
- ✅ CORS configuration
- ✅ Tailscale integration

### 2. Fly.io Security Tests

**Purpose**: Test Fly.io-specific security configurations

**Run**:
```bash
# Requires TEST_DEPLOYMENT=1
TEST_DEPLOYMENT=1 uv run pytest tests/test_security_flyio.py -v

# Or via justfile
just test-security-flyio
```

**Coverage**:
- ✅ No public IPs (private deployment)
- ✅ Secrets not exposed
- ✅ HTTPS enforced
- ✅ Health checks configured
- ✅ Auto-stop enabled
- ✅ Configuration security
- ✅ Dockerfile security
- ✅ Rate limiting
- ✅ Tailscale security

### 3. Persistence Tests

**Purpose**: Test persistence options and data storage

**Run**:
```bash
# Requires TEST_DEPLOYMENT=1
TEST_DEPLOYMENT=1 uv run pytest tests/test_persistence_flyio.py -v

# Or via justfile
just test-persistence
```

**Coverage**:
- ✅ Persistence requirements analysis
- ✅ Fly.io volume options
- ✅ Database options
- ✅ Configuration persistence
- ✅ Backup strategy
- ✅ Session persistence
- ✅ Performance implications

### 4. Comprehensive Security Script

**Purpose**: Quick comprehensive security validation

**Run**:
```bash
./scripts/test_security_comprehensive.sh

# Or via justfile
just test-security-comprehensive
```

**Coverage**:
- ✅ Fly.io security configuration
- ✅ Secrets security
- ✅ API security
- ✅ Information disclosure
- ✅ Configuration security
- ✅ Persistence security
- ✅ Rate limiting

### 5. Deployment E2E Tests

**Purpose**: End-to-end deployment validation

**Run**:
```bash
TEST_DEPLOYMENT=1 uv run pytest tests/test_deployment_e2e.py -v -m e2e

# Or via justfile
just test-deployment-e2e
```

**Coverage**:
- ✅ Fly.io authentication
- ✅ App status and health
- ✅ Secrets management
- ✅ IP configuration
- ✅ Endpoint accessibility
- ✅ Deployment scripts

## Running All Tests

### All Security Tests
```bash
just test-security-all
```

### All Deployment Tests
```bash
just test-deployment
just test-deployment-e2e
```

### Quick Security Check
```bash
./scripts/test_security_comprehensive.sh
```

## Test Configuration

### Environment Variables

```bash
# Required for deployment tests
export TEST_DEPLOYMENT=1
export FLY_APP_NAME=bop-wispy-voice-3017
export BOP_APP_URL=https://bop-wispy-voice-3017.fly.dev
export BOP_API_KEY=your-api-key

# Optional
export FLY_API_TOKEN=your-fly-token
```

### Prerequisites

1. **flyctl installed and authenticated**:
   ```bash
   flyctl auth login
   ```

2. **App deployed**:
   ```bash
   flyctl status -a bop-wispy-voice-3017
   ```

3. **API key set** (for API tests):
   ```bash
   flyctl secrets list -a bop-wispy-voice-3017 | grep BOP_API_KEY
   ```

## Security Test Categories

### 1. Authentication & Authorization
- Public endpoints accessible without auth
- Protected endpoints require API key
- Invalid API keys rejected
- Valid API keys accepted

### 2. Input Validation
- SQL injection protection
- XSS (Cross-Site Scripting) protection
- Command injection protection
- Oversized payload handling
- Malformed JSON rejection

### 3. Information Disclosure
- Error messages don't leak file paths
- Server headers don't expose versions
- Debug endpoints not exposed
- Stack traces not exposed
- No sensitive data in responses

### 4. Fly.io Security
- No public IPs
- Secrets not in code
- HTTPS enforced
- Health checks configured
- Auto-stop enabled
- Dockerfile security

### 5. Persistence Security
- No sensitive data in ephemeral
- Session data secure
- Adaptive learning data secure
- Backup strategy documented

### 6. Configuration Security
- Environment variables not exposed
- fly.toml not exposed
- Dockerfile not exposed
- Secrets rotation capability

## Persistence Strategy

### Current: Ephemeral Storage ✅

**Why**: BOP's data can be regenerated
- `adaptive_learning.json` - Regenerates over time
- `quality_history.json` - Can rebuild
- `sessions/` - Temporary, can be lost
- `eval_results.json` - Can rerun

**Benefits**:
- ✅ Simple deployment
- ✅ Lower cost
- ✅ Stateless (easier scaling)
- ✅ No backup needed

### Future Options (If Needed)

#### Option 1: Fly.io Volumes
**Use when**: Want faster startup, session continuity

**Setup**:
```bash
flyctl volumes create bop_data --size 1 --region iad -a bop-wispy-voice-3017
```

**Add to fly.toml**:
```toml
[[mounts]]
  source = "bop_data"
  destination = "/data"
```

**Pros**: Simple, fast, encrypted, low cost
**Cons**: Single machine, manual backups

#### Option 2: Fly.io Postgres
**Use when**: Production, multi-machine, complex queries

**Setup**:
```bash
flyctl postgres create --name bop-db --region iad
flyctl postgres attach bop-db -a bop-wispy-voice-3017
```

**Pros**: Managed, backups, scaling, production-ready
**Cons**: Higher cost, more complexity

#### Option 3: LiteFS
**Use when**: Need SQLite with multi-machine

**Pros**: SQLite compatibility, multi-machine
**Cons**: Complexity, write to primary only

**See**: `FLYIO_PERSISTENCE_STRATEGY.md` for details

## Configuration Security

### Secrets Management ✅

**Current**:
- ✅ Secrets stored in Fly.io (not in code)
- ✅ No secrets in fly.toml
- ✅ No secrets in Dockerfile
- ✅ Rotation via `flyctl secrets set`

**Test**:
```bash
# Verify secrets not in code
grep -r "api_key.*=" --include="*.py" --include="*.toml" src/ fly.toml | grep -v "API_KEY_HEADER"
# Should return nothing
```

### Environment Variables ✅

**Current**:
- ✅ Non-sensitive config in fly.toml (BOP_USE_CONSTRAINTS, PORT)
- ✅ Sensitive config in secrets (API keys)
- ✅ Persist across deployments

### Volume Encryption ✅

**If using volumes**:
- ✅ Encrypted at rest by default
- ✅ No action needed

## Test Results Interpretation

### ✅ PASS
Security control is working correctly

### ⚠️ WARN
Optional security feature not implemented or not critical
- Rate limiting not detected (may still be working)
- Volumes not configured (ephemeral is acceptable)

### ❌ FAIL
Security vulnerability that should be fixed
- Public IPs found
- Secrets exposed in code
- Debug endpoints accessible

## Continuous Testing

### Pre-Deployment
```bash
# Quick security check
./scripts/test_security_comprehensive.sh

# Full security tests
just test-security-all
```

### Post-Deployment
```bash
# Comprehensive validation
TEST_DEPLOYMENT=1 just test-security-flyio
TEST_DEPLOYMENT=1 just test-persistence
```

### CI/CD Integration
```yaml
# Example GitHub Actions
- name: Security Tests
  run: |
    ./scripts/test_security_comprehensive.sh
  env:
    BOP_APP_URL: ${{ secrets.BOP_APP_URL }}
    BOP_API_KEY: ${{ secrets.BOP_API_KEY }}
    FLY_APP_NAME: ${{ secrets.FLY_APP_NAME }}
```

## Troubleshooting

### Tests Fail: "flyctl not found"
```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh
```

### Tests Fail: "Not authenticated"
```bash
# Login to Fly.io
flyctl auth login
```

### Tests Fail: "App not found"
```bash
# Verify app exists
flyctl apps list | grep bop-wispy-voice-3017
```

### Tests Fail: "API key not set"
```bash
# Set API key for testing
export BOP_API_KEY=$(flyctl secrets list -a bop-wispy-voice-3017 | grep BOP_API_KEY | awk '{print $2}')
```

## Best Practices

1. **Run security tests before deployment**
2. **Run comprehensive tests after deployment**
3. **Review test results regularly**
4. **Fix failures immediately**
5. **Document warnings and decisions**
6. **Keep test suite updated**

## Related Documentation

- `SECURITY_TESTING.md` - Detailed security testing guide
- `REDTEAM_README.md` - Red team test documentation
- `FLYIO_PERSISTENCE_STRATEGY.md` - Persistence options
- `DEPLOYMENT.md` - Deployment guide
- `DEPLOYMENT_SETUP_TAILSCALE.md` - Tailscale setup

