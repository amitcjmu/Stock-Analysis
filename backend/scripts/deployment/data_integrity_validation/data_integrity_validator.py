"""
Main data integrity validator class.
Coordinates all validation checks and provides comprehensive reporting.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from .constraint_validator import ConstraintValidator
from .foreign_key_validator import ForeignKeyValidator
from .orphaned_records_checker import OrphanedRecordsChecker
from .performance_validator import PerformanceValidator
from .tenant_isolation_validator import TenantIsolationValidator

logger = logging.getLogger(__name__)


class DataIntegrityValidator:
    """
    Production data integrity validator for the discovery flow system.

    This class provides comprehensive validation of data relationships,
    constraints, and performance characteristics in production environments.
    """

    def __init__(
        self,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
        fix_issues: bool = False,
    ):
        """
        Initialize the data integrity validator.

        Args:
            client_account_id: Optional client account ID to limit scope
            engagement_id: Optional engagement ID to limit scope
            fix_issues: Whether to attempt to fix identified issues
        """
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.fix_issues = fix_issues
        self.issues_found = []
        self.performance_metrics = {}

        # Initialize component validators
        self.foreign_key_validator = ForeignKeyValidator(
            client_account_id, engagement_id
        )
        self.orphaned_records_checker = OrphanedRecordsChecker(
            client_account_id, engagement_id, fix_issues
        )
        self.constraint_validator = ConstraintValidator(
            client_account_id, engagement_id, fix_issues
        )
        self.performance_validator = PerformanceValidator(
            client_account_id, engagement_id
        )
        self.tenant_isolation_validator = TenantIsolationValidator(
            client_account_id, engagement_id
        )

    async def validate_all(self) -> Dict[str, Any]:
        """
        Run complete data integrity validation.

        Returns:
            Dict containing validation results and performance metrics
        """
        logger.info("🚀 Starting comprehensive data integrity validation")
        start_time = datetime.utcnow()

        validation_results = {
            "validation_id": f"integrity_check_{start_time.strftime('%Y%m%d_%H%M%S')}",
            "start_time": start_time.isoformat(),
            "scope": {
                "client_account_id": self.client_account_id,
                "engagement_id": self.engagement_id,
                "fix_issues_enabled": self.fix_issues,
            },
            "overall_status": "UNKNOWN",
            "validation_components": {},
            "summary": {},
            "issues_found": [],
            "recommendations": [],
        }

        try:
            # Import database session here to avoid circular imports
            from app.core.database import AsyncSessionLocal

            async with AsyncSessionLocal() as session:
                # 1. Validate foreign key relationships
                logger.info("🔗 Step 1/6: Validating foreign key relationships")
                fk_results = (
                    await self.foreign_key_validator.validate_foreign_key_relationships(
                        session
                    )
                )
                validation_results["validation_components"]["foreign_keys"] = fk_results
                if not fk_results["valid"]:
                    validation_results["issues_found"].extend(fk_results["issues"])

                # 2. Check for orphaned records
                logger.info("🔍 Step 2/6: Checking for orphaned records")
                orphan_results = (
                    await self.orphaned_records_checker.check_orphaned_records(session)
                )
                validation_results["validation_components"][
                    "orphaned_records"
                ] = orphan_results
                if not orphan_results["valid"]:
                    validation_results["issues_found"].extend(orphan_results["issues"])

                # 3. Validate cascade configuration
                logger.info("🔗 Step 3/6: Validating cascade configuration")
                cascade_results = (
                    await self.constraint_validator.validate_cascade_configuration(
                        session
                    )
                )
                validation_results["validation_components"][
                    "cascade_config"
                ] = cascade_results
                if not cascade_results["valid"]:
                    validation_results["issues_found"].extend(cascade_results["issues"])

                # 4. Test constraint enforcement
                logger.info("🧪 Step 4/6: Testing constraint enforcement")
                constraint_results = (
                    await self.constraint_validator.test_constraint_enforcement(session)
                )
                validation_results["validation_components"][
                    "constraint_enforcement"
                ] = constraint_results
                if not constraint_results["valid"]:
                    validation_results["issues_found"].extend(
                        constraint_results["issues"]
                    )

                # 5. Validate query performance
                logger.info("⚡ Step 5/6: Validating query performance")
                performance_results = (
                    await self.performance_validator.validate_query_performance(session)
                )
                validation_results["validation_components"][
                    "query_performance"
                ] = performance_results
                if not performance_results["valid"]:
                    validation_results["issues_found"].extend(
                        performance_results["issues"]
                    )

                # 6. Validate tenant isolation
                logger.info("🏢 Step 6/6: Validating tenant isolation")
                tenant_results = (
                    await self.tenant_isolation_validator.validate_tenant_isolation(
                        session
                    )
                )
                validation_results["validation_components"][
                    "tenant_isolation"
                ] = tenant_results
                if not tenant_results["valid"]:
                    validation_results["issues_found"].extend(tenant_results["issues"])

            # Generate summary and recommendations
            validation_results["summary"] = self._generate_summary(validation_results)
            validation_results["recommendations"] = self._generate_recommendations(
                validation_results
            )

            # Determine overall status
            total_issues = len(validation_results["issues_found"])
            if total_issues == 0:
                validation_results["overall_status"] = "HEALTHY"
                logger.info(
                    "✅ Data integrity validation completed successfully - no issues found"
                )
            elif total_issues <= 5:
                validation_results["overall_status"] = "WARNING"
                logger.warning(
                    f"⚠️ Data integrity validation completed with {total_issues} issues"
                )
            else:
                validation_results["overall_status"] = "CRITICAL"
                logger.error(
                    f"❌ Data integrity validation found {total_issues} critical issues"
                )

        except Exception as e:
            logger.error(
                f"❌ Data integrity validation failed: {str(e)}", exc_info=True
            )
            validation_results["overall_status"] = "ERROR"
            validation_results["error"] = str(e)
            validation_results["issues_found"].append(
                f"Validation process failed: {str(e)}"
            )

        finally:
            end_time = datetime.utcnow()
            validation_results["end_time"] = end_time.isoformat()
            validation_results["duration_seconds"] = (
                end_time - start_time
            ).total_seconds()

        return validation_results

    def _generate_summary(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of validation results"""
        components = validation_results["validation_components"]

        summary = {
            "components_tested": len(components),
            "components_passed": sum(
                1 for comp in components.values() if comp.get("valid", False)
            ),
            "total_issues": len(validation_results["issues_found"]),
            "component_status": {},
        }

        # Generate per-component status
        for component_name, component_results in components.items():
            summary["component_status"][component_name] = {
                "status": "PASS" if component_results.get("valid", False) else "FAIL",
                "issues_count": len(component_results.get("issues", [])),
            }

            # Add component-specific metrics
            if component_name == "orphaned_records":
                summary["component_status"][component_name]["orphaned_records"] = (
                    component_results.get("total_orphaned_records", 0)
                )
                summary["component_status"][component_name]["cleaned_records"] = (
                    component_results.get("cleaned_records", 0)
                )
            elif component_name == "foreign_keys":
                summary["component_status"][component_name]["relationships_checked"] = (
                    component_results.get("relationships_checked", 0)
                )
                summary["component_status"][component_name]["broken_relationships"] = (
                    len(component_results.get("broken_relationships", []))
                )
            elif component_name == "query_performance":
                summary["component_status"][component_name]["performance_score"] = (
                    component_results.get("performance_score", 0.0)
                )
                summary["component_status"][component_name]["slow_queries"] = len(
                    component_results.get("slow_queries", [])
                )

        return summary

    def _generate_recommendations(self, validation_results: Dict[str, Any]) -> list:
        """Generate actionable recommendations based on validation results"""
        recommendations = []
        components = validation_results["validation_components"]

        # Foreign key recommendations
        fk_results = components.get("foreign_keys", {})
        if not fk_results.get("valid", True):
            recommendations.append(
                {
                    "priority": "HIGH",
                    "category": "Data Integrity",
                    "title": "Fix Broken Foreign Key Relationships",
                    "description": f"Found {len(fk_results.get('broken_relationships', []))} "
                    f"broken foreign key relationships",
                    "action": "Review and fix orphaned foreign key references or establish missing parent records",
                }
            )

        # Orphaned records recommendations
        orphan_results = components.get("orphaned_records", {})
        if orphan_results.get("total_orphaned_records", 0) > 0:
            recommendations.append(
                {
                    "priority": "MEDIUM",
                    "category": "Data Cleanup",
                    "title": "Clean Up Orphaned Records",
                    "description": f"Found {orphan_results.get('total_orphaned_records', 0)} orphaned records",
                    "action": (
                        "Run the validator with --fix-issues flag to automatically clean up orphaned records"
                        if not self.fix_issues
                        else "Continue monitoring for new orphaned records"
                    ),
                }
            )

        # Performance recommendations
        perf_results = components.get("query_performance", {})
        if perf_results.get("slow_queries"):
            recommendations.append(
                {
                    "priority": "MEDIUM",
                    "category": "Performance",
                    "title": "Optimize Slow Queries",
                    "description": f"Found {len(perf_results.get('slow_queries', []))} slow queries",
                    "action": "Review query execution plans and add appropriate indexes",
                }
            )

        # Constraint recommendations
        constraint_results = components.get("constraint_enforcement", {})
        if constraint_results.get("failed_tests"):
            recommendations.append(
                {
                    "priority": "HIGH",
                    "category": "Database Schema",
                    "title": "Fix Constraint Enforcement Issues",
                    "description": f"Found {len(constraint_results.get('failed_tests', []))} "
                    f"constraint enforcement failures",
                    "action": "Review and fix database schema constraints to ensure data integrity",
                }
            )

        # Cascade configuration recommendations
        cascade_results = components.get("cascade_config", {})
        if cascade_results.get("missing_cascades"):
            recommendations.append(
                {
                    "priority": "HIGH",
                    "category": "Database Schema",
                    "title": "Configure Missing Cascade Rules",
                    "description": f"Found {len(cascade_results.get('missing_cascades', []))} "
                    f"missing cascade configurations",
                    "action": "Add appropriate CASCADE or RESTRICT rules to foreign key constraints",
                }
            )

        # Tenant isolation recommendations
        tenant_results = components.get("tenant_isolation", {})
        if not tenant_results.get("valid", True):
            recommendations.append(
                {
                    "priority": "CRITICAL",
                    "category": "Security",
                    "title": "Fix Tenant Isolation Issues",
                    "description": "Multi-tenant data isolation is not properly enforced",
                    "action": "Review and fix tenant isolation implementation to prevent data leakage",
                }
            )

        # Default recommendation if everything is healthy
        if not recommendations:
            recommendations.append(
                {
                    "priority": "LOW",
                    "category": "Maintenance",
                    "title": "Continue Regular Monitoring",
                    "description": "Data integrity validation passed successfully",
                    "action": "Schedule regular integrity checks to maintain database health",
                }
            )

        return recommendations
