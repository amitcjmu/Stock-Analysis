#!/usr/bin/env python3
"""
Comprehensive Test Suite for Master Flow Orchestrator
Phase 6: Day 9 - Execute Full Test Suite (MFO-095)

This script runs the complete test suite including unit tests, integration tests,
end-to-end tests, and Master Flow Orchestrator specific tests.
"""

import os
import sys
import asyncio
import logging
import json
import subprocess
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_tests.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ComprehensiveTestRunner:
    """Runs comprehensive test suite for Master Flow Orchestrator"""
    
    def __init__(self):
        self.test_id = f"tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.base_path = Path(__file__).parent.parent.parent
        self.results_path = self.base_path / "test_results"
        self.results_path.mkdir(parents=True, exist_ok=True)
        
        # Test configuration
        self.config = {
            "backend_url": os.getenv("BACKEND_URL", "http://localhost:8001"),
            "frontend_url": os.getenv("FRONTEND_URL", "http://localhost:3001"),
            "staging_db_url": os.getenv("STAGING_DATABASE_URL"),
            "test_timeout": 1800,  # 30 minutes
            "retry_count": 3,
            "parallel_workers": 4
        }
        
        # Test results
        self.test_results = {
            "test_id": self.test_id,
            "start_time": datetime.now().isoformat(),
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "test_suites": {},
            "coverage": {},
            "performance": {},
            "errors": []
        }
        
        logger.info(f"🧪 Starting comprehensive test suite: {self.test_id}")
    
    async def run_comprehensive_tests(self) -> bool:
        """
        Run the complete test suite
        Task: MFO-095
        """
        try:
            logger.info("=" * 80)
            logger.info("🧪 COMPREHENSIVE TEST SUITE - MASTER FLOW ORCHESTRATOR")
            logger.info("=" * 80)
            
            # Phase 1: Environment setup and validation
            if not await self._setup_test_environment():
                return False
            
            # Phase 2: Unit tests
            if not await self._run_unit_tests():
                return False
            
            # Phase 3: Integration tests
            if not await self._run_integration_tests():
                return False
            
            # Phase 4: Master Flow Orchestrator specific tests
            if not await self._run_master_flow_orchestrator_tests():
                return False
            
            # Phase 5: API tests
            if not await self._run_api_tests():
                return False
            
            # Phase 6: End-to-end tests
            if not await self._run_e2e_tests():
                return False
            
            # Phase 7: Performance tests
            if not await self._run_performance_tests():
                return False
            
            # Phase 8: Security tests
            if not await self._run_security_tests():
                return False
            
            # Phase 9: Generate test report
            await self._generate_test_report()
            
            # Determine overall success
            success_rate = self.test_results["passed_tests"] / max(self.test_results["total_tests"], 1)
            
            if success_rate >= 0.95:  # 95% pass rate required
                logger.info("✅ Comprehensive test suite PASSED!")
                return True
            else:
                logger.error(f"❌ Test suite FAILED - Pass rate: {success_rate:.2%}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Test suite execution failed: {e}")
            await self._handle_test_failure(e)
            return False
    
    async def _setup_test_environment(self) -> bool:
        """Setup and validate test environment"""
        logger.info("📋 Phase 1: Test environment setup")
        
        try:
            # Verify services are running
            services = ["backend", "frontend", "postgres", "redis"]
            
            for service in services:
                if not await self._verify_service_availability(service):
                    return False
            
            # Initialize test database
            if not await self._initialize_test_database():
                return False
            
            # Verify Master Flow Orchestrator availability
            if not await self._verify_master_flow_orchestrator():
                return False
            
            logger.info("✅ Test environment setup completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Test environment setup failed: {e}")
            return False
    
    async def _verify_service_availability(self, service: str) -> bool:
        """Verify service is available"""
        try:
            if service == "backend":
                import requests
                response = requests.get(f"{self.config['backend_url']}/health", timeout=10)
                return response.status_code == 200
            
            elif service == "frontend":
                import requests
                response = requests.get(f"{self.config['frontend_url']}", timeout=10)
                return response.status_code == 200
            
            elif service in ["postgres", "redis"]:
                # Check through docker-compose
                result = subprocess.run(
                    ["docker-compose", "-f", "docker-compose.staging.yml", 
                     "ps", "-q", service],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                return bool(result.stdout.strip())
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Service {service} not available: {e}")
            return False
    
    async def _initialize_test_database(self) -> bool:
        """Initialize test database with clean state"""
        try:
            logger.info("🗄️ Initializing test database...")
            
            # Run database initialization
            result = subprocess.run(
                ["docker-compose", "-f", "docker-compose.staging.yml", 
                 "exec", "-T", "backend", "python", "-m", "app.core.database_initialization"],
                timeout=120,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"❌ Database initialization failed: {result.stderr}")
                return False
            
            logger.info("✅ Test database initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            return False
    
    async def _verify_master_flow_orchestrator(self) -> bool:
        """Verify Master Flow Orchestrator is available"""
        try:
            import requests
            
            # Test Master Flow Orchestrator endpoints
            endpoints = [
                "/api/v1/flows",
                "/api/v1/flows/active",
                "/api/v1/flows/analytics"
            ]
            
            for endpoint in endpoints:
                url = f"{self.config['backend_url']}{endpoint}"
                response = requests.get(url, timeout=10)
                
                if response.status_code >= 500:
                    logger.error(f"❌ Master Flow Orchestrator endpoint {endpoint} failed: {response.status_code}")
                    return False
            
            logger.info("✅ Master Flow Orchestrator verified")
            return True
            
        except Exception as e:
            logger.error(f"❌ Master Flow Orchestrator verification failed: {e}")
            return False
    
    async def _run_unit_tests(self) -> bool:
        """Run unit tests"""
        logger.info("📋 Phase 2: Unit tests")
        
        try:
            result = await self._run_pytest_suite(
                "tests/unit/",
                "unit_tests",
                markers="unit"
            )
            
            self.test_results["test_suites"]["unit"] = result
            return result["success"]
            
        except Exception as e:
            logger.error(f"❌ Unit tests failed: {e}")
            return False
    
    async def _run_integration_tests(self) -> bool:
        """Run integration tests"""
        logger.info("📋 Phase 3: Integration tests")
        
        try:
            result = await self._run_pytest_suite(
                "tests/integration/",
                "integration_tests",
                markers="integration"
            )
            
            self.test_results["test_suites"]["integration"] = result
            return result["success"]
            
        except Exception as e:
            logger.error(f"❌ Integration tests failed: {e}")
            return False
    
    async def _run_master_flow_orchestrator_tests(self) -> bool:
        """Run Master Flow Orchestrator specific tests"""
        logger.info("📋 Phase 4: Master Flow Orchestrator tests")
        
        try:
            # Test Master Flow Orchestrator core functionality
            result = await self._run_pytest_suite(
                "tests/services/test_master_flow_orchestrator.py",
                "master_flow_orchestrator_tests",
                markers="master_flow"
            )
            
            # Test flow type registry
            registry_result = await self._run_pytest_suite(
                "tests/services/test_flow_type_registry.py",
                "flow_registry_tests",
                markers="flow_registry"
            )
            
            # Test flow state manager
            state_result = await self._run_pytest_suite(
                "tests/services/test_flow_state_manager.py",
                "flow_state_tests",
                markers="flow_state"
            )
            
            # Combine results
            total_success = result["success"] and registry_result["success"] and state_result["success"]
            
            self.test_results["test_suites"]["master_flow_orchestrator"] = {
                "core": result,
                "registry": registry_result,
                "state": state_result,
                "success": total_success
            }
            
            return total_success
            
        except Exception as e:
            logger.error(f"❌ Master Flow Orchestrator tests failed: {e}")
            return False
    
    async def _run_api_tests(self) -> bool:
        """Run API tests"""
        logger.info("📋 Phase 5: API tests")
        
        try:
            result = await self._run_pytest_suite(
                "tests/api/",
                "api_tests",
                markers="api"
            )
            
            self.test_results["test_suites"]["api"] = result
            return result["success"]
            
        except Exception as e:
            logger.error(f"❌ API tests failed: {e}")
            return False
    
    async def _run_e2e_tests(self) -> bool:
        """Run end-to-end tests"""
        logger.info("📋 Phase 6: End-to-end tests")
        
        try:
            # Run Playwright E2E tests
            result = subprocess.run(
                ["npx", "playwright", "test", "--reporter=json"],
                cwd=self.base_path,
                timeout=self.config["test_timeout"],
                capture_output=True,
                text=True
            )
            
            e2e_result = {
                "success": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr,
                "duration": 0  # Playwright will provide this
            }
            
            # Parse Playwright results
            try:
                if result.stdout:
                    playwright_results = json.loads(result.stdout)
                    e2e_result["stats"] = playwright_results.get("stats", {})
                    e2e_result["duration"] = playwright_results.get("stats", {}).get("duration", 0)
            except json.JSONDecodeError:
                pass
            
            self.test_results["test_suites"]["e2e"] = e2e_result
            
            if e2e_result["success"]:
                logger.info("✅ End-to-end tests passed")
            else:
                logger.error("❌ End-to-end tests failed")
                logger.error(f"Error output: {result.stderr}")
            
            return e2e_result["success"]
            
        except Exception as e:
            logger.error(f"❌ End-to-end tests failed: {e}")
            return False
    
    async def _run_performance_tests(self) -> bool:
        """Run performance tests"""
        logger.info("📋 Phase 7: Performance tests")
        
        try:
            result = await self._run_pytest_suite(
                "tests/performance/",
                "performance_tests",
                markers="performance"
            )
            
            self.test_results["test_suites"]["performance"] = result
            return result["success"]
            
        except Exception as e:
            logger.error(f"❌ Performance tests failed: {e}")
            return False
    
    async def _run_security_tests(self) -> bool:
        """Run security tests"""
        logger.info("📋 Phase 8: Security tests")
        
        try:
            result = await self._run_pytest_suite(
                "tests/security/",
                "security_tests",
                markers="security"
            )
            
            self.test_results["test_suites"]["security"] = result
            return result["success"]
            
        except Exception as e:
            logger.error(f"❌ Security tests failed: {e}")
            return False
    
    async def _run_pytest_suite(self, test_path: str, suite_name: str, markers: str = None) -> Dict[str, Any]:
        """Run a pytest suite and return results"""
        try:
            logger.info(f"🧪 Running {suite_name}...")
            
            cmd = [
                "docker-compose", "-f", "docker-compose.staging.yml",
                "exec", "-T", "backend",
                "python", "-m", "pytest",
                test_path,
                "-v",
                "--tb=short",
                f"--junitxml=/app/test_results/{suite_name}.xml",
                "--cov=app",
                f"--cov-report=json:/app/test_results/{suite_name}_coverage.json",
                "--cov-report=term-missing"
            ]
            
            if markers:
                cmd.extend(["-m", markers])
            
            start_time = time.time()
            
            result = subprocess.run(
                cmd,
                timeout=self.config["test_timeout"],
                capture_output=True,
                text=True
            )
            
            duration = time.time() - start_time
            
            # Parse test results
            test_result = {
                "success": result.returncode == 0,
                "duration": duration,
                "output": result.stdout,
                "errors": result.stderr,
                "test_count": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0
            }
            
            # Parse pytest output for test counts
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if "passed" in line and "failed" in line:
                    # Parse line like "10 passed, 2 failed, 1 skipped"
                    parts = line.split(',')
                    for part in parts:
                        part = part.strip()
                        if "passed" in part:
                            test_result["passed"] = int(part.split()[0])
                        elif "failed" in part:
                            test_result["failed"] = int(part.split()[0])
                        elif "skipped" in part:
                            test_result["skipped"] = int(part.split()[0])
                    break
            
            test_result["test_count"] = test_result["passed"] + test_result["failed"] + test_result["skipped"]
            
            # Update global test results
            self.test_results["total_tests"] += test_result["test_count"]
            self.test_results["passed_tests"] += test_result["passed"]
            self.test_results["failed_tests"] += test_result["failed"]
            self.test_results["skipped_tests"] += test_result["skipped"]
            
            if test_result["success"]:
                logger.info(f"✅ {suite_name} passed ({test_result['passed']} tests, {duration:.2f}s)")
            else:
                logger.error(f"❌ {suite_name} failed ({test_result['failed']} failures)")
                if result.stderr:
                    logger.error(f"Errors: {result.stderr}")
            
            return test_result
            
        except subprocess.TimeoutExpired:
            logger.error(f"❌ {suite_name} timed out after {self.config['test_timeout']} seconds")
            return {
                "success": False,
                "duration": self.config["test_timeout"],
                "output": "",
                "errors": "Test suite timed out",
                "test_count": 0,
                "passed": 0,
                "failed": 1,
                "skipped": 0
            }
        except Exception as e:
            logger.error(f"❌ {suite_name} execution failed: {e}")
            return {
                "success": False,
                "duration": 0,
                "output": "",
                "errors": str(e),
                "test_count": 0,
                "passed": 0,
                "failed": 1,
                "skipped": 0
            }
    
    async def _generate_test_report(self) -> None:
        """Generate comprehensive test report"""
        self.test_results["end_time"] = datetime.now().isoformat()
        
        # Calculate overall duration
        start_time = datetime.fromisoformat(self.test_results["start_time"])
        end_time = datetime.fromisoformat(self.test_results["end_time"])
        total_duration = (end_time - start_time).total_seconds()
        
        self.test_results["total_duration"] = total_duration
        
        # Calculate success rate
        if self.test_results["total_tests"] > 0:
            success_rate = self.test_results["passed_tests"] / self.test_results["total_tests"]
        else:
            success_rate = 0
        
        self.test_results["success_rate"] = success_rate
        
        # Generate detailed report
        report = {
            "test_execution": self.test_results,
            "configuration": self.config,
            "environment": {
                "backend_url": self.config["backend_url"],
                "frontend_url": self.config["frontend_url"],
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Save detailed report
        report_file = self.results_path / f"test_report_{self.test_id}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate summary
        logger.info("\n" + "=" * 80)
        logger.info("📊 COMPREHENSIVE TEST RESULTS")
        logger.info("=" * 80)
        logger.info(f"Test ID: {self.test_id}")
        logger.info(f"Duration: {total_duration:.2f} seconds")
        logger.info(f"Total Tests: {self.test_results['total_tests']}")
        logger.info(f"Passed: {self.test_results['passed_tests']}")
        logger.info(f"Failed: {self.test_results['failed_tests']}")
        logger.info(f"Skipped: {self.test_results['skipped_tests']}")
        logger.info(f"Success Rate: {success_rate:.2%}")
        logger.info(f"Report saved: {report_file}")
        
        # Suite breakdown
        logger.info("\n📋 Test Suite Breakdown:")
        for suite_name, suite_result in self.test_results["test_suites"].items():
            if isinstance(suite_result, dict) and "success" in suite_result:
                status = "✅ PASS" if suite_result["success"] else "❌ FAIL"
                duration = suite_result.get("duration", 0)
                logger.info(f"  {suite_name}: {status} ({duration:.2f}s)")
        
        if success_rate >= 0.95:
            logger.info("\n🎉 COMPREHENSIVE TEST SUITE PASSED!")
            logger.info("✅ Ready for load testing (MFO-096)")
        else:
            logger.error("\n❌ COMPREHENSIVE TEST SUITE FAILED!")
            logger.error("🔧 Fix failing tests before proceeding")
        
        logger.info("=" * 80)
    
    async def _handle_test_failure(self, error: Exception) -> None:
        """Handle test execution failure"""
        self.test_results["execution_error"] = str(error)
        self.test_results["end_time"] = datetime.now().isoformat()
        
        # Save failure report
        failure_report_file = self.results_path / f"test_failure_{self.test_id}.json"
        with open(failure_report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        logger.error("=" * 80)
        logger.error("❌ COMPREHENSIVE TEST SUITE EXECUTION FAILED")
        logger.error("=" * 80)
        logger.error(f"Error: {error}")
        logger.error(f"Failure report saved: {failure_report_file}")
        logger.error("=" * 80)


async def main():
    """Main test execution function"""
    test_runner = ComprehensiveTestRunner()
    
    try:
        success = await test_runner.run_comprehensive_tests()
        
        if success:
            logger.info("✅ Comprehensive test suite completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Comprehensive test suite failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("⏹️  Test execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Test execution failed with unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())