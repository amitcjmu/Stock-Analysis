"""
Dynamic Field Mapping Service
Learns and maintains field mappings based on user feedback and AI agent learning.
"""

import logging
from typing import Dict, List, Set, Optional
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
        
        # Base field mappings - these are the starting point
        self.base_mappings = {
            'Asset Name': ['name', 'asset_name', 'hostname', 'ci_name', 'computer_name', 'server_name'],
            'Asset Type': ['type', 'asset_type', 'ci_type', 'classification', 'sys_class_name'],
            'Environment': ['environment', 'env', 'stage', 'tier'],
            'Business Owner': ['owner', 'business_owner', 'responsible_party', 'assigned_to'],
            'Criticality': ['criticality', 'business_criticality', 'priority', 'importance'],
            'Operating System': ['os', 'operating_system', 'platform', 'os_name', 'os_version'],
            'CPU Cores': ['cpu', 'cores', 'processors', 'vcpu', 'cpu_cores'],
            'Memory (GB)': ['memory', 'ram', 'memory_gb', 'mem', 'ram_gb'],  # Enhanced with ram_gb
            'Storage (GB)': ['storage', 'disk', 'storage_gb', 'disk_gb', 'hdd'],
            'IP Address': ['ip_address', 'ip', 'network_address', 'host_ip'],
            'MAC Address': ['mac_address', 'mac', 'ethernet_address'],
            'Application Service': ['application', 'service', 'application_service', 'business_service'],
            'Version': ['version', 'release', 'build', 'app_version'],
            'Dependencies': ['related_ci', 'depends_on', 'relationships', 'dependencies']
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
        """Extract field mapping from a pattern string."""
        
        pattern_lower = pattern.lower()
        
        # Extract memory field mappings
        if 'ram_gb' in pattern_lower and 'memory' in pattern_lower:
            memory_fields = ['ram_gb', 'memory_gb', 'memory (gb)', 'memory', 'ram']
            self.learn_field_mapping('Memory (GB)', memory_fields, "pattern_extraction")
        
        # Extract CPU field mappings
        if 'cpu_cores' in pattern_lower and 'cores' in pattern_lower:
            cpu_fields = ['cpu_cores', 'cores', 'cpu', 'processors', 'vcpu']
            self.learn_field_mapping('CPU Cores', cpu_fields, "pattern_extraction")
        
        # Extract asset name mappings
        if 'asset_name' in pattern_lower and 'name' in pattern_lower:
            name_fields = ['asset_name', 'asset name', 'name', 'hostname', 'ci_name']
            self.learn_field_mapping('Asset Name', name_fields, "pattern_extraction")
    
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


# Global instance
field_mapper = DynamicFieldMapper() 