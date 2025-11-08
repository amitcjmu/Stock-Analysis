"""
ApplicationInspector - Inspects CanonicalApplication metadata for completeness.

Performance: <10ms per asset (in-memory checks, no database queries)
Part of Issue #980: Intelligent Multi-Layer Gap Detection System
"""

import logging
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

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

        Args:
            asset: Asset SQLAlchemy model (not directly used)
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

        if application is None:
            # No application linked - all fields missing
            logger.debug(
                "application_not_linked",
                extra={
                    "asset_id": str(asset.id) if hasattr(asset, "id") else None,
                    "asset_name": getattr(asset, "asset_name", None),
                },
            )
            return ApplicationGapReport(
                missing_metadata=self.METADATA_FIELDS,
                incomplete_tech_stack=self.TECH_STACK_FIELDS,
                missing_business_context=self.BUSINESS_CONTEXT_FIELDS,
                completeness_score=0.0,
            )

        missing_metadata = []
        incomplete_tech_stack = []
        missing_business_context = []

        # Check metadata fields
        for field in self.METADATA_FIELDS:
            value = getattr(application, field, None)
            if value is None or (isinstance(value, str) and not value.strip()):
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

        # Calculate completeness score
        total_fields = (
            len(self.METADATA_FIELDS)
            + len(self.TECH_STACK_FIELDS)
            + len(self.BUSINESS_CONTEXT_FIELDS)
        )

        missing_total = (
            len(missing_metadata)
            + len(incomplete_tech_stack)
            + len(missing_business_context)
        )

        if total_fields == 0:
            score = 1.0
        else:
            score = (total_fields - missing_total) / total_fields

        # JSON safety: Clamp and sanitize (GPT-5 Rec #8)
        score = max(0.0, min(1.0, float(score)))

        logger.debug(
            "application_inspector_completed",
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
            },
        )

        return ApplicationGapReport(
            missing_metadata=missing_metadata,
            incomplete_tech_stack=incomplete_tech_stack,
            missing_business_context=missing_business_context,
            completeness_score=score,
        )
