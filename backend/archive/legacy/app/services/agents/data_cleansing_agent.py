"""
Data Cleansing Agent - Enterprise Data Standardization and Bulk Processing Specialist
Performs intelligent data cleansing, bulk data population, and mass editing operations
"""

import time
import re
from typing import Dict, Any, List, Optional, Tuple, Set, Union
import pandas as pd
import numpy as np
from datetime import datetime, date
import logging
from collections import Counter, defaultdict

from .base_discovery_agent import BaseDiscoveryAgent, AgentResult

logger = logging.getLogger(__name__)

class DataCleansingAgent(BaseDiscoveryAgent):
    """
    Enterprise Data Standardization and Bulk Processing Specialist
    
    Applies intelligent data cleansing and standardization rules based on confirmed field mappings,
    performs bulk data population for missing values, and executes mass data edits based on user clarifications.
    """
    
    def __init__(self):
        super().__init__("Data Cleansing Agent", "data_cleansing_001")
        
        # Standardization patterns
        self.standardization_patterns = {
            'date_formats': [
                r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
                r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
                r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
                r'\d{1,2}/\d{1,2}/\d{4}',  # M/D/YYYY
            ],
            'ip_addresses': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            'mac_addresses': r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})',
            'phone_numbers': r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
            'email_addresses': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        }
        
        # Data type inference patterns
        self.data_type_patterns = {
            'boolean': ['yes', 'no', 'true', 'false', '1', '0', 'y', 'n'],
            'currency': r'[\$€£¥]\s*\d+\.?\d*',
            'percentage': r'\d+\.?\d*\s*%',
            'size_gb': r'\d+\.?\d*\s*(gb|mb|tb|gib|mib|tib)',
            'version': r'\d+\.\d+(\.\d+)?(\.\d+)?'
        }
        
        # Common value mappings for standardization
        self.value_mappings = {
            'environment': {
                'prod': 'Production',
                'production': 'Production',
                'prd': 'Production',
                'dev': 'Development',
                'development': 'Development',
                'test': 'Test',
                'testing': 'Test',
                'tst': 'Test',
                'staging': 'Staging',
                'stage': 'Staging',
                'stg': 'Staging',
                'uat': 'UAT',
                'qa': 'QA',
                'quality': 'QA'
            },
            'status': {
                'active': 'Active',
                'running': 'Active',
                'online': 'Active',
                'up': 'Active',
                'inactive': 'Inactive',
                'down': 'Inactive',
                'offline': 'Inactive',
                'stopped': 'Inactive',
                'retired': 'Retired',
                'decommissioned': 'Retired'
            },
            'criticality': {
                'high': 'High',
                'critical': 'High',
                'medium': 'Medium',
                'med': 'Medium',
                'low': 'Low',
                'minimal': 'Low'
            },
            'os_family': {
                'windows': 'Windows',
                'win': 'Windows',
                'linux': 'Linux',
                'unix': 'Unix',
                'aix': 'Unix',
                'solaris': 'Unix',
                'macos': 'macOS',
                'mac': 'macOS'
            }
        }
        
        # Bulk operation strategies
        self.bulk_strategies = {
            'pattern_inference': self._infer_from_patterns,
            'common_value': self._use_most_common_value,
            'contextual_inference': self._infer_from_context,
            'default_assignment': self._assign_default_value,
            'rule_based': self._apply_rules
        }
    
    def get_role(self) -> str:
        return "Enterprise Data Standardization and Bulk Processing Specialist"
    
    def get_goal(self) -> str:
        return "Apply intelligent data cleansing and standardization rules based on confirmed field mappings, perform bulk data population for missing values, and execute mass data edits based on user clarifications"
    
    def get_backstory(self) -> str:
        return ("You are a data quality expert who understands that clean data is the foundation of successful migrations. "
                "With the field mappings confirmed, you can apply precise standardization rules. You excel at bulk operations, "
                "pattern-based data population, and mass corrections. You balance automation with accuracy, using user clarifications "
                "to guide bulk transformations across entire datasets.")
    
    async def execute(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> AgentResult:
        """
        Execute comprehensive data cleansing and bulk operations
        
        Args:
            data: Data with field mappings and raw data
            context: Flow context with metadata
            
        Returns:
            AgentResult with cleaned data and bulk operation summaries
        """
        return await self.execute_analysis(data, context)
    
    async def execute_analysis(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> AgentResult:
        """
        Execute comprehensive data cleansing and bulk operations analysis
        
        Args:
            data: Data with field mappings and raw data
            context: Flow context with metadata
            
        Returns:
            AgentResult with cleaned data and bulk operation summaries
        """
        start_time = time.time()
        context = context or {}
        
        try:
            self.logger.info("🧹 Starting comprehensive data cleansing and bulk operations...")
            
            # Extract input data
            raw_data = data.get('raw_data', [])
            field_mappings = data.get('field_mappings', {})
            
            if not raw_data:
                return self._create_result(
                    execution_time=time.time() - start_time,
                    confidence_score=0.0,
                    status="failed",
                    data={},
                    errors=["No data provided for cleansing"]
                )
            
            # Convert to DataFrame for processing
            df = pd.DataFrame(raw_data)
            original_shape = df.shape
            
            self.logger.info(f"📊 Processing {original_shape[0]} records with {original_shape[1]} columns")
            
            # Perform comprehensive cleansing
            cleansing_results = {
                'cleaned_data': [],
                'standardization_summary': {},
                'bulk_operations_summary': {},
                'data_quality_metrics': {},
                'transformation_log': [],
                'recommendations': []
            }
            
            # Step 1: Apply field mappings and standardization
            df_cleaned = await self._apply_field_mappings(df, field_mappings, cleansing_results)
            
            # Step 2: Standardize data formats
            df_cleaned = await self._standardize_data_formats(df_cleaned, cleansing_results)
            
            # Step 3: Identify and handle missing data
            df_cleaned = await self._handle_missing_data(df_cleaned, cleansing_results)
            
            # Step 4: Perform bulk operations based on patterns
            df_cleaned = await self._perform_bulk_operations(df_cleaned, cleansing_results)
            
            # Step 5: Data validation and quality assessment
            await self._assess_data_quality(df_cleaned, df, cleansing_results)
            
            # Step 6: Generate insights and recommendations
            await self._generate_cleansing_insights(cleansing_results, df, df_cleaned)
            
            # Step 7: Check for user clarifications needed
            await self._check_bulk_operation_clarifications(cleansing_results, df_cleaned)
            
            # Convert cleaned DataFrame back to records
            cleansing_results['cleaned_data'] = df_cleaned.to_dict('records')
            
            # Calculate overall confidence
            overall_confidence = self._calculate_cleansing_confidence(cleansing_results)
            
            # Determine status
            status = self._determine_cleansing_status(cleansing_results, overall_confidence)
            
            execution_time = time.time() - start_time
            self.logger.info(f"✅ Data cleansing completed in {execution_time:.2f}s with {overall_confidence:.1f}% confidence")
            
            return self._create_result(
                execution_time=execution_time,
                confidence_score=overall_confidence,
                status=status,
                data=cleansing_results,
                metadata={
                    'original_records': original_shape[0],
                    'cleaned_records': len(cleansing_results['cleaned_data']),
                    'columns_processed': original_shape[1],
                    'transformations_applied': len(cleansing_results['transformation_log']),
                    'cleansing_timestamp': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"❌ Data cleansing failed: {str(e)}")
            
            return self._create_result(
                execution_time=execution_time,
                confidence_score=0.0,
                status="failed",
                data={},
                errors=[f"Cleansing failed: {str(e)}"]
            )
    
    async def _apply_field_mappings(self, df: pd.DataFrame, field_mappings: Dict[str, Any], results: Dict[str, Any]) -> pd.DataFrame:
        """Apply field mappings and rename columns"""
        df_mapped = df.copy()
        mapping_log = []
        
        # Apply mappings if provided
        if field_mappings:
            rename_dict = {}
            for asset_field, mapping_info in field_mappings.items():
                if isinstance(mapping_info, dict) and 'source_column' in mapping_info:
                    source_col = mapping_info['source_column']
                    if source_col in df.columns:
                        rename_dict[source_col] = asset_field
                        mapping_log.append(f"Mapped '{source_col}' → '{asset_field}'")
            
            if rename_dict:
                df_mapped = df_mapped.rename(columns=rename_dict)
                results['transformation_log'].extend(mapping_log)
        
        return df_mapped
    
    async def _standardize_data_formats(self, df: pd.DataFrame, results: Dict[str, Any]) -> pd.DataFrame:
        """Standardize data formats across columns"""
        df_standardized = df.copy()
        standardization_summary = defaultdict(list)
        
        for column in df.columns:
            col_data = df[column].dropna()
            if len(col_data) == 0:
                continue
            
            # Detect and standardize data types
            standardized_col = await self._standardize_column(col_data, column)
            
            if not standardized_col.equals(col_data):
                df_standardized[column] = standardized_col
                changes_count = (col_data != standardized_col).sum()
                standardization_summary[column].append(f"Standardized {changes_count} values")
                results['transformation_log'].append(f"Standardized {changes_count} values in '{column}'")
        
        results['standardization_summary'] = dict(standardization_summary)
        return df_standardized
    
    async def _standardize_column(self, col_data: pd.Series, column_name: str) -> pd.Series:
        """Standardize a single column based on detected patterns"""
        col_lower = column_name.lower()
        standardized = col_data.copy()
        
        # Environment standardization
        if any(env_term in col_lower for env_term in ['env', 'environment', 'stage', 'tier']):
            standardized = standardized.map(lambda x: self._standardize_value(str(x).lower(), 'environment')).fillna(standardized)
        
        # Status standardization
        elif any(status_term in col_lower for status_term in ['status', 'state', 'health']):
            standardized = standardized.map(lambda x: self._standardize_value(str(x).lower(), 'status')).fillna(standardized)
        
        # Criticality standardization
        elif any(crit_term in col_lower for crit_term in ['critical', 'priority', 'importance']):
            standardized = standardized.map(lambda x: self._standardize_value(str(x).lower(), 'criticality')).fillna(standardized)
        
        # OS standardization
        elif any(os_term in col_lower for os_term in ['os', 'operating', 'platform', 'system']):
            standardized = standardized.map(lambda x: self._standardize_os_value(str(x).lower())).fillna(standardized)
        
        # Date standardization
        elif any(date_term in col_lower for date_term in ['date', 'time', 'created', 'updated']):
            standardized = await self._standardize_dates(standardized)
        
        # IP address standardization
        elif any(ip_term in col_lower for ip_term in ['ip', 'address']):
            standardized = await self._standardize_ip_addresses(standardized)
        
        # Boolean standardization
        elif self._is_boolean_column(col_data):
            standardized = await self._standardize_booleans(standardized)
        
        return standardized
    
    def _standardize_value(self, value: str, category: str) -> Optional[str]:
        """Standardize a value using predefined mappings"""
        if category in self.value_mappings:
            return self.value_mappings[category].get(value.strip())
        return None
    
    def _standardize_os_value(self, value: str) -> Optional[str]:
        """Standardize operating system values"""
        value_clean = value.strip().lower()
        
        # Check for Windows variants
        if any(win_term in value_clean for win_term in ['windows', 'win', 'microsoft']):
            return 'Windows'
        
        # Check for Linux variants
        elif any(linux_term in value_clean for linux_term in ['linux', 'ubuntu', 'centos', 'rhel', 'debian', 'suse']):
            return 'Linux'
        
        # Check for Unix variants
        elif any(unix_term in value_clean for unix_term in ['unix', 'aix', 'solaris', 'hp-ux']):
            return 'Unix'
        
        # Check for macOS variants
        elif any(mac_term in value_clean for mac_term in ['macos', 'mac', 'darwin', 'osx']):
            return 'macOS'
        
        return None
    
    async def _standardize_dates(self, col_data: pd.Series) -> pd.Series:
        """Standardize date formats to ISO format"""
        standardized = col_data.copy()
        
        for idx, value in col_data.items():
            if pd.isna(value):
                continue
                
            try:
                # Try to parse various date formats
                if isinstance(value, str):
                    # Remove common date separators and try parsing
                    parsed_date = pd.to_datetime(value, errors='coerce')
                    if not pd.isna(parsed_date):
                        standardized[idx] = parsed_date.strftime('%Y-%m-%d')
            except:
                continue
        
        return standardized
    
    async def _standardize_ip_addresses(self, col_data: pd.Series) -> pd.Series:
        """Standardize IP address formats"""
        standardized = col_data.copy()
        ip_pattern = re.compile(self.standardization_patterns['ip_addresses'])
        
        for idx, value in col_data.items():
            if pd.isna(value) or not isinstance(value, str):
                continue
                
            # Extract IP address if embedded in text
            match = ip_pattern.search(value)
            if match:
                standardized[idx] = match.group()
        
        return standardized
    
    def _is_boolean_column(self, col_data: pd.Series) -> bool:
        """Check if column contains boolean-like values"""
        unique_values = set(str(v).lower().strip() for v in col_data.dropna().unique())
        boolean_values = set(self.data_type_patterns['boolean'])
        
        return len(unique_values) <= 4 and unique_values.issubset(boolean_values)
    
    async def _standardize_booleans(self, col_data: pd.Series) -> pd.Series:
        """Standardize boolean values to True/False"""
        standardized = col_data.copy()
        
        true_values = {'yes', 'true', '1', 'y', 'on', 'enabled', 'active'}
        false_values = {'no', 'false', '0', 'n', 'off', 'disabled', 'inactive'}
        
        for idx, value in col_data.items():
            if pd.isna(value):
                continue
                
            value_clean = str(value).lower().strip()
            if value_clean in true_values:
                standardized[idx] = True
            elif value_clean in false_values:
                standardized[idx] = False
        
        return standardized
    
    async def _handle_missing_data(self, df: pd.DataFrame, results: Dict[str, Any]) -> pd.DataFrame:
        """Identify and prepare bulk operations for missing data"""
        df_processed = df.copy()
        missing_data_summary = {}
        
        for column in df.columns:
            null_count = df[column].isnull().sum()
            null_percentage = (null_count / len(df)) * 100
            
            if null_count > 0:
                missing_data_summary[column] = {
                    'null_count': null_count,
                    'null_percentage': null_percentage,
                    'suggested_strategy': self._suggest_missing_data_strategy(df[column], column)
                }
        
        results['bulk_operations_summary']['missing_data'] = missing_data_summary
        return df_processed
    
    def _suggest_missing_data_strategy(self, col_data: pd.Series, column_name: str) -> str:
        """Suggest strategy for handling missing data"""
        null_percentage = (col_data.isnull().sum() / len(col_data)) * 100
        col_lower = column_name.lower()
        
        # High percentage missing - suggest exclusion or manual review
        if null_percentage > 80:
            return "exclude_column"
        elif null_percentage > 50:
            return "manual_review"
        
        # Based on column type/name
        if any(id_term in col_lower for id_term in ['id', 'identifier', 'key']):
            return "generate_unique"
        elif any(date_term in col_lower for date_term in ['date', 'time', 'created']):
            return "use_current_date"
        elif any(env_term in col_lower for env_term in ['env', 'environment']):
            return "infer_from_patterns"
        elif any(status_term in col_lower for status_term in ['status', 'state']):
            return "use_most_common"
        else:
            return "pattern_inference"
    
    async def _perform_bulk_operations(self, df: pd.DataFrame, results: Dict[str, Any]) -> pd.DataFrame:
        """Perform bulk operations for data population and correction"""
        df_bulk = df.copy()
        bulk_operations_log = []
        
        # Process missing data based on suggested strategies
        missing_data_info = results['bulk_operations_summary'].get('missing_data', {})
        
        for column, info in missing_data_info.items():
            if info['null_count'] > 0:
                strategy = info['suggested_strategy']
                
                if strategy in self.bulk_strategies:
                    original_nulls = df_bulk[column].isnull().sum()
                    df_bulk[column] = await self.bulk_strategies[strategy](df_bulk[column], column)
                    filled_count = original_nulls - df_bulk[column].isnull().sum()
                    
                    if filled_count > 0:
                        bulk_operations_log.append(f"Filled {filled_count} missing values in '{column}' using {strategy}")
        
        results['bulk_operations_summary']['operations_performed'] = bulk_operations_log
        results['transformation_log'].extend(bulk_operations_log)
        
        return df_bulk
    
    async def _infer_from_patterns(self, col_data: pd.Series, column_name: str) -> pd.Series:
        """Infer missing values from existing patterns"""
        filled_data = col_data.copy()
        non_null_values = col_data.dropna()
        
        if len(non_null_values) == 0:
            return filled_data
        
        # For environment-like columns, use most common value
        if any(env_term in column_name.lower() for env_term in ['env', 'environment', 'stage']):
            most_common = non_null_values.mode().iloc[0] if len(non_null_values.mode()) > 0 else 'Production'
            filled_data = filled_data.fillna(most_common)
        
        # For hostname patterns, try to infer from existing patterns
        elif 'hostname' in column_name.lower() or 'host' in column_name.lower():
            # Look for patterns in existing hostnames
            patterns = self._extract_hostname_patterns(non_null_values)
            if patterns:
                # Generate hostnames based on patterns (simplified)
                filled_data = filled_data.fillna('unknown-host')
        
        return filled_data
    
    async def _use_most_common_value(self, col_data: pd.Series, column_name: str) -> pd.Series:
        """Fill missing values with most common value"""
        filled_data = col_data.copy()
        non_null_values = col_data.dropna()
        
        if len(non_null_values) > 0:
            most_common = non_null_values.mode().iloc[0] if len(non_null_values.mode()) > 0 else non_null_values.iloc[0]
            filled_data = filled_data.fillna(most_common)
        
        return filled_data
    
    async def _infer_from_context(self, col_data: pd.Series, column_name: str) -> pd.Series:
        """Infer missing values from contextual information"""
        # This would use other columns as context - simplified implementation
        return await self._use_most_common_value(col_data, column_name)
    
    async def _assign_default_value(self, col_data: pd.Series, column_name: str) -> pd.Series:
        """Assign appropriate default values"""
        filled_data = col_data.copy()
        col_lower = column_name.lower()
        
        # Default values based on column type
        if any(env_term in col_lower for env_term in ['env', 'environment']):
            filled_data = filled_data.fillna('Production')
        elif any(status_term in col_lower for status_term in ['status', 'state']):
            filled_data = filled_data.fillna('Active')
        elif any(crit_term in col_lower for crit_term in ['critical', 'priority']):
            filled_data = filled_data.fillna('Medium')
        elif any(date_term in col_lower for date_term in ['date', 'time']):
            filled_data = filled_data.fillna(datetime.now().strftime('%Y-%m-%d'))
        else:
            filled_data = filled_data.fillna('Unknown')
        
        return filled_data
    
    async def _apply_rules(self, col_data: pd.Series, column_name: str) -> pd.Series:
        """Apply rule-based logic for missing values"""
        # This would implement business rules - simplified implementation
        return await self._assign_default_value(col_data, column_name)
    
    def _extract_hostname_patterns(self, hostnames: pd.Series) -> List[str]:
        """Extract common patterns from hostnames"""
        patterns = []
        
        for hostname in hostnames:
            if isinstance(hostname, str):
                # Look for common patterns like server001, web-01, etc.
                if re.search(r'\d+$', hostname):
                    base = re.sub(r'\d+$', '', hostname)
                    patterns.append(base)
        
        return list(set(patterns))
    
    async def _assess_data_quality(self, df_cleaned: pd.DataFrame, df_original: pd.DataFrame, results: Dict[str, Any]):
        """Assess data quality after cleansing"""
        quality_metrics = {
            'completeness': {},
            'consistency': {},
            'validity': {},
            'overall_improvement': {}
        }
        
        for column in df_cleaned.columns:
            if column in df_original.columns:
                # Completeness improvement
                original_completeness = (1 - df_original[column].isnull().sum() / len(df_original)) * 100
                cleaned_completeness = (1 - df_cleaned[column].isnull().sum() / len(df_cleaned)) * 100
                
                quality_metrics['completeness'][column] = {
                    'original': original_completeness,
                    'cleaned': cleaned_completeness,
                    'improvement': cleaned_completeness - original_completeness
                }
                
                # Consistency (standardization impact)
                original_unique = len(df_original[column].dropna().unique())
                cleaned_unique = len(df_cleaned[column].dropna().unique())
                
                quality_metrics['consistency'][column] = {
                    'original_unique_values': original_unique,
                    'cleaned_unique_values': cleaned_unique,
                    'standardization_ratio': cleaned_unique / original_unique if original_unique > 0 else 1.0
                }
        
        # Overall quality score
        avg_completeness_improvement = np.mean([
            metrics['improvement'] for metrics in quality_metrics['completeness'].values()
        ])
        
        quality_metrics['overall_improvement'] = {
            'completeness_improvement': avg_completeness_improvement,
            'total_transformations': len(results['transformation_log']),
            'quality_score': min(100, 70 + avg_completeness_improvement)  # Base 70 + improvements
        }
        
        results['data_quality_metrics'] = quality_metrics
    
    async def _generate_cleansing_insights(self, results: Dict[str, Any], df_original: pd.DataFrame, df_cleaned: pd.DataFrame):
        """Generate insights for the Agent-UI-monitor panel"""
        quality_metrics = results['data_quality_metrics']
        
        # Data quality improvement insight
        overall_improvement = quality_metrics['overall_improvement']
        self.add_insight(
            title="Data Quality Enhancement",
            description=f"Applied {overall_improvement['total_transformations']} transformations. "
                       f"Completeness improved by {overall_improvement['completeness_improvement']:.1f}%. "
                       f"Quality score: {overall_improvement['quality_score']:.1f}%",
            confidence_score=overall_improvement['quality_score'],
            category="quality"
        )
        
        # Bulk operations insight
        bulk_ops = results['bulk_operations_summary'].get('operations_performed', [])
        if bulk_ops:
            self.add_insight(
                title="Bulk Operations Summary",
                description=f"Performed {len(bulk_ops)} bulk operations including missing data population and standardization",
                confidence_score=85.0,
                category="recommendation",
                actionable=True,
                action_items=["Review bulk operation results", "Validate filled values"]
            )
        
        # Missing data insight
        missing_data = results['bulk_operations_summary'].get('missing_data', {})
        high_missing_cols = [col for col, info in missing_data.items() if info['null_percentage'] > 50]
        
        if high_missing_cols:
            self.add_insight(
                title="High Missing Data Alert",
                description=f"Columns with >50% missing data: {', '.join(high_missing_cols[:3])}{'...' if len(high_missing_cols) > 3 else ''}",
                confidence_score=60.0,
                category="quality",
                actionable=True,
                action_items=["Review high-missing columns", "Consider data collection improvements"]
            )
    
    async def _check_bulk_operation_clarifications(self, results: Dict[str, Any], df_cleaned: pd.DataFrame):
        """Check for bulk operation clarifications needed"""
        missing_data = results['bulk_operations_summary'].get('missing_data', {})
        
        # High missing data clarification
        high_missing = [(col, info) for col, info in missing_data.items() if info['null_percentage'] > 50]
        
        if high_missing:
            col_names = [col for col, _ in high_missing[:3]]
            self.add_clarification_request(
                question_text=f"Columns with >50% missing data: {', '.join(col_names)}. How should we handle these?",
                options=[
                    {"value": "fill_pattern", "label": "Fill using pattern inference"},
                    {"value": "fill_common", "label": "Fill with most common value"},
                    {"value": "fill_default", "label": "Fill with default values"},
                    {"value": "exclude", "label": "Exclude from processing"},
                    {"value": "manual", "label": "Manual review required"}
                ],
                context={"high_missing_columns": col_names},
                priority="medium",
                clarification_type="bulk_operation"
            )
        
        # Standardization confirmation
        standardization_summary = results.get('standardization_summary', {})
        if standardization_summary:
            total_standardized = sum(len(changes) for changes in standardization_summary.values())
            if total_standardized > 100:  # Significant standardization
                self.add_clarification_request(
                    question_text=f"Applied standardization to {len(standardization_summary)} columns affecting {total_standardized} values. Confirm these changes?",
                    options=[
                        {"value": "confirm", "label": "Confirm all standardizations"},
                        {"value": "review", "label": "Review individual changes"},
                        {"value": "revert", "label": "Revert standardizations"},
                        {"value": "selective", "label": "Apply selectively"}
                    ],
                    context={"standardization_summary": standardization_summary},
                    priority="medium",
                    clarification_type="bulk_operation"
                )
    
    def _calculate_cleansing_confidence(self, results: Dict[str, Any]) -> float:
        """Calculate overall cleansing confidence score"""
        quality_metrics = results.get('data_quality_metrics', {})
        overall_improvement = quality_metrics.get('overall_improvement', {})
        
        base_confidence = overall_improvement.get('quality_score', 70.0)
        
        # Adjust for successful operations
        transformations = len(results.get('transformation_log', []))
        if transformations > 0:
            base_confidence += min(10.0, transformations * 0.5)  # Bonus for transformations
        
        # Adjust for missing data handling
        missing_data = results['bulk_operations_summary'].get('missing_data', {})
        high_missing_count = sum(1 for info in missing_data.values() if info['null_percentage'] > 50)
        if high_missing_count > 0:
            base_confidence -= min(20.0, high_missing_count * 5)  # Penalty for high missing data
        
        return min(100.0, max(0.0, base_confidence))
    
    def _determine_cleansing_status(self, results: Dict[str, Any], confidence: float) -> str:
        """Determine overall cleansing status"""
        quality_score = results['data_quality_metrics']['overall_improvement']['quality_score']
        missing_data = results['bulk_operations_summary'].get('missing_data', {})
        
        # Check for critical issues
        critical_missing = sum(1 for info in missing_data.values() if info['null_percentage'] > 80)
        
        if critical_missing > 0 or quality_score < 60:
            return "partial"
        elif confidence < 75 or quality_score < 80:
            return "partial"
        else:
            return "success" 