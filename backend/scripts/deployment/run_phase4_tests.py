#!/usr/bin/env python3
"""
Phase 4 Discovery Flow Data Integrity Test Runner

This script orchestrates the complete Phase 4 test suite for discovery flow data integrity,
including end-to-end integration tests, database constraint validation, API consistency tests,
performance validation, and deployment readiness checks.

Test Suite Coverage:
1. End-to-End Integration Tests
2. Database Constraint Tests
3. API Consistency Tests
4. Performance Validation Tests
5. Deployment Validation Tests
6. Monitoring Query Generation

Usage:
    python scripts/deployment/run_phase4_tests.py --all
    python scripts/deployment/run_phase4_tests.py --integration
    python scripts/deployment/run_phase4_tests.py --performance
    python scripts/deployment/run_phase4_tests.py --deployment
    python scripts/deployment/run_phase4_tests.py --generate-report
"""

import argparse
import asyncio
import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get the backend directory path
BACKEND_DIR = Path(__file__).parent.parent.parent
TESTS_DIR = BACKEND_DIR / "tests"
SCRIPTS_DIR = BACKEND_DIR / "scripts" / "deployment"


class Phase4TestRunner:
    """
    Comprehensive test runner for Phase 4 discovery flow data integrity validation.

    This class coordinates all Phase 4 tests and generates comprehensive reports
    on data integrity, performance, and deployment readiness.
    """

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the Phase 4 test runner.

        Args:
            output_dir: Directory to store test results and reports
        """
        self.output_dir = (
            Path(output_dir) if output_dir else BACKEND_DIR / "test_results"
        )
        self.output_dir.mkdir(exist_ok=True)

        self.test_results = {
            "test_run_id": f"phase4_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "start_time": datetime.now().isoformat(),
            "test_suites": {},
            "summary": {},
            "recommendations": [],
        }

    async def run_all_tests(self) -> Dict[str, Any]:
        """
        Run the complete Phase 4 test suite.

        Returns:
            Dict containing comprehensive test results
        """
        logger.info("🚀 Starting Phase 4 Discovery Flow Data Integrity Test Suite")
        logger.info(f"📁 Output directory: {self.output_dir}")

        try:
            # 1. Run integration tests
            logger.info("🧪 Running integration tests...")
            integration_results = await self._run_integration_tests()
            self.test_results["test_suites"]["integration"] = integration_results

            # 2. Run API consistency tests
            logger.info("🔗 Running API consistency tests...")
            api_results = await self._run_api_consistency_tests()
            self.test_results["test_suites"]["api_consistency"] = api_results

            # 3. Run performance tests
            logger.info("⚡ Running performance tests...")
            performance_results = await self._run_performance_tests()
            self.test_results["test_suites"]["performance"] = performance_results

            # 4. Run deployment validation
            logger.info("🚀 Running deployment validation...")
            deployment_results = await self._run_deployment_validation()
            self.test_results["test_suites"]["deployment"] = deployment_results

            # 5. Generate monitoring queries
            logger.info("📊 Generating monitoring queries...")
            monitoring_results = await self._generate_monitoring_queries()
            self.test_results["test_suites"]["monitoring"] = monitoring_results

            # Generate summary and recommendations
            self.test_results["summary"] = self._generate_test_summary()
            self.test_results["recommendations"] = self._generate_recommendations()
            self.test_results["end_time"] = datetime.now().isoformat()

            # Save results
            await self._save_test_results()

            logger.info("✅ Phase 4 test suite completed successfully")
            return self.test_results

        except Exception as e:
            logger.error(f"❌ Phase 4 test suite failed: {e}")
            self.test_results["error"] = str(e)
            self.test_results["end_time"] = datetime.now().isoformat()
            await self._save_test_results()
            raise

    async def _run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests using pytest"""
        try:
            # Run discovery flow data integrity tests
            integration_cmd = [
                sys.executable,
                "-m",
                "pytest",
                str(
                    TESTS_DIR / "integration" / "test_discovery_flow_data_integrity.py"
                ),
                "-v",
                "--tb=short",
                "--json-report",
                f"--json-report-file={self.output_dir}/integration_test_results.json",
            ]

            logger.info(f"Running: {' '.join(integration_cmd)}")
            result = subprocess.run(
                integration_cmd,
                cwd=BACKEND_DIR,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes timeout
            )

            # Parse results
            integration_results = {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "status": "passed" if result.returncode == 0 else "failed",
            }

            # Try to load JSON report if available
            json_report_path = self.output_dir / "integration_test_results.json"
            if json_report_path.exists():
                try:
                    with open(json_report_path, "r") as f:
                        json_report = json.load(f)
                    integration_results["detailed_results"] = json_report
                except Exception as e:
                    logger.warning(f"Could not parse JSON test report: {e}")

            return integration_results

        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "error": "Integration tests timed out after 10 minutes",
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _run_api_consistency_tests(self) -> Dict[str, Any]:
        """Run API consistency tests using pytest"""
        try:
            # Run API consistency tests
            api_cmd = [
                sys.executable,
                "-m",
                "pytest",
                str(TESTS_DIR / "integration" / "test_api_consistency.py"),
                "-v",
                "--tb=short",
                "--json-report",
                f"--json-report-file={self.output_dir}/api_consistency_test_results.json",
            ]

            logger.info(f"Running: {' '.join(api_cmd)}")
            result = subprocess.run(
                api_cmd,
                cwd=BACKEND_DIR,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
            )

            # Parse results
            api_results = {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "status": "passed" if result.returncode == 0 else "failed",
            }

            # Try to load JSON report if available
            json_report_path = self.output_dir / "api_consistency_test_results.json"
            if json_report_path.exists():
                try:
                    with open(json_report_path, "r") as f:
                        json_report = json.load(f)
                    api_results["detailed_results"] = json_report
                except Exception as e:
                    logger.warning(f"Could not parse API test JSON report: {e}")

            return api_results

        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "error": "API consistency tests timed out after 5 minutes",
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests using the performance monitoring script"""
        try:
            # Run performance benchmark
            performance_cmd = [
                sys.executable,
                str(SCRIPTS_DIR / "performance_monitoring.py"),
                "--benchmark",
                "--output",
                str(self.output_dir / "performance_benchmark_results.json"),
            ]

            logger.info(f"Running: {' '.join(performance_cmd)}")
            result = subprocess.run(
                performance_cmd,
                cwd=BACKEND_DIR,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
            )

            # Parse results
            performance_results = {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "status": "passed" if result.returncode == 0 else "failed",
            }

            # Load benchmark results if available
            benchmark_file = self.output_dir / "performance_benchmark_results.json"
            if benchmark_file.exists():
                try:
                    with open(benchmark_file, "r") as f:
                        benchmark_data = json.load(f)
                    performance_results["benchmark_data"] = benchmark_data
                except Exception as e:
                    logger.warning(
                        f"Could not parse performance benchmark results: {e}"
                    )

            return performance_results

        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "error": "Performance tests timed out after 5 minutes",
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _run_deployment_validation(self) -> Dict[str, Any]:
        """Run deployment validation using the data integrity validation script"""
        try:
            # Run deployment validation
            validation_cmd = [
                sys.executable,
                str(SCRIPTS_DIR / "validate_data_integrity.py"),
                "--output",
                str(self.output_dir / "deployment_validation_results.json"),
                "--monitoring-queries",
            ]

            logger.info(f"Running: {' '.join(validation_cmd)}")
            result = subprocess.run(
                validation_cmd,
                cwd=BACKEND_DIR,
                capture_output=True,
                text=True,
                timeout=180,  # 3 minutes timeout
            )

            # Parse results
            validation_results = {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "status": "passed" if result.returncode == 0 else "failed",
            }

            # Load validation results if available
            validation_file = self.output_dir / "deployment_validation_results.json"
            if validation_file.exists():
                try:
                    with open(validation_file, "r") as f:
                        validation_data = json.load(f)
                    validation_results["validation_data"] = validation_data
                except Exception as e:
                    logger.warning(
                        f"Could not parse deployment validation results: {e}"
                    )

            return validation_results

        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "error": "Deployment validation timed out after 3 minutes",
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _generate_monitoring_queries(self) -> Dict[str, Any]:
        """Generate monitoring queries for ongoing data integrity monitoring"""
        try:
            # Check if monitoring queries were generated by deployment validation
            monitoring_file = (
                self.output_dir / "deployment_validation_results_monitoring.sql"
            )

            if monitoring_file.exists():
                with open(monitoring_file, "r") as f:
                    monitoring_queries = f.read()

                return {
                    "status": "completed",
                    "queries_generated": True,
                    "monitoring_file": str(monitoring_file),
                    "query_content": monitoring_queries,
                }
            else:
                return {
                    "status": "warning",
                    "queries_generated": False,
                    "message": "Monitoring queries file not found - may not have been generated",
                }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _generate_test_summary(self) -> Dict[str, Any]:
        """Generate comprehensive test summary"""
        summary = {
            "total_test_suites": len(self.test_results["test_suites"]),
            "passed_test_suites": 0,
            "failed_test_suites": 0,
            "test_suite_status": {},
            "overall_status": "unknown",
            "critical_issues": [],
            "warnings": [],
        }

        # Analyze each test suite
        for suite_name, suite_results in self.test_results["test_suites"].items():
            suite_status = suite_results.get("status", "unknown")
            summary["test_suite_status"][suite_name] = suite_status

            if suite_status == "passed":
                summary["passed_test_suites"] += 1
            elif suite_status in ["failed", "error", "timeout"]:
                summary["failed_test_suites"] += 1
                summary["critical_issues"].append(f"{suite_name}: {suite_status}")
            else:
                summary["warnings"].append(f"{suite_name}: {suite_status}")

        # Determine overall status
        if summary["failed_test_suites"] == 0:
            summary["overall_status"] = "passed"
        elif summary["passed_test_suites"] > 0:
            summary["overall_status"] = "partial"
        else:
            summary["overall_status"] = "failed"

        return summary

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        # Check each test suite for specific recommendations
        test_suites = self.test_results["test_suites"]

        # Integration test recommendations
        integration_results = test_suites.get("integration", {})
        if integration_results.get("status") == "failed":
            recommendations.append(
                "CRITICAL: Integration tests failed - data integrity issues detected. "
                "Review foreign key relationships and cascade deletion configuration."
            )

        # API consistency recommendations
        api_results = test_suites.get("api_consistency", {})
        if api_results.get("status") == "failed":
            recommendations.append(
                "WARNING: API consistency issues detected. "
                "Review API response formats and data relationship consistency."
            )

        # Performance recommendations
        performance_results = test_suites.get("performance", {})
        if performance_results.get("status") == "failed":
            recommendations.append(
                "PERFORMANCE: Performance issues detected. "
                "Review query optimization and database indexing."
            )

        benchmark_data = performance_results.get("benchmark_data", {})
        if benchmark_data:
            benchmark_recommendations = benchmark_data.get("recommendations", [])
            recommendations.extend(benchmark_recommendations)

        # Deployment recommendations
        deployment_results = test_suites.get("deployment", {})
        if deployment_results.get("status") == "failed":
            recommendations.append(
                "DEPLOYMENT: Deployment validation failed. "
                "System is not ready for production deployment."
            )

        validation_data = deployment_results.get("validation_data", {})
        if validation_data and validation_data.get("issues"):
            issues = validation_data["issues"]
            if issues:
                recommendations.append(
                    f"DATA INTEGRITY: {len(issues)} data integrity issues found. "
                    "Review orphaned records and constraint violations."
                )

        # Overall recommendations
        if self.test_results["summary"]["overall_status"] == "passed":
            recommendations.append(
                "✅ All tests passed - Discovery flow data integrity is validated and ready for production."
            )
        elif self.test_results["summary"]["overall_status"] == "partial":
            recommendations.append(
                "⚠️ Some tests failed - Address critical issues before production deployment."
            )
        else:
            recommendations.append(
                "❌ Critical failures detected - Do not deploy to production until all issues are resolved."
            )

        return recommendations

    async def _save_test_results(self):
        """Save test results to output directory"""
        try:
            # Save main results file
            results_file = self.output_dir / "phase4_test_results.json"
            with open(results_file, "w") as f:
                json.dump(self.test_results, f, indent=2, default=str)

            # Generate HTML report
            await self._generate_html_report()

            # Generate summary report
            await self._generate_summary_report()

            logger.info(f"📄 Test results saved to {results_file}")

        except Exception as e:
            logger.error(f"❌ Failed to save test results: {e}")

    async def _generate_html_report(self):
        """Generate HTML test report"""
        try:
            html_content = self._create_html_report_content()

            html_file = self.output_dir / "phase4_test_report.html"
            with open(html_file, "w") as f:
                f.write(html_content)

            logger.info(f"📄 HTML report generated: {html_file}")

        except Exception as e:
            logger.error(f"❌ Failed to generate HTML report: {e}")

    def _create_html_report_content(self) -> str:
        """Create HTML content for test report"""
        summary = self.test_results.get("summary", {})
        test_suites = self.test_results.get("test_suites", {})
        recommendations = self.test_results.get("recommendations", [])

        status_color = {
            "passed": "#28a745",
            "failed": "#dc3545",
            "partial": "#ffc107",
            "unknown": "#6c757d",
        }

        overall_status = summary.get("overall_status", "unknown")
        status_bg_color = status_color.get(overall_status, "#6c757d")

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Phase 4 Discovery Flow Data Integrity Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: {status_bg_color}; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ background-color: #f8f9fa; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        .test-suite {{ margin: 20px 0; padding: 15px; border: 1px solid #dee2e6; border-radius: 5px; }}
        .passed {{ border-left: 5px solid #28a745; }}
        .failed {{ border-left: 5px solid #dc3545; }}
        .warning {{ border-left: 5px solid #ffc107; }}
        .recommendations {{ background-color: #e9ecef; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        pre {{ background-color: #f8f9fa; padding: 10px; border-radius: 3px; overflow-x: auto; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: white; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Phase 4 Discovery Flow Data Integrity Test Report</h1>
        <p>Test Run ID: {self.test_results.get('test_run_id', 'unknown')}</p>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Overall Status: <strong>{overall_status.upper()}</strong></p>
    </div>

    <div class="summary">
        <h2>Test Summary</h2>
        <div class="metric">Total Test Suites: <strong>{summary.get('total_test_suites', 0)}</strong></div>
        <div class="metric">Passed: <strong>{summary.get('passed_test_suites', 0)}</strong></div>
        <div class="metric">Failed: <strong>{summary.get('failed_test_suites', 0)}</strong></div>
    </div>
"""

        # Add test suite details
        html += "<h2>Test Suite Results</h2>"

        for suite_name, suite_results in test_suites.items():
            suite_status = suite_results.get("status", "unknown")
            css_class = (
                "passed"
                if suite_status == "passed"
                else (
                    "failed"
                    if suite_status in ["failed", "error", "timeout"]
                    else "warning"
                )
            )

            html += f"""
    <div class="test-suite {css_class}">
        <h3>{suite_name.replace('_', ' ').title()}</h3>
        <p><strong>Status:</strong> {suite_status}</p>
"""

            if "error" in suite_results:
                html += f"<p><strong>Error:</strong> {suite_results['error']}</p>"

            if "stdout" in suite_results and suite_results["stdout"]:
                html += f"<details><summary>Output</summary><pre>{suite_results['stdout'][:1000]}...</pre></details>"

            html += "</div>"

        # Add recommendations
        if recommendations:
            html += """
    <div class="recommendations">
        <h2>Recommendations</h2>
        <ul>
"""
            for rec in recommendations:
                html += f"<li>{rec}</li>"

            html += """
        </ul>
    </div>
"""

        html += """
</body>
</html>
"""

        return html

    async def _generate_summary_report(self):
        """Generate text summary report"""
        try:
            summary_content = self._create_summary_report_content()

            summary_file = self.output_dir / "phase4_test_summary.txt"
            with open(summary_file, "w") as f:
                f.write(summary_content)

            logger.info(f"📄 Summary report generated: {summary_file}")

        except Exception as e:
            logger.error(f"❌ Failed to generate summary report: {e}")

    def _create_summary_report_content(self) -> str:
        """Create text content for summary report"""
        summary = self.test_results.get("summary", {})
        recommendations = self.test_results.get("recommendations", [])

        content = f"""
Phase 4 Discovery Flow Data Integrity Test Summary
==================================================

Test Run ID: {self.test_results.get('test_run_id', 'unknown')}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Overall Status: {summary.get('overall_status', 'unknown').upper()}

Test Results:
- Total Test Suites: {summary.get('total_test_suites', 0)}
- Passed: {summary.get('passed_test_suites', 0)}
- Failed: {summary.get('failed_test_suites', 0)}

Test Suite Status:
"""

        for suite_name, status in summary.get("test_suite_status", {}).items():
            content += f"- {suite_name.replace('_', ' ').title()}: {status}\n"

        if summary.get("critical_issues"):
            content += "\nCritical Issues:\n"
            for issue in summary["critical_issues"]:
                content += f"- {issue}\n"

        if summary.get("warnings"):
            content += "\nWarnings:\n"
            for warning in summary["warnings"]:
                content += f"- {warning}\n"

        if recommendations:
            content += "\nRecommendations:\n"
            for i, rec in enumerate(recommendations, 1):
                content += f"{i}. {rec}\n"

        content += "\nDetailed results available in phase4_test_results.json\n"

        return content


