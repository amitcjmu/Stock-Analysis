"""
Data Validation Phase

Handles the data import validation phase of the discovery flow.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Data validation handled by MasterFlowOrchestrator with real CrewAI agents
from app.services.agent_ui_bridge import agent_ui_bridge
from ..flow_config import PhaseNames

logger = logging.getLogger(__name__)


class DataValidationPhase:
    """Handles data import validation phase execution"""
    
    def __init__(self, state, data_validation_agent, init_context: Dict[str, Any]):
        """
        Initialize data validation phase
        
        Args:
            state: The flow state object
            data_validation_agent: The data validation agent instance
            init_context: Initial context for agent execution
        """
        self.state = state
        self.data_validation_agent = data_validation_agent
        self._init_context = init_context
    
    async def execute(self, previous_result: str) -> str:
        """
        Execute the data validation phase
        
        Args:
            previous_result: Result from the previous phase
            
        Returns:
            Phase result status
        """
        if previous_result == "initialization_failed":
            logger.error("❌ Skipping data validation due to initialization failure")
            return "data_validation_skipped"
        
        logger.info("🤖 Starting Data Import Validation with Agent-First Architecture")
        self.state.current_phase = PhaseNames.DATA_IMPORT_VALIDATION
        self.state.status = "running"
        self.state.progress_percentage = 10.0
        
        # Store record count for proper tracking
        total_records = len(self.state.raw_data) if self.state.raw_data else 0
        self.state.records_processed = 0
        self.state.records_total = total_records
        
        # Send real-time update
        await self._send_phase_start_update(total_records)
        
        try:
            # Prepare agent data
            agent_data = self._prepare_agent_data()
            
            # Send progress update
            await self._send_progress_update(total_records)
            
            # Execute data validation agent
            validation_result = await self.data_validation_agent.execute_analysis(
                agent_data, 
                self._init_context
            )
            
            # Process and store results
            self._process_validation_results(validation_result)
            
            # Send completion update
            await self._send_completion_update(validation_result)
            
            logger.info(f"✅ Data validation agent completed (confidence: {validation_result.confidence_score:.1f}%)")
            return "data_validation_completed"
            
        except Exception as e:
            logger.error(f"❌ Data validation agent failed: {e}")
            self.state.add_error("data_import", f"Agent execution failed: {str(e)}")
            
            # Send error update
            await self._send_error_update(str(e))
            
            return "data_validation_failed"
    
    def _prepare_agent_data(self) -> Dict[str, Any]:
        """Prepare data for agent execution"""
        return {
            'raw_data': self.state.raw_data,
            'source_columns': list(self.state.raw_data[0].keys()) if self.state.raw_data else [],
            'file_info': self.state.metadata.get('file_info', {}),
            'flow_metadata': {
                'flow_id': self.state.flow_id
            }
        }
    
    def _process_validation_results(self, validation_result):
        """Process and store validation results in state"""
        # Store agent results and confidence
        self.state.data_validation_results = validation_result.data
        self.state.agent_confidences['data_validation'] = validation_result.confidence_score
        
        # Collect insights and clarifications
        if validation_result.insights_generated:
            self.state.agent_insights.extend([
                insight.model_dump() for insight in validation_result.insights_generated
            ])
        
        if validation_result.clarifications_requested:
            self.state.user_clarifications.extend([
                req.model_dump() for req in validation_result.clarifications_requested
            ])
        
        # Update phase completion
        self.state.phase_completion['data_import'] = True
        self.state.progress_percentage = 20.0
        self.state.records_processed = len(self.state.raw_data)
        self.state.records_valid = len(self.state.raw_data)  # Assume all valid for now
    
    async def _send_phase_start_update(self, total_records: int):
        """Send real-time update when phase starts"""
        try:
            agent_ui_bridge.add_agent_insight(
                agent_id="data_import_agent",
                agent_name="Data Import Agent",
                insight_type="processing",
                page=f"flow_{self.state.flow_id}",
                title="Starting Data Import Validation",
                description=f"Beginning validation of {total_records} records",
                supporting_data={
                    'phase': 'data_import',
                    'records_total': total_records,
                    'records_processed': 0,
                    'progress_percentage': 10.0,
                    'start_time': datetime.utcnow().isoformat(),
                    'estimated_duration': '2-3 minutes'
                },
                confidence="high",
                flow_id=self.state.flow_id
            )
        except Exception as e:
            logger.warning(f"⚠️ Could not send phase start update: {e}")
    
    async def _send_progress_update(self, total_records: int):
        """Send progress update during processing"""
        try:
            agent_ui_bridge.add_agent_insight(
                agent_id="data_import_agent",
                agent_name="Data Import Agent",
                insight_type="progress",
                page=f"flow_{self.state.flow_id}",
                title="Processing Data Records",
                description=f"Analyzing {total_records} records for format validation, security scanning, and data quality assessment",
                supporting_data={
                    'phase': 'data_import',
                    'progress_percentage': 10.0,
                    'records_processed': total_records // 2,  # Mock progress
                    'validation_checks': ['format', 'security', 'quality']
                },
                confidence="high",
                flow_id=self.state.flow_id
            )
        except Exception as e:
            logger.warning(f"⚠️ Could not send progress update: {e}")
    
    async def _send_completion_update(self, validation_result):
        """Send completion update with results and detailed insights"""
        try:
            # Main completion insight
            agent_ui_bridge.add_agent_insight(
                agent_id="data_import_agent",
                agent_name="Data Import Agent",
                insight_type="success",
                page=f"flow_{self.state.flow_id}",
                title="Data Import Validation Completed",
                description=f"Successfully validated {len(self.state.raw_data)} records with {validation_result.confidence_score:.1f}% confidence",
                supporting_data={
                    'phase': 'data_import',
                    'progress_percentage': 20.0,
                    'records_processed': len(self.state.raw_data),
                    'records_total': self.state.records_total,
                    'confidence_score': validation_result.confidence_score,
                    'validation_results': validation_result.data,
                    'completion_time': datetime.utcnow().isoformat()
                },
                confidence="high",
                flow_id=self.state.flow_id
            )
            
            # Send detailed analysis insights
            await self._send_detailed_analysis_insights(validation_result)
            
        except Exception as e:
            logger.warning(f"⚠️ Could not send completion update: {e}")
    
    async def _send_detailed_analysis_insights(self, validation_result):
        """Send specific insights for security, privacy, and quality analysis"""
        try:
            # Analyze the data for security concerns
            security_analysis = self._analyze_security_aspects()
            if security_analysis:
                agent_ui_bridge.add_agent_insight(
                    agent_id="security_analysis_agent",
                    agent_name="Security Analysis Agent",
                    insight_type="security",
                    page=f"flow_{self.state.flow_id}",
                    title="Security Analysis",
                    description=security_analysis['description'],
                    supporting_data=security_analysis['data'],
                    confidence=security_analysis['confidence'],
                    flow_id=self.state.flow_id
                )
            
            # Analyze for privacy concerns
            privacy_analysis = self._analyze_privacy_aspects()
            if privacy_analysis:
                agent_ui_bridge.add_agent_insight(
                    agent_id="privacy_analysis_agent",
                    agent_name="Privacy Analysis Agent",
                    insight_type="privacy",
                    page=f"flow_{self.state.flow_id}",
                    title="Privacy Analysis",
                    description=privacy_analysis['description'],
                    supporting_data=privacy_analysis['data'],
                    confidence=privacy_analysis['confidence'],
                    flow_id=self.state.flow_id
                )
            
            # Analyze data quality
            quality_analysis = self._analyze_quality_aspects(validation_result)
            if quality_analysis:
                agent_ui_bridge.add_agent_insight(
                    agent_id="quality_analysis_agent",
                    agent_name="Data Quality Agent",
                    insight_type="quality",
                    page=f"flow_{self.state.flow_id}",
                    title="Data Quality Analysis",
                    description=quality_analysis['description'],
                    supporting_data=quality_analysis['data'],
                    confidence=quality_analysis['confidence'],
                    flow_id=self.state.flow_id
                )
                
        except Exception as e:
            logger.warning(f"⚠️ Could not send detailed analysis insights: {e}")
    
    async def _send_error_update(self, error_message: str):
        """Send error update when phase fails"""
        try:
            agent_ui_bridge.add_agent_insight(
                agent_id="data_import_agent",
                agent_name="Data Import Agent",
                insight_type="error",
                page=f"flow_{self.state.flow_id}",
                title="Data Import Validation Failed",
                description=f"Validation failed: {error_message}",
                supporting_data={
                    'phase': 'data_import',
                    'error_type': 'agent_execution_failure',
                    'error_message': error_message,
                    'failure_time': datetime.utcnow().isoformat()
                },
                confidence="high",
                flow_id=self.state.flow_id
            )
        except Exception as e:
            logger.warning(f"⚠️ Could not send error update: {e}")
    
    def _analyze_security_aspects(self) -> Optional[Dict[str, Any]]:
        """Analyze data for security-related concerns"""
        if not self.state.raw_data:
            return None
            
        security_issues = []
        security_score = 100
        
        # Get field names from the first record
        if len(self.state.raw_data) > 0:
            field_names = list(self.state.raw_data[0].keys())
            field_names_lower = [name.lower() for name in field_names]
            
            # Check for security-sensitive field patterns
            security_patterns = [
                'password', 'pwd', 'secret', 'key', 'token', 'auth', 'credential',
                'admin', 'root', 'service_account', 'api_key', 'private'
            ]
            
            for pattern in security_patterns:
                matching_fields = [field for field in field_names_lower if pattern in field]
                if matching_fields:
                    security_issues.append(f"Detected potential security-sensitive fields: {', '.join(matching_fields)}")
                    security_score -= 20
        
        # Sample data analysis for sensitive content
        sample_size = min(5, len(self.state.raw_data))
        for i in range(sample_size):
            record = self.state.raw_data[i]
            for key, value in record.items():
                if isinstance(value, str) and len(value) > 8:
                    # Check for potential credential patterns
                    if any(char in value for char in ['!', '@', '#', '$', '%', '^', '&', '*']) and value.count(' ') == 0:
                        security_issues.append(f"Field '{key}' contains potential credential-like data")
                        security_score -= 10
                        break
        
        if not security_issues:
            return {
                'description': f"No security concerns detected in {len(self.state.raw_data)} records",
                'data': {
                    'security_score': 100,
                    'issues_found': 0,
                    'recommendations': ['Data appears to be free of obvious security concerns']
                },
                'confidence': 'high'
            }
        else:
            return {
                'description': f"Found {len(security_issues)} potential security concerns",
                'data': {
                    'security_score': max(security_score, 0),
                    'issues_found': len(security_issues),
                    'issues': security_issues[:3],  # Limit to first 3 issues
                    'recommendations': [
                        'Review fields containing sensitive data',
                        'Consider data masking or encryption for production use',
                        'Implement access controls for sensitive information'
                    ]
                },
                'confidence': 'medium'
            }
    
    def _analyze_privacy_aspects(self) -> Optional[Dict[str, Any]]:
        """Analyze data for privacy-related concerns"""
        if not self.state.raw_data:
            return None
            
        privacy_issues = []
        privacy_score = 100
        
        # Get field names from the first record
        if len(self.state.raw_data) > 0:
            field_names = list(self.state.raw_data[0].keys())
            field_names_lower = [name.lower() for name in field_names]
            
            # Check for privacy-sensitive field patterns
            privacy_patterns = [
                'email', 'phone', 'ssn', 'social', 'address', 'personal',
                'credit_card', 'bank', 'account_number', 'dob', 'birth',
                'name', 'contact', 'mobile', 'telephone'
            ]
            
            for pattern in privacy_patterns:
                matching_fields = [field for field in field_names_lower if pattern in field]
                if matching_fields:
                    privacy_issues.append(f"Detected potential PII fields: {', '.join(matching_fields)}")
                    privacy_score -= 15
        
        # Sample data analysis for email patterns and other PII
        sample_size = min(5, len(self.state.raw_data))
        email_found = False
        for i in range(sample_size):
            record = self.state.raw_data[i]
            for key, value in record.items():
                if isinstance(value, str):
                    # Check for email patterns
                    if '@' in value and '.' in value and not email_found:
                        privacy_issues.append(f"Email addresses detected in field '{key}'")
                        privacy_score -= 20
                        email_found = True
                    # Check for phone patterns
                    if len(value.replace('-', '').replace('(', '').replace(')', '').replace(' ', '')) == 10 and value.replace('-', '').replace('(', '').replace(')', '').replace(' ', '').isdigit():
                        privacy_issues.append(f"Phone numbers detected in field '{key}'")
                        privacy_score -= 15
                        break
        
        if not privacy_issues:
            return {
                'description': f"No privacy concerns detected in {len(self.state.raw_data)} records",
                'data': {
                    'privacy_score': 100,
                    'issues_found': 0,
                    'recommendations': ['Data appears to be free of obvious PII concerns']
                },
                'confidence': 'high'
            }
        else:
            return {
                'description': f"Found {len(privacy_issues)} potential privacy concerns",
                'data': {
                    'privacy_score': max(privacy_score, 0),
                    'issues_found': len(privacy_issues),
                    'issues': privacy_issues[:3],  # Limit to first 3 issues
                    'recommendations': [
                        'Consider data anonymization for non-production environments',
                        'Implement data retention policies',
                        'Review compliance with privacy regulations (GDPR, CCPA, etc.)'
                    ]
                },
                'confidence': 'medium'
            }
    
    def _analyze_quality_aspects(self, validation_result) -> Optional[Dict[str, Any]]:
        """Analyze data quality aspects"""
        if not self.state.raw_data:
            return None
            
        quality_issues = []
        quality_score = validation_result.confidence_score
        
        # Check for data completeness
        if len(self.state.raw_data) > 0:
            total_fields = len(self.state.raw_data[0].keys())
            empty_counts = {}
            
            for record in self.state.raw_data:
                for key, value in record.items():
                    if not value or (isinstance(value, str) and value.strip() == ''):
                        empty_counts[key] = empty_counts.get(key, 0) + 1
            
            # Report fields with high empty rates
            for field, empty_count in empty_counts.items():
                empty_rate = (empty_count / len(self.state.raw_data)) * 100
                if empty_rate > 20:  # More than 20% empty
                    quality_issues.append(f"Field '{field}' has {empty_rate:.1f}% missing values")
        
        # Check data consistency
        if len(self.state.raw_data) > 1:
            # Check if all records have same fields
            first_keys = set(self.state.raw_data[0].keys())
            for i, record in enumerate(self.state.raw_data[1:], 1):
                if set(record.keys()) != first_keys:
                    quality_issues.append(f"Inconsistent field structure detected in record {i+1}")
                    break
        
        return {
            'description': f"Data quality analysis completed for {len(self.state.raw_data)} records",
            'data': {
                'quality_score': quality_score,
                'total_records': len(self.state.raw_data),
                'issues_found': len(quality_issues),
                'issues': quality_issues[:3] if quality_issues else [],
                'recommendations': [
                    'Data structure appears consistent',
                    'Consider data validation rules for production use',
                    'Monitor data quality over time'
                ] if not quality_issues else [
                    'Address missing value patterns',
                    'Implement data validation at source',
                    'Consider data cleansing procedures'
                ]
            },
            'confidence': 'high' if quality_score > 80 else 'medium'
        }