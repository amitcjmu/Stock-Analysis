"""
Asset Field Update Service (Issue #911)

Handles AI grid editing for asset inventory with field validation
and type checking. Supports both single field and bulk updates.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import (
    AssetType,
    AssetStatus,
    SixRStrategy,
    CriticalityLevel,
    ComplexityLevel,
    RiskLevel,
)
from app.repositories.asset_repository import AssetRepository
from app.schemas.asset_schemas import (
    AssetFieldUpdateResponse,
    BulkAssetUpdateResponse,
    AssetFieldUpdateRequest,
)

logger = logging.getLogger(__name__)


# Issue #911: Define allowed editable fields
# These are the fields that can be edited via the AI grid interface
ALLOWED_EDITABLE_FIELDS: Set[str] = {
    # Identification fields
    "name",
    "asset_name",
    "hostname",
    "description",
    "asset_type",
    # Technical specs
    "operating_system",
    "os_version",
    "cpu_cores",
    "memory_gb",
    "storage_gb",
    # Network info
    "ip_address",
    "fqdn",
    "mac_address",
    # Business fields
    "business_owner",
    "technical_owner",
    "business_unit",
    "department",
    "environment",
    "business_criticality",
    # Assessment fields
    "six_r_strategy",
    "migration_complexity",
    "risk_level",
    "status",
    # CMDB enhancement fields
    "vendor",
    "application_type",
    "lifecycle",
    "hosting_model",
    "server_role",
    "security_zone",
    "database_type",
    "database_version",
    "database_size_gb",
    # Performance metrics
    "cpu_utilization_percent_max",
    "memory_utilization_percent_max",
    "storage_free_gb",
    "storage_used_gb",
    # Compliance and security
    "tech_debt_flags",
    "pii_flag",
    "application_data_classification",
    "has_saas_replacement",
    # Planning
    "proposed_treatmentplan_rationale",
    "annual_cost_estimate",
    "backup_policy",
    "tshirt_size",
    # Relationships (CC FIX: Issue #962 - dependencies multi-select)
    "dependencies",
    "dependents",
}


# Field type definitions for validation
NUMERIC_FIELDS: Set[str] = {
    "cpu_cores",
    "memory_gb",
    "storage_gb",
    "database_size_gb",
    "cpu_utilization_percent_max",
    "memory_utilization_percent_max",
    "storage_free_gb",
    "storage_used_gb",
    "annual_cost_estimate",
}

INTEGER_FIELDS: Set[str] = {"cpu_cores"}

FLOAT_FIELDS: Set[str] = NUMERIC_FIELDS - INTEGER_FIELDS

BOOLEAN_FIELDS: Set[str] = {"pii_flag", "has_saas_replacement"}

ENUM_FIELDS: Dict[str, type] = {
    "asset_type": AssetType,
    "status": AssetStatus,
    "six_r_strategy": SixRStrategy,
    "business_criticality": CriticalityLevel,
    "migration_complexity": ComplexityLevel,
    "risk_level": RiskLevel,
}

STRING_FIELDS: Set[str] = (
    ALLOWED_EDITABLE_FIELDS - NUMERIC_FIELDS - BOOLEAN_FIELDS - set(ENUM_FIELDS.keys())
)


class FieldValidationError(ValueError):
    """Raised when field validation fails."""

    pass


class AssetFieldUpdateService:
    """
    Service for updating individual asset fields with validation.

    Follows 7-layer architecture pattern:
    - Validates field names and types
    - Ensures tenant scoping
    - Maintains audit trail
    """

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: str,
        engagement_id: str,
    ):
        """
        Initialize the asset field update service.

        Args:
            db: Database session
            client_account_id: Client account ID for tenant scoping
            engagement_id: Engagement ID for tenant scoping
        """
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.repository = AssetRepository(
            db=db,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
        )

    def validate_field_name(self, field_name: str) -> None:
        """
        Validate that the field name is allowed for editing.

        Args:
            field_name: Field name to validate

        Raises:
            FieldValidationError: If field is not editable
        """
        if field_name not in ALLOWED_EDITABLE_FIELDS:
            raise FieldValidationError(
                f"Field '{field_name}' is not editable or does not exist"
            )

    def validate_field_value(self, field_name: str, value: Any) -> Any:  # noqa: C901
        """
        Validate and convert field value to the correct type.

        Args:
            field_name: Field name being updated
            value: Value to validate and convert

        Returns:
            Validated and type-converted value

        Raises:
            FieldValidationError: If value is invalid for field type
        """
        # Handle None/null values
        if value is None:
            return None

        # Integer fields
        if field_name in INTEGER_FIELDS:
            try:
                return int(value)
            except (ValueError, TypeError) as e:
                raise FieldValidationError(
                    f"Field '{field_name}' requires an integer value, got {type(value).__name__}"
                ) from e

        # Float fields
        if field_name in FLOAT_FIELDS:
            try:
                return float(value)
            except (ValueError, TypeError) as e:
                raise FieldValidationError(
                    f"Field '{field_name}' requires a numeric value, got {type(value).__name__}"
                ) from e

        # Boolean fields - strict validation
        if field_name in BOOLEAN_FIELDS:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                if value.lower() == "true":
                    return True
                if value.lower() == "false":
                    return False
            raise FieldValidationError(
                f"Field '{field_name}' requires a boolean value (true/false), got '{value}'"
            )

        # Enum fields
        if field_name in ENUM_FIELDS:
            enum_class = ENUM_FIELDS[field_name]
            try:
                # If value is already an enum instance, return its value
                if isinstance(value, enum_class):
                    return value.value
                # Try to get the enum value
                if isinstance(value, str):
                    # Check if it's a valid enum value
                    for enum_member in enum_class:
                        if enum_member.value == value.lower():
                            return value.lower()
                    raise ValueError(
                        f"Invalid value '{value}' for {enum_class.__name__}"
                    )
                raise ValueError(f"Invalid type for {enum_class.__name__}")
            except (ValueError, AttributeError) as e:
                valid_values = [e.value for e in enum_class]
                raise FieldValidationError(
                    f"Field '{field_name}' must be one of {valid_values}, got '{value}'"
                ) from e

        # String fields - convert to string
        if field_name in STRING_FIELDS:
            return str(value) if value is not None else None

        # Unknown field type (shouldn't happen if validate_field_name passed)
        return value

    async def update_single_field(
        self,
        asset_id: UUID,
        field_name: str,
        request: AssetFieldUpdateRequest,
    ) -> AssetFieldUpdateResponse:
        """
        Update a single field on an asset.

        Args:
            asset_id: Asset ID to update
            field_name: Field name to update
            request: Request containing new value and metadata

        Returns:
            Response with old and new values

        Raises:
            FieldValidationError: If field or value is invalid
            ValueError: If asset not found or not accessible
        """
        # Validate field name
        self.validate_field_name(field_name)

        # Get asset with tenant scoping
        asset = await self.repository.get_by_id(asset_id)
        if not asset:
            raise ValueError(
                f"Asset {asset_id} not found or not accessible in this account/engagement"
            )

        # Store old value
        old_value = getattr(asset, field_name, None)

        # Validate and convert new value
        new_value = self.validate_field_value(field_name, request.value)

        # Update the asset
        update_data = {
            field_name: new_value,
            "updated_at": datetime.utcnow(),
        }
        if request.updated_by:
            update_data["updated_by"] = request.updated_by

        updated_asset = await self.repository.update(asset_id, **update_data)

        logger.info(
            f"Updated asset {asset_id} field '{field_name}' from '{old_value}' to '{new_value}' "
            f"(tenant: {self.client_account_id}/{self.engagement_id})"
        )

        return AssetFieldUpdateResponse(
            asset_id=asset_id,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            updated_at=updated_asset.updated_at,
            updated_by=request.updated_by,
        )

    async def bulk_update_fields(
        self,
        updates: List[Dict[str, Any]],
        updated_by: Optional[UUID] = None,
    ) -> BulkAssetUpdateResponse:
        """
        Perform bulk field updates on multiple assets.

        Args:
            updates: List of updates (asset_id, field_name, value)
            updated_by: User ID performing the updates

        Returns:
            Response with success/failure counts and details
        """
        success_count = 0
        failure_count = 0
        updated_assets: List[AssetFieldUpdateResponse] = []
        errors: List[Dict[str, Any]] = []

        for update_item in updates:
            try:
                asset_id = update_item["asset_id"]
                field_name = update_item["field_name"]
                value = update_item["value"]

                # Create request object
                request = AssetFieldUpdateRequest(
                    value=value,
                    updated_by=updated_by,
                )

                # Update the field
                result = await self.update_single_field(
                    asset_id=asset_id,
                    field_name=field_name,
                    request=request,
                )

                updated_assets.append(result)
                success_count += 1

            except Exception as e:
                failure_count += 1
                errors.append(
                    {
                        "asset_id": str(update_item.get("asset_id", "unknown")),
                        "field_name": update_item.get("field_name", "unknown"),
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                )
                logger.error(
                    f"Failed to update asset {update_item.get('asset_id')} "
                    f"field {update_item.get('field_name')}: {e}"
                )

        logger.info(
            f"Bulk update completed: {success_count} succeeded, {failure_count} failed "
            f"(tenant: {self.client_account_id}/{self.engagement_id})"
        )

        return BulkAssetUpdateResponse(
            success_count=success_count,
            failure_count=failure_count,
            updated_assets=updated_assets,
            errors=errors,
        )
