"""
CMDB Analysis and Processing Endpoints.
Handles AI-powered CMDB data validation and processing.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException
import pandas as pd

from app.services.agent_monitor import agent_monitor, TaskStatus
from app.api.v1.discovery.models import (
    CMDBAnalysisRequest,
    CMDBProcessingRequest, 
    CMDBFeedbackRequest,
    CMDBAnalysisResponse,
    DataQualityResult,
    AssetCoverage
)
from app.api.v1.discovery.processor import CMDBDataProcessor
from app.api.v1.discovery.utils import (
    standardize_asset_type,
    get_field_value,
    get_tech_stack,
    assess_6r_readiness,
    assess_migration_complexity
)
from app.api.v1.discovery.persistence import (
    processed_assets_store,
    backup_processed_assets,
    save_to_file,
    load_from_file
)
from app.api.v1.discovery.serialization import clean_for_json_serialization
from app.services.tools.field_mapping_tool import field_mapping_tool

logger = logging.getLogger(__name__)

router = APIRouter()
processor = CMDBDataProcessor()

# Initialize feedback store
feedback_store = load_from_file("feedback_store", [])

@router.post("/analyze-cmdb", response_model=CMDBAnalysisResponse)
async def analyze_cmdb_data(request: CMDBAnalysisRequest):
    """
    Analyze CMDB data using CrewAI agents with enhanced monitoring.
    """
    try:
        logger.info(f"Starting CMDB analysis for file: {request.filename}")
        
        # Parse the file content first
        df = processor.parse_file_content(request.content, request.fileType)
        
        if len(df) == 0:
            raise HTTPException(status_code=400, detail="No data found in the uploaded file")
        
        # Start monitoring the analysis task
        task_id = f"cmdb_analysis_{str(uuid.uuid4())[:8]}"
        task_exec = agent_monitor.start_task(
            task_id, 
            "CMDB_Analysis_Crew", 
            f"Analyzing CMDB data from {request.filename}"
        )
        
        try:
            # Update task status
            agent_monitor.update_task_status(task_id, TaskStatus.RUNNING, "Initializing CMDB analysis")
            
            # Analyze data structure
            structure_analysis = processor.analyze_data_structure(df)
            
            # Use agentic field mapping to analyze columns
            columns = df.columns.tolist()
            sample_rows = []
            for _, row in df.head(10).iterrows():
                sample_row = [str(row[col]) if pd.notna(row[col]) else '' for col in columns]
                sample_rows.append(sample_row)
            
            # Get intelligent field mapping analysis
            agent_monitor.update_task_status(task_id, TaskStatus.RUNNING, "Analyzing field patterns with AI")
            mapping_analysis = field_mapping_tool.analyze_data_patterns(columns, sample_rows, "server")
            
            # Prepare enhanced data for analysis
            cmdb_data = {
                "filename": request.filename,
                "structure": structure_analysis,
                "sample_data": df.head(10).to_dict('records'),
                "total_rows": len(df),
                "columns": columns,
                "field_mapping_analysis": mapping_analysis
            }
            
            # Record thinking phase
            agent_monitor.record_thinking_phase(task_id, "Preparing data for AI analysis")
            
            # Run CrewAI analysis (this is the core agentic intelligence)
            agent_monitor.update_task_status(task_id, TaskStatus.WAITING_LLM, "Starting AI analysis")
            try:
                crewai_result = await processor.crewai_service.analyze_cmdb_data(cmdb_data)
                logger.info(f"CrewAI analysis completed: {crewai_result}")
            except Exception as e:
                logger.warning(f"CrewAI analysis failed: {e}, continuing with enhanced fallback analysis")
                
                # Enhanced fallback analysis with structured approach
                agent_monitor.update_task_status(task_id, TaskStatus.RUNNING, "Using fallback analysis method")
                crewai_result = _perform_fallback_analysis(df, structure_analysis)
            
            # Process the analysis result
            agent_monitor.update_task_status(task_id, TaskStatus.RUNNING, "Processing analysis results")
            
            # Extract data quality assessment
            data_quality = _extract_data_quality(crewai_result, df)
            
            # Extract coverage information  
            coverage = _extract_coverage(crewai_result, df)
            
            # Identify missing fields and processing requirements
            missing_fields = _identify_missing_fields(crewai_result, df)
            required_processing = _identify_processing_requirements(crewai_result, df)
            
            # Determine if ready for import
            ready_for_import = _assess_import_readiness(data_quality, coverage, missing_fields)
            
            # Generate preview data
            preview_data = _generate_preview_data(df, structure_analysis)
            
            # Complete the task
            agent_monitor.complete_task(
                task_id, 
                f"CMDB analysis completed for {request.filename} - Quality: {data_quality.score}%, Assets: {coverage.applications + coverage.servers + coverage.databases}"
            )
            
            return CMDBAnalysisResponse(
                status="success",
                dataQuality=data_quality,
                coverage=coverage,
                missingFields=missing_fields,
                requiredProcessing=required_processing,
                readyForImport=ready_for_import,
                preview=preview_data
            )
            
        except Exception as e:
            agent_monitor.fail_task(task_id, f"Analysis failed: {str(e)}")
            raise
            
    except Exception as e:
        logger.error(f"CMDB analysis error: {e}")
        if "HTTPException" in str(type(e)):
            raise
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/process-cmdb")
async def process_cmdb_data(request: CMDBProcessingRequest):
    """
    Process and validate CMDB data for import with enhanced AI-driven processing.
    """
    global processed_assets_store
    
    try:
        logger.info(f"Processing CMDB data from {request.filename}")
        
        # Start monitoring
        task_id = f"cmdb_processing_{str(uuid.uuid4())[:8]}"
        task_exec = agent_monitor.start_task(
            task_id,
            "CMDB_Processing_Crew", 
            f"Processing CMDB data from {request.filename}"
        )
        
        # Convert to DataFrame for processing
        df = pd.DataFrame(request.data)
        
        # Update task status
        agent_monitor.update_task_status(task_id, TaskStatus.RUNNING, "Starting data processing")
        
        # Process each row with enhanced AI capabilities
        processed_assets = []
        total_rows = len(df)
        
        for index, row in df.iterrows():
            try:
                # Update progress
                progress = int((index / total_rows) * 100)
                agent_monitor.update_task_status(
                    task_id, 
                    TaskStatus.RUNNING, 
                    f"Processing asset {index + 1}/{total_rows} ({progress}%)"
                )
                
                # Process individual asset
                processed_asset = await _process_single_asset(row, request.projectInfo)
                processed_assets.append(processed_asset)
                
            except Exception as e:
                logger.warning(f"Failed to process row {index}: {e}")
                continue
        
        # Store processed assets
        processed_assets_store.extend(processed_assets)
        backup_processed_assets()
        
        # Complete task
        agent_monitor.complete_task(
            task_id,
            f"Successfully processed {len(processed_assets)} assets from {total_rows} rows"
        )
        
        return {
            "status": "success",
            "message": f"Successfully processed {len(processed_assets)} assets",
            "processedCount": len(processed_assets),
            "totalAssets": len(processed_assets_store)
        }
        
    except Exception as e:
        logger.error(f"CMDB processing error: {e}")
        if task_id:
            agent_monitor.fail_task(task_id, f"Processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.post("/cmdb-feedback")
async def submit_cmdb_feedback(request: CMDBFeedbackRequest):
    """
    Submit feedback on CMDB analysis results to improve AI accuracy.
    """
    try:
        feedback_entry = {
            "id": str(uuid.uuid4()),
            "timestamp": pd.Timestamp.now().isoformat(),
            "filename": request.filename,
            "original_analysis": request.originalAnalysis,
            "user_corrections": request.userCorrections,
            "asset_type_override": request.assetTypeOverride,
            "feedback_type": "cmdb_analysis"
        }
        
        feedback_store.append(feedback_entry)
        save_to_file("feedback_store", feedback_store)
        
        logger.info(f"CMDB feedback received for {request.filename}")
        
        return {
            "status": "success",
            "message": "Feedback submitted successfully",
            "feedback_id": feedback_entry["id"]
        }
        
    except Exception as e:
        logger.error(f"Failed to submit CMDB feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")

@router.get("/cmdb-templates")
async def get_cmdb_templates():
    """
    Get CMDB template examples and field mappings.
    """
    return {
        "templates": [
            {
                "name": "Enterprise CMDB",
                "description": "Standard enterprise configuration management database format",
                "required_fields": ["hostname", "asset_type", "environment", "department"],
                "optional_fields": ["ip_address", "operating_system", "application_name", "criticality"],
                "sample_data": {
                    "hostname": "web-server-01",
                    "asset_type": "Server", 
                    "environment": "Production",
                    "department": "IT",
                    "ip_address": "10.0.1.100",
                    "operating_system": "Ubuntu 20.04",
                    "application_name": "Web Portal",
                    "criticality": "High"
                }
            },
            {
                "name": "Application Inventory",
                "description": "Application-focused inventory with technical details",
                "required_fields": ["application_name", "technology_stack", "environment"],
                "optional_fields": ["department", "criticality", "dependencies", "data_sensitivity"],
                "sample_data": {
                    "application_name": "Customer Portal",
                    "technology_stack": "Java, Spring Boot, PostgreSQL",
                    "environment": "Production",
                    "department": "Customer Service",
                    "criticality": "High",
                    "dependencies": "User Management Service, Payment Gateway",
                    "data_sensitivity": "High"
                }
            }
        ],
        "field_mappings": {
            "hostname": ["host", "server_name", "machine_name", "system_name"],
            "asset_type": ["type", "category", "classification", "asset_category"],
            "environment": ["env", "stage", "tier", "deployment_environment"],
            "department": ["dept", "business_unit", "organization", "team"],
            "application_name": ["app", "application", "service_name", "app_name"],
            "technology_stack": ["tech_stack", "technologies", "platform", "stack"],
            "criticality": ["priority", "importance", "business_criticality", "critical"]
        }
    }

# Helper functions
def _perform_fallback_analysis(df: pd.DataFrame, structure_analysis: Dict) -> Dict[str, Any]:
    """Perform fallback analysis when CrewAI is unavailable."""
    return {
        "data_quality": {
            "score": 75,
            "completeness": len([col for col in df.columns if not df[col].isna().all()]) / len(df.columns) * 100,
            "consistency": 85,
            "accuracy": 70
        },
        "coverage": {
            "applications": len(df[df['asset_type'].str.contains('app', case=False, na=False)]) if 'asset_type' in df.columns else 0,
            "servers": len(df[df['asset_type'].str.contains('server', case=False, na=False)]) if 'asset_type' in df.columns else 0,
            "databases": len(df[df['asset_type'].str.contains('database', case=False, na=False)]) if 'asset_type' in df.columns else 0
        },
        "missing_fields": [col for col in ['hostname', 'environment', 'department'] if col not in df.columns],
        "processing_requirements": ["standardize_asset_types", "validate_dependencies"]
    }

def _extract_data_quality(crewai_result: Dict, df: pd.DataFrame) -> DataQualityResult:
    """Extract data quality assessment from CrewAI result."""
    # Get score from CrewAI result (it returns data_quality_score, not data_quality.score)
    score = crewai_result.get("data_quality_score", 75)
    
    # Get issues and recommendations from CrewAI
    issues = crewai_result.get("issues", [])
    recommendations = crewai_result.get("recommendations", [])
    
    # Add additional issues based on data analysis
    null_percentage = df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100
    if null_percentage > 20:
        issues.append(f"High percentage of missing data ({null_percentage:.1f}%)")
        recommendations.append("Review data collection processes to reduce missing values")
    
    return DataQualityResult(
        score=int(score),
        issues=issues,
        recommendations=recommendations
    )

def _extract_coverage(crewai_result: Dict, df: pd.DataFrame) -> AssetCoverage:
    """Extract asset coverage from CrewAI result."""
    # CrewAI doesn't return coverage directly, calculate from detected asset type
    asset_type_detected = crewai_result.get("asset_type_detected", "mixed")
    total_rows = len(df)
    
    # If CrewAI detected a specific type, assign all rows to that type
    if asset_type_detected == "server":
        return AssetCoverage(
            applications=0,
            servers=total_rows,
            databases=0,
            dependencies=0
        )
    elif asset_type_detected == "application":
        return AssetCoverage(
            applications=total_rows,
            servers=0,
            databases=0,
            dependencies=0
        )
    elif asset_type_detected == "database":
        return AssetCoverage(
            applications=0,
            servers=0,
            databases=total_rows,
            dependencies=0
        )
    else:
        # Mixed or unknown - try to analyze columns for hints
        applications = 0
        servers = 0
        databases = 0
        
        # Look for asset type hints in column names or data
        columns_str = ' '.join(df.columns).lower()
        if 'server' in columns_str or 'host' in columns_str:
            servers = total_rows
        elif 'app' in columns_str or 'application' in columns_str:
            applications = total_rows
        elif 'db' in columns_str or 'database' in columns_str:
            databases = total_rows
        else:
            # Default to servers if AWS migration data
            servers = total_rows
        
        return AssetCoverage(
            applications=applications,
            servers=servers,
            databases=databases,
            dependencies=0
        )

def _identify_missing_fields(crewai_result: Dict, df: pd.DataFrame) -> List[str]:
    """Identify missing required fields using agentic field mapping analysis."""
    
    # Get field mapping analysis from the enhanced data
    columns = df.columns.tolist()
    sample_rows = []
    for _, row in df.head(5).iterrows():
        sample_row = [str(row[col]) if pd.notna(row[col]) else '' for col in columns]
        sample_rows.append(sample_row)
    
    # Use the field mapping tool to analyze what's actually missing
    mapping_analysis = field_mapping_tool.analyze_data_columns(columns, "server")
    
    # Get fields that are truly missing (not just differently named)
    missing_fields = mapping_analysis.get("missing_fields", [])
    
    # Also include any missing fields from CrewAI analysis that aren't resolved by field mapping
    crewai_missing = crewai_result.get("missing_fields_relevant", [])
    column_mappings = mapping_analysis.get("column_mappings", {})
    
    # Filter CrewAI missing fields - only include if not mapped by field mapping tool
    mapped_canonical_fields = set()
    for col, mapping_info in column_mappings.items():
        canonical = mapping_info.get("canonical_field")
        if canonical and mapping_info.get("confidence", 0) > 0.5:
            mapped_canonical_fields.add(canonical)
    
    for crewai_field in crewai_missing:
        if crewai_field not in mapped_canonical_fields and crewai_field not in missing_fields:
            missing_fields.append(crewai_field)
    
    return list(set(missing_fields))  # Remove duplicates

def _identify_processing_requirements(crewai_result: Dict, df: pd.DataFrame) -> List[str]:
    """Identify required processing steps."""
    requirements = []
    
    if "asset_type" in df.columns:
        unique_types = df["asset_type"].dropna().unique()
        if len(unique_types) > 10:
            requirements.append("standardize_asset_types")
    
    return requirements + crewai_result.get("processing_requirements", [])

def _assess_import_readiness(data_quality: DataQualityResult, coverage: AssetCoverage, missing_fields: List[str]) -> bool:
    """Assess if data is ready for import."""
    return (
        data_quality.score >= 70 and
        len(missing_fields) <= 2 and
        (coverage.applications + coverage.servers + coverage.databases) > 0
    )

def _generate_preview_data(df: pd.DataFrame, structure_analysis: Dict) -> List[Dict[str, Any]]:
    """Generate preview data for UI display."""
    preview = df.head(5).to_dict('records')
    return [clean_for_json_serialization(row) for row in preview]

async def _process_single_asset(row: pd.Series, project_info: Optional[Dict] = None) -> Dict[str, Any]:
    """Process a single asset using agentic field mapping intelligence."""
    
    # Get the raw data
    raw_data = row.to_dict()
    columns = list(raw_data.keys())
    
    # Use agentic field mapping to analyze and map the columns
    mapping_analysis = field_mapping_tool.analyze_data_columns(columns, "server")
    column_mappings = mapping_analysis.get("column_mappings", {})
    
    # Build the processed asset using intelligent field mapping
    asset_id = str(uuid.uuid4())
    
    # Use agentic field mapping to extract values
    def get_mapped_value(canonical_field: str, default: str = "Unknown") -> str:
        """Get value using agentic field mapping."""
        for column, mapping_info in column_mappings.items():
            if mapping_info.get("canonical_field") == canonical_field and mapping_info.get("confidence", 0) > 0.5:
                value = raw_data.get(column)
                if value and str(value).strip() and str(value).strip().lower() not in ['unknown', 'null', 'none', '']:
                    return str(value).strip()
        return default
    
    # Build processed asset using canonical field names
    processed_asset = {
        "id": asset_id,
        "hostname": get_mapped_value("Asset Name") or get_mapped_value("hostname"),
        "asset_type": standardize_asset_type(get_mapped_value("Asset Type")),
        "environment": get_mapped_value("Environment"),
        "department": get_mapped_value("Business Owner") or get_mapped_value("Department"),
        "operating_system": get_mapped_value("Operating System"),
        "ip_address": get_mapped_value("IP Address"),
        "application_name": get_mapped_value("Application Name") or get_mapped_value("Service Name"),
        "technology_stack": get_tech_stack(row),
        "criticality": get_mapped_value("Criticality"),
        "dependencies": get_mapped_value("Dependencies"),
        "six_r_readiness": assess_6r_readiness(get_mapped_value("Asset Type"), raw_data),
        "migration_complexity": assess_migration_complexity(get_mapped_value("Asset Type"), raw_data),
        "discovery_source": "cmdb_import",
        "processed_timestamp": pd.Timestamp.now().isoformat(),
        "raw_data": clean_for_json_serialization(raw_data),
        "field_mappings_used": {col: info.get("canonical_field") for col, info in column_mappings.items() if info.get("confidence", 0) > 0.5}
    }
    
    return clean_for_json_serialization(processed_asset) 