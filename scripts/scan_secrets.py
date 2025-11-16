#!/usr/bin/env python3
"""
Scan for hardcoded secrets and exposed credentials.
Steers toward secure code practices.
"""

import re
import sys
from pathlib import Path

# Patterns that might indicate secrets
SECRET_PATTERNS = [
    (r'api[_-]?key\s*=\s*["\']([^"\']+)["\']', 'API key'),
    (r'secret\s*=\s*["\']([^"\']+)["\']', 'Secret'),
    (r'password\s*=\s*["\']([^"\']+)["\']', 'Password'),
    (r'token\s*=\s*["\']([^"\']+)["\']', 'Token'),
    (r'sk-[a-zA-Z0-9]{20,}', 'OpenAI API key pattern'),
    (r'sk-ant-[a-zA-Z0-9-]{20,}', 'Anthropic API key pattern'),
    (r'AIza[0-9A-Za-z_-]{35}', 'Google API key pattern'),
    (r'pplx-[a-zA-Z0-9]{20,}', 'Perplexity API key pattern'),
    (r'tskey-[a-zA-Z0-9-]{20,}', 'Tailscale auth key pattern'),
]

# Files/directories to ignore
IGNORE_PATTERNS = [
    '.git',
    'node_modules',
    '__pycache__',
    '.ruff_cache',
    '.pytest_cache',
    'venv',
    'env',
    '.env',  # .env files are expected to have secrets
    '.env.example',
    'uv.lock',
    'package-lock.json',
]

# File extensions to check
CHECK_EXTENSIONS = {'.py', '.js', '.mjs', '.ts', '.tsx', '.sh', '.bash', '.yaml', '.yml', '.json', '.md'}

def should_ignore(path: Path) -> bool:
    """Check if path should be ignored."""
    path_str = str(path)
    for pattern in IGNORE_PATTERNS:
        if pattern in path_str:
            return True
    return False

def scan_file(file_path: Path) -> list:
    """Scan a file for potential secrets."""
    issues = []
    
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return issues
    
    for pattern, description in SECRET_PATTERNS:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            # Skip if it's clearly a placeholder or example
            value = match.group(1) if match.groups() else match.group(0)
            if any(x in value.lower() for x in ['example', 'placeholder', 'your_', 'xxx', 'test', 'dummy']):
                continue
            # Skip if it's an environment variable reference
            if '${' in content[max(0, match.start()-10):match.start()] or 'os.getenv' in content[max(0, match.start()-50):match.start()]:
                continue
            
            issues.append({
                'file': str(file_path),
                'line': line_num,
                'type': description,
                'match': match.group(0)[:50] + '...' if len(match.group(0)) > 50 else match.group(0)
            })
    
    return issues

def scan_directory(directory: Path = Path('.')) -> list:
    """Scan directory for potential secrets."""
    all_issues = []
    
    for path in directory.rglob('*'):
        if should_ignore(path):
            continue
        
        if path.is_file():
            if path.suffix in CHECK_EXTENSIONS or path.name in ['.gitignore', '.dockerignore']:
                issues = scan_file(path)
                all_issues.extend(issues)
    
    return all_issues

def main():
    """Run secret scanning."""
    print("🔒 Scanning for potential secrets...")
    print()
    
    issues = scan_directory()
    
    if not issues:
        print("✅ No potential secrets found")
        return 0
    
    print(f"⚠️  Found {len(issues)} potential secret(s):")
    print()
    
    for issue in issues:
        print(f"   {issue['file']}:{issue['line']}")
        print(f"   Type: {issue['type']}")
        print(f"   Match: {issue['match']}")
        print()
    
    print("💡 Recommendations:")
    print("   - Use environment variables instead of hardcoded values")
    print("   - Add secrets to .env (not committed)")
    print("   - Use .env.example for documentation")
    print("   - Review false positives and add to IGNORE_PATTERNS if needed")
    print()
    
    # Don't block on warnings, but inform
    return 0

if __name__ == "__main__":
    sys.exit(main())

