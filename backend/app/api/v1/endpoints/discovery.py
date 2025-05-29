"""
Discovery API endpoints for CMDB import and analysis.
Provides AI-powered data validation and processing capabilities.
"""

import json
import logging
import time
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
import pandas as pd
import numpy as np
import io
from datetime import datetime
import math
import uuid
from pathlib import Path
import os

from app.services.crewai_service import CrewAIService
from app.core.config import settings
from app.services.agent_monitor import agent_monitor, TaskStatus
from app.api.v1.discovery import (
    CMDBDataProcessor,
    standardize_asset_type,
    get_field_value,
    get_tech_stack,
    generate_suggested_headers,
    assess_6r_readiness,
    assess_migration_complexity
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize processor and global storage
processor = CMDBDataProcessor()
processed_assets_store = []  # Global storage for processed assets

# Simple persistence helpers until full client account design
DATA_DIR = Path("data/persistence")
DATA_DIR.mkdir(parents=True, exist_ok=True)

def save_to_file(filename: str, data: any):
    """Save data to a JSON file for persistence."""
    try:
        filepath = DATA_DIR / f"{filename}.json"
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.warning(f"Failed to save {filename}: {e}")

def load_from_file(filename: str, default_value=None):
    """Load data from a JSON file."""
    try:
        filepath = DATA_DIR / f"{filename}.json"
        if filepath.exists():
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load {filename}: {e}")
    return default_value or []

# Initialize persistent stores
feedback_store = load_from_file("feedback_store", [])

# Load processed assets from backup on startup
saved_assets = load_from_file("processed_assets_backup", [])
if saved_assets:
    processed_assets_store.extend(saved_assets)
    logger.info(f"Loaded {len(saved_assets)} assets from backup")

def backup_processed_assets():
    """Backup processed assets to file."""
    save_to_file("processed_assets_backup", processed_assets_store)

def clean_for_json_serialization(data):
    """Convert pandas/numpy data types to JSON-serializable types."""
    if isinstance(data, dict):
        return {k: clean_for_json_serialization(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_for_json_serialization(item) for item in data]
    elif isinstance(data, (pd.Timestamp, pd.DatetimeIndex)):
        return str(data)
    elif isinstance(data, (np.integer, np.int64, np.int32, int)):
        return int(data)
    elif isinstance(data, (np.floating, np.float64, np.float32, float)):
        if isinstance(data, (np.floating, np.float64, np.float32)):
            if np.isnan(data) or np.isinf(data):
                return None
        return float(data)
    elif isinstance(data, (np.bool_, bool)):
        return bool(data)
    elif isinstance(data, np.ndarray):
        return data.tolist()
    elif pd.isna(data):
        return None
    elif hasattr(data, 'item'):  # numpy scalars
        try:
            return data.item()
        except (AttributeError, ValueError):
            return str(data)
    else:
        return data

# Pydantic models for request/response
class CMDBAnalysisRequest(BaseModel):
    filename: str
    content: str
    fileType: str

class CMDBProcessingRequest(BaseModel):
    filename: str
    data: List[Dict[str, Any]]
    projectInfo: Optional[Dict[str, Any]] = None

class CMDBFeedbackRequest(BaseModel):
    filename: str
    originalAnalysis: Dict[str, Any]
    userCorrections: Dict[str, Any]
    assetTypeOverride: Optional[str] = None

class PageFeedbackRequest(BaseModel):
    page: str
    rating: int
    comment: str
    category: str = 'general'
    breadcrumb: str = ''
    timestamp: str

class DataQualityResult(BaseModel):
    score: int
    issues: List[str]
    recommendations: List[str]

class AssetCoverage(BaseModel):
    applications: int
    servers: int
    databases: int
    dependencies: int

class CMDBAnalysisResponse(BaseModel):
    status: str
    dataQuality: DataQualityResult
    coverage: AssetCoverage
    missingFields: List[str]
    requiredProcessing: List[str]
    readyForImport: bool
    preview: Optional[List[Dict[str, Any]]] = None

@router.post("/analyze-cmdb")
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
                crewai_result = {"issues": [], "recommendations": []}
            
            # Enhanced fallback analysis using pattern analysis if AI failed
            if crewai_result.get("parsed") == False or crewai_result.get("fallback_used") == True:
                logger.info("AI analysis failed or used fallback, enhancing with pattern analysis")
                
                # Use pattern analysis to improve the fallback
                try:
                    from app.services.tools.field_mapping_tool import field_mapping_tool
                    
                    # Prepare sample data for pattern analysis
                    sample_rows = []
                    if cmdb_data.get('sample_data'):
                        for record in cmdb_data['sample_data'][:10]:
                            row = [record.get(col, '') for col in df.columns.tolist()]
                            sample_rows.append(row)
                    
                    # Get enhanced pattern analysis
                    pattern_analysis = field_mapping_tool.analyze_data_patterns(
                        df.columns.tolist(), sample_rows, "server"
                    )
                    
                    # Use pattern analysis to enhance the result
                    column_mappings = pattern_analysis.get("column_analysis", {})
                    confidence_scores = pattern_analysis.get("confidence_scores", {})
                    
                    # Calculate better quality score based on pattern analysis
                    total_columns = len(df.columns)
                    mapped_columns = len([col for col, conf in confidence_scores.items() if conf > 0.6])
                    mapping_quality = (mapped_columns / total_columns) * 100 if total_columns > 0 else 0
                    
                    # Enhanced missing fields detection
                    enhanced_missing_fields = processor.identify_missing_fields(df)
                    
                    # Store pattern analysis results in agent memory for fallback use
                    try:
                        from app.services.memory import agent_memory
                        pattern_analysis_experience = {
                            "action": "pattern_analysis_for_fallback",
                            "context": {
                                "missing_fields": enhanced_missing_fields,
                                "mapped_columns": mapped_columns,
                                "total_columns": total_columns,
                                "field_mappings": column_mappings,
                                "confidence_scores": confidence_scores,
                                "asset_type": "server",
                                "filename": request.filename
                            },
                            "result": f"Successfully analyzed {mapped_columns}/{total_columns} columns",
                            "timestamp": datetime.now().isoformat()
                        }
                        agent_memory.add_experience("Field_Mapping_Specialist", pattern_analysis_experience)
                        logger.info(f"Stored pattern analysis in memory for fallback: {enhanced_missing_fields}")
                    except Exception as memory_error:
                        logger.warning(f"Could not store pattern analysis in memory: {memory_error}")
                    
                    # Update crewai_result with enhanced data
                    crewai_result.update({
                        "data_quality_score": max(crewai_result.get("data_quality_score", 0), int(mapping_quality)),
                        "missing_fields_relevant": enhanced_missing_fields,
                        "field_mappings_discovered": [f"{col} → {mapped}" for col, mapped in column_mappings.items() if confidence_scores.get(col, 0) > 0.7],
                        "pattern_analysis_applied": True,
                        "columns_successfully_mapped": mapped_columns,
                        "total_columns": total_columns,
                        "enhanced_with_pattern_analysis": True
                    })
                    
                    logger.info(f"Enhanced fallback with pattern analysis: {mapped_columns}/{total_columns} columns mapped")
                    
                except Exception as pattern_error:
                    logger.warning(f"Pattern analysis enhancement failed: {pattern_error}")
            
            # Perform local analysis to supplement agentic analysis
            coverage = processor.identify_asset_types(df)
            missing_fields = processor.identify_missing_fields(df)
            processing_steps = processor.suggest_processing_steps(df, structure_analysis)
            
            # Ensure all numeric values are JSON-serializable
            def ensure_json_serializable(value):
                if value is None:
                    return 0
                if isinstance(value, (int, str, bool)):
                    return value
                if isinstance(value, float):
                    if math.isnan(value) or math.isinf(value):
                        return 0
                    return int(value) if value.is_integer() else float(value)
                return 0
            
            # Use CrewAI results as primary source, supplement with local analysis
            if crewai_result and isinstance(crewai_result, dict):
                # Extract agentic analysis results
                quality_score = ensure_json_serializable(crewai_result.get('data_quality_score', 75))
                quality_issues = crewai_result.get('issues', [])
                quality_recommendations = crewai_result.get('recommendations', [])
                
                # CRITICAL FIX: Only override asset type classification if we don't have granular workload-based data
                # Check if the processor found granular classifications (mixed asset types)
                has_granular_classification = (coverage.applications > 0 and coverage.databases > 0) or \
                                            (coverage.applications > 0 and coverage.servers > 0) or \
                                            (coverage.databases > 0 and coverage.servers > 0)
                
                if not has_granular_classification:
                    # Only override if we don't have mixed types from workload analysis
                    asset_type_detected = crewai_result.get('asset_type_detected', 'mixed')
                    if asset_type_detected == 'application':
                        coverage = AssetCoverage(applications=len(df), servers=0, databases=0, dependencies=0)
                    elif asset_type_detected == 'server':
                        coverage = AssetCoverage(applications=0, servers=len(df), databases=0, dependencies=0)
                    elif asset_type_detected == 'database':
                        coverage = AssetCoverage(applications=0, servers=0, databases=len(df), dependencies=0)
                else:
                    # Keep the granular workload-based classification
                    logger.info(f"Preserving granular workload classification: Apps={coverage.applications}, DBs={coverage.databases}, Servers={coverage.servers}")
                
                # Use agentic missing fields analysis
                agentic_missing_fields = crewai_result.get('missing_fields_relevant', [])
                if agentic_missing_fields:
                    missing_fields = agentic_missing_fields
            
            else:
                # Fallback to local analysis if agentic analysis failed
                logger.info("Using local analysis as fallback")
                
                # Calculate data quality score locally
                total_cells = len(df) * len(df.columns)
                null_count = df.isnull().sum().sum()
                null_percentage = (null_count / total_cells * 100) if total_cells > 0 else 0
                duplicate_count = len(df) - len(df.drop_duplicates())
                
                base_score = 100.0
                base_score -= min(30.0, null_percentage)
                if len(df) > 0:
                    base_score -= min(20.0, (duplicate_count / len(df)) * 100)
                base_score -= len(missing_fields) * 5.0
                
                quality_score = ensure_json_serializable(max(0, min(100, int(base_score))))
                
                quality_issues = []
                quality_recommendations = []
                
                if null_percentage > 10:
                    quality_issues.append(f"High percentage of missing values: {null_percentage:.1f}%")
                    quality_recommendations.append("Fill missing values or remove incomplete records")
                
                if duplicate_count > 0:
                    quality_issues.append(f"Found {duplicate_count} duplicate records")
                    quality_recommendations.append("Remove duplicate entries")
            
            # Prepare response in the format expected by frontend
            result = {
                "status": "completed",
                "dataQuality": {
                    "score": ensure_json_serializable(quality_score),
                    "issues": quality_issues if isinstance(quality_issues, list) else [],
                    "recommendations": quality_recommendations if isinstance(quality_recommendations, list) else []
                },
                "coverage": {
                    "applications": ensure_json_serializable(coverage.applications),
                    "servers": ensure_json_serializable(coverage.servers),
                    "databases": ensure_json_serializable(coverage.databases),
                    "dependencies": ensure_json_serializable(coverage.dependencies)
                },
                "missingFields": missing_fields if isinstance(missing_fields, list) else [],
                "requiredProcessing": processing_steps if isinstance(processing_steps, list) else [],
                "readyForImport": quality_score >= 70 and len(missing_fields) <= 3,
                "preview": []  # Initialize empty, will populate below
            }
            
            # Safely create preview data with JSON-serializable values
            try:
                preview_df = df.head(10)
                preview_records = []
                
                for _, row in preview_df.iterrows():
                    record = {}
                    for col in preview_df.columns:
                        value = row[col]
                        # Convert pandas/numpy types to JSON-serializable types
                        if pd.isna(value):
                            record[str(col)] = None
                        elif isinstance(value, (pd.Timestamp, pd.DatetimeIndex)):
                            record[str(col)] = str(value)
                        elif isinstance(value, (int, str, bool)):
                            record[str(col)] = value
                        elif isinstance(value, float):
                            if math.isnan(value) or math.isinf(value):
                                record[str(col)] = None
                            else:
                                record[str(col)] = float(value)
                        else:
                            record[str(col)] = str(value)
                    preview_records.append(record)
                
                result["preview"] = preview_records
                
            except Exception as e:
                logger.warning(f"Error creating preview data: {e}")
                result["preview"] = []
            
            # Complete the task
            agent_monitor.complete_task(task_id, f"Analysis completed with {quality_score}% quality score")
            
            logger.info(f"CMDB analysis completed for {request.filename}")
            return result
            
        except Exception as e:
            # Fail the task
            agent_monitor.fail_task(task_id, str(e))
            raise e
            
    except Exception as e:
        logger.error(f"Error in CMDB analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/process-cmdb")
async def process_cmdb_data(request: CMDBProcessingRequest):
    """
    Process and clean CMDB data based on user edits and AI recommendations.
    """
    global processed_assets_store  # Move global declaration to the beginning
    
    try:
        logger.info(f"Starting CMDB processing for file: {request.filename}")
        
        # Convert the edited data to DataFrame
        df = pd.DataFrame(request.data)
        
        if len(df) == 0:
            raise HTTPException(status_code=400, detail="No data provided for processing")
        
        # Apply data processing steps with agentic intelligence
        processed_df = df.copy()
        
        # CRITICAL: Apply field mappings discovered during analysis
        # This ensures the data is transformed using the learned field mappings
        try:
            from app.services.tools.field_mapping_tool import field_mapping_tool
            
            # Get enhanced pattern analysis to apply field mappings
            sample_rows = []
            for _, row in processed_df.head(10).iterrows():
                sample_row = [str(row[col]) if pd.notna(row[col]) else '' for col in processed_df.columns]
                sample_rows.append(sample_row)
            
            # Analyze current column patterns
            pattern_analysis = field_mapping_tool.analyze_data_patterns(
                processed_df.columns.tolist(), sample_rows, "server"
            )
            
            column_mappings = pattern_analysis.get("column_analysis", {})
            confidence_scores = pattern_analysis.get("confidence_scores", {})
            
            # Apply field renaming based on discovered mappings
            field_rename_map = {}
            used_target_names = set()
            
            for original_column, canonical_field in column_mappings.items():
                confidence = confidence_scores.get(original_column, 0.0)
                if confidence > 0.7:  # High confidence mappings
                    # Convert canonical field name to standardized column name
                    standardized_name = canonical_field.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')
                    
                    # Avoid duplicate target column names
                    if standardized_name not in used_target_names and standardized_name not in processed_df.columns:
                        field_rename_map[original_column] = standardized_name
                        used_target_names.add(standardized_name)
                        logger.info(f"Mapping field: {original_column} → {standardized_name} (canonical: {canonical_field})")
                    else:
                        logger.warning(f"Skipping mapping {original_column} → {standardized_name} (target already exists)")
            
            # Apply the field renaming
            if field_rename_map:
                processed_df = processed_df.rename(columns=field_rename_map)
                logger.info(f"Applied {len(field_rename_map)} field mappings during processing")
            
            # Combine OS fields if both exist
            os_type_col = None
            os_version_col = None
            
            # Find OS-related columns (could be renamed or original)
            for col in processed_df.columns:
                col_lower = col.lower()
                if 'operating_system' in col_lower and 'version' not in col_lower:
                    os_type_col = col
                elif 'os_version' in col_lower or col_lower in ['os version', 'os_version']:
                    os_version_col = col
                elif col_lower == 'os version':
                    os_version_col = col
            
            # Rename OS columns to standardized names
            if os_type_col and os_type_col in processed_df.columns:
                if 'operating_system' not in processed_df.columns:
                    processed_df = processed_df.rename(columns={os_type_col: 'operating_system'})
                    logger.info(f"Renamed {os_type_col} to operating_system")
            
            if os_version_col and os_version_col in processed_df.columns:
                if 'os_version' not in processed_df.columns:
                    processed_df = processed_df.rename(columns={os_version_col: 'os_version'})
                    logger.info(f"Renamed {os_version_col} to os_version")
            
        except Exception as e:
            logger.warning(f"Field mapping application failed: {e}")
        
        # Use CrewAI for intelligent asset processing and classification
        processing_result = await processor.crewai_service.process_cmdb_data({
            'original_data': request.data,
            'processed_data': processed_df.to_dict('records'),
            'filename': request.filename,
            'project_info': request.projectInfo
        })
        
        # Apply intelligent asset type classification to each record
        for idx, row in processed_df.iterrows():
            asset_data = row.to_dict()
            
            # Get asset name using multiple field name variations
            asset_name = get_field_value(asset_data, ['asset_name', 'hostname', 'name', 'ci_name', 'server_name'])
            
            # Get asset type - CRITICAL: Use workload_type which contains the granular classification
            workload_type = get_field_value(asset_data, ['workload_type', 'workload type', 'asset_type', 'ci_type', 'type'])
            
            # ENHANCED APPLICATION MAPPING - Try multiple field patterns and smart detection
            app_mapped = get_field_value(asset_data, [
                'application_mapped', 'app_mapped', 'application mapped', 'mapped_application', 
                'application_service', 'application', 'app_name', 'business_service',
                'service_name', 'hosted_application', 'running_application'
            ])
            
            # Smart application detection for servers based on naming patterns
            if app_mapped == "Unknown" and workload_type in ["App Server", "Application Server", "Web Server"]:
                # Try to infer application from server name
                server_name_lower = asset_name.lower()
                if "hr" in server_name_lower or "payroll" in server_name_lower:
                    app_mapped = "HR_Payroll"
                elif "finance" in server_name_lower or "erp" in server_name_lower:
                    app_mapped = "Finance_ERP"
                elif "crm" in server_name_lower or "customer" in server_name_lower:
                    app_mapped = "CRM_System"
                elif "web" in server_name_lower and "app" in server_name_lower:
                    app_mapped = f"WebApp_{asset_name[:10]}"
                elif "db" in server_name_lower or "database" in server_name_lower:
                    app_mapped = f"Database_{asset_name[:10]}"
                elif "file" in server_name_lower:
                    app_mapped = "File_Services"
                elif "ad" in server_name_lower or "domain" in server_name_lower:
                    app_mapped = "Active_Directory"
                else:
                    # Create application mapping based on department or owner
                    department = get_field_value(asset_data, ['business_owner', 'department', 'owner'])
                    if department != "Unknown":
                        app_mapped = f"{department.replace(' ', '_')}_Application"
            
            # For databases, try to map to related applications
            elif app_mapped == "Unknown" and workload_type in ["Database Server", "DB Server"]:
                server_name_lower = asset_name.lower()
                if "hr" in server_name_lower or "payroll" in server_name_lower:
                    app_mapped = "HR_Payroll"
                elif "finance" in server_name_lower or "erp" in server_name_lower:
                    app_mapped = "Finance_ERP"
                elif "crm" in server_name_lower:
                    app_mapped = "CRM_System"
                else:
                    app_mapped = f"Database_Service_{asset_name[:10]}"
            
            # Use enhanced asset type classification with workload type
            intelligent_type = standardize_asset_type(workload_type, asset_name, asset_data)
            processed_df.at[idx, 'intelligent_asset_type'] = intelligent_type
            
            # Also update the main asset_type field to use the intelligent classification
            processed_df.at[idx, 'asset_type'] = intelligent_type
            
            # PRESERVE and ENHANCE the application mapping data
            if app_mapped != "Unknown":
                processed_df.at[idx, 'application_mapped'] = app_mapped
                processed_df.at[idx, 'app_mapped'] = app_mapped  # Store in both fields
                logger.info(f"Preserved/Enhanced app mapping for {asset_name}: {app_mapped}")
            
            # Add 6R readiness assessment
            processed_df.at[idx, 'sixr_ready'] = assess_6r_readiness(intelligent_type, asset_data)
            
            # Add migration complexity indicator
            processed_df.at[idx, 'migration_complexity'] = assess_migration_complexity(intelligent_type, asset_data)
        
        # Remove duplicates
        original_rows = len(processed_df)
        processed_df = processed_df.drop_duplicates()
        duplicates_removed = original_rows - len(processed_df)
        
        # Clean and standardize data
        processing_steps = []
        
        # Standardize column names
        old_columns = processed_df.columns.tolist()
        processed_df.columns = [col.strip().replace(' ', '_').lower() for col in processed_df.columns]
        if old_columns != processed_df.columns.tolist():
            processing_steps.append("Standardized column names")
        
        # Fill missing values with appropriate defaults
        null_counts_before = processed_df.isnull().sum().sum()
        for column in processed_df.columns:
            try:
                # Check if column exists and is accessible
                if column in processed_df.columns and not processed_df[column].empty:
                    if processed_df[column].dtype == 'object':
                        processed_df[column] = processed_df[column].fillna('Unknown')
                    else:
                        processed_df[column] = processed_df[column].fillna(0)
                else:
                    logger.warning(f"Skipping column {column} - empty or inaccessible")
            except Exception as e:
                logger.warning(f"Error processing column {column}: {e}")
                # Set default values for problematic columns
                try:
                    processed_df[column] = processed_df[column].fillna('Unknown')
                except:
                    logger.error(f"Failed to fill NA values for column {column}")
                    continue
        
        null_counts_after = processed_df.isnull().sum().sum()
        if null_counts_before > null_counts_after:
            processing_steps.append(f"Filled {null_counts_before - null_counts_after} missing values")
        
        if duplicates_removed > 0:
            processing_steps.append(f"Removed {duplicates_removed} duplicate records")
        
        # Validate required fields
        required_fields = ['asset_name', 'asset_type', 'environment']
        missing_required = [field for field in required_fields if field not in processed_df.columns]
        
        # Calculate final quality score
        total_cells = len(processed_df) * len(processed_df.columns)
        null_percentage = (processed_df.isnull().sum().sum() / total_cells) * 100 if total_cells > 0 else 0
        duplicate_percentage = (duplicates_removed / original_rows) * 100 if original_rows > 0 else 0
        quality_score = max(0, 100 - null_percentage - duplicate_percentage)
        
        # Store processed assets in memory (in production, this would be saved to database)
        processed_data_records = processed_df.to_dict('records')
        
        # Clean the data for JSON serialization (fix numpy types)
        processed_data_records = clean_for_json_serialization(processed_data_records)
        
        # Clear existing data and add new processed assets
        global processed_assets_store
        processed_assets_store.clear()
        processed_assets_store.extend(processed_data_records)
        
        logger.info(f"Stored {len(processed_data_records)} processed assets in inventory")
        
        # Handle project creation if requested
        project_created = False
        project_id = None
        
        if request.projectInfo and request.projectInfo.get('saveToDatabase'):
            try:
                # Here you would typically save to your database
                # For now, we'll simulate project creation
                project_id = f"proj_{int(time.time())}"
                project_created = True
                processing_steps.append(f"Created project: {request.projectInfo.get('name', 'Unnamed Project')}")
                logger.info(f"Created project {project_id} for CMDB data")
            except Exception as e:
                logger.warning(f"Failed to create project: {e}")
        
        response = {
            "status": "completed",
            "message": "Data processing completed successfully",
            "summary": {
                "original_rows": original_rows,
                "processed_rows": len(processed_df),
                "duplicates_removed": duplicates_removed,
                "quality_score": int(quality_score),
                "missing_required_fields": missing_required
            },
            "processing_steps_applied": processing_steps,
            "project": {
                "created": project_created,
                "project_id": project_id,
                "name": request.projectInfo.get('name') if request.projectInfo else None
            } if request.projectInfo else None,
            "processed_data": clean_for_json_serialization(processed_df.to_dict('records')),
            "ai_processing_result": clean_for_json_serialization(processing_result),
            "ready_for_import": len(missing_required) == 0 and quality_score >= 70
        }
        
        # Clean the entire response to ensure no numpy types anywhere
        response = clean_for_json_serialization(response)
        
        # Store processed assets globally for cross-endpoint access
        processed_assets_store = processed_data_records
        
        # Backup processed assets for persistence
        backup_processed_assets()
        
        logger.info(f"CMDB processing completed for {request.filename}. Processed {len(processed_data_records)} assets")
        return response
        
    except Exception as e:
        logger.error(f"Error processing CMDB data: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.post("/cmdb-feedback")
async def submit_cmdb_feedback(request: CMDBFeedbackRequest):
    """
    Submit user feedback to correct AI analysis and improve future predictions.
    Returns updated analysis based on user corrections.
    """
    try:
        logger.info(f"Receiving user feedback for file: {request.filename}")
        
        # Start monitoring the feedback processing task
        task_id = f"feedback_processing_{str(uuid.uuid4())[:8]}"
        task_exec = agent_monitor.start_task(
            task_id, 
            "AI_Learning_Specialist", 
            f"Processing user feedback for {request.filename}"
        )
        
        try:
            # Update task status
            agent_monitor.update_task_status(task_id, TaskStatus.RUNNING, "Processing user feedback")
            
            # Process user corrections
            corrections = request.userCorrections
            asset_type_override = request.assetTypeOverride
            
            # Record thinking phase
            agent_monitor.record_thinking_phase(task_id, "Analyzing user corrections and patterns")
            
            # Re-analyze with user feedback
            feedback_context = {
                'filename': request.filename,
                'original_analysis': request.originalAnalysis,
                'user_corrections': corrections,
                'asset_type_override': asset_type_override,
                'feedback_timestamp': datetime.now().isoformat()
            }
            
            # Use CrewAI to learn from feedback
            agent_monitor.update_task_status(task_id, TaskStatus.WAITING_LLM, "AI learning in progress")
            learning_result = await processor.crewai_service.process_user_feedback(feedback_context)
            
            # Generate updated analysis based on feedback
            original_analysis = request.originalAnalysis
            updated_analysis = original_analysis.copy()
            
            # Apply asset type correction if provided
            if asset_type_override:
                # Update coverage based on corrected asset type
                total_assets = (original_analysis.get('coverage', {}).get('applications', 0) + 
                              original_analysis.get('coverage', {}).get('servers', 0) + 
                              original_analysis.get('coverage', {}).get('databases', 0))
                
                if asset_type_override.lower() == 'application':
                    updated_analysis['coverage'] = {
                        'applications': total_assets,
                        'servers': 0,
                        'databases': 0,
                        'dependencies': original_analysis.get('coverage', {}).get('dependencies', 0)
                    }
                elif asset_type_override.lower() == 'server':
                    updated_analysis['coverage'] = {
                        'applications': 0,
                        'servers': total_assets,
                        'databases': 0,
                        'dependencies': original_analysis.get('coverage', {}).get('dependencies', 0)
                    }
                elif asset_type_override.lower() == 'database':
                    updated_analysis['coverage'] = {
                        'applications': 0,
                        'servers': 0,
                        'databases': total_assets,
                        'dependencies': original_analysis.get('coverage', {}).get('dependencies', 0)
                    }
                
                # Update missing fields based on asset type
                if asset_type_override.lower() == 'application':
                    # Applications don't need hardware specs
                    hardware_fields = ['cpu_cores', 'memory_gb', 'storage_gb', 'ip_address', 'operating_system']
                    updated_missing_fields = [field for field in original_analysis.get('missingFields', []) 
                                            if field.lower() not in [f.lower() for f in hardware_fields]]
                    updated_analysis['missingFields'] = updated_missing_fields
                elif asset_type_override.lower() == 'server':
                    # Servers need hardware specs
                    required_server_fields = ['operating_system', 'cpu_cores', 'memory_gb']
                    current_missing = set(original_analysis.get('missingFields', []))
                    for field in required_server_fields:
                        if field not in current_missing:
                            current_missing.add(field)
                    updated_analysis['missingFields'] = list(current_missing)
            
            # Update data quality score based on corrections
            if corrections.get('analysisIssues'):
                # Improve quality score if user provided corrections
                current_score = original_analysis.get('dataQuality', {}).get('score', 0)
                improved_score = min(100, current_score + 10)  # Boost by 10 points
                updated_analysis['dataQuality']['score'] = improved_score
                
                # Update issues and recommendations
                updated_issues = original_analysis.get('dataQuality', {}).get('issues', []).copy()
                updated_recommendations = original_analysis.get('dataQuality', {}).get('recommendations', []).copy()
                
                # Add feedback-based improvements
                if asset_type_override:
                    updated_recommendations.append(f"Asset type corrected to: {asset_type_override}")
                
                updated_recommendations.append("Analysis improved based on user feedback")
                
                updated_analysis['dataQuality']['issues'] = updated_issues
                updated_analysis['dataQuality']['recommendations'] = updated_recommendations
            
            # Generate response with both learning result and updated analysis
            response = {
                'status': 'corrected',
                'message': 'Analysis updated based on user feedback',
                'corrections_applied': corrections,
                'asset_type_corrected': asset_type_override,
                'learning_result': learning_result,
                'updated_analysis': updated_analysis,  # Include the updated analysis
                'improvements': [
                    f"Asset type corrected to: {asset_type_override}" if asset_type_override else None,
                    "Field requirements updated based on asset type context",
                    "Data quality score improved based on feedback",
                    "Future analysis will consider this feedback for similar datasets"
                ]
            }
            
            # Filter out None values
            response['improvements'] = [
                improvement for improvement in response['improvements'] if improvement is not None
            ]
            
            # Complete the task
            patterns_count = len(learning_result.get("patterns_identified", []))
            agent_monitor.complete_task(task_id, f"Learning completed: {patterns_count} patterns identified")
            
            logger.info(f"User feedback processed for {request.filename}")
            return response
            
        except Exception as e:
            # Fail the task
            agent_monitor.fail_task(task_id, str(e))
            raise e
        
    except Exception as e:
        logger.error(f"Error processing user feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Feedback processing failed: {str(e)}")

@router.post("/feedback")
async def submit_page_feedback(request: PageFeedbackRequest):
    """
    Submit general page feedback from users.
    Stores feedback for analysis and improvements.
    """
    try:
        logger.info(f"Receiving page feedback for: {request.page}")
        
        # Store feedback with persistent storage
        global feedback_store
        feedback_entry = {
            "id": str(uuid.uuid4()),
            "page": request.page,
            "rating": request.rating,
            "comment": request.comment,
            "category": request.category,
            "breadcrumb": request.breadcrumb,
            "timestamp": request.timestamp,
            "status": "new"
        }
        
        # Add to in-memory store
        feedback_store.append(feedback_entry)
        
        # Save to persistent storage
        save_to_file("feedback_store", feedback_store)
        
        logger.info(f"Feedback stored with ID: {feedback_entry['id']}")
        
        return {
            "status": "success",
            "message": "Feedback submitted successfully",
            "feedback_id": feedback_entry["id"]
        }
        
    except Exception as e:
        logger.error(f"Error storing page feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Feedback submission failed: {str(e)}")

@router.get("/feedback")
async def get_feedback():
    """
    Get all submitted feedback from persistent storage.
    """
    try:
        global feedback_store
        
        # If no feedback in store, load demo data
        if not feedback_store:
            demo_feedback = [
                {
                    "id": "demo-1",
                    "page": "Asset Inventory",
                    "rating": 4,
                    "comment": "The app dependencies dropdown is now working great with the refresh button! Makes it much easier to see which applications are mapped to servers.",
                    "category": "feature",
                    "breadcrumb": "/discovery/inventory",
                    "timestamp": "2025-01-28T15:45:00Z",
                    "status": "resolved"
                },
                {
                    "id": "demo-2",
                    "page": "Chat Interface",
                    "rating": 5,
                    "comment": "The enhanced chat provides much better context about my actual asset data instead of generic responses.",
                    "category": "feature",
                    "breadcrumb": "/discovery/inventory",
                    "timestamp": "2025-01-28T14:30:00Z",
                    "status": "reviewed"
                }
            ]
            return {
                "feedback": demo_feedback,
                "summary": {
                    "total": len(demo_feedback),
                    "avgRating": 4.5,
                    "byStatus": {"new": 0, "reviewed": 1, "resolved": 1}
                }
            }
        
        # Calculate summary from actual feedback
        total = len(feedback_store)
        avgRating = sum(f["rating"] for f in feedback_store) / total if total > 0 else 0
        byStatus = {}
        for feedback in feedback_store:
            status = feedback.get("status", "new")
            byStatus[status] = byStatus.get(status, 0) + 1
        
        return {
            "feedback": feedback_store,
            "summary": {
                "total": total,
                "avgRating": round(avgRating, 1),
                "byStatus": byStatus
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve feedback: {str(e)}")

@router.get("/assets")
async def get_processed_assets(
    page: int = 1,
    page_size: int = 50,
    asset_type: str = None,
    environment: str = None,
    department: str = None,
    criticality: str = None,
    search: str = None
):
    """
    Get all processed assets from CMDB imports with pagination and filtering.
    Returns test data if no processed data exists.
    """
    try:
        # Check if we have processed data
        has_processed_data = len(processed_assets_store) > 0
        
        if has_processed_data:
            # Return processed assets with proper formatting
            formatted_assets = []
            
            for asset in processed_assets_store:
                # Get asset name for better type detection with flexible field mapping
                asset_name = get_field_value(asset, ["asset_name", "name", "hostname", "ci_name"])
                asset_type_value = get_field_value(asset, ["asset_type", "ci_type", "type", "sys_class_name"])
                
                # Helper function to get numeric values
                def get_numeric_value(asset, field_names):
                    value = get_field_value(asset, field_names)
                    if value == "Unknown":
                        return None
                    try:
                        # Handle various numeric formats
                        numeric_val = float(str(value).replace(',', '').strip())
                        return int(numeric_val) if numeric_val.is_integer() else numeric_val
                    except (ValueError, AttributeError):
                        return None
                
                # CRITICAL: Preserve Application Mapping data
                app_mapped = get_field_value(asset, ["application_mapped", "app_mapped", "application mapped"])
                
                # Extract app ID from application mapping (e.g., "App 130" -> "130")
                app_id = None
                if app_mapped != "Unknown" and "app" in app_mapped.lower():
                    try:
                        app_id = ''.join(filter(str.isdigit, app_mapped))
                        if app_id:
                            app_id = f"APP_{app_id}"
                    except:
                        pass
                
                # Standardize asset data format with flexible field mapping
                formatted_asset = {
                    "id": get_field_value(asset, ["ci_id", "asset_id", "id", "asset_name", "name", "hostname"]) or f"ASSET_{len(formatted_assets) + 1}",
                    "type": standardize_asset_type(asset_type_value, asset_name, asset),
                    "name": asset_name,
                    "techStack": get_tech_stack(asset),
                    "department": get_field_value(asset, ["business_owner", "department", "owner", "responsible_party", "assigned_to"]),
                    "status": "Discovered",
                    "environment": get_field_value(asset, ["environment", "env", "stage", "tier"]),
                    "criticality": get_field_value(asset, ["criticality", "business_criticality", "priority", "importance"]),
                    "ipAddress": get_field_value(asset, ["ip_address", "ip", "network_address", "host_ip"]),
                    "operatingSystem": get_field_value(asset, ["operating_system", "os", "platform", "os_name", "os_type"]),
                    "osVersion": get_field_value(asset, ["os_version", "version", "os_ver", "operating_system_version"]),
                    "cpuCores": get_numeric_value(asset, ["cpu_cores", "cpu", "cores", "processors", "vcpu"]),
                    "memoryGb": get_numeric_value(asset, ["memory_gb", "memory", "ram", "ram_gb", "mem"]),
                    "storageGb": get_numeric_value(asset, ["storage_gb", "storage", "disk", "disk_gb", "hdd", "disk_size_gb"]),
                    # PRESERVE APP MAPPING
                    "applicationMapped": app_mapped if app_mapped != "Unknown" else None,
                    "applicationId": app_id,
                    # Additional fields for enhanced functionality
                    "workloadType": get_field_value(asset, ["workload_type", "workload type"]),
                    "location": get_field_value(asset, ["location", "datacenter", "site"]),
                    "vendor": get_field_value(asset, ["vendor", "manufacturer"]),
                    "model": get_field_value(asset, ["model", "hardware_model"]),
                    "serialNumber": get_field_value(asset, ["serial_number", "serial", "asset_tag"]),
                    # Metadata for editing
                    "lastUpdated": asset.get("last_updated", "2025-01-28T10:18:14"),
                    "discoverySource": "CMDB Import"
                }
                formatted_assets.append(formatted_asset)
            
            data_source = "live"
            
        else:
            # Return default test data for UI development and demonstration
            formatted_assets = [
                {
                    "id": "APP001",
                    "type": "Application",
                    "name": "HR_Payroll",
                    "techStack": "Java 8 | Spring Boot",
                    "department": "Human Resources",
                    "status": "Discovered",
                    "environment": "Production",
                    "criticality": "High",
                    "ipAddress": None,
                    "operatingSystem": None,
                    "osVersion": None,
                    "cpuCores": None,
                    "memoryGb": None,
                    "storageGb": None,
                    "applicationMapped": None,
                    "applicationId": "APP001",
                    "workloadType": "Application",
                    "location": "Datacenter A",
                    "vendor": None,
                    "model": None,
                    "serialNumber": None,
                    "lastUpdated": "2025-01-28T10:18:14",
                    "discoverySource": "Demo Data"
                },
                {
                    "id": "SRV001",
                    "type": "Server",
                    "name": "srv-hr-01",
                    "techStack": "Windows Server 2019",
                    "department": "IT Operations",
                    "status": "Discovered",
                    "environment": "Production",
                    "criticality": "High",
                    "ipAddress": "192.168.1.10",
                    "operatingSystem": "Windows Server 2019",
                    "osVersion": "2019",
                    "cpuCores": 8,
                    "memoryGb": 32,
                    "storageGb": 500,
                    "applicationMapped": "HR_Payroll",
                    "applicationId": "APP001",
                    "workloadType": "App Server",
                    "location": "Datacenter A",
                    "vendor": "Dell",
                    "model": "PowerEdge R640",
                    "serialNumber": "SRV001-2023",
                    "lastUpdated": "2025-01-28T10:18:14",
                    "discoverySource": "Demo Data"
                }
            ]
            
            data_source = "test"
        
        # Apply filters
        filtered_assets = formatted_assets
        
        if asset_type:
            filtered_assets = [a for a in filtered_assets if a["type"].lower() == asset_type.lower()]
        
        if environment:
            filtered_assets = [a for a in filtered_assets if a["environment"].lower() == environment.lower()]
            
        if department:
            filtered_assets = [a for a in filtered_assets if department.lower() in a["department"].lower()]
            
        if criticality:
            filtered_assets = [a for a in filtered_assets if a["criticality"].lower() == criticality.lower()]
            
        if search:
            search_lower = search.lower()
            filtered_assets = [a for a in filtered_assets if 
                             search_lower in a["name"].lower() or 
                             search_lower in a["type"].lower() or
                             search_lower in a["techStack"].lower() or
                             search_lower in (a["applicationMapped"] or "").lower()]
        
        # Calculate pagination
        total_filtered = len(filtered_assets)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_assets = filtered_assets[start_idx:end_idx]
        
        # Calculate summary statistics with enhanced device types
        device_types = ["Network Device", "Storage Device", "Security Device", "Infrastructure Device", "Virtualization Platform"]
        
        summary = {
            "total": len(formatted_assets),
            "filtered": total_filtered,
            "applications": len([a for a in filtered_assets if a["type"] == "Application"]),
            "servers": len([a for a in filtered_assets if a["type"] == "Server"]),
            "databases": len([a for a in filtered_assets if a["type"] == "Database"]),
            "devices": len([a for a in filtered_assets if a["type"] in device_types]),
            "unknown": len([a for a in filtered_assets if a["type"] == "Unknown"]),
            "discovered": len([a for a in filtered_assets if a["status"] == "Discovered"]),
            "pending": len([a for a in filtered_assets if a["status"] == "Pending"]),
            # Breakdown by device type
            "device_breakdown": {
                "network": len([a for a in filtered_assets if a["type"] == "Network Device"]),
                "storage": len([a for a in filtered_assets if a["type"] == "Storage Device"]),
                "security": len([a for a in filtered_assets if a["type"] == "Security Device"]),
                "infrastructure": len([a for a in filtered_assets if a["type"] == "Infrastructure Device"]),
                "virtualization": len([a for a in filtered_assets if a["type"] == "Virtualization Platform"])
            }
        }
        
        # Generate suggested headers based on actual data
        suggested_headers = generate_suggested_headers(formatted_assets)
        
        # Pagination metadata
        total_pages = (total_filtered + page_size - 1) // page_size
        
        return {
            "assets": paginated_assets,
            "summary": summary,
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_items": total_filtered,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            },
            "dataSource": data_source,
            "suggestedHeaders": suggested_headers,
            "lastUpdated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error retrieving processed assets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve assets: {str(e)}")

@router.get("/cmdb-templates")
async def get_cmdb_templates():
    """
    Get CMDB import templates and field mappings.
    """
    templates = {
        "standard_cmdb": {
            "name": "Standard CMDB Template",
            "description": "Standard CMDB export format with essential fields",
            "required_fields": [
                "asset_name", "asset_type", "environment", "business_owner",
                "criticality", "operating_system", "cpu_cores", "memory_gb", "storage_gb"
            ],
            "optional_fields": [
                "location", "cost_center", "support_group", "vendor",
                "model", "serial_number", "ip_address", "dependencies"
            ]
        },
        "servicenow": {
            "name": "ServiceNow CMDB",
            "description": "ServiceNow Configuration Management Database format",
            "field_mappings": {
                "name": "asset_name",
                "sys_class_name": "asset_type",
                "environment": "environment",
                "business_service": "business_owner"
            }
        },
        "remedy": {
            "name": "BMC Remedy CMDB",
            "description": "BMC Remedy Asset Management format",
            "field_mappings": {
                "InstanceId": "asset_name",
                "ClassId": "asset_type",
                "Site": "environment",
                "BusinessService": "business_owner"
            }
        }
    }
    
    return {
        "templates": templates,
        "minimal_required_fields": [
            "Asset Name/Hostname",
            "Asset Type/Category", 
            "Environment",
            "Business Criticality"
        ],
        "recommended_fields": [
            "Operating System",
            "CPU Cores",
            "Memory (GB)",
            "Storage (GB)",
            "Business Owner",
            "Dependencies"
        ]
    }

@router.get("/test-field-mapping")
async def test_field_mapping():
    """
    Test endpoint to verify field mapping functionality.
    Helps debug missing field detection issues.
    """
    try:
        from app.services.field_mapper import field_mapper
        
        # Test with the user's actual column names
        test_columns = [
            'Asset_ID', 'Asset_Name', 'Asset_Type', 'Manufacturer', 'Model', 
            'Serial_Number', 'Location_Rack', 'Location_U', 'Location_DataCenter',
            'Operating_System', 'OS_Version', 'CPU_Cores', 'RAM_GB', 'Storage_GB',
            'IP_Address', 'MAC_Address', 'Application_Service', 'Application_Owner',
            'Virtualization_Host_ID', 'Last_Discovery_Date', 'Support_Contract_End_Date',
            'Maintenance_Window', 'DR_Tier', 'Cloud_Migration_Readiness_Score', 'Migration_Notes'
        ]
        
        # Test missing field detection
        missing_fields = field_mapper.identify_missing_fields(test_columns, 'server')
        
        # Test specific field matches
        memory_matches = field_mapper.find_matching_fields(test_columns, 'Memory (GB)')
        cpu_matches = field_mapper.find_matching_fields(test_columns, 'CPU Cores')
        asset_name_matches = field_mapper.find_matching_fields(test_columns, 'Asset Name')
        
        # Get mapping statistics
        stats = field_mapper.get_mapping_statistics()
        
        return {
            "status": "success",
            "test_columns": test_columns,
            "missing_fields": missing_fields,
            "field_matches": {
                "Memory (GB)": memory_matches,
                "CPU Cores": cpu_matches,
                "Asset Name": asset_name_matches
            },
            "mapping_statistics": stats,
            "message": "Field mapping test completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Field mapping test failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Field mapping test failed"
        }

@router.get("/applications")
async def get_applications_for_analysis():
    """
    Get applications from discovered assets that are suitable for 6R analysis.
    Transforms asset inventory data into application format for 6R treatment.
    """
    try:
        # Get all discovered assets
        has_processed_data = len(processed_assets_store) > 0
        
        if not has_processed_data:
            # Return demo applications if no real data
            return {
                "applications": [
                    {
                        "id": 1,
                        "name": "HR_Payroll",
                        "description": "Human Resources payroll management system",
                        "techStack": "Java 8, Spring Boot, MySQL",
                        "department": "Human Resources", 
                        "environment": "Production",
                        "criticality": "High",
                        "sixr_ready": "Ready",
                        "migration_complexity": "Medium",
                        "application_type": "custom",
                        "business_unit": "Human Resources",
                        "complexity_score": 6
                    },
                    {
                        "id": 2,
                        "name": "Finance_ERP",
                        "description": "Enterprise resource planning system for finance",
                        "techStack": ".NET Core 6, SQL Server",
                        "department": "Finance",
                        "environment": "Production", 
                        "criticality": "Critical",
                        "sixr_ready": "Ready",
                        "migration_complexity": "High",
                        "application_type": "commercial",
                        "business_unit": "Finance",
                        "complexity_score": 8
                    },
                    {
                        "id": 3,
                        "name": "CRM_System", 
                        "description": "Customer relationship management platform",
                        "techStack": "Python Django, PostgreSQL",
                        "department": "Sales",
                        "environment": "Production",
                        "criticality": "Medium",
                        "sixr_ready": "Needs Owner Info",
                        "migration_complexity": "Low",
                        "application_type": "custom",
                        "business_unit": "Sales",
                        "complexity_score": 4
                    }
                ],
                "summary": {
                    "total": 3,
                    "ready_for_analysis": 2,
                    "need_more_data": 1,
                    "by_criticality": {
                        "Critical": 1,
                        "High": 1,
                        "Medium": 1,
                        "Low": 0
                    },
                    "by_environment": {
                        "Production": 3,
                        "Development": 0,
                        "Staging": 0
                    }
                },
                "dataSource": "demo"
            }
        
        # Filter and transform assets that are applications or can be treated as applications
        applications = []
        app_id_counter = 1
        
        for asset in processed_assets_store:
            asset_type = get_field_value(asset, ["asset_type", "ci_type", "type", "sys_class_name"])
            asset_name = get_field_value(asset, ["asset_name", "name", "hostname", "ci_name"])
            
            # Only include assets that make sense for 6R analysis
            if asset_type in ["Application", "Server", "Database"]:
                # Determine application type
                app_type = "custom"
                if asset_type == "Application":
                    tech_stack = get_tech_stack(asset)
                    if any(tech in tech_stack.lower() for tech in ["sharepoint", "dynamics", "sap", "oracle"]):
                        app_type = "commercial"
                elif asset_type == "Server":
                    # Servers can be treated as infrastructure applications
                    app_type = "infrastructure"
                elif asset_type == "Database":
                    # Databases can be treated as data applications  
                    app_type = "database"
                
                # Calculate complexity score
                complexity_score = 5  # Default medium
                if asset_type == "Application":
                    complexity_score = 6
                elif asset_type == "Database":
                    complexity_score = 7
                elif asset_type == "Server":
                    complexity_score = 4
                
                # Assess 6R readiness
                sixr_ready = assess_6r_readiness(asset_type, asset)
                
                # Map complexity assessment to score
                migration_complexity = get_field_value(asset, ["migration_complexity"])
                if migration_complexity == "High":
                    complexity_score = min(complexity_score + 2, 10)
                elif migration_complexity == "Low":
                    complexity_score = max(complexity_score - 2, 1)
                
                application = {
                    "id": app_id_counter,
                    "name": asset_name or f"Asset_{app_id_counter}",
                    "description": f"{asset_type} - {get_tech_stack(asset)}",
                    "techStack": get_tech_stack(asset),
                    "department": get_field_value(asset, ["business_owner", "department", "owner", "responsible_party"]) or "Unknown",
                    "environment": get_field_value(asset, ["environment", "env", "stage", "tier"]) or "Unknown",
                    "criticality": get_field_value(asset, ["criticality", "business_criticality", "priority"]) or "Medium",
                    "sixr_ready": sixr_ready,
                    "migration_complexity": migration_complexity or "Medium",
                    "application_type": app_type,
                    "business_unit": get_field_value(asset, ["business_owner", "department"]) or "IT Operations",
                    "complexity_score": complexity_score,
                    "original_asset_type": asset_type,
                    "asset_id": get_field_value(asset, ["ci_id", "asset_id", "id"]) or f"ASSET_{app_id_counter}"
                }
                
                applications.append(application)
                app_id_counter += 1
        
        # Calculate summary statistics
        total = len(applications)
        ready_count = len([app for app in applications if app["sixr_ready"] == "Ready"])
        need_data_count = total - ready_count
        
        criticality_counts = {}
        environment_counts = {}
        
        for app in applications:
            crit = app["criticality"]
            env = app["environment"]
            criticality_counts[crit] = criticality_counts.get(crit, 0) + 1
            environment_counts[env] = environment_counts.get(env, 0) + 1
        
        return {
            "applications": applications,
            "summary": {
                "total": total,
                "ready_for_analysis": ready_count,
                "need_more_data": need_data_count,
                "by_criticality": criticality_counts,
                "by_environment": environment_counts
            },
            "dataSource": "live" if has_processed_data else "demo"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving applications for analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve applications: {str(e)}")

@router.post("/test-asset-classification")
async def test_asset_classification(test_data: Dict[str, Any]):
    """
    Test endpoint to verify asset type classification logic.
    """
    try:
        from app.api.v1.discovery import standardize_asset_type
        
        test_workload_types = test_data.get("test_workload_types", [])
        results = {}
        
        for workload_type in test_workload_types:
            classified_type = standardize_asset_type(workload_type, "", {})
            results[workload_type] = classified_type
            logger.info(f"Classification test: '{workload_type}' → '{classified_type}'")
        
        return {
            "status": "success",
            "classification_results": results,
            "message": "Asset type classification test completed"
        }
        
    except Exception as e:
        logger.error(f"Asset classification test failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Asset classification test failed"
        }

@router.post("/reprocess-assets")
async def reprocess_stored_assets():
    """
    Reprocess stored assets with updated classification logic.
    """
    try:
        global processed_assets_store
        
        if not processed_assets_store:
            return {
                "status": "no_data",
                "message": "No processed assets found to reprocess"
            }
        
        logger.info(f"Reprocessing {len(processed_assets_store)} stored assets with updated classification")
        
        # Reprocess each asset with updated classification
        reprocessed_count = 0
        for asset in processed_assets_store:
            # Get workload type for reclassification
            workload_type = get_field_value(asset, ['workload_type', 'workload type', 'asset_type', 'ci_type', 'type'])
            asset_name = get_field_value(asset, ['asset_name', 'hostname', 'name', 'ci_name', 'server_name'])
            
            # Apply enhanced classification
            old_type = asset.get('asset_type', 'Unknown')
            new_type = standardize_asset_type(workload_type, asset_name, asset)
            
            # Update asset type
            asset['asset_type'] = new_type
            asset['intelligent_asset_type'] = new_type
            
            if old_type != new_type:
                logger.info(f"Reclassified {asset_name}: {old_type} → {new_type} (workload: {workload_type})")
                reprocessed_count += 1
        
        # Count updated classifications
        applications = len([a for a in processed_assets_store if a.get('asset_type') == 'Application'])
        servers = len([a for a in processed_assets_store if a.get('asset_type') == 'Server'])
        databases = len([a for a in processed_assets_store if a.get('asset_type') == 'Database'])
        devices = len([a for a in processed_assets_store if a.get('asset_type') in ['Network Device', 'Storage Device', 'Security Device', 'Infrastructure Device', 'Virtualization Platform']])
        unknown = len([a for a in processed_assets_store if a.get('asset_type') == 'Unknown'])
        
        return {
            "status": "completed",
            "message": f"Reprocessed {reprocessed_count} assets with updated classifications",
            "reprocessed_count": reprocessed_count,
            "total_assets": len(processed_assets_store),
            "new_classification_summary": {
                "applications": applications,
                "servers": servers,
                "databases": databases,
                "devices": devices,
                "unknown": unknown
            }
        }
        
    except Exception as e:
        logger.error(f"Error reprocessing assets: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Asset reprocessing failed"
        }

@router.put("/assets/{asset_id}")
async def update_asset(asset_id: str, asset_data: Dict[str, Any]):
    """
    Update an individual asset in the inventory.
    """
    try:
        global processed_assets_store
        
        if not processed_assets_store:
            raise HTTPException(status_code=404, detail="No assets found")
        
        # Find the asset to update
        asset_found = False
        for i, asset in enumerate(processed_assets_store):
            asset_id_in_store = get_field_value(asset, ["ci_id", "asset_id", "id", "asset_name", "name", "hostname"])
            if asset_id_in_store == asset_id or f"ASSET_{i + 1}" == asset_id:
                # Update the asset with new data
                for key, value in asset_data.items():
                    # Map frontend field names to backend field names
                    if key == "name":
                        asset["asset_name"] = value
                        asset["name"] = value
                    elif key == "type":
                        asset["asset_type"] = value
                        asset["intelligent_asset_type"] = value
                    elif key == "applicationMapped":
                        asset["application_mapped"] = value
                    elif key == "ipAddress":
                        asset["ip_address"] = value
                    elif key == "operatingSystem":
                        asset["operating_system"] = value
                    elif key == "osVersion":
                        asset["os_version"] = value
                    elif key == "cpuCores":
                        asset["cpu_cores"] = value
                    elif key == "memoryGb":
                        asset["memory_gb"] = value
                    elif key == "storageGb":
                        asset["storage_gb"] = value
                    else:
                        # Direct mapping for other fields
                        asset[key] = value
                
                # Update timestamp
                asset["last_updated"] = datetime.now().isoformat()
                
                asset_found = True
                logger.info(f"Updated asset {asset_id}: {asset_data}")
                break
        
        if not asset_found:
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
        
        # Backup processed assets after successful update
        backup_processed_assets()
        
        return {
            "status": "success",
            "message": f"Asset {asset_id} updated successfully",
            "updated_fields": list(asset_data.keys())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update asset: {str(e)}")

@router.get("/test-json-parsing")
async def test_json_parsing_improvements():
    """
    Test endpoint to validate improved JSON parsing logic.
    """
    try:
        test_results = processor.crewai_service.test_json_parsing_improvements()
        return {
            "status": "completed",
            "message": "JSON parsing test completed",
            "results": test_results
        }
        
    except Exception as e:
        logger.error(f"Error testing JSON parsing: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "JSON parsing test failed"
        }

@router.get("/ai-parsing-analytics")
async def get_ai_parsing_analytics():
    """
    Get analytics on AI response parsing success rates and common issues.
    """
    try:
        # Get analytics from agent memory
        from app.services.memory import agent_memory
        
        # Get recent analysis experiences
        recent_analyses = agent_memory.get_recent_experiences(limit=50)
        
        # Count parsing successes vs failures
        parsing_stats = {
            "total_analyses": 0,
            "successful_parses": 0,
            "fallback_used": 0,
            "parsing_failures": 0,
            "common_issues": {},
            "success_rate": 0.0,
            "last_24h_success_rate": 0.0,
            "model_performance": {
                "avg_response_length": 0,
                "avg_parsing_time": 0,
                "most_common_asset_types": {}
            }
        }
        
        fallback_reasons = []
        asset_types = []
        
        for exp in recent_analyses:
            if exp.get("action") == "successful_analysis":
                parsing_stats["total_analyses"] += 1
                result = exp.get("result", {})
                
                if result.get("parsed") == True:
                    parsing_stats["successful_parses"] += 1
                elif result.get("fallback_used") == True:
                    parsing_stats["fallback_used"] += 1
                    if "parsing_error" in result:
                        error = result["parsing_error"]
                        fallback_reasons.append(error)
                else:
                    parsing_stats["parsing_failures"] += 1
                
                # Track asset types
                asset_type = result.get("asset_type_detected", "unknown")
                asset_types.append(asset_type)
        
        # Calculate success rate
        if parsing_stats["total_analyses"] > 0:
            parsing_stats["success_rate"] = (parsing_stats["successful_parses"] / parsing_stats["total_analyses"]) * 100
        
        # Count common issues
        from collections import Counter
        if fallback_reasons:
            parsing_stats["common_issues"] = dict(Counter(fallback_reasons).most_common(5))
        
        if asset_types:
            parsing_stats["model_performance"]["most_common_asset_types"] = dict(Counter(asset_types).most_common(5))
        
        # Add recommendations based on success rate
        recommendations = []
        if parsing_stats["success_rate"] < 80:
            recommendations.append("Consider adjusting LLM temperature settings for more structured output")
            recommendations.append("Review prompt engineering to emphasize JSON-only responses")
        
        if parsing_stats["fallback_used"] > parsing_stats["successful_parses"]:
            recommendations.append("High fallback usage detected - consider model fine-tuning")
        
        if parsing_stats["success_rate"] > 95:
            recommendations.append("Excellent parsing performance - system is operating optimally")
        
        return {
            "status": "success",
            "parsing_analytics": parsing_stats,
            "recommendations": recommendations,
            "robustness_indicators": {
                "parsing_resilience": "High" if parsing_stats["success_rate"] > 90 else "Medium" if parsing_stats["success_rate"] > 70 else "Low",
                "fallback_effectiveness": "Functioning" if parsing_stats["fallback_used"] > 0 else "Untested",
                "system_reliability": "Production Ready" if parsing_stats["success_rate"] > 85 else "Needs Improvement"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting AI parsing analytics: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to retrieve AI parsing analytics"
        }

@router.post("/chat-test")
async def chat_test(request: Dict[str, Any]):
    """
    Enhanced chat endpoint with app context and asset data awareness.
    """
    try:
        from app.services.multi_model_service import multi_model_service
        
        message = request.get("message", "Hello!")
        task_type = request.get("task_type", "chat")
        system_prompt = request.get("system_prompt")
        context = request.get("context", "")
        
        # Build enhanced context with current asset data
        global processed_assets_store
        
        # Get current asset summary for context
        asset_summary = {
            "total_assets": len(processed_assets_store),
            "applications": 0,
            "servers": 0,
            "databases": 0,
            "mapped_assets": 0,
            "environments": set(),
            "departments": set()
        }
        
        for asset in processed_assets_store:
            asset_type = get_field_value(asset, ["asset_type", "ci_type", "type"]).lower()
            if "application" in asset_type:
                asset_summary["applications"] += 1
            elif "server" in asset_type:
                asset_summary["servers"] += 1
            elif "database" in asset_type:
                asset_summary["databases"] += 1
            
            # Check if asset has application mapping
            app_mapped = get_field_value(asset, ["application_mapped", "app_mapped"])
            if app_mapped != "Unknown" and app_mapped:
                asset_summary["mapped_assets"] += 1
            
            # Collect environments and departments
            env = get_field_value(asset, ["environment", "env"])
            if env != "Unknown":
                asset_summary["environments"].add(env)
            
            dept = get_field_value(asset, ["department", "dept", "business_unit"])
            if dept != "Unknown":
                asset_summary["departments"].add(dept)
        
        # Convert sets to lists for JSON serialization
        asset_summary["environments"] = list(asset_summary["environments"])
        asset_summary["departments"] = list(asset_summary["departments"])
        
        # Enhanced context with actual app data
        enhanced_context = f"""
CURRENT SYSTEM CONTEXT:
- Asset Inventory: {asset_summary['total_assets']} total assets discovered
- Applications: {asset_summary['applications']} identified
- Servers: {asset_summary['servers']} discovered  
- Databases: {asset_summary['databases']} found
- Application Mapping: {asset_summary['mapped_assets']} assets mapped to applications
- Environments: {', '.join(asset_summary['environments'][:5])}
- Departments: {', '.join(asset_summary['departments'][:5])}

USER QUESTION CONTEXT: {context}
CURRENT DATA STATE: {'Live CMDB data loaded' if len(processed_assets_store) > 0 else 'Demo/sample data in use'}

When answering questions, reference this actual data context. For asset inventory questions, provide specific insights based on the numbers above.
"""
        
        # Enhanced system prompt with context awareness
        if system_prompt:
            full_system_prompt = f"{system_prompt}\n\n{enhanced_context}"
        else:
            full_system_prompt = f"""You are a specialized AI assistant for IT infrastructure migration and cloud transformation with full access to the current asset inventory data.

CURRENT ASSET CONTEXT:
{enhanced_context}

EXPERTISE AREAS:
- Asset inventory analysis (reference current data: {asset_summary['total_assets']} assets)
- Application dependency mapping ({asset_summary['mapped_assets']} currently mapped)
- 6R migration strategies for discovered assets
- Cloud migration planning based on current inventory
- Infrastructure modernization recommendations
- Cost optimization using actual asset data

RESPONSE GUIDELINES:
- Always reference actual asset numbers when relevant
- Provide specific recommendations based on current inventory state
- For inventory questions, use the real data context above
- Keep responses focused on migration and infrastructure
- Be specific and actionable, not generic

For off-topic questions, respond: "I'm specialized in IT migration and infrastructure. Based on your current inventory of {asset_summary['total_assets']} assets, how can I help you with migration planning or infrastructure analysis instead?"

Be specific and data-driven in your responses."""
        
        result = await multi_model_service.generate_response(
            prompt=message,
            task_type=task_type,
            system_message=full_system_prompt
        )
        
        return {
            "status": "success",
            "chat_response": result.get("response", "Hello there! How can I help you today? 😊"),
            "model_used": result.get("model_used", "gemma3_4b"),
            "timestamp": result.get("timestamp", datetime.now().isoformat()),
            "multi_model_service_available": True,
            "tokens_used": result.get("tokens_used", 0),
            "context_applied": True,
            "asset_context": asset_summary,
            "context_source": "live_data" if len(processed_assets_store) > 0 else "demo_data"
        }
        
    except Exception as e:
        logger.error(f"Error in chat test: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Chat test failed",
            "multi_model_service_available": False,
            "fallback_response": "I'm here to help with IT migration and infrastructure questions. Please try again!"
        } 

@router.get("/app-server-mappings")
async def get_app_server_mappings():
    """
    Get application to server dependency mappings.
    """
    try:
        global processed_assets_store
        
        if not processed_assets_store:
            # Return demo data if no processed data
            return {
                "applications": [
                    {
                        "id": "APP001",
                        "name": "HR_Payroll",
                        "description": "Human Resources Payroll System",
                        "servers": [
                            {
                                "id": "SRV001",
                                "name": "srv-hr-01",
                                "type": "Server",
                                "ipAddress": "192.168.1.10",
                                "operatingSystem": "Windows Server 2019",
                                "cpuCores": 8,
                                "memoryGb": 32,
                                "storageGb": 500,
                                "environment": "Production",
                                "role": "Application Server"
                            }
                        ]
                    }
                ],
                "summary": {
                    "total_applications": 1,
                    "total_servers": 1,
                    "unmapped_servers": 0
                },
                "dataSource": "demo"
            }
        
        # Build app-to-server mappings from processed data
        app_mappings = {}
        unmapped_servers = []
        
        for asset in processed_assets_store:
            asset_type = get_field_value(asset, ["asset_type", "intelligent_asset_type"])
            asset_name = get_field_value(asset, ["asset_name", "name", "hostname"])
            app_mapped = get_field_value(asset, ["application_mapped", "app_mapped"])
            
            if asset_type in ["Server", "Database"] and app_mapped != "Unknown":
                # Extract app name/ID from mapping
                app_name = app_mapped
                app_id = f"APP_{hash(app_name) % 10000}"  # Generate consistent ID
                
                if app_name not in app_mappings:
                    app_mappings[app_name] = {
                        "id": app_id,
                        "name": app_name,
                        "description": f"Application: {app_name}",
                        "servers": []
                    }
                
                # Add server to application
                server_info = {
                    "id": get_field_value(asset, ["ci_id", "asset_id", "id"]) or asset_name,
                    "name": asset_name,
                    "type": asset_type,
                    "ipAddress": get_field_value(asset, ["ip_address", "ip"]),
                    "operatingSystem": get_field_value(asset, ["operating_system", "os"]),
                    "cpuCores": asset.get("cpu_cores"),
                    "memoryGb": asset.get("memory_gb"),
                    "storageGb": asset.get("storage_gb"),
                    "environment": get_field_value(asset, ["environment", "env"]),
                    "workloadType": get_field_value(asset, ["workload_type", "workload type"]),
                    "role": get_field_value(asset, ["workload_type", "workload type", "role"])
                }
                app_mappings[app_name]["servers"].append(server_info)
                
            elif asset_type in ["Server", "Database"] and app_mapped == "Unknown":
                # Track unmapped servers
                unmapped_servers.append({
                    "id": get_field_value(asset, ["ci_id", "asset_id", "id"]) or asset_name,
                    "name": asset_name,
                    "type": asset_type,
                    "ipAddress": get_field_value(asset, ["ip_address", "ip"]),
                    "operatingSystem": get_field_value(asset, ["operating_system", "os"]),
                    "environment": get_field_value(asset, ["environment", "env"]),
                    "workloadType": get_field_value(asset, ["workload_type", "workload type"])
                })
        
        applications = list(app_mappings.values())
        
        return {
            "applications": applications,
            "unmapped_servers": unmapped_servers,
            "summary": {
                "total_applications": len(applications),
                "total_servers": sum(len(app["servers"]) for app in applications),
                "unmapped_servers": len(unmapped_servers)
            },
            "dataSource": "live"
        }
        
    except Exception as e:
        logger.error(f"Error retrieving app-server mappings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve mappings: {str(e)}")

@router.post("/app-server-mappings/{app_id}/add-server")
async def add_server_to_app(app_id: str, server_data: Dict[str, Any]):
    """
    Add a server to an application mapping.
    """
    try:
        global processed_assets_store
        
        server_id = server_data.get("server_id")
        if not server_id:
            raise HTTPException(status_code=400, detail="Server ID is required")
        
        # Find the server and update its application mapping
        for asset in processed_assets_store:
            asset_id = get_field_value(asset, ["ci_id", "asset_id", "id", "asset_name", "name"])
            if asset_id == server_id:
                asset["application_mapped"] = app_id
                asset["last_updated"] = datetime.now().isoformat()
                logger.info(f"Mapped server {server_id} to application {app_id}")
                break
        
        # Backup after mapping change
        backup_processed_assets()
        
        return {
            "status": "success",
            "message": f"Server {server_id} added to application {app_id}"
        }
        
    except Exception as e:
        logger.error(f"Error adding server to app: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add server: {str(e)}")
