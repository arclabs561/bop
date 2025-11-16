# Security Testing Guide

## Overview

Comprehensive, rerunnable security tests to validate deployment security posture.

## Quick Start

```bash
# Fastest check (3 tests, ~5 seconds)
./scripts/redteam_quick.sh

# Basic tests (13 tests, ~30 seconds)
./scripts/redteam_test.sh

# Comprehensive tests (detailed report)
./scripts/redteam_comprehensive.sh

# Python tests (most detailed, pytest)
uv run pytest tests/test_security_redteam.py -v
```

## Test Suites

### 1. Quick Security Check (`redteam_quick.sh`)

**Purpose**: Fast validation that core security is working  
**Duration**: ~5 seconds  
**Tests**: 3 critical checks

```bash
./scripts/redteam_quick.sh
```

**Checks**:
- Health endpoint accessible
- Authentication required
- Valid API key works

### 2. Basic Security Tests (`redteam_test.sh`)

**Purpose**: Comprehensive security validation  
**Duration**: ~30-60 seconds  
**Tests**: 13 security checks

```bash
./scripts/redteam_test.sh
```

**Checks**:
- Authentication & authorization
- Input validation (SQL injection, XSS, command injection)
- Oversized payload handling
- Malformed JSON rejection
- Error message security
- HTTPS enforcement
- Server header security
- Debug endpoint security

### 3. Comprehensive Tests (`redteam_comprehensive.sh`)

**Purpose**: Detailed security assessment with report  
**Duration**: ~60-120 seconds  
**Tests**: 20+ security checks  
**Output**: Timestamped report file

```bash
./scripts/redteam_comprehensive.sh
# Report saved to: redteam_report_YYYYMMDD_HHMMSS.txt
```

**Additional Checks**:
- Detailed error analysis
- Response content validation
- Multiple attack vectors
- Rate limiting validation

### 4. Python Tests (`test_security_redteam.py`)

**Purpose**: Most detailed, programmatic tests  
**Duration**: ~30-60 seconds  
**Tests**: 20+ test cases

```bash
uv run pytest tests/test_security_redteam.py -v
```

**Test Classes**:
- `TestAuthentication` - Auth & authorization
- `TestInputValidation` - Input sanitization
- `TestErrorHandling` - Error disclosure prevention
- `TestRateLimiting` - Service stability
- `TestCORS` - CORS configuration
- `TestInformationDisclosure` - Info leak prevention
- `TestTLS` - TLS/HTTPS security
- `TestTailscaleIntegration` - Tailscale connectivity

## Test Coverage

### Authentication & Authorization ✅
- Public endpoints accessible without auth
- Protected endpoints require API key
- Invalid API keys rejected (401)
- Valid API keys accepted (200)
- All protected endpoints verified

### Input Validation ✅
- SQL injection attempts blocked
- XSS attempts sanitized
- Command injection prevented
- Oversized payloads handled gracefully
- Malformed JSON rejected
- Missing required fields handled

### Information Disclosure ✅
- Error messages don't leak file paths
- Server headers don't expose versions
- Debug endpoints not exposed
- Stack traces not exposed
- No sensitive info in responses

### TLS/HTTPS ✅
- HTTPS enforced (HTTP redirects)
- TLS 1.2+ used
- Secure connections validated

### Rate Limiting ✅
- Rapid requests handled
- Service stability maintained
- No crashes under load

## Running Tests

### Before Deployment
```bash
# Quick validation
./scripts/redteam_quick.sh
```

### After Deployment
```bash
# Comprehensive validation
./scripts/redteam_comprehensive.sh

# Review report
cat redteam_report_*.txt
```

### Continuous Testing
```bash
# Add to CI/CD pipeline
- name: Security Tests
  run: ./scripts/redteam_test.sh
  env:
    BOP_APP_URL: ${{ secrets.BOP_APP_URL }}
    BOP_API_KEY: ${{ secrets.BOP_API_KEY }}
```

### Scheduled Testing
```bash
# Daily security validation
0 0 * * * cd /path/to/bop && ./scripts/redteam_comprehensive.sh
```

## Customization

### Environment Variables

```bash
# Custom app URL
export BOP_APP_URL=https://your-app.fly.dev

# Custom API key
export BOP_API_KEY=your-api-key

# Run tests
./scripts/redteam_test.sh
```

### Test Configuration

Edit test files to customize:
- `scripts/redteam_test.sh` - Basic tests
- `scripts/redteam_comprehensive.sh` - Comprehensive tests
- `tests/test_security_redteam.py` - Python tests

## Interpreting Results

### ✅ PASS
Security control is working correctly. No action needed.

### ⚠️ WARN
Optional security feature not implemented or not critical. Review if needed.

### ❌ FAIL
Security vulnerability detected. **Should be fixed immediately.**

## Common Issues

### Tests Timeout
- **Cause**: App not responding or slow
- **Fix**: Check app status, increase timeouts

### Authentication Fails
- **Cause**: API key incorrect or not set
- **Fix**: Verify `BOP_API_KEY` environment variable

### False Positives
- **Cause**: Expected behavior differs from test
- **Fix**: Review test logic, adjust if needed

## Best Practices

1. **Run regularly**: After each deployment
2. **Review reports**: Check detailed reports
3. **Fix failures**: Address issues promptly
4. **Update tests**: Add tests for new features
5. **Document exceptions**: Note expected failures

## Integration

### CI/CD Pipeline
```yaml
- name: Security Tests
  run: |
    ./scripts/redteam_test.sh
  env:
    BOP_APP_URL: ${{ secrets.BOP_APP_URL }}
    BOP_API_KEY: ${{ secrets.BOP_API_KEY }}
```

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-push
./scripts/redteam_quick.sh || exit 1
```

### Monitoring
```bash
# Daily security report
0 0 * * * cd /path/to/bop && \
  ./scripts/redteam_comprehensive.sh && \
  mail -s "Security Report" admin@example.com < redteam_report_*.txt
```

## Related Documentation

- `REDTEAM_README.md` - Complete red team guide
- `PRIVATE_DEPLOYMENT.md` - Security configuration
- `FLY_COMMANDS.md` - Fly.io CLI reference

