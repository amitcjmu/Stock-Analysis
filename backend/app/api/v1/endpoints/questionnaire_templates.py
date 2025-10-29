"""
Collection Flow Questionnaire Templates

This module contains questionnaire templates and field definitions for collection flows.
Extracted from collection_crud_questionnaires.py to maintain the 400-line file limit.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional, Sequence

from app.models.asset import Asset


def get_bootstrap_questionnaire_template(
    flow_id: str,
    selected_application_id: Optional[str] = None,  # Legacy support
    selected_application_name: Optional[str] = None,  # Legacy support
    existing_assets: Optional[Sequence[Asset]] = None,  # NEW: Asset-aware
    scope: str = "engagement",  # NEW: Collection scope
) -> Dict[str, Any]:
    """Generate asset-aware bootstrap questionnaire.

    Args:
        flow_id: Collection flow ID
        selected_application_id: Pre-selected application ID (legacy)
        selected_application_name: Pre-selected application name (legacy)
        existing_assets: List of available assets from database
        scope: Collection scope (tenant/engagement/asset)

    Returns:
        Bootstrap questionnaire with asset selector or fallback
    """
    form_fields = []

    # Build asset selector field if assets available
    if existing_assets and len(existing_assets) > 0:
        # Create options from assets
        asset_options = []
        for asset in existing_assets:
            asset_id = str(asset.id) if hasattr(asset, "id") else str(asset)
            asset_name: str = ""
            if hasattr(asset, "name") and asset.name:
                asset_name = str(asset.name)
            elif hasattr(asset, "application_name") and asset.application_name:
                asset_name = str(asset.application_name)

            if not asset_name:
                asset_name = f"Asset {asset_id[:8]}"

            asset_type = getattr(asset, "asset_type", "unknown")

            # Calculate simple completeness (can be enhanced later)
            completeness = 0.5  # Default 50%
            if hasattr(asset, "business_criticality") and asset.business_criticality:
                completeness += 0.1
            # business_owner and technical_owner moved to asset_contacts (Migration 113)
            if hasattr(asset, "contacts") and asset.contacts:
                completeness += 0.1
            if hasattr(asset, "dependencies") and asset.dependencies:
                completeness += 0.1
            if hasattr(asset, "technical_details") and asset.technical_details:
                completeness += 0.1

            asset_options.append(
                {
                    "value": asset_id,
                    "label": asset_name,
                    "metadata": {
                        "type": asset_type,
                        "completeness": min(completeness, 1.0),
                        "gap_count": int((1.0 - completeness) * 10),  # Estimate gaps
                    },
                }
            )

        # Add asset selector field
        form_fields.append(
            {
                "field_id": "selected_assets",
                "question_text": "Select assets to enhance with additional data",
                "field_type": "asset_selector",  # NEW field type
                "required": True,
                "category": "asset_selection",
                "multiple": True,  # Allow multiple selection
                "options": asset_options,
                "help_text": (
                    f"Choose one or more assets from {len(asset_options)} "
                    "available assets to collect additional data"
                ),
                "metadata": {
                    "show_completeness": True,
                    "show_type_filter": len(asset_options) > 10,
                    "allow_search": len(asset_options) > 5,
                },
            }
        )

        # If pre-selected, mark it
        if selected_application_id:
            for option in asset_options:
                if option["value"] == str(selected_application_id):
                    form_fields[0]["default_value"] = [str(selected_application_id)]
                    break

    else:
        # Fallback to text input if no assets available
        form_fields.append(
            {
                "field_id": "asset_name",
                "question_text": "What is the asset name?",
                "field_type": "text",
                "required": True,
                "category": "identity",
                "help_text": "No assets found in database. Enter the asset name manually.",
                "default_value": (
                    selected_application_name if selected_application_name else None
                ),
            }
        )

        form_fields.append(
            {
                "field_id": "asset_type",
                "question_text": "What type of asset is this?",
                "field_type": "select",
                "required": True,
                "category": "identity",
                "options": [
                    "application",
                    "database",
                    "server",
                    "network_device",
                    "storage_system",
                    "middleware",
                    "container",
                    "virtual_machine",
                    "cloud_service",
                    "other",
                ],
            }
        )

        # Add remaining fields (existing code for fallback mode)
        form_fields.extend(
            [
                {
                    "field_id": "business_purpose",
                    "question_text": "What is the primary business purpose?",
                    "field_type": "text",
                    "required": True,
                    "category": "business",
                    "help_text": "Describe the main business function this asset serves",
                },
                {
                    "field_id": "primary_technology",
                    "question_text": "What is the primary technology stack?",
                    "field_type": "select",
                    "required": True,
                    "category": "technical",
                    "options": [
                        "java",
                        "dotnet",
                        "python",
                        "nodejs",
                        "php",
                        "ruby",
                        "go",
                        "other",
                    ],
                },
            ]
        )

    # Return enhanced template
    return {
        "id": f"bootstrap_{flow_id}",
        "flow_id": flow_id,
        "title": "Asset Data Collection" if existing_assets else "Asset Information",
        "description": (
            f"Select from {len(existing_assets)} available assets to enhance with additional data"
            if existing_assets
            else "Please provide essential information about the asset"
        ),
        "form_fields": form_fields,
        "validation_rules": {
            "required_fields": (
                ["selected_assets"] if existing_assets else ["asset_name", "asset_type"]
            ),
            "min_selections": 1 if existing_assets else None,
        },
        "completion_status": {
            "total_fields": len(form_fields),
            "required_fields": sum(1 for f in form_fields if f.get("required", False)),
            "completed_fields": 0,
        },
        "responses_collected": 0,
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "metadata": {
            "scope": scope,
            "asset_aware": bool(existing_assets),
            "total_assets": len(existing_assets) if existing_assets else 0,
            "fallback_mode": not bool(existing_assets),
        },
    }


def get_field_categories() -> Dict[str, List[str]]:
    """Get field categories for organizing questionnaire fields.

    Returns:
        Dictionary mapping category names to lists of field descriptions
    """
    return {
        "identity": ["Application name and type identification"],
        "business": ["Business purpose, criticality, and impact"],
        "technical": ["Technology stack and architecture details"],
        "infrastructure": ["Hosting, scaling, and infrastructure"],
        "compliance": ["Security, data classification, and compliance"],
    }


def validate_questionnaire_field(field: Dict[str, Any]) -> bool:
    """Validate a questionnaire field definition.

    Args:
        field: Field definition dictionary

    Returns:
        True if valid, False otherwise
    """
    required_keys = {"field_id", "question_text", "field_type"}
    return all(key in field for key in required_keys)


def get_field_type_options() -> List[str]:
    """Get available field types for questionnaire fields.

    Returns:
        List of valid field type options
    """
    return [
        "text",
        "select",
        "multi_select",
        "number",
        "boolean",
        "date",
        "textarea",
        "asset_selector",
    ]
