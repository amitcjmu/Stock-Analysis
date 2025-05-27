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
        
        # Calculate data quality score
        null_percentage = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        duplicate_percentage = (df.duplicated().sum() / len(df)) * 100
        
        quality_score = max(0, 100 - null_percentage - duplicate_percentage)
        analysis['quality_score'] = int(quality_score)
        
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
        """Identify missing required fields based on asset type context and learned patterns."""
        columns_lower = [col.lower() for col in df.columns]
        missing_fields = []
        
        # Determine primary asset type
        coverage = self.identify_asset_types(df)
        primary_type = 'application'
        if coverage.servers > coverage.applications and coverage.servers > coverage.databases:
            primary_type = 'server'
        elif coverage.databases > coverage.applications and coverage.databases > coverage.servers:
            primary_type = 'database'
        
        # Get learned field mappings from agent memory if available
        learned_mappings = self._get_learned_field_mappings()
        
        # Asset-type-specific field requirements with enhanced mappings
        if primary_type == 'application':
            essential_mappings = {
                'Asset Name': ['name', 'application_name', 'service_name', 'business_service', 'asset_name'],
                'Asset Type': ['type', 'asset_type', 'ci_type', 'classification'],
                'Environment': ['environment', 'env', 'stage', 'tier'],
                'Business Owner': ['owner', 'business_owner', 'application_owner', 'responsible_party'],
                'Criticality': ['criticality', 'business_criticality', 'priority', 'importance'],
                'Version': ['version', 'release', 'build'],
                'Dependencies': ['related_ci', 'depends_on', 'relationships']
            }
        elif primary_type == 'server':
            essential_mappings = {
                'Asset Name': ['name', 'hostname', 'server_name', 'computer_name', 'asset_name'],
                'Asset Type': ['type', 'asset_type', 'ci_type', 'classification'],
                'Environment': ['environment', 'env', 'stage'],
                'Business Owner': ['owner', 'business_owner', 'responsible_party'],
                'Criticality': ['criticality', 'business_criticality', 'priority'],
                'Operating System': ['os', 'operating_system', 'platform', 'os_version'],
                'CPU Cores': ['cpu', 'cores', 'processors', 'vcpu', 'cpu_cores'],
                'Memory (GB)': ['memory', 'ram', 'memory_gb', 'mem', 'ram_gb'],  # Added ram_gb
                'IP Address': ['ip_address', 'ip', 'network_address']
            }
        else:  # database
            essential_mappings = {
                'Asset Name': ['name', 'database_name', 'instance_name', 'asset_name'],
                'Asset Type': ['type', 'asset_type', 'ci_type', 'db_type'],
                'Environment': ['environment', 'env', 'stage'],
                'Business Owner': ['owner', 'business_owner', 'dba_owner'],
                'Criticality': ['criticality', 'business_criticality', 'priority'],
                'Database Version': ['version', 'db_version', 'release'],
                'Host Server': ['host', 'server', 'hostname'],
                'Port': ['port', 'db_port', 'connection_port']
            }
        
        # Apply learned mappings to enhance field detection
        if learned_mappings:
            for field_name, possible_columns in essential_mappings.items():
                if field_name in learned_mappings:
                    # Add learned field variations
                    enhanced_columns = list(set(possible_columns + learned_mappings[field_name]))
                    essential_mappings[field_name] = enhanced_columns
        
        # Check for missing essential fields
        for field_name, possible_columns in essential_mappings.items():
            if not any(col in columns_lower for col in possible_columns):
                missing_fields.append(field_name)
        
        return missing_fields
    
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
        if analysis['duplicate_rows'] > 0:
            processing_steps.append(f"Remove {analysis['duplicate_rows']} duplicate records")
        
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

# Initialize processor
processor = CMDBDataProcessor()

