# Deployment Test Coverage

This document outlines the test coverage for all deployment-related functionality.

## Test Files

### 1. `test_server_deployment.py` (Unit Tests)
**Purpose**: Tests server endpoints, API authentication, and configuration validation.

**Coverage**:
- ✅ Server endpoints (root, health, chat, constraints, metrics)
- ✅ API key authentication (with/without key, valid/invalid keys)
- ✅ Response format validation
- ✅ Deployment configuration (fly.toml, Dockerfile)
- ✅ Deployment scripts existence and structure
- ✅ Secret validation logic (unit tests)

**Key Test Classes**:
- `TestServerEndpoints` - HTTP endpoint tests
- `TestAPIKeyAuthentication` - Authentication logic tests
- `TestDeploymentConfiguration` - Configuration validation
- `TestSecretValidation` - Secret validation logic
- `TestDeploymentVerification` - Verification logic
- `TestDeploymentScripts` - Script structure tests

### 2. `test_deployment_scripts.py` (Unit Tests)
**Purpose**: Tests deployment script structure, logic, and properties.

**Coverage**:
- ✅ Script existence and executability
- ✅ Script structure (shebang, error handling)
- ✅ Script logic validation
- ✅ Property-based tests for consistency
- ✅ Error handling verification

**Key Test Classes**:
- `TestDeploymentScriptsStructure` - Script structure tests
- `TestDeployScript` - deploy_fly.sh logic
- `TestVerifyScript` - verify_deployment.sh logic
- `TestValidateScript` - validate_secrets.sh logic
- `TestMakePrivateScript` - make_private.sh logic
- `TestTailscaleStartScript` - tailscale-start.sh logic
- `TestDeploymentScriptProperties` - Property-based tests

### 3. `test_deployment_flow.py` (Unit Tests)
**Purpose**: Tests end-to-end deployment flows and configuration consistency.

**Coverage**:
- ✅ Deployment flow (validation → deploy → verification)
- ✅ Configuration consistency (Dockerfile ↔ fly.toml ↔ scripts)
- ✅ Validation flow
- ✅ Verification flow

**Key Test Classes**:
- `TestDeploymentFlow` - End-to-end flow tests
- `TestDeploymentConfigurationFlow` - Configuration validation
- `TestDeploymentValidationFlow` - Validation flow tests
- `TestDeploymentVerificationFlow` - Verification flow tests

### 4. `test_deployment_e2e.py` (E2E Tests) ⭐ NEW
**Purpose**: End-to-end tests using actual flyctl commands and HTTP requests.

**Coverage**:
- ✅ flyctl authentication and commands
- ✅ App status and configuration via flyctl
- ✅ Secrets management via flyctl
- ✅ Actual HTTP endpoint testing
- ✅ Response time validation
- ✅ Full deployment script execution
- ✅ Configuration consistency with actual deployment
- ✅ Optional Fly Python SDK integration

**Key Test Classes**:
- `TestDeploymentE2E` - flyctl command tests
- `TestDeployedEndpointsE2E` - HTTP endpoint tests
- `TestDeploymentFlySDKE2E` - Fly SDK tests (optional)
- `TestDeploymentFlowE2E` - Full flow tests
- `TestDeploymentConfigurationE2E` - Configuration validation

**Requirements**:
- `TEST_DEPLOYMENT=1` environment variable
- `flyctl` installed and authenticated
- Optional: `FLY_API_TOKEN` for SDK tests
- Optional: `USE_FLY_SDK=1` to enable SDK tests

## Test Categories

### Unit Tests
- Server endpoint responses
- API key authentication logic
- Configuration file parsing
- Script structure validation
- Flow logic validation

### Integration Tests
- Configuration consistency
- Script chaining
- Flow validation

### E2E Tests
- Actual flyctl command execution
- Real HTTP endpoint testing
- Full deployment script execution
- Actual deployment validation

## Running Tests

### Run All Deployment Tests (Unit)
```bash
pytest tests/test_server_deployment.py tests/test_deployment_scripts.py tests/test_deployment_flow.py -v
```

### Run E2E Tests (Requires Deployment)
```bash
# Set environment variables
export TEST_DEPLOYMENT=1
export FLY_APP_NAME=bop-wispy-voice-3017
export BOP_APP_URL=https://bop-wispy-voice-3017.fly.dev

# Run e2e tests
pytest tests/test_deployment_e2e.py -v -m e2e
```

