#!/usr/bin/env python3
"""
Phase 3 Validation Runner
Comprehensive validation suite for CrewAI Flow migration Phase 3: Validation and Cleanup

This script runs:
1. Backend unit tests
2. API integration tests  
3. Docker container validation
4. Migration-specific validation
5. Performance and stress tests
6. Cleanup verification

Usage:
    python tests/scripts/run_phase3_validation.py
    python tests/scripts/run_phase3_validation.py --verbose
    python tests/scripts/run_phase3_validation.py --quick
    python tests/scripts/run_phase3_validation.py --docker-only
"""

import sys
import os
import time
import subprocess
import argparse
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path


class Phase3ValidationRunner:
    """Comprehensive Phase 3 validation runner."""
    
    def __init__(self, verbose: bool = False, quick: bool = False):
        self.verbose = verbose
        self.quick = quick
        self.results = []
        self.start_time = time.time()
        
        # Get project root
        self.project_root = Path(__file__).parent.parent.parent
        self.tests_dir = self.project_root / "tests"
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if self.verbose or level in ["ERROR", "SUCCESS", "FAIL", "PHASE"]:
            print(f"[{timestamp}] {level}: {message}")
    
    def run_command(self, command: List[str], description: str, cwd: str = None) -> Dict[str, Any]:
        """Run a command and capture results."""
        self.log(f"Running: {description}")
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                cwd=cwd or str(self.project_root),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            duration = time.time() - start_time
            success = result.returncode == 0
            
            test_result = {
                "description": description,
                "command": " ".join(command),
                "success": success,
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
            self.results.append(test_result)
            
            if success:
                self.log(f"✅ {description} ({duration:.2f}s)", "SUCCESS")
            else:
                self.log(f"❌ {description} ({duration:.2f}s)", "FAIL")
                if self.verbose:
                    self.log(f"Error: {result.stderr}", "ERROR")
            
            return test_result
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            test_result = {
                "description": description,
                "command": " ".join(command),
                "success": False,
                "duration": duration,
                "stdout": "",
                "stderr": "Command timed out after 5 minutes",
                "returncode": -1
            }
            
            self.results.append(test_result)
            self.log(f"❌ {description} (TIMEOUT after {duration:.2f}s)", "FAIL")
            return test_result
            
        except Exception as e:
            duration = time.time() - start_time
            test_result = {
                "description": description,
                "command": " ".join(command),
                "success": False,
                "duration": duration,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
            
            self.results.append(test_result)
            self.log(f"❌ {description} (Exception: {str(e)})", "ERROR")
            return test_result
    
    def check_docker_containers(self) -> bool:
        """Check that Docker containers are running."""
        self.log("Checking Docker container status...", "PHASE")
        
        result = self.run_command(
            ["docker-compose", "ps"],
            "Docker Container Status Check"
        )
        
        if not result["success"]:
            self.log("Docker containers not running. Starting them...", "INFO")
            
            # Try to start containers
            start_result = self.run_command(
                ["docker-compose", "up", "-d"],
                "Start Docker Containers"
            )
            
            if start_result["success"]:
                # Wait for containers to be ready
                self.log("Waiting for containers to be ready...", "INFO")
                time.sleep(10)
                
                # Check again
                check_result = self.run_command(
                    ["docker-compose", "ps"],
                    "Docker Container Status Recheck"
                )
                return check_result["success"]
            else:
                return False
        
        return True
    
    def run_backend_unit_tests(self):
        """Run backend unit tests."""
        self.log("Running Backend Unit Tests...", "PHASE")
        
        # Run specific CrewAI Flow migration tests
        test_files = [
            "tests/backend/test_crewai_flow_migration.py",
            "tests/backend/test_crewai_flow_validation.py"
        ]
        
        for test_file in test_files:
            if (self.project_root / test_file).exists():
                self.run_command(
                    ["python", "-m", "pytest", test_file, "-v"],
                    f"Backend Test: {test_file}"
                )
    
    def run_api_integration_tests(self):
        """Run API integration tests."""
        self.log("Running API Integration Tests...", "PHASE")
        
        # Run the fixed validation script
        self.run_command(
            ["python", "tests/scripts/validate_crewai_flow_migration_fixed.py", "--quick"],
            "CrewAI Flow Migration Validation"
        )
        
        # Run backend test runner
        if (self.tests_dir / "scripts" / "run_backend_tests.py").exists():
            self.run_command(
                ["python", "tests/scripts/run_backend_tests.py", "--quick"],
                "Backend Integration Tests"
            )
    
    def run_docker_validation(self):
        """Run Docker-specific validation."""
        self.log("Running Docker Validation...", "PHASE")
        
        # Run Docker validation script if it exists
        if (self.tests_dir / "scripts" / "run_docker_validation.sh").exists():
            self.run_command(
                ["bash", "tests/scripts/run_docker_validation.sh", "--quick"],
                "Docker Environment Validation"
            )
    
    def run_performance_tests(self):
        """Run performance and stress tests."""
        if self.quick:
            self.log("Skipping performance tests in quick mode", "INFO")
            return
            
        self.log("Running Performance Tests...", "PHASE")
        
        # Run performance validation
        self.run_command(
            ["python", "tests/scripts/validate_crewai_flow_migration_fixed.py", "--verbose"],
            "Performance and Extended Validation"
        )
    
    def run_cleanup_verification(self):
        """Verify cleanup and resource management."""
        self.log("Running Cleanup Verification...", "PHASE")
        
        # Test cleanup endpoints
        cleanup_commands = [
            ["curl", "-s", "http://localhost:8000/api/v1/discovery/flow/cleanup", "-X", "POST"],
            ["curl", "-s", "http://localhost:8000/api/v1/discovery/flow/active"],
            ["curl", "-s", "http://localhost:8000/api/v1/discovery/flow/health"]
        ]
        
        for cmd in cleanup_commands:
            self.run_command(cmd, f"Cleanup Test: {' '.join(cmd[1:])}")
    
    def run_all_validations(self, docker_only: bool = False) -> Dict[str, Any]:
        """Run all Phase 3 validations."""
        self.log("Starting Phase 3: Validation and Cleanup", "PHASE")
        
        # 1. Check Docker containers
        if not self.check_docker_containers():
            self.log("Docker containers not available. Cannot proceed.", "ERROR")
            return self.generate_summary()
        
        if docker_only:
            # 2. Docker validation only
            self.run_docker_validation()
            self.run_api_integration_tests()
        else:
            # 2. Backend unit tests
            self.run_backend_unit_tests()
            
            # 3. API integration tests
            self.run_api_integration_tests()
            
            # 4. Docker validation
            self.run_docker_validation()
            
            # 5. Performance tests (unless quick mode)
            self.run_performance_tests()
            
            # 6. Cleanup verification
            self.run_cleanup_verification()
        
        return self.generate_summary()
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate validation summary."""
        total_duration = time.time() - self.start_time
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        summary = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": success_rate,
            "total_duration": total_duration,
            "results": self.results
        }
        
        return summary
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print formatted summary."""
        print("\n" + "="*80)
        print("PHASE 3: VALIDATION AND CLEANUP SUMMARY")
        print("="*80)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ✅")
        print(f"Failed: {summary['failed']} ❌")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Total Duration: {summary['total_duration']:.2f}s")
        
        # Show failed tests
        failed_results = [r for r in summary['results'] if not r["success"]]
        if failed_results:
            print("\nFAILED TESTS:")
            print("-" * 40)
            for result in failed_results:
                print(f"❌ {result['description']}")
                if self.verbose and result['stderr']:
                    print(f"   Error: {result['stderr'][:200]}...")
        
        # Show all test results
        print("\nALL TEST RESULTS:")
        print("-" * 40)
        for result in summary['results']:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['description']} ({result['duration']:.2f}s)")
        
        print("\n" + "="*80)
        if summary['success_rate'] >= 90:
            print("🎉 Phase 3 validation EXCELLENT!")
        elif summary['success_rate'] >= 80:
            print("✅ Phase 3 validation successful!")
        elif summary['success_rate'] >= 60:
            print("⚠️ Phase 3 mostly working - some issues to review.")
        else:
            print("🚨 Phase 3 validation failed - needs attention.")
        print("="*80)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run Phase 3 Validation and Cleanup")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--quick", "-q", action="store_true", help="Quick validation (skip performance tests)")
    parser.add_argument("--docker-only", action="store_true", help="Only run Docker-related tests")
    
    args = parser.parse_args()
    
    # Create runner
    runner = Phase3ValidationRunner(verbose=args.verbose, quick=args.quick)
    
    # Run validations
    summary = runner.run_all_validations(docker_only=args.docker_only)
    
    # Print summary
    runner.print_summary(summary)
    
    # Exit with appropriate code
    sys.exit(0 if summary['success_rate'] >= 80 else 1)


if __name__ == "__main__":
    main() 