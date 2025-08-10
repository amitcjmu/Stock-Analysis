#!/usr/bin/env python3
"""
System Health Validation Script
Validates system health before and after legacy code cleanup operations.
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, Any
import aiohttp
import psutil
import os

# Add backend path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import text

    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    print("⚠️  Some imports unavailable - running in minimal mode")


class SystemHealthValidator:
    def __init__(self):
        self.results = {}
        self.errors = []
        self.warnings = []

    async def validate_database_connectivity(self) -> Dict[str, Any]:
        """Test database connection and basic query execution."""
        if not IMPORTS_AVAILABLE:
            return {"status": "skipped", "reason": "imports_unavailable"}

        try:
            async with AsyncSessionLocal() as session:
                # Test basic connectivity
                result = await session.execute(text("SELECT 1 as health_check"))
                row = result.fetchone()

                if row and row.health_check == 1:
                    # Test table access
                    tables_query = text(
                        """
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name LIKE '%flow%'
                        LIMIT 5
                    """
                    )
                    tables_result = await session.execute(tables_query)
                    tables = [row.table_name for row in tables_result.fetchall()]

                    return {
                        "status": "healthy",
                        "connection": True,
                        "tables_accessible": len(tables),
                        "sample_tables": tables[:3],
                    }

        except Exception as e:
            self.errors.append(f"Database connectivity failed: {str(e)}")
            return {"status": "failed", "error": str(e)}

        return {"status": "failed", "error": "Unknown database issue"}

    async def validate_api_endpoints(self) -> Dict[str, Any]:
        """Test critical API endpoints for availability and response."""
        base_url = "http://localhost:8000"
        endpoints_to_test = [
            "/health",
            "/api/v1/health",
            "/api/v1/flows",
            "/debug/routes",
        ]

        results = {}

        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints_to_test:
                try:
                    async with session.get(
                        f"{base_url}{endpoint}", timeout=5
                    ) as response:
                        results[endpoint] = {
                            "status_code": response.status,
                            "response_time_ms": None,  # Would need timing
                            "accessible": 200 <= response.status < 400,
                        }

                        # Special validation for health endpoints
                        if endpoint in ["/health", "/api/v1/health"]:
                            try:
                                data = await response.json()
                                results[endpoint]["health_status"] = data.get(
                                    "status", "unknown"
                                )
                            except (ValueError, KeyError):
                                results[endpoint]["health_status"] = "unparseable"

                except Exception as e:
                    results[endpoint] = {
                        "status_code": None,
                        "accessible": False,
                        "error": str(e),
                    }

        return results

    def validate_system_resources(self) -> Dict[str, Any]:
        """Check system resource utilization."""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
                "available_memory_gb": round(
                    psutil.virtual_memory().available / 1024 / 1024 / 1024, 2
                ),
            }
        except Exception as e:
            self.errors.append(f"System resource check failed: {str(e)}")
            return {"status": "failed", "error": str(e)}

    def validate_docker_environment(self) -> Dict[str, Any]:
        """Validate Docker environment and container status."""
        try:
            import subprocess

            # Check if we're running in Docker
            in_docker = os.path.exists("/.dockerenv")

            # Try to get container stats
            if in_docker:
                result = subprocess.run(
                    [
                        "docker",
                        "stats",
                        "--no-stream",
                        "--format",
                        "table {{.Name}}\\t{{.CPUPerc}}\\t{{.MemUsage}}",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                return {
                    "in_docker": in_docker,
                    "docker_accessible": result.returncode == 0,
                    "stats_available": bool(result.stdout),
                }
            else:
                return {"in_docker": False, "host_environment": True}

        except Exception as e:
            self.warnings.append(f"Docker validation failed: {str(e)}")
            return {"status": "warning", "error": str(e)}

    def validate_legacy_cleanup_readiness(self) -> Dict[str, Any]:
        """Validate system readiness for legacy code cleanup."""
        checks = {}

        # Check for legacy endpoint guard middleware
        try:
            guard_file = "backend/app/middleware/legacy_endpoint_guard.py"
            checks["legacy_guard_exists"] = os.path.exists(guard_file)
        except OSError:
            checks["legacy_guard_exists"] = False

        # Check policy enforcement script
        try:
            policy_script = "scripts/policy-checks.sh"
            checks["policy_script_exists"] = os.path.exists(policy_script)
        except OSError:
            checks["policy_script_exists"] = False

        # Check for test files that need updates
        test_patterns = [
            "tests/temp/test_discovery_flow_api.py",
            "tests/temp/test_discovery_flow_api_fixed.py",
        ]
        checks["test_files_exist"] = sum(
            1 for pattern in test_patterns if os.path.exists(pattern)
        )

        return checks

    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run all validation checks and return comprehensive results."""
        print("🏥 Starting System Health Validation...")

        # Database connectivity
        print("🔍 Checking database connectivity...")
        self.results["database"] = await self.validate_database_connectivity()

        # API endpoints
        print("🌐 Validating API endpoints...")
        self.results["api_endpoints"] = await self.validate_api_endpoints()

        # System resources
        print("💻 Checking system resources...")
        self.results["system_resources"] = self.validate_system_resources()

        # Docker environment
        print("🐳 Validating Docker environment...")
        self.results["docker"] = self.validate_docker_environment()

        # Legacy cleanup readiness
        print("🧹 Checking legacy cleanup readiness...")
        self.results["cleanup_readiness"] = self.validate_legacy_cleanup_readiness()

        # Overall health assessment
        self.results["overall"] = self._assess_overall_health()

        return self.results

    def _assess_overall_health(self) -> Dict[str, Any]:
        """Assess overall system health based on all checks."""
        critical_failures = len(
            [e for e in self.errors if "database" in e.lower() or "api" in e.lower()]
        )
        total_warnings = len(self.warnings)

        if critical_failures > 0:
            status = "unhealthy"
        elif total_warnings > 2:
            status = "degraded"
        else:
            status = "healthy"

        return {
            "status": status,
            "critical_failures": critical_failures,
            "warnings": total_warnings,
            "timestamp": datetime.utcnow().isoformat(),
            "ready_for_cleanup": critical_failures == 0,
        }

    def print_results(self):
        """Print formatted validation results."""
        print(f"\n{'='*60}")
        print("🏥 SYSTEM HEALTH VALIDATION RESULTS")
        print(f"{'='*60}")

        overall = self.results.get("overall", {})
        status = overall.get("status", "unknown")

        if status == "healthy":
            print("✅ Overall Status: HEALTHY")
        elif status == "degraded":
            print("⚠️  Overall Status: DEGRADED")
        else:
            print("❌ Overall Status: UNHEALTHY")

        print(f"🔍 Critical Failures: {overall.get('critical_failures', 0)}")
        print(f"⚠️  Warnings: {overall.get('warnings', 0)}")
        print(
            f"🧹 Ready for Cleanup: {'✅ YES' if overall.get('ready_for_cleanup') else '❌ NO'}"
        )

        # Database status
        db_status = self.results.get("database", {}).get("status", "unknown")
        print(
            f"\n🗄️  Database: {'✅' if db_status == 'healthy' else '❌'} {db_status.upper()}"
        )

        # API endpoints summary
        api_results = self.results.get("api_endpoints", {})
        accessible_endpoints = sum(
            1
            for ep in api_results.values()
            if isinstance(ep, dict) and ep.get("accessible", False)
        )
        total_endpoints = len(api_results)
        print(f"🌐 API Endpoints: {accessible_endpoints}/{total_endpoints} accessible")

        # System resources
        resources = self.results.get("system_resources", {})
        if "cpu_percent" in resources:
            print(
                f"💻 System Resources: CPU {resources['cpu_percent']}%, Memory {resources['memory_percent']}%"
            )

        # Cleanup readiness
        cleanup = self.results.get("cleanup_readiness", {})
        readiness_score = sum(1 for v in cleanup.values() if v)
        print(f"🧹 Cleanup Readiness: {readiness_score}/{len(cleanup)} checks passed")

        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   • {warning}")

        print(
            f"\n📊 Detailed results saved to: /tmp/system_health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )


async def main():
    """Main execution function."""
    validator = SystemHealthValidator()

    try:
        results = await validator.run_comprehensive_validation()
        validator.print_results()

        # Save detailed results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"/tmp/system_health_{timestamp}.json"

        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        # Exit code based on overall health
        overall_status = results.get("overall", {}).get("status", "unknown")
        if overall_status == "healthy":
            sys.exit(0)
        elif overall_status == "degraded":
            sys.exit(1)  # Warning level
        else:
            sys.exit(2)  # Critical failure

    except KeyboardInterrupt:
        print("\n🛑 Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Validation failed with error: {e}")
        sys.exit(3)


if __name__ == "__main__":
    # Handle both sync and async execution
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Failed to run async validation: {e}")
        sys.exit(4)
