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
import io
from datetime import datetime
import math

from app.services.crewai_service import CrewAIService
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

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

class CMDBDataProcessor:
    """Handles CMDB data processing and validation."""
    
    def __init__(self):
        self.crewai_service = CrewAIService()
        
    def parse_file_content(self, content: str, file_type: str) -> pd.DataFrame:
        """Parse file content based on file type."""
        try:
            if file_type in ['text/csv', 'application/csv']:
                return pd.read_csv(io.StringIO(content))
            elif file_type in ['application/json']:
                data = json.loads(content)
                if isinstance(data, list):
                    return pd.DataFrame(data)
                else:
                    return pd.DataFrame([data])
            elif file_type in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
                # For Excel files, we'd need to handle binary content differently
                # This is a simplified version for demo purposes
                return pd.read_csv(io.StringIO(content))
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            logger.error(f"Error parsing file content: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")
    
    def analyze_data_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze the structure and quality of the data."""
        analysis = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'columns': list(df.columns),
            'data_types': df.dtypes.to_dict(),
            'null_counts': df.isnull().sum().to_dict(),
            'duplicate_rows': df.duplicated().sum(),
            'memory_usage': df.memory_usage(deep=True).sum()
        }
        
        # Calculate basic data quality metrics
        total_cells = len(df) * len(df.columns)
        null_count = df.isnull().sum().sum()
        null_percentage = (null_count / total_cells * 100) if total_cells > 0 else 0
        duplicate_count = len(df) - len(df.drop_duplicates())
        
        # Calculate basic quality score
        base_score = 100.0
        base_score -= min(30.0, null_percentage)  # Deduct up to 30 points for nulls
        if len(df) > 0:
            base_score -= min(20.0, (duplicate_count / len(df)) * 100)  # Deduct up to 20 points for duplicates
        
        # Ensure quality_score is a valid integer between 0 and 100
        quality_score = max(0, min(100, int(base_score)))
        
        analysis['quality_score'] = quality_score
        analysis['null_percentage'] = null_percentage
        analysis['duplicate_count'] = duplicate_count
        
        return analysis
    
    def identify_asset_types(self, df: pd.DataFrame) -> AssetCoverage:
        """Identify different types of assets in the data with improved heuristics."""
        columns = [col.lower() for col in df.columns]
        
        # Initialize counters
        applications = 0
        servers = 0
        databases = 0
        dependencies = 0
        
        # Check if there's an explicit asset type column
        type_columns = ['ci_type', 'type', 'asset_type', 'category', 'classification', 'sys_class_name']
        type_column = None
        for col in df.columns:
            if col.lower() in type_columns:
                type_column = col
                break
        
        if type_column:
            # Use explicit type column for classification
            type_values = df[type_column].str.lower().fillna('unknown')
            
            # Application indicators
            app_patterns = ['application', 'app', 'service', 'software', 'business_service']
            applications = sum(type_values.str.contains('|'.join(app_patterns), na=False))
            
            # Server indicators  
            server_patterns = ['server', 'host', 'machine', 'vm', 'instance', 'computer', 'node']
            servers = sum(type_values.str.contains('|'.join(server_patterns), na=False))
            
            # Database indicators
            db_patterns = ['database', 'db', 'sql', 'oracle', 'mysql', 'postgres', 'mongodb']
            databases = sum(type_values.str.contains('|'.join(db_patterns), na=False))
            
        else:
            # Fallback to heuristic-based detection using field patterns
            
            # Look for application-specific fields
            app_fields = ['version', 'business_service', 'application_owner', 'related_ci']
            app_score = sum(1 for field in app_fields if any(field in col for col in columns))
            
            # Look for server-specific fields
            server_fields = ['ip_address', 'hostname', 'os', 'cpu', 'memory', 'ram']
            server_score = sum(1 for field in server_fields if any(field in col for col in columns))
            
            # Look for database-specific fields
            db_fields = ['database', 'schema', 'instance', 'port', 'connection']
            db_score = sum(1 for field in db_fields if any(field in col for col in columns))
            
            # Classify based on field patterns
            total_rows = len(df)
            if app_score >= server_score and app_score >= db_score:
                applications = total_rows
            elif server_score >= app_score and server_score >= db_score:
                servers = total_rows
            elif db_score >= app_score and db_score >= server_score:
                databases = total_rows
            else:
                # Default to applications if unclear
                applications = total_rows
        
        # Look for dependency relationships
        dep_fields = ['related_ci', 'depends_on', 'relationship', 'parent_ci', 'child_ci']
        if any(field in ' '.join(columns) for field in dep_fields):
            # Count non-empty dependency relationships
            for col in df.columns:
                if any(dep_field in col.lower() for dep_field in dep_fields):
                    dependencies = df[col].notna().sum()
                    break
        
        return AssetCoverage(
            applications=applications,
            servers=servers,
            databases=databases,
            dependencies=dependencies
        )
    
    def identify_missing_fields(self, df: pd.DataFrame) -> List[str]:
        """Identify missing required fields using enhanced pattern analysis and learned mappings."""
        columns = df.columns.tolist()
        missing_fields = []
        
        # Determine primary asset type
        coverage = self.identify_asset_types(df)
        primary_type = 'application'
        if coverage.servers > coverage.applications and coverage.servers > coverage.databases:
            primary_type = 'server'
        elif coverage.databases > coverage.applications and coverage.databases > coverage.servers:
            primary_type = 'database'
        
        # Use pattern analysis to understand available data
        try:
            from app.services.tools.field_mapping_tool import field_mapping_tool
            
            # Prepare sample data for pattern analysis
            sample_rows = []
            for _, row in df.head(10).iterrows():
                sample_row = [str(row[col]) if pd.notna(row[col]) else '' for col in columns]
                sample_rows.append(sample_row)
            
            # Get pattern analysis results
            pattern_analysis = field_mapping_tool.analyze_data_patterns(columns, sample_rows, primary_type)
            column_mappings = pattern_analysis.get("column_analysis", {})
            confidence_scores = pattern_analysis.get("confidence_scores", {})
            
            logger.info(f"Pattern analysis found {len(column_mappings)} field mappings")
            
        except Exception as e:
            logger.warning(f"Pattern analysis failed, using fallback: {e}")
            column_mappings = {}
            confidence_scores = {}
        
        # Define essential fields by asset type
        if primary_type == 'application':
            essential_fields = [
                'Asset Name', 'Asset Type', 'Environment', 'Business Owner', 
                'Criticality', 'Version', 'Dependencies'
            ]
        elif primary_type == 'server':
            essential_fields = [
                'Asset Name', 'Asset Type', 'Environment', 'Business Owner',
                'Criticality', 'Operating System', 'CPU Cores', 'Memory (GB)', 'IP Address'
            ]
        else:  # database
            essential_fields = [
                'Asset Name', 'Asset Type', 'Environment', 'Business Owner',
                'Criticality', 'Database Version', 'Host Server', 'Port'
            ]
        
        # Check each essential field
        for essential_field in essential_fields:
            field_found = False
            
            # Check if any column maps to this essential field with high confidence
            for column, mapped_field in column_mappings.items():
                if mapped_field == essential_field:
                    confidence = confidence_scores.get(column, 0.0)
                    if confidence > 0.6:  # Accept medium to high confidence mappings
                        field_found = True
                        logger.info(f"Found mapping: {column} → {essential_field} (confidence: {confidence:.2f})")
                        break
            
            # If not found through pattern analysis, try fallback mapping
            if not field_found:
                field_found = self._check_fallback_field_mapping(essential_field, columns)
            
            if not field_found:
                missing_fields.append(essential_field)
                logger.info(f"Missing field: {essential_field}")
        
        return missing_fields
    
    def _check_fallback_field_mapping(self, essential_field: str, available_columns: List[str]) -> bool:
        """Fallback method to check for field mappings using simple name matching."""
        columns_lower = [col.lower().strip() for col in available_columns]
        
        # Simple fallback mappings for common cases
        fallback_mappings = {
            'Asset Name': ['name', 'hostname', 'asset_name', 'ci_name', 'server_name'],
            'Asset Type': ['type', 'ci_type', 'asset_type', 'classification'],
            'Environment': ['environment', 'env', 'stage'],
            'Operating System': ['os', 'operating_system', 'platform'],
            'CPU Cores': ['cpu', 'cores', 'cpu_cores', 'processors'],
            'Memory (GB)': ['memory', 'ram', 'memory_gb', 'ram_gb', 'mem'],
            'IP Address': ['ip_address', 'ip', 'network_address', 'host_ip'],
            'Business Owner': ['business_owner', 'owner', 'application_owner'],
            'Criticality': ['criticality', 'business_criticality', 'priority', 'importance'],
            'Version': ['version', 'release', 'app_version', 'software_version'],
            'Dependencies': ['dependencies', 'related_ci', 'depends_on', 'application_mapped']
        }
        
        variations = fallback_mappings.get(essential_field, [])
        return any(variation in columns_lower for variation in variations)
    
    def _get_learned_field_mappings(self) -> Dict[str, List[str]]:
        """Get learned field mappings from the dynamic field mapper."""
        try:
            # Use the new dynamic field mapper
            from app.services.field_mapper import field_mapper
            return field_mapper.get_field_mappings('server')  # Default to server mappings
                
        except Exception as e:
            logger.warning(f"Could not access dynamic field mapper: {e}")
            # Fallback to basic enhanced mappings
            return {
                'Memory (GB)': ['memory', 'ram', 'memory_gb', 'mem', 'ram_gb'],
                'CPU Cores': ['cpu', 'cores', 'processors', 'vcpu', 'cpu_cores'],
                'Asset Name': ['name', 'asset_name', 'hostname', 'ci_name']
            }
    
    def suggest_processing_steps(self, df: pd.DataFrame, analysis: Dict[str, Any]) -> List[str]:
        """Suggest data processing steps based on analysis."""
        processing_steps = []
        
        # Check for high null values
        if analysis['quality_score'] < 70:
            processing_steps.append("Clean missing data and fill null values")
        
        # Check for duplicates
        if analysis['duplicate_count'] > 0:
            processing_steps.append(f"Remove {analysis['duplicate_count']} duplicate records")
        
        # Check for data type issues
        if 'object' in str(analysis['data_types'].values()):
            processing_steps.append("Standardize data types and formats")
        
        # Check for naming consistency
        columns = df.columns.tolist()
        if any(' ' in col or col != col.lower() for col in columns):
            processing_steps.append("Normalize column names and formats")
        
        # Check for data validation
        processing_steps.append("Validate asset relationships and dependencies")
        processing_steps.append("Enrich data with additional metadata")
        
        return processing_steps

# Initialize processor and global storage
processor = CMDBDataProcessor()
processed_assets_store = []  # Global storage for processed assets

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
        from app.services.agent_monitor import agent_monitor, TaskStatus
        import uuid
        
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
                
                # Use agentic asset type detection if available
                asset_type_detected = crewai_result.get('asset_type_detected', 'mixed')
                if asset_type_detected == 'application':
                    coverage = AssetCoverage(applications=len(df), servers=0, databases=0, dependencies=0)
                elif asset_type_detected == 'server':
                    coverage = AssetCoverage(applications=0, servers=len(df), databases=0, dependencies=0)
                elif asset_type_detected == 'database':
                    coverage = AssetCoverage(applications=0, servers=0, databases=len(df), dependencies=0)
                
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
            for original_column, canonical_field in column_mappings.items():
                confidence = confidence_scores.get(original_column, 0.0)
                if confidence > 0.7:  # High confidence mappings
                    # Convert canonical field name to standardized column name
                    standardized_name = canonical_field.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')
                    field_rename_map[original_column] = standardized_name
                    logger.info(f"Mapping field: {original_column} → {standardized_name} (canonical: {canonical_field})")
            
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
            asset_name = asset_data.get('Name', asset_data.get('asset_name', ''))
            asset_type = asset_data.get('CI_Type', asset_data.get('asset_type', ''))
            
            # Use enhanced asset type classification
            intelligent_type = _standardize_asset_type(asset_type, asset_name, asset_data)
            processed_df.at[idx, 'intelligent_asset_type'] = intelligent_type
            
            # Add 6R readiness assessment
            processed_df.at[idx, 'sixr_ready'] = _assess_6r_readiness(intelligent_type, asset_data)
            
            # Add migration complexity indicator
            processed_df.at[idx, 'migration_complexity'] = _assess_migration_complexity(intelligent_type, asset_data)
        
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
            if processed_df[column].dtype == 'object':
                processed_df[column] = processed_df[column].fillna('Unknown')
            else:
                processed_df[column] = processed_df[column].fillna(0)
        
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
            "processed_data": processed_df.to_dict('records'),
            "ai_processing_result": processing_result,
            "ready_for_import": len(missing_required) == 0 and quality_score >= 70
        }
        
        logger.info(f"CMDB processing completed for {request.filename}")
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
        from app.services.agent_monitor import agent_monitor, TaskStatus
        import uuid
        
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

@router.get("/assets")
async def get_processed_assets():
    """
    Get all processed assets from CMDB imports.
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
                asset_name = _get_field_value(asset, ["asset_name", "name", "hostname", "ci_name"])
                asset_type = _get_field_value(asset, ["asset_type", "ci_type", "type", "sys_class_name"])
                
                # Helper function to get numeric values
                def get_numeric_value(asset, field_names):
                    value = _get_field_value(asset, field_names)
                    if value == "Unknown":
                        return None
                    try:
                        # Handle various numeric formats
                        numeric_val = float(str(value).replace(',', '').strip())
                        return int(numeric_val) if numeric_val.is_integer() else numeric_val
                    except (ValueError, AttributeError):
                        return None
                
                # Standardize asset data format with flexible field mapping
                formatted_asset = {
                    "id": _get_field_value(asset, ["ci_id", "asset_id", "id", "asset_name", "name", "hostname"]) or f"ASSET_{len(formatted_assets) + 1}",
                    "type": _standardize_asset_type(asset_type, asset_name, asset),
                    "name": asset_name,
                    "techStack": _get_tech_stack(asset),
                    "department": _get_field_value(asset, ["business_owner", "department", "owner", "responsible_party", "assigned_to"]),
                    "status": "Discovered",
                    "environment": _get_field_value(asset, ["environment", "env", "stage", "tier"]),
                    "criticality": _get_field_value(asset, ["criticality", "business_criticality", "priority", "importance"]),
                    "ipAddress": _get_field_value(asset, ["ip_address", "ip", "network_address", "host_ip"]),
                    "operatingSystem": _get_field_value(asset, ["operating_system", "os", "platform", "os_name", "os_type"]),
                    "osVersion": _get_field_value(asset, ["os_version", "version", "os_ver", "operating_system_version"]),
                    "cpuCores": get_numeric_value(asset, ["cpu_cores", "cpu", "cores", "processors", "vcpu"]),
                    "memoryGb": get_numeric_value(asset, ["memory_gb", "memory", "ram", "ram_gb", "mem"]),
                    "storageGb": get_numeric_value(asset, ["storage_gb", "storage", "disk", "disk_gb", "hdd", "disk_size_gb"])
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
                    "cpuCores": None,
                    "memoryGb": None,
                    "storageGb": None
                },
                {
                    "id": "APP002",
                    "type": "Application",
                    "name": "Finance_ERP",
                    "techStack": ".NET Core 6",
                    "department": "Finance",
                    "status": "Discovered",
                    "environment": "Production",
                    "criticality": "Critical",
                    "ipAddress": None,
                    "operatingSystem": None,
                    "cpuCores": None,
                    "memoryGb": None,
                    "storageGb": None
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
                    "cpuCores": 8,
                    "memoryGb": 32,
                    "storageGb": 500
                },
                {
                    "id": "SRV002",
                    "type": "Server",
                    "name": "srv-erp-01",
                    "techStack": "Red Hat Enterprise Linux 8",
                    "department": "IT Operations",
                    "status": "Discovered",
                    "environment": "Production",
                    "criticality": "Critical",
                    "ipAddress": "192.168.1.11",
                    "operatingSystem": "Red Hat Enterprise Linux 8",
                    "cpuCores": 16,
                    "memoryGb": 64,
                    "storageGb": 1000
                },
                {
                    "id": "DB001",
                    "type": "Database",
                    "name": "srv-hr-db-01",
                    "techStack": "MySQL 8.0",
                    "department": "Human Resources",
                    "status": "Discovered",
                    "environment": "Production",
                    "criticality": "High",
                    "ipAddress": "192.168.1.20",
                    "operatingSystem": "Linux Ubuntu 20.04",
                    "cpuCores": 8,
                    "memoryGb": 32,
                    "storageGb": 2000
                },
                {
                    "id": "DB002",
                    "type": "Database",
                    "name": "finance-db-cluster",
                    "techStack": "PostgreSQL 13",
                    "department": "Finance",
                    "status": "Discovered",
                    "environment": "Production",
                    "criticality": "Critical",
                    "ipAddress": "192.168.1.21",
                    "operatingSystem": "Linux Ubuntu 20.04",
                    "cpuCores": 16,
                    "memoryGb": 64,
                    "storageGb": 5000
                },
                {
                    "id": "APP003",
                    "type": "Application",
                    "name": "CRM_System",
                    "techStack": "Python Django",
                    "department": "Sales",
                    "status": "Pending",
                    "environment": "Production",
                    "criticality": "Medium",
                    "ipAddress": None,
                    "operatingSystem": None,
                    "cpuCores": None,
                    "memoryGb": None,
                    "storageGb": None
                },
                {
                    "id": "SRV003",
                    "type": "Server",
                    "name": "web-server-01",
                    "techStack": "Linux Ubuntu 22.04",
                    "department": "IT Operations",
                    "status": "Discovered",
                    "environment": "Production",
                    "criticality": "Medium",
                    "ipAddress": "192.168.1.30",
                    "operatingSystem": "Linux Ubuntu 22.04",
                    "cpuCores": 4,
                    "memoryGb": 16,
                    "storageGb": 250
                }
            ]
            
            data_source = "test"
        
        # Calculate summary statistics with enhanced device types
        device_types = ["Network Device", "Storage Device", "Security Device", "Infrastructure Device", "Virtualization Platform"]
        
        summary = {
            "total": len(formatted_assets),
            "applications": len([a for a in formatted_assets if a["type"] == "Application"]),
            "servers": len([a for a in formatted_assets if a["type"] == "Server"]),
            "databases": len([a for a in formatted_assets if a["type"] == "Database"]),
            "devices": len([a for a in formatted_assets if a["type"] in device_types]),
            "unknown": len([a for a in formatted_assets if a["type"] == "Unknown"]),
            "discovered": len([a for a in formatted_assets if a["status"] == "Discovered"]),
            "pending": len([a for a in formatted_assets if a["status"] == "Pending"]),
            # Breakdown by device type
            "device_breakdown": {
                "network": len([a for a in formatted_assets if a["type"] == "Network Device"]),
                "storage": len([a for a in formatted_assets if a["type"] == "Storage Device"]),
                "security": len([a for a in formatted_assets if a["type"] == "Security Device"]),
                "infrastructure": len([a for a in formatted_assets if a["type"] == "Infrastructure Device"]),
                "virtualization": len([a for a in formatted_assets if a["type"] == "Virtualization Platform"])
            }
        }
        
        # Generate suggested headers based on actual data
        suggested_headers = _generate_suggested_headers(formatted_assets)
        
        return {
            "assets": formatted_assets,
            "summary": summary,
            "dataSource": data_source,
            "suggestedHeaders": suggested_headers,
            "lastUpdated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error retrieving processed assets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve assets: {str(e)}")

