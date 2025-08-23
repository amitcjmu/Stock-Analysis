#!/usr/bin/env python3
"""
Backend Test Runner for CrewAI Flow Migration
Runs comprehensive backend tests for the CrewAI Flow migration validation.
"""

import sys
import subprocess
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any


class BackendTestRunner:
    """Comprehensive backend test runner for CrewAI Flow migration."""

    def __init__(self, verbose: bool = False, docker: bool = True):
        self.verbose = verbose
        self.docker = docker
        self.project_root = Path(__file__).parent.parent.parent
        self.test_results: List[Dict[str, Any]] = []

    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = time.strftime("%H:%M:%S")
        if self.verbose or level in ["ERROR", "SUCCESS", "FAIL"]:
            print(f"[{timestamp}] {level}: {message}")

    def run_command(self, cmd: List[str], cwd: str = None) -> Dict[str, Any]:
        """Run a command and return the result."""
        if cwd is None:
            cwd = str(self.project_root)

        self.log(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd)
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": "Command timed out after 5 minutes",
                "command": " ".join(cmd)
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "command": " ".join(cmd)
            }

    def run_pytest_tests(self, test_pattern: str = None) -> Dict[str, Any]:
        """Run pytest tests."""
        cmd = ["python", "-m", "pytest"]

        if test_pattern:
            cmd.append(test_pattern)
        else:
            cmd.append("tests/backend/")

        # Add pytest options
        cmd.extend([
            "-v",  # Verbose
            "--tb=short",  # Short traceback format
            "--strict-markers",  # Strict marker checking
            "--disable-warnings",  # Disable warnings for cleaner output
        ])

        if self.docker:
            # Run tests in Docker container
            docker_cmd = [
                "docker", "exec", "-it", "migration_backend"
            ] + cmd
            return self.run_command(docker_cmd)
        else:
            return self.run_command(cmd)

    def run_migration_validation_tests(self) -> Dict[str, Any]:
        """Run CrewAI Flow migration validation tests."""
        test_file = "tests/backend/test_crewai_flow_migration.py"
        return self.run_pytest_tests(test_file)

    def run_flow_validation_tests(self) -> Dict[str, Any]:
        """Run CrewAI Flow end-to-end validation tests."""
        test_file = "tests/backend/test_crewai_flow_validation.py"
        return self.run_pytest_tests(test_file)

    def run_service_health_tests(self) -> Dict[str, Any]:
        """Run service health tests."""
        if self.docker:
            # Test service health in Docker
            cmd = [
                "docker", "exec", "-it", "migration_backend",
                "python", "-c",
                """
import requests
import sys
try:
    # Test backend health
    response = requests.get('http://localhost:8000/health', timeout=10)
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'

    # Test CrewAI Flow service health (unified)
    response = requests.get('http://localhost:8000/api/v1/unified-discovery/flow/health', timeout=10)
    assert response.status_code == 200
    assert response.json()['service_name'] == 'CrewAI Flow Service'

    print('All health checks passed')
    sys.exit(0)
except Exception as e:
    print(f'Health check failed: {e}')
    sys.exit(1)
                """
            ]
        else:
            cmd = [
                "python", "-c",
                """
import requests
import sys
try:
    response = requests.get('http://localhost:8000/health', timeout=10)
    assert response.status_code == 200
    print('Health check passed')
    sys.exit(0)
except Exception as e:
    print(f'Health check failed: {e}')
    sys.exit(1)
                """
            ]

        return self.run_command(cmd)

    def run_import_tests(self) -> Dict[str, Any]:
        """Test that all imports work correctly."""
        if self.docker:
            cmd = [
                "docker", "exec", "-it", "migration_backend",
                "python", "-c",
                """
import sys
try:
    # Test core imports
    from app.services.crewai_flow_service import CrewAIFlowService
    from app.services.crewai_flows.discovery_flow import DiscoveryFlow, DiscoveryFlowState
    from app.api.v1.discovery.discovery_flow import router

    print('All imports successful')
    sys.exit(0)
except ImportError as e:
    print(f'Import error: {e}')
    sys.exit(1)
except Exception as e:
    print(f'Unexpected error: {e}')
    sys.exit(1)
                """
            ]
        else:
            cmd = [
                "python", "-c",
                """
import sys
sys.path.insert(0, 'backend')
try:
    from app.services.crewai_flow_service import CrewAIFlowService
    from app.services.crewai_flows.discovery_flow import DiscoveryFlow, DiscoveryFlowState
    print('All imports successful')
    sys.exit(0)
except ImportError as e:
    print(f'Import error: {e}')
    sys.exit(1)
                """
            ]

        return self.run_command(cmd)

    def run_database_tests(self) -> Dict[str, Any]:
        """Test database connectivity."""
        if self.docker:
            cmd = [
                "docker", "exec", "-it", "migration_backend",
                "python", "-c",
                """
import sys
try:
    from app.core.database import get_db
    from sqlalchemy import text

    # Test database connection
    db = next(get_db())
    result = db.execute(text('SELECT 1'))
    assert result.fetchone()[0] == 1

    print('Database connection successful')
    sys.exit(0)
except Exception as e:
    print(f'Database test failed: {e}')
    sys.exit(1)
                """
            ]
        else:
            # Skip database tests if not in Docker
            return {
                "success": True,
                "returncode": 0,
                "stdout": "Database tests skipped (not in Docker)",
                "stderr": "",
                "command": "database_test_skipped"
            }

        return self.run_command(cmd)

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all backend tests."""
        self.log("Starting comprehensive backend test suite")

        test_suite = [
            ("Import Tests", self.run_import_tests),
            ("Service Health Tests", self.run_service_health_tests),
            ("Database Tests", self.run_database_tests),
            ("Migration Validation Tests", self.run_migration_validation_tests),
            ("Flow Validation Tests", self.run_flow_validation_tests),
        ]

        results = []
        total_tests = len(test_suite)
        passed_tests = 0

        for test_name, test_func in test_suite:
            self.log(f"Running {test_name}...")

            start_time = time.time()
            result = test_func()
            duration = time.time() - start_time

            result["test_name"] = test_name
            result["duration"] = duration
            results.append(result)

            if result["success"]:
                passed_tests += 1
                self.log(f"✅ {test_name}: PASSED ({duration:.2f}s)", "SUCCESS")
            else:
                self.log(f"❌ {test_name}: FAILED ({duration:.2f}s)", "FAIL")
                if self.verbose:
                    self.log(f"STDOUT: {result['stdout']}")
                    self.log(f"STDERR: {result['stderr']}")

        # Generate summary
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": success_rate,
            "results": results,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        return summary

    def print_summary(self, summary: Dict[str, Any]):
        """Print test summary."""
        print("\n" + "="*80)
        print("BACKEND TEST SUITE SUMMARY")
        print("="*80)

        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']} ✅")
        print(f"Failed: {summary['failed_tests']} ❌")
        print(f"Success Rate: {summary['success_rate']:.1f}%")

        if summary['failed_tests'] > 0:
            print("\nFAILED TESTS:")
            print("-" * 40)
            for result in summary['results']:
                if not result['success']:
                    print(f"❌ {result['test_name']}")
                    if result['stderr']:
                        print(f"   Error: {result['stderr'][:200]}...")

        print("\nALL TEST RESULTS:")
        print("-" * 40)
        for result in summary['results']:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test_name']}: {result['duration']:.2f}s")

        print("\n" + "="*80)

        if summary['success_rate'] == 100:
            print("🎉 ALL BACKEND TESTS PASSED!")
        elif summary['success_rate'] >= 80:
            print("⚠️  Most tests passed, but some issues need attention.")
        else:
            print("🚨 Multiple test failures - backend needs review.")

        print("="*80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run Backend Tests for CrewAI Flow Migration")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-docker", action="store_true", help="Run tests without Docker")
    parser.add_argument("--test", "-t", help="Run specific test (imports, health, database, migration, flow)")
    parser.add_argument("--output", "-o", help="Output results to JSON file")

    args = parser.parse_args()

    runner = BackendTestRunner(verbose=args.verbose, docker=not args.no_docker)

    try:
        if args.test:
            # Run specific test
            test_map = {
                "imports": runner.run_import_tests,
                "health": runner.run_service_health_tests,
                "database": runner.run_database_tests,
                "migration": runner.run_migration_validation_tests,
                "flow": runner.run_flow_validation_tests,
            }

            if args.test not in test_map:
                print(f"Unknown test: {args.test}")
                print(f"Available tests: {', '.join(test_map.keys())}")
                sys.exit(1)

            result = test_map[args.test]()

            if result["success"]:
                print(f"✅ {args.test} test PASSED")
                sys.exit(0)
            else:
                print(f"❌ {args.test} test FAILED")
                print(f"Error: {result['stderr']}")
                sys.exit(1)
        else:
            # Run all tests
            summary = runner.run_all_tests()
            runner.print_summary(summary)

            if args.output:
                import json
                with open(args.output, 'w') as f:
                    json.dump(summary, f, indent=2)
                print(f"\nResults saved to: {args.output}")

            sys.exit(0 if summary['success_rate'] == 100 else 1)

    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nTest runner failed with exception: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
