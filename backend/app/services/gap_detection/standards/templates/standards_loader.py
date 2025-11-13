"""
Standards Template Loader

Centralized loader for compliance standards templates (PCI-DSS, HIPAA, SOC2, GDPR, ISO27001).
Populates EngagementArchitectureStandard table with pre-defined compliance requirements.

Part of Issue #980: Intelligent Multi-Layer Gap Detection System - Day 18
Author: CC (Claude Code)
GPT-5 Recommendations: #1 (tenant scoping), #3 (async), #11 (idempotent operations)
"""

import logging
from typing import List
from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment_flow import EngagementArchitectureStandard
from app.services.gap_detection.standards.templates.hipaa import get_hipaa_standards
from app.services.gap_detection.standards.templates.pci_dss import (
    get_pci_dss_standards,
)
from app.services.gap_detection.standards.templates.soc2 import get_soc2_standards

logger = logging.getLogger(__name__)


class StandardsTemplateLoader:
    """
    Loader for compliance standards templates.

    Supports:
    - PCI-DSS (Payment Card Industry Data Security Standard)
    - HIPAA (Health Insurance Portability and Accountability Act)
    - SOC 2 (Service Organization Control 2)
    - GDPR (General Data Protection Regulation) [placeholder]
    - ISO27001 (Information Security Management) [placeholder]

    Usage:
        loader = StandardsTemplateLoader()
        await loader.load_standards(
            db=db,
            client_account_id=uuid,
            engagement_id=uuid,
            standards=["pci_dss", "hipaa"],
        )
    """

    AVAILABLE_STANDARDS = {
        "pci_dss": get_pci_dss_standards,
        "hipaa": get_hipaa_standards,
        "soc2": get_soc2_standards,
        # Future: "gdpr": get_gdpr_standards,
        # Future: "iso27001": get_iso27001_standards,
    }

    async def load_standards(
        self,
        db: AsyncSession,
        client_account_id: UUID,
        engagement_id: UUID,
        standards: List[str],
    ) -> dict:
        """
        Load compliance standards templates into database.

        Args:
            db: Database session
            client_account_id: Client account UUID for tenant scoping
            engagement_id: Engagement UUID for tenant scoping
            standards: List of standard names to load (e.g., ["pci_dss", "hipaa"])

        Returns:
            Dict with loading results:
            {
                "loaded": 15,
                "skipped": 2,
                "failed": 0,
                "standards_loaded": ["pci_dss", "hipaa"]
            }

        Raises:
            ValueError: If unknown standard name provided
        """
        logger.info(
            f"Loading {len(standards)} compliance standards for engagement {engagement_id}"
        )

        loaded_count = 0
        skipped_count = 0
        failed_count = 0
        loaded_standards = []

        for standard_name in standards:
            if standard_name not in self.AVAILABLE_STANDARDS:
                logger.warning(
                    f"Unknown standard '{standard_name}', available: {list(self.AVAILABLE_STANDARDS.keys())}"
                )
                failed_count += 1
                continue

            try:
                # Get template function
                get_template = self.AVAILABLE_STANDARDS[standard_name]
                templates = get_template()

                # Load templates
                result = await self._load_template_batch(
                    db=db,
                    client_account_id=client_account_id,
                    engagement_id=engagement_id,
                    templates=templates,
                    standard_name=standard_name,
                )

                loaded_count += result["loaded"]
                skipped_count += result["skipped"]
                loaded_standards.append(standard_name)

                logger.info(
                    f"Loaded {result['loaded']} standards from {standard_name} "
                    f"({result['skipped']} skipped duplicates)"
                )

            except Exception as e:
                logger.error(
                    f"Failed to load standard '{standard_name}': {e}", exc_info=True
                )
                failed_count += 1

        await db.commit()

        return {
            "loaded": loaded_count,
            "skipped": skipped_count,
            "failed": failed_count,
            "standards_loaded": loaded_standards,
        }

    async def _load_template_batch(
        self,
        db: AsyncSession,
        client_account_id: UUID,
        engagement_id: UUID,
        templates: List[dict],
        standard_name: str,
    ) -> dict:
        """
        Load a batch of templates with upsert logic.

        Uses PostgreSQL INSERT ... ON CONFLICT DO NOTHING for idempotency.

        Returns:
            Dict with loaded and skipped counts
        """
        loaded = 0
        skipped = 0

        for template in templates:
            # Check if already exists
            existing = await db.execute(
                select(EngagementArchitectureStandard).where(
                    EngagementArchitectureStandard.engagement_id == engagement_id,
                    EngagementArchitectureStandard.requirement_type
                    == template["requirement_type"],
                    EngagementArchitectureStandard.standard_name
                    == template["standard_name"],
                )
            )

            if existing.scalar_one_or_none():
                skipped += 1
                continue

            # Insert new standard
            stmt = insert(EngagementArchitectureStandard).values(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                requirement_type=template["requirement_type"],
                standard_name=template["standard_name"],
                description=template.get("description"),
                minimum_requirements=template.get("minimum_requirements", {}),
                preferred_patterns=template.get("preferred_patterns", {}),
                constraints=template.get("constraints", {}),
                is_mandatory=template.get("is_mandatory", False),
                supported_versions=template.get("supported_versions"),
                requirement_details=template.get("requirement_details"),
            )

            await db.execute(stmt)
            loaded += 1

        return {"loaded": loaded, "skipped": skipped}

    async def list_loaded_standards(
        self,
        db: AsyncSession,
        client_account_id: UUID,
        engagement_id: UUID,
    ) -> dict:
        """
        List currently loaded standards for an engagement.

        Args:
            db: Database session
            client_account_id: Client account UUID
            engagement_id: Engagement UUID

        Returns:
            Dict with standard names and counts
        """
        result = await db.execute(
            select(EngagementArchitectureStandard).where(
                EngagementArchitectureStandard.client_account_id == client_account_id,
                EngagementArchitectureStandard.engagement_id == engagement_id,
            )
        )
        standards = result.scalars().all()

        # Group by standard name (extract from full standard_name field)
        by_standard = {}
        for std in standards:
            # Detect standard type from standard_name prefix
            std_type = "unknown"
            if "PCI-DSS" in std.standard_name or "PCI" in std.standard_name:
                std_type = "pci_dss"
            elif "HIPAA" in std.standard_name:
                std_type = "hipaa"
            elif "SOC 2" in std.standard_name or "SOC2" in std.standard_name:
                std_type = "soc2"

            if std_type not in by_standard:
                by_standard[std_type] = 0
            by_standard[std_type] += 1

        return {
            "total_standards": len(standards),
            "by_standard": by_standard,
            "standards": [
                {
                    "requirement_type": s.requirement_type,
                    "standard_name": s.standard_name,
                    "is_mandatory": s.is_mandatory,
                }
                for s in standards
            ],
        }

    async def remove_standards(
        self,
        db: AsyncSession,
        client_account_id: UUID,
        engagement_id: UUID,
        standard_name: str = None,
    ) -> int:
        """
        Remove loaded standards (useful for testing or re-loading).

        Args:
            db: Database session
            client_account_id: Client account UUID
            engagement_id: Engagement UUID
            standard_name: Optional specific standard to remove (None = all)

        Returns:
            Number of standards removed
        """
        from sqlalchemy import delete

        query = delete(EngagementArchitectureStandard).where(
            EngagementArchitectureStandard.client_account_id == client_account_id,
            EngagementArchitectureStandard.engagement_id == engagement_id,
        )

        if standard_name:
            # Filter by standard name pattern
            query = query.where(
                EngagementArchitectureStandard.standard_name.ilike(f"%{standard_name}%")
            )

        result = await db.execute(query)
        await db.commit()

        removed_count = result.rowcount
        logger.info(
            f"Removed {removed_count} standards from engagement {engagement_id}"
        )

        return removed_count


__all__ = ["StandardsTemplateLoader"]
