"""
Quality Analysis Module - Data quality assessment and issue management.
Handles data quality analysis, issue detection, and resolution tracking.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.database import get_db
from app.models.data_import import (
    DataImport,  # DataQualityIssue removed in consolidation
    RawImportRecord,
)

from .utilities import expand_abbreviation, get_suggested_value, is_valid_ip

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/imports/{import_id}/quality-issues")
async def get_data_quality_issues(
    import_id: str,
    issue_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get data quality issues for a specific import."""
    query = select(DataQualityIssue).where(DataQualityIssue.data_import_id == import_id)
    
    if issue_type:
        query = query.where(DataQualityIssue.issue_type == issue_type)
    if status:
        query = query.where(DataQualityIssue.status == status)
    
    query = query.order_by(desc(DataQualityIssue.severity), desc(DataQualityIssue.confidence_score))
    
    result = await db.execute(query)
    issues = result.scalars().all()
    
    issues_list = []
    for issue in issues:
        issues_list.append({
            "id": str(issue.id),
            "issue_type": issue.issue_type,
            "field_name": issue.field_name,
            "current_value": issue.current_value,
            "suggested_value": issue.suggested_value,
            "severity": issue.severity,
            "confidence_score": issue.confidence_score,
            "reasoning": issue.reasoning,
            "status": issue.status,
            "detected_at": issue.detected_at.isoformat() if issue.detected_at else None
        })
    
    return {"issues": issues_list}

@router.delete("/imports/{import_id}/quality-issues/{issue_id}")
async def resolve_quality_issue(
    import_id: str,
    issue_id: str,
    resolution_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Resolve a data quality issue."""
    query = select(DataQualityIssue).where(
        and_(
            DataQualityIssue.data_import_id == import_id,
            DataQualityIssue.id == issue_id
        )
    )
    
    result = await db.execute(query)
    issue = result.scalar_one_or_none()
    
    if not issue:
        raise HTTPException(status_code=404, detail="Quality issue not found")
    
    issue.status = resolution_data.get("status", "resolved")
    issue.resolved_value = resolution_data.get("resolved_value")
    issue.resolution_notes = resolution_data.get("notes")
    
    await db.commit()
    
    return {"status": "resolved"}

async def analyze_data_quality(data_import: DataImport, raw_records: List[RawImportRecord], 
                              db: AsyncSession, context: RequestContext):
    """Analyze data quality and create issue records with context awareness."""
    issues = []
    
    # Get a sample record to understand the column structure
    if not raw_records:
        return
    
    sample_data = raw_records[0].raw_data
    available_fields = list(sample_data.keys())
    
    # Create field mapping from CSV columns to standard fields
    field_mappings = {
        'hostname': ['NAME', 'HOSTNAME', 'name', 'hostname', 'asset_name'],
        'ip_address': ['IP ADDRESS', 'IP_ADDRESS', 'ip_address', 'ip', 'IP'],
        'operating_system': ['OS', 'OPERATING_SYSTEM', 'operating_system', 'os'],
        'asset_type': ['TYPE', 'ASSET_TYPE', 'asset_type', 'type'],
        'environment': ['ENVIRONMENT', 'environment', 'env'],
        'cpu_cores': ['CPU (CORES)', 'CPU_CORES', 'cpu_cores', 'cores', 'CPU'],
        'memory_gb': ['RAM (GB)', 'MEMORY_GB', 'memory_gb', 'ram', 'memory'],
        'location': ['LOCATION', 'location', 'datacenter', 'dc']
    }
    
    # Find actual field mappings in the CSV
    actual_mappings = {}
    for standard_field, possible_names in field_mappings.items():
        for possible_name in possible_names:
            if possible_name in available_fields:
                actual_mappings[standard_field] = possible_name
                break
    
    logger.info(f"Found field mappings for client {context.client_account_id}: {actual_mappings}")
    
    for record in raw_records:
        raw_data = record.raw_data
        
        # Check for missing critical fields using actual field mappings
        for standard_field, csv_field in actual_mappings.items():
            value = raw_data.get(csv_field)
            
            # Check if value is missing or empty (including <empty> placeholder)
            if not value or value in ['', '<empty>', 'Unknown', 'NULL', 'null', 'N/A', 'undefined']:
                suggested_value = get_suggested_value(standard_field, raw_data)
                
                severity = 'high' if standard_field in ['hostname', 'asset_type'] else 'medium'
                
                issue = DataQualityIssue(
                    data_import_id=data_import.id,
                    raw_record_id=record.id,
                    issue_type='missing_data',
                    field_name=csv_field,  # Use the actual CSV field name
                    current_value=str(value) if value else '<empty>',
                    suggested_value=suggested_value,
                    severity=severity,
                    confidence_score=0.8,
                    reasoning=f"Field '{csv_field}' (mapped to {standard_field}) is missing or empty for asset {raw_data.get('ID', 'Unknown')}. AI suggests '{suggested_value}' based on asset patterns.",
                    status='pending'
                )
                issues.append(issue)
        
        # Check for format issues
        if 'IP ADDRESS' in raw_data or 'IP_ADDRESS' in raw_data:
            ip_field = 'IP ADDRESS' if 'IP ADDRESS' in raw_data else 'IP_ADDRESS'
            ip_value = raw_data.get(ip_field)
            
            # Only flag as format error if value exists but is invalid format (not missing)
            if ip_value and ip_value not in ['<empty>', '', 'Unknown'] and not is_valid_ip(ip_value):
                issue = DataQualityIssue(
                    data_import_id=data_import.id,
                    raw_record_id=record.id,
                    issue_type='format_error',
                    field_name=ip_field,
                    current_value=str(ip_value),
                    suggested_value='192.168.1.100',
                    severity='medium',
                    confidence_score=0.9,
                    reasoning=f"IP address '{ip_value}' appears to have invalid format.",
                    status='pending'
                )
                issues.append(issue)
        
        # Check for abbreviated values that need expansion
        type_field = actual_mappings.get('asset_type')
        if type_field and raw_data.get(type_field):
            type_value = raw_data.get(type_field)
            if type_value and len(type_value) <= 3 and type_value not in ['<empty>', '']:
                expanded_value = expand_abbreviation(type_value)
                if expanded_value != type_value:
                    issue = DataQualityIssue(
                        data_import_id=data_import.id,
                        raw_record_id=record.id,
                        issue_type='format_error',
                        field_name=type_field,
                        current_value=str(type_value),
                        suggested_value=expanded_value,
                        severity='low',
                        confidence_score=0.7,
                        reasoning=f"Asset type '{type_value}' appears to be abbreviated. Consider expanding to '{expanded_value}' for clarity.",
                        status='pending'
                    )
                    issues.append(issue)
    
    # Bulk insert issues
    if issues:
        db.add_all(issues)
        await db.commit()
        logger.info(f"Created {len(issues)} data quality issues")
    else:
        logger.info("No data quality issues detected") 