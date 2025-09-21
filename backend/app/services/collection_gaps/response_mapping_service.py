"""
Response mapping service for collection gaps.

This service handles the mapping of questionnaire responses to appropriate
database tables using the QUESTION_TO_TABLE_MAPPING registry.
"""

import logging
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.governance_repository import (
    ApprovalRequestRepository,
    MigrationExceptionRepository,
)
from app.repositories.maintenance_window_repository import (
    BlackoutPeriodRepository,
    MaintenanceWindowRepository,
)
from app.repositories.resilience_repository import (
    ComplianceRepository,
    LicenseRepository,
    ResilienceRepository,
    VulnerabilityRepository,
)
from app.repositories.vendor_product_repository import (
    AssetProductLinkRepository,
    LifecycleRepository,
    TenantVendorProductRepository,
    VendorProductRepository,
)

logger = logging.getLogger(__name__)

# Mapping configuration as specified in the documentation
QUESTION_TO_TABLE_MAPPING = {
    "vendor_product": {
        "tables": ["tenant_vendor_products", "asset_product_links"],
        "handler": "map_vendor_product",
    },
    "product_version": {
        "tables": ["tenant_product_versions", "asset_product_links"],
        "handler": "map_product_version",
    },
    "lifecycle_dates": {
        "tables": ["lifecycle_milestones"],
        "handler": "map_lifecycle_dates",
    },
    "rto_rpo": {"tables": ["asset_resilience"], "handler": "map_resilience_metrics"},
    "maintenance_window": {
        "tables": ["maintenance_windows"],
        "handler": "map_maintenance_window",
    },
    "blackout_period": {
        "tables": ["blackout_periods"],
        "handler": "map_blackout_period",
    },
    "dependency_mapping": {
        "tables": ["asset_dependencies"],
        "handler": "map_dependencies",
    },
    "compliance_scopes": {
        "tables": ["asset_compliance_flags"],
        "handler": "map_compliance_flags",
    },
    "data_classification": {
        "tables": ["asset_compliance_flags"],
        "handler": "map_compliance_flags",
    },
    "residency": {
        "tables": ["asset_compliance_flags"],
        "handler": "map_compliance_flags",
    },
    "license_type": {"tables": ["asset_licenses"], "handler": "map_license"},
    "license_renewal_date": {"tables": ["asset_licenses"], "handler": "map_license"},
    "vulnerability_scan": {
        "tables": ["asset_vulnerabilities"],
        "handler": "map_vulnerability",
    },
    "exception_request": {
        "tables": ["migration_exceptions", "approval_requests"],
        "handler": "map_exception",
    },
}

# Batch configuration as specified in the documentation
BATCH_CONFIG = {"default_size": 500, "max_size": 1000, "timeout_ms": 5000}


