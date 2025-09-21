"""
Resilience and compliance mapping handlers for response mapping service.

Contains handlers for mapping resilience metrics, compliance flags, licenses,
and vulnerability-related responses to appropriate database tables.
"""

import logging
from typing import Any, Dict, List

from .base import BaseResponseMapper

logger = logging.getLogger(__name__)


class ResilienceMappers(BaseResponseMapper):
    """Mappers for resilience and compliance related responses."""

    async def map_resilience_metrics(self, response: Dict[str, Any]) -> List[str]:
        """
        Map RTO/RPO response to asset_resilience table.

        Expected response format:
        {
            "asset_id": "uuid",
            "rto_minutes": integer,
            "rpo_minutes": integer,
            "availability_target": float,
            "metadata": {...}
        }
        """
        try:
            asset_id = response.get("asset_id")
            rto_minutes = response.get("rto_minutes")
            rpo_minutes = response.get("rpo_minutes")

            if not asset_id:
                raise ValueError("Missing asset_id in response")

            if rto_minutes is None and rpo_minutes is None:
                raise ValueError(
                    "At least one of rto_minutes or rpo_minutes is required"
                )

            # Create or update resilience record
            resilience_record = await self.resilience_repo.upsert(
                asset_id=asset_id,
                rto_minutes=rto_minutes,
                rpo_minutes=rpo_minutes,
                availability_target=response.get("availability_target"),
                resilience_metadata=response.get("metadata", {}),
            )

            logger.info(
                f"✅ Successfully mapped resilience metrics for asset {asset_id}: "
                f"RTO={rto_minutes}min, RPO={rpo_minutes}min"
            )
            return [f"asset_resilience:{resilience_record.id}"]

        except Exception as e:
            logger.error(f"❌ Failed to map resilience metrics response: {e}")
            raise

    async def map_compliance_flags(self, response: Dict[str, Any]) -> List[str]:
        """
        Map compliance response to asset_compliance_flags table.

        Expected response format:
        {
            "asset_id": "uuid",
            "compliance_scope": "string",
            "data_classification": "string",
            "residency_requirement": "string",
            "metadata": {...}
        }
        """
        try:
            asset_id = response.get("asset_id")

            if not asset_id:
                raise ValueError("Missing asset_id in response")

            # Create or update compliance record
            compliance_record = await self.compliance_repo.upsert(
                asset_id=asset_id,
                compliance_scope=response.get("compliance_scope"),
                data_classification=response.get("data_classification"),
                residency_requirement=response.get("residency_requirement"),
                compliance_metadata=response.get("metadata", {}),
            )

            logger.info(f"✅ Successfully mapped compliance flags for asset {asset_id}")
            return [f"asset_compliance_flags:{compliance_record.id}"]

        except Exception as e:
            logger.error(f"❌ Failed to map compliance flags response: {e}")
            raise

    async def map_license(self, response: Dict[str, Any]) -> List[str]:
        """
        Map license response to asset_licenses table.

        Expected response format:
        {
            "asset_id": "uuid",
            "license_type": "string",
            "license_key": "string",
            "expiry_date": "YYYY-MM-DD",
            "metadata": {...}
        }
        """
        try:
            asset_id = response.get("asset_id")
            license_type = response.get("license_type")

            if not asset_id:
                raise ValueError("Missing asset_id in response")

            if not license_type:
                raise ValueError("Missing license_type in response")

            # Create or update license record
            license_record = await self.license_repo.upsert(
                asset_id=asset_id,
                license_type=license_type,
                license_key=response.get("license_key"),
                expiry_date=response.get("expiry_date"),
                license_metadata=response.get("metadata", {}),
            )

            logger.info(
                f"✅ Successfully mapped license for asset {asset_id}: {license_type}"
            )
            return [f"asset_licenses:{license_record.id}"]

        except Exception as e:
            logger.error(f"❌ Failed to map license response: {e}")
            raise

    async def map_vulnerability(self, response: Dict[str, Any]) -> List[str]:
        """
        Map vulnerability response to asset_vulnerabilities table.

        Expected response format:
        {
            "asset_id": "uuid",
            "cve_id": "string",
            "severity": "string",
            "cvss_score": float,
            "metadata": {...}
        }
        """
        try:
            asset_id = response.get("asset_id")
            cve_id = response.get("cve_id")
            severity = response.get("severity")

            if not asset_id:
                raise ValueError("Missing asset_id in response")

            if not cve_id:
                raise ValueError("Missing cve_id in response")

            # Create vulnerability record
            vulnerability_record = await self.vulnerability_repo.create(
                asset_id=asset_id,
                cve_id=cve_id,
                severity=severity,
                cvss_score=response.get("cvss_score"),
                vulnerability_metadata=response.get("metadata", {}),
            )

            logger.info(
                f"✅ Successfully mapped vulnerability for asset {asset_id}: "
                f"{cve_id} ({severity})"
            )
            return [f"asset_vulnerabilities:{vulnerability_record.id}"]

        except Exception as e:
            logger.error(f"❌ Failed to map vulnerability response: {e}")
            raise
