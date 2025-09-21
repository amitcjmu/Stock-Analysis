"""
Repository for asset resilience and compliance management.

This module provides data access methods for asset resilience metrics,
compliance flags, vulnerabilities, and licensing information.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset_resilience import (
    AssetComplianceFlags,
    AssetLicenses,
    AssetResilience,
    AssetVulnerabilities,
)
from app.repositories.context_aware_repository import ContextAwareRepository

logger = logging.getLogger(__name__)


class ResilienceRepository(ContextAwareRepository[AssetResilience]):
    """Repository for asset resilience metrics."""

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ):
        super().__init__(db, AssetResilience, client_account_id, engagement_id)

    async def get_by_asset(self, asset_id: str) -> Optional[AssetResilience]:
        """
        Get resilience metrics for a specific asset.

        Args:
            asset_id: Asset UUID

        Returns:
            Asset resilience record if found
        """
        return await self.get_by_filters(asset_id=asset_id)

    async def upsert_resilience(
        self,
        asset_id: str,
        rto_minutes: Optional[int] = None,
        rpo_minutes: Optional[int] = None,
        sla_json: Optional[Dict[str, Any]] = None,
        commit: bool = True,
    ) -> AssetResilience:
        """
        Create or update resilience metrics for an asset.

        Args:
            asset_id: Asset UUID
            rto_minutes: Recovery Time Objective in minutes
            rpo_minutes: Recovery Point Objective in minutes
            sla_json: SLA details and targets
            commit: Whether to commit the transaction

        Returns:
            Asset resilience record
        """
        existing = await self.get_by_filters(asset_id=asset_id)

        update_data = {}
        if rto_minutes is not None:
            update_data["rto_minutes"] = rto_minutes
        if rpo_minutes is not None:
            update_data["rpo_minutes"] = rpo_minutes
        if sla_json is not None:
            update_data["sla_json"] = sla_json

        if existing:
            # Update existing record
            return await self.update(existing[0].id, commit=commit, **update_data)
        else:
            # Create new record
            return await self.create(commit=commit, asset_id=asset_id, **update_data)

    async def get_critical_rto_assets(
        self, max_rto_minutes: int = 60
    ) -> List[AssetResilience]:
        """
        Get assets with critical RTO requirements.

        Args:
            max_rto_minutes: Maximum RTO to consider critical

        Returns:
            List of assets with critical RTO requirements
        """
        query = select(AssetResilience).where(
            and_(
                AssetResilience.rto_minutes.isnot(None),
                AssetResilience.rto_minutes <= max_rto_minutes,
            )
        )
        query = self._apply_context_filter(query)

        result = await self.db.execute(query)
        return result.scalars().all()


class ComplianceRepository(ContextAwareRepository[AssetComplianceFlags]):
    """Repository for asset compliance flags."""

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ):
        super().__init__(db, AssetComplianceFlags, client_account_id, engagement_id)

    async def get_by_asset(self, asset_id: str) -> Optional[AssetComplianceFlags]:
        """
        Get compliance flags for a specific asset.

        Args:
            asset_id: Asset UUID

        Returns:
            Asset compliance flags if found
        """
        results = await self.get_by_filters(asset_id=asset_id)
        return results[0] if results else None

    async def upsert_compliance(
        self,
        asset_id: str,
        compliance_scopes: Optional[List[str]] = None,
        data_classification: Optional[str] = None,
        residency: Optional[str] = None,
        evidence_refs: Optional[List[Dict[str, Any]]] = None,
        commit: bool = True,
    ) -> AssetComplianceFlags:
        """
        Create or update compliance flags for an asset.

        Args:
            asset_id: Asset UUID
            compliance_scopes: List of compliance requirements (GDPR, HIPAA, etc.)
            data_classification: Data classification level
            residency: Data residency requirements
            evidence_refs: Evidence/document references
            commit: Whether to commit the transaction

        Returns:
            Asset compliance flags record
        """
        existing = await self.get_by_filters(asset_id=asset_id)

        update_data = {}
        if compliance_scopes is not None:
            update_data["compliance_scopes"] = compliance_scopes
        if data_classification is not None:
            update_data["data_classification"] = data_classification
        if residency is not None:
            update_data["residency"] = residency
        if evidence_refs is not None:
            update_data["evidence_refs"] = evidence_refs

        if existing:
            # Update existing record
            return await self.update(existing[0].id, commit=commit, **update_data)
        else:
            # Create new record
            return await self.create(commit=commit, asset_id=asset_id, **update_data)

    async def get_by_compliance_scope(self, scope: str) -> List[AssetComplianceFlags]:
        """
        Get assets with specific compliance requirements.

        Args:
            scope: Compliance scope to filter by (e.g., "GDPR", "HIPAA")

        Returns:
            List of assets with the specified compliance requirement
        """
        query = select(AssetComplianceFlags).where(
            AssetComplianceFlags.compliance_scopes.contains([scope])
        )
        query = self._apply_context_filter(query)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_classification(
        self, classification: str
    ) -> List[AssetComplianceFlags]:
        """
        Get assets by data classification.

        Args:
            classification: Data classification level

        Returns:
            List of assets with the specified classification
        """
        return await self.get_by_filters(data_classification=classification)


class VulnerabilityRepository(ContextAwareRepository[AssetVulnerabilities]):
    """Repository for asset vulnerabilities."""

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ):
        super().__init__(db, AssetVulnerabilities, client_account_id, engagement_id)

    async def get_by_asset(self, asset_id: str) -> List[AssetVulnerabilities]:
        """
        Get all vulnerabilities for a specific asset.

        Args:
            asset_id: Asset UUID

        Returns:
            List of vulnerabilities for the asset
        """
        return await self.get_by_filters(asset_id=asset_id)

    async def get_by_severity(self, severity: str) -> List[AssetVulnerabilities]:
        """
        Get vulnerabilities by severity level.

        Args:
            severity: Severity level (low, medium, high, critical)

        Returns:
            List of vulnerabilities with specified severity
        """
        return await self.get_by_filters(severity=severity)

    async def get_critical_vulnerabilities(self) -> List[AssetVulnerabilities]:
        """
        Get all critical and high severity vulnerabilities.

        Returns:
            List of critical/high severity vulnerabilities
        """
        query = select(AssetVulnerabilities).where(
            AssetVulnerabilities.severity.in_(["critical", "high"])
        )
        query = self._apply_context_filter(query)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def add_vulnerability(
        self,
        asset_id: str,
        cve_id: Optional[str] = None,
        severity: Optional[str] = None,
        source: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        commit: bool = True,
    ) -> AssetVulnerabilities:
        """
        Add a new vulnerability record for an asset.

        Args:
            asset_id: Asset UUID
            cve_id: CVE identifier if applicable
            severity: Severity level
            source: Source of vulnerability detection
            details: Additional vulnerability details
            commit: Whether to commit the transaction

        Returns:
            Created vulnerability record
        """
        from datetime import datetime

        return await self.create(
            commit=commit,
            asset_id=asset_id,
            cve_id=cve_id,
            severity=severity,
            detected_at=datetime.utcnow(),
            source=source,
            details=details or {},
        )


class LicenseRepository(ContextAwareRepository[AssetLicenses]):
    """Repository for asset licensing information."""

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ):
        super().__init__(db, AssetLicenses, client_account_id, engagement_id)

    async def get_by_asset(self, asset_id: str) -> List[AssetLicenses]:
        """
        Get all licenses for a specific asset.

        Args:
            asset_id: Asset UUID

        Returns:
            List of licenses for the asset
        """
        return await self.get_by_filters(asset_id=asset_id)

    async def get_expiring_licenses(self, days_ahead: int = 90) -> List[AssetLicenses]:
        """
        Get licenses expiring within specified days.

        Args:
            days_ahead: Number of days to look ahead

        Returns:
            List of expiring licenses
        """
        from datetime import date, timedelta

        cutoff_date = date.today() + timedelta(days=days_ahead)

        query = select(AssetLicenses).where(
            and_(
                AssetLicenses.renewal_date.isnot(None),
                AssetLicenses.renewal_date <= cutoff_date,
                AssetLicenses.renewal_date >= date.today(),
            )
        )
        query = self._apply_context_filter(query)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def upsert_license(
        self,
        asset_id: str,
        license_type: Optional[str] = None,
        renewal_date: Optional[str] = None,
        contract_reference: Optional[str] = None,
        support_tier: Optional[str] = None,
        commit: bool = True,
    ) -> AssetLicenses:
        """
        Create or update license information for an asset.

        Args:
            asset_id: Asset UUID
            license_type: Type of license
            renewal_date: License renewal date
            contract_reference: Contract reference number
            support_tier: Support tier level
            commit: Whether to commit the transaction

        Returns:
            Asset license record
        """
        # For now, create new license records rather than updating
        # In production, you might want to update existing records based on license_type
        return await self.create(
            commit=commit,
            asset_id=asset_id,
            license_type=license_type,
            renewal_date=renewal_date,
            contract_reference=contract_reference,
            support_tier=support_tier,
        )
