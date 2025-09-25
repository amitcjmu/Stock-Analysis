"""
Gap analysis functions for assets and questionnaire generation.
Functions for identifying gaps, overlays, and 6R readiness assessment.
"""

from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models import Asset

from ..overlay_loader import get_overlay_loader


def identify_gaps(asset: Asset) -> list[str]:
    """
    Basic gap identification for backward compatibility.
    Use identify_comprehensive_gaps for full analysis.

    Args:
        asset: Asset instance to evaluate

    Returns:
        List of gap descriptions
    """
    gaps = []

    # Direct field checks
    if not asset.business_criticality:
        gaps.append("Business criticality not specified")

    # Technical details field checks (using correct Asset model field names)
    if not asset.technology_stack:
        gaps.append("Technical stack information missing")

    if not asset.environment:
        gaps.append("Deployment environment not documented")

    # Custom attributes field checks
    if not asset.custom_attributes or not asset.custom_attributes.get(
        "data_classification"
    ):
        gaps.append("Data classification required")

    return gaps


async def identify_comprehensive_gaps(
    asset: Asset, db: AsyncSession, context: RequestContext
) -> List[Dict[str, Any]]:
    """
    Comprehensive gap analysis including imported data, dependencies, and 6R readiness.

    Args:
        asset: Asset instance to evaluate
        db: Database session
        context: Request context for tenant scoping

    Returns:
        List of gap objects with structured information
    """
    from .context import (
        _analyze_collected_data_gaps,
        _check_dependency_gaps,
    )

    gaps = []

    # Get overlay requirements for this asset type
    overlay_requirements = _get_overlay_requirements(asset.asset_type)

    # Check asset fields against overlay requirements
    overlay_gaps = _check_asset_fields_against_overlay(asset, overlay_requirements)
    gaps.extend(overlay_gaps)

    # Analyze collected data gaps
    collected_data_gaps = await _analyze_collected_data_gaps(asset, db, context)
    gaps.extend(collected_data_gaps)

    # Check dependency analysis gaps
    dependency_gaps = await _check_dependency_gaps(asset, db)
    gaps.extend(dependency_gaps)

    # Add 6R readiness gaps
    sixr_gaps = assess_6r_readiness_gaps(asset)
    gaps.extend(sixr_gaps)

    # Prioritize and sort gaps
    from .context import _prioritize_and_sort_gaps

    return _prioritize_and_sort_gaps(gaps)


def get_asset_type_overlay(
    asset_type: str, overlay_loader: Any = None
) -> Dict[str, Any]:
    """
    Get asset type overlay with proper loader handling.

    Args:
        asset_type: Type of asset
        overlay_loader: Optional overlay loader instance

    Returns:
        Asset type overlay configuration
    """
    if overlay_loader is None:
        overlay_loader = get_overlay_loader()

    try:
        return overlay_loader.get_asset_overlay(asset_type)
    except Exception:
        # Fallback to legacy method if overlay loader fails
        return get_asset_type_overlay_legacy(asset_type)


def get_asset_type_overlay_legacy(asset_type: str) -> Dict[str, Any]:
    """
    Legacy asset type overlay for backward compatibility.

    Args:
        asset_type: Type of asset

    Returns:
        Asset type overlay configuration
    """
    overlays = {
        "application": {
            "required_fields": [
                "business_criticality",
                "owner",
                "technology_stack",
                "environment",
            ],
            "optional_fields": [
                "data_classification",
                "compliance_requirements",
                "performance_metrics",
                "integration_points",
                "disaster_recovery",
            ],
            "technical_details": {
                "architecture_type": "required",
                "database_dependencies": "optional",
                "external_integrations": "optional",
                "scalability_requirements": "optional",
            },
            "6r_considerations": {
                "rehost_feasibility": "check_containerization",
                "replatform_complexity": "assess_dependencies",
                "refactor_requirements": "evaluate_technical_debt",
                "repurchase_alternatives": "identify_saas_options",
                "retire_eligibility": "check_usage_metrics",
                "retain_justification": "document_business_value",
            },
        },
        "database": {
            "required_fields": [
                "business_criticality",
                "owner",
                "technology_stack",
                "environment",
            ],
            "optional_fields": [
                "data_classification",
                "compliance_requirements",
                "backup_strategy",
                "performance_metrics",
            ],
            "technical_details": {
                "database_size": "required",
                "backup_frequency": "required",
                "replication_setup": "optional",
                "performance_baseline": "optional",
            },
            "6r_considerations": {
                "rehost_feasibility": "check_compatibility",
                "replatform_complexity": "assess_migration_tools",
                "refactor_requirements": "evaluate_schema_changes",
                "repurchase_alternatives": "identify_managed_services",
                "retire_eligibility": "check_data_archival",
                "retain_justification": "document_performance_requirements",
            },
        },
        "service": {
            "required_fields": ["business_criticality", "owner", "environment"],
            "optional_fields": [
                "api_documentation",
                "sla_requirements",
                "monitoring_setup",
            ],
            "technical_details": {
                "api_endpoints": "required",
                "authentication_method": "required",
                "rate_limits": "optional",
                "monitoring_endpoints": "optional",
            },
            "6r_considerations": {
                "rehost_feasibility": "check_deployment_model",
                "replatform_complexity": "assess_cloud_services",
                "refactor_requirements": "evaluate_microservices_split",
                "repurchase_alternatives": "identify_managed_apis",
                "retire_eligibility": "check_service_usage",
                "retain_justification": "document_integration_complexity",
            },
        },
        "platform": {
            "required_fields": [
                "business_criticality",
                "owner",
                "technology_stack",
                "environment",
            ],
            "optional_fields": [
                "capacity_planning",
                "disaster_recovery",
                "compliance_requirements",
            ],
            "technical_details": {
                "resource_utilization": "required",
                "scaling_policies": "optional",
                "backup_procedures": "required",
                "monitoring_setup": "optional",
            },
            "6r_considerations": {
                "rehost_feasibility": "check_hardware_compatibility",
                "replatform_complexity": "assess_managed_services",
                "refactor_requirements": "evaluate_architecture_modernization",
                "repurchase_alternatives": "identify_paas_solutions",
                "retire_eligibility": "check_platform_consolidation",
                "retain_justification": "document_specialized_requirements",
            },
        },
    }

    return overlays.get(asset_type, overlays["application"])


