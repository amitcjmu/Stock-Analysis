#!/usr/bin/env python3
"""
Comprehensive Test Execution Script for Docker Containers
Runs all Python test files found in /tests and /backend/tests folders within Docker containers.
"""

import json
import subprocess
import os
import sys
import time
import re
from datetime import datetime
from typing import Dict, List, Any


class DockerTestExecutor:
    def __init__(self):
        self.project_root = "/Users/chocka/CursorProjects/migrate-ui-orchestrator"
        self.results = {
            "execution_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_files": 0,
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "errors": 0,
            },
            "results": [],
        }

    def find_test_files(self) -> List[str]:
        """Find all Python test files in tests and backend/tests directories."""

        test_files = []

        # Use find command to locate test files
        for pattern in ["*test*.py", "test_*.py"]:
            # Find in tests directory
            try:
                result = subprocess.run(
                    [
                        "find",
                        f"{self.project_root}/tests",
                        "-name",
                        pattern,
                        "-type",
                        "f",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    test_files.extend(
                        result.stdout.strip().split("\n")
                        if result.stdout.strip()
                        else []
                    )
            except subprocess.TimeoutExpired:
                print("Warning: Timeout finding test files in tests directory")

            # Find in backend/tests directory
            try:
                result = subprocess.run(
                    [
                        "find",
                        f"{self.project_root}/backend/tests",
                        "-name",
                        pattern,
                        "-type",
                        "f",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    test_files.extend(
                        result.stdout.strip().split("\n")
                        if result.stdout.strip()
                        else []
                    )
            except subprocess.TimeoutExpired:
                print("Warning: Timeout finding test files in backend/tests directory")

        # Remove duplicates and filter valid files
        test_files = list(set([f for f in test_files if f and os.path.exists(f)]))

        # Filter to only include actual test files (containing pytest/unittest imports)
        filtered_files = []
        for file_path in test_files:
            if self.is_test_file(file_path):
                filtered_files.append(file_path)

        return sorted(filtered_files)

    def is_test_file(self, file_path: str) -> bool:
        """Check if file contains test imports and appears to be a test file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for test-related imports or patterns
            test_indicators = [
                "import pytest",
                "from pytest",
                "import unittest",
                "from unittest",
                "def test_",
                "class Test",
                "@pytest",
                "TestCase",
            ]

            return any(indicator in content for indicator in test_indicators)
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
            return False

    def run_test_in_docker(self, test_file: str) -> Dict[str, Any]:
        """Execute a single test file in the Docker container."""
        print(f"\n🧪 Running test: {test_file}")

        # Convert absolute path to relative path for Docker execution
        rel_path = os.path.relpath(test_file, self.project_root)

        # Determine appropriate working directory and command
        if rel_path.startswith("backend/"):
            # Backend tests - run from backend directory
            docker_cmd = [
                "docker",
                "exec",
                "-i",
                "migration_backend",
                "bash",
                "-c",
                f"cd /app && python -m pytest {rel_path} -v --tb=short --no-header",
            ]
        else:
            # Root tests - run from project root
            docker_cmd = [
                "docker",
                "exec",
                "-i",
                "migration_backend",
                "bash",
                "-c",
                f"cd /app && python -m pytest {rel_path} -v --tb=short --no-header",
            ]

        start_time = time.time()

        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout per test file
            )

            execution_time = time.time() - start_time

            # Parse pytest output
            test_result = self.parse_pytest_output(
                result.stdout, result.stderr, result.returncode
            )
            test_result.update(
                {
                    "file": rel_path,
                    "execution_time": round(execution_time, 2),
                    "return_code": result.returncode,
                }
            )

            return test_result

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return {
                "file": rel_path,
                "status": "timeout",
                "tests_run": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "failures": [
                    {
                        "test_name": "timeout",
                        "error_type": "TimeoutError",
                        "message": "Test execution timed out after 5 minutes",
                        "traceback": "",
                    }
                ],
                "execution_time": round(execution_time, 2),
                "return_code": -1,
            }
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "file": rel_path,
                "status": "error",
                "tests_run": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "failures": [
                    {
                        "test_name": "execution_error",
                        "error_type": type(e).__name__,
                        "message": str(e),
                        "traceback": "",
                    }
                ],
                "execution_time": round(execution_time, 2),
                "return_code": -1,
            }

    def parse_pytest_output(
        self, stdout: str, stderr: str, return_code: int
    ) -> Dict[str, Any]:
        """Parse pytest output to extract test results."""

        # Initialize result structure
        result = {
            "status": "pass" if return_code == 0 else "fail",
            "tests_run": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "failures": [],
            "stdout": stdout,
            "stderr": stderr,
        }

        # Look for pytest summary line
        summary_patterns = [
            r"=+ (\d+) failed.*?(\d+) passed.*?(\d+) skipped.*?=+",
            r"=+ (\d+) failed.*?(\d+) passed.*?=+",
            r"=+ (\d+) passed.*?(\d+) skipped.*?=+",
            r"=+ (\d+) passed.*?=+",
            r"=+ (\d+) failed.*?=+",
            r"=+ (\d+) skipped.*?=+",
        ]

        combined_output = stdout + stderr

        # Try to extract summary from output
        for pattern in summary_patterns:
            match = re.search(pattern, combined_output)
            if match:
                numbers = [int(x) for x in match.groups()]
                if "failed" in pattern and "passed" in pattern:
                    if "skipped" in pattern:
                        result["failed"], result["passed"], result["skipped"] = numbers
                    else:
                        result["failed"], result["passed"] = numbers
                elif "passed" in pattern and "skipped" in pattern:
                    result["passed"], result["skipped"] = numbers
                elif "passed" in pattern:
                    result["passed"] = numbers[0]
                elif "failed" in pattern:
                    result["failed"] = numbers[0]
                elif "skipped" in pattern:
                    result["skipped"] = numbers[0]
                break

        result["tests_run"] = result["passed"] + result["failed"] + result["skipped"]

        # Extract individual test failures
        if result["failed"] > 0:
            result["failures"] = self.extract_test_failures(combined_output)

        # If no tests were detected but there's output, it might be an import error
        if result["tests_run"] == 0 and (
            stderr or "ERROR" in stdout or "ImportError" in stdout
        ):
            result["status"] = "error"
            result["failures"] = [
                {
                    "test_name": "import_or_setup_error",
                    "error_type": "SetupError",
                    "message": stderr or "Import or setup error detected",
                    "traceback": combined_output,
                }
            ]

        return result

    def extract_test_failures(self, output: str) -> List[Dict[str, str]]:
        """Extract individual test failure details from pytest output."""
        failures = []

        # Look for FAILED test_file.py::test_name patterns
        failed_pattern = r"FAILED (.*?) - (.*?)(?=\n|$)"
        matches = re.findall(failed_pattern, output, re.MULTILINE)

        for match in matches:
            test_name = match[0]
            error_msg = match[1]

            failures.append(
                {
                    "test_name": test_name,
                    "error_type": "AssertionError",  # Default, could be parsed more specifically
                    "message": error_msg,
                    "traceback": "",  # Could extract full traceback if needed
                }
            )

        # If no specific failures found but output indicates failure
        if not failures and ("FAILED" in output or "ERROR" in output):
            failures.append(
                {
                    "test_name": "unknown_failure",
                    "error_type": "TestFailure",
                    "message": "Test failed but specific details could not be parsed",
                    "traceback": output,
                }
            )

        return failures

    def run_all_tests(self):
        """Execute all tests and generate comprehensive results."""
        print("🔍 Finding all test files...")
        test_files = self.find_test_files()

        if not test_files:
            print("❌ No test files found!")
            return

        print(f"📝 Found {len(test_files)} test files:")
        for f in test_files:
            print(f"  - {f}")

        self.results["summary"]["total_files"] = len(test_files)

        print(f"\n🚀 Executing {len(test_files)} test files...")

        for i, test_file in enumerate(test_files, 1):
            print(f"\n[{i}/{len(test_files)}] Testing: {os.path.basename(test_file)}")

            result = self.run_test_in_docker(test_file)
            self.results["results"].append(result)

            # Update summary
            self.results["summary"]["total_tests"] += result["tests_run"]
            self.results["summary"]["passed"] += result["passed"]
            self.results["summary"]["failed"] += result["failed"]
            self.results["summary"]["skipped"] += result["skipped"]

            if result["status"] in ["error", "timeout"]:
                self.results["summary"]["errors"] += 1

            # Print progress
            status_icon = (
                "✅"
                if result["status"] == "pass"
                else "❌" if result["status"] == "fail" else "⚠️"
            )
            print(
                f"   {status_icon} {result['tests_run']} tests, {result['passed']} passed, {result['failed']} failed, {result['skipped']} skipped"
            )

        # Save results to JSON file
        output_file = "/tmp/test_execution_results.json"
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)

        print("\n📊 Test execution completed!")
        print(f"📄 Results saved to: {output_file}")

        # Print summary
        summary = self.results["summary"]
        print("\n📈 Summary:")
        print(f"   Total files: {summary['total_files']}")
        print(f"   Total tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed']}")
        print(f"   Failed: {summary['failed']}")
        print(f"   Skipped: {summary['skipped']}")
        print(f"   Errors: {summary['errors']}")

        # List files with failures
        failed_files = [
            r
            for r in self.results["results"]
            if r["failed"] > 0 or r["status"] in ["error", "timeout"]
        ]
        if failed_files:
            print(f"\n❌ Files with failures ({len(failed_files)}):")
            for result in failed_files:
                print(f"   - {result['file']} ({result['status']})")

        return output_file


def main():
    """Main execution function."""
    print("🧪 Docker Test Matrix Executor")
    print("=" * 50)

    # Check Docker containers are running
    try:
        result = subprocess.run(
            ["docker", "exec", "migration_backend", "echo", "Container accessible"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            print("❌ Backend container not accessible!")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Cannot access Docker containers: {e}")
        sys.exit(1)

    print("✅ Docker containers accessible")

    # Execute tests
    executor = DockerTestExecutor()
    results_file = executor.run_all_tests()

    return results_file


if __name__ == "__main__":
    main()
