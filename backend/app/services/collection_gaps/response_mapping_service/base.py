"""
Base classes and configuration for response mapping service.

Contains the core configuration, constants, and base functionality
for mapping questionnaire responses to database tables.
"""

import logging
from typing import Any, Dict

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


class BaseResponseMapper:
    """Base class for response mapping functionality."""

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: str,
        engagement_id: str,
    ):
        """Initialize base mapper with database session and tenant context."""
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

        # Initialize repositories with tenant context
        self._init_repositories()

    def _init_repositories(self):
        """Initialize all repositories with tenant context."""
        # Vendor/Product repositories
        self.vendor_product_repo = VendorProductRepository(
            self.db, self.client_account_id, self.engagement_id
        )
        self.tenant_vendor_product_repo = TenantVendorProductRepository(
            self.db, self.client_account_id, self.engagement_id
        )
        self.asset_product_link_repo = AssetProductLinkRepository(
            self.db, self.client_account_id, self.engagement_id
        )
        self.lifecycle_repo = LifecycleRepository(
            self.db, self.client_account_id, self.engagement_id
        )

        # Resilience repositories
        self.resilience_repo = ResilienceRepository(
            self.db, self.client_account_id, self.engagement_id
        )
        self.compliance_repo = ComplianceRepository(
            self.db, self.client_account_id, self.engagement_id
        )
        self.license_repo = LicenseRepository(
            self.db, self.client_account_id, self.engagement_id
        )
        self.vulnerability_repo = VulnerabilityRepository(
            self.db, self.client_account_id, self.engagement_id
        )

        # Maintenance repositories
        self.maintenance_window_repo = MaintenanceWindowRepository(
            self.db, self.client_account_id, self.engagement_id
        )
        self.blackout_period_repo = BlackoutPeriodRepository(
            self.db, self.client_account_id, self.engagement_id
        )

        # Governance repositories
        self.migration_exception_repo = MigrationExceptionRepository(
            self.db, self.client_account_id, self.engagement_id
        )
        self.approval_request_repo = ApprovalRequestRepository(
            self.db, self.client_account_id, self.engagement_id
        )

    async def _handle_direct_field_mapping(
        self, response: Dict[str, Any], field_name: str, model_field: str
    ) -> str:
        """
        Handle direct field mapping between response and model.

        Args:
            response: Response data dictionary
            field_name: Field name in the response
            model_field: Corresponding field in the database model

        Returns:
            String identifier of created/updated record
        """
        # This would implement direct field mapping logic
        # For now, return a placeholder since the exact implementation
        # depends on the specific use case
        return f"mapped_{field_name}_to_{model_field}"
