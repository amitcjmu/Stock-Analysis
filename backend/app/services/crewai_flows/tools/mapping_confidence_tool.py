"""
Mapping Confidence Tools for Field Mapping Crew
Provides confidence scoring and validation for field mappings
"""

import json
import logging
from typing import Any, Dict, List, Optional

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class MappingConfidenceTool(BaseTool):
    name: str = "mapping_confidence_tool"
    description: str = "Analyzes field mappings and provides confidence scores based on pattern matching and semantic analysis"
    
    def _run(self, field_mappings: str) -> str:
        """
        Analyze field mappings and provide confidence scores
        
        Args:
            field_mappings: JSON string of field mappings to analyze
            
        Returns:
            JSON string with confidence scores and validation results
        """
        try:
            mappings = json.loads(field_mappings)
            
            # Standard migration attributes for confidence scoring
            standard_attributes = {
                "asset_name": ["name", "hostname", "server_name", "asset_name", "device_name"],
                "asset_type": ["type", "asset_type", "category", "classification"],
                "asset_id": ["id", "asset_id", "ci_id", "sys_id"],
                "environment": ["environment", "env", "stage", "tier"],
                "business_criticality": ["criticality", "priority", "importance", "tier"],
                "operating_system": ["os", "operating_system", "platform"],
                "ip_address": ["ip", "ip_address", "primary_ip"],
                "location": ["location", "site", "datacenter", "facility"]
            }
            
            confidence_results = {}
            validation_results = {}
            
            for source_field, target_attribute in mappings.items():
                # Calculate confidence based on name similarity
                confidence = 0.5  # Base confidence
                
                if target_attribute in standard_attributes:
                    # Check for exact matches
                    if source_field.lower() in [attr.lower() for attr in standard_attributes[target_attribute]]:
                        confidence = 1.0
                    # Check for partial matches
                    elif any(attr.lower() in source_field.lower() or source_field.lower() in attr.lower() 
                            for attr in standard_attributes[target_attribute]):
                        confidence = 0.85
                    # Semantic similarity (simplified)
                    elif any(word in source_field.lower() for word in target_attribute.split('_')):
                        confidence = 0.7
                
                confidence_results[source_field] = {
                    "target": target_attribute,
                    "confidence": confidence,
                    "reasoning": self._get_mapping_reasoning(source_field, target_attribute, confidence)
                }
                
                # Validation
                validation_results[source_field] = {
                    "valid": confidence >= 0.6,
                    "needs_review": confidence < 0.8,
                    "issues": [] if confidence >= 0.6 else ["Low confidence mapping"]
                }
            
            return json.dumps({
                "confidence_scores": confidence_results,
                "validation_results": validation_results,
                "overall_confidence": sum(r["confidence"] for r in confidence_results.values()) / len(confidence_results) if confidence_results else 0,
                "requires_human_review": any(r["needs_review"] for r in validation_results.values())
            })
            
        except Exception as e:
            logger.error(f"Error in mapping confidence tool: {e}")
            return json.dumps({"error": str(e)})
    
    def _get_mapping_reasoning(self, source: str, target: str, confidence: float) -> str:
        """Generate reasoning for mapping confidence score"""
        if confidence >= 0.9:
            return f"High confidence: '{source}' closely matches standard attribute '{target}'"
        elif confidence >= 0.7:
            return f"Good confidence: '{source}' has semantic similarity to '{target}'"
        elif confidence >= 0.5:
            return f"Medium confidence: '{source}' may relate to '{target}' but needs verification"
        else:
            return f"Low confidence: '{source}' to '{target}' mapping is uncertain"

class ValidationTool(BaseTool):
    name: str = "validation_tool"
    description: str = "Validates field mappings against business rules and data quality standards"
    
    def _run(self, mapping_data: str) -> str:
        """
        Validate field mappings against business rules
        
        Args:
            mapping_data: JSON string with mapping data to validate
            
        Returns:
            JSON string with validation results
        """
        try:
            data = json.loads(mapping_data)
            
            # Required fields for migration
            required_fields = ["asset_name", "asset_type"]
            business_critical_fields = ["environment", "business_criticality"]
            
            validation_results = {
                "required_fields_mapped": [],
                "missing_required_fields": [],
                "business_critical_mapped": [],
                "missing_business_critical": [],
                "unmapped_source_fields": [],
                "validation_score": 0.0,
                "validation_passed": False
            }
            
            mapped_targets = list(data.get("mappings", {}).values())
            source_fields = list(data.get("mappings", {}).keys())
            
            # Check required fields
            for field in required_fields:
                if field in mapped_targets:
                    validation_results["required_fields_mapped"].append(field)
                else:
                    validation_results["missing_required_fields"].append(field)
            
            # Check business critical fields
            for field in business_critical_fields:
                if field in mapped_targets:
                    validation_results["business_critical_mapped"].append(field)
                else:
                    validation_results["missing_business_critical"].append(field)
            
            # Calculate validation score
            required_score = len(validation_results["required_fields_mapped"]) / len(required_fields)
            business_score = len(validation_results["business_critical_mapped"]) / len(business_critical_fields)
            validation_results["validation_score"] = (required_score * 0.7) + (business_score * 0.3)
            validation_results["validation_passed"] = validation_results["validation_score"] >= 0.7
            
            return json.dumps(validation_results)
            
        except Exception as e:
            logger.error(f"Error in validation tool: {e}")
            return json.dumps({"error": str(e)}) 