### Run by Category
```bash
# Server endpoint tests
pytest tests/test_server_deployment.py::TestServerEndpoints -v

# Script tests
pytest tests/test_deployment_scripts.py -v

# Flow tests
pytest tests/test_deployment_flow.py -v

# E2E tests
TEST_DEPLOYMENT=1 pytest tests/test_deployment_e2e.py -v
```

### Run via Test Runner
```bash
# Run deployment category (unit tests)
python tests/run_all_tests.py --category deployment

# Run deployment e2e category
TEST_DEPLOYMENT=1 python tests/run_all_tests.py --category deployment_e2e

# Run server category
python tests/run_all_tests.py --category server
```

### Run via Just
```bash
# Unit tests
just test-deployment

# E2E tests (requires TEST_DEPLOYMENT=1)
just test-deployment-e2e

# Server tests
just test-server
```

## Coverage Summary

### Server Endpoints (Unit + E2E)
- ✅ `/` (root) - Service info
- ✅ `/health` - Health check
- ✅ `/chat` - Chat endpoint (with/without API key)
- ✅ `/constraints/status` - Constraint solver status
- ✅ `/metrics` - System metrics

### API Authentication (Unit + E2E)
- ✅ No API key required (when BOP_API_KEY not set)
- ✅ Valid API key accepted
- ✅ Invalid API key rejected
- ✅ Missing API key rejected (when required)

### Configuration Files (Unit + E2E)
- ✅ `fly.toml` - Valid TOML, required fields, health checks
- ✅ `Dockerfile` - Required stages, file copies, port exposure
- ✅ Configuration consistency between files
- ✅ Configuration matches actual deployment (E2E)

### Deployment Scripts (Unit + E2E)
- ✅ `deploy_fly.sh` - Structure, flyctl checks, flow
- ✅ `verify_deployment.sh` - Endpoint checks, waiting logic
- ✅ `validate_secrets.sh` - Secret validation logic
- ✅ `make_private.sh` - IP release logic
- ✅ `tailscale-start.sh` - Tailscale and server startup
- ✅ Script execution (E2E)

### Deployment Flow (Unit + E2E)
- ✅ Validation runs before deployment
- ✅ Verification runs after deployment
- ✅ Scripts chain correctly
- ✅ Configuration consistency
- ✅ Full flow execution (E2E)

### Fly.io Integration (E2E)
- ✅ flyctl authentication
- ✅ App status retrieval
- ✅ Secrets management
- ✅ IP address management
- ✅ Logs retrieval
- ✅ Optional Fly Python SDK

## Test Execution Strategy

### Local Development
1. Run unit tests: `just test-deployment`
2. Run server tests: `just test-server`
3. E2E tests require actual deployment setup

### CI/CD Pipeline
1. Always run unit tests
2. Run E2E tests if `TEST_DEPLOYMENT=1` is set
3. E2E tests require:
   - `flyctl` installed
   - Fly.io authentication
   - App deployed and accessible

### Pre-Deployment
1. Run all unit tests
2. Validate configuration
3. Check script structure

### Post-Deployment
1. Run E2E tests
2. Verify endpoints
3. Check deployment configuration

## Gaps and Future Work

### Not Yet Tested
- Actual deployment process (would deploy new app)
- Rollback process
- Scaling operations
- Multi-region deployment

### Could Be Enhanced
- More detailed flyctl command testing
- Performance benchmarks
- Load testing
- Security scanning integration

## Integration with CI/CD

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Deployment Unit Tests
  run: |
    pytest tests/test_server_deployment.py tests/test_deployment_scripts.py tests/test_deployment_flow.py -v

- name: Run Deployment E2E Tests
  if: env.TEST_DEPLOYMENT == '1'
  env:
    TEST_DEPLOYMENT: 1
    FLY_APP_NAME: bop-wispy-voice-3017
    BOP_APP_URL: https://bop-wispy-voice-3017.fly.dev
    FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
  run: |
    pytest tests/test_deployment_e2e.py -v -m e2e
```

## Notes

- **Unit tests** validate structure, logic, and configuration without requiring actual deployment
- **E2E tests** require actual Fly.io deployment and are marked with `@pytest.mark.e2e`
- E2E tests are skipped unless `TEST_DEPLOYMENT=1` is set
- Fly Python SDK tests are optional and require `USE_FLY_SDK=1` and SDK installation
- All tests use `requests` library for HTTP testing (included in dev dependencies)