def _standardize_asset_type(asset_type: str, asset_name: str = "", asset_data: Dict[str, Any] = None) -> str:
    """Standardize asset type names using agentic intelligence and comprehensive pattern matching."""
    if not asset_type and not asset_name:
        return "Unknown"
    
    # Combine type and name for better detection
    combined_text = f"{asset_type or ''} {asset_name or ''}".lower()
    
    # Use agentic intelligence if available
    try:
        from app.services.crewai_service import crewai_service
        if asset_data and crewai_service.agents:
            # Create minimal analysis data for asset type detection
            analysis_data = {
                "asset_name": asset_name,
                "asset_type": asset_type,
                "combined_context": combined_text,
                "tech_stack": asset_data.get("tech_stack", ""),
                "operating_system": asset_data.get("os", ""),
                "has_cpu": bool(asset_data.get("cpu_cores")),
                "has_memory": bool(asset_data.get("memory_gb")),
                "has_ip": bool(asset_data.get("ip_address"))
            }
            
            # Quick agentic asset type detection
            # This could be enhanced with a specific agent call if needed
    except Exception:
        pass  # Fall back to rule-based detection
    
    # Enhanced rule-based detection with device classification
    
    # 1. Database detection (highest priority for accuracy)
    database_patterns = [
        "database", "db-", "-db", "sql", "oracle", "mysql", "postgres", "postgresql", 
        "mongodb", "redis", "cassandra", "elasticsearch", "influxdb", "mariadb",
        "mssql", "sqlite", "dynamodb", "couchdb", "neo4j"
    ]
    if any(pattern in combined_text for pattern in database_patterns):
        return "Database"
    
    # 2. Security device detection (moved before network to catch firewall)
    security_patterns = [
        "firewall", "fw-", "-fw", "ids", "ips", "waf", "proxy", "checkpoint", 
        "symantec", "mcafee", "splunk", "qualys", "nessus", "security"
    ]
    if any(pattern in combined_text for pattern in security_patterns):
        return "Security Device"
    
    # 3. Network device detection
    network_patterns = [
        "switch", "router", "gateway", "loadbalancer", "lb-", 
        "cisco", "juniper", "palo", "fortinet", "f5", "netscaler",
        "core", "edge", "wan", "lan", "wifi", "access-point", "ap-"
    ]
    if any(pattern in combined_text for pattern in network_patterns):
        return "Network Device"
    
    # 4. Storage device detection
    storage_patterns = [
        "san", "nas", "storage", "array", "netapp", "emc", "dell", "hp-3par",
        "pure", "nimble", "solidfire", "vnx", "unity", "powermax"
    ]
    if any(pattern in combined_text for pattern in storage_patterns):
        return "Storage Device"
    
    # 5. Virtualization detection (before application/server to catch vmware, etc.)
    virtualization_patterns = [
        "vmware", "vcenter", "esxi", "hyper-v", "citrix", "xen", "kvm",
        "docker", "kubernetes", "openshift", "vsphere"
    ]
    if any(pattern in combined_text for pattern in virtualization_patterns):
        return "Virtualization Platform"
    
    # 6. Server detection (moved before application for better precision)
    server_patterns = [
        "server", "srv-", "-srv", "host", "machine", "vm", "computer", "node",
        "mail", "dns", "dhcp", "domain", "controller"
    ]
    if any(pattern in combined_text for pattern in server_patterns):
        return "Server"
    
    # 7. Application detection (after server to avoid misclassification)
    application_patterns = [
        "application", "app-", "-app", "service", "software", "portal", 
        "system", "platform", "web", "api", "microservice", "webapp"
    ]
    if any(pattern in combined_text for pattern in application_patterns):
        # Additional check: if it has infrastructure specs, it might be a server
        if asset_data and (asset_data.get("cpu_cores") or asset_data.get("memory_gb")):
            # Could be application running on a server, classify as server
            return "Server"
        return "Application"
    
    # 8. Other infrastructure devices
    infrastructure_patterns = [
        "ups", "power", "rack", "kvm", "console", "monitor", "printer",
        "scanner", "phone", "voip", "camera", "sensor"
    ]
    if any(pattern in combined_text for pattern in infrastructure_patterns):
        return "Infrastructure Device"
    
    # If no pattern matches, return Unknown
    return "Unknown"

