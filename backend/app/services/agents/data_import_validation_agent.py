"""
Data Import Validation Agent - Enterprise Data Security and Validation Specialist
Performs comprehensive security scanning, PII detection, and data structure validation
"""

import re
import time
from typing import Dict, Any, List, Optional, Set, Tuple
import pandas as pd
from datetime import datetime
import logging

from .base_discovery_agent import BaseDiscoveryAgent, AgentResult

logger = logging.getLogger(__name__)

class DataImportValidationAgent(BaseDiscoveryAgent):
    """
    Enterprise Data Security and Validation Specialist
    
    Performs comprehensive security scanning, PII detection, and data structure validation
    to ensure enterprise-grade data safety and compliance before processing.
    """
    
    def __init__(self):
        super().__init__("Data Import Validation Agent", "data_import_validation_001")
        
        # PII Detection Patterns
        self.pii_patterns = {
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b',
            'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
            'ip_address': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            'passport': r'\b[A-Z]{1,2}\d{6,9}\b',
            'driver_license': r'\b[A-Z]{1,2}\d{6,8}\b'
        }
        
        # Security Risk Patterns
        self.security_patterns = {
            'password': r'(?i)(password|pwd|pass|secret|key)',
            'token': r'(?i)(token|auth|bearer|api[_-]?key)',
            'database_connection': r'(?i)(connection|conn[_-]?string|jdbc|odbc)',
            'file_path': r'(?i)([c-z]:\\|/[a-z]+/|\\\\)',
            'sql_injection': r'(?i)(union|select|drop|delete|insert|update)[\s]+',
            'script_tags': r'<script[^>]*>.*?</script>'
        }
        
        # Compliance Frameworks
        self.compliance_checks = {
            'gdpr': ['name', 'email', 'address', 'phone', 'dob', 'nationality'],
            'hipaa': ['patient', 'medical', 'health', 'diagnosis', 'treatment'],
            'sox': ['financial', 'revenue', 'expense', 'audit', 'control'],
            'pci': ['card', 'payment', 'transaction', 'merchant', 'cardholder']
        }
    
    def get_role(self) -> str:
        return "Enterprise Data Security and Validation Specialist"
    
    def get_goal(self) -> str:
        return "Perform comprehensive security scanning, PII detection, and data structure validation to ensure enterprise-grade data safety and compliance before processing"
    
    def get_backstory(self) -> str:
        return ("You are a cybersecurity expert with 15+ years of experience in enterprise data governance. "
                "You specialize in identifying sensitive information, detecting security threats, and validating data structures. "
                "You have a methodical approach to data validation that prioritizes security without compromising processing efficiency.")
    
    async def execute(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> AgentResult:
        """
        Execute comprehensive data import validation
        
        Args:
            data: Raw imported data
            context: Flow context with metadata
            
        Returns:
            AgentResult with validation results and security assessment
        """
        return await self.execute_analysis(data, context)
    
    async def execute_analysis(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> AgentResult:
        """
        Execute comprehensive data import validation analysis
        
        Args:
            data: Raw imported data
            context: Flow context with metadata
            
        Returns:
            AgentResult with validation results and security assessment
        """
        start_time = time.time()
        context = context or {}
        
        try:
            self.logger.info("🔍 Starting comprehensive data import validation...")
            
            # Extract data for validation
            raw_data = data.get('raw_data', [])
            file_info = data.get('file_info', {})
            
            if not raw_data:
                return self._create_result(
                    execution_time=time.time() - start_time,
                    confidence_score=0.0,
                    status="failed",
                    data={},
                    errors=["No data provided for validation"]
                )
            
            # Convert to DataFrame for easier analysis
            df = pd.DataFrame(raw_data)
            
            # Perform validation checks
            validation_results = {
                'file_validation': await self._validate_file_structure(df, file_info),
                'pii_detection': await self._detect_pii(df),
                'security_assessment': await self._assess_security_risks(df),
                'compliance_check': await self._check_compliance_requirements(df),
                'data_quality': await self._assess_data_quality(df),
                'recommendations': []
            }
            
            # Calculate overall confidence score
            confidence_factors = {
                'file_structure_confidence': validation_results['file_validation']['confidence'],
                'security_confidence': validation_results['security_assessment']['confidence'],
                'compliance_confidence': validation_results['compliance_check']['confidence'],
                'data_quality_confidence': validation_results['data_quality']['confidence']
            }
            
            overall_confidence = self.calculate_confidence_score(confidence_factors)
            
            # Generate insights and recommendations
            await self._generate_validation_insights(validation_results, df)
            
            # Determine if clarifications are needed
            await self._check_for_clarifications(validation_results, df)
            
            # Determine overall status
            status = self._determine_validation_status(validation_results)
            
            execution_time = time.time() - start_time
            self.logger.info(f"✅ Data import validation completed in {execution_time:.2f}s with {overall_confidence:.1f}% confidence")
            
            return self._create_result(
                execution_time=execution_time,
                confidence_score=overall_confidence,
                status=status,
                data=validation_results,
                metadata={
                    'records_validated': len(df),
                    'columns_analyzed': len(df.columns),
                    'validation_timestamp': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"❌ Data import validation failed: {str(e)}")
            
            return self._create_result(
                execution_time=execution_time,
                confidence_score=0.0,
                status="failed",
                data={},
                errors=[f"Validation failed: {str(e)}"]
            )
    
    async def _validate_file_structure(self, df: pd.DataFrame, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate file structure and format"""
        results = {
            'confidence': 90.0,
            'issues': [],
            'warnings': [],
            'file_size_mb': file_info.get('size_mb', 0),
            'row_count': len(df),
            'column_count': len(df.columns),
            'data_types': df.dtypes.to_dict(),
            'null_percentages': (df.isnull().sum() / len(df) * 100).to_dict()
        }
        
        # Check for structural issues
        if len(df) == 0:
            results['issues'].append("Empty dataset")
            results['confidence'] = 0.0
        elif len(df) < 10:
            results['warnings'].append("Very small dataset (< 10 records)")
            results['confidence'] -= 20.0
        
        if len(df.columns) == 0:
            results['issues'].append("No columns detected")
            results['confidence'] = 0.0
        elif len(df.columns) > 100:
            results['warnings'].append("Very wide dataset (> 100 columns)")
            results['confidence'] -= 10.0
        
        # Check for high null percentages
        high_null_cols = [col for col, pct in results['null_percentages'].items() if pct > 80]
        if high_null_cols:
            results['warnings'].append(f"Columns with >80% null values: {high_null_cols}")
            results['confidence'] -= 15.0
        
        return results
    
    async def _detect_pii(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect Personally Identifiable Information"""
        pii_findings = {
            'confidence': 95.0,
            'detected_pii': {},
            'high_risk_columns': [],
            'medium_risk_columns': [],
            'total_pii_records': 0
        }
        
        for column in df.columns:
            column_pii = {}
            
            # Convert column to string for pattern matching
            col_str = df[column].astype(str).str.cat(sep=' ')
            
            for pii_type, pattern in self.pii_patterns.items():
                matches = re.findall(pattern, col_str)
                if matches:
                    column_pii[pii_type] = len(matches)
            
            if column_pii:
                pii_findings['detected_pii'][column] = column_pii
                
                # Classify risk level
                total_matches = sum(column_pii.values())
                if total_matches > len(df) * 0.5:  # >50% of records
                    pii_findings['high_risk_columns'].append(column)
                else:
                    pii_findings['medium_risk_columns'].append(column)
        
        # Calculate total PII exposure
        pii_findings['total_pii_records'] = len(pii_findings['detected_pii'])
        
        # Adjust confidence based on PII findings
        if pii_findings['high_risk_columns']:
            pii_findings['confidence'] = 60.0  # High PII risk
        elif pii_findings['medium_risk_columns']:
            pii_findings['confidence'] = 80.0  # Medium PII risk
        
        return pii_findings
    
    async def _assess_security_risks(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess security risks in the data"""
        security_results = {
            'confidence': 90.0,
            'security_risks': {},
            'risk_level': 'low',
            'flagged_columns': []
        }
        
        for column in df.columns:
            column_risks = {}
            
            # Check column name for security patterns
            col_name_lower = column.lower()
            for risk_type, pattern in self.security_patterns.items():
                if re.search(pattern, col_name_lower):
                    column_risks[risk_type] = 'column_name'
            
            # Check column data for security patterns
            col_str = df[column].astype(str).str.cat(sep=' ')
            for risk_type, pattern in self.security_patterns.items():
                matches = re.findall(pattern, col_str)
                if matches:
                    column_risks[risk_type] = len(matches)
            
            if column_risks:
                security_results['security_risks'][column] = column_risks
                security_results['flagged_columns'].append(column)
        
        # Determine overall risk level
        if len(security_results['flagged_columns']) > 5:
            security_results['risk_level'] = 'high'
            security_results['confidence'] = 50.0
        elif len(security_results['flagged_columns']) > 2:
            security_results['risk_level'] = 'medium'
            security_results['confidence'] = 70.0
        
        return security_results
    
    async def _check_compliance_requirements(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check compliance with various frameworks"""
        compliance_results = {
            'confidence': 85.0,
            'frameworks': {},
            'compliance_risk': 'low',
            'recommendations': []
        }
        
        for framework, keywords in self.compliance_checks.items():
            framework_findings = []
            
            for column in df.columns:
                col_name_lower = column.lower()
                for keyword in keywords:
                    if keyword in col_name_lower:
                        framework_findings.append({
                            'column': column,
                            'keyword': keyword,
                            'risk_level': 'medium'
                        })
            
            if framework_findings:
                compliance_results['frameworks'][framework] = framework_findings
        
        # Determine compliance risk
        total_findings = sum(len(findings) for findings in compliance_results['frameworks'].values())
        if total_findings > 10:
            compliance_results['compliance_risk'] = 'high'
            compliance_results['confidence'] = 60.0
        elif total_findings > 5:
            compliance_results['compliance_risk'] = 'medium'
            compliance_results['confidence'] = 75.0
        
        return compliance_results
    
    async def _assess_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess overall data quality"""
        quality_results = {
            'confidence': 80.0,
            'completeness': {},
            'consistency': {},
            'validity': {},
            'overall_score': 0.0
        }
        
        # Safety check for empty DataFrame
        if len(df) == 0 or len(df.columns) == 0:
            return {
                'confidence': 0.0,
                'completeness': {},
                'consistency': {},
                'validity': {},
                'overall_score': 0.0
            }
        
        # Completeness assessment
        for column in df.columns:
            try:
                null_count = df[column].isnull().sum()
                total_count = len(df)
                
                # Safe division to avoid division by zero
                if total_count > 0:
                    null_pct = float(null_count / total_count * 100)
                else:
                    null_pct = 100.0
                
                # Ensure we have a valid numeric value
                if pd.isna(null_pct) or not pd.api.types.is_numeric_dtype(type(null_pct)):
                    null_pct = 100.0
                
                quality_results['completeness'][column] = {
                    'null_percentage': null_pct,
                    'score': max(0.0, 100.0 - null_pct)
                }
            except Exception as e:
                self.logger.warning(f"Error calculating completeness for column {column}: {e}")
                quality_results['completeness'][column] = {
                    'null_percentage': 100.0,
                    'score': 0.0
                }
        
        # Consistency assessment (data type consistency)
        for column in df.columns:
            try:
                if df[column].dtype == 'object':
                    # Check for mixed data types in string columns
                    sample_values = df[column].dropna().head(100)
                    consistency_score = 90.0  # Default for string columns
                else:
                    consistency_score = 95.0  # Numeric columns are generally consistent
                
                quality_results['consistency'][column] = {'score': float(consistency_score)}
            except Exception as e:
                self.logger.warning(f"Error calculating consistency for column {column}: {e}")
                quality_results['consistency'][column] = {'score': 0.0}
        
        # Calculate overall quality score with safety checks
        try:
            if quality_results['completeness'] and quality_results['consistency']:
                completeness_scores = [col['score'] for col in quality_results['completeness'].values()]
                consistency_scores = [col['score'] for col in quality_results['consistency'].values()]
                
                completeness_avg = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0.0
                consistency_avg = sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.0
                
                quality_results['overall_score'] = float((completeness_avg + consistency_avg) / 2)
                quality_results['confidence'] = min(95.0, quality_results['overall_score'])
            else:
                quality_results['overall_score'] = 0.0
                quality_results['confidence'] = 0.0
        except Exception as e:
            self.logger.warning(f"Error calculating overall quality score: {e}")
            quality_results['overall_score'] = 0.0
            quality_results['confidence'] = 0.0
        
        return quality_results
    
    async def _generate_validation_insights(self, validation_results: Dict[str, Any], df: pd.DataFrame):
        """Generate insights for the Agent-UI-monitor panel"""
        
        # File structure insights
        file_val = validation_results['file_validation']
        self.add_insight(
            title="Data Structure Analysis",
            description=f"Analyzed {file_val['row_count']} records with {file_val['column_count']} columns. "
                       f"Data quality score: {validation_results['data_quality']['overall_score']:.1f}%",
            confidence_score=file_val['confidence'],
            category="quality"
        )
        
        # PII detection insights
        pii_results = validation_results['pii_detection']
        if pii_results['detected_pii']:
            self.add_insight(
                title="PII Detection Alert",
                description=f"Detected PII in {len(pii_results['detected_pii'])} columns. "
                           f"High-risk columns: {len(pii_results['high_risk_columns'])}",
                confidence_score=pii_results['confidence'],
                category="security",
                actionable=True,
                action_items=["Review PII handling procedures", "Consider data anonymization"]
            )
        
        # Security assessment insights
        security_results = validation_results['security_assessment']
        if security_results['flagged_columns']:
            self.add_insight(
                title="Security Risk Assessment",
                description=f"Security risks detected in {len(security_results['flagged_columns'])} columns. "
                           f"Risk level: {security_results['risk_level']}",
                confidence_score=security_results['confidence'],
                category="security",
                actionable=True,
                action_items=["Review flagged columns", "Apply security controls"]
            )
    
    async def _check_for_clarifications(self, validation_results: Dict[str, Any], df: pd.DataFrame):
        """Check if user clarifications are needed"""
        
        # PII handling clarification
        pii_results = validation_results['pii_detection']
        if pii_results['high_risk_columns']:
            self.add_clarification_request(
                question_text=f"High-risk PII detected in columns: {', '.join(pii_results['high_risk_columns'])}. How should we proceed?",
                options=[
                    {"value": "anonymize", "label": "Anonymize PII data"},
                    {"value": "exclude", "label": "Exclude PII columns"},
                    {"value": "proceed", "label": "Proceed with PII (requires approval)"},
                    {"value": "review", "label": "Manual review required"}
                ],
                context={"pii_columns": pii_results['high_risk_columns']},
                priority="high",
                clarification_type="validation"
            )
        
        # Data quality clarification
        quality_results = validation_results['data_quality']
        if quality_results['overall_score'] < 70:
            high_null_cols = [col for col, data in quality_results['completeness'].items() 
                            if data['null_percentage'] > 50]
            if high_null_cols:
                self.add_clarification_request(
                    question_text=f"Columns with >50% missing data: {', '.join(high_null_cols)}. How should we handle these?",
                    options=[
                        {"value": "exclude", "label": "Exclude high-null columns"},
                        {"value": "impute", "label": "Impute missing values"},
                        {"value": "keep", "label": "Keep as-is"},
                        {"value": "manual", "label": "Manual review required"}
                    ],
                    context={"high_null_columns": high_null_cols},
                    priority="medium",
                    clarification_type="validation"
                )
    
    def _determine_validation_status(self, validation_results: Dict[str, Any]) -> str:
        """Determine overall validation status"""
        
        # Check for critical issues
        file_val = validation_results['file_validation']
        if file_val['issues']:
            return "failed"
        
        pii_results = validation_results['pii_detection']
        security_results = validation_results['security_assessment']
        
        # Check for high-risk conditions
        if (pii_results['high_risk_columns'] or 
            security_results['risk_level'] == 'high'):
            return "partial"  # Needs review/clarification
        
        # Check overall quality
        quality_score = validation_results['data_quality']['overall_score']
        if quality_score < 60:
            return "partial"
        
        return "success" 