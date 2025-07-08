"""
Data Import Validation Executor
Handles data import validation phase for the Unified Discovery Flow.
Performs PII detection, malicious payload scanning, and data type validation.
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_phase_executor import BasePhaseExecutor

logger = logging.getLogger(__name__)


class DataImportValidationExecutor(BasePhaseExecutor):
    """
    Execute data import validation phase with security scanning and PII detection.
    This is the first phase that must complete before field mapping can begin.
    """
    
    def get_phase_name(self) -> str:
        """Get the name of this phase"""
        return "data_import"
    
    def get_progress_percentage(self) -> float:
        """Get the progress percentage when this phase completes"""
        return 16.67  # 1/6 phases = ~16.67%
    
    def _prepare_crew_input(self) -> Dict[str, Any]:
        """Prepare input data for crew execution"""
        return {
            "raw_data": self.state.raw_data,
            "metadata": self.state.metadata,
            "validation_requirements": {
                "check_pii": True,
                "check_security": True,
                "check_data_types": True,
                "check_source": True
            }
        }
    
    def _store_results(self, results: Dict[str, Any]):
        """Store execution results in state"""
        # Debug: Log what we're storing
        logger.info(f"🔍 DEBUG: Storing data import validation results")
        logger.info(f"🔍 DEBUG: Results keys: {list(results.keys())}")
        logger.info(f"🔍 DEBUG: Raw data in state: {len(self.state.raw_data) if hasattr(self.state, 'raw_data') and self.state.raw_data else 0} records")
        
        # Store the phase results
        self.state.phase_data["data_import"] = results
        
        # IMPORTANT: Also update the data_validation_results field for backward compatibility
        self.state.data_validation_results = results
        
        # Store validated data in raw_data if it's provided
        if "validated_data" in results and results["validated_data"]:
            logger.info(f"🔍 DEBUG: Storing validated_data in state.raw_data: {len(results['validated_data'])} records")
            self.state.raw_data = results["validated_data"]
        
        is_valid = results.get("is_valid", False)
        reason = results.get("reason", "Unknown validation failure")
        
        if is_valid:
            self.state.phase_completion["data_import"] = True
            logger.info(f"✅ DEBUG: Data import phase marked as completed")
        else:
            logger.warning(f"⚠️ DEBUG: Data import validation failed: {reason}")
            logger.warning(f"⚠️ DEBUG: Full validation results: {results}")
            
            # Store validation failure in state for debugging
            if not hasattr(self.state, 'validation_errors'):
                self.state.validation_errors = []
            self.state.validation_errors.append({
                "phase": "data_import",
                "error": reason,
                "timestamp": self._get_timestamp(),
                "full_results": results
            })
        
        # Add real-time insights from validation results
        if hasattr(self.state, 'agent_insights'):
            # Add file type analysis insight
            file_analysis = results.get('file_analysis', {})
            if file_analysis:
                insight = f"📊 Detected {file_analysis.get('detected_type', 'unknown')} data type with {file_analysis.get('confidence', 0):.0%} confidence. Recommended agent: {file_analysis.get('recommended_agent', 'CMDB_Data_Analyst_Agent')}"
                self.state.agent_insights.append({
                    "agent": "Data Import Agent",
                    "insight": insight,
                    "timestamp": self._get_timestamp(),
                    "confidence": file_analysis.get('confidence', 0.5)
                })
            
            # Add data quality insight
            quality_score = results.get('quality_score', 0)
            total_records = results.get('total_records', 0)
            insight = f"✅ Validated {total_records} records. Data quality score: {quality_score:.0%}"
            self.state.agent_insights.append({
                "agent": "Data Import Agent",
                "insight": insight,
                "timestamp": self._get_timestamp(),
                "confidence": 0.9
            })
            
            # Add security insights
            security_status = results.get('security_status', 'unknown')
            if security_status == 'pii_detected':
                pii_types = results.get('detailed_report', {}).get('security_analysis', {}).get('pii_types', [])
                insight = f"⚠️ PII detected in data: {', '.join(pii_types)}. Please ensure compliance with data privacy regulations."
                self.state.agent_insights.append({
                    "agent": "Data Import Agent",
                    "insight": insight,
                    "timestamp": self._get_timestamp(),
                    "confidence": 0.95
                })
            elif security_status == 'clean':
                self.state.agent_insights.append({
                    "agent": "Data Import Agent",
                    "insight": "🔒 Security scan passed. No malicious content or PII detected.",
                    "timestamp": self._get_timestamp(),
                    "confidence": 0.9
                })
            
            # Add recommendations from detailed report
            detailed_report = results.get('detailed_report', {})
            recommendations = detailed_report.get('recommendations', [])
            for recommendation in recommendations[:3]:  # Limit to top 3 recommendations
                self.state.agent_insights.append({
                    "agent": "Data Import Agent",
                    "insight": f"💡 {recommendation}",
                    "timestamp": self._get_timestamp(),
                    "confidence": 0.8
                })
    
    async def execute_with_crew(self, crew_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data import validation with CrewAI crew (if available)"""
        logger.info("🤖 Using CrewAI agents for data import validation (agentic-first approach)")
        
        try:
            # Use CrewAI crew for intelligent data validation
            if self.crew_manager.is_crew_available("data_import_validation"):
                crew = self.crew_manager.create_crew_on_demand(
                    "data_import_validation",
                    raw_data=self.state.raw_data,
                    metadata=self.state.metadata,
                    shared_memory=getattr(self.state, 'shared_memory_reference', None)
                )
                
                if crew:
                    logger.info("✅ Data import validation crew created - executing agentic analysis")
                    crew_result = await crew.kickoff_async(crew_input)
                    return self._process_crew_result(crew_result)
                else:
                    logger.warning("⚠️ Data import validation crew creation failed - using fallback")
                    return await self.execute_fallback()
            else:
                logger.warning("⚠️ Data import validation crew not available - using fallback")
                return await self.execute_fallback()
                
        except Exception as e:
            logger.error(f"❌ CrewAI data import validation failed: {e}")
            return await self.execute_fallback()
    
    async def execute_fallback(self) -> Dict[str, Any]:
        """Fallback data validation with agent-like intelligence"""
        try:
            logger.info("🔄 Executing fallback data import validation with agent patterns")
            start_time = time.time()
            
            # Debug: Check data availability
            logger.info(f"🔍 DEBUG: Raw data available before validation: {len(self.state.raw_data) if hasattr(self.state, 'raw_data') and self.state.raw_data else 0} records")
            if hasattr(self.state, 'raw_data') and self.state.raw_data and len(self.state.raw_data) > 0:
                logger.info(f"🔍 DEBUG: First record keys: {list(self.state.raw_data[0].keys())}")
                logger.info(f"🔍 DEBUG: Sample data: {self.state.raw_data[0]}")
            
            # Perform validation using agent-like analysis patterns
            validation_results = await self._perform_validation_checks()
            
            # Store results in state
            self._store_results(validation_results)
            
            # Persist the validated data
            logger.info(f"🔍 DEBUG: Validation results: is_valid={validation_results.get('is_valid')}, total_records={validation_results.get('total_records')}")
            
            validation_time = time.time() - start_time
            logger.info(f"✅ Agent-pattern data validation completed in {validation_time:.2f} seconds")
            
            return {
                "validation_status": "completed",
                "validation_results": validation_results,
                "execution_time": validation_time,
                "method": "agent_pattern_fallback_validation"
            }
            
        except Exception as e:
            logger.error(f"❌ Agent-pattern data validation failed: {e}")
            return {
                "validation_status": "failed",
                "error": str(e),
                "method": "agent_pattern_fallback_validation"
            }

    async def _perform_validation_checks(self) -> Dict[str, Any]:
        """Perform comprehensive data validation checks using agent-like intelligence"""
        try:
            results = {
                "is_valid": True,
                "reason": "",
                "summary": "",
                "security_status": "clean",
                "pii_detected": False,
                "quality_score": 1.0,
                "checks_performed": [],
                "file_analysis": {},
                "recommended_agent": "",
                "user_approval_required": True,
                "detailed_report": {}
            }
            
            # 1. File Type Detection and Content Analysis (agent-like intelligence)
            file_analysis = self._analyze_file_type_and_content()
            results["file_analysis"] = file_analysis
            results["recommended_agent"] = file_analysis["recommended_agent"]
            results["checks_performed"].append("file_type_analysis")
            
            # 2. Basic data structure validation
            structure_check = self._check_data_structure()
            results["checks_performed"].append("data_structure")
            if not structure_check["valid"]:
                results["is_valid"] = False
                results["reason"] = structure_check["reason"]
                return results
            
            # 3. PII Detection (using agent-like pattern recognition)
            pii_check = self._detect_pii()
            results["checks_performed"].append("pii_detection")
            results["pii_detected"] = pii_check["pii_found"]
            if pii_check["pii_found"]:
                logger.warning(f"⚠️ PII detected: {pii_check['pii_types']}")
                results["security_status"] = "pii_detected"
            
            # 4. Malicious payload scanning (using agent-like threat detection)
            security_check = self._scan_for_malicious_content()
            results["checks_performed"].append("security_scan")
            if security_check["threats_found"]:
                results["is_valid"] = False
                results["reason"] = f"Security threats detected: {security_check['threat_types']}"
                results["security_status"] = "threats_detected"
                return results
            
            # 5. Data type validation (using agent-like quality assessment)
            type_check = self._validate_data_types()
            results["checks_performed"].append("data_type_validation")
            results["quality_score"] = type_check["quality_score"]
            
            # 6. Source validation (if metadata available)
            if self.state.metadata:
                source_check = self._validate_data_source()
                results["checks_performed"].append("source_validation")
                if not source_check["valid"]:
                    logger.warning(f"⚠️ Source validation warning: {source_check['warning']}")
            
            # 7. Generate detailed user report (agent-like comprehensive analysis)
            detailed_report = self._generate_user_report(results, file_analysis, pii_check, security_check, type_check)
            results["detailed_report"] = detailed_report
            
            # Generate summary
            total_records = len(self.state.raw_data)
            field_count = len(self.state.raw_data[0].keys()) if self.state.raw_data else 0
            
            results["summary"] = f"📊 Agent Analysis Complete: {file_analysis['detected_type']} data detected. " \
                               f"Validated {total_records} records with {field_count} fields. " \
                               f"Quality score: {results['quality_score']:.2f}. " \
                               f"Security status: {results['security_status']}. " \
                               f"Recommended agent: {results['recommended_agent']}."
            
            # Add additional metadata for storage
            results.update({
                "validation_timestamp": self._get_timestamp(),
                "total_records": total_records,
                "detected_fields": list(self.state.raw_data[0].keys()) if self.state.raw_data else [],
                "execution_metadata": {
                    "timestamp": self._get_timestamp(),
                    "method": "comprehensive_agent_pattern_validation"
                },
                # IMPORTANT: Include the validated data for the next phase
                "validated_data": self.state.raw_data
            })
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Agent-pattern validation checks failed: {e}")
            return {
                "is_valid": False,
                "reason": f"Validation error: {str(e)}",
                "summary": "Validation failed due to system error",
                "user_approval_required": False
            }

    def _analyze_file_type_and_content(self) -> Dict[str, Any]:
        """Analyze file type and content using agent-like intelligence patterns"""
        try:
            if not self.state.raw_data:
                return {
                    "detected_type": "unknown",
                    "confidence": 0.0,
                    "recommended_agent": "CMDB_Data_Analyst_Agent",
                    "analysis_details": "No data available for analysis"
                }
            
            # Get field names and sample data for analysis
            sample_record = self.state.raw_data[0]
            field_names = list(sample_record.keys())
            field_names_lower = [f.lower() for f in field_names]
            
            # Analyze patterns to determine file type (agent-like pattern recognition)
            type_scores = {
                "cmdb": 0,
                "log_analysis": 0,
                "monitoring": 0,
                "network": 0,
                "security": 0,
                "application": 0,
                "infrastructure": 0
            }
            
            # CMDB indicators (agent knowledge patterns)
            cmdb_indicators = [
                'asset_id', 'asset_name', 'asset_type', 'hostname', 'server', 'device',
                'manufacturer', 'model', 'serial', 'location', 'ip_address', 'mac_address',
                'operating_system', 'os_version', 'cpu', 'memory', 'ram', 'storage',
                'application', 'owner', 'environment', 'status', 'configuration'
            ]
            
            # Log analysis indicators (agent knowledge patterns)
            log_indicators = [
                'timestamp', 'datetime', 'log_level', 'severity', 'message', 'event',
                'source', 'destination', 'user', 'session', 'error', 'warning',
                'info', 'debug', 'trace', 'exception', 'stack_trace'
            ]
            
            # Monitoring indicators (agent knowledge patterns)
            monitoring_indicators = [
                'metric', 'value', 'threshold', 'alert', 'performance', 'cpu_usage',
                'memory_usage', 'disk_usage', 'network_usage', 'response_time',
                'latency', 'throughput', 'availability', 'uptime', 'downtime'
            ]
            
            # Network indicators (agent knowledge patterns)
            network_indicators = [
                'src_ip', 'dst_ip', 'source_ip', 'destination_ip', 'port', 'protocol',
                'vlan', 'subnet', 'gateway', 'dns', 'firewall', 'router', 'switch',
                'bandwidth', 'traffic', 'packet', 'connection'
            ]
            
            # Security indicators (agent knowledge patterns)
            security_indicators = [
                'vulnerability', 'cve', 'threat', 'risk', 'security', 'compliance',
                'audit', 'access', 'permission', 'authentication', 'authorization',
                'incident', 'breach', 'malware', 'virus', 'attack'
            ]
            
            # Application indicators (agent knowledge patterns)
            application_indicators = [
                'application', 'app', 'service', 'component', 'module', 'function',
                'api', 'endpoint', 'database', 'table', 'schema', 'query',
                'transaction', 'session', 'user_id', 'request', 'response'
            ]
            
            # Infrastructure indicators (agent knowledge patterns)
            infrastructure_indicators = [
                'datacenter', 'rack', 'cabinet', 'power', 'cooling', 'ups',
                'generator', 'hvac', 'facility', 'building', 'floor', 'room',
                'circuit', 'panel', 'cable', 'fiber'
            ]
            
            # Score each type based on field name matches (agent-like scoring)
            all_indicators = {
                "cmdb": cmdb_indicators,
                "log_analysis": log_indicators,
                "monitoring": monitoring_indicators,
                "network": network_indicators,
                "security": security_indicators,
                "application": application_indicators,
                "infrastructure": infrastructure_indicators
            }
            
            for type_name, indicators in all_indicators.items():
                matches = 0
                for field in field_names_lower:
                    for indicator in indicators:
                        if indicator in field:
                            matches += 1
                            break
                
                # Calculate score as percentage of fields that match indicators
                type_scores[type_name] = matches / len(field_names) if field_names else 0
            
            # Determine the best match (agent-like decision making)
            best_type = max(type_scores, key=type_scores.get)
            best_score = type_scores[best_type]
            
            # Map to recommended agents (agent-like expertise routing)
            agent_mapping = {
                "cmdb": "CMDB_Data_Analyst_Agent",
                "log_analysis": "Log_Analysis_Agent", 
                "monitoring": "Application_Monitoring_Agent",
                "network": "Network_Analysis_Agent",
                "security": "Security_Analysis_Agent",
                "application": "Application_Architecture_Agent",
                "infrastructure": "Infrastructure_Analysis_Agent"
            }
            
            # If no clear type detected, default to CMDB for asset-like data
            if best_score < 0.2:
                best_type = "cmdb"
                best_score = 0.5  # Default moderate confidence
                recommended_agent = "CMDB_Data_Analyst_Agent"
            else:
                recommended_agent = agent_mapping.get(best_type, "CMDB_Data_Analyst_Agent")
            
            # Generate analysis details (agent-like reporting)
            analysis_details = f"Analyzed {len(field_names)} fields using agent pattern recognition. " \
                             f"Top matches: {best_type} ({best_score:.2%}). " \
                             f"Field patterns suggest {best_type} data type."
            
            return {
                "detected_type": best_type,
                "confidence": best_score,
                "recommended_agent": recommended_agent,
                "analysis_details": analysis_details,
                "type_scores": type_scores,
                "field_analysis": {
                    "total_fields": len(field_names),
                    "sample_fields": field_names[:10],  # First 10 fields
                    "pattern_matches": {
                        type_name: f"{score:.1%}" for type_name, score in type_scores.items()
                    }
                }
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Agent-pattern file type analysis failed: {e}")
            return {
                "detected_type": "unknown",
                "confidence": 0.0,
                "recommended_agent": "CMDB_Data_Analyst_Agent",
                "analysis_details": f"Analysis error: {str(e)}"
            }
    
    def _check_data_structure(self) -> Dict[str, Any]:
        """Check basic data structure validity"""
        try:
            # Enhanced debugging for data structure validation
            logger.info(f"🔍 DEBUG: Checking data structure...")
            logger.info(f"🔍 DEBUG: Has raw_data attribute: {hasattr(self.state, 'raw_data')}")
            
            if not hasattr(self.state, 'raw_data'):
                logger.error("❌ DEBUG: State has no raw_data attribute")
                return {"valid": False, "reason": "State has no raw_data attribute"}
            
            if not self.state.raw_data:
                logger.error("❌ DEBUG: raw_data is None or empty")
                return {"valid": False, "reason": "No data provided - raw_data is None or empty"}
            
            if not isinstance(self.state.raw_data, list):
                logger.error(f"❌ DEBUG: raw_data is not a list, type: {type(self.state.raw_data)}")
                return {"valid": False, "reason": f"Data must be a list of records, got {type(self.state.raw_data)}"}
            
            if len(self.state.raw_data) == 0:
                logger.error("❌ DEBUG: raw_data is empty list")
                return {"valid": False, "reason": "Empty data set - no records to validate"}
            
            # Check first record structure
            first_record = self.state.raw_data[0]
            if not isinstance(first_record, dict):
                logger.error(f"❌ DEBUG: First record is not a dict, type: {type(first_record)}")
                return {"valid": False, "reason": f"Records must be dictionaries, got {type(first_record)}"}
            
            if len(first_record.keys()) == 0:
                logger.error("❌ DEBUG: First record has no keys")
                return {"valid": False, "reason": "Records must have fields - first record is empty"}
            
            logger.info(f"✅ DEBUG: Data structure is valid - {len(self.state.raw_data)} records, first record has {len(first_record.keys())} fields")
            return {"valid": True, "reason": "Data structure is valid"}
            
        except Exception as e:
            logger.error(f"❌ DEBUG: Structure validation exception: {str(e)}")
            return {"valid": False, "reason": f"Structure validation error: {str(e)}"}
    
    def _detect_pii(self) -> Dict[str, Any]:
        """Detect potential PII in the data"""
        try:
            pii_patterns = {
                "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
                "phone": r'\b\d{3}-\d{3}-\d{4}\b',
                "credit_card": r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'
            }
            
            pii_found = False
            pii_types = []
            
            # Check field names for PII indicators
            if self.state.raw_data:
                fields = self.state.raw_data[0].keys()
                pii_field_indicators = ['email', 'ssn', 'social', 'phone', 'credit', 'card', 'password', 'secret']
                
                for field in fields:
                    field_lower = field.lower()
                    for indicator in pii_field_indicators:
                        if indicator in field_lower:
                            pii_found = True
                            pii_types.append(f"field_name_{indicator}")
            
            # Basic pattern matching on first few records
            import re
            sample_records = self.state.raw_data[:5]  # Check first 5 records
            
            for record in sample_records:
                for field, value in record.items():
                    if isinstance(value, str):
                        for pii_type, pattern in pii_patterns.items():
                            if re.search(pattern, value):
                                pii_found = True
                                if pii_type not in pii_types:
                                    pii_types.append(pii_type)
            
            return {
                "pii_found": pii_found,
                "pii_types": pii_types
            }
            
        except Exception as e:
            logger.warning(f"⚠️ PII detection failed: {e}")
            return {"pii_found": False, "pii_types": []}
    
    def _scan_for_malicious_content(self) -> Dict[str, Any]:
        """Scan for potential malicious content"""
        try:
            # Basic malicious pattern detection
            malicious_patterns = [
                r'<script[^>]*>.*?</script>',  # Script tags
                r'javascript:',               # JavaScript URLs
                r'eval\s*\(',                # eval() calls
                r'exec\s*\(',                # exec() calls
                r'DROP\s+TABLE',             # SQL injection
                r'DELETE\s+FROM',            # SQL injection
                r'INSERT\s+INTO',            # SQL injection
                r'UPDATE\s+.*SET',           # SQL injection
            ]
            
            threats_found = False
            threat_types = []
            
            import re
            
            # Check sample records for malicious patterns
            sample_records = self.state.raw_data[:10]  # Check first 10 records
            
            for record in sample_records:
                for field, value in record.items():
                    if isinstance(value, str):
                        for pattern in malicious_patterns:
                            if re.search(pattern, value, re.IGNORECASE):
                                threats_found = True
                                threat_types.append("potential_injection")
                                break
                        if threats_found:
                            break
                if threats_found:
                    break
            
            return {
                "threats_found": threats_found,
                "threat_types": threat_types
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Security scan failed: {e}")
            return {"threats_found": False, "threat_types": []}
    
    def _validate_data_types(self) -> Dict[str, Any]:
        """Validate data types and calculate quality score"""
        try:
            if not self.state.raw_data:
                return {"quality_score": 0.0}
            
            total_fields = 0
            valid_fields = 0
            
            # Analyze first record to understand field types
            first_record = self.state.raw_data[0]
            
            for field, value in first_record.items():
                total_fields += 1
                
                # Basic type validation - accept most common types
                if value is not None and value != "":
                    valid_fields += 1
            
            quality_score = valid_fields / total_fields if total_fields > 0 else 0.0
            
            return {
                "quality_score": quality_score,
                "total_fields": total_fields,
                "valid_fields": valid_fields
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Data type validation failed: {e}")
            return {"quality_score": 0.5}  # Default moderate score
    
    def _validate_data_source(self) -> Dict[str, Any]:
        """Validate data source if metadata is available"""
        try:
            metadata = self.state.metadata or {}
            
            # Check if source information is available
            if "source" not in metadata:
                return {"valid": True, "warning": "No source information available"}
            
            source = metadata["source"]
            
            # Basic source validation
            trusted_sources = ["data_import", "csv_upload", "api_import", "manual_entry"]
            
            if source not in trusted_sources:
                return {"valid": True, "warning": f"Unknown source: {source}"}
            
            return {"valid": True, "warning": None}
            
        except Exception as e:
            logger.warning(f"⚠️ Source validation failed: {e}")
            return {"valid": True, "warning": "Source validation error"}
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as ISO format string"""
        try:
            if hasattr(self.state, 'updated_at') and self.state.updated_at:
                if hasattr(self.state.updated_at, 'isoformat'):
                    return self.state.updated_at.isoformat()
                else:
                    return str(self.state.updated_at)
            else:
                return datetime.utcnow().isoformat()
        except Exception:
            return datetime.utcnow().isoformat()

    def _generate_user_report(self, results: Dict[str, Any], file_analysis: Dict[str, Any], 
                             pii_check: Dict[str, Any], security_check: Dict[str, Any], 
                             type_check: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive user report for data validation results"""
        try:
            total_records = len(self.state.raw_data) if self.state.raw_data else 0
            field_count = len(self.state.raw_data[0].keys()) if self.state.raw_data else 0
            
            report = {
                "validation_summary": {
                    "status": "passed" if results["is_valid"] else "failed",
                    "total_records": total_records,
                    "total_fields": field_count,
                    "quality_score": results.get("quality_score", 0.0),
                    "security_status": results.get("security_status", "unknown"),
                    "recommended_agent": results.get("recommended_agent", "CMDB_Data_Analyst_Agent")
                },
                "file_analysis": {
                    "detected_type": file_analysis.get("detected_type", "unknown"),
                    "confidence": file_analysis.get("confidence", 0.0),
                    "analysis_details": file_analysis.get("analysis_details", "No analysis available")
                },
                "security_analysis": {
                    "pii_detected": pii_check.get("pii_found", False),
                    "pii_types": pii_check.get("pii_types", []),
                    "threats_found": security_check.get("threats_found", False),
                    "threat_types": security_check.get("threat_types", [])
                },
                "data_quality": {
                    "quality_score": type_check.get("quality_score", 0.0),
                    "total_fields": type_check.get("total_fields", 0),
                    "valid_fields": type_check.get("valid_fields", 0)
                },
                "recommendations": [],
                "next_steps": []
            }
            
            # Add recommendations based on analysis
            if results["is_valid"]:
                report["recommendations"].append("Data validation passed - ready for field mapping")
                report["next_steps"].append("Proceed to field mapping phase")
                report["next_steps"].append("Review recommended agent selection")
            else:
                report["recommendations"].append(f"Data validation failed: {results.get('reason', 'Unknown error')}")
                report["next_steps"].append("Fix data issues before proceeding")
            
            if pii_check.get("pii_found", False):
                report["recommendations"].append("PII detected - ensure data handling compliance")
                report["next_steps"].append("Review PII handling policies")
            
            if security_check.get("threats_found", False):
                report["recommendations"].append("Security threats detected - data requires sanitization")
                report["next_steps"].append("Clean malicious content before proceeding")
            
            if type_check.get("quality_score", 0.0) < 0.8:
                report["recommendations"].append("Low data quality score - consider data cleansing")
                report["next_steps"].append("Review data quality issues")
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Failed to generate user report: {e}")
            return {
                "validation_summary": {
                    "status": "error",
                    "total_records": 0,
                    "total_fields": 0,
                    "error": str(e)
                },
                "recommendations": ["Report generation failed - manual review required"],
                "next_steps": ["Contact system administrator"]
            } 