class ResponseMappingService:
    """Service for mapping questionnaire responses to database tables."""

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: str,
        engagement_id: str,
    ):
        """
        Initialize the response mapping service.

        Args:
            db: Database session
            client_account_id: Client account UUID for tenant scoping
            engagement_id: Engagement UUID for project scoping
        """
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

        # Initialize repositories
        self.vendor_product_repo = VendorProductRepository(
            db, client_account_id, engagement_id
        )
        self.tenant_vendor_repo = TenantVendorProductRepository(
            db, client_account_id, engagement_id
        )
        self.lifecycle_repo = LifecycleRepository(db, client_account_id, engagement_id)
        self.asset_link_repo = AssetProductLinkRepository(
            db, client_account_id, engagement_id
        )
        self.resilience_repo = ResilienceRepository(
            db, client_account_id, engagement_id
        )
        self.compliance_repo = ComplianceRepository(
            db, client_account_id, engagement_id
        )
        self.vulnerability_repo = VulnerabilityRepository(
            db, client_account_id, engagement_id
        )
        self.license_repo = LicenseRepository(db, client_account_id, engagement_id)
        self.maintenance_repo = MaintenanceWindowRepository(
            db, client_account_id, engagement_id
        )
        self.blackout_repo = BlackoutPeriodRepository(
            db, client_account_id, engagement_id
        )
        self.approval_repo = ApprovalRequestRepository(
            db, client_account_id, engagement_id
        )
        self.exception_repo = MigrationExceptionRepository(
            db, client_account_id, engagement_id
        )

    async def process_responses_batch(
        self, responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process a batch of questionnaire responses.

        Args:
            responses: List of response dictionaries with question_id, response_value, etc.

        Returns:
            Dictionary with upserted counts by target table
        """
        # Validate batch size
        if len(responses) > BATCH_CONFIG["max_size"]:
            raise ValueError(
                f"Batch size {len(responses)} exceeds maximum {BATCH_CONFIG['max_size']}"
            )

        results = {"upserted": 0, "by_target": {}}
        errors = []

        try:
            async with self.db.begin():  # Start transaction
                for response in responses:
                    try:
                        await self._process_single_response(response, results)
                    except Exception as e:
                        logger.error(
                            f"Error processing response {response.get('question_id', 'unknown')}: {e}"
                        )
                        errors.append(
                            {
                                "question_id": response.get("question_id"),
                                "error": str(e),
                            }
                        )

                logger.info(f"Processed batch of {len(responses)} responses: {results}")

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            raise

        if errors:
            results["errors"] = errors

        return results

    async def _process_single_response(
        self, response: Dict[str, Any], results: Dict[str, Any]
    ) -> None:
        """
        Process a single questionnaire response.

        Args:
            response: Response dictionary
            results: Results dictionary to update
        """
        question_id = response.get("question_id")
        if not question_id:
            raise ValueError("Missing question_id in response")

        # Check if we have a mapping for this question
        mapping = QUESTION_TO_TABLE_MAPPING.get(question_id)
        if not mapping:
            # For unmapped questions, try direct field mapping
            await self._handle_direct_field_mapping(response, results)
            return

        # Get the handler method
        handler_name = mapping["handler"]
        handler_method = getattr(self, handler_name, None)
        if not handler_method:
            raise ValueError(f"Handler method {handler_name} not found")

        # Call the handler
        affected_tables = await handler_method(response)

        # Update results
        results["upserted"] += 1
        for table in affected_tables:
            results["by_target"][table] = results["by_target"].get(table, 0) + 1

    async def _handle_direct_field_mapping(
        self, response: Dict[str, Any], results: Dict[str, Any]
    ) -> None:
        """
        Handle direct field mapping for simple cases.

        Args:
            response: Response dictionary
            results: Results dictionary to update
        """
        question_id = response["question_id"]

        # For now, log unmapped questions for analysis
        logger.warning(f"No mapping found for question_id: {question_id}")

        # Could implement direct field updates here for simple cases
        # For example: asset.field_name = response_value

    async def map_vendor_product(self, response: Dict[str, Any]) -> List[str]:
        """
        Map vendor/product response to tenant_vendor_products and asset_product_links.

        Args:
            response: Response containing vendor/product information

        Returns:
            List of affected table names
        """
        vendor_name = response.get("metadata", {}).get("vendor_name")
        product_name = response.get("metadata", {}).get("product_name")
        asset_id = response.get("asset_id")
        confidence_score = response.get("metadata", {}).get("confidence_score", 0.8)

        if not vendor_name or not product_name:
            raise ValueError("Missing vendor_name or product_name in response metadata")

        affected_tables = []

        # Create or find tenant vendor product
        tenant_product = await self.tenant_vendor_repo.create_custom_product(
            vendor_name=vendor_name,
            product_name=product_name,
            commit=False,  # We're in a transaction
        )
        affected_tables.append("tenant_vendor_products")

        # If asset_id provided, create asset-product link
        if asset_id:
            await self.asset_link_repo.link_asset_to_product(
                asset_id=asset_id,
                tenant_version_id=str(
                    tenant_product.id
                ),  # Link to tenant product for now
                confidence_score=confidence_score,
                matched_by="questionnaire",
                commit=False,
            )
            affected_tables.append("asset_product_links")

        return affected_tables

    async def map_product_version(self, response: Dict[str, Any]) -> List[str]:
        """
        Map product version response.

        Args:
            response: Response containing version information

        Returns:
            List of affected table names
        """
        # Implementation would handle product version mapping
        # For now, return empty list as stub
        logger.info(f"Processing product version mapping: {response}")
        return ["tenant_product_versions"]

    async def map_lifecycle_dates(self, response: Dict[str, Any]) -> List[str]:
        """
        Map lifecycle dates to lifecycle_milestones.

        Args:
            response: Response containing lifecycle date information

        Returns:
            List of affected table names
        """
        milestone_type = response.get("metadata", {}).get(
            "milestone_type", "end_of_life"
        )
        milestone_date = response.get("response_value")
        source = response.get("metadata", {}).get("source", "questionnaire")

        if not milestone_date:
            raise ValueError("Missing milestone_date in response")

        # For now, create a lifecycle milestone (would need product version context in real implementation)
        await self.lifecycle_repo.create(
            milestone_type=milestone_type,
            milestone_date=milestone_date,
            source=source,
            provenance={"questionnaire_response": response},
            commit=False,
        )

        return ["lifecycle_milestones"]

    async def map_resilience_metrics(self, response: Dict[str, Any]) -> List[str]:
        """
        Map RTO/RPO metrics to asset_resilience.

        Args:
            response: Response containing resilience metrics

        Returns:
            List of affected table names
        """
        asset_id = response.get("asset_id")
        if not asset_id:
            raise ValueError("Missing asset_id for resilience metrics")

        rto_minutes = response.get("metadata", {}).get("rto_minutes")
        rpo_minutes = response.get("metadata", {}).get("rpo_minutes")
        sla_targets = response.get("metadata", {}).get("sla_targets", {})

        await self.resilience_repo.upsert_resilience(
            asset_id=asset_id,
            rto_minutes=rto_minutes,
            rpo_minutes=rpo_minutes,
            sla_json=sla_targets,
            commit=False,
        )

        return ["asset_resilience"]

    async def map_maintenance_window(self, response: Dict[str, Any]) -> List[str]:
        """
        Map maintenance window response.

        Args:
            response: Response containing maintenance window information

        Returns:
            List of affected table names
        """
        name = response.get("metadata", {}).get("name", "Scheduled Maintenance")
        start_time = response.get("metadata", {}).get("start_time")
        end_time = response.get("metadata", {}).get("end_time")
        scope_type = response.get("metadata", {}).get("scope_type", "tenant")

        if not start_time or not end_time:
            raise ValueError("Missing start_time or end_time for maintenance window")

        await self.maintenance_repo.create_window(
            name=name,
            start_time=start_time,
            end_time=end_time,
            scope_type=scope_type,
            commit=False,
        )

        return ["maintenance_windows"]

    async def map_blackout_period(self, response: Dict[str, Any]) -> List[str]:
        """
        Map blackout period response.

        Args:
            response: Response containing blackout period information

        Returns:
            List of affected table names
        """
        start_date = response.get("metadata", {}).get("start_date")
        end_date = response.get("metadata", {}).get("end_date")
        scope_type = response.get("metadata", {}).get("scope_type", "tenant")
        reason = response.get("metadata", {}).get("reason", "Migration blackout")

        if not start_date or not end_date:
            raise ValueError("Missing start_date or end_date for blackout period")

        await self.blackout_repo.create_blackout(
            start_date=start_date,
            end_date=end_date,
            scope_type=scope_type,
            reason=reason,
            commit=False,
        )

        return ["blackout_periods"]

    async def map_dependencies(self, response: Dict[str, Any]) -> List[str]:
        """
        Map dependency relationships to asset_dependencies.

        Args:
            response: Response containing dependency information

        Returns:
            List of affected table names
        """
        # For now, log that this would update asset_dependencies
        logger.info(f"Processing dependency mapping: {response}")
        return ["asset_dependencies"]

    async def map_compliance_flags(self, response: Dict[str, Any]) -> List[str]:
        """
        Map compliance information to asset_compliance_flags.

        Args:
            response: Response containing compliance information

        Returns:
            List of affected table names
        """
        asset_id = response.get("asset_id")
        if not asset_id:
            raise ValueError("Missing asset_id for compliance flags")

        question_id = response["question_id"]
        response_value = response.get("response_value")

        update_data = {}
        if question_id == "compliance_scopes":
            update_data["compliance_scopes"] = (
                response_value if isinstance(response_value, list) else [response_value]
            )
        elif question_id == "data_classification":
            update_data["data_classification"] = response_value
        elif question_id == "residency":
            update_data["residency"] = response_value

        await self.compliance_repo.upsert_compliance(
            asset_id=asset_id, commit=False, **update_data
        )

        return ["asset_compliance_flags"]

    async def map_license(self, response: Dict[str, Any]) -> List[str]:
        """
        Map license information to asset_licenses.

        Args:
            response: Response containing license information

        Returns:
            List of affected table names
        """
        asset_id = response.get("asset_id")
        if not asset_id:
            raise ValueError("Missing asset_id for license information")

        question_id = response["question_id"]
        response_value = response.get("response_value")

        license_data = {}
        if question_id == "license_type":
            license_data["license_type"] = response_value
        elif question_id == "license_renewal_date":
            license_data["renewal_date"] = response_value

        # Add other license fields from metadata
        metadata = response.get("metadata", {})
        if "contract_reference" in metadata:
            license_data["contract_reference"] = metadata["contract_reference"]
        if "support_tier" in metadata:
            license_data["support_tier"] = metadata["support_tier"]

        await self.license_repo.upsert_license(
            asset_id=asset_id, commit=False, **license_data
        )

        return ["asset_licenses"]

    async def map_vulnerability(self, response: Dict[str, Any]) -> List[str]:
        """
        Map vulnerability information to asset_vulnerabilities.

        Args:
            response: Response containing vulnerability information

        Returns:
            List of affected table names
        """
        asset_id = response.get("asset_id")
        if not asset_id:
            raise ValueError("Missing asset_id for vulnerability information")

        metadata = response.get("metadata", {})
        await self.vulnerability_repo.add_vulnerability(
            asset_id=asset_id,
            cve_id=metadata.get("cve_id"),
            severity=metadata.get("severity"),
            source="questionnaire",
            details=metadata,
            commit=False,
        )

        return ["asset_vulnerabilities"]

    async def map_exception(self, response: Dict[str, Any]) -> List[str]:
        """
        Map exception request to migration_exceptions and approval_requests.

        Args:
            response: Response containing exception request information

        Returns:
            List of affected table names
        """
        exception_type = response.get("metadata", {}).get("exception_type")
        rationale = response.get("response_value")
        risk_level = response.get("metadata", {}).get("risk_level", "medium")
        asset_id = response.get("asset_id")
        application_id = response.get("application_id")

        if not exception_type or not rationale:
            raise ValueError(
                "Missing exception_type or rationale for exception request"
            )

        # Create migration exception
        exception = await self.exception_repo.create_exception(
            exception_type=exception_type,
            rationale=rationale,
            risk_level=risk_level,
            asset_id=asset_id,
            application_id=application_id,
            commit=False,
        )

        affected_tables = ["migration_exceptions"]

        # Create approval request if needed for high-risk exceptions
        if risk_level in ["high", "critical"] or exception_type in [
            "custom_approach",
            "skip_migration",
        ]:
            approval_request = await self.approval_repo.create_request(
                entity_type="exception",
                entity_id=str(exception.id),
                notes=f"Approval required for {risk_level} risk {exception_type} exception",
                commit=False,
            )

            # Link exception to approval request
            await self.exception_repo.update(
                exception.id, approval_request_id=str(approval_request.id), commit=False
            )

            affected_tables.append("approval_requests")

        return affected_tables
