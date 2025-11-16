#!/usr/bin/env python3
"""
Validate deployment configuration files.
Steers toward correct deployment setup.
"""

import sys
from pathlib import Path

# Try to import TOML parser (tomli for Python <3.11, tomllib for Python 3.11+)
try:
    import tomllib  # Python 3.11+
    TOML_AVAILABLE = True
    TOML_LOAD = lambda f: tomllib.load(f)
except ImportError:
    try:
        import tomli  # Python <3.11
        TOML_AVAILABLE = True
        TOML_LOAD = lambda f: tomli.load(f)
    except ImportError:
        TOML_AVAILABLE = False
        TOML_LOAD = None

def validate_fly_toml():
    """Validate fly.toml structure and required fields."""
    errors = []
    warnings = []
    
    fly_toml = Path("fly.toml")
    if not fly_toml.exists():
        errors.append("fly.toml not found")
        return errors, warnings
    
    if not TOML_AVAILABLE:
        warnings.append("TOML parser not available, skipping structure validation")
        # Basic file existence and readability check
        try:
            content = fly_toml.read_text()
            if "app" not in content:
                warnings.append("fly.toml may be missing 'app' field")
            if "http_service" not in content:
                warnings.append("fly.toml may be missing 'http_service' field")
        except Exception as e:
            errors.append(f"fly.toml read error: {e}")
        return errors, warnings
    
    try:
        with open(fly_toml, "rb") as f:
            config = TOML_LOAD(f)
    except Exception as e:
        errors.append(f"fly.toml parse error: {e}")
        return errors, warnings
    
    # Check required fields
    required = ["app", "build", "http_service"]
    for field in required:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    
    # Check http_service.checks
    if "http_service" in config:
        http_service = config["http_service"]
        if "checks" not in http_service or len(http_service["checks"]) == 0:
            warnings.append("No health checks configured in http_service")
        else:
            checks = http_service["checks"]
            if not any(c.get("path") == "/health" for c in checks):
                warnings.append("No /health endpoint check found")
    
    # Check processes
    if "processes" not in config:
        warnings.append("No processes defined")
    
    return errors, warnings

def validate_dockerfile():
    """Validate Dockerfile structure."""
    errors = []
    warnings = []
    
    dockerfile = Path("Dockerfile")
    if not dockerfile.exists():
        errors.append("Dockerfile not found")
        return errors, warnings
    
    content = dockerfile.read_text()
    
    # Check for required elements
    required_patterns = [
        ("FROM", "Base image"),
        ("EXPOSE", "Port exposure"),
        ("COPY", "File copying"),
    ]
    
    for pattern, name in required_patterns:
        if pattern not in content:
            warnings.append(f"Dockerfile missing {name} ({pattern})")
    
    # Check for port 8080
    if "EXPOSE" in content and "8080" not in content:
        warnings.append("Dockerfile may not expose port 8080")
    
    # Check for health check
    if "HEALTHCHECK" not in content:
        warnings.append("Dockerfile missing HEALTHCHECK")
    
    return errors, warnings

def validate_deployment_scripts():
    """Validate deployment scripts exist and are executable."""
    errors = []
    warnings = []
    
    scripts = [
        "scripts/deploy_fly.sh",
        "scripts/validate_secrets.sh",
        "scripts/verify_deployment.sh",
    ]
    
    for script_path in scripts:
        script = Path(script_path)
        if not script.exists():
            warnings.append(f"Deployment script not found: {script_path}")
        elif not script.is_file():
            errors.append(f"Deployment script is not a file: {script_path}")
        elif not (script.stat().st_mode & 0o111):
            warnings.append(f"Deployment script not executable: {script_path}")
    
    return errors, warnings

def main():
    """Run all validation checks."""
    print("🔍 Validating deployment configuration...")
    print()
    
    all_errors = []
    all_warnings = []
    
    # Validate fly.toml
    errors, warnings = validate_fly_toml()
    all_errors.extend(errors)
    all_warnings.extend(warnings)
    if errors or warnings:
        print("📄 fly.toml:")
        for e in errors:
            print(f"   ❌ {e}")
        for w in warnings:
            print(f"   ⚠️  {w}")
        print()
    
    # Validate Dockerfile
    errors, warnings = validate_dockerfile()
    all_errors.extend(errors)
    all_warnings.extend(warnings)
    if errors or warnings:
        print("🐳 Dockerfile:")
        for e in errors:
            print(f"   ❌ {e}")
        for w in warnings:
            print(f"   ⚠️  {w}")
        print()
    
    # Validate scripts
    errors, warnings = validate_deployment_scripts()
    all_errors.extend(errors)
    all_warnings.extend(warnings)
    if errors or warnings:
        print("📜 Deployment Scripts:")
        for e in errors:
            print(f"   ❌ {e}")
        for w in warnings:
            print(f"   ⚠️  {w}")
        print()
    
    # Summary
    if all_errors:
        print(f"❌ Found {len(all_errors)} error(s)")
        return 1
    
    if all_warnings:
        print(f"⚠️  Found {len(all_warnings)} warning(s) (non-blocking)")
        return 0
    
    print("✅ Deployment configuration valid")
    return 0

if __name__ == "__main__":
    sys.exit(main())

