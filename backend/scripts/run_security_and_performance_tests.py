#!/usr/bin/env python3
"""
CRITICAL Security and Performance Test Runner for MFO Compliance

This script runs the updated security and performance tests to validate
Master Flow Orchestrator (MFO) compliance with enterprise requirements.

Usage:
    python backend/scripts/run_security_and_performance_tests.py

Test Categories:
1. CRITICAL Security Tests (tenant isolation)
2. MFO API Consistency Tests
3. MFO Performance Benchmarks
4. Atomic Transaction Pattern Validation
"""

import sys
import subprocess
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


def run_pytest_command(test_path: str, markers: str = None, description: str = ""):
    """Run pytest command with proper configuration"""
    cmd = [
        "python",
        "-m",
        "pytest",
        test_path,
        "-v",
        "--tb=short",
        "--strict-markers",
        "--disable-warnings",
    ]

    if markers:
        cmd.extend(["-m", markers])

    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=backend_dir)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"ERROR running tests: {e}")
        return False


def main():
    """Run all security and performance tests"""
    print("🔒 CRITICAL Security and Performance Test Suite for MFO Compliance")
    print("📋 Testing Master Flow Orchestrator (MFO) enterprise requirements")

    tests_passed = 0
    tests_total = 0

    # Test categories to run
    test_categories = [
        {
            "path": "tests/backend/security/test_tenant_isolation.py",
            "markers": "security and critical",
            "description": "CRITICAL Security - Tenant Isolation Tests",
        },
        {
            "path": "tests/backend/security/test_tenant_isolation.py::TestMFOTenantIsolation",
            "markers": None,
            "description": "MFO Tenant Isolation Specific Tests",
        },
        {
            "path": "tests/backend/integration/test_api_consistency.py::TestMFOAPIConsistency",
            "markers": "mfo",
            "description": "MFO API Consistency and Compliance Tests",
        },
        {
            "path": "tests/backend/performance/test_state_operations.py::TestMFOPerformance",
            "markers": "performance",
            "description": "MFO Performance Benchmarks",
        },
        {
            "path": "tests/backend/integration/test_api_consistency.py",
            "markers": "mfo and critical",
            "description": "CRITICAL MFO API Tests",
        },
    ]

    for test_category in test_categories:
        tests_total += 1
        if run_pytest_command(
            test_category["path"],
            test_category["markers"],
            test_category["description"],
        ):
            tests_passed += 1
            print(f"✅ PASSED: {test_category['description']}")
        else:
            print(f"❌ FAILED: {test_category['description']}")

    # Summary
    print(f"\n{'='*60}")
    print("🎯 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests Passed: {tests_passed}/{tests_total}")
    print(f"Success Rate: {(tests_passed/tests_total)*100:.1f}%")

    if tests_passed == tests_total:
        print("🚀 ALL TESTS PASSED - MFO is ready for production!")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED - Review failures before deployment")
        return 1


if __name__ == "__main__":
    sys.exit(main())
