"""
StandardsInspector - Validates asset against EngagementArchitectureStandard.

CRITICAL: This is the ONLY inspector requiring database access.
Queries with tenant scoping (client_account_id + engagement_id).

Performance: <50ms per asset (cached standards query)
Part of Issue #980: Intelligent Multi-Layer Gap Detection System
"""

import logging
from typing import Any, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment_flow.core_models import EngagementArchitectureStandard
from app.services.gap_detection.schemas import (
    DataRequirements,
    StandardsGapReport,
    StandardViolation,
)

from .base import BaseInspector

logger = logging.getLogger(__name__)


class StandardsInspector(BaseInspector):
    """
    Validates asset against EngagementArchitectureStandard.

    CRITICAL: This is the ONLY inspector requiring database access.
    Queries with tenant scoping (client_account_id + engagement_id).

    Performance: <50ms per asset (cached standards query)

    GPT-5 Recommendations Applied:
    - #1: Tenant scoping on all database queries (MANDATORY)
    - #3: Async method signature
    - #8: Completeness score clamped to [0.0, 1.0]
    """

    async def inspect(
        self,
        asset: Any,
        application: Optional[Any],
        requirements: DataRequirements,
        client_account_id: str,
        engagement_id: str,
        db: AsyncSession,  # ← REQUIRED for standards inspector
    ) -> StandardsGapReport:
        """
        Validate asset against engagement architecture standards.

        Queries EngagementArchitectureStandard with tenant scoping (GPT-5 Rec #1).

        Args:
            asset: Asset SQLAlchemy model to validate
            application: Optional CanonicalApplication (used as fallback for fields)
            requirements: DataRequirements (not used - standards come from DB)
            client_account_id: Tenant client account UUID (REQUIRED for query scoping)
            engagement_id: Engagement UUID (REQUIRED for query scoping)
            db: Async database session (REQUIRED for standards query)

        Returns:
            StandardsGapReport with violations and override requirements

        Raises:
            ValueError: If asset, client_account_id, engagement_id, or db are None
        """
        if asset is None:
            raise ValueError("Asset cannot be None")
        if not client_account_id:
            raise ValueError("client_account_id is required for tenant scoping")
        if not engagement_id:
            raise ValueError("engagement_id is required for tenant scoping")
        if db is None:
            logger.error(
                "standards_inspector_requires_db",
                extra={
                    "asset_id": str(asset.id) if hasattr(asset, "id") else None,
                    "client_account_id": client_account_id,
                    "engagement_id": engagement_id,
                },
            )
            return StandardsGapReport(
                violated_standards=[],
                missing_mandatory_data=[
                    "Database session required for standards validation"
                ],
                override_required=False,
                completeness_score=0.0,
            )

        # Query standards with tenant scoping (GPT-5 Rec #1)
        stmt = select(EngagementArchitectureStandard).where(
            EngagementArchitectureStandard.client_account_id == client_account_id,
            EngagementArchitectureStandard.engagement_id == engagement_id,
        )

        result = await db.execute(stmt)
        standards = result.scalars().all()

        if not standards:
            # No standards defined for this engagement
            logger.debug(
                "no_standards_defined",
                extra={
                    "client_account_id": client_account_id,
                    "engagement_id": engagement_id,
                    "asset_id": str(asset.id) if hasattr(asset, "id") else None,
                },
            )
            return StandardsGapReport(
                violated_standards=[],
                missing_mandatory_data=[],
                override_required=False,
                completeness_score=1.0,
            )

        violations: List[StandardViolation] = []
        missing_mandatory_data: List[str] = []

        for standard in standards:
            violation = await self._validate_standard(asset, application, standard)
            if violation:
                violations.append(violation)

                if standard.is_mandatory:
                    missing_mandatory_data.append(standard.standard_name)

        # Calculate completeness score
        # Violations reduce score proportionally
        if len(standards) == 0:
            score = 1.0
        else:
            score = 1.0 - (len(violations) / len(standards))

        # JSON safety: Clamp and sanitize (GPT-5 Rec #8)
        score = max(0.0, min(1.0, float(score)))

        override_required = any(v.is_mandatory for v in violations)

        logger.debug(
            "standards_inspector_completed",
            extra={
                "asset_id": str(asset.id) if hasattr(asset, "id") else None,
                "asset_name": getattr(asset, "asset_name", None),
                "standards_checked": len(standards),
                "violations_found": len(violations),
                "mandatory_violations": len(missing_mandatory_data),
                "completeness_score": score,
                "override_required": override_required,
            },
        )

        return StandardsGapReport(
            violated_standards=violations,
            missing_mandatory_data=missing_mandatory_data,
            override_required=override_required,
            completeness_score=score,
        )

    async def _validate_standard(
        self,
        asset: Any,
        application: Optional[Any],
        standard: EngagementArchitectureStandard,
    ) -> Optional[StandardViolation]:
        """
        Validate asset against a single standard.

        Checks minimum_requirements dict against asset and application attributes.

        Args:
            asset: Asset to validate
            application: Optional CanonicalApplication (fallback for fields)
            standard: EngagementArchitectureStandard to validate against

        Returns:
            StandardViolation if validation fails, None if passes
        """
        minimum_requirements = standard.minimum_requirements or {}

        # Check each requirement
        for req_key, req_value in minimum_requirements.items():
            # Try to get value from asset first, then application
            asset_value = getattr(asset, req_key, None)

            if asset_value is None and application:
                asset_value = getattr(application, req_key, None)

            # Get override_available safely (field may not exist on model)
            override_available = False
            if (
                hasattr(standard, "override_available")
                and standard.override_available is not None
            ):
                override_available = bool(standard.override_available)

            # Validate based on requirement type
            if isinstance(req_value, bool):
                # Boolean requirement (e.g., encryption_enabled: True)
                if asset_value != req_value:
                    return StandardViolation(
                        standard_name=standard.standard_name,
                        requirement_type=standard.requirement_type,
                        violation_details=f"Required: {req_key}={req_value}, Found: {asset_value}",
                        is_mandatory=standard.is_mandatory,
                        override_available=override_available,
                    )

            elif isinstance(req_value, str):
                # String requirement (e.g., min_tls_version: "1.2")
                if asset_value != req_value:
                    return StandardViolation(
                        standard_name=standard.standard_name,
                        requirement_type=standard.requirement_type,
                        violation_details=f"Required: {req_key}='{req_value}', Found: '{asset_value}'",
                        is_mandatory=standard.is_mandatory,
                        override_available=override_available,
                    )

            elif isinstance(req_value, (int, float)):
                # Numeric requirement (e.g., min_availability_percent: 99.9)
                try:
                    if asset_value is None or float(asset_value) < float(req_value):
                        return StandardViolation(
                            standard_name=standard.standard_name,
                            requirement_type=standard.requirement_type,
                            violation_details=f"Required: {req_key}>={req_value}, Found: {asset_value}",
                            is_mandatory=standard.is_mandatory,
                            override_available=override_available,
                        )
                except (ValueError, TypeError):
                    # Value cannot be converted to float
                    return StandardViolation(
                        standard_name=standard.standard_name,
                        requirement_type=standard.requirement_type,
                        violation_details=f"Required: {req_key}>={req_value}, Found: {asset_value} (invalid type)",
                        is_mandatory=standard.is_mandatory,
                        override_available=override_available,
                    )

        # All requirements passed
        return None
