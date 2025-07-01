"""
Data Import API v3
Dedicated endpoints for data import operations
"""

import logging
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, validator
import uuid
import json

from app.core.database import get_db
from app.core.context import get_current_context, RequestContext
from app.api.v3.schemas.responses import ErrorResponse, create_error_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data-import", tags=["data-import-v3"])


# === Data Import Schemas ===

class DataImportCreate(BaseModel):
    """Request schema for creating data imports"""
    name: str = Field(..., description="Import name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Import description", max_length=1000)
    source_type: str = Field(..., description="Data source type (csv, excel, json, etc.)")
    data: List[Dict[str, Any]] = Field(..., description="Raw data to import")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    auto_create_flow: bool = Field(default=True, description="Automatically create discovery flow")


class DataImportUpdate(BaseModel):
    """Request schema for updating data imports"""
    name: Optional[str] = Field(None, description="Import name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Import description", max_length=1000)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    status: Optional[str] = Field(None, description="Import status")


class DataValidationRule(BaseModel):
    """Data validation rule definition"""
    field: str = Field(..., description="Field name to validate")
    rule_type: str = Field(..., description="Validation rule type")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Rule parameters")
    severity: str = Field(default="error", description="Validation severity (error, warning, info)")


class DataImportResponse(BaseModel):
    """Response schema for data import operations"""
    import_id: uuid.UUID
    name: str
    description: Optional[str] = None
    source_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    # Multi-tenant context
    client_account_id: uuid.UUID
    engagement_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    
    # Data statistics
    total_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    processed_records: int = 0
    
    # Quality metrics
    data_quality_score: float = Field(ge=0.0, le=1.0, default=0.0)
    validation_errors: List[Dict[str, Any]] = Field(default_factory=list)
    validation_warnings: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Field analysis
    field_analysis: Dict[str, Any] = Field(default_factory=dict)
    suggested_mappings: Dict[str, str] = Field(default_factory=dict)
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Associated flow
    flow_id: Optional[uuid.UUID] = None


class DataImportListResponse(BaseModel):
    """Response schema for data import list operations"""
    imports: List[DataImportResponse]
    total: int
    page: int = 1
    page_size: int = 20
    has_next: bool = False
    has_previous: bool = False


class DataValidationResponse(BaseModel):
    """Response schema for data validation operations"""
    is_valid: bool
    validation_score: float = Field(ge=0.0, le=1.0)
    total_records: int
    valid_records: int
    invalid_records: int
    
    # Detailed validation results
    field_validation: Dict[str, Any] = Field(default_factory=dict)
    data_type_analysis: Dict[str, Any] = Field(default_factory=dict)
    completeness_analysis: Dict[str, Any] = Field(default_factory=dict)
    
    # Issues and recommendations
    validation_errors: List[Dict[str, Any]] = Field(default_factory=list)
    validation_warnings: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class DataPreviewResponse(BaseModel):
    """Response schema for data preview operations"""
    preview_data: List[Dict[str, Any]] = Field(default_factory=list)
    total_records: int
    field_names: List[str] = Field(default_factory=list)
    field_types: Dict[str, str] = Field(default_factory=dict)
    sample_size: int
    
    # Basic statistics
    numeric_fields: List[str] = Field(default_factory=list)
    text_fields: List[str] = Field(default_factory=list)
    date_fields: List[str] = Field(default_factory=list)
    
    # Data quality indicators
    completeness_rates: Dict[str, float] = Field(default_factory=dict)
    unique_value_counts: Dict[str, int] = Field(default_factory=dict)


# === Import V3 Services ===

from app.services.v3.data_import_service import V3DataImportService
from app.services.v3.discovery_flow_service import V3DiscoveryFlowService
from app.services.v3.field_mapping_service import V3FieldMappingService
from app.api.v3.utils.backward_compatibility import field_compatibility
from app.api.v3.utils.error_handling import (
    V3ErrorHandler, handle_api_error, log_api_error, with_error_handling
)

