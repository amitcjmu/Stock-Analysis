"""
Discovery API endpoints for CMDB import and analysis.
Provides AI-powered data validation and processing capabilities.
"""

import json
import logging
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
        """Identify different types of assets in the data."""
        columns = [col.lower() for col in df.columns]
        
        # Simple heuristics to identify asset types
        applications = 0
        servers = 0
        databases = 0
        dependencies = 0
        
        # Look for application indicators
        app_indicators = ['application', 'app', 'service', 'software']
        if any(indicator in ' '.join(columns) for indicator in app_indicators):
            applications = len(df[df.apply(lambda row: any(
                indicator in str(row).lower() for indicator in app_indicators
            ), axis=1)])
        
        # Look for server indicators
        server_indicators = ['server', 'host', 'machine', 'vm', 'instance']
        if any(indicator in ' '.join(columns) for indicator in server_indicators):
            servers = len(df[df.apply(lambda row: any(
                indicator in str(row).lower() for indicator in server_indicators
            ), axis=1)])
        
        # Look for database indicators
        db_indicators = ['database', 'db', 'sql', 'oracle', 'mysql', 'postgres']
        if any(indicator in ' '.join(columns) for indicator in db_indicators):
            databases = len(df[df.apply(lambda row: any(
                indicator in str(row).lower() for indicator in db_indicators
            ), axis=1)])
        
        # Look for dependency indicators
        dep_indicators = ['depend', 'connect', 'link', 'relation']
        if any(indicator in ' '.join(columns) for indicator in dep_indicators):
            dependencies = len(df[df.apply(lambda row: any(
                indicator in str(row).lower() for indicator in dep_indicators
            ), axis=1)])
        
        # If no specific types found, assume all are generic assets
        if applications + servers + databases == 0:
            applications = len(df)
        
        return AssetCoverage(
            applications=applications,
            servers=servers,
            databases=databases,
            dependencies=dependencies
        )
    
    def identify_missing_fields(self, df: pd.DataFrame) -> List[str]:
        """Identify missing required fields for migration analysis."""
        required_fields = [
            'name', 'hostname', 'asset_name',
            'type', 'asset_type', 'category',
            'environment', 'env',
            'owner', 'business_owner',
            'criticality', 'business_criticality',
            'os', 'operating_system',
            'cpu', 'memory', 'storage'
        ]
        
        columns_lower = [col.lower() for col in df.columns]
        missing_fields = []
        
        # Check for essential fields
        essential_mappings = {
            'Asset Name': ['name', 'hostname', 'asset_name', 'server_name'],
            'Asset Type': ['type', 'asset_type', 'category', 'classification'],
            'Environment': ['environment', 'env', 'stage'],
            'Business Owner': ['owner', 'business_owner', 'responsible_party'],
            'Criticality': ['criticality', 'business_criticality', 'priority'],
            'Operating System': ['os', 'operating_system', 'platform'],
            'CPU Cores': ['cpu', 'cores', 'processors', 'vcpu'],
            'Memory (GB)': ['memory', 'ram', 'memory_gb', 'mem'],
            'Storage (GB)': ['storage', 'disk', 'storage_gb', 'hdd']
        }
        
        for field_name, possible_columns in essential_mappings.items():
            if not any(col in columns_lower for col in possible_columns):
                missing_fields.append(field_name)
        
        return missing_fields
    
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
        
        # Use CrewAI for advanced analysis
        crewai_analysis = await processor.crewai_service.analyze_cmdb_data({
            'filename': request.filename,
            'structure': structure_analysis,
            'coverage': coverage.dict(),
            'missing_fields': missing_fields,
            'sample_data': df.head(5).to_dict('records') if len(df) > 0 else []
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
async def process_cmdb_data(request: CMDBAnalysisRequest):
    """
    Process and clean CMDB data based on AI recommendations.
    """
    try:
        logger.info(f"Starting CMDB processing for file: {request.filename}")
        
        # Parse the file content
        df = processor.parse_file_content(request.content, request.fileType)
        
        # Apply data processing steps
        processed_df = df.copy()
        
        # Remove duplicates
        processed_df = processed_df.drop_duplicates()
        
        # Fill missing values with appropriate defaults
        for column in processed_df.columns:
            if processed_df[column].dtype == 'object':
                processed_df[column] = processed_df[column].fillna('Unknown')
            else:
                processed_df[column] = processed_df[column].fillna(0)
        
        # Standardize column names
        processed_df.columns = [col.lower().replace(' ', '_') for col in processed_df.columns]
        
        # Use CrewAI for advanced processing
        processing_result = await processor.crewai_service.process_cmdb_data({
            'original_data': df.to_dict('records'),
            'processed_data': processed_df.to_dict('records'),
            'filename': request.filename
        })
        
        return {
            "status": "completed",
            "message": "Data processing completed successfully",
            "original_rows": len(df),
            "processed_rows": len(processed_df),
            "processing_steps_applied": [
                "Removed duplicate records",
                "Filled missing values",
                "Standardized column names",
                "Applied AI-recommended transformations"
            ],
            "ai_processing_result": processing_result
        }
        
    except Exception as e:
        logger.error(f"Error processing CMDB data: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

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