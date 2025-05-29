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
            
            # Prepare data for analysis
            cmdb_data = {
                "filename": request.filename,
                "structure": structure_analysis,
                "sample_data": df.head(10).to_dict('records'),
                "total_rows": len(df),
                "columns": df.columns.tolist()
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
                f"CMDB analysis completed for {request.filename}",
                {"data_quality_score": data_quality.score, "asset_count": coverage.applications + coverage.servers + coverage.databases}
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
                    f"Processing asset {index + 1}/{total_rows} ({progress}%)",
                    progress_percentage=progress
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
            f"Successfully processed {len(processed_assets)} assets",
            {"processed_count": len(processed_assets), "total_input": total_rows}
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
    dq_data = crewai_result.get("data_quality", {})
    
    issues = []
    recommendations = []
    
    # Check for common data quality issues
    null_percentage = df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100
    if null_percentage > 20:
        issues.append(f"High percentage of missing data ({null_percentage:.1f}%)")
        recommendations.append("Review data collection processes to reduce missing values")
    
    return DataQualityResult(
        score=int(dq_data.get("score", 75)),
        issues=issues + dq_data.get("issues", []),
        recommendations=recommendations + dq_data.get("recommendations", [])
    )

def _extract_coverage(crewai_result: Dict, df: pd.DataFrame) -> AssetCoverage:
    """Extract asset coverage from CrewAI result."""
    coverage_data = crewai_result.get("coverage", {})
    
    return AssetCoverage(
        applications=coverage_data.get("applications", 0),
        servers=coverage_data.get("servers", 0), 
        databases=coverage_data.get("databases", 0),
        dependencies=coverage_data.get("dependencies", 0)
    )

def _identify_missing_fields(crewai_result: Dict, df: pd.DataFrame) -> List[str]:
    """Identify missing required fields."""
    required_fields = ["hostname", "asset_type", "environment", "department"]
    missing = [field for field in required_fields if field not in df.columns]
    return missing + crewai_result.get("missing_fields", [])

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
    """Process a single asset with enhanced AI capabilities."""
    
    # Extract basic information
    asset_id = str(uuid.uuid4())
    hostname = get_field_value(row, ['hostname', 'host', 'server_name', 'machine_name'])
    asset_type = standardize_asset_type(get_field_value(row, ['asset_type', 'type', 'category']))
    
    # Build processed asset
    processed_asset = {
        "id": asset_id,
        "hostname": hostname,
        "asset_type": asset_type,
        "environment": get_field_value(row, ['environment', 'env', 'stage']),
        "department": get_field_value(row, ['department', 'dept', 'business_unit']),
        "operating_system": get_field_value(row, ['os', 'operating_system', 'platform']),
        "ip_address": get_field_value(row, ['ip', 'ip_address', 'host_ip']),
        "application_name": get_field_value(row, ['application', 'app_name', 'service']),
        "technology_stack": get_tech_stack(row),
        "criticality": get_field_value(row, ['criticality', 'priority', 'importance']),
        "dependencies": get_field_value(row, ['dependencies', 'dependent_services']),
        "six_r_readiness": assess_6r_readiness(row),
        "migration_complexity": assess_migration_complexity(row),
        "discovery_source": "cmdb_import",
        "processed_timestamp": pd.Timestamp.now().isoformat(),
        "raw_data": clean_for_json_serialization(row.to_dict())
    }
    
    return clean_for_json_serialization(processed_asset) 