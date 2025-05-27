"""
Dynamic Field Mapping Service
Learns and maintains field mappings based on user feedback and AI agent learning.
"""

import logging
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class DynamicFieldMapper:
    """Manages dynamic field mappings that learn from user feedback."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.mappings_file = self.data_dir / "field_mappings.json"
        
        # Base field mappings - MINIMAL starting point, AI should learn the rest
        self.base_mappings = {
            'Asset Name': ['name', 'asset_name', 'hostname'],
            'Asset Type': ['type', 'asset_type', 'ci_type'],
            'Environment': ['environment', 'env'],
            'Operating System': ['os', 'operating_system'],
            'CPU Cores': ['cpu', 'cores'],
            'Memory (GB)': ['memory', 'memory_gb'],  # AI must learn ram_gb mapping
            'Storage (GB)': ['storage', 'storage_gb'],
            'IP Address': ['ip_address', 'ip'],
            'MAC Address': ['mac_address', 'mac'],
            'Application Service': ['application', 'service'],
            'Version': ['version', 'release'],
            'Dependencies': ['related_ci', 'depends_on']
            # Business Owner and Criticality removed - AI must learn these mappings
        }
        
        # Load existing learned mappings
        self.learned_mappings = self._load_learned_mappings()
        
    def _load_learned_mappings(self) -> Dict[str, List[str]]:
        """Load learned field mappings from file."""
        try:
            if self.mappings_file.exists():
                with open(self.mappings_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load learned mappings: {e}")
        
        return {}
    
    def _save_learned_mappings(self):
        """Save learned field mappings to file."""
        try:
            with open(self.mappings_file, 'w') as f:
                json.dump(self.learned_mappings, f, indent=2)
            logger.info(f"Saved learned mappings to {self.mappings_file}")
        except Exception as e:
            logger.error(f"Could not save learned mappings: {e}")
    
    def get_field_mappings(self, asset_type: str = 'server') -> Dict[str, List[str]]:
        """Get complete field mappings (base + learned) for an asset type."""
        
        # Start with base mappings
        complete_mappings = {}
        for field_name, variations in self.base_mappings.items():
            complete_mappings[field_name] = list(variations)
        
        # Add learned mappings
        for field_name, learned_variations in self.learned_mappings.items():
            if field_name in complete_mappings:
                # Merge with existing mappings, avoiding duplicates
                existing = set(complete_mappings[field_name])
                learned = set(learned_variations)
                complete_mappings[field_name] = list(existing | learned)
            else:
                # New field mapping learned
                complete_mappings[field_name] = learned_variations
        
        # Filter mappings based on asset type relevance
        if asset_type == 'application':
            # Applications don't need hardware specs
            irrelevant_fields = ['CPU Cores', 'Memory (GB)', 'Storage (GB)', 'IP Address', 'MAC Address']
            for field in irrelevant_fields:
                if field in complete_mappings:
                    del complete_mappings[field]
        elif asset_type == 'database':
            # Databases have specific requirements
            complete_mappings['Database Name'] = ['db_name', 'database_name', 'instance_name']
            complete_mappings['Database Type'] = ['db_type', 'database_type', 'engine']
            complete_mappings['Port'] = ['port', 'db_port', 'connection_port']
            complete_mappings['Host Server'] = ['host', 'server', 'hostname', 'host_server']
        
        return complete_mappings
    
    def learn_field_mapping(self, canonical_field: str, field_variations: List[str], source: str = "user_feedback"):
        """Learn a new field mapping from user feedback or AI analysis."""
        
        # Normalize field variations
        normalized_variations = [var.lower().strip() for var in field_variations if var]
        
        if canonical_field in self.learned_mappings:
            # Add to existing learned mappings
            existing = set(self.learned_mappings[canonical_field])
            new_variations = set(normalized_variations)
            self.learned_mappings[canonical_field] = list(existing | new_variations)
        else:
            # New field mapping
            self.learned_mappings[canonical_field] = normalized_variations
        
        # Save the updated mappings
        self._save_learned_mappings()
        
        logger.info(f"Learned field mapping for '{canonical_field}': {normalized_variations} (source: {source})")
    
    def process_feedback_patterns(self, patterns: List[str]):
        """Process feedback patterns to extract field mappings."""
        
        for pattern in patterns:
            if 'field mapping:' in pattern.lower():
                self._extract_mapping_from_pattern(pattern)
    
    def _extract_mapping_from_pattern(self, pattern: str):
        """Extract field mapping from a pattern string using AI-driven pattern recognition."""
        
        pattern_lower = pattern.lower()
        
        # Generic field mapping extraction using regex - let AI determine the mappings
        import re
        
        # Pattern: "field X should map to Y" or "X maps to Y"
        mapping_patterns = [
            r'(\w+(?:_\w+)*)\s+(?:should\s+)?(?:map|maps)\s+to\s+["\']?([^"\']+)["\']?',
            r'["\']?([^"\']+)["\']?\s+(?:should\s+)?(?:map|maps)\s+to\s+(\w+(?:_\w+)*)',
            r'field\s+["\']?([^"\']+)["\']?\s+(?:is\s+)?(?:same\s+as|equivalent\s+to)\s+["\']?([^"\']+)["\']?',
            r'(\w+(?:_\w+)*)\s+(?:is\s+)?(?:available|present)\s+(?:for|as)\s+["\']?([^"\']+)["\']?',
            r'["\']?([^"\']+)["\']?\s+(?:shows|appears)\s+as\s+(\w+(?:_\w+)*)',
            r'(\w+(?:_\w+)*)\s+(?:should\s+be\s+)?(?:recognized\s+as)\s+["\']?([^"\']+)["\']?'
        ]
        
        for regex_pattern in mapping_patterns:
            matches = re.findall(regex_pattern, pattern_lower, re.IGNORECASE)
            for match in matches:
                source_field, target_field = match
                # Determine which is the canonical field name
                canonical_field = self._determine_canonical_field(source_field, target_field)
                if canonical_field:
                    variations = [source_field.strip(), target_field.strip()]
                    self.learn_field_mapping(canonical_field, variations, "ai_pattern_extraction")
                    logger.info(f"AI extracted field mapping: {source_field} → {canonical_field}")
    
    def _determine_canonical_field(self, field1: str, field2: str) -> str:
        """Determine which field name should be the canonical one."""
        
        # Check if either field matches our known canonical names (base + learned)
        all_canonical_names = list(self.base_mappings.keys()) + list(self.learned_mappings.keys())
        
        for canonical in all_canonical_names:
            if canonical.lower().replace(' ', '_') in field1.lower() or canonical.lower() in field1.lower():
                return canonical
            if canonical.lower().replace(' ', '_') in field2.lower() or canonical.lower() in field2.lower():
                return canonical
        
        # Special mappings for common business terms
        business_mappings = {
            'application_owner': 'Business Owner',
            'business_owner': 'Business Owner', 
            'owner': 'Business Owner',
            'dr_tier': 'Criticality',
            'business_criticality': 'Criticality',
            'criticality': 'Criticality',
            'ram_gb': 'Memory (GB)',
            'memory_gb': 'Memory (GB)',
            'memory': 'Memory (GB)'
        }
        
        # Check if either field has a known business mapping
        field1_lower = field1.lower()
        field2_lower = field2.lower()
        
        if field1_lower in business_mappings:
            return business_mappings[field1_lower]
        if field2_lower in business_mappings:
            return business_mappings[field2_lower]
        
        # If neither matches, prefer the more descriptive one
        if len(field1) > len(field2):
            return field1.title().replace('_', ' ')
        else:
            return field2.title().replace('_', ' ')
    
    def find_matching_fields(self, available_columns: List[str], required_field: str) -> List[str]:
        """Find matching fields in available columns for a required field."""
        
        mappings = self.get_field_mappings()
        if required_field not in mappings:
            return []
        
        possible_variations = mappings[required_field]
        available_lower = [col.lower() for col in available_columns]
        
        matches = []
        for variation in possible_variations:
            if variation.lower() in available_lower:
                # Find the original case column name
                for original_col in available_columns:
                    if original_col.lower() == variation.lower():
                        matches.append(original_col)
                        break
        
        return matches
    
    def identify_missing_fields(self, available_columns: List[str], asset_type: str = 'server') -> List[str]:
        """Identify missing required fields using learned mappings."""
        
        mappings = self.get_field_mappings(asset_type)
        missing_fields = []
        
        for required_field, variations in mappings.items():
            matches = self.find_matching_fields(available_columns, required_field)
            if not matches:
                missing_fields.append(required_field)
        
        return missing_fields
    
    def get_mapping_statistics(self) -> Dict[str, any]:
        """Get statistics about learned mappings."""
        
        total_base_mappings = sum(len(variations) for variations in self.base_mappings.values())
        total_learned_mappings = sum(len(variations) for variations in self.learned_mappings.values())
        
        return {
            "base_field_types": len(self.base_mappings),
            "base_variations": total_base_mappings,
            "learned_field_types": len(self.learned_mappings),
            "learned_variations": total_learned_mappings,
            "total_field_types": len(set(self.base_mappings.keys()) | set(self.learned_mappings.keys())),
            "learning_effectiveness": total_learned_mappings / max(1, total_base_mappings),
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def export_mappings(self, export_path: str) -> bool:
        """Export all mappings for analysis or backup."""
        
        try:
            export_data = {
                "base_mappings": self.base_mappings,
                "learned_mappings": self.learned_mappings,
                "statistics": self.get_mapping_statistics(),
                "exported_at": datetime.utcnow().isoformat()
            }
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Field mappings exported to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export mappings: {e}")
            return False

    # External Tool Interface for AI Agents
    def agent_query_field_mapping(self, field_name: str) -> Dict[str, Any]:
        """
        External tool for agents to query field mappings.
        Returns all known variations for a canonical field name.
        """
        mappings = self.get_field_mappings()
        
        # Try exact match first
        if field_name in mappings:
            return {
                "canonical_field": field_name,
                "variations": mappings[field_name],
                "source": "exact_match",
                "confidence": 1.0
            }
        
        # Try fuzzy matching
        field_lower = field_name.lower().replace(' ', '_')
        for canonical, variations in mappings.items():
            canonical_lower = canonical.lower().replace(' ', '_')
            if field_lower in canonical_lower or canonical_lower in field_lower:
                return {
                    "canonical_field": canonical,
                    "variations": variations,
                    "source": "fuzzy_match",
                    "confidence": 0.8
                }
            
            # Check if field matches any variation
            for variation in variations:
                if field_lower == variation.lower() or variation.lower() in field_lower:
                    return {
                        "canonical_field": canonical,
                        "variations": variations,
                        "source": "variation_match",
                        "confidence": 0.9
                    }
        
        return {
            "canonical_field": None,
            "variations": [],
            "source": "no_match",
            "confidence": 0.0,
            "suggestion": "Consider learning this as a new field mapping"
        }
    
    def agent_learn_field_mapping(self, source_field: str, target_field: str, context: str = "") -> Dict[str, Any]:
        """
        External tool for agents to learn new field mappings from data analysis or feedback.
        
        Args:
            source_field: The field name found in data
            target_field: The canonical field name it should map to
            context: Additional context about where this mapping was learned
        """
        try:
            # Determine canonical field
            canonical_field = self._determine_canonical_field(source_field, target_field)
            
            # Learn the mapping
            variations = [source_field.lower().strip(), target_field.lower().strip()]
            self.learn_field_mapping(canonical_field, variations, f"agent_learning_{context}")
            
            return {
                "success": True,
                "canonical_field": canonical_field,
                "learned_variations": variations,
                "context": context,
                "message": f"Successfully learned mapping: {source_field} → {canonical_field}"
            }
            
        except Exception as e:
            logger.error(f"Agent failed to learn field mapping: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to learn mapping: {source_field} → {target_field}"
            }
    
    def agent_analyze_columns(self, columns: List[str], asset_type: str = "server") -> Dict[str, Any]:
        """
        External tool for agents to analyze available columns and identify mappings.
        
        Args:
            columns: List of column names from data
            asset_type: Type of asset being analyzed
            
        Returns:
            Analysis of field mappings and missing fields
        """
        try:
            # Get current mappings
            mappings = self.get_field_mappings(asset_type)
            
            # Analyze each column
            column_analysis = {}
            for col in columns:
                mapping_result = self.agent_query_field_mapping(col)
                column_analysis[col] = mapping_result
            
            # Identify missing fields
            missing_fields = self.identify_missing_fields(columns, asset_type)
            
            # Find potential new mappings
            unmapped_columns = [col for col in columns 
                              if column_analysis[col]["confidence"] == 0.0]
            
            return {
                "total_columns": len(columns),
                "mapped_columns": len(columns) - len(unmapped_columns),
                "unmapped_columns": unmapped_columns,
                "missing_fields": missing_fields,
                "column_mappings": column_analysis,
                "asset_type": asset_type,
                "suggestions": self._generate_mapping_suggestions(unmapped_columns, missing_fields)
            }
            
        except Exception as e:
            logger.error(f"Agent column analysis failed: {e}")
            return {
                "error": str(e),
                "message": "Column analysis failed"
            }
    
    def _generate_mapping_suggestions(self, unmapped_columns: List[str], missing_fields: List[str]) -> List[Dict[str, str]]:
        """Generate suggestions for potential field mappings."""
        suggestions = []
        
        for unmapped_col in unmapped_columns:
            col_lower = unmapped_col.lower()
            
            for missing_field in missing_fields:
                missing_lower = missing_field.lower().replace(' ', '_')
                
                # Simple similarity check
                if any(word in col_lower for word in missing_lower.split('_')):
                    suggestions.append({
                        "unmapped_column": unmapped_col,
                        "suggested_mapping": missing_field,
                        "reason": f"Column '{unmapped_col}' contains keywords from '{missing_field}'"
                    })
        
        return suggestions
    
    def agent_get_mapping_context(self) -> Dict[str, Any]:
        """
        External tool for agents to get context about the current state of field mappings.
        Useful for agents to understand what they've learned so far.
        """
        stats = self.get_mapping_statistics()
        
        # Get recent learning activity
        recent_mappings = {}
        for field, variations in self.learned_mappings.items():
            if variations:  # Only include fields with learned variations
                recent_mappings[field] = variations
        
        return {
            "mapping_statistics": stats,
            "learned_mappings": recent_mappings,
            "base_field_types": list(self.base_mappings.keys()),
            "total_variations_learned": sum(len(v) for v in self.learned_mappings.values()),
            "learning_effectiveness": stats.get("learning_effectiveness", 0),
            "context_message": f"Currently tracking {len(self.base_mappings)} base field types with {stats.get('learned_variations', 0)} learned variations"
        }


# Global instance
field_mapper = DynamicFieldMapper() 