async def main():
    """Main function for running Phase 4 tests"""
    parser = argparse.ArgumentParser(
        description="Run Phase 4 Discovery Flow Data Integrity Tests"
    )
    parser.add_argument("--all", action="store_true", help="Run all test suites")
    parser.add_argument(
        "--integration", action="store_true", help="Run integration tests only"
    )
    parser.add_argument(
        "--api", action="store_true", help="Run API consistency tests only"
    )
    parser.add_argument(
        "--performance", action="store_true", help="Run performance tests only"
    )
    parser.add_argument(
        "--deployment", action="store_true", help="Run deployment validation only"
    )
    parser.add_argument("--output-dir", help="Output directory for test results")
    parser.add_argument(
        "--generate-report",
        action="store_true",
        help="Generate HTML and summary reports",
    )

    args = parser.parse_args()

    if not any(
        [args.all, args.integration, args.api, args.performance, args.deployment]
    ):
        args.all = True  # Default to running all tests

    # Initialize test runner
    runner = Phase4TestRunner(output_dir=args.output_dir)

    try:
        if args.all:
            logger.info("🚀 Running complete Phase 4 test suite...")
            results = await runner.run_all_tests()
        else:
            # Run individual test suites
            results = {
                "test_run_id": f"phase4_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "start_time": datetime.now().isoformat(),
                "test_suites": {},
                "summary": {},
                "recommendations": [],
            }

            if args.integration:
                logger.info("🧪 Running integration tests...")
                results["test_suites"][
                    "integration"
                ] = await runner._run_integration_tests()

            if args.api:
                logger.info("🔗 Running API consistency tests...")
                results["test_suites"][
                    "api_consistency"
                ] = await runner._run_api_consistency_tests()

            if args.performance:
                logger.info("⚡ Running performance tests...")
                results["test_suites"][
                    "performance"
                ] = await runner._run_performance_tests()

            if args.deployment:
                logger.info("🚀 Running deployment validation...")
                results["test_suites"][
                    "deployment"
                ] = await runner._run_deployment_validation()

            # Update runner results and generate summary
            runner.test_results = results
            results["summary"] = runner._generate_test_summary()
            results["recommendations"] = runner._generate_recommendations()
            results["end_time"] = datetime.now().isoformat()

            await runner._save_test_results()

        # Print summary
        summary = results["summary"]
        logger.info(
            f"📊 Test Summary: {summary.get('passed_test_suites', 0)}/{summary.get('total_test_suites', 0)} test suites passed"
        )
        logger.info(
            f"🎯 Overall Status: {summary.get('overall_status', 'unknown').upper()}"
        )

        if results.get("recommendations"):
            logger.info("💡 Recommendations:")
            for rec in results["recommendations"][:3]:  # Show first 3 recommendations
                logger.info(f"   - {rec}")

        # Print file locations
        logger.info(f"📁 Results saved to: {runner.output_dir}")
        logger.info(f"📄 Main results: {runner.output_dir}/phase4_test_results.json")
        logger.info(f"📄 HTML report: {runner.output_dir}/phase4_test_report.html")
        logger.info(f"📄 Summary: {runner.output_dir}/phase4_test_summary.txt")

        # Exit with appropriate code
        if summary.get("overall_status") == "passed":
            logger.info("✅ All Phase 4 tests passed - Data integrity validated")
            exit(0)
        elif summary.get("overall_status") == "partial":
            logger.warning(
                "⚠️ Some Phase 4 tests failed - Review issues before deployment"
            )
            exit(1)
        else:
            logger.error("❌ Phase 4 tests failed - Critical issues detected")
            exit(2)

    except Exception as e:
        logger.error(f"❌ Phase 4 test execution failed: {e}")
        exit(3)


if __name__ == "__main__":
    asyncio.run(main())
