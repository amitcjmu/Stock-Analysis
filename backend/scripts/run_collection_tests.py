#!/usr/bin/env python3
"""
Test runner script for collection manual submission tests.

Usage:
    python scripts/run_collection_tests.py              # Run all collection tests
    python scripts/run_collection_tests.py --gap        # Run gap resolution tests only
    python scripts/run_collection_tests.py --tenant     # Run tenant scoping tests only
    python scripts/run_collection_tests.py --writeback  # Run asset write-back tests only
    python scripts/run_collection_tests.py --verbose    # Run with verbose output

CC Generated with Claude Code
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_pytest(test_path: str, verbose: bool = False) -> int:
    """Run pytest with the specified test path and options."""
    cmd = ["python", "-m", "pytest"]

    if verbose:
        cmd.extend(["-v", "-s"])
    else:
        cmd.append("-v")

    cmd.extend(["--tb=short", "--asyncio-mode=auto", test_path])

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(
        description="Run collection manual submission tests"
    )
    parser.add_argument(
        "--gap", action="store_true", help="Run gap resolution tests only"
    )
    parser.add_argument(
        "--tenant", action="store_true", help="Run tenant scoping tests only"
    )
    parser.add_argument(
        "--writeback", action="store_true", help="Run asset write-back tests only"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Run with verbose output"
    )
    parser.add_argument(
        "--all", action="store_true", help="Run all collection tests (default)"
    )

    args = parser.parse_args()

    # Determine which tests to run
    test_files = []

    if args.gap:
        test_files.append("tests/api/v1/endpoints/test_collection_gap_resolution.py")
    elif args.tenant:
        test_files.append("tests/api/v1/endpoints/test_collection_tenant_scoping.py")
    elif args.writeback:
        test_files.append("tests/services/test_asset_write_back.py")
    else:
        # Default: run all collection tests
        test_files.extend(
            [
                "tests/api/v1/endpoints/test_collection_gap_resolution.py",
                "tests/api/v1/endpoints/test_collection_tenant_scoping.py",
                "tests/services/test_asset_write_back.py",
            ]
        )

    print("=" * 80)
    print("Collection Manual Submission Tests")
    print("=" * 80)
    print(f"Running {len(test_files)} test file(s):")
    for test_file in test_files:
        print(f"  - {test_file}")
    print()

    # Run each test file
    total_failures = 0
    for test_file in test_files:
        print(f"\n{'-' * 60}")
        print(f"Running {test_file}")
        print(f"{'-' * 60}")

        exit_code = run_pytest(test_file, args.verbose)
        if exit_code != 0:
            total_failures += 1
            print(f"❌ {test_file} FAILED (exit code: {exit_code})")
        else:
            print(f"✅ {test_file} PASSED")

    print(f"\n{'=' * 80}")
    print("Test Summary")
    print(f"{'=' * 80}")
    print(f"Total test files: {len(test_files)}")
    print(f"Passed: {len(test_files) - total_failures}")
    print(f"Failed: {total_failures}")

    if total_failures == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n💥 {total_failures} test file(s) failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