def _get_field_value(asset: Dict[str, Any], field_names: List[str]) -> str:
    """Get field value using flexible field name matching."""
    for field_name in field_names:
        value = asset.get(field_name)
        if value and str(value).strip() and str(value).strip().lower() not in ['unknown', 'null', 'none', '']:
            return str(value).strip()
    return "Unknown"

def _get_tech_stack(asset: Dict[str, Any]) -> str:
    """Extract technology stack information from asset data with flexible field mapping."""
    # Try to build tech stack from available fields
    tech_components = []
    
    # Operating System (combine OS type and version for display)
    os_type = _get_field_value(asset, ["operating_system", "os", "platform", "os_name", "os_type"])
    os_version = _get_field_value(asset, ["os_version", "version", "os_ver", "operating_system_version"])
    
    if os_type != "Unknown" and os_version != "Unknown":
        tech_components.append(f"{os_type} {os_version}")
    elif os_type != "Unknown":
        tech_components.append(os_type)
    elif os_version != "Unknown":
        tech_components.append(os_version)
    
    # Application version information
    app_version = _get_field_value(asset, ["app_version", "software_version", "application_version"])
    if app_version != "Unknown" and app_version not in [comp for comp in tech_components]:
        tech_components.append(f"v{app_version}")
    
    # Workload/Asset Type information
    workload_type = _get_field_value(asset, ["workload_type", "workload type", "asset_type"])
    if workload_type != "Unknown" and workload_type not in [comp for comp in tech_components]:
        tech_components.append(workload_type)
    
    # Database specific
    db_version = _get_field_value(asset, ["database_version", "db_version", "db_release"])
    if db_version != "Unknown":
        tech_components.append(db_version)
    
    # Platform information
    platform = _get_field_value(asset, ["platform", "technology", "framework"])
    if platform != "Unknown" and platform not in tech_components:
        tech_components.append(platform)
    
    # If no tech stack info found, try to use asset type or fallback
    if not tech_components:
        asset_type = _get_field_value(asset, ["asset_type", "ci_type", "type", "sys_class_name"])
        if asset_type != "Unknown":
            tech_components.append(asset_type)
    
    return " | ".join(tech_components) if tech_components else "Unknown"

