"""
Data Import API endpoints for persistent storage of raw import data.
Enhanced with multi-tenant context awareness and automatic session management.
"""

import uuid
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, desc, select
import re
import pandas as pd
from io import StringIO
import logging

from app.core.database import get_db
from app.core.context import get_current_context, RequestContext
from app.models.data_import import (
    DataImport, RawImportRecord, ImportProcessingStep, 
    ImportFieldMapping, DataQualityIssue, ImportStatus, ImportType,
    CustomTargetField, MappingLearningPattern
)

# Make client_account import conditional to avoid deployment failures
try:
    from app.models.client_account import ClientAccount, Engagement
    CLIENT_ACCOUNT_AVAILABLE = True
except ImportError:
    CLIENT_ACCOUNT_AVAILABLE = False
    ClientAccount = None
    Engagement = None

# Import session management service
try:
    from app.services.session_management_service import SessionManagementService, create_session_management_service
    SESSION_MANAGEMENT_AVAILABLE = True
except ImportError:
    SESSION_MANAGEMENT_AVAILABLE = False
    SessionManagementService = None

from app.models.asset import Asset
from app.repositories.demo_repository import DemoRepository
from app.repositories.session_aware_repository import create_session_aware_repository
from app.schemas.demo import DemoAssetResponse

router = APIRouter()

logger = logging.getLogger(__name__)

