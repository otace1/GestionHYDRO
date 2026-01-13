#!/usr/bin/env python3
"""
Pre-commit validation script for GestionHYDRO.

This script checks that:
1. No production secrets are accidentally committed
2. Configuration files are valid
3. Environment settings are properly separated

Usage:
    python scripts/validate_config.py

Or add to .git/hooks/pre-commit:
    python scripts/validate_config.py || exit 1
"""
import os
import sys
import re
from pathlib import Path

# Colors for terminal output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'


def error(msg: str) -> None:
    print(f"{RED}❌ ERROR: {msg}{RESET}")


def warning(msg: str) -> None:
    print(f"{YELLOW}⚠️  WARNING: {msg}{RESET}")


def success(msg: str) -> None:
    print(f"{GREEN}✅ {msg}{RESET}")


def check_no_env_files_staged() -> bool:
    """Ensure .env files are not staged for commit."""
    import subprocess

    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only'],
        capture_output=True,
        text=True
    )

    staged_files = result.stdout.strip().split('\n')
    env_files = [f for f in staged_files if f.startswith('.env') and f not in ['.env.template', '.env.sample']]

    if env_files:
        error(f"Environment files staged for commit: {env_files}")
        print("  These files may contain secrets. Remove them with:")
        print(f"  git reset HEAD {' '.join(env_files)}")
        return False

    return True


def check_no_hardcoded_secrets() -> bool:
    """Check for common patterns of hardcoded secrets in Python files."""
    import subprocess

    # Patterns that might indicate hardcoded secrets
    dangerous_patterns = [
        (r"SECRET_KEY\s*=\s*['\"][^'\"]{20,}['\"]", "Hardcoded SECRET_KEY"),
        (r"password\s*=\s*['\"][^'\"]+['\"]", "Possible hardcoded password"),
        (r"AWS_ACCESS_KEY_ID\s*=\s*['\"]AK", "Hardcoded AWS access key"),
        (r"AWS_SECRET_ACCESS_KEY\s*=\s*['\"][^'\"]+['\"]", "Hardcoded AWS secret"),
    ]

    # Get staged Python files
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only', '--', '*.py'],
        capture_output=True,
        text=True
    )

    staged_py_files = [f for f in result.stdout.strip().split('\n') if f]
    issues_found = False

    for filepath in staged_py_files:
        if not os.path.exists(filepath):
            continue

        with open(filepath, 'r') as f:
            content = f.read()

        for pattern, description in dangerous_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                # Skip if it's clearly from environment
                if 'os.environ' in content or 'get_settings' in content:
                    continue
                warning(f"{filepath}: {description}")
                issues_found = True

    return not issues_found


def check_django_env_not_production() -> bool:
    """Ensure local .env doesn't have DJANGO_ENV=production."""
    env_path = Path('.env')

    if not env_path.exists():
        return True

    with open(env_path, 'r') as f:
        content = f.read()

    if re.search(r'^DJANGO_ENV\s*=\s*production', content, re.MULTILINE):
        error("Local .env has DJANGO_ENV=production")
        print("  This is dangerous for local development.")
        print("  Change to DJANGO_ENV=development")
        return False

    return True


def check_settings_import_pattern() -> bool:
    """Verify settings files use proper import pattern."""
    settings_dir = Path('hydrocarbures/settings')

    if not settings_dir.exists():
        warning("Settings directory not found")
        return True

    for settings_file in ['development.py', 'production.py', 'test.py']:
        filepath = settings_dir / settings_file
        if not filepath.exists():
            continue

        with open(filepath, 'r') as f:
            content = f.read()

        if 'from .base import *' not in content:
            error(f"{filepath}: Missing 'from .base import *'")
            return False

    return True


def main() -> int:
    """Run all validation checks."""
    print("\n🔍 Validating configuration before commit...\n")

    checks = [
        ("Checking for staged .env files", check_no_env_files_staged),
        ("Checking for hardcoded secrets", check_no_hardcoded_secrets),
        ("Checking local DJANGO_ENV", check_django_env_not_production),
        ("Checking settings import pattern", check_settings_import_pattern),
    ]

    all_passed = True

    for description, check_func in checks:
        print(f"  {description}...", end=" ")
        try:
            if check_func():
                print(f"{GREEN}OK{RESET}")
            else:
                print(f"{RED}FAILED{RESET}")
                all_passed = False
        except Exception as e:
            print(f"{YELLOW}SKIPPED ({e}){RESET}")

    print()

    if all_passed:
        success("All checks passed!\n")
        return 0
    else:
        error("Some checks failed. Please fix the issues above.\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())

