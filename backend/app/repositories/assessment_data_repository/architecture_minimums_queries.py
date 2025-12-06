"""
Assessment Data Repository - Architecture Minimums Queries

Mixin for architecture minimums (compliance validation) data fetching.
ADR-039 Enhancement: Provides methods for loading engagement standards
and assessment applications for compliance validation.

Per ADR-024: All queries include tenant scoping.
"""

from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import and_, select

from app.core.logging import get_logger
from app.models.assessment_flow.core_models import (
    AssessmentFlow,
    EngagementArchitectureStandard,
)
from app.models.canonical_applications import CanonicalApplication

logger = get_logger(__name__)


class ArchitectureMinimumsQueriesMixin:
    """Mixin for architecture minimums (compliance validation) data queries."""

    async def get_engagement_standards(self, engagement_id: str) -> Dict[str, Any]:
        """
        Load engagement architecture standards from the database.

        ADR-039: Required for validate_technology_compliance() to check
        technology versions against engagement-specific standards.

        Args:
            engagement_id: Engagement UUID string

        Returns:
            Dictionary with supported languages, databases, cloud providers, etc.
            Returns default standards if none defined for engagement.
        """
        try:
            # Query engagement standards with multi-tenant scoping
            stmt = select(EngagementArchitectureStandard).where(
                EngagementArchitectureStandard.engagement_id == self.engagement_id,
                EngagementArchitectureStandard.client_account_id
                == self.client_account_id,
            )
            result = await self.db.execute(stmt)
            standards = result.scalars().all()

            if not standards:
                logger.info(
                    f"No engagement standards found for engagement {engagement_id}, "
                    f"using default standards"
                )
                # Return None to signal caller should use defaults
                return None

            # Build engagement standards dict from database records
            # Group by requirement_type for the compliance validator
            supported_languages = []
            supported_databases = []
            cloud_providers = []
            compliance_frameworks = []

            for std in standards:
                req_type = std.requirement_type.lower() if std.requirement_type else ""
                supported_versions = std.supported_versions or {}

                if "language" in req_type or "runtime" in req_type:
                    supported_languages.append(
                        {
                            "name": std.standard_name,
                            "min_version": supported_versions.get("min_version", ""),
                            "max_version": supported_versions.get("max_version", ""),
                        }
                    )
                elif "database" in req_type or "data_store" in req_type:
                    supported_databases.append(
                        {
                            "name": std.standard_name,
                            "min_version": supported_versions.get("min_version", ""),
                            "max_version": supported_versions.get("max_version", ""),
                        }
                    )
                elif "cloud" in req_type:
                    cloud_providers.append(std.standard_name)
                elif "compliance" in req_type or "framework" in req_type:
                    compliance_frameworks.append(std.standard_name)

            logger.info(
                f"Loaded engagement standards: {len(supported_languages)} languages, "
                f"{len(supported_databases)} databases, {len(cloud_providers)} cloud providers"
            )

            return {
                "supported_languages": supported_languages,
                "supported_databases": supported_databases,
                "cloud_providers": cloud_providers,
                "compliance_frameworks": compliance_frameworks,
            }

        except Exception as e:
            logger.error(f"Failed to load engagement standards: {e}")
            # Return None to signal caller should use defaults
            return None

    async def get_assessment_applications(self, flow_id: str) -> List[Dict[str, Any]]:
        """
        Get applications for an assessment flow.

        Retrieves canonical applications linked to the assessment flow
        for compliance validation against engagement standards.

        Args:
            flow_id: Assessment flow ID (child flow ID)

        Returns:
            List of application dictionaries with technology_stack for validation
        """
        try:
            # First, get the assessment flow to find selected applications
            stmt = select(AssessmentFlow).where(
                and_(
                    AssessmentFlow.id == UUID(flow_id),
                    AssessmentFlow.client_account_id == self.client_account_id,
                    AssessmentFlow.engagement_id == self.engagement_id,
                )
            )
            result = await self.db.execute(stmt)
            flow = result.scalar_one_or_none()

            if not flow:
                logger.warning(f"Assessment flow not found: {flow_id}")
                return []

            # Get selected canonical application IDs from flow
            selected_app_ids = flow.selected_canonical_application_ids or []

            if not selected_app_ids:
                logger.info(
                    f"No selected applications for flow {flow_id}, "
                    f"returning all engagement applications"
                )
                # Fallback: return all canonical applications for this engagement
                stmt = select(CanonicalApplication).where(
                    and_(
                        CanonicalApplication.client_account_id
                        == self.client_account_id,
                        CanonicalApplication.engagement_id == self.engagement_id,
                    )
                )
                result = await self.db.execute(stmt)
                apps = result.scalars().all()
            else:
                # Convert string IDs to UUIDs
                uuid_ids = []
                for app_id in selected_app_ids:
                    if isinstance(app_id, str):
                        uuid_ids.append(UUID(app_id))
                    elif isinstance(app_id, UUID):
                        uuid_ids.append(app_id)

                # Query selected applications
                stmt = select(CanonicalApplication).where(
                    and_(
                        CanonicalApplication.client_account_id
                        == self.client_account_id,
                        CanonicalApplication.engagement_id == self.engagement_id,
                        CanonicalApplication.id.in_(uuid_ids),
                    )
                )
                result = await self.db.execute(stmt)
                apps = result.scalars().all()

            # Serialize applications for compliance validation
            serialized_apps = []
            for app in apps:
                serialized_apps.append(
                    {
                        "id": str(app.id),
                        "application_id": str(app.id),
                        "name": app.canonical_name,
                        "application_name": app.canonical_name,
                        "technology_stack": app.technology_stack or {},
                        "application_type": app.application_type,
                        "business_criticality": app.business_criticality,
                    }
                )

            logger.info(
                f"Retrieved {len(serialized_apps)} applications for compliance validation"
            )
            return serialized_apps

        except Exception as e:
            logger.error(f"Failed to get assessment applications: {e}")
            return []
