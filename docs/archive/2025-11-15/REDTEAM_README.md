# Red Team Security Tests

Comprehensive, rerunnable security tests for the BOP service deployment.

## Quick Run

### Basic Tests (Fast)
```bash
# Run basic security tests
./scripts/redteam_test.sh

# Or with custom URL/key
BOP_APP_URL=https://your-app.fly.dev \
BOP_API_KEY=your-key \
./scripts/redteam_test.sh
```

### Comprehensive Tests (Detailed)
```bash
# Run comprehensive tests with detailed report
./scripts/redteam_comprehensive.sh

# Report saved to: redteam_report_YYYYMMDD_HHMMSS.txt
```

### Python Tests (Most Detailed)
```bash
# Run pytest-based tests
uv run pytest tests/test_security_redteam.py -v

# With custom URL
BOP_APP_URL=https://your-app.fly.dev \
BOP_API_KEY=your-key \
uv run pytest tests/test_security_redteam.py -v
```

## Test Coverage

### Authentication & Authorization
- ✅ Health endpoint accessible without auth
- ✅ Protected endpoints require API key
- ✅ Invalid API keys rejected
- ✅ Valid API keys accepted
- ✅ All protected endpoints verified

### Input Validation
- ✅ SQL injection protection
- ✅ XSS (Cross-Site Scripting) protection
- ✅ Command injection protection
- ✅ Oversized payload handling
- ✅ Malformed JSON rejection
- ✅ Missing required fields handling

### Information Disclosure
- ✅ Error messages don't leak file paths
- ✅ Server headers don't expose versions
- ✅ Debug endpoints not exposed
- ✅ Stack traces not exposed

### TLS/HTTPS
- ✅ HTTPS enforcement
- ✅ TLS version security
- ✅ Secure connection validation

### Rate Limiting
- ✅ Rapid request handling
- ✅ Service stability under load

### Tailscale Integration
- ✅ Tailscale hostname accessibility (if configured)

## Test Results

### Expected Results
- **All tests should pass** for a secure deployment
- **Warnings** may appear for optional features (e.g., rate limiting)
- **Failures** indicate security issues that should be addressed

### Interpreting Results

**✅ PASS**: Security control is working correctly

**⚠️ WARN**: Optional security feature not implemented or not critical

**❌ FAIL**: Security vulnerability that should be fixed

## Running Tests Regularly

### CI/CD Integration
```yaml
# Example GitHub Actions
- name: Security Tests
  run: |
    ./scripts/redteam_test.sh
  env:
    BOP_APP_URL: ${{ secrets.BOP_APP_URL }}
    BOP_API_KEY: ${{ secrets.BOP_API_KEY }}
```

### Scheduled Testing
```bash
# Run daily security tests
0 0 * * * cd /path/to/bop && ./scripts/redteam_comprehensive.sh
```

### Manual Testing
```bash
# Before deployment
./scripts/redteam_test.sh

# After deployment
./scripts/redteam_comprehensive.sh

# Review report
cat redteam_report_*.txt
```

## Customization

### Environment Variables
- `BOP_APP_URL`: Target application URL (default: https://bop-wispy-voice-3017.fly.dev)
- `BOP_API_KEY`: Valid API key for testing (default: from deployment)

### Adding New Tests

1. **Shell Script**: Add to `scripts/redteam_test.sh` or `scripts/redteam_comprehensive.sh`
2. **Python Tests**: Add to `tests/test_security_redteam.py`

Example:
```python
def test_new_security_control(self):
    """Test new security feature."""
    response = requests.get(f"{APP_URL}/endpoint")
    assert response.status_code == expected_code
```

## Security Test Categories

### 1. Authentication Tests
Verify API key authentication works correctly:
- No auth → 401
- Invalid key → 401
- Valid key → 200

### 2. Authorization Tests
Verify endpoint access control:
- Public endpoints accessible
- Protected endpoints require auth
- Admin endpoints restricted

### 3. Input Validation Tests
Verify input sanitization:
- SQL injection attempts blocked
- XSS attempts sanitized
- Command injection prevented
- Oversized payloads handled

### 4. Information Disclosure Tests
Verify no sensitive info leaked:
- No file paths in errors
- No version info in headers
- No debug endpoints exposed
- No stack traces exposed

### 5. TLS/HTTPS Tests
Verify secure connections:
- HTTPS enforced
- TLS 1.2+ used
- No insecure redirects

### 6. Rate Limiting Tests
Verify service stability:
- Rapid requests handled
- No service crashes
- Graceful degradation

## Troubleshooting

### Tests Failing
1. Check app is running: `flyctl status -a bop-wispy-voice-3017`
2. Verify API key: `flyctl secrets list -a bop-wispy-voice-3017`
3. Check logs: `flyctl logs -a bop-wispy-voice-3017 --no-tail`

### Timeout Issues
- Increase timeout in test scripts
- Check network connectivity
- Verify app is responding

### False Positives
- Some tests may fail due to expected behavior
- Review test logic and adjust if needed
- Document expected failures

## Best Practices

1. **Run regularly**: Test after each deployment
2. **Review reports**: Check detailed reports for issues
3. **Fix failures**: Address security issues promptly
4. **Update tests**: Add tests for new features
5. **Document exceptions**: Note any expected test failures

## Related Documentation

- `PRIVATE_DEPLOYMENT.md` - Security configuration
- `TAILSCALE_FLY_SETUP.md` - Tailscale integration
- `FLY_COMMANDS.md` - Fly.io CLI reference