@router.post("/upload")
async def upload_data_file(
    file: UploadFile = File(...),
    import_type: str = Form(...),
    import_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Upload and create a new data import session with automatic session management."""
    try:
        # Get current context from middleware
        context = get_current_context()
        
        # Read file content
        content = await file.read()
        file_hash = hashlib.sha256(content).hexdigest()
        
        # Create or get active session using SessionManagementService
        session_id = None
        if SESSION_MANAGEMENT_AVAILABLE:
            try:
                session_service = create_session_management_service(db)
                session = await session_service.get_or_create_active_session(
                    client_account_id=context.client_account_id,
                    engagement_id=context.engagement_id,
                    auto_create=True
                )
                session_id = str(session.id) if session else None
                logger.info(f"Using session {session_id} for data import")
            except Exception as session_e:
                logger.warning(f"Session management failed, continuing without session: {session_e}")
        
        # Create data import record with context
        data_import = DataImport(
            client_account_id=context.client_account_id or "bafd5b46-aaaf-4c95-8142-573699d93171",  # Complete Test Client UUID
            engagement_id=context.engagement_id,
            session_id=session_id,  # Link to session if available
            import_name=import_name or f"{file.filename} Import",
            import_type=import_type,
            description=description,
            source_filename=file.filename,
            file_size_bytes=len(content),
            file_type=file.content_type,
            file_hash=file_hash,
            status=ImportStatus.UPLOADED,
            imported_by=context.user_id,
            is_mock=False  # This is now real data import
        )
        
        db.add(data_import)
        await db.commit()
        await db.refresh(data_import)
        
        # Process the file content
        await process_uploaded_file(data_import, content, db, context)
        
        return {
            "import_id": str(data_import.id),
            "session_id": session_id,
            "client_account_id": context.client_account_id,
            "engagement_id": context.engagement_id,
            "status": "uploaded",
            "filename": file.filename,
            "size_bytes": len(content),
            "message": "File uploaded and processing started"
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

async def process_uploaded_file(data_import: DataImport, content: bytes, db: AsyncSession, context: RequestContext):
    """Process uploaded file and create raw import records with context awareness."""
    try:
        # Update status to processing
        data_import.status = ImportStatus.PROCESSING
        await db.commit()
        
        # Parse file content (assuming CSV for demo)
        import csv
        import io
        
        content_str = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(content_str))
        
        raw_records = []
        row_number = 1
        
        for row in csv_reader:
            # Create raw import record with context
            raw_record = RawImportRecord(
                data_import_id=data_import.id,
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id,
                session_id=data_import.session_id,
                row_number=row_number,
                record_id=row.get('ID') or row.get('id') or f"ROW_{row_number}",
                raw_data=dict(row),  # Store exactly as imported
                is_processed=False,
                is_valid=True
            )
            raw_records.append(raw_record)
            row_number += 1
        
        # Bulk insert raw records
        db.add_all(raw_records)
        
        # Update import statistics
        data_import.total_records = len(raw_records)
        data_import.status = ImportStatus.PROCESSED
        data_import.completed_at = datetime.utcnow()
        
        await db.commit()
        
        # Analyze data quality issues
        await analyze_data_quality(data_import, raw_records, db, context)
        
    except Exception as e:
        data_import.status = ImportStatus.FAILED
        await db.commit()
        raise e

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
                    client_account_id=context.client_account_id,
                    engagement_id=context.engagement_id,
                    session_id=data_import.session_id,
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
                    client_account_id=context.client_account_id,
                    engagement_id=context.engagement_id,
                    session_id=data_import.session_id,
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
                        client_account_id=context.client_account_id,
                        engagement_id=context.engagement_id,
                        session_id=data_import.session_id,
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
        print(f"Created {len(issues)} data quality issues")
    else:
        print("No data quality issues detected")

def expand_abbreviation(value: str) -> str:
    """Expand common abbreviations."""
    expansions = {
        'DB': 'Database',
        'SRV': 'Server', 
        'APP': 'Application',
        'WEB': 'Web Server',
        'API': 'API Service'
    }
    return expansions.get(value.upper(), value)

def get_suggested_value(field: str, raw_data: Dict[str, Any]) -> str:
    """Generate AI-suggested values for missing fields."""
    suggestions = {
        'hostname': f"server-{raw_data.get('ID', '001')}",
        'ip_address': '192.168.1.100',
        'operating_system': 'Windows Server 2019',
        'asset_type': 'Server',
        'environment': 'Production'
    }
    return suggestions.get(field, 'Unknown')

def is_valid_ip(ip: str) -> bool:
    """Basic IP address validation."""
    try:
        parts = ip.split('.')
        return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
    except:
        return False

@router.get("/imports")
async def get_data_imports(
    limit: int = 10,
    offset: int = 0,
    view_mode: str = "engagement_view",  # "session_view" or "engagement_view"
    db: AsyncSession = Depends(get_db)
):
    """Get list of data imports with context-aware filtering."""
    context = get_current_context()
    
    # Use session-aware repository for context-aware data access
    import_repo = create_session_aware_repository(db, DataImport, view_mode=view_mode)
    imports = await import_repo.get_all(limit=limit, offset=offset)
    
    return {
        "imports": [import_to_dict(imp) for imp in imports],
        "context": {
            "client_account_id": context.client_account_id,
            "engagement_id": context.engagement_id,
            "session_id": context.session_id,
            "view_mode": view_mode
        }
    }

@router.get("/imports/{import_id}/raw-records")
async def get_raw_import_records(
    import_id: str,
    limit: int = 100,
    offset: int = 0,
    view_mode: str = "engagement_view",
    db: AsyncSession = Depends(get_db)
):
    """Get raw import records for a specific import with context awareness."""
    context = get_current_context()
    
    # Use session-aware repository for context-aware data access
    record_repo = create_session_aware_repository(db, RawImportRecord, view_mode=view_mode)
    records = await record_repo.get_by_filters(data_import_id=import_id)
    
    # Apply pagination
    paginated_records = records[offset:offset + limit]
    
    records_list = []
    for record in paginated_records:
        records_list.append({
            "id": str(record.id),
            "row_number": record.row_number,
            "record_id": record.record_id,
            "raw_data": record.raw_data,
            "processed_data": record.processed_data,
            "is_processed": record.is_processed,
            "is_valid": record.is_valid,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "session_id": record.session_id
        })
    
    return {
        "records": records_list,
        "context": {
            "client_account_id": context.client_account_id,
            "engagement_id": context.engagement_id,
            "view_mode": view_mode,
            "total_records": len(records),
            "paginated_count": len(paginated_records)
        }
    }

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

@router.get("/imports/latest")
async def get_latest_import(
    view_mode: str = "engagement_view",
    db: AsyncSession = Depends(get_db)
):
    """Get the latest data import for the current context."""
    context = get_current_context()
    
    # Use session-aware repository for context-aware data access
    import_repo = create_session_aware_repository(db, DataImport, view_mode=view_mode)
    imports = await import_repo.get_all(limit=1)
    
    if not imports:
        raise HTTPException(status_code=404, detail="No imports found for current context")
    
    latest = imports[0]
    result = import_to_dict(latest)
    result["context"] = {
        "client_account_id": context.client_account_id,
        "engagement_id": context.engagement_id,
        "session_id": context.session_id,
        "view_mode": view_mode
    }
    
    return result

@router.get("/imports/{import_id}/field-mappings")
async def get_field_mappings(
    import_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get field mappings for a specific import."""
    query = select(ImportFieldMapping).where(ImportFieldMapping.data_import_id == import_id)
    result = await db.execute(query)
    mappings = result.scalars().all()
    
    return {
        "mappings": [
            {
                "id": str(mapping.id),
                "source_field": mapping.source_field,
                "target_field": mapping.target_field,
                "mapping_type": mapping.mapping_type,
                "confidence_score": mapping.confidence_score,
                "is_user_defined": mapping.is_user_defined,
                "status": mapping.status,
                "created_at": mapping.created_at.isoformat() if mapping.created_at else None
            }
            for mapping in mappings
        ]
    }

@router.post("/imports/{import_id}/field-mappings")
async def create_field_mapping(
    import_id: str,
    mapping_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Create a new field mapping."""
    mapping = ImportFieldMapping(
        data_import_id=import_id,
        source_field=mapping_data["source_field"],
        target_field=mapping_data["target_field"],
        mapping_type=mapping_data.get("mapping_type", "direct"),
        confidence_score=mapping_data.get("confidence_score", 1.0),
        is_user_defined=mapping_data.get("is_user_defined", True),
        validation_rules=mapping_data.get("validation_rules"),
        transformation_logic=mapping_data.get("transformation_logic"),
        status="approved"
    )
    
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    
    return {
        "id": str(mapping.id),
        "source_field": mapping.source_field,
        "target_field": mapping.target_field,
        "status": "created"
    }

@router.get("/available-target-fields")
async def get_available_target_fields():
    """Get list of available target fields for mapping."""
    # Standard CMDB fields
    standard_fields = [
        {"name": "hostname", "type": "string", "required": True, "description": "Asset hostname or server ID"},
        {"name": "asset_name", "type": "string", "required": False, "description": "Descriptive name of application/service"},
        {"name": "ip_address", "type": "string", "required": False, "description": "Primary IP address"},
        {"name": "mac_address", "type": "string", "required": False, "description": "MAC address (separate from IP)"},
        {"name": "asset_type", "type": "string", "required": True, "description": "Type of asset (Server, Database, etc.)"},
        {"name": "operating_system", "type": "string", "required": False, "description": "Operating system"},
        {"name": "environment", "type": "string", "required": True, "description": "Environment (Production, Test, etc.)"},
        {"name": "cpu_cores", "type": "integer", "required": False, "description": "Number of CPU cores"},
        {"name": "memory_gb", "type": "number", "required": False, "description": "Memory in GB"},
        {"name": "storage_gb", "type": "number", "required": False, "description": "Storage in GB"},
        {"name": "location", "type": "string", "required": False, "description": "Physical location or datacenter"},
        {"name": "department", "type": "string", "required": False, "description": "Owning department"},
        {"name": "business_criticality", "type": "string", "required": False, "description": "Business criticality level"},
        {"name": "cost_center", "type": "string", "required": False, "description": "Cost center code"},
        {"name": "owner", "type": "string", "required": False, "description": "Asset owner"},
        {"name": "vendor", "type": "string", "required": False, "description": "Hardware/software vendor"},
        {"name": "model", "type": "string", "required": False, "description": "Asset model number"},
        {"name": "serial_number", "type": "string", "required": False, "description": "Serial number"},
        {"name": "purchase_date", "type": "date", "required": False, "description": "Purchase date"},
        {"name": "warranty_end", "type": "date", "required": False, "description": "Warranty end date"},
        {"name": "application_name", "type": "string", "required": False, "description": "Primary application running on asset"},
        {"name": "database_name", "type": "string", "required": False, "description": "Database name if applicable"},
        {"name": "service_tier", "type": "string", "required": False, "description": "Service tier classification"}
    ]
    
    return {"fields": standard_fields}

@router.post("/custom-fields")
async def create_custom_field(
    field_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Create a custom target field dynamically that becomes available for all future mappings."""
    try:
        # Validate field data
        required_fields = ["field_name", "field_type"]
        for field in required_fields:
            if field not in field_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        field_name = field_data["field_name"].lower().replace(" ", "_").replace('(', '').replace(')', '')
        
        # Check if field already exists
        existing_query = select(CustomTargetField).where(
            and_(
                CustomTargetField.field_name == field_name,
                CustomTargetField.client_account_id == "d838573d-f461-44e4-81b5-5af510ef83b7"
            )
        )
        existing_result = await db.execute(existing_query)
        existing_field = existing_result.scalar_one_or_none()
        
        if existing_field:
            return {
                "field_name": field_name,
                "status": "already_exists",
                "message": f"Field '{field_name}' already exists",
                "field_id": str(existing_field.id)
            }
        
        # Create new custom field
        custom_field = CustomTargetField(
            client_account_id="d838573d-f461-44e4-81b5-5af510ef83b7",
            field_name=field_name,
            field_type=field_data["field_type"],
            description=field_data.get("description", f"Custom field: {field_name}"),
            is_required=field_data.get("required", False),
            is_critical=field_data.get("is_critical", False),
            created_by="eef6ea50-6550-4f14-be2c-081d4eb23038",  # Demo user
            validation_schema=field_data.get("validation_schema"),
            default_value=field_data.get("default_value"),
            allowed_values=field_data.get("allowed_values")
        )
        
        db.add(custom_field)
        await db.commit()
        await db.refresh(custom_field)
        
        return {
            "field_id": str(custom_field.id),
            "field_name": custom_field.field_name,
            "field_type": custom_field.field_type,
            "description": custom_field.description,
            "status": "created",
            "message": f"Custom field '{field_name}' created successfully and is now available for mapping"
        }
    except Exception as e:
        await db.rollback()
        print(f"Error creating custom field: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create custom field: {str(e)}")

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

@router.get("/imports/{import_id}/field-mapping-suggestions")
async def get_field_mapping_suggestions(
    import_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get AI-learned field mapping suggestions based on historical patterns."""
    try:
        # Get raw records to analyze content
        query = select(RawImportRecord).where(RawImportRecord.data_import_id == import_id).limit(10)
        result = await db.execute(query)
        records = result.scalars().all()
        
        if not records:
            return {"suggestions": []}
        
        # Get all available target fields (standard + custom)
        available_fields = await get_all_available_fields(db)
        
        # Get learned patterns for this client
        client_account_id = "d838573d-f461-44e4-81b5-5af510ef83b7"  # Demo context
        learned_patterns = await get_learned_patterns(client_account_id, db)
        
        # Analyze each source field using AI learning
        sample_data = records[0].raw_data
        suggestions = []
        
        for source_field, sample_value in sample_data.items():
            suggestion = generate_learned_suggestion(
                source_field, 
                sample_value,
                [record.raw_data.get(source_field, "") for record in records[:5]],
                available_fields,
                learned_patterns
            )
            if suggestion:
                suggestions.append(suggestion)
        
        return {"suggestions": suggestions}
    except Exception as e:
        print(f"Error in field mapping suggestions: {e}")
        return {"suggestions": [], "error": str(e)}

async def get_all_available_fields(db: AsyncSession):
    """Get both standard and custom target fields."""
    # Standard fields (from your existing endpoint)
    standard_fields = [
        {"name": "hostname", "type": "string", "required": True, "description": "Asset hostname or server ID"},
        {"name": "asset_name", "type": "string", "required": False, "description": "Descriptive name of application/service"},
        {"name": "ip_address", "type": "string", "required": False, "description": "Primary IP address"},
        {"name": "asset_type", "type": "string", "required": True, "description": "Type of asset"},
        {"name": "operating_system", "type": "string", "required": False, "description": "Operating system"},
        {"name": "environment", "type": "string", "required": True, "description": "Environment"},
        {"name": "cpu_cores", "type": "integer", "required": False, "description": "Number of CPU cores"},
        {"name": "memory_gb", "type": "number", "required": False, "description": "Memory in GB"},
        {"name": "location", "type": "string", "required": False, "description": "Physical location"},
        {"name": "department", "type": "string", "required": False, "description": "Owning department"},
        {"name": "owner", "type": "string", "required": False, "description": "Asset owner"},
        {"name": "vendor", "type": "string", "required": False, "description": "Hardware/software vendor"},
        {"name": "model", "type": "string", "required": False, "description": "Asset model number"}
    ]
    
    try:
        # Get custom fields for this client
        query = select(CustomTargetField).where(CustomTargetField.client_account_id == "d838573d-f461-44e4-81b5-5af510ef83b7")
        result = await db.execute(query)
        custom_fields = result.scalars().all()
        
        # Combine standard and custom fields
        all_fields = standard_fields + [
            {
                "name": field.field_name,
                "type": field.field_type,
                "required": field.is_required,
                "description": field.description,
                "is_custom": True,
                "usage_count": field.usage_count,
                "success_rate": field.success_rate
            }
            for field in custom_fields
        ]
        
        return all_fields
    except Exception as e:
        print(f"Error getting custom fields: {e}")
        return standard_fields

async def get_learned_patterns(client_account_id: str, db: AsyncSession):
    """Get AI-learned mapping patterns for this client."""
    try:
        query = select(MappingLearningPattern).where(
            MappingLearningPattern.client_account_id == client_account_id
        ).order_by(MappingLearningPattern.pattern_confidence.desc())
        
        result = await db.execute(query)
        patterns = result.scalars().all()
        
        return [
            {
                "source_pattern": pattern.source_field_pattern,
                "target_field": pattern.target_field,
                "confidence": pattern.pattern_confidence,
                "content_pattern": pattern.content_pattern,
                "matching_rules": pattern.matching_rules,
                "success_count": pattern.success_count,
                "failure_count": pattern.failure_count
            }
            for pattern in patterns
        ]
    except Exception as e:
        print(f"Error getting learned patterns: {e}")
        return []

def generate_learned_suggestion(source_field: str, sample_value: str, all_values: list, available_fields: list, learned_patterns: list):
    """Generate mapping suggestions using learned patterns instead of hardcoded rules."""
    best_suggestion = None
    max_confidence = 0.0
    
    # First, try learned patterns
    for pattern in learned_patterns:
        confidence = calculate_pattern_match(source_field, sample_value, all_values, pattern)
        
        if confidence > max_confidence and confidence > 0.3:  # Minimum confidence threshold
            max_confidence = confidence
            best_suggestion = {
                "source_field": source_field,
                "target_field": pattern["target_field"],
                "confidence": confidence,
                "reasoning": f"AI learned pattern: '{pattern['source_pattern']}' → '{pattern['target_field']}' (success rate: {pattern['success_count']}/{pattern['success_count'] + pattern['failure_count']})",
                "sample_values": all_values[:3],
                "mapping_type": "ai_learned",
                "pattern_id": pattern.get("id"),
                "learned_from": f"{pattern['success_count']} successful mappings"
            }
    
    # If no learned pattern matches well, suggest creating a new field
    if not best_suggestion or max_confidence < 0.5:
        # Check if this looks like a new field type
        if is_potential_new_field(source_field, sample_value, available_fields):
            best_suggestion = {
                "source_field": source_field,
                "target_field": None,  # Will be created dynamically
                "confidence": 0.7,
                "reasoning": f"New field detected: '{source_field}' with values like '{sample_value}'. Consider creating a custom target field.",
                "sample_values": all_values[:3],
                "mapping_type": "suggest_new_field",
                "suggested_field_name": source_field.lower().replace(' ', '_').replace('(', '').replace(')', ''),
                "suggested_field_type": infer_field_type(all_values),
                "requires_new_field": True
            }
    
    return best_suggestion

def calculate_pattern_match(source_field: str, sample_value: str, all_values: list, pattern: dict) -> float:
    """Calculate how well a source field matches a learned pattern."""
    confidence = 0.0
    
    # Field name similarity
    if pattern["source_pattern"].lower() in source_field.lower():
        confidence += 0.4
    
    # Content pattern matching
    if pattern.get("content_pattern"):
        content_match = check_content_pattern_match(all_values, pattern["content_pattern"])
        confidence += content_match * 0.4
    
    # Apply custom matching rules if available
    if pattern.get("matching_rules"):
        rule_match = apply_matching_rules(source_field, sample_value, all_values, pattern["matching_rules"])
        confidence += rule_match * 0.2
    
    # Boost confidence based on historical success rate
    base_confidence = pattern.get("confidence", 0.0)
    confidence = confidence * (0.5 + base_confidence * 0.5)
    
    return min(confidence, 1.0)

def check_content_pattern_match(values: list, content_pattern: dict) -> float:
    """Check if values match the learned content pattern."""
    if not content_pattern or not values:
        return 0.0
    
    matches = 0
    total = len(values)
    
    for value in values:
        if not value or value in ['<empty>', '', 'Unknown']:
            continue
            
        # Check data type pattern
        expected_type = content_pattern.get("data_type")
        if expected_type and matches_data_type(value, expected_type):
            matches += 1
            
        # Check format pattern
        format_pattern = content_pattern.get("format_regex")
        if format_pattern and re.search(format_pattern, str(value), re.IGNORECASE):
            matches += 1
            
        # Check value range
        value_range = content_pattern.get("value_range")
        if value_range and is_in_range(value, value_range):
            matches += 1
    
    return matches / max(total, 1)

def apply_matching_rules(source_field: str, sample_value: str, all_values: list, matching_rules: dict) -> float:
    """Apply learned matching rules to calculate confidence."""
    # This would contain AI-learned rules specific to this pattern
    # For now, return basic matching
    return 0.1

def matches_data_type(value: str, expected_type: str) -> bool:
    """Check if value matches expected data type."""
    try:
        if expected_type == "integer":
            int(value)
            return True
        elif expected_type == "float":
            float(value)
            return True
        elif expected_type == "ip_address":
            parts = value.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        elif expected_type == "string":
            return isinstance(value, str) and len(value) > 0
    except:
        pass
    return False

def is_in_range(value: str, value_range: dict) -> bool:
    """Check if value is within expected range."""
    try:
        if "min" in value_range and "max" in value_range:
            num_val = float(value)
            return value_range["min"] <= num_val <= value_range["max"]
    except:
        pass
    return False

def is_potential_new_field(source_field: str, sample_value: str, available_fields: list) -> bool:
    """Check if this looks like a field that should be added to the schema."""
    existing_names = {field["name"] for field in available_fields}
    
    # Don't suggest new field if it's very similar to existing ones
    normalized_source = source_field.lower().replace(' ', '_').replace('(', '').replace(')', '')
    
    for existing in existing_names:
        if normalized_source in existing or existing in normalized_source:
            return False
    
    # Suggest new field if it has meaningful data
    if sample_value and sample_value not in ['<empty>', '', 'Unknown', 'NULL']:
        return True
    
    return False

def infer_field_type(values: list) -> str:
    """Infer the appropriate field type from sample values."""
    if not values:
        return "string"
    
    # Check if all values are integers
    try:
        for value in values[:5]:
            if value and value not in ['<empty>', '', 'Unknown']:
                int(value)
        return "integer"
    except:
        pass
    
    # Check if all values are floats
    try:
        for value in values[:5]:
            if value and value not in ['<empty>', '', 'Unknown']:
                float(value)
        return "number"
    except:
        pass
    
    # Check if values look like dates
    import re
    date_patterns = [
        r'\d{4}-\d{2}-\d{2}',
        r'\d{2}/\d{2}/\d{4}',
        r'\d{2}-\d{2}-\d{4}'
    ]
    
    for value in values[:3]:
        if value and any(re.search(pattern, str(value)) for pattern in date_patterns):
            return "date"
    
    return "string"

def import_to_dict(data_import: DataImport) -> dict:
    """Convert DataImport model to dictionary."""
    return {
        "id": str(data_import.id),
        "import_name": data_import.import_name,
        "import_type": data_import.import_type,
        "source_filename": data_import.source_filename,
        "status": data_import.status,
        "total_records": data_import.total_records,
        "processed_records": data_import.processed_records,
        "failed_records": data_import.failed_records,
        "created_at": data_import.created_at.isoformat() if data_import.created_at else None,
        "completed_at": data_import.completed_at.isoformat() if data_import.completed_at else None
    }

@router.post("/imports/{import_id}/learn-from-mapping")
async def learn_from_user_mapping(
    import_id: str,
    learning_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Store user corrections for AI learning - this is how the system gets smarter."""
    try:
        # Store the corrected mapping
        corrected_mapping = ImportFieldMapping(
            data_import_id=import_id,
            source_field=learning_data["source_field"],
            target_field=learning_data["corrected_target_field"],
            mapping_type="user_corrected",
            confidence_score=1.0,  # User correction has highest confidence
            is_user_defined=True,
            status="approved",
            user_feedback=learning_data.get("feedback", "User corrected AI suggestion"),
            original_ai_suggestion=learning_data.get("original_suggestion"),
            correction_reason=learning_data.get("reason", "User preference")
        )
        
        db.add(corrected_mapping)
        
        # Create or update learning pattern
        await create_or_update_learning_pattern(
            learning_data["source_field"],
            learning_data["corrected_target_field"],
            learning_data.get("sample_values", []),
            learning_data.get("was_correct", False),
            corrected_mapping,
            db
        )
        
        # Update custom field usage if applicable
        if learning_data.get("is_custom_field"):
            await update_custom_field_usage(learning_data["corrected_target_field"], learning_data.get("was_correct", True), db)
        
        await db.commit()
        
        return {
            "status": "learned",
            "message": f"✅ AI learned: '{learning_data['source_field']}' → '{learning_data['corrected_target_field']}'",
            "confidence_improved": True,
            "pattern_created": True
        }
    except Exception as e:
        await db.rollback()
        print(f"Error learning from mapping: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to learn from mapping: {str(e)}")

async def create_or_update_learning_pattern(
    source_field: str, 
    target_field: str, 
    sample_values: list, 
    was_correct: bool,
    mapping: ImportFieldMapping,
    db: AsyncSession
):
    """Create or update AI learning patterns based on user feedback."""
    try:
        # Look for existing pattern
        existing_query = select(MappingLearningPattern).where(
            and_(
                MappingLearningPattern.source_field_pattern == source_field,
                MappingLearningPattern.target_field == target_field,
                MappingLearningPattern.client_account_id == "d838573d-f461-44e4-81b5-5af510ef83b7"
            )
        )
        existing_result = await db.execute(existing_query)
        existing_pattern = existing_result.scalar_one_or_none()
        
        if existing_pattern:
            # Update existing pattern
            if was_correct:
                existing_pattern.success_count += 1
            else:
                existing_pattern.failure_count += 1
            
            existing_pattern.update_success_rate()
            existing_pattern.last_applied_at = datetime.utcnow()
            existing_pattern.times_applied += 1
            
            # Update content pattern with new samples
            content_pattern = existing_pattern.content_pattern or {}
            if sample_values:
                existing_samples = content_pattern.get("sample_values", [])
                content_pattern["sample_values"] = list(set(existing_samples + sample_values[:3]))
                content_pattern["data_type"] = infer_field_type(sample_values)
                existing_pattern.content_pattern = content_pattern
            
        else:
            # Create new learning pattern
            content_pattern = {
                "data_type": infer_field_type(sample_values),
                "sample_values": sample_values[:3],
                "format_regex": generate_format_regex(sample_values)
            }
            
            new_pattern = MappingLearningPattern(
                client_account_id="d838573d-f461-44e4-81b5-5af510ef83b7",
                source_field_pattern=source_field,
                target_field=target_field,
                content_pattern=content_pattern,
                success_count=1 if was_correct else 0,
                failure_count=0 if was_correct else 1,
                pattern_confidence=1.0 if was_correct else 0.0,
                learned_from_mapping_id=mapping.id,
                user_feedback=f"Learned from user mapping: {source_field} → {target_field}",
                matching_rules=generate_matching_rules(source_field, sample_values),
                times_applied=1,
                last_applied_at=datetime.utcnow()
            )
            
            new_pattern.update_success_rate()
            db.add(new_pattern)
    except Exception as e:
        print(f"Error creating/updating learning pattern: {e}")
        raise e

async def update_custom_field_usage(field_name: str, was_successful: bool, db: AsyncSession):
    """Update usage statistics for custom fields."""
    try:
        query = select(CustomTargetField).where(
            and_(
                CustomTargetField.field_name == field_name,
                CustomTargetField.client_account_id == "d838573d-f461-44e4-81b5-5af510ef83b7"
            )
        )
        result = await db.execute(query)
        custom_field = result.scalar_one_or_none()
        
        if custom_field:
            custom_field.usage_count += 1
            custom_field.last_used_at = datetime.utcnow()
            
            # Update success rate
            if was_successful:
                current_successes = custom_field.success_rate * (custom_field.usage_count - 1)
                custom_field.success_rate = (current_successes + 1) / custom_field.usage_count
            else:
                current_successes = custom_field.success_rate * (custom_field.usage_count - 1)
                custom_field.success_rate = current_successes / custom_field.usage_count
    except Exception as e:
        print(f"Error updating custom field usage: {e}")
        raise e

def generate_format_regex(sample_values: list) -> str:
    """Generate a regex pattern from sample values for future matching."""
    if not sample_values:
        return ""
    
    # Simple pattern generation - in production this would be more sophisticated
    first_value = str(sample_values[0]) if sample_values[0] else ""
    
    # IP pattern
    if re.match(r'\d+\.\d+\.\d+\.\d+', first_value):
        return r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
    
    # Server ID pattern
    if re.match(r'[A-Z]{2,4}\d+', first_value.upper()):
        return r'[A-Z]{2,4}\d+'
    
    # Generic alphanumeric
    if first_value.isalnum():
        return r'[A-Za-z0-9]+'
    
    return ""

def generate_matching_rules(source_field: str, sample_values: list) -> dict:
    """Generate matching rules for future AI use."""
    rules = {
        "field_name_patterns": [source_field.lower()],
        "content_validation": {},
        "priority_score": 1.0
    }
    
    # Add content-based rules
    if sample_values:
        rules["content_validation"] = {
            "expected_type": infer_field_type(sample_values),
            "sample_formats": [str(v)[:20] for v in sample_values[:3] if v]
        }
    
    return rules

@router.get("/learning-statistics")
async def get_learning_statistics(db: AsyncSession = Depends(get_db)):
    """Get statistics on how much the AI has learned."""
    try:
        # Get custom fields count
        custom_fields_query = select(CustomTargetField).where(
            CustomTargetField.client_account_id == "d838573d-f461-44e4-81b5-5af510ef83b7"
        )
        custom_fields_result = await db.execute(custom_fields_query)
        custom_fields = custom_fields_result.scalars().all()
        
        # Get learning patterns count
        patterns_query = select(MappingLearningPattern).where(
            MappingLearningPattern.client_account_id == "d838573d-f461-44e4-81b5-5af510ef83b7"
        )
        patterns_result = await db.execute(patterns_query)
        patterns = patterns_result.scalars().all()
        
        # Calculate statistics
        total_patterns = len(patterns)
        successful_patterns = sum(1 for p in patterns if p.pattern_confidence > 0.7)
        total_mappings_learned = sum(p.success_count + p.failure_count for p in patterns)
        
        avg_confidence = sum(p.pattern_confidence for p in patterns) / len(patterns) if patterns else 0
        
        return {
            "learning_summary": {
                "total_custom_fields_created": len(custom_fields),
                "total_patterns_learned": total_patterns,
                "high_confidence_patterns": successful_patterns,
                "total_mappings_processed": total_mappings_learned,
                "average_pattern_confidence": round(avg_confidence, 2),
                "learning_enabled": True
            },
            "custom_fields": [
                {
                    "name": field.field_name,
                    "type": field.field_type,
                    "usage_count": field.usage_count,
                    "success_rate": round(field.success_rate, 2),
                    "created_at": field.created_at.isoformat() if field.created_at else None
                }
                for field in custom_fields
            ],
            "top_patterns": [
                {
                    "source_pattern": pattern.source_field_pattern,
                    "target_field": pattern.target_field,
                    "confidence": round(pattern.pattern_confidence, 2),
                    "success_count": pattern.success_count,
                    "failure_count": pattern.failure_count,
                    "times_applied": pattern.times_applied
                }
                for pattern in sorted(patterns, key=lambda p: p.pattern_confidence, reverse=True)[:10]
            ]
        }
    except Exception as e:
        print(f"Error getting learning statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get learning statistics: {str(e)}")

@router.post("/store-import")
async def store_import_data(
    file_data: List[Dict[str, Any]],
    metadata: Dict[str, Any],
    upload_context: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Store imported data in database for persistent access across pages.
    Replaces localStorage with proper database persistence and audit trail.
    """
    try:
        logger.info(f"Storing import data: {len(file_data)} records")
        
        # Get current context from middleware
        context = get_current_context()
        
        # Dynamically resolve demo client and engagement UUIDs
        demo_client_uuid = None
        demo_engagement_uuid = None
        demo_user_uuid = "eef6ea50-6550-4f14-be2c-081d4eb23038"  # John Doe
        
        # Resolve demo client dynamically if context is missing
        if not context.client_account_id:
            try:
                # Find demo client by is_mock=true
                demo_client_query = select(ClientAccount).where(ClientAccount.is_mock == True)
                demo_client_result = await db.execute(demo_client_query)
                demo_client = demo_client_result.scalar_one_or_none()
                
                if demo_client:
                    demo_client_uuid = str(demo_client.id)
                    logger.info(f"Dynamically resolved demo client: {demo_client.name} ({demo_client_uuid})")
                    
                    # Get first engagement for demo client
                    demo_engagement_query = select(Engagement).where(
                        Engagement.client_account_id == demo_client.id
                    ).limit(1)
                    demo_engagement_result = await db.execute(demo_engagement_query)
                    demo_engagement = demo_engagement_result.scalar_one_or_none()
                    
                    if demo_engagement:
                        demo_engagement_uuid = str(demo_engagement.id)
                        logger.info(f"Dynamically resolved demo engagement: {demo_engagement.name} ({demo_engagement_uuid})")
            except Exception as resolve_e:
                logger.warning(f"Failed to resolve demo client/engagement dynamically: {resolve_e}")
                # Keep None values to trigger error handling below
        
        # Use actual context or fallback to dynamically resolved demo values
        client_account_id = context.client_account_id or demo_client_uuid
        engagement_id = context.engagement_id or demo_engagement_uuid  
        user_id = context.user_id or demo_user_uuid
        
        # Verify we have required IDs
        if not client_account_id or not engagement_id:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required context: client_account_id={client_account_id}, engagement_id={engagement_id}"
            )
        
        # Simplified session management - don't fail the whole operation if session fails
        session_id = None
        try:
            if SESSION_MANAGEMENT_AVAILABLE:
                session_service = create_session_management_service(db)
                session = await session_service.get_or_create_active_session(
                    client_account_id=client_account_id,
                    engagement_id=engagement_id,
                    auto_create=True
                )
                session_id = str(session.id) if session else None
                logger.info(f"Using session {session_id} for data import from store-import")
        except Exception as session_e:
            logger.warning(f"Session management failed, continuing without session: {session_e}")
            # Continue without session - this is not critical for data storage
        
        # Create import session record with proper context and session
        import_session = DataImport(
            import_name=metadata.get("filename", "Unknown Import"),
            import_type=upload_context.get("intended_type", "unknown"),
            description=f"Data import session from {metadata.get('filename')}",
            source_filename=metadata.get("filename", "unknown.csv"),
            file_size_bytes=metadata.get("size", 0),
            file_type=metadata.get("type", "text/csv"),
            file_hash=hashlib.sha256(str(file_data).encode()).hexdigest()[:32],
            status=ImportStatus.PROCESSED,
            total_records=len(file_data),
            processed_records=len(file_data),
            failed_records=0,
            import_config={
                "upload_context": upload_context,
                "analysis_timestamp": datetime.utcnow().isoformat()
            },
            # Use context values with fallbacks for demo/development
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            imported_by=user_id,
            session_id=session_id,  # Link to session if available
            completed_at=datetime.utcnow()
        )
        
        db.add(import_session)
        await db.flush()  # Get the ID using async flush
        
        # Store raw import records
        for index, record in enumerate(file_data):
            raw_record = RawImportRecord(
                data_import_id=import_session.id,
                row_number=index + 1,
                record_id=record.get("hostname") or record.get("asset_name") or f"row_{index + 1}",
                raw_data=record,
                is_processed=True,
                is_valid=True,
                created_at=datetime.utcnow()
            )
            db.add(raw_record)
        
        await db.commit()
        
        logger.info(f"Successfully stored import session {import_session.id} with {len(file_data)} records")
        
        return {
            "success": True,
            "import_session_id": str(import_session.id),
            "records_stored": len(file_data),
            "message": f"Successfully stored {len(file_data)} records with full audit trail"
        }
        
    except Exception as e:
        logger.error(f"Failed to store import data: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to store import data: {str(e)}")

@router.get("/latest-import")
async def get_latest_import(db: AsyncSession = Depends(get_db)):
    """
    Get the most recent import data for attribute mapping.
    Replaces localStorage dependency with database persistence.
    """
    try:
        # Find the most recent completed import using async session pattern
        latest_query = select(DataImport).where(
            DataImport.status == ImportStatus.PROCESSED
        ).order_by(desc(DataImport.completed_at)).limit(1)
        
        result = await db.execute(latest_query)
        latest_import = result.scalar_one_or_none()
        
        if not latest_import:
            return {
                "success": False,
                "message": "No import data found",
                "data": []
            }
        
        # Get the raw records using async session pattern
        records_query = select(RawImportRecord).where(
            RawImportRecord.data_import_id == latest_import.id
        ).order_by(RawImportRecord.row_number)
        
        records_result = await db.execute(records_query)
        raw_records = records_result.scalars().all()
        
        # Extract the data
        imported_data = [record.raw_data for record in raw_records]
        
        logger.info(f"Retrieved {len(imported_data)} records from import session {latest_import.id}")
        
        return {
            "success": True,
            "import_session_id": str(latest_import.id),
            "import_metadata": {
                "filename": latest_import.source_filename,
                "import_type": latest_import.import_type,
                "imported_at": latest_import.completed_at.isoformat() if latest_import.completed_at else None,
                "total_records": latest_import.total_records
            },
            "data": imported_data,
            "message": f"Retrieved {len(imported_data)} records from latest import"
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve import data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve import data: {str(e)}")

@router.get("/import/{import_session_id}")
async def get_import_by_id(
    import_session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get specific import data by session ID.
    Enables linking and retrieving specific import sessions.
    """
    try:
        # Find the import session using async session pattern
        session_query = select(DataImport).where(
            DataImport.id == import_session_id
        )
        
        result = await db.execute(session_query)
        import_session = result.scalar_one_or_none()
        
        if not import_session:
            raise HTTPException(status_code=404, detail="Import session not found")
        
        # Get the raw records using async session pattern
        records_query = select(RawImportRecord).where(
            RawImportRecord.data_import_id == import_session.id
        ).order_by(RawImportRecord.row_number)
        
        records_result = await db.execute(records_query)
        raw_records = records_result.scalars().all()
        
        # Extract the data
        imported_data = [record.raw_data for record in raw_records]
        
        return {
            "success": True,
            "import_session_id": str(import_session.id),
            "import_metadata": {
                "filename": import_session.source_filename,
                "import_type": import_session.import_type,
                "imported_at": import_session.completed_at.isoformat() if import_session.completed_at else None,
                "total_records": import_session.total_records,
                "status": import_session.status
            },
            "data": imported_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve import {import_session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve import: {str(e)}")

@router.get("/imports")
async def list_imports(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    List recent import sessions for traceability and audit.
    """
    try:
        # Use async session pattern for querying imports
        imports_query = select(DataImport).order_by(
            desc(DataImport.created_at)
        ).limit(limit)
        
        result = await db.execute(imports_query)
        imports = result.scalars().all()
        
        import_list = []
        for imp in imports:
            import_list.append({
                "id": str(imp.id),
                "filename": imp.source_filename,
                "import_type": imp.import_type,
                "status": imp.status,
                "total_records": imp.total_records,
                "imported_at": imp.created_at.isoformat() if imp.created_at else None,
                "completed_at": imp.completed_at.isoformat() if imp.completed_at else None
            })
        
        return {
            "success": True,
            "imports": import_list,
            "total": len(import_list)
        }
        
    except Exception as e:
        logger.error(f"Failed to list imports: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list imports: {str(e)}")

@router.post("/process-raw-to-assets")
async def process_raw_to_assets(
    import_session_id: str = None,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    CrewAI Flow endpoint to process raw import records into assets using agentic intelligence.
    Now uses proper CrewAI Flow state management pattern for complete application and server classification.
    """
    try:
        logger.info(f"🚀 Starting enhanced CrewAI Flow processing with state management for session: {import_session_id}")
        
        # Use the new CrewAI Flow Data Processing Service with proper state management
        try:
            from app.services.crewai_flow_data_processing import CrewAIFlowDataProcessingService
            flow_service = CrewAIFlowDataProcessingService()
            
            # Process using CrewAI Flow with state management
            result = await flow_service.process_import_session(
                import_session_id=import_session_id,
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id,
                user_id=context.user_id
            )
            
            # Enhanced response with detailed classification results
            if result.get("status") == "success":
                logger.info(f"✅ CrewAI Flow completed successfully!")
                logger.info(f"   📊 Processing Status: {result.get('processing_status')}")
                logger.info(f"   📱 Applications: {result.get('classification_results', {}).get('applications', 0)}")
                logger.info(f"   🖥️  Servers: {result.get('classification_results', {}).get('servers', 0)}")
                logger.info(f"   🗄️  Databases: {result.get('classification_results', {}).get('databases', 0)}")
                logger.info(f"   🔗 Dependencies: {result.get('classification_results', {}).get('dependencies', 0)}")
                
                return {
                    "status": "success",
                    "message": f"CrewAI Flow successfully processed {result.get('total_processed', 0)} assets with intelligent classification",
                    "processed_count": result.get("total_processed", 0),
                    "flow_id": result.get("flow_id"),
                    "processing_status": result.get("processing_status"),
                    "progress_percentage": result.get("progress_percentage", 100),
                    "agentic_intelligence": {
                        "crewai_flow_active": result.get("crewai_flow_used", False),
                        "state_management": True,
                        "intelligent_classification": True,
                        "asset_breakdown": result.get("classification_results", {}),
                        "field_mappings_applied": len(result.get("field_mappings", {})),
                        "processing_method": "crewai_flow_with_state_management"
                    },
                    "classification_results": result.get("classification_results", {}),
                    "processed_asset_ids": result.get("processed_asset_ids", []),
                    "processing_errors": result.get("processing_errors", []),
                    "import_session_id": import_session_id,
                    "completed_at": result.get("completed_at")
                }
            else:
                logger.warning(f"CrewAI Flow returned error, falling back: {result.get('error', 'Unknown error')}")
                return await _fallback_raw_to_assets_processing(import_session_id, db, context)
                
        except ImportError as e:
            logger.warning(f"CrewAI Flow Data Processing service not available: {e}")
            return await _fallback_raw_to_assets_processing(import_session_id, db, context)
        
    except Exception as e:
        logger.error(f"Error in enhanced CrewAI Flow processing: {e}")
        # Fallback to non-agentic processing
        return await _fallback_raw_to_assets_processing(import_session_id, db, context)


async def _process_single_raw_record_agentic(
    record: RawImportRecord,
    field_mappings: Dict[str, str],
    asset_classifications: List[Dict[str, Any]],
    context: RequestContext
) -> Dict[str, Any]:
    """Process a single raw record using agentic CrewAI intelligence."""
    
    raw_data = record.raw_data
    
    # Apply agentic field mappings
    mapped_data = {}
    for source_field, canonical_field in field_mappings.items():
        if source_field in raw_data:
            mapped_data[canonical_field.lower().replace(" ", "_")] = raw_data[source_field]
    
    # Find agentic asset classification for this record
    asset_classification = None
    for classification in asset_classifications:
        # Match by hostname, name, or other identifier
        if (classification.get("hostname") == raw_data.get("hostname") or
            classification.get("name") == raw_data.get("name") or
            classification.get("asset_name") == raw_data.get("asset_name")):
            asset_classification = classification
            break
    
    # Build CMDBAsset data using agentic intelligence
    asset_data = {
        "id": uuid.uuid4(),
        "client_account_id": context.client_account_id,
        "engagement_id": context.engagement_id,
        
        # Core identification using agentic field mapping
        "name": (mapped_data.get("asset_name") or 
                mapped_data.get("hostname") or 
                raw_data.get("hostname") or 
                raw_data.get("name") or 
                f"Asset_{record.row_number}"),
        "hostname": mapped_data.get("hostname") or raw_data.get("hostname"),
        "asset_type": _determine_asset_type_agentic(raw_data, asset_classification),
        
        # Infrastructure details from agentic mapping
        "ip_address": mapped_data.get("ip_address") or raw_data.get("ip_address"),
        "operating_system": mapped_data.get("operating_system") or raw_data.get("os"),
        "environment": mapped_data.get("environment") or raw_data.get("environment"),
        
        # Business information from agentic analysis
        "business_owner": mapped_data.get("business_owner") or raw_data.get("business_owner"),
        "department": mapped_data.get("department") or raw_data.get("department"),
        
        # Migration assessment from agentic intelligence
        "sixr_ready": asset_classification.get("sixr_readiness") if asset_classification else "Pending Analysis",
        "migration_complexity": asset_classification.get("migration_complexity") if asset_classification else "Unknown",
        
        # Source and processing metadata
        "discovery_source": "agentic_cmdb_import",
        "discovery_method": "crewai_flow",
        "discovery_timestamp": datetime.utcnow(),
        "imported_by": context.user_id,
        "imported_at": datetime.utcnow(),
        "source_filename": f"import_session_{record.data_import_id}",
        "raw_data": raw_data,
        "field_mappings_used": field_mappings,
        
        # Audit
        "created_at": datetime.utcnow(),
        "created_by": context.user_id,
        "is_mock": False
    }
    
    return asset_data


def _determine_asset_type_agentic(raw_data: Dict[str, Any], asset_classification: Dict[str, Any]) -> str:
    """Determine asset type using agentic intelligence with enhanced CITYPE field reading."""
    
    # First, use agentic classification if available
    if asset_classification and asset_classification.get("asset_type"):
        agentic_type = asset_classification["asset_type"].lower()
        if agentic_type in ["server", "application", "database", "network_device", "storage_device"]:
            return agentic_type
    
    # Enhanced raw data analysis - check for CITYPE field first (most reliable)
    citype_variations = ["CITYPE", "citype", "CI_TYPE", "ci_type", "CIType"]
    raw_type = ""
    
    # Check for CITYPE field variations
    for field_name in citype_variations:
        if field_name in raw_data and raw_data[field_name]:
            raw_type = str(raw_data[field_name]).lower()
            break
    
    # If no CITYPE found, check other type fields
    if not raw_type:
        raw_type = (raw_data.get("asset_type") or 
                    raw_data.get("type") or 
                    raw_data.get("Type") or 
                    raw_data.get("TYPE") or "").lower()
    
    # Enhanced mapping with exact CITYPE matches first
    if "application" in raw_type:
        return "application"
    elif "server" in raw_type:
        return "server" 
    elif "database" in raw_type:
        return "database"
    elif any(term in raw_type for term in ["network", "switch", "router", "firewall"]):
        return "network_device"
    elif any(term in raw_type for term in ["storage", "san", "nas", "disk"]):
        return "storage_device"
    # Pattern-based fallback for unclear types
    elif any(term in raw_type for term in ["app", "software", "portal", "service"]):
        return "application" 
    elif any(term in raw_type for term in ["srv", "vm", "virtual", "host"]):
        return "server"
    elif any(term in raw_type for term in ["db", "sql", "oracle", "mysql", "postgres"]):
        return "database"
    else:
        # Check CIID patterns as final fallback
        ciid = raw_data.get("CIID", raw_data.get("ciid", raw_data.get("CI_ID", "")))
        if ciid:
            ciid_lower = str(ciid).lower()
            if ciid_lower.startswith("app"):
                return "application"
            elif ciid_lower.startswith("srv"):
                return "server"
            elif ciid_lower.startswith("db"):
                return "database"
        
        return "server"  # Default fallback


async def _fallback_raw_to_assets_processing(
    import_session_id: str,
    db: AsyncSession,
    context: RequestContext
) -> Dict[str, Any]:
    """Fallback processing when CrewAI Flow is not available."""
    
    logger.info("🔄 Using fallback processing (non-agentic) for raw import records")
    
    # Get unprocessed raw records
    if import_session_id:
        raw_records_query = await db.execute(
            select(RawImportRecord).where(
                and_(
                    RawImportRecord.data_import_id == import_session_id,
                    RawImportRecord.asset_id.is_(None)
                )
            )
        )
    else:
        raw_records_query = await db.execute(
            select(RawImportRecord).where(
                RawImportRecord.asset_id.is_(None)
            )
        )
    
    raw_records = raw_records_query.scalars().all()
    
    if not raw_records:
        return {
            "status": "no_data",
            "message": "No unprocessed raw import records found",
            "processed_count": 0
        }
    
    # Simple processing without agentic intelligence
    processed_count = 0
    for record in raw_records:
        try:
            raw_data = record.raw_data
            
            # Basic field mapping
            asset_data = {
                "id": uuid.uuid4(),
                "client_account_id": context.client_account_id,
                "engagement_id": context.engagement_id,
                "name": (raw_data.get("hostname") or 
                        raw_data.get("name") or 
                        raw_data.get("asset_name") or
                        f"Asset_{record.row_number}"),
                "hostname": raw_data.get("hostname"),
                "asset_type": _determine_asset_type_agentic(raw_data, None),
                "ip_address": raw_data.get("ip_address"),
                "operating_system": raw_data.get("os") or raw_data.get("operating_system"),
                "environment": raw_data.get("environment"),
                "business_owner": raw_data.get("business_owner"),
                "department": raw_data.get("department"),
                "discovery_source": "fallback_cmdb_import",
                "discovery_method": "basic_mapping",
                "discovery_timestamp": datetime.utcnow(),
                "imported_by": context.user_id,
                "imported_at": datetime.utcnow(),
                "source_filename": f"import_session_{record.data_import_id}",
                "raw_data": raw_data,
                "created_at": datetime.utcnow(),
                "created_by": context.user_id,
                "is_mock": False
            }
            
            # Create Asset
            asset = Asset(**asset_data)
            db.add(asset)
            await db.flush()
            
            # Update raw record
            record.asset_id = asset.id
            record.is_processed = True
            record.processed_at = datetime.utcnow()
            record.processing_notes = "Processed by fallback method (non-agentic)"
            
            processed_count += 1
            
        except Exception as e:
            logger.error(f"Error in fallback processing for record {record.id}: {e}")
            continue
    
    await db.commit()
    
    return {
        "status": "success",
        "message": f"Fallback processing completed: {processed_count} assets created",
        "processed_count": processed_count,
        "total_raw_records": len(raw_records),
        "agentic_intelligence": False,
        "import_session_id": import_session_id
    } 