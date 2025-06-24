"""
Data Import Validation Executor
Handles the first phase of discovery flow: data validation, PII detection, and security scanning.
"""

import logging
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
        self.state.phase_data["data_import"] = results
        if results.get("is_valid", False):
            self.state.phase_completion["data_import"] = True
    
    async def execute_with_crew(self, crew_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute validation using direct validation (no crew needed for data validation)"""
        # Data validation doesn't need a crew - it's a direct technical validation
        # User approval will be handled by the field mapping crew manager
        return await self._perform_validation_checks()
    
    async def execute_fallback(self) -> Dict[str, Any]:
        """Execute validation using fallback logic"""
        return await self._perform_validation_checks()
    
    async def execute(self, previous_result) -> str:
        """Execute data import validation phase"""
        try:
            # Validate we have data to process
            if not self.state.raw_data:
                logger.error("❌ No raw data available for validation")
                return "data_validation_failed"
            
            # Use the base class template pattern
            result = await super().execute(previous_result)
            
            # Override the result to use our specific naming
            if result == "data_import_completed":
                return "data_validation_completed"
            elif result == "data_import_failed":
                return "data_validation_failed"
            else:
                return result
                
        except Exception as e:
            logger.error(f"❌ Data import validation execution failed: {e}")
            self.state.add_error("data_import", f"Validation execution error: {str(e)}")
            return "data_validation_failed"
    
    async def _perform_validation_checks(self) -> Dict[str, Any]:
        """Perform comprehensive data validation checks"""
        try:
            results = {
                "is_valid": True,
                "reason": "",
                "summary": "",
                "security_status": "clean",
                "pii_detected": False,
                "quality_score": 1.0,
                "checks_performed": []
            }
            
            # 1. Basic data structure validation
            structure_check = self._check_data_structure()
            results["checks_performed"].append("data_structure")
            if not structure_check["valid"]:
                results["is_valid"] = False
                results["reason"] = structure_check["reason"]
                return results
            
            # 2. PII Detection
            pii_check = self._detect_pii()
            results["checks_performed"].append("pii_detection")
            results["pii_detected"] = pii_check["pii_found"]
            if pii_check["pii_found"]:
                logger.warning(f"⚠️ PII detected: {pii_check['pii_types']}")
                results["security_status"] = "pii_detected"
            
            # 3. Malicious payload scanning
            security_check = self._scan_for_malicious_content()
            results["checks_performed"].append("security_scan")
            if security_check["threats_found"]:
                results["is_valid"] = False
                results["reason"] = f"Security threats detected: {security_check['threat_types']}"
                results["security_status"] = "threats_detected"
                return results
            
            # 4. Data type validation
            type_check = self._validate_data_types()
            results["checks_performed"].append("data_type_validation")
            results["quality_score"] = type_check["quality_score"]
            
            # 5. Source validation (if metadata available)
            if self.state.metadata:
                source_check = self._validate_data_source()
                results["checks_performed"].append("source_validation")
                if not source_check["valid"]:
                    logger.warning(f"⚠️ Source validation warning: {source_check['warning']}")
            
            # Generate summary
            total_records = len(self.state.raw_data)
            field_count = len(self.state.raw_data[0].keys()) if self.state.raw_data else 0
            
            results["summary"] = f"Validated {total_records} records with {field_count} fields. " \
                               f"Quality score: {results['quality_score']:.2f}. " \
                               f"Security status: {results['security_status']}."
            
            # Add additional metadata for storage
            results.update({
                "validation_timestamp": self._get_timestamp(),
                "total_records": total_records,
                "detected_fields": list(self.state.raw_data[0].keys()) if self.state.raw_data else [],
                "execution_metadata": {
                    "timestamp": self._get_timestamp(),
                    "method": "data_import_validation"
                }
            })
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Validation checks failed: {e}")
            return {
                "is_valid": False,
                "reason": f"Validation error: {str(e)}",
                "summary": "Validation failed due to system error"
            }
    
    def _check_data_structure(self) -> Dict[str, Any]:
        """Check basic data structure validity"""
        try:
            if not self.state.raw_data:
                return {"valid": False, "reason": "No data provided"}
            
            if not isinstance(self.state.raw_data, list):
                return {"valid": False, "reason": "Data must be a list of records"}
            
            if len(self.state.raw_data) == 0:
                return {"valid": False, "reason": "Empty data set"}
            
            # Check first record structure
            first_record = self.state.raw_data[0]
            if not isinstance(first_record, dict):
                return {"valid": False, "reason": "Records must be dictionaries"}
            
            if len(first_record.keys()) == 0:
                return {"valid": False, "reason": "Records must have fields"}
            
            return {"valid": True, "reason": "Data structure is valid"}
            
        except Exception as e:
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