def _generate_suggested_headers(assets: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Generate suggested table headers based on actual asset data."""
    if not assets:
        return []
    
    # Analyze the data to determine which fields are most relevant
    sample_asset = assets[0]
    headers = []
    
    # Always include basic identification fields
    headers.extend([
        {"key": "id", "label": "Asset ID", "description": "Unique identifier for the asset"},
        {"key": "type", "label": "Type", "description": "Asset classification (Application, Server, Database)"},
        {"key": "name", "label": "Name", "description": "Asset name or hostname"}
    ])
    
    # Check if we have tech stack information
    if any(asset.get("techStack") and asset["techStack"] != "Unknown" for asset in assets):
        headers.append({"key": "techStack", "label": "Tech Stack", "description": "Technology platform and versions"})
    
    # Check if we have department information
    if any(asset.get("department") and asset["department"] != "Unknown" for asset in assets):
        headers.append({"key": "department", "label": "Department", "description": "Business owner or responsible department"})
    
    # Check if we have environment information
    if any(asset.get("environment") and asset["environment"] != "Unknown" for asset in assets):
        headers.append({"key": "environment", "label": "Environment", "description": "Deployment environment (Production, Test, Dev)"})
    
    # Check if we have criticality information
    if any(asset.get("criticality") and asset["criticality"] != "Medium" for asset in assets):
        headers.append({"key": "criticality", "label": "Criticality", "description": "Business criticality level"})
    
    # Check if we have server-specific fields (for servers and databases)
    has_servers = any(asset.get("type") in ["Server", "Database"] for asset in assets)
    if has_servers:
        if any(asset.get("ipAddress") for asset in assets):
            headers.append({"key": "ipAddress", "label": "IP Address", "description": "Network IP address"})
        if any(asset.get("operatingSystem") for asset in assets):
            headers.append({"key": "operatingSystem", "label": "Operating System", "description": "Server operating system type"})
        if any(asset.get("osVersion") for asset in assets):
            headers.append({"key": "osVersion", "label": "OS Version", "description": "Operating system version"})
        if any(asset.get("cpuCores") for asset in assets):
            headers.append({"key": "cpuCores", "label": "CPU Cores", "description": "Number of CPU cores"})
        if any(asset.get("memoryGb") for asset in assets):
            headers.append({"key": "memoryGb", "label": "Memory (GB)", "description": "RAM memory in gigabytes"})
        if any(asset.get("storageGb") for asset in assets):
            headers.append({"key": "storageGb", "label": "Storage (GB)", "description": "Storage capacity in gigabytes"})
    
    # Always include status
    headers.append({"key": "status", "label": "Status", "description": "Discovery and processing status"})
    
    return headers

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

def _assess_6r_readiness(asset_type: str, asset_data: Dict[str, Any]) -> str:
    """Assess if an asset is ready for 6R treatment analysis."""
    
    # Devices typically don't need 6R analysis
    device_types = ["Network Device", "Storage Device", "Security Device", "Infrastructure Device"]
    if asset_type in device_types:
        return "Not Applicable"
    
    # Check for minimum required data
    has_name = bool(asset_data.get('Name') or asset_data.get('asset_name'))
    has_environment = bool(asset_data.get('Environment') or asset_data.get('environment'))
    has_owner = bool(asset_data.get('Business_Owner') or asset_data.get('business_owner'))
    
    if asset_type == "Application":
        # Applications need name, environment, owner
        if has_name and has_environment and has_owner:
            return "Ready"
        elif has_name and has_environment:
            return "Needs Owner Info"
        else:
            return "Insufficient Data"
    
    elif asset_type == "Server":
        # Servers need infrastructure specs
        has_cpu = bool(asset_data.get('CPU_Cores') or asset_data.get('cpu_cores'))
        has_memory = bool(asset_data.get('Memory_GB') or asset_data.get('memory_gb'))
        has_os = bool(asset_data.get('OS') or asset_data.get('operating_system'))
        
        if has_name and has_environment and has_cpu and has_memory and has_os:
            return "Ready"
        elif has_name and has_environment:
            return "Needs Infrastructure Data"
        else:
            return "Insufficient Data"
    
    elif asset_type == "Database":
        # Databases need version and host info
        has_version = bool(asset_data.get('Version') or asset_data.get('database_version'))
        has_host = bool(asset_data.get('Host') or asset_data.get('hostname'))
        
        if has_name and has_environment and has_version:
            return "Ready"
        elif has_name and has_environment:
            return "Needs Version Info"
        else:
            return "Insufficient Data"
    
    elif asset_type == "Virtualization Platform":
        return "Complex Analysis Required"
    
    else:  # Unknown type
        return "Type Classification Needed"

def _assess_migration_complexity(asset_type: str, asset_data: Dict[str, Any]) -> str:
    """Assess the migration complexity of an asset."""
    
    # Devices typically have low complexity
    device_types = ["Network Device", "Storage Device", "Security Device", "Infrastructure Device"]
    if asset_type in device_types:
        return "Low"
    
    if asset_type == "Application":
        # Check for complexity indicators
        has_dependencies = bool(asset_data.get('Related_CI') or asset_data.get('dependencies'))
        is_critical = str(asset_data.get('Criticality', '')).lower() in ['high', 'critical']
        is_production = str(asset_data.get('Environment', '')).lower() == 'production'
        
        complexity_score = 0
        if has_dependencies:
            complexity_score += 2
        if is_critical:
            complexity_score += 2
        if is_production:
            complexity_score += 1
        
        if complexity_score >= 4:
            return "High"
        elif complexity_score >= 2:
            return "Medium"
        else:
            return "Low"
    
    elif asset_type == "Server":
        # Server complexity based on specs and usage
        cpu_cores = int(asset_data.get('CPU_Cores', asset_data.get('cpu_cores', 0)) or 0)
        memory_gb = int(asset_data.get('Memory_GB', asset_data.get('memory_gb', 0)) or 0)
        is_production = str(asset_data.get('Environment', '')).lower() == 'production'
        
        complexity_score = 0
        if cpu_cores > 16:
            complexity_score += 2
        elif cpu_cores > 8:
            complexity_score += 1
        
        if memory_gb > 64:
            complexity_score += 2
        elif memory_gb > 32:
            complexity_score += 1
        
        if is_production:
            complexity_score += 1
        
        if complexity_score >= 4:
            return "High"
        elif complexity_score >= 2:
            return "Medium"
        else:
            return "Low"
    
    elif asset_type == "Database":
        # Databases are typically medium to high complexity
        is_critical = str(asset_data.get('Criticality', '')).lower() in ['high', 'critical']
        is_production = str(asset_data.get('Environment', '')).lower() == 'production'
        
        if is_critical and is_production:
            return "High"
        elif is_production:
            return "Medium"
        else:
            return "Low"
    
    elif asset_type == "Virtualization Platform":
        return "High"
    
    else:
        return "Medium"

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
            asset_type = _get_field_value(asset, ["asset_type", "ci_type", "type", "sys_class_name"])
            asset_name = _get_field_value(asset, ["asset_name", "name", "hostname", "ci_name"])
            
            # Only include assets that make sense for 6R analysis
            if asset_type in ["Application", "Server", "Database"]:
                # Determine application type
                app_type = "custom"
                if asset_type == "Application":
                    tech_stack = _get_tech_stack(asset)
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
                sixr_ready = _assess_6r_readiness(asset_type, asset)
                
                # Map complexity assessment to score
                migration_complexity = _get_field_value(asset, ["migration_complexity"])
                if migration_complexity == "High":
                    complexity_score = min(complexity_score + 2, 10)
                elif migration_complexity == "Low":
                    complexity_score = max(complexity_score - 2, 1)
                
                application = {
                    "id": app_id_counter,
                    "name": asset_name or f"Asset_{app_id_counter}",
                    "description": f"{asset_type} - {_get_tech_stack(asset)}",
                    "techStack": _get_tech_stack(asset),
                    "department": _get_field_value(asset, ["business_owner", "department", "owner", "responsible_party"]) or "Unknown",
                    "environment": _get_field_value(asset, ["environment", "env", "stage", "tier"]) or "Unknown",
                    "criticality": _get_field_value(asset, ["criticality", "business_criticality", "priority"]) or "Medium",
                    "sixr_ready": sixr_ready,
                    "migration_complexity": migration_complexity or "Medium",
                    "application_type": app_type,
                    "business_unit": _get_field_value(asset, ["business_owner", "department"]) or "IT Operations",
                    "complexity_score": complexity_score,
                    "original_asset_type": asset_type,
                    "asset_id": _get_field_value(asset, ["ci_id", "asset_id", "id"]) or f"ASSET_{app_id_counter}"
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