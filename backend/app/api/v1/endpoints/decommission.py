"""
Decommission API endpoints for system retirement and data retention.
"""

from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import get_current_context
from app.core.database import get_db

router = APIRouter()


@router.get("/data-retention")
async def get_data_retention(
    db: AsyncSession = Depends(get_db), context=Depends(get_current_context)
) -> Dict[str, Any]:
    """Get data retention policy and requirements for system decommissioning."""

    # Return data retention info in the format expected by frontend
    data_retention_info = {
        "metrics": [
            {
                "label": "Data Archived",
                "value": "2.4 TB",
                "color": "#22C55E",
                "icon": "archive",
            },
            {
                "label": "Systems Retired",
                "value": "12",
                "color": "#F59E0B",
                "icon": "server",
            },
            {
                "label": "Retention Policies",
                "value": "8",
                "color": "#3B82F6",
                "icon": "file-text",
            },
            {
                "label": "Compliance Score",
                "value": "98%",
                "color": "#10B981",
                "icon": "shield-check",
            },
        ],
        "policies": [
            {
                "id": "pol-001",
                "name": "Business Critical Data",
                "description": "Financial records, audit trails, and compliance data",
                "retentionPeriod": "7 years",
                "complianceReqs": ["GDPR", "SOX", "HIPAA"],
                "dataTypes": ["Financial Records", "Audit Trails", "Compliance Data"],
                "storageLocation": "Encrypted Cloud Archive",
                "status": "Active",
                "affectedSystems": 15,
            },
            {
                "id": "pol-002",
                "name": "Application Data",
                "description": "User data, application logs, and configuration files",
                "retentionPeriod": "3 years",
                "complianceReqs": ["GDPR", "CCPA"],
                "dataTypes": ["User Data", "Application Logs", "Configuration Files"],
                "storageLocation": "Secure Archive Storage",
                "status": "Active",
                "affectedSystems": 8,
            },
            {
                "id": "pol-003",
                "name": "System Logs",
                "description": "Security logs, system events, and monitoring data",
                "retentionPeriod": "1 year",
                "complianceReqs": ["SOX", "PCI-DSS"],
                "dataTypes": ["Security Logs", "System Events", "Monitoring Data"],
                "storageLocation": "Log Archive System",
                "status": "Active",
                "affectedSystems": 25,
            },
        ],
        "archiveJobs": [
            {
                "id": "job-001",
                "systemName": "Legacy CRM System",
                "dataSize": "847 GB",
                "status": "In Progress",
                "progress": 75,
                "startDate": "2025-01-15",
                "estimatedCompletion": "2025-01-20",
                "priority": "High",
                "policy": "Business Critical Data",
            },
            {
                "id": "job-002",
                "systemName": "Old Email Server",
                "dataSize": "1.2 TB",
                "status": "Queued",
                "progress": 0,
                "startDate": "2025-01-22",
                "estimatedCompletion": "2025-01-28",
                "priority": "Medium",
                "policy": "Application Data",
            },
            {
                "id": "job-003",
                "systemName": "Legacy Database",
                "dataSize": "345 GB",
                "status": "Completed",
                "progress": 100,
                "startDate": "2025-01-10",
                "estimatedCompletion": "2025-01-12",
                "priority": "High",
                "policy": "Business Critical Data",
            },
        ],
        "retentionSteps": [
            {
                "step": 1,
                "title": "Data Classification",
                "description": "Classify all data according to retention requirements",
                "status": "completed",
            },
            {
                "step": 2,
                "title": "Policy Assignment",
                "description": "Assign appropriate retention policies to each data type",
                "status": "completed",
            },
            {
                "step": 3,
                "title": "Archive Setup",
                "description": "Configure secure archive storage systems",
                "status": "in-progress",
            },
            {
                "step": 4,
                "title": "Data Migration",
                "description": "Migrate data to long-term archive storage",
                "status": "pending",
            },
            {
                "step": 5,
                "title": "Verification",
                "description": "Verify data integrity and accessibility",
                "status": "pending",
            },
        ],
    }

    return data_retention_info


@router.post("/initialize")
async def initialize_decommission(
    data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    context=Depends(get_current_context),
) -> Dict[str, Any]:
    """Initialize decommission process for specified systems."""

    systems = data.get("systems", [])
    if not systems:
        raise HTTPException(
            status_code=400, detail="No systems specified for decommission"
        )

    # Create decommission plan
    decommission_plan = {
        "id": f"decom_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "systems": systems,
        "status": "planning",
        "created_at": datetime.now().isoformat(),
        "phases": [
            {
                "name": "decommission_planning",
                "status": "active",
                "description": "Plan safe system decommissioning",
                "estimated_duration": "2-4 weeks",
            },
            {
                "name": "data_migration",
                "status": "pending",
                "description": "Migrate and archive critical data",
                "estimated_duration": "1-3 weeks",
            },
            {
                "name": "system_shutdown",
                "status": "pending",
                "description": "Safely shutdown systems",
                "estimated_duration": "1 week",
            },
        ],
    }

    return {
        "message": "Decommission process initialized successfully",
        "decommission_plan": decommission_plan,
    }


@router.get("/status/{decommission_id}")
async def get_decommission_status(
    decommission_id: str,
    db: AsyncSession = Depends(get_db),
    context=Depends(get_current_context),
) -> Dict[str, Any]:
    """Get status of decommission process."""

    # Mock status response
    status_info = {
        "id": decommission_id,
        "status": "in_progress",
        "current_phase": "data_migration",
        "progress": 45,
        "last_updated": datetime.now().isoformat(),
        "phases": [
            {
                "name": "decommission_planning",
                "status": "completed",
                "progress": 100,
                "completed_at": (datetime.now() - timedelta(days=7)).isoformat(),
            },
            {
                "name": "data_migration",
                "status": "in_progress",
                "progress": 45,
                "started_at": (datetime.now() - timedelta(days=3)).isoformat(),
            },
            {"name": "system_shutdown", "status": "pending", "progress": 0},
        ],
    }

    return status_info


@router.get("/checklist")
async def get_decommission_checklist(
    db: AsyncSession = Depends(get_db), context=Depends(get_current_context)
) -> Dict[str, Any]:
    """Get comprehensive decommission checklist."""

    checklist = {
        "pre_decommission": [
            {
                "task": "Inventory all applications and systems",
                "status": "pending",
                "priority": "high",
            },
            {
                "task": "Identify data retention requirements",
                "status": "pending",
                "priority": "high",
            },
            {
                "task": "Assess compliance obligations",
                "status": "pending",
                "priority": "high",
            },
            {
                "task": "Create communication plan",
                "status": "pending",
                "priority": "medium",
            },
        ],
        "data_migration": [
            {
                "task": "Export critical business data",
                "status": "pending",
                "priority": "high",
            },
            {
                "task": "Archive system configurations",
                "status": "pending",
                "priority": "medium",
            },
            {
                "task": "Preserve security logs",
                "status": "pending",
                "priority": "medium",
            },
            {
                "task": "Validate data integrity",
                "status": "pending",
                "priority": "high",
            },
        ],
        "system_shutdown": [
            {
                "task": "Graceful service shutdown",
                "status": "pending",
                "priority": "high",
            },
            {"task": "Secure data wiping", "status": "pending", "priority": "high"},
            {
                "task": "Infrastructure cleanup",
                "status": "pending",
                "priority": "medium",
            },
            {"task": "Access revocation", "status": "pending", "priority": "high"},
        ],
    }

    return checklist
