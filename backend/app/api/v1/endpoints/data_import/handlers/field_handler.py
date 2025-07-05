"""
Field Handler - Provides field mapping and target field information.
"""

import logging
from typing import Dict, List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.context import get_current_context, RequestContext

logger = logging.getLogger(__name__)

router = APIRouter()

# Define standard target fields for asset migration
STANDARD_TARGET_FIELDS = [
    # Identification fields
    {"name": "asset_id", "type": "string", "required": True, "description": "Unique asset identifier", "category": "identification"},
    {"name": "name", "type": "string", "required": True, "description": "Asset name or identifier", "category": "identification"},
    {"name": "hostname", "type": "string", "required": True, "description": "Asset hostname", "category": "identification"},
    {"name": "fqdn", "type": "string", "required": False, "description": "Fully qualified domain name", "category": "identification"},
    {"name": "asset_name", "type": "string", "required": False, "description": "Friendly asset name", "category": "identification"},
    
    # Technical fields
    {"name": "asset_type", "type": "enum", "required": True, "description": "Type of asset (server, vm, container, etc.)", "category": "technical"},
    {"name": "operating_system", "type": "string", "required": True, "description": "Operating system name and version", "category": "technical"},
    {"name": "os_version", "type": "string", "required": False, "description": "Detailed OS version", "category": "technical"},
    {"name": "cpu_cores", "type": "integer", "required": True, "description": "Number of CPU cores", "category": "technical"},
    {"name": "memory_gb", "type": "number", "required": True, "description": "Memory in gigabytes", "category": "technical"},
    {"name": "storage_gb", "type": "number", "required": False, "description": "Total storage in gigabytes", "category": "technical"},
    {"name": "architecture", "type": "string", "required": False, "description": "System architecture (x86_64, arm64, etc.)", "category": "technical"},
    
    # Network fields
    {"name": "ip_address", "type": "string", "required": True, "description": "Primary IP address", "category": "network"},
    {"name": "mac_address", "type": "string", "required": False, "description": "MAC address", "category": "network"},
    {"name": "subnet", "type": "string", "required": False, "description": "Network subnet", "category": "network"},
    {"name": "vlan", "type": "string", "required": False, "description": "VLAN identifier", "category": "network"},
    {"name": "dns_name", "type": "string", "required": False, "description": "DNS name", "category": "network"},
    
    # Environment fields
    {"name": "environment", "type": "enum", "required": True, "description": "Environment (production, staging, dev, etc.)", "category": "environment"},
    {"name": "datacenter", "type": "string", "required": False, "description": "Datacenter location", "category": "environment"},
    {"name": "region", "type": "string", "required": False, "description": "Geographic region", "category": "environment"},
    {"name": "availability_zone", "type": "string", "required": False, "description": "Availability zone", "category": "environment"},
    {"name": "rack", "type": "string", "required": False, "description": "Rack location", "category": "environment"},
    
    # Business fields
    {"name": "owner", "type": "string", "required": True, "description": "Technical owner", "category": "business"},
    {"name": "business_owner", "type": "string", "required": False, "description": "Business owner", "category": "business"},
    {"name": "department", "type": "string", "required": False, "description": "Department", "category": "business"},
    {"name": "cost_center", "type": "string", "required": False, "description": "Cost center", "category": "business"},
    {"name": "business_unit", "type": "string", "required": False, "description": "Business unit", "category": "business"},
    {"name": "application", "type": "string", "required": False, "description": "Application name", "category": "business"},
    {"name": "criticality", "type": "enum", "required": False, "description": "Business criticality level", "category": "business"},
    
    # Cloud readiness fields
    {"name": "virtualization_platform", "type": "string", "required": False, "description": "Current virtualization platform", "category": "cloud_readiness"},
    {"name": "is_virtual", "type": "boolean", "required": False, "description": "Is this a virtual machine", "category": "cloud_readiness"},
    {"name": "migration_readiness", "type": "enum", "required": False, "description": "Migration readiness status", "category": "cloud_readiness"},
    {"name": "target_cloud", "type": "string", "required": False, "description": "Target cloud platform", "category": "cloud_readiness"},
    
    # Metadata fields
    {"name": "created_date", "type": "datetime", "required": False, "description": "Asset creation date", "category": "metadata"},
    {"name": "last_updated", "type": "datetime", "required": False, "description": "Last update timestamp", "category": "metadata"},
    {"name": "tags", "type": "array", "required": False, "description": "Asset tags", "category": "metadata"},
    {"name": "notes", "type": "text", "required": False, "description": "Additional notes", "category": "metadata"},
]

@router.get("/available-target-fields")
async def get_available_target_fields(
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get available target fields for field mapping.
    
    Returns standard asset fields organized by category.
    """
    try:
        logger.info(f"Getting available target fields for client {context.client_account_id}")
        
        # Group fields by category
        categories = {}
        for field in STANDARD_TARGET_FIELDS:
            category = field["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(field)
        
        # Count required fields
        required_count = sum(1 for field in STANDARD_TARGET_FIELDS if field["required"])
        
        return {
            "success": True,
            "fields": STANDARD_TARGET_FIELDS,
            "categories": categories,
            "total_fields": len(STANDARD_TARGET_FIELDS),
            "required_fields": required_count,
            "category_count": len(categories),
            "message": f"Retrieved {len(STANDARD_TARGET_FIELDS)} target fields across {len(categories)} categories"
        }
        
    except Exception as e:
        logger.error(f"Error getting available target fields: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve target fields: {str(e)}"
        )

@router.get("/target-field-categories")
async def get_target_field_categories(
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get available target field categories.
    """
    try:
        categories = list(set(field["category"] for field in STANDARD_TARGET_FIELDS))
        categories.sort()
        
        return {
            "success": True,
            "categories": categories,
            "total": len(categories)
        }
        
    except Exception as e:
        logger.error(f"Error getting field categories: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve field categories: {str(e)}"
        )