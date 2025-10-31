"""
Asset serialization for agent context.

Provides comprehensive asset data serialization including all enrichment tables
for intelligent cloud migration and modernization decisions.
"""

import logging
from typing import Any, Dict, List

from app.models import Asset

logger = logging.getLogger(__name__)


def serialize_asset_for_agent_context(
    asset: Asset,
    completeness: float,
    gaps: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Serialize asset with ALL enriched data for intelligent cloud migration decisions.

    This function provides the COMPLETE context that agents need for:
    - Cloud readiness assessment
    - 6R strategy recommendation (Rehost, Replatform, Refactor, Rearchitect, Retire, Retain)
    - Migration complexity estimation
    - Cost-benefit analysis
    - Risk assessment
    - Modernization opportunity identification

    The agent receives data from:
    - Core Asset model (50+ structured fields)
    - AssetResilience (RTO/RPO/SLA requirements)
    - AssetComplianceFlags (GDPR/HIPAA/SOX, data classification)
    - AssetVulnerabilities (CVEs, security posture)
    - AssetLicenses (License renewals, support contracts)
    - AssetEOLAssessment (End-of-life technology risks)
    - AssetContact (Business owners, technical owners, architects)

    Args:
        asset: Asset ORM object with eager-loaded relationships
        completeness: Calculated completeness score (0.0-1.0)
        gaps: List of identified data gaps

    Returns:
        Dictionary with comprehensive asset context
    """

    # ====================
    # 1. CORE ASSET FIELDS
    # ====================

    core_data = {
        # Identity
        "id": str(asset.id),
        "name": asset.name,
        "hostname": asset.hostname,
        "asset_name": asset.asset_name,
        "asset_type": asset.asset_type,
        "description": asset.description,
        # Infrastructure (CRITICAL for cloud sizing and compatibility)
        "operating_system": asset.operating_system,
        "os_version": asset.os_version,
        "technology_stack": asset.technology_stack,
        "environment": asset.environment,
        # Resources (CRITICAL for right-sizing in cloud)
        "cpu_cores": asset.cpu_cores,
        "memory_gb": asset.memory_gb,
        "storage_gb": asset.storage_gb,
        # Performance (CRITICAL for cloud tier selection)
        "cpu_utilization_percent": asset.cpu_utilization_percent,
        "memory_utilization_percent": asset.memory_utilization_percent,
        "disk_iops": asset.disk_iops,
        "network_throughput_mbps": asset.network_throughput_mbps,
        # Business Context (CRITICAL for migration priority and stakeholder engagement)
        "business_owner": asset.business_owner,
        "technical_owner": asset.technical_owner,
        "application_name": asset.application_name,
        "department": asset.department,
        "business_criticality": asset.business_criticality,
        "criticality": asset.criticality,
        # Location (CRITICAL for data residency and migration logistics)
        "location": asset.location,
        "datacenter": asset.datacenter,
        "rack_location": asset.rack_location,
        "availability_zone": asset.availability_zone,
        # Network
        "ip_address": asset.ip_address,
        "fqdn": asset.fqdn,
        "mac_address": asset.mac_address,
        # Assessment (CRITICAL for 6R strategy and wave planning)
        "six_r_strategy": asset.six_r_strategy,
        "migration_complexity": asset.migration_complexity,
        "migration_priority": asset.migration_priority,
        "migration_wave": asset.migration_wave,
        "sixr_ready": asset.sixr_ready,
        # Cost (CRITICAL for business case and ROI analysis)
        "current_monthly_cost": asset.current_monthly_cost,
        "estimated_cloud_cost": asset.estimated_cloud_cost,
        # Data Quality Metrics
        "completeness_score": asset.completeness_score,
        "quality_score": asset.quality_score,
        "confidence_score": asset.confidence_score,
        "complexity_score": asset.complexity_score,
        # Discovery Metadata
        "discovery_method": asset.discovery_method,
        "discovery_source": asset.discovery_source,
        "discovery_timestamp": (
            asset.discovery_timestamp.isoformat() if asset.discovery_timestamp else None
        ),
        # Status
        "status": asset.status,
        "migration_status": asset.migration_status,
        "mapping_status": asset.mapping_status,
        # Flexible Data (for additional context not in structured fields)
        "custom_attributes": asset.custom_attributes or {},
        "technical_details": asset.technical_details or {},
        # Dependencies (JSON field - note: actual dependency relationships in separate query)
        "dependencies": asset.dependencies or [],
        "related_assets": asset.related_assets or [],
        # Calculated fields
        "completeness": completeness,
        "gaps": gaps,
    }

    # ============================
    # 2. ENRICHMENT: RESILIENCE
    # ============================
    # Business continuity, SLA requirements, disaster recovery planning
    # CRITICAL for: Multi-AZ deployment, backup strategy, cloud tier selection

    if hasattr(asset, "resilience") and asset.resilience:
        core_data["resilience"] = {
            "rto_minutes": asset.resilience.rto_minutes,
            "rpo_minutes": asset.resilience.rpo_minutes,
            "sla_json": asset.resilience.sla_json or {},
        }
        logger.debug(
            f"Asset {asset.name}: Added resilience data - RTO={asset.resilience.rto_minutes}min, "
            f"RPO={asset.resilience.rpo_minutes}min"
        )

    # ============================
    # 3. ENRICHMENT: COMPLIANCE
    # ============================
    # Regulatory requirements, data classification, residency constraints
    # CRITICAL for: Cloud region selection, encryption requirements, audit controls

    if hasattr(asset, "compliance_flags") and asset.compliance_flags:
        core_data["compliance"] = {
            "scopes": asset.compliance_flags.compliance_scopes or [],
            "data_classification": asset.compliance_flags.data_classification,
            "residency": asset.compliance_flags.residency,
            "evidence_refs": asset.compliance_flags.evidence_refs or [],
        }
        logger.debug(
            f"Asset {asset.name}: Added compliance data - Scopes={asset.compliance_flags.compliance_scopes}, "
            f"Classification={asset.compliance_flags.data_classification}"
        )

    # ============================
    # 4. ENRICHMENT: VULNERABILITIES
    # ============================
    # Security posture, CVEs, patch status
    # CRITICAL for: Migration blockers, security hardening, risk assessment

    if hasattr(asset, "vulnerabilities") and asset.vulnerabilities:
        core_data["vulnerabilities"] = [
            {
                "cve_id": vuln.cve_id,
                "severity": vuln.severity,
                "detected_at": (
                    vuln.detected_at.isoformat() if vuln.detected_at else None
                ),
                "source": vuln.source,
                "details": vuln.details or {},
            }
            for vuln in asset.vulnerabilities
        ]
        logger.debug(
            f"Asset {asset.name}: Added {len(asset.vulnerabilities)} vulnerabilities - "
            f"Critical count: {sum(1 for v in asset.vulnerabilities if v.severity == 'critical')}"
        )

    # ============================
    # 5. ENRICHMENT: LICENSES
    # ============================
    # Software licensing, support contracts, renewal dates
    # CRITICAL for: BYOL decisions, license portability, timing optimization, cost optimization

    if hasattr(asset, "licenses") and asset.licenses:
        core_data["licenses"] = [
            {
                "license_type": lic.license_type,
                "renewal_date": (
                    lic.renewal_date.isoformat() if lic.renewal_date else None
                ),
                "contract_reference": lic.contract_reference,
                "support_tier": lic.support_tier,
            }
            for lic in asset.licenses
        ]
        logger.debug(
            f"Asset {asset.name}: Added {len(asset.licenses)} licenses - "
            f"Types: {[lic.license_type for lic in asset.licenses]}"
        )

    # ============================
    # 6. ENRICHMENT: EOL ASSESSMENTS
    # ============================
    # End-of-life technology risks and remediation options
    # CRITICAL for: Migration urgency, modernization opportunities, 6R strategy selection

    if hasattr(asset, "eol_assessments") and asset.eol_assessments:
        core_data["eol_assessments"] = [
            {
                "technology_component": eol.technology_component,
                "eol_date": eol.eol_date.isoformat() if eol.eol_date else None,
                "eol_risk_level": eol.eol_risk_level,
                "assessment_notes": eol.assessment_notes,
                "remediation_options": eol.remediation_options or [],
            }
            for eol in asset.eol_assessments
        ]
        logger.debug(
            f"Asset {asset.name}: Added {len(asset.eol_assessments)} EOL assessments - "
            f"Critical risks: {sum(1 for e in asset.eol_assessments if e.eol_risk_level == 'critical')}"
        )

    # ============================
    # 7. ENRICHMENT: CONTACTS
    # ============================
    # Stakeholders, SMEs, contact information
    # CRITICAL for: Engagement planning, questionnaire personalization, SME identification

    if hasattr(asset, "contacts") and asset.contacts:
        core_data["contacts"] = [
            {
                "contact_type": contact.contact_type,
                "name": contact.name,
                "email": contact.email,
                "phone": contact.phone,
                "user_id": str(contact.user_id) if contact.user_id else None,
            }
            for contact in asset.contacts
        ]
        logger.debug(
            f"Asset {asset.name}: Added {len(asset.contacts)} contacts - "
            f"Types: {[c.contact_type for c in asset.contacts]}"
        )

    # Log summary of enriched data
    enrichment_summary = []
    if "resilience" in core_data:
        enrichment_summary.append("resilience")
    if "compliance" in core_data:
        enrichment_summary.append("compliance")
    if "vulnerabilities" in core_data:
        enrichment_summary.append(
            f"{len(core_data['vulnerabilities'])} vulnerabilities"
        )
    if "licenses" in core_data:
        enrichment_summary.append(f"{len(core_data['licenses'])} licenses")
    if "eol_assessments" in core_data:
        enrichment_summary.append(
            f"{len(core_data['eol_assessments'])} EOL assessments"
        )
    if "contacts" in core_data:
        enrichment_summary.append(f"{len(core_data['contacts'])} contacts")

    enrichment_list = ", ".join(enrichment_summary) if enrichment_summary else "none"
    logger.info(
        f"✅ Serialized asset {asset.name} with enrichments: [{enrichment_list}]"
    )

    return core_data


def serialize_multiple_assets(
    assets: List[Asset],
    completeness_scores: Dict[str, float],
    gaps_by_asset: Dict[str, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """
    Serialize multiple assets efficiently.

    Args:
        assets: List of Asset ORM objects
        completeness_scores: Mapping of asset_id -> completeness score
        gaps_by_asset: Mapping of asset_id -> list of gaps

    Returns:
        List of serialized asset dictionaries
    """
    serialized = []

    for asset in assets:
        asset_id_str = str(asset.id)
        completeness = completeness_scores.get(asset_id_str, 0.0)
        gaps = gaps_by_asset.get(asset_id_str, [])

        asset_data = serialize_asset_for_agent_context(asset, completeness, gaps)
        serialized.append(asset_data)

    logger.info(
        f"✅ Batch serialized {len(serialized)} assets with comprehensive enrichment data"
    )

    return serialized
