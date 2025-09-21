#!/usr/bin/env python3
"""
Focused Test Execution Script for Docker Containers
Runs a selection of core test files to get meaningful results
"""

import json
import subprocess
import os
import sys
import time
import re
from datetime import datetime
from typing import Dict, List, Any


class FocusedTestExecutor:
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

    def get_core_test_files(self) -> List[str]:
        """Get a focused list of key test files that are likely to have actual tests."""
        core_tests = [
            # Auth and cache tests
            "tests/test_auth_cache_service.py",
            # Service layer tests
            "tests/services/test_flow_state_machine.py",
            "tests/services/test_asset_write_back.py",
            # Backend integration tests
            "tests/backend/integration/test_collection_flow_simple.py",
            "tests/backend/integration/test_collection_flow_api.py",
            "tests/backend/integration/test_asset_inventory_api.py",
            "tests/backend/integration/test_field_mapping_api.py",
            "tests/backend/integration/test_error_handling.py",
            # Backend unit tests
            "tests/backend/unit/services/test_collection_flow_services.py",
            "tests/backend/unit/services/test_ai_analysis_services.py",
            "tests/backend/unit/test_phase1_migration_patterns.py",
            # Flow tests
            "tests/backend/flows/test_discovery_flow.py",
            "tests/backend/flows/test_unified_discovery_flow.py",
            # Security tests
            "tests/backend/security/test_tenant_isolation.py",
            # Master Flow Orchestrator tests
            "tests/backend/services/test_master_flow_orchestrator.py",
            "tests/backend/services/test_master_flow_orchestrator_comprehensive.py",
            # Core backend tests
            "tests/backend/test_crewai_system.py",
            "tests/backend/test_cache_integration.py",
            "tests/backend/test_memory_system.py",
            "tests/backend/test_multitenant_workflow.py",
            # Performance tests
            "tests/backend/performance/test_discovery_performance.py",
            "tests/backend/performance/test_state_operations.py",
            # Docker integration
            "tests/docker/test_docker_containers.py",
        ]

        # Verify files exist in Docker container first
        verified_tests = []
        for test_file in core_tests:
            result = subprocess.run(
                [
                    "docker",
                    "exec",
                    "migration_backend",
                    "test",
                    "-f",
                    f"/app/{test_file}",
                ],
                capture_output=True,
            )

            if result.returncode == 0:
                verified_tests.append(test_file)
            else:
                print(f"Warning: {test_file} not found in container")

        return verified_tests

    def run_test_in_docker(self, test_file: str) -> Dict[str, Any]:
        """Execute a single test file in the Docker container."""
        print(f"\n🧪 Running test: {test_file}")

        # Use absolute path in container
        container_path = f"/app/{test_file}"

        docker_cmd = [
            "docker",
            "exec",
            "-i",
            "migration_backend",
            "bash",
            "-c",
            f"cd /app && python -m pytest {container_path} -v --tb=short --no-header",
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
                    "file": test_file,
                    "execution_time": round(execution_time, 2),
                    "return_code": result.returncode,
                }
            )

            return test_result

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return {
                "file": test_file,
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
                "file": test_file,
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

        combined_output = stdout + stderr

        # Look for test count in the final summary
        # Examples: "32 passed, 50 warnings in 1.38s"
        # "1 failed, 31 passed in 2.34s"
        # "5 passed, 3 skipped in 1.2s"

        final_summary_pattern = r"=+ (\d+(?:\s+\w+,?\s*)*) in \d+\.\d+s =+"
        summary_match = re.search(final_summary_pattern, combined_output)

        if summary_match:
            summary_text = summary_match.group(1)

            # Extract individual counts
            passed_match = re.search(r"(\d+) passed", summary_text)
            failed_match = re.search(r"(\d+) failed", summary_text)
            skipped_match = re.search(r"(\d+) skipped", summary_text)

            if passed_match:
                result["passed"] = int(passed_match.group(1))
            if failed_match:
                result["failed"] = int(failed_match.group(1))
            if skipped_match:
                result["skipped"] = int(skipped_match.group(1))

        result["tests_run"] = result["passed"] + result["failed"] + result["skipped"]

        # Extract individual test failures
        if result["failed"] > 0:
            result["failures"] = self.extract_test_failures(combined_output)

        # Handle error cases
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
                    "error_type": "AssertionError",
                    "message": error_msg,
                    "traceback": "",
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

    def run_focused_tests(self):
        """Execute focused test suite."""
        print("🔍 Getting focused list of core test files...")
        test_files = self.get_core_test_files()

        if not test_files:
            print("❌ No test files found!")
            return

        print(f"📝 Found {len(test_files)} core test files:")
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
                f"   {status_icon} {result['tests_run']} tests, {result['passed']} passed, "
                f"{result['failed']} failed, {result['skipped']} skipped"
            )

        # Save results to JSON file
        output_file = "/tmp/focused_test_execution_results.json"
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)

        print("\n📊 Focused test execution completed!")
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
    print("🧪 Focused Docker Test Executor")
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
    executor = FocusedTestExecutor()
    results_file = executor.run_focused_tests()

    return results_file


if __name__ == "__main__":
    main()
