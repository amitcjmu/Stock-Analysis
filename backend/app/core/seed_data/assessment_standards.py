"""
Assessment Flow Architecture Standards Seed Data
Industry-standard templates for common technology stacks and engagement initialization.
"""

import logging
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.assessment_flow import EngagementArchitectureStandard

# Import standards from modular files
from .standards.technology_versions import TECH_VERSION_STANDARDS
from .standards.security_compliance import SECURITY_STANDARDS
from .standards.architecture_patterns import ARCHITECTURE_STANDARDS
from .standards.cloud_native import CLOUD_NATIVE_STANDARDS

logger = logging.getLogger(__name__)

# === MAIN INITIALIZATION FUNCTIONS ===


async def initialize_assessment_standards(db: AsyncSession, engagement_id: str) -> None:
    """
    Initialize engagement with default architecture standards.

    Args:
        db: Async database session
        engagement_id: UUID of the engagement
    """
    logger.info(f"Initializing assessment standards for engagement {engagement_id}")

    # Get the engagement to retrieve client_account_id
    from app.models import Engagement
    from uuid import UUID

    eng_result = await db.execute(
        select(Engagement).where(Engagement.id == UUID(engagement_id))
    )
    engagement = eng_result.scalar_one_or_none()

    if not engagement:
        logger.error(f"Engagement {engagement_id} not found")
        return

    client_account_id = engagement.client_account_id
    engagement_id = engagement.id  # Convert to UUID type

    # Check if standards already exist
    existing_standards = await db.execute(
        select(EngagementArchitectureStandard).where(
            EngagementArchitectureStandard.engagement_id == engagement_id
        )
    )

    if existing_standards.first():
        logger.info(
            f"Standards already exist for engagement {engagement_id}, skipping initialization"
        )
        return

    # Combine all standard categories
    all_standards = (
        TECH_VERSION_STANDARDS
        + SECURITY_STANDARDS
        + ARCHITECTURE_STANDARDS
        + CLOUD_NATIVE_STANDARDS
    )

    # Create standard records
    standards_created = 0
    for standard in all_standards:
        try:
            standard_record = EngagementArchitectureStandard(
                engagement_id=engagement_id,
                client_account_id=client_account_id,  # Add required field
                requirement_type=standard["requirement_type"],
                standard_name=standard.get(
                    "standard_name", standard["requirement_type"]
                ),  # Add required field
                description=standard["description"],
                is_mandatory=standard["mandatory"],
                minimum_requirements=standard.get(
                    "requirement_details", {}
                ),  # Map to correct field
                preferred_patterns=standard.get(
                    "supported_versions", {}
                ),  # Map to correct field
                priority=standard.get("priority", 5),
                business_impact=standard.get("business_impact", "medium"),
            )
            db.add(standard_record)
            standards_created += 1

        except Exception as e:
            logger.error(
                f"Failed to create standard {standard['requirement_type']}: {str(e)}"
            )
            continue

    try:
        await db.commit()
        logger.info(
            f"Successfully created {standards_created} architecture standards for engagement {engagement_id}"
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to commit architecture standards: {str(e)}")
        raise


def get_default_standards() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all default architecture standards organized by category.

    Returns:
        Dictionary with standard categories as keys and lists of standards as values
    """
    return {
        "technology_versions": TECH_VERSION_STANDARDS,
        "security_compliance": SECURITY_STANDARDS,
        "architecture_patterns": ARCHITECTURE_STANDARDS,
        "cloud_native": CLOUD_NATIVE_STANDARDS,
    }


def get_standards_by_type(requirement_type: str) -> Dict[str, Any]:
    """
    Get a specific standard by requirement type.

    Args:
        requirement_type: The type of requirement to retrieve

    Returns:
        Standard definition or None if not found
    """
    all_standards = (
        TECH_VERSION_STANDARDS
        + SECURITY_STANDARDS
        + ARCHITECTURE_STANDARDS
        + CLOUD_NATIVE_STANDARDS
    )

    for standard in all_standards:
        if standard["requirement_type"] == requirement_type:
            return standard

    return None


def validate_technology_compliance(
    technology_stack: Dict[str, str], engagement_standards: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Validate a technology stack against engagement standards.

    Args:
        technology_stack: Dictionary of technology and version pairs
        engagement_standards: List of engagement architecture standards

    Returns:
        Validation result with compliance status and recommendations
    """
    validation_result = {
        "compliant": True,
        "issues": [],
        "recommendations": [],
        "exceptions_needed": [],
    }

    # Check each technology in the stack
    for tech, version in technology_stack.items():
        # Find matching standard
        matching_standard = None
        for standard in engagement_standards:
            if (
                standard.get("supported_versions")
                and tech in standard["supported_versions"]
            ):
                matching_standard = standard
                break

        if not matching_standard:
            validation_result["recommendations"].append(
                f"No standard defined for {tech}"
            )
            continue

        # Check version compliance
        required_version = matching_standard["supported_versions"][tech]
        if not _is_version_compliant(version, required_version):
            # Issue keys match ComplianceIssue schema: field, current, required, severity
            issue = {
                "field": tech,
                "current": version,
                "required": required_version,
                "severity": "critical" if matching_standard["mandatory"] else "medium",
                "recommendation": (
                    f"Upgrade {tech} from {version} to {required_version}"
                ),
                # Keep legacy keys for backward compatibility
                "technology": tech,
                "current_version": version,
                "required_version": required_version,
                "mandatory": matching_standard["mandatory"],
            }

            if matching_standard["mandatory"]:
                validation_result["compliant"] = False
                validation_result["issues"].append(issue)
            else:
                validation_result["recommendations"].append(
                    f"Consider upgrading {tech} from {version} to {required_version}"
                )

    return validation_result


def _is_version_compliant(current_version: str, required_version: str) -> bool:
    """
    Check if current version meets the requirement.

    Args:
        current_version: Current version string
        required_version: Required version string (may include + for minimum)

    Returns:
        True if compliant, False otherwise
    """
    # Simple version comparison - can be enhanced with proper semver parsing
    if required_version.endswith("+"):
        min_version = required_version[:-1]
        # Basic string comparison - in production, use proper version parsing
        return current_version >= min_version
    else:
        return current_version == required_version
