"""
Field Mapping Tool for AI Agents
External tool interface for dynamic field mapping learning and querying.
"""

import logging
from typing import Any, Dict, List

from app.services.field_mapper_modular import field_mapper

logger = logging.getLogger(__name__)


class FieldMappingTool:
    """
    External tool for AI agents to interact with the dynamic field mapping system.
    Agents can query existing mappings, learn new ones, and analyze data columns.
    """
    
    def __init__(self):
        self.field_mapper = field_mapper
        self.tool_name = "field_mapping_tool"
        self.description = "Tool for learning and querying field mappings between data columns and canonical field names"
    
    def query_field_mapping(self, field_name: str) -> Dict[str, Any]:
        """
        Query existing field mappings for a given field name.
        
        Args:
            field_name: The field name to look up
            
        Returns:
            Dictionary with mapping information and confidence score
        """
        try:
            result = self.field_mapper.agent_query_field_mapping(field_name)
            logger.info(f"Agent queried field mapping for '{field_name}': {result['source']}")
            return result
        except Exception as e:
            logger.error(f"Field mapping query failed: {e}")
            return {
                "canonical_field": None,
                "variations": [],
                "source": "error",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def learn_field_mapping(self, source_field: str, target_field: str, context: str = "agent_discovery") -> Dict[str, Any]:
        """
        Learn a new field mapping from agent analysis or user feedback.
        
        Args:
            source_field: The field name found in data
            target_field: The canonical field name it should map to
            context: Context about where this mapping was discovered
            
        Returns:
            Success status and learned mapping details
        """
        try:
            result = self.field_mapper.agent_learn_field_mapping(source_field, target_field, context)
            if result["success"]:
                logger.info(f"Agent learned new field mapping: {source_field} → {result['canonical_field']}")
            return result
        except Exception as e:
            logger.error(f"Field mapping learning failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to learn mapping: {source_field} → {target_field}"
            }
    
    def analyze_data_columns(self, columns: List[str], asset_type: str = "server") -> Dict[str, Any]:
        """
        Analyze a list of data columns to identify existing mappings and suggest new ones.
        
        Args:
            columns: List of column names from the data
            asset_type: Type of asset being analyzed (server, application, database)
            
        Returns:
            Analysis of column mappings and suggestions for unmapped columns
        """
        try:
            result = self.field_mapper.agent_analyze_columns(columns, asset_type)
            logger.info(f"Agent analyzed {len(columns)} columns for {asset_type} assets")
            return result
        except Exception as e:
            logger.error(f"Column analysis failed: {e}")
            return {
                "error": str(e),
                "message": "Column analysis failed"
            }
    
    def analyze_data_and_learn(self, columns: List[str], sample_data: List[List[Any]], asset_type: str = "server") -> Dict[str, Any]:
        """
        Analyze data patterns and auto-learn high-confidence mappings.
        This replaces the old `analyze_data_patterns` method.
        
        Args:
            columns: List of column names from the data
            sample_data: Sample data rows for pattern analysis
            asset_type: Type of asset being analyzed
            
        Returns:
            Comprehensive analysis with suggested field mappings based on patterns
        """
        try:
            # Use the correct method on the field_mapper service
            result = self.field_mapper.agent_analyze_columns(columns, asset_type)
            logger.info(f"Agent analyzed data patterns for {len(columns)} columns with {len(sample_data)} sample rows")
            
            # Auto-learn high-confidence mappings from the analysis result
            suggested_mappings = result.get("suggested_mappings", {})
            learned_mappings = []

            for column, suggestion in suggested_mappings.items():
                confidence = suggestion.get("confidence", 0.0)
                if confidence > 0.85:  # Auto-learn high-confidence mappings
                    target_field = suggestion.get("canonical_field")
                    if target_field:
                        learn_result = self.learn_field_mapping(column, target_field, f"auto_pattern_analysis_{asset_type}")
                        if learn_result.get("success"):
                            learned_mappings.append(f"{column} → {target_field} (confidence: {confidence:.2f})")
            
            result["auto_learned_mappings"] = learned_mappings
            return result
            
        except Exception as e:
            logger.error(f"Data pattern analysis and learning failed: {e}", exc_info=True)
            return {
                "error": str(e),
                "message": "Data pattern analysis and learning failed",
                "column_analysis": {},
                "confidence_scores": {}
            }
    
    def get_mapping_context(self) -> Dict[str, Any]:
        """
        Get current context about learned field mappings.
        Useful for agents to understand what they've learned so far.
        
        Returns:
            Current state of field mappings and learning statistics
        """
        try:
            result = self.field_mapper.agent_get_mapping_context()
            logger.info("Agent retrieved field mapping context")
            return result
        except Exception as e:
            logger.error(f"Failed to get mapping context: {e}")
            return {
                "error": str(e),
                "message": "Failed to retrieve mapping context"
            }
    
    def learn_from_feedback_text(self, feedback_text: str, context: str = "user_feedback") -> Dict[str, Any]:
        """
        Extract and learn field mappings from user feedback text.
        
        Args:
            feedback_text: User feedback containing field mapping information
            context: Context about the feedback source
            
        Returns:
            Mappings learned from the feedback text
        """
        try:
            # Process the feedback text to extract patterns
            patterns = [f"Field mapping pattern detected in feedback: {feedback_text}"]
            self.field_mapper.process_feedback_patterns(patterns)
            
            # Get statistics about what was learned
            stats = self.field_mapper.get_mapping_statistics()
            
            return {
                "success": True,
                "patterns_processed": len(patterns),
                "context": context,
                "learning_statistics": stats,
                "message": "Processed feedback text for field mapping patterns"
            }
            
        except Exception as e:
            logger.error(f"Failed to learn from feedback text: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process feedback text"
            }
    
    def suggest_mappings_for_missing_fields(self, available_columns: List[str], missing_fields: List[str]) -> List[Dict[str, Any]]:
        """
        Suggest potential mappings between available columns and missing required fields.
        
        Args:
            available_columns: Columns available in the data
            missing_fields: Required fields that are missing
            
        Returns:
            List of suggested mappings with confidence scores
        """
        try:
            suggestions = []
            
            for missing_field in missing_fields:
                # Query existing mappings for this field
                mapping_info = self.query_field_mapping(missing_field)
                
                if mapping_info["confidence"] > 0:
                    # Check if any available columns match known variations
                    for col in available_columns:
                        if col.lower() in [v.lower() for v in mapping_info["variations"]]:
                            suggestions.append({
                                "available_column": col,
                                "missing_field": missing_field,
                                "confidence": 0.9,
                                "reason": f"Column '{col}' matches known variation for '{missing_field}'"
                            })
                else:
                    # Use similarity matching for unknown fields
                    missing_lower = missing_field.lower().replace(' ', '_')
                    for col in available_columns:
                        col_lower = col.lower()
                        
                        # Check for keyword overlap
                        missing_words = set(missing_lower.split('_'))
                        col_words = set(col_lower.replace('_', ' ').split())
                        
                        overlap = missing_words.intersection(col_words)
                        if overlap:
                            confidence = len(overlap) / max(len(missing_words), len(col_words))
                            suggestions.append({
                                "available_column": col,
                                "missing_field": missing_field,
                                "confidence": confidence,
                                "reason": f"Keyword overlap: {', '.join(overlap)}"
                            })
            
            # Sort by confidence
            suggestions.sort(key=lambda x: x["confidence"], reverse=True)
            
            logger.info(f"Generated {len(suggestions)} mapping suggestions")
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to suggest mappings: {e}")
            return []
    
    def get_tool_description(self) -> Dict[str, Any]:
        """
        Get description of this tool for agent awareness.
        
        Returns:
            Tool description and available methods
        """
        return {
            "tool_name": self.tool_name,
            "description": self.description,
            "available_methods": [
                {
                    "name": "query_field_mapping",
                    "description": "Look up existing field mappings for a field name",
                    "parameters": ["field_name"]
                },
                {
                    "name": "learn_field_mapping", 
                    "description": "Learn a new field mapping from data or feedback",
                    "parameters": ["source_field", "target_field", "context"]
                },
                {
                    "name": "analyze_data_columns",
                    "description": "Analyze data columns to identify mappings and missing fields",
                    "parameters": ["columns", "asset_type"]
                },
                {
                    "name": "analyze_data_and_learn",
                    "description": "Analyze data patterns and auto-learn high-confidence mappings",
                    "parameters": ["columns", "sample_data", "asset_type"]
                },
                {
                    "name": "get_mapping_context",
                    "description": "Get current state of learned field mappings",
                    "parameters": []
                },
                {
                    "name": "learn_from_feedback_text",
                    "description": "Extract field mappings from user feedback text",
                    "parameters": ["feedback_text", "context"]
                },
                {
                    "name": "suggest_mappings_for_missing_fields",
                    "description": "Suggest mappings between available columns and missing fields",
                    "parameters": ["available_columns", "missing_fields"]
                }
            ],
            "usage_examples": [
                "Query if 'RAM_GB' maps to any canonical field",
                "Learn that 'APPLICATION_OWNER' maps to 'Business Owner'",
                "Analyze columns ['Asset_Name', 'RAM_GB', 'DR_TIER'] for server assets",
                "Get context about what field mappings have been learned so far"
            ]
        }


# Global tool instance for agents
field_mapping_tool = FieldMappingTool() 