@router.post("/analyze-cmdb", response_model=CMDBAnalysisResponse)
async def analyze_cmdb_data(request: CMDBAnalysisRequest):
    """
    Analyze CMDB data using AI agents for validation and processing recommendations.
    """
    try:
        logger.info(f"Starting CMDB analysis for file: {request.filename}")
        
        # Parse the file content
        df = processor.parse_file_content(request.content, request.fileType)
        
        # Perform structural analysis
        structure_analysis = processor.analyze_data_structure(df)
        
        # Identify asset types
        coverage = processor.identify_asset_types(df)
        
        # Identify missing fields
        missing_fields = processor.identify_missing_fields(df)
        
        # Suggest processing steps
        processing_steps = processor.suggest_processing_steps(df, structure_analysis)
        
        # Determine primary asset type for context
        primary_type = 'application'
        if coverage.servers > coverage.applications and coverage.servers > coverage.databases:
            primary_type = 'server'
        elif coverage.databases > coverage.applications and coverage.databases > coverage.servers:
            primary_type = 'database'
        
        # Use CrewAI for advanced analysis with asset type context
        crewai_analysis = await processor.crewai_service.analyze_cmdb_data({
            'filename': request.filename,
            'structure': structure_analysis,
            'coverage': coverage.dict(),
            'missing_fields': missing_fields,
            'sample_data': df.head(5).to_dict('records') if len(df) > 0 else [],
            'primary_asset_type': primary_type,
            'asset_type_context': {
                'applications': coverage.applications,
                'servers': coverage.servers,
                'databases': coverage.databases,
                'dependencies': coverage.dependencies
            }
        })
        
        # Combine AI analysis with structural analysis
        ai_issues = crewai_analysis.get('issues', [])
        ai_recommendations = crewai_analysis.get('recommendations', [])
        
        # Create comprehensive issues list
        issues = []
        if structure_analysis['quality_score'] < 80:
            issues.append(f"Data quality score is {structure_analysis['quality_score']}% - below recommended 80%")
        if structure_analysis['duplicate_rows'] > 0:
            issues.append(f"Found {structure_analysis['duplicate_rows']} duplicate records")
        if missing_fields:
            issues.append(f"Missing {len(missing_fields)} essential fields for migration analysis")
        
        issues.extend(ai_issues)
        
        # Create comprehensive recommendations
        recommendations = [
            "Validate data accuracy with business stakeholders",
            "Implement data governance standards",
            "Establish regular data quality monitoring"
        ]
        recommendations.extend(ai_recommendations)
        
        # Determine if ready for import
        ready_for_import = (
            structure_analysis['quality_score'] >= 70 and
            len(missing_fields) <= 3 and
            structure_analysis['duplicate_rows'] < len(df) * 0.1
        )
        
        # Create preview data
        preview = df.head(10).to_dict('records') if len(df) > 0 else []
        
        response = CMDBAnalysisResponse(
            status="completed",
            dataQuality=DataQualityResult(
                score=structure_analysis['quality_score'],
                issues=issues,
                recommendations=recommendations
            ),
            coverage=coverage,
            missingFields=missing_fields,
            requiredProcessing=processing_steps,
            readyForImport=ready_for_import,
            preview=preview
        )
        
        logger.info(f"CMDB analysis completed for {request.filename}")
        return response
        
    except Exception as e:
        logger.error(f"Error analyzing CMDB data: {e}")
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
        
        # Apply data processing steps
        processed_df = df.copy()
        
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
        
        # Use CrewAI for advanced processing validation
        processing_result = await processor.crewai_service.process_cmdb_data({
            'original_data': request.data,
            'processed_data': processed_df.to_dict('records'),
            'filename': request.filename,
            'project_info': request.projectInfo
        })
        
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
        
        # Process user corrections
        corrections = request.userCorrections
        asset_type_override = request.assetTypeOverride
        
        # Re-analyze with user feedback
        feedback_context = {
            'filename': request.filename,
            'original_analysis': request.originalAnalysis,
            'user_corrections': corrections,
            'asset_type_override': asset_type_override,
            'feedback_timestamp': datetime.now().isoformat()
        }
        
        # Use CrewAI to learn from feedback
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
        
        logger.info(f"User feedback processed for {request.filename}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing user feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Feedback processing failed: {str(e)}")

