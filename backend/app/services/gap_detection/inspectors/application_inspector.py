"""
ApplicationInspector - Inspects CanonicalApplication metadata for completeness.

Performance: <10ms per asset (in-memory checks, no database queries)
Part of Issue #980: Intelligent Multi-Layer Gap Detection System

CRITICAL: Per Bug #11, this inspector MUST check all 22 critical assessment attributes
to ensure 85% readiness threshold is met. Each attribute is checked individually with
correct gap_category mapping (infrastructure, dependencies, compliance, tech_debt).
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.crewai_flows.tools.critical_attributes_tool.base import (
    CriticalAttributesDefinition,
)
from app.services.gap_detection.schemas import ApplicationGapReport, DataRequirements

from .base import BaseInspector

logger = logging.getLogger(__name__)


class ApplicationInspector(BaseInspector):
    """
    Inspects CanonicalApplication metadata for completeness.

    Checks:
    - Application metadata fields (name, description, type, business unit)
    - Technology stack completeness
    - Business context fields (owners, stakeholders, user base)

    Performance: <10ms per asset (in-memory checks only)

    GPT-5 Recommendations Applied:
    - #1: Tenant scoping parameters included (not used for in-memory checks)
    - #3: Async method signature
    - #8: Completeness score clamped to [0.0, 1.0]
    """

    # Critical CanonicalApplication fields
    METADATA_FIELDS = [
        "canonical_name",
        "description",
        "application_type",
        "business_criticality",
    ]

    TECH_STACK_FIELDS = [
        "technology_stack",
    ]

    # Note: CanonicalApplication model doesn't have these fields yet
    # They may be in JSONB or in separate tables
    BUSINESS_CONTEXT_FIELDS = [
        "created_by",
        "updated_by",
    ]

    async def inspect(
        self,
        asset: Any,
        application: Optional[Any],
        requirements: DataRequirements,
        client_account_id: str,
        engagement_id: str,
        db: Optional[AsyncSession] = None,
    ) -> ApplicationGapReport:
        """
        Validate CanonicalApplication completeness.

        CRITICAL (Bug #11): Now checks ALL 22 critical assessment attributes
        with proper category mapping (infrastructure, dependencies, compliance, tech_debt).

        Args:
            asset: Asset SQLAlchemy model
            application: Optional CanonicalApplication model to inspect
            requirements: DataRequirements (not used - checks standard fields)
            client_account_id: Tenant client account UUID (not used for in-memory checks)
            engagement_id: Engagement UUID (not used for in-memory checks)
            db: Not used by application inspector

        Returns:
            ApplicationGapReport with missing fields and completeness score

        Raises:
            ValueError: If asset is None
        """
        if asset is None:
            raise ValueError("Asset cannot be None")

        # Get critical attributes mapping
        attribute_mapping = CriticalAttributesDefinition.get_attribute_mapping()

        if application is None:
            # No application linked - all fields missing
            logger.debug(
                "application_not_linked",
                extra={
                    "asset_id": str(asset.id) if hasattr(asset, "id") else None,
                    "asset_name": getattr(asset, "asset_name", None),
                },
            )

            # Bug #11: When no application, mark ALL 22 critical attributes as missing
            missing_critical_by_category = self._check_critical_attributes(
                asset, application, attribute_mapping
            )

            return ApplicationGapReport(
                missing_metadata=self.METADATA_FIELDS,
                incomplete_tech_stack=self.TECH_STACK_FIELDS,
                missing_business_context=self.BUSINESS_CONTEXT_FIELDS,
                missing_critical_attributes=missing_critical_by_category,
                completeness_score=0.0,
            )

        missing_metadata = []
        incomplete_tech_stack = []
        missing_business_context = []

        # Check metadata fields
        for field in self.METADATA_FIELDS:
            value = getattr(application, field, None)

            # Special handling for canonical_name: check if asset already has a name
            if field == "canonical_name":
                # If canonical_name is missing, check if asset has a name
                asset_name = getattr(asset, "name", None) or getattr(
                    asset, "asset_name", None
                )
                if (
                    value is None or (isinstance(value, str) and not value.strip())
                ) and not asset_name:
                    # Only flag as missing if both canonical_name and asset name are missing
                    missing_metadata.append(field)
                elif asset_name:
                    # Asset has a name, so canonical_name is not truly missing
                    logger.debug(
                        f"Asset '{asset_name}' already has a name, skipping canonical_name gap",
                        extra={
                            "asset_id": str(asset.id) if hasattr(asset, "id") else None,
                            "asset_name": asset_name,
                        },
                    )
            elif value is None or (isinstance(value, str) and not value.strip()):
                missing_metadata.append(field)

        # Check tech stack fields
        for field in self.TECH_STACK_FIELDS:
            value = getattr(application, field, None)
            if value is None:
                incomplete_tech_stack.append(field)
            elif isinstance(value, dict) and not value:
                incomplete_tech_stack.append(field)
            elif isinstance(value, list) and not value:
                incomplete_tech_stack.append(field)
            elif isinstance(value, str) and not value.strip():
                incomplete_tech_stack.append(field)

        # Check business context fields
        for field in self.BUSINESS_CONTEXT_FIELDS:
            value = getattr(application, field, None)
            if value is None:
                missing_business_context.append(field)
            elif isinstance(value, str) and not value.strip():
                missing_business_context.append(field)

        # Bug #11: Check all 22 critical assessment attributes
        missing_critical_by_category = self._check_critical_attributes(
            asset, application, attribute_mapping
        )

        # Calculate completeness score (now includes critical attributes)
        total_fields = (
            len(self.METADATA_FIELDS)
            + len(self.TECH_STACK_FIELDS)
            + len(self.BUSINESS_CONTEXT_FIELDS)
            + 22  # 22 critical assessment attributes
        )

        missing_total = (
            len(missing_metadata)
            + len(incomplete_tech_stack)
            + len(missing_business_context)
            + sum(len(attrs) for attrs in missing_critical_by_category.values())
        )

        if total_fields == 0:
            score = 1.0
        else:
            score = (total_fields - missing_total) / total_fields

        # JSON safety: Clamp and sanitize (GPT-5 Rec #8)
        score = max(0.0, min(1.0, float(score)))

        logger.info(
            f"application_inspector_completed: {len(missing_critical_by_category)} critical attribute categories, "
            f"{sum(len(attrs) for attrs in missing_critical_by_category.values())} total critical gaps",
            extra={
                "application_id": str(application.id) if application else None,
                "application_name": (
                    getattr(application, "canonical_name", None)
                    if application
                    else None
                ),
                "total_fields": total_fields,
                "missing_total": missing_total,
                "completeness_score": score,
                "missing_critical_by_category": {
                    cat: len(attrs)
                    for cat, attrs in missing_critical_by_category.items()
                },
            },
        )

        return ApplicationGapReport(
            missing_metadata=missing_metadata,
            incomplete_tech_stack=incomplete_tech_stack,
            missing_business_context=missing_business_context,
            missing_critical_attributes=missing_critical_by_category,
            completeness_score=score,
        )

    def _check_critical_attributes(
        self,
        asset: Any,
        application: Optional[Any],
        attribute_mapping: Dict[str, Dict[str, Any]],
    ) -> Dict[str, List[str]]:
        """
        Check all 22 critical assessment attributes with proper category mapping.

        Per Bug #11: Each critical attribute must be checked individually and
        assigned to its correct gap_category (infrastructure, dependencies,
        compliance, tech_debt) so section filtering works properly.

        Args:
            asset: Asset SQLAlchemy model
            application: Optional CanonicalApplication model
            attribute_mapping: CriticalAttributesDefinition.get_attribute_mapping()

        Returns:
            Dict mapping gap_category to list of missing critical attribute names
            Example: {
                "infrastructure": ["operating_system_version", "cpu_memory_storage_specs"],
                "dependencies": ["technology_stack"],
                "compliance": ["business_criticality_score"],
                "tech_debt": []
            }
        """
        missing_by_category: Dict[str, List[str]] = {
            "infrastructure": [],
            "dependencies": [],
            "compliance": [],
            "tech_debt": [],
        }

        for attr_name, attr_config in attribute_mapping.items():
            category = attr_config.get("category", "application")

            # Map "application" category to "dependencies" for section filtering
            # Per section_helpers.py, most application attributes are in dependencies section
            if category == "application":
                category = "dependencies"

            asset_fields = attr_config.get("asset_fields", [])

            # Check if attribute is missing by examining all mapped asset fields
            is_missing = True
            for field in asset_fields:
                if "." in field:  # custom_attributes.field_name
                    parts = field.split(".")
                    if hasattr(asset, parts[0]):
                        custom_attrs = getattr(asset, parts[0])
                        if custom_attrs and isinstance(custom_attrs, dict):
                            if parts[1] in custom_attrs:
                                value = custom_attrs[parts[1]]
                                if value is not None and value != "":
                                    is_missing = False
                                    break
                else:
                    # Check asset or application model directly
                    for obj in [asset, application]:
                        if obj and hasattr(obj, field):
                            value = getattr(obj, field)
                            if value is not None and value != "":
                                is_missing = False
                                break
                    if not is_missing:
                        break

            if is_missing:
                # Ensure category key exists
                if category not in missing_by_category:
                    missing_by_category[category] = []
                missing_by_category[category].append(attr_name)

        total_missing = sum(len(attrs) for attrs in missing_by_category.values())
        num_categories = len(missing_by_category)
        logger.debug(
            f"Critical attributes check: {total_missing} missing "
            f"across {num_categories} categories",
            extra={
                "asset_id": str(asset.id) if hasattr(asset, "id") else None,
                "missing_by_category": {
                    cat: len(attrs) for cat, attrs in missing_by_category.items()
                },
            },
        )

        return missing_by_category