def assess_6r_readiness_gaps(asset: Asset) -> List[Dict[str, Any]]:
    """
    Assess gaps specifically related to 6R migration readiness.

    Args:
        asset: Asset instance to evaluate

    Returns:
        List of 6R readiness gap objects
    """
    sixr_gaps = []

    # Check for business criticality (affects all 6R decisions)
    if not asset.business_criticality:
        sixr_gaps.append(
            {
                "field": "business_criticality",
                "severity": "critical",
                "category": "6r_readiness",
                "description": "Business criticality required to determine appropriate migration strategy",
                "6r_impact": ["all"],
                "source": "6r_assessment",
            }
        )

    # Check for compliance requirements (affects replatform/refactor decisions)
    if not asset.custom_attributes or not asset.custom_attributes.get(
        "compliance_requirements"
    ):
        sixr_gaps.append(
            {
                "field": "compliance_requirements",
                "severity": "high",
                "category": "6r_readiness",
                "description": "Compliance requirements needed to evaluate replacement options",
                "6r_impact": ["repurchase", "refactor"],
                "source": "6r_assessment",
            }
        )

    # Check for modernization potential indicators
    if asset.asset_type == "application":
        if not asset.technical_details or not asset.technical_details.get(
            "containerized"
        ):
            sixr_gaps.append(
                {
                    "field": "containerization_status",
                    "severity": "medium",
                    "category": "6r_readiness",
                    "description": "Containerization status needed to assess modernization path",
                    "6r_impact": ["replatform", "refactor"],
                    "source": "6r_assessment",
                }
            )

    # Check for retirement candidates
    if not asset.custom_attributes or not asset.custom_attributes.get("last_used_date"):
        sixr_gaps.append(
            {
                "field": "usage_metrics",
                "severity": "medium",
                "category": "6r_readiness",
                "description": "Usage metrics needed to evaluate retirement eligibility",
                "6r_impact": ["retire"],
                "source": "6r_assessment",
            }
        )

    return sixr_gaps


def _get_overlay_requirements(asset_type: str) -> Dict[str, Any]:
    """Get overlay requirements for an asset type."""
    overlay_loader = get_overlay_loader()
    try:
        return overlay_loader.get_asset_overlay(asset_type)
    except Exception:
        return get_asset_type_overlay_legacy(asset_type)


def _check_asset_fields_against_overlay(
    asset: Asset, overlay_requirements: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Check asset fields against overlay requirements."""
    gaps = []

    # Check required fields
    required_fields = overlay_requirements.get("required_fields", [])
    for field in required_fields:
        value = getattr(asset, field, None)
        if not value:
            gaps.append(
                {
                    "field": field,
                    "severity": "high",
                    "category": "required_field",
                    "description": f"Required field '{field}' is missing",
                    "source": "asset_type_overlay",
                    "original_value": value,
                }
            )

    # Check technical details fields
    technical_details = overlay_requirements.get("technical_details", {})
    for field, requirement in technical_details.items():
        if requirement == "required":
            # Check if field exists in technical_details
            if not asset.technical_details or not asset.technical_details.get(field):
                gaps.append(
                    {
                        "field": f"technical_details.{field}",
                        "severity": "high",
                        "category": "technical_detail",
                        "description": f"Required technical detail '{field}' is missing",
                        "source": "asset_type_overlay",
                    }
                )

    # Check optional fields (medium priority)
    optional_fields = overlay_requirements.get("optional_fields", [])
    for field in optional_fields:
        # Check in custom_attributes for most optional fields
        if not asset.custom_attributes or not asset.custom_attributes.get(field):
            gaps.append(
                {
                    "field": field,
                    "severity": "medium",
                    "category": "optional_field",
                    "description": f"Optional field '{field}' would improve migration planning",
                    "source": "asset_type_overlay",
                }
            )

    return gaps