# In-memory storage for processed assets (in production, this would be a database)
processed_assets_store = []

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
                
                # Standardize asset data format with flexible field mapping
                formatted_asset = {
                    "id": _get_field_value(asset, ["ci_id", "asset_id", "id", "asset_name", "name"]) or f"ASSET_{len(formatted_assets) + 1}",
                    "type": _standardize_asset_type(asset_type, asset_name),
                    "name": asset_name,
                    "techStack": _get_tech_stack(asset),
                    "department": _get_field_value(asset, ["business_owner", "department", "owner", "responsible_party", "assigned_to"]),
                    "status": "Discovered",
                    "environment": _get_field_value(asset, ["environment", "env", "stage", "tier"]),
                    "criticality": _get_field_value(asset, ["criticality", "business_criticality", "priority", "importance"]),
                    "ipAddress": _get_field_value(asset, ["ip_address", "ip", "network_address", "host_ip"]),
                    "operatingSystem": _get_field_value(asset, ["operating_system", "os", "platform", "os_name"]),
                    "cpuCores": _get_field_value(asset, ["cpu_cores", "cpu", "cores", "processors", "vcpu"]),
                    "memoryGb": _get_field_value(asset, ["memory_gb", "memory", "ram", "ram_gb", "mem"]),
                    "storageGb": _get_field_value(asset, ["storage_gb", "storage", "disk", "disk_gb", "hdd"])
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
        
        # Calculate summary statistics
        summary = {
            "total": len(formatted_assets),
            "applications": len([a for a in formatted_assets if a["type"] == "Application"]),
            "servers": len([a for a in formatted_assets if a["type"] == "Server"]),
            "databases": len([a for a in formatted_assets if a["type"] == "Database"]),
            "discovered": len([a for a in formatted_assets if a["status"] == "Discovered"]),
            "pending": len([a for a in formatted_assets if a["status"] == "Pending"])
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

def _standardize_asset_type(asset_type: str, asset_name: str = "") -> str:
    """Standardize asset type names using both type and name fields."""
    if not asset_type and not asset_name:
        return "Unknown"
    
    # Combine type and name for better detection
    combined_text = f"{asset_type or ''} {asset_name or ''}".lower()
    
    # Database detection (check name patterns first for better accuracy)
    if any(keyword in combined_text for keyword in ["database", "db-", "-db", "sql", "oracle", "mysql", "postgres", "mongodb", "redis"]):
        return "Database"
    # Application detection
    elif any(keyword in combined_text for keyword in ["application", "app-", "-app", "service", "software", "portal", "system", "platform"]):
        return "Application"
    # Server detection (most generic, check last)
    elif any(keyword in combined_text for keyword in ["server", "srv-", "-srv", "host", "machine", "vm", "computer", "node"]):
        return "Server"
    # Network detection
    elif any(keyword in combined_text for keyword in ["network", "switch", "router", "firewall", "gateway"]):
        return "Network"
    else:
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
    
    # Operating System
    os_info = _get_field_value(asset, ["operating_system", "os", "platform", "os_name"])
    if os_info != "Unknown":
        tech_components.append(os_info)
    
    # Version information
    version = _get_field_value(asset, ["version", "release", "app_version", "software_version"])
    if version != "Unknown":
        tech_components.append(f"v{version}")
    
    # Database specific
    db_version = _get_field_value(asset, ["database_version", "db_version", "db_release"])
    if db_version != "Unknown":
        tech_components.append(db_version)
    
    # Platform information
    platform = _get_field_value(asset, ["platform", "technology", "framework"])
    if platform != "Unknown" and platform not in tech_components:
        tech_components.append(platform)
    
    # If no tech stack info found, use asset type
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
            headers.append({"key": "operatingSystem", "label": "Operating System", "description": "Server operating system"})
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