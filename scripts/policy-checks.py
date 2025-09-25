#!/usr/bin/env python3
"""
Policy Enforcement Script - Windows-compatible Python version
Local Alternative to GitHub CI - Replace GitHub Actions limits by running policy checks during pre-commit
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


def get_project_root():
    """Get the project root directory."""
    script_dir = Path(__file__).parent
    return script_dir.parent


def get_staged_files(pattern: str) -> List[str]:
    """Get staged files matching the pattern."""
    try:
        result = subprocess.run(
            ["git", "diff", "--staged", "--name-only", "--diff-filter=AM"],
            capture_output=True,
            text=True,
            check=True
        )
        files = result.stdout.strip().split('\n') if result.stdout.strip() else []

        # Filter files by pattern
        filtered_files = []
        for file in files:
            if file and re.search(pattern, file):
                filtered_files.append(file)
        return filtered_files
    except subprocess.CalledProcessError:
        return []


def check_file_content(file_path: str, pattern: str) -> bool:
    """Check if file contains the given pattern."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return bool(re.search(pattern, content))
    except Exception:
        return False


def check_legacy_endpoints():
    """Check 1: Block legacy discovery endpoint usage in app code."""
    print("Checking for legacy discovery endpoint usage...")

    app_files = get_staged_files(r"backend/app/.*\.py$")
    # Exclude files that document removal or block legacy endpoints
    app_files = [f for f in app_files if not any(exclude in f for exclude in [
        "backend/app/middleware/legacy_endpoint_guard.py",
        "backend/app/utils/endpoint_migration_logger.py",
        "_DEPRECATED"
    ])]

    violations = []
    for file_path in app_files:
        if check_file_content(file_path, r"/api/v1/discovery"):
            violations.append(file_path)

    if violations:
        print("ERROR: Legacy discovery endpoints found in application code!")
        print("   Use /api/v1/flows or unified endpoints instead.")
        print("   Found in staged files:")
        for file in violations:
            print(f"     {file}")
        return False

    print("OK: No legacy discovery endpoints in app code")
    return True


def check_deprecated_imports():
    """Check 2: Block deprecated repository base imports."""
    print("Checking for deprecated repository imports...")

    backend_files = get_staged_files(r"backend/.*\.py$")

    violations = []
    for file_path in backend_files:
        if check_file_content(file_path, r"from app\.repositories\.base import ContextAwareRepository"):
            violations.append(file_path)
        elif check_file_content(file_path, r"from app\.core\.context_aware import ContextAwareRepository"):
            violations.append(file_path)

    if violations:
        print("ERROR: Deprecated ContextAwareRepository import detected!")
        print("   Use: from app.repositories.context_aware_repository import ContextAwareRepository")
        print("   Found in staged files:")
        for file in violations:
            print(f"     {file}")
        return False

    print("OK: No deprecated repository imports found")
    return True


def check_sync_db_patterns():
    """Check 3: Block sync database patterns in async code."""
    print("Checking for sync database patterns in async code...")

    app_files = get_staged_files(r"backend/app/.*\.py$")

    violations = []
    for file_path in app_files:
        if check_file_content(file_path, r"SessionLocal\(") and not check_file_content(file_path, r"AsyncSessionLocal"):
            violations.append(file_path)

    if violations:
        print("ERROR: Sync SessionLocal usage found in async app code!")
        print("   Use AsyncSessionLocal instead for consistency.")
        for file in violations:
            print(f"     {file}")
        return False

    print("OK: No sync database patterns in async code")
    return True


def check_env_flags():
    """Check 4: Validate environment flag usage."""
    print("Checking environment flag consistency...")

    python_files = get_staged_files(r"backend/.*\.py$")

    flag_usage = []
    for file_path in python_files:
        if check_file_content(file_path, r"CREWAI_ENABLE_MEMORY|LEGACY_ENDPOINTS_ALLOW"):
            flag_usage.append(file_path)

    if flag_usage:
        print("Environment flag usage found:")
        for file in flag_usage[:3]:  # Show first 3
            print(f"     {file}")

        # Check for proper import pattern
        missing_imports = []
        for file_path in flag_usage:
            if not check_file_content(file_path, r"from app\.core\.env_flags import is_truthy_env"):
                missing_imports.append(file_path)

        if missing_imports:
            print("WARNING: Files using environment flags but missing proper import:")
            for file in missing_imports:
                print(f"     {file}")
                print("   Add: from app.core.env_flags import is_truthy_env")

    print("OK: Environment flag usage consistent")
    return True


def check_unified_endpoints():
    """Check 5: Validate unified endpoint usage."""
    print("Validating unified endpoint consistency...")

    api_files = get_staged_files(r"(backend/app/api/.*|src/.*)\.(py|ts|tsx)$")

    unified_count = 0
    legacy_count = 0

    for file_path in api_files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            unified_count += len(re.findall(r"/api/v1/flows", content))
            legacy_count += len(re.findall(r"/api/v1/discovery", content))
        except Exception:
            continue

    print(f"Endpoint usage: Unified(/api/v1/flows): {unified_count}, Legacy(/api/v1/discovery): {legacy_count}")

    if legacy_count > 0 and unified_count == 0:
        print("WARNING: High legacy endpoint usage with no unified endpoints. Consider migration.")

    return True


def main():
    """Main function to run all policy checks."""
    os.chdir(get_project_root())

    print("Running Code Policy Enforcement Checks...")

    checks = [
        check_legacy_endpoints,
        check_deprecated_imports,
        check_sync_db_patterns,
        check_env_flags,
        check_unified_endpoints
    ]

    exit_code = 0
    for check_func in checks:
        try:
            if not check_func():
                exit_code = 1
        except Exception as e:
            print(f"ERROR: Error in {check_func.__name__}: {e}")
            exit_code = 1
        print()

    if exit_code == 0:
        print("OK: All policy checks passed!")
    else:
        print("ERROR: Policy violations found. Please fix before committing.")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
