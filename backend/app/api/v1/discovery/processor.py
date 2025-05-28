"""
CMDB Data Processor
Handles CMDB data processing and validation with agentic intelligence.
"""

import json
import logging
from typing import Dict, List, Any
import pandas as pd
import io
from datetime import datetime

from app.services.crewai_service import CrewAIService
from .models import AssetCoverage

logger = logging.getLogger(__name__)


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
            raise ValueError(f"Failed to parse file: {str(e)}")
    
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
        
        # Check if there's an explicit asset type column (including workload_type)
        type_columns = ['ci_type', 'type', 'asset_type', 'category', 'classification', 'sys_class_name', 'workload_type', 'workload type']
        type_column = None
        for col in df.columns:
            if col.lower().replace(' ', '_') in [tc.replace(' ', '_') for tc in type_columns]:
                type_column = col
                break
        
        if type_column:
            # Use explicit type column for classification
            type_values = df[type_column].str.lower().fillna('unknown')
            
            # Enhanced patterns for workload type detection
            # Application indicators (including workload-specific patterns)
            app_patterns = ['application', 'app', 'service', 'software', 'business_service', 'app server', 'application server', 'web server', 'api server']
            applications = sum(type_values.str.contains('|'.join(app_patterns), na=False))
            
            # Database indicators (including workload-specific patterns)
            db_patterns = ['database', 'db', 'sql', 'oracle', 'mysql', 'postgres', 'mongodb', 'db server', 'database server']
            databases = sum(type_values.str.contains('|'.join(db_patterns), na=False))
            
            # Server indicators (catch-all for generic servers)
            server_patterns = ['server', 'host', 'machine', 'vm', 'instance', 'computer', 'node']
            # Only count as generic servers if not already counted as app or db servers
            remaining_servers = len(df) - applications - databases
            
            # For workload type, we need to be more specific about what counts as a "generic server"
            if 'workload' in type_column.lower():
                # With workload type, count specific server types that aren't apps or databases
                generic_server_patterns = ['file server', 'print server', 'mail server', 'dns server', 'dhcp server', 'domain controller']
                servers = sum(type_values.str.contains('|'.join(generic_server_patterns), na=False))
                
                # Add any remaining unclassified items as servers
                unclassified = len(df) - applications - databases - servers
                if unclassified > 0:
                    servers += unclassified
            else:
                # For non-workload columns, use original server detection
                servers = sum(type_values.str.contains('|'.join(server_patterns), na=False))
            
            logger.info(f"Asset type detection from column '{type_column}': Apps={applications}, DBs={databases}, Servers={servers}")
            
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
        
        # Define essential fields by asset type (focused on migration assessment needs)
        if primary_type == 'application':
            essential_fields = [
                'Asset Name', 'Environment', 'Business Owner', 
                'Criticality'
            ]
        elif primary_type == 'server':
            essential_fields = [
                'Asset Name', 'Environment', 'Business Owner',
                'Criticality'
            ]
        elif primary_type == 'mixed':
            # For mixed asset types, focus on the most critical migration fields
            essential_fields = [
                'Asset Name', 'Environment', 'Business Owner',
                'Criticality'
            ]
        else:  # database
            essential_fields = [
                'Asset Name', 'Environment', 'Business Owner',
                'Criticality'
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
        
        # Simple fallback mappings for common cases (focused on migration assessment)
        fallback_mappings = {
            'Asset Name': ['name', 'hostname', 'asset_name', 'ci_name', 'server_name'],
            'Environment': ['environment', 'env', 'stage', 'tier'],
            'Business Owner': ['business_owner', 'owner', 'application_owner', 'app_owner', 'responsible_party', 'contact', 'primary_contact'],
            'Criticality': ['criticality', 'business_criticality', 'priority', 'importance', 'critical', 'business_priority']
        }
        
        variations = fallback_mappings.get(essential_field, [])
        return any(variation in columns_lower for variation in variations)
    
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