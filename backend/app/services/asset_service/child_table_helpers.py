"""
Helper functions for creating child table records (EOL assessments, contacts).

These functions handle conditional creation of records in:
- asset_eol_assessments table
- asset_contacts table

Only creates records when user actually supplies data via CSV import.
"""

import logging
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def has_eol_data(asset_data: Dict[str, Any]) -> bool:
    """Check if asset_data contains EOL assessment information."""
    eol_fields = [
        "eol_date",
        "eol_risk_level",
        "technology_component",
        "assessment_notes",
    ]
    return any(asset_data.get(field) for field in eol_fields)


def has_contact_data(asset_data: Dict[str, Any]) -> bool:
    """Check if asset_data contains contact information."""
    contact_fields = [
        "business_owner_email",
        "technical_owner_email",
        "architect_email",
        "business_owner",  # Fallback if only name provided
        "technical_owner",  # Fallback if only name provided
    ]
    return any(asset_data.get(field) for field in contact_fields)


async def create_eol_assessment(
    db: AsyncSession,
    asset,
    asset_data: Dict[str, Any],
) -> None:
    """
    Create EOL assessment record for asset.

    Tenant context (client_account_id, engagement_id) is retrieved from the asset itself,
    following the standard pattern where context comes from the data object, not parameters.
    """
    from app.models.asset.specialized import AssetEOLAssessment
    from dateutil import parser as date_parser

    # Extract EOL date if provided
    eol_date = None
    if asset_data.get("eol_date"):
        try:
            eol_date = date_parser.parse(str(asset_data["eol_date"])).date()
        except Exception:
            logger.warning(f"⚠️ Invalid EOL date format: {asset_data['eol_date']}")

    # Validate and normalize EOL risk level (DB constraint: 'low', 'medium', 'high', 'critical')
    eol_risk_level = None
    if asset_data.get("eol_risk_level"):
        raw_risk = str(asset_data["eol_risk_level"]).lower().strip()
        valid_levels = ["low", "medium", "high", "critical"]
        if raw_risk in valid_levels:
            eol_risk_level = raw_risk
        else:
            logger.warning(
                f"⚠️ Invalid EOL risk level '{asset_data['eol_risk_level']}' "
                f"for asset {asset.name}. Must be one of: {valid_levels}"
            )

    # Create EOL assessment with tenant context from asset
    eol_assessment = AssetEOLAssessment(
        client_account_id=asset.client_account_id,  # From asset, not parameter
        engagement_id=asset.engagement_id,  # From asset, not parameter
        asset_id=asset.id,
        technology_component=asset_data.get("technology_component")
        or asset_data.get("technology_stack")
        or "Unknown",
        eol_date=eol_date,
        eol_risk_level=eol_risk_level,
        assessment_notes=asset_data.get("assessment_notes")
        or asset_data.get("eol_notes"),
        remediation_options=asset_data.get("remediation_options", []),
    )

    db.add(eol_assessment)
    await db.flush()
    logger.info(f"✅ Created EOL assessment for asset {asset.name}")


async def create_contacts_if_exists(
    db: AsyncSession,
    asset,
    asset_data: Dict[str, Any],
) -> None:
    """
    Create asset contact records if contact information exists.

    Tenant context (client_account_id, engagement_id) is retrieved from the asset itself,
    following the standard pattern where context comes from the data object, not parameters.
    """
    from app.models.asset.specialized import AssetContact

    # Define contact mappings: CSV field → contact_type
    contact_mappings = {
        "business_owner_email": ("business_owner", "business_owner_name"),
        "technical_owner_email": ("technical_owner", "technical_owner_name"),
        "architect_email": ("architect", "architect_name"),
        "business_owner": ("business_owner", "business_owner_name"),  # Fallback
        "technical_owner": ("technical_owner", "technical_owner_name"),  # Fallback
    }

    contacts_created = 0
    for email_field, (contact_type, name_field) in contact_mappings.items():
        email = asset_data.get(email_field)
        if email:
            # Create contact record with tenant context from asset
            contact = AssetContact(
                client_account_id=asset.client_account_id,  # From asset, not parameter
                engagement_id=asset.engagement_id,  # From asset, not parameter
                asset_id=asset.id,
                contact_type=contact_type,
                email=email,
                name=asset_data.get(name_field)
                or email.split("@")[0],  # Extract name from email if not provided
                phone=asset_data.get(f"{contact_type}_phone"),
            )
            db.add(contact)
            contacts_created += 1

    if contacts_created > 0:
        await db.flush()
        logger.info(f"✅ Created {contacts_created} contact(s) for asset {asset.name}")


async def create_child_records_if_needed(
    db: AsyncSession,
    asset,
    asset_data: Dict[str, Any],
) -> None:
    """
    Create child table records (EOL assessments, contacts) if data exists.
    Only creates records when user actually supplied the data via CSV.

    Tenant context is automatically inherited from the asset object, following
    the standard pattern where context comes from data objects, not parameters.
    """
    try:
        # 1. Create EOL Assessment if EOL data exists
        if has_eol_data(asset_data):
            await create_eol_assessment(db, asset, asset_data)

        # 2. Create Asset Contacts if contact data exists
        if has_contact_data(asset_data):
            await create_contacts_if_exists(db, asset, asset_data)

    except Exception as e:
        # Log error but don't fail asset creation
        # Just log the error and continue
        logger.warning(f"⚠️ Failed to create child records for asset {asset.id}: {e}")