logger.info("✅ V3 Data import services loaded")


# === Data Import Endpoints ===

@router.get("/debug/context")
async def debug_v3_context(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Debug endpoint to check V3 context"""
    return {
        "context": {
            "client_account_id": context.client_account_id,
            "engagement_id": context.engagement_id,
            "user_id": context.user_id,
            "session_id": context.session_id
        },
        "str_values": {
            "client_account_id": str(context.client_account_id),
            "engagement_id": str(context.engagement_id),
            "user_id": str(context.user_id),
            "session_id": str(context.session_id)
        }
    }

@router.post("/imports", response_model=DataImportResponse, status_code=status.HTTP_201_CREATED)
async def create_data_import(
    request: DataImportCreate,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> DataImportResponse:
    """
    Create a new data import and optionally start discovery flow
    """
    try:
        logger.info(f"📥 Creating data import: {request.name}")
        
        # Initialize V3 services
        import_service = V3DataImportService(
            db, 
            str(context.client_account_id), 
            str(context.engagement_id)
        )
        
        # Convert request data to bytes for storage
        data_json = json.dumps(request.data)
        file_data = data_json.encode('utf-8')
        
        # Create the import using V3 service
        data_import = await import_service.create_import(
            filename=f"{request.name}.{request.source_type}",
            file_data=file_data,
            source_system=request.source_type,
            import_name=request.name,
            import_type=request.source_type,
            user_id=str(context.user_id) if context.user_id and context.user_id != "anonymous" else None
        )
        
        # Process the data
        await import_service.process_import_data(
            str(data_import.id),
            request.data
        )
        
        # Generate field mappings
        if request.data:
            field_names = list(request.data[0].keys()) if request.data else []
            mapping_service = V3FieldMappingService(
                db,
                str(context.client_account_id),
                str(context.engagement_id)
            )
            await mapping_service.generate_auto_mappings(
                str(data_import.id),
                field_names
            )
        
        # Get the complete import data with mappings
        import_data = await import_service.get_import_with_flow(str(data_import.id))
        
        # Build response with backward compatibility
        response_data = {
            "import_id": data_import.id,
            "name": request.name,
            "description": request.description,
            "source_type": request.source_type,
            "status": data_import.status,
            "created_at": data_import.created_at,
            "updated_at": data_import.updated_at,
            "client_account_id": data_import.client_account_id,
            "engagement_id": data_import.engagement_id,
            "user_id": uuid.UUID(context.user_id) if context.user_id and context.user_id != "anonymous" else None,
            "total_records": data_import.total_records,
            "valid_records": data_import.total_records,  # All records valid initially
            "invalid_records": 0,
            "processed_records": data_import.processed_records,
            "data_quality_score": 0.9,  # Default good score
            "validation_errors": [],
            "validation_warnings": [],
            "field_analysis": {},  # Could be populated from data analysis
            "suggested_mappings": {},  # Populated from field mappings
            "metadata": {
                "filename": data_import.filename,
                "file_size": data_import.file_size,
                "mime_type": data_import.mime_type,
                **(request.metadata or {})
            },
            "flow_id": import_data["flow"].id if import_data["flow"] else None
        }
        
        # Apply backward compatibility to response
        response_data = field_compatibility.process_response(response_data)
        result = DataImportResponse(**response_data)
        
        logger.info(f"✅ Data import created: {data_import.id}, {len(request.data)} records")
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to create data import: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create data import: {str(e)}"
        )


@router.post("/imports/upload", response_model=DataImportResponse, status_code=status.HTTP_201_CREATED)
async def upload_data_file(
    file: UploadFile = File(..., description="Data file to upload"),
    name: Optional[str] = Query(None, description="Import name"),
    description: Optional[str] = Query(None, description="Import description"),
    auto_create_flow: bool = Query(True, description="Auto-create discovery flow"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> DataImportResponse:
    """
    Upload and import data from file (CSV, Excel, JSON)
    """
    try:
        logger.info(f"📤 Uploading data file: {file.filename}")
        
        # Read file content
        content = await file.read()
        
        # Determine file type and parse data
        filename = file.filename or "unknown"
        file_extension = filename.lower().split('.')[-1] if '.' in filename else 'unknown'
        
        data = []
        source_type = file_extension
        
        if file_extension == 'json':
            try:
                json_data = json.loads(content.decode('utf-8'))
                if isinstance(json_data, list):
                    data = json_data
                elif isinstance(json_data, dict):
                    data = [json_data]
                else:
                    raise ValueError("JSON must contain array or object")
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid JSON file: {str(e)}"
                )
        
        elif file_extension in ['csv', 'txt']:
            try:
                import csv
                import io
                
                content_str = content.decode('utf-8')
                csv_reader = csv.DictReader(io.StringIO(content_str))
                data = [row for row in csv_reader]
                
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid CSV file: {str(e)}"
                )
        
        elif file_extension in ['xlsx', 'xls']:
            try:
                import pandas as pd
                import io
                
                df = pd.read_excel(io.BytesIO(content))
                data = df.to_dict('records')
                
            except ImportError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Excel support not available. Please install pandas and openpyxl."
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid Excel file: {str(e)}"
                )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_extension}. Supported types: json, csv, xlsx, xls"
            )
        
        # Create data import request
        import_name = name or f"Import from {filename}"
        import_description = description or f"Data imported from file: {filename}"
        
        create_request = DataImportCreate(
            name=import_name,
            description=import_description,
            source_type=source_type,
            data=data,
            metadata={
                "filename": filename,
                "file_size": len(content),
                "upload_timestamp": datetime.utcnow().isoformat()
            },
            auto_create_flow=auto_create_flow
        )
        
        # Create the import
        result = await create_data_import(create_request, db, context)
        
        logger.info(f"✅ File uploaded and imported: {len(data)} records")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to upload data file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload data file: {str(e)}"
        )


@router.get("/imports/{import_id}", response_model=DataImportResponse)
async def get_data_import(
    import_id: uuid.UUID = Path(..., description="Import identifier"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> DataImportResponse:
    """
    Get data import details
    """
    request_id = str(uuid.uuid4())
    try:
        logger.info(f"🔍 Getting data import: {import_id} (request_id: {request_id})")
        
        # Use V3 service to get import data
        import_service = V3DataImportService(
            db, 
            str(context.client_account_id), 
            str(context.engagement_id)
        )
        
        import_with_flow = await import_service.get_import_with_flow(str(import_id))
        
        if not import_with_flow:
            error_handler = V3ErrorHandler()
            error_response = error_handler.handle_not_found_error(
                "Data Import", str(import_id), request_id
            )
            raise error_response.to_http_exception()
        
        data_import = import_with_flow["import"]
        flow = import_with_flow["flow"]
        mappings = import_with_flow.get("mappings", [])
        
        # Get statistics
        stats = await import_service.get_import_statistics(str(import_id))
        
        # Build response with backward compatibility
        response_data = {
            "import_id": data_import.id,
            "name": data_import.import_name,
            "description": data_import.description,
            "source_type": data_import.import_type,
            "status": data_import.status,
            "created_at": data_import.created_at,
            "updated_at": data_import.updated_at,
            "client_account_id": data_import.client_account_id,
            "engagement_id": data_import.engagement_id,
            "user_id": data_import.imported_by,
            "total_records": data_import.total_records or 0,
            "valid_records": data_import.processed_records or 0,
            "invalid_records": data_import.failed_records or 0,
            "processed_records": data_import.processed_records or 0,
            "data_quality_score": stats.get("processing_rate", 0.0),
            "validation_errors": [],
            "validation_warnings": [],
            "field_analysis": {},
            "suggested_mappings": {mapping["source_field"]: mapping["target_field"] for mapping in mappings},
            "metadata": {
                "filename": data_import.filename,
                "file_size": data_import.file_size,
                "mime_type": data_import.mime_type,
                "source_system": data_import.source_system
            },
            "flow_id": flow.id if flow else None
        }
        
        # Apply backward compatibility to response
        response_data = field_compatibility.process_response(response_data)
        result = DataImportResponse(**response_data)
        
        logger.info(f"✅ Data import retrieved: {import_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        log_api_error("get_data_import", e, request_id, {"import_id": str(import_id)})
        raise handle_api_error(e, request_id)


@router.get("/imports", response_model=DataImportListResponse)
async def list_data_imports(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    source_type: Optional[str] = Query(None, description="Filter by source type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> DataImportListResponse:
    """
    List data imports with filtering and pagination
    """
    try:
        logger.info(f"📋 Listing data imports")
        
        # Use V3 service to list imports
        import_service = V3DataImportService(
            db, 
            str(context.client_account_id), 
            str(context.engagement_id)
        )
        
        # Convert status_filter to ImportStatus enum if needed
        from app.models.data_import.enums import ImportStatus
        status_enum = None
        if status_filter:
            try:
                status_enum = ImportStatus(status_filter.lower())
            except ValueError:
                logger.warning(f"Invalid status filter: {status_filter}")
        
        # Get imports from V3 service
        all_imports = await import_service.list_imports(
            status_filter=status_enum,
            limit=page_size * 10,  # Get extra to handle pagination
            offset=(page - 1) * page_size
        )
        
        # Convert to response format
        imports = []
        for import_data in all_imports:
            try:
                import_response = DataImportResponse(
                    import_id=uuid.UUID(import_data["import_id"]),
                    name=import_data.get("import_name", import_data.get("filename", "Unknown")),
                    description="",
                    source_type=import_data.get("import_type", "unknown"),
                    status=import_data["status"],
                    created_at=datetime.fromisoformat(import_data["created_at"]) if import_data.get("created_at") else datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    client_account_id=uuid.UUID(str(context.client_account_id)),
                    engagement_id=uuid.UUID(str(context.engagement_id)),
                    total_records=import_data.get("total_records", 0),
                    valid_records=import_data.get("processed_records", 0),
                    invalid_records=0,
                    processed_records=import_data.get("processed_records", 0),
                    data_quality_score=0.9,
                    validation_errors=[],
                    validation_warnings=[],
                    field_analysis={},
                    suggested_mappings={},
                    metadata={}
                )
                imports.append(import_response)
            except Exception as e:
                logger.warning(f"⚠️ Failed to convert import data: {e}")
                continue
        
        total_imports = len(imports)
        
        # Apply pagination to results
        start_idx = 0  # Already handled by service offset
        end_idx = min(page_size, len(imports))
        paginated_imports = imports[start_idx:end_idx]
        
        # Calculate pagination info
        has_next = len(imports) >= page_size
        has_previous = page > 1
        
        result = DataImportListResponse(
            imports=paginated_imports,
            total=total_imports,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )
        
        logger.info(f"✅ Import list retrieved: {len(paginated_imports)} items")
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to list data imports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list data imports: {str(e)}"
        )


@router.post("/imports/{import_id}/validate", response_model=DataValidationResponse)
async def validate_data_import(
    import_id: uuid.UUID = Path(..., description="Import identifier"),
    validation_rules: Optional[List[DataValidationRule]] = None,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> DataValidationResponse:
    """
    Validate data import against rules
    """
    try:
        logger.info(f"✅ Validating data import: {import_id}")
        
        # Get import data first
        import_data = await get_data_import(import_id, db, context)
        
        # Initialize validation results
        validation_errors = []
        validation_warnings = []
        field_validation = {}
        data_type_analysis = {}
        completeness_analysis = {}
        
        # Basic validation metrics
        total_records = import_data.total_records
        valid_records = import_data.valid_records
        invalid_records = import_data.invalid_records
        
        # Field-level validation
        for field_name, field_info in import_data.field_analysis.items():
            completeness_rate = field_info.get("completeness_rate", 0.0)
            data_types = field_info.get("data_types", [])
            unique_values = field_info.get("unique_values", 0)
            
            # Completeness analysis
            completeness_analysis[field_name] = {
                "completeness_rate": completeness_rate,
                "missing_count": int(total_records * (1 - completeness_rate)),
                "status": "good" if completeness_rate >= 0.8 else "warning" if completeness_rate >= 0.5 else "poor"
            }
            
            # Data type analysis
            data_type_analysis[field_name] = {
                "detected_types": data_types,
                "type_consistency": "consistent" if len(data_types) <= 1 else "mixed",
                "unique_value_count": unique_values,
                "cardinality": "high" if unique_values > total_records * 0.8 else "medium" if unique_values > total_records * 0.1 else "low"
            }
            
            # Field validation results
            field_validation[field_name] = {
                "is_valid": completeness_rate >= 0.5 and len(data_types) <= 2,
                "score": min(1.0, completeness_rate + (0.2 if len(data_types) <= 1 else 0)),
                "issues": []
            }
            
            # Generate validation issues
            if completeness_rate < 0.5:
                validation_errors.append({
                    "type": "LOW_COMPLETENESS",
                    "field": field_name,
                    "message": f"Field '{field_name}' has low completeness rate ({completeness_rate:.1%})",
                    "severity": "error"
                })
                field_validation[field_name]["issues"].append("Low completeness rate")
            
            if len(data_types) > 2:
                validation_warnings.append({
                    "type": "MIXED_DATA_TYPES",
                    "field": field_name,
                    "message": f"Field '{field_name}' has mixed data types: {data_types}",
                    "severity": "warning"
                })
                field_validation[field_name]["issues"].append("Mixed data types")
        
        # Apply custom validation rules if provided
        if validation_rules:
            for rule in validation_rules:
                # Implement custom rule validation logic here
                # This is a placeholder for extensible validation
                pass
        
        # Calculate overall validation score
        field_scores = [info["score"] for info in field_validation.values()]
        validation_score = sum(field_scores) / max(len(field_scores), 1) if field_scores else 0.0
        
        # Adjust score based on errors and warnings
        error_penalty = len(validation_errors) * 0.1
        warning_penalty = len(validation_warnings) * 0.05
        validation_score = max(0.0, validation_score - error_penalty - warning_penalty)
        
        is_valid = len(validation_errors) == 0 and validation_score >= 0.7
        
        # Generate recommendations
        recommendations = []
        if not is_valid:
            recommendations.append("Address validation errors before proceeding with discovery flow")
        if len(validation_warnings) > 0:
            recommendations.append("Review validation warnings to improve data quality")
        if validation_score < 0.8:
            recommendations.append("Consider data cleansing to improve overall quality")
        
        result = DataValidationResponse(
            is_valid=is_valid,
            validation_score=validation_score,
            total_records=total_records,
            valid_records=valid_records,
            invalid_records=invalid_records,
            field_validation=field_validation,
            data_type_analysis=data_type_analysis,
            completeness_analysis=completeness_analysis,
            validation_errors=validation_errors,
            validation_warnings=validation_warnings,
            recommendations=recommendations
        )
        
        logger.info(f"✅ Validation completed: score={validation_score:.2f}, valid={is_valid}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to validate data import: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate data import: {str(e)}"
        )


@router.get("/imports/{import_id}/preview", response_model=DataPreviewResponse)
async def preview_data_import(
    import_id: uuid.UUID = Path(..., description="Import identifier"),
    sample_size: int = Query(10, ge=1, le=100, description="Number of records to preview"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> DataPreviewResponse:
    """
    Preview data import with sample records
    """
    try:
        logger.info(f"👀 Previewing data import: {import_id}")
        
        # Get full import data (this would be optimized in production to avoid loading all data)
        import_data = await get_data_import(import_id, db, context)
        
        # Get sample data from V3 service
        preview_data = []
        try:
            # For now, return empty preview data - this would be implemented
            # to get actual raw records from the database
            preview_data = []
            logger.info("Preview data functionality to be implemented")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to get raw data from service: {e}")
        
        # Extract field information from sample
        field_names = []
        field_types = {}
        numeric_fields = []
        text_fields = []
        date_fields = []
        completeness_rates = {}
        unique_value_counts = {}
        
        if preview_data:
            # Get all field names from first record
            field_names = list(preview_data[0].keys()) if preview_data else []
            
            # Analyze field types and statistics
            for field_name in field_names:
                field_values = [record.get(field_name) for record in preview_data if record.get(field_name) is not None]
                
                if field_values:
                    # Determine field type
                    sample_value = field_values[0]
                    if isinstance(sample_value, (int, float)):
                        field_types[field_name] = "numeric"
                        numeric_fields.append(field_name)
                    elif isinstance(sample_value, str):
                        # Check if it could be a date
                        if any(keyword in field_name.lower() for keyword in ['date', 'time', 'created', 'updated']):
                            field_types[field_name] = "date"
                            date_fields.append(field_name)
                        else:
                            field_types[field_name] = "text"
                            text_fields.append(field_name)
                    else:
                        field_types[field_name] = "other"
                        text_fields.append(field_name)
                    
                    # Calculate completeness rate for sample
                    non_null_count = len(field_values)
                    completeness_rates[field_name] = non_null_count / len(preview_data)
                    
                    # Count unique values in sample
                    unique_value_counts[field_name] = len(set(str(value) for value in field_values))
                else:
                    field_types[field_name] = "unknown"
                    completeness_rates[field_name] = 0.0
                    unique_value_counts[field_name] = 0
        
        result = DataPreviewResponse(
            preview_data=preview_data,
            total_records=import_data.total_records,
            field_names=field_names,
            field_types=field_types,
            sample_size=len(preview_data),
            numeric_fields=numeric_fields,
            text_fields=text_fields,
            date_fields=date_fields,
            completeness_rates=completeness_rates,
            unique_value_counts=unique_value_counts
        )
        
        logger.info(f"✅ Data preview generated: {len(preview_data)} records, {len(field_names)} fields")
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to preview data import: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview data import: {str(e)}"
        )


@router.delete("/imports/{import_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_data_import(
    import_id: uuid.UUID = Path(..., description="Import identifier"),
    cascade: bool = Query(False, description="Also delete associated discovery flow"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    Delete data import and optionally associated flow
    """
    try:
        logger.info(f"🗑️ Deleting data import: {import_id}, cascade: {cascade}")
        
        # Use V3 service to delete import
        import_service = V3DataImportService(
            db, 
            str(context.client_account_id), 
            str(context.engagement_id)
        )
        
        # Get import data to check for associated flow
        try:
            import_with_flow = await import_service.get_import_with_flow(str(import_id))
            
            if import_with_flow and cascade and import_with_flow.get("flow"):
                # Delete associated flow if cascade is requested
                try:
                    flow_service = V3DiscoveryFlowService(
                        db,
                        str(context.client_account_id),
                        str(context.engagement_id)
                    )
                    await flow_service.delete_flow(str(import_with_flow["flow"].id))
                    logger.info(f"✅ Associated flow deleted: {import_with_flow['flow'].id}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to delete associated flow: {e}")
                    
        except Exception as e:
            logger.warning(f"⚠️ Failed to get import data: {e}")
        
        # Delete import data using V3 service
        success = await import_service.delete_import(str(import_id), cascade=cascade)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Data import not found: {import_id}"
            )
        
        logger.info(f"✅ Data import deleted: {import_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete data import: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete data import: {str(e)}"
        )


@router.get("/field-mappings", response_model=Dict[str, Any])
async def get_field_mappings():
    """
    Get field mapping information for backward compatibility
    """
    from app.api.v3.utils.backward_compatibility import get_field_mapping_info
    
    return {
        "success": True,
        "data": get_field_mapping_info(),
        "message": "Field mapping information for V3 API backward compatibility"
    }