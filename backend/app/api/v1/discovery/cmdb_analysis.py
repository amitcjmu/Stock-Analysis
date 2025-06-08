"""
CMDB Analysis and Processing Endpoints.
Handles AI-powered CMDB data validation and processing.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
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
from app.core.database import get_db
from app.services.crewai_flow_service import crewai_flow_service
from app.core.context import RequestContext, get_current_context
from app.services.agent_ui_bridge import agent_ui_bridge
from app.schemas.auth_schemas import UserRoleInfo
from app.api.v1.auth.auth_utils import get_current_active_user, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()
processor = CMDBDataProcessor(crewai_service=crewai_flow_service)

# Initialize feedback store
feedback_store = load_from_file("feedback_store", [])

@router.post("/analyze-cmdb", response_model=CMDBAnalysisResponse)
async def analyze_cmdb_data(
    request: CMDBAnalysisRequest,
    context: RequestContext = Depends(get_current_context)
):
    """
    Analyze data intelligently using CrewAI agents with enhanced monitoring.
    Handles both structured data (CSV, JSON) and unstructured content (PDF, docs).
    """
    try:
        logger.info(f"Starting intelligent analysis for file: {request.filename}")
        
        # Parse the file content intelligently
        df, parsing_info = processor.parse_file_content(
            request.content, 
            request.fileType, 
            request.filename
        )
        
        # Start monitoring the analysis task
        task_id = f"intelligent_analysis_{str(uuid.uuid4())[:8]}"
        task_exec = agent_monitor.start_task(
            task_id, 
            "Intelligent_Analysis_Crew", 
            f"Analyzing {parsing_info['type']} content from {request.filename}"
        )
        
        try:
            # Handle structured data (traditional CMDB processing)
            if df is not None and len(df) > 0:
                return await _process_structured_data(df, request, task_id, context)
            
            # Handle unstructured content (documents, PDFs, etc.)
            elif parsing_info['type'] in ['unstructured', 'unknown', 'error']:
                return await _process_unstructured_content(parsing_info, request, task_id)
            
            else:
                raise HTTPException(status_code=400, detail="No analyzable content found in the uploaded file")
                
        except Exception as e:
            agent_monitor.fail_task(task_id, f"Analysis failed: {str(e)}")
            raise
            
    except Exception as e:
        logger.error(f"Intelligent analysis error: {e}")
        if "HTTPException" in str(type(e)):
            raise
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

async def _process_structured_data(
    df: pd.DataFrame, 
    request: CMDBAnalysisRequest, 
    task_id: str,
    context: RequestContext
) -> CMDBAnalysisResponse:
    """Process structured data (CSV, JSON, Excel) using traditional CMDB analysis."""
    
    # Update task status
    agent_monitor.update_task_status(task_id, TaskStatus.RUNNING, "Analyzing structured data")
    
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
    mapping_analysis = field_mapping_tool.analyze_data_and_learn(columns, sample_rows, "server")
    
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
    agent_monitor.record_thinking_phase(task_id, "Preparing structured data for AI analysis")
    
    # Run CrewAI analysis (this is the core agentic intelligence)
    agent_monitor.update_task_status(task_id, TaskStatus.WAITING_LLM, "Starting AI analysis")
    try:
        # Correctly call the main discovery flow execution method
        crewai_result = await processor.crewai_service.execute_discovery_flow(
            flow_type="cmdb_analysis",
            cmdb_data=cmdb_data,
            page_context="data-import",
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id
        )
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
        f"Structured data analysis completed for {request.filename} - Quality: {data_quality.score}%, Assets: {coverage.applications + coverage.servers + coverage.databases}"
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

async def _process_unstructured_content(parsing_info: Dict[str, Any], request: CMDBAnalysisRequest, task_id: str) -> CMDBAnalysisResponse:
    """Process unstructured content (PDFs, documents) using AI content analysis."""
    
    agent_monitor.update_task_status(task_id, TaskStatus.RUNNING, "Analyzing unstructured content with AI")
    
    # Extract AI analysis from parsing info
    ai_analysis = parsing_info.get('ai_analysis', {})
    content_type = ai_analysis.get('content_type', 'unknown')
    relevance_score = ai_analysis.get('relevance_score', 50)
    insights = ai_analysis.get('insights', [])
    assets_mentioned = ai_analysis.get('assets_mentioned', [])
    recommendation = ai_analysis.get('recommendation', '')
    
    # Record thinking phase
    agent_monitor.record_thinking_phase(task_id, f"AI analyzing {content_type} content")
    
    # Create data quality result based on AI analysis
    data_quality = DataQualityResult(
        score=min(100, max(50, relevance_score)),  # Convert relevance to quality score
        issues=[] if relevance_score > 70 else [
            "Document content requires manual review for structured data extraction",
            "Consider converting to structured format for better processing"
        ],
        recommendations=[
            recommendation,
            "Extract key information from document for migration planning",
            "Review document for application and infrastructure details",
            "Consider using OCR or document parsing tools for better analysis"
        ] if recommendation else [
            "Manual document review recommended",
            "Extract structured data from document content",
            "Identify migration-relevant information"
        ]
    )
    
    # Create coverage based on content analysis
    coverage = AssetCoverage(
        applications=len([asset for asset in assets_mentioned if 'app' in asset.lower() or 'service' in asset.lower()]),
        servers=len([asset for asset in assets_mentioned if 'server' in asset.lower() or 'srv' in asset.lower()]),
        databases=len([asset for asset in assets_mentioned if 'db' in asset.lower() or 'database' in asset.lower()]),
        dependencies=0  # Cannot determine from unstructured content
    )
    
    # Define missing fields for unstructured content
    missing_fields = [
        "Structured asset inventory needed",
        "Application metadata extraction required",
        "Technical specifications documentation"
    ]
    
    # Processing requirements for unstructured content
    required_processing = [
        "Extract structured data from document content",
        recommendation,
        "Convert findings to asset inventory format",
        "Validate extracted information with stakeholders"
    ]
    
    # Unstructured content typically requires additional processing
    ready_for_import = False
    
    # Create preview data based on AI insights
    preview_data = [
        {
            "Content Type": content_type,
            "AI Relevance Score": f"{relevance_score}%",
            "Assets Found": len(assets_mentioned),
            "Key Insights": ", ".join(insights[:3]) if insights else "Manual review required",
            "Recommendation": recommendation
        }
    ]
    
    # Complete the task
    agent_monitor.complete_task(
        task_id, 
        f"Unstructured content analysis completed for {request.filename} - Type: {content_type}, Relevance: {relevance_score}%"
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
async def submit_cmdb_feedback(request: CMDBFeedbackRequest, db: AsyncSession = Depends(get_db)):
    """
    Submit feedback on CMDB analysis results to improve AI accuracy.
    Now stored in database for Vercel compatibility.
    """
    try:
        from app.models.feedback import Feedback
        
        # Create feedback entry in database
        feedback_entry = Feedback(
            id=uuid.uuid4(),
            feedback_type="cmdb_analysis",
            filename=request.filename,
            original_analysis=request.originalAnalysis,
            user_corrections=request.userCorrections,
            asset_type_override=request.assetTypeOverride,
            status="new"
            # Note: client_account_id and engagement_id are nullable for general feedback
        )
        
        db.add(feedback_entry)
        await db.commit()
        await db.refresh(feedback_entry)
        
        logger.info(f"CMDB feedback stored in database for {request.filename}")
        
        return {
            "status": "success",
            "message": "Feedback submitted successfully",
            "feedback_id": str(feedback_entry.id),
            "storage_method": "database"
        }
        
    except Exception as e:
        logger.error(f"Failed to submit CMDB feedback: {e}")
        await db.rollback()
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
    """Extract data quality assessment from CrewAI result and analyze real data issues."""
    # Get score from CrewAI result (it returns data_quality_score, not data_quality.score)
    score = crewai_result.get("data_quality_score", 75)
    
    # Get issues and recommendations from CrewAI
    issues = crewai_result.get("issues", [])
    recommendations = crewai_result.get("recommendations", [])
    
    # Analyze actual DataFrame for specific data quality issues
    # 1. Missing data analysis
    null_percentage = df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100
    if null_percentage > 20:
        issues.append(f"High percentage of missing data ({null_percentage:.1f}%)")
        recommendations.append("Review data collection processes to reduce missing values")
    
    # 2. Duplicate detection
    duplicate_count = df.duplicated().sum()
    if duplicate_count > 0:
        issues.append(f"Found {duplicate_count} duplicate records requiring de-duplication")
        recommendations.append("Remove or consolidate duplicate entries before proceeding")
    
    # 3. Data format inconsistencies
    for col in df.columns:
        if df[col].dtype == 'object':  # String columns
            unique_values = df[col].dropna().unique()
            
            # Check for mixed case inconsistencies
            if len(unique_values) > 1:
                lower_values = [str(v).lower() for v in unique_values]
                if len(set(lower_values)) < len(unique_values):
                    issues.append(f"Column '{col}' has inconsistent capitalization")
                    recommendations.append(f"Standardize capitalization in '{col}' field")
            
            # Check for abbreviated values that should be standardized
            abbreviated_values = [v for v in unique_values if isinstance(v, str) and len(v) <= 3 and v.isalpha()]
            if abbreviated_values:
                issues.append(f"Column '{col}' contains abbreviated values: {', '.join(abbreviated_values[:3])}")
                recommendations.append(f"Expand abbreviated values in '{col}' to full descriptive names")
            
            # Check for trailing/leading whitespace
            whitespace_values = [v for v in unique_values if isinstance(v, str) and (v.startswith(' ') or v.endswith(' '))]
            if whitespace_values:
                issues.append(f"Column '{col}' contains values with extra whitespace")
                recommendations.append(f"Trim whitespace from '{col}' values")
    
    # 4. Missing critical fields for migration
    critical_fields = ['hostname', 'asset_type', 'environment', 'ip_address', 'application_name']
    missing_critical = [field for field in critical_fields if field not in df.columns]
    if missing_critical:
        issues.append(f"Missing critical fields for migration: {', '.join(missing_critical)}")
        recommendations.append("Add missing critical fields or map from existing columns")
    
    # 5. Inconsistent naming conventions
    column_issues = []
    for col in df.columns:
        if ' ' in col:
            column_issues.append(f"'{col}' contains spaces")
        elif col != col.lower():
            column_issues.append(f"'{col}' not lowercase")
    
    if column_issues:
        issues.append(f"Column naming inconsistencies: {'; '.join(column_issues[:3])}")
        recommendations.append("Standardize column names to lowercase with underscores")
    
    # 6. Asset type validation
    if 'asset_type' in df.columns:
        asset_types = df['asset_type'].dropna().unique()
        invalid_types = [at for at in asset_types if isinstance(at, str) and at.lower() not in [
            'server', 'application', 'database', 'network device', 'storage', 'security device'
        ]]
        if invalid_types:
            issues.append(f"Non-standard asset types found: {', '.join(invalid_types[:3])}")
            recommendations.append("Standardize asset types to canonical values")
    
    # 7. Environment validation
    if 'environment' in df.columns:
        environments = df['environment'].dropna().unique()
        # Check for empty or placeholder values
        empty_envs = [env for env in environments if isinstance(env, str) and env.lower() in ['', 'unknown', 'tbd', 'n/a', 'null']]
        if empty_envs or df['environment'].isnull().sum() > 0:
            missing_env_count = df['environment'].isnull().sum() + len([env for env in environments if env in empty_envs])
            issues.append(f"{missing_env_count} assets missing environment classification")
            recommendations.append("Classify assets into proper environments (Production, Development, Test, etc.)")
    
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