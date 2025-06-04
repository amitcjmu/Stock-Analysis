"""
Parsing Handler for CrewAI Flow Service
Handles AI result parsing, pattern extraction, and structured data conversion.
"""

import logging
import re
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class ParsingHandler:
    """Handler for parsing AI agent results into structured data."""
    
    def __init__(self):
        self.parsing_patterns = self._initialize_parsing_patterns()
        self.fallback_mappings = self._initialize_fallback_mappings()
    
    def _initialize_parsing_patterns(self) -> Dict[str, Any]:
        """Initialize regex patterns for parsing different result types."""
        return {
            "validation": {
                "quality_score": r'QUALITY_SCORE:\s*(\d+(?:\.\d+)?)',
                "missing_fields": r'MISSING_FIELDS:\s*\[(.*?)\]',
                "issues": r'ISSUES:\s*\[(.*?)\]',
                "ready": r'READY:\s*(Yes|No)',
                "actions": r'ACTIONS:\s*\[(.*?)\]'
            },
            "field_mapping": {
                "mapping": r'(\w+)\s*->\s*(\w+)\s*\(confidence:\s*([\d.]+)\)',
                "confidence_threshold": 0.7
            },
            "asset_classification": {
                "asset_block": r'ASSET_INDEX:\s*\d+',
                "name": r'NAME:\s*([^\n]+)',
                "type": r'TYPE:\s*(\w+)', 
                "priority": r'PRIORITY:\s*(\w+)',
                "complexity": r'COMPLEXITY:\s*(\w+)',
                "risk": r'RISK:\s*(\w+)',
                "dependencies": r'DEPENDENCIES:\s*(Yes|No)',
                "confidence": r'CONFIDENCE:\s*([\d.]+)'
            }
        }
    
    def _initialize_fallback_mappings(self) -> Dict[str, Any]:
        """Initialize fallback mapping patterns for common field types."""
        return {
            "field_patterns": {
                "asset_name": ["name", "hostname", "server", "asset", "system"],
                "ci_type": ["type", "ci_type", "category", "kind", "class"],
                "environment": ["env", "environment", "tier", "stage"],
                "business_owner": ["owner", "responsible", "business", "contact"],
                "technical_owner": ["tech", "technical", "admin", "engineer"],
                "location": ["location", "site", "datacenter", "region", "zone"],
                "dependencies": ["depend", "related", "connected", "linked"],
                "risk_level": ["risk", "criticality", "priority", "importance"]
            },
            "asset_types": {
                "server_patterns": ["server", "host", "machine", "vm", "virtual"],
                "database_patterns": ["database", "db", "sql", "oracle", "mysql", "postgres"],
                "application_patterns": ["application", "app", "service", "web", "api"],
                "network_patterns": ["network", "router", "switch", "firewall", "lb"],
                "storage_patterns": ["storage", "disk", "san", "nas", "volume"]
            }
        }
    
    def parse_validation_result(self, result: str) -> Dict[str, Any]:
        """Parse data validation result with enhanced pattern matching."""
        parsed = {
            "quality_score": 7.0,
            "missing_fields": [],
            "issues": [],
            "ready": True,
            "actions": []
        }
        
        try:
            patterns = self.parsing_patterns["validation"]
            
            # Extract quality score
            score_match = re.search(patterns["quality_score"], result, re.IGNORECASE)
            if score_match:
                parsed["quality_score"] = float(score_match.group(1))
            
            # Extract missing fields
            missing_match = re.search(patterns["missing_fields"], result, re.IGNORECASE)
            if missing_match:
                fields = [f.strip().strip('"\'') for f in missing_match.group(1).split(',') if f.strip()]
                parsed["missing_fields"] = fields
            
            # Extract issues
            issues_match = re.search(patterns["issues"], result, re.IGNORECASE)
            if issues_match:
                issues = [i.strip().strip('"\'') for i in issues_match.group(1).split(',') if i.strip()]
                parsed["issues"] = issues
            
            # Extract readiness
            ready_match = re.search(patterns["ready"], result, re.IGNORECASE)
            if ready_match:
                parsed["ready"] = ready_match.group(1).lower() == 'yes'
            
            # Extract actions
            actions_match = re.search(patterns["actions"], result, re.IGNORECASE)
            if actions_match:
                actions = [a.strip().strip('"\'') for a in actions_match.group(1).split(',') if a.strip()]
                parsed["actions"] = actions
            
            logger.info("Validation result parsed successfully")
            
        except Exception as e:
            logger.warning(f"Failed to parse validation result: {e}")
        
        return parsed
    
    def parse_field_mapping_result(self, result: str, headers: List[str]) -> Dict[str, str]:
        """Parse field mapping result with enhanced pattern recognition."""
        mappings = {}
        
        try:
            patterns = self.parsing_patterns["field_mapping"]
            
            # Look for explicit mappings with confidence scores
            mapping_pattern = patterns["mapping"]
            matches = re.findall(mapping_pattern, result, re.IGNORECASE)
            
            confidence_threshold = patterns["confidence_threshold"]
            
            for field, attribute, confidence in matches:
                if field in headers and float(confidence) >= confidence_threshold:
                    mappings[field] = attribute
                    logger.debug(f"Mapped {field} -> {attribute} (confidence: {confidence})")
            
            # Apply intelligent fallback for unmapped fields
            unmapped_headers = [h for h in headers if h not in mappings]
            fallback_mappings = self._apply_fallback_field_mapping(unmapped_headers)
            mappings.update(fallback_mappings)
            
            logger.info(f"Field mapping parsed: {len(mappings)}/{len(headers)} fields mapped")
            
        except Exception as e:
            logger.warning(f"Enhanced field mapping parsing failed: {e}")
            mappings = self._apply_fallback_field_mapping(headers)
        
        return mappings
    
    def parse_asset_classification_result(self, result: str, sample_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse asset classification result with structured extraction."""
        classifications = []
        
        try:
            patterns = self.parsing_patterns["asset_classification"]
            
            # Split result into asset blocks
            asset_blocks = re.split(patterns["asset_block"], result)[1:]  # Skip first empty split
            
            for i, block in enumerate(asset_blocks[:len(sample_data)]):
                asset_data = sample_data[i] if i < len(sample_data) else {}
                
                classification = {
                    "asset_index": i,
                    "asset_data": asset_data,
                    "asset_type": "Server",  # Default
                    "migration_priority": "Medium",
                    "complexity_level": "Moderate", 
                    "risk_level": "Medium",
                    "has_dependencies": True,
                    "confidence_score": 0.75
                }
                
                # Extract structured information using patterns
                type_match = re.search(patterns["type"], block, re.IGNORECASE)
                if type_match:
                    classification["asset_type"] = type_match.group(1)
                
                priority_match = re.search(patterns["priority"], block, re.IGNORECASE)
                if priority_match:
                    classification["migration_priority"] = priority_match.group(1)
                
                complexity_match = re.search(patterns["complexity"], block, re.IGNORECASE)
                if complexity_match:
                    classification["complexity_level"] = complexity_match.group(1)
                
                risk_match = re.search(patterns["risk"], block, re.IGNORECASE)
                if risk_match:
                    classification["risk_level"] = risk_match.group(1)
                
                deps_match = re.search(patterns["dependencies"], block, re.IGNORECASE)
                if deps_match:
                    classification["has_dependencies"] = deps_match.group(1).lower() == 'yes'
                
                conf_match = re.search(patterns["confidence"], block, re.IGNORECASE)
                if conf_match:
                    classification["confidence_score"] = float(conf_match.group(1))
                
                # Apply intelligent classification enhancement
                enhanced_classification = self._enhance_asset_classification(classification, asset_data)
                classifications.append(enhanced_classification)
            
            logger.info(f"Asset classification parsed: {len(classifications)} assets")
            
        except Exception as e:
            logger.warning(f"Enhanced asset classification parsing failed: {e}")
            classifications = self._apply_fallback_asset_classification(sample_data)
        
        return classifications
    
    def _apply_fallback_field_mapping(self, headers: List[str]) -> Dict[str, str]:
        """Apply intelligent fallback field mapping using pattern matching."""
        mappings = {}
        field_patterns = self.fallback_mappings["field_patterns"]
        
        for header in headers:
            header_lower = header.lower()
            mapped = False
            
            # Try to match against known patterns
            for attribute, patterns in field_patterns.items():
                if any(pattern in header_lower for pattern in patterns):
                    mappings[header] = attribute
                    mapped = True
                    break
            
            # Default mapping for unmapped fields
            if not mapped:
                mappings[header] = 'custom_attribute'
        
        return mappings
    
    def _enhance_asset_classification(self, classification: Dict[str, Any], asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance asset classification using data content analysis."""
        enhanced = classification.copy()
        asset_types = self.fallback_mappings["asset_types"]
        
        # Analyze asset data content for better classification
        content_text = " ".join(str(v).lower() for v in asset_data.values() if v)
        
        # Detect asset type from content
        for asset_type, patterns in asset_types.items():
            if any(pattern in content_text for pattern in patterns):
                detected_type = asset_type.replace("_patterns", "").title()
                enhanced["asset_type"] = detected_type
                
                # Adjust priority and complexity based on type
                if "database" in asset_type:
                    enhanced["migration_priority"] = "High"
                    enhanced["complexity_level"] = "Complex"
                    enhanced["risk_level"] = "High"
                elif "application" in asset_type:
                    enhanced["migration_priority"] = "Medium"
                    enhanced["complexity_level"] = "Moderate"
                elif "network" in asset_type:
                    enhanced["migration_priority"] = "High"
                    enhanced["complexity_level"] = "Complex"
                
                break
        
        return enhanced
    
    def _apply_fallback_asset_classification(self, sample_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply intelligent fallback asset classification."""
        classifications = []
        
        for i, asset in enumerate(sample_data[:5]):
            # Smart classification based on data content
            asset_type = "Server"
            priority = "Medium"
            complexity = "Moderate"
            risk = "Medium"
            
            # Analyze content for classification hints
            content_text = " ".join(str(v).lower() for v in asset.values() if v)
            
            # Database detection
            if any(term in content_text for term in ['database', 'db', 'sql', 'oracle', 'mysql']):
                asset_type = "Database"
                priority = "High"
                complexity = "Complex"
                risk = "High"
            # Application detection
            elif any(term in content_text for term in ['application', 'app', 'web', 'service']):
                asset_type = "Application"
                priority = "Medium"
                complexity = "Moderate"
            # Network device detection
            elif any(term in content_text for term in ['router', 'switch', 'firewall', 'network']):
                asset_type = "Network"
                priority = "High"
                complexity = "Complex"
            
            classifications.append({
                "asset_index": i,
                "asset_data": asset,
                "asset_type": asset_type,
                "migration_priority": priority,
                "complexity_level": complexity,
                "risk_level": risk,
                "has_dependencies": True,
                "confidence_score": 0.75
            })
        
        return classifications
    
    def extract_insights_from_result(self, result: str, result_type: str) -> Dict[str, Any]:
        """Extract general insights from AI agent results."""
        insights = {
            "result_type": result_type,
            "key_findings": [],
            "recommendations": [],
            "confidence_indicators": [],
            "data_quality_notes": []
        }
        
        try:
            # Extract key findings (sentences with numbers or percentages)
            finding_pattern = r'[^.!?]*(?:\d+(?:\.\d+)?%?|score|quality|coverage)[^.!?]*[.!?]'
            findings = re.findall(finding_pattern, result, re.IGNORECASE)
            insights["key_findings"] = [f.strip() for f in findings[:5]]
            
            # Extract recommendations (action-oriented sentences)
            recommendation_pattern = r'[^.!?]*(?:recommend|suggest|should|must|need)[^.!?]*[.!?]'
            recommendations = re.findall(recommendation_pattern, result, re.IGNORECASE)
            insights["recommendations"] = [r.strip() for r in recommendations[:3]]
            
            # Extract confidence indicators
            confidence_pattern = r'(?:confidence|certain|likely|probable):\s*([\d.]+)'
            confidences = re.findall(confidence_pattern, result, re.IGNORECASE)
            insights["confidence_indicators"] = [float(c) for c in confidences]
            
        except Exception as e:
            logger.warning(f"Failed to extract insights: {e}")
        
        return insights
    
    def validate_parsed_result(self, parsed_data: Any, expected_type: str) -> bool:
        """Validate parsed result structure and content."""
        try:
            if expected_type == "validation":
                required_keys = ["quality_score", "missing_fields", "issues", "ready", "actions"]
                return all(key in parsed_data for key in required_keys)
            
            elif expected_type == "field_mapping":
                return isinstance(parsed_data, dict) and len(parsed_data) > 0
            
            elif expected_type == "asset_classification":
                if not isinstance(parsed_data, list) or len(parsed_data) == 0:
                    return False
                required_keys = ["asset_index", "asset_type", "migration_priority", "confidence_score"]
                return all(all(key in item for key in required_keys) for item in parsed_data)
            
        except Exception as e:
            logger.error(f"Validation failed for {expected_type}: {e}")
            return False
        
        return False
    
    def get_parsing_summary(self) -> Dict[str, Any]:
        """Get parsing handler summary and statistics."""
        return {
            "handler": "parsing_handler",
            "version": "1.0.0",
            "supported_result_types": ["validation", "field_mapping", "asset_classification"],
            "parsing_patterns": {
                "validation_patterns": len(self.parsing_patterns["validation"]),
                "field_mapping_patterns": len(self.parsing_patterns["field_mapping"]),
                "asset_classification_patterns": len(self.parsing_patterns["asset_classification"])
            },
            "fallback_capabilities": {
                "field_mapping_patterns": len(self.fallback_mappings["field_patterns"]),
                "asset_type_detection": len(self.fallback_mappings["asset_types"])
            },
            "features": [
                "regex_pattern_matching",
                "confidence_scoring", 
                "intelligent_fallbacks",
                "content_analysis",
                "structured_extraction"
            ]
        } 