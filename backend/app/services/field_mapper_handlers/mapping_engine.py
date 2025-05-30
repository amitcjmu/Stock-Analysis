"""
Mapping Engine Handler
Handles core field mapping, learning, and matching functionality.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class MappingEngineHandler:
    """Handles core mapping engine operations with graceful fallbacks."""
    
    def __init__(self, data_dir: str = "data"):
        self.service_available = True
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.mappings_file = self.data_dir / "field_mappings.json"
        
        # Enhanced base field mappings
        self.base_mappings = {
            'Asset Name': ['name', 'asset_name', 'hostname', 'ci_name', 'server_name', 'host_name'],
            'Asset Type': ['type', 'asset_type', 'ci_type', 'classification', 'category', 'device_type'],
            'Environment': ['environment', 'env', 'stage', 'tier', 'deployment_stage'],
            'Operating System': ['os', 'operating_system', 'platform', 'os_version', 'os_type'],
            'CPU Cores': ['cpu', 'cores', 'cpu_cores', 'processors', 'vcpu', 'cpu_count'],
            'Memory (GB)': ['memory', 'memory_gb', 'ram', 'ram_gb', 'mem', 'memory_size'],
            'Storage (GB)': ['storage', 'storage_gb', 'disk', 'disk_gb', 'storage_size'],
            'IP Address': ['ip_address', 'ip', 'network_address', 'primary_ip', 'mgmt_ip'],
            'Business Owner': ['business_owner', 'owner', 'application_owner', 'responsible_party'],
            'Criticality': ['criticality', 'business_criticality', 'priority', 'importance', 'tier'],
            'Application Service': ['application', 'service', 'business_service', 'app_name'],
            'Version': ['version', 'release', 'build', 'software_version', 'app_version'],
            'Dependencies': ['related_ci', 'depends_on', 'relationships', 'dependencies'],
            'Location': ['location', 'site', 'datacenter', 'dc', 'facility'],
            'Vendor': ['vendor', 'manufacturer', 'make', 'brand'],
            'Model': ['model', 'device_model', 'hardware_model', 'product_model']
        }
        
        self.learned_mappings = self._load_learned_mappings()
        logger.info("Mapping engine handler initialized successfully")
    
    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return True  # Always available with fallbacks
    
    def _load_learned_mappings(self) -> Dict[str, List[str]]:
        """Load learned mappings from file."""
        try:
            if self.mappings_file.exists():
                with open(self.mappings_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading learned mappings: {e}")
            return {}
    
    def _save_learned_mappings(self):
        """Save learned mappings to file."""
        try:
            with open(self.mappings_file, 'w') as f:
                json.dump(self.learned_mappings, f, indent=2)
            logger.info("Learned mappings saved successfully")
        except Exception as e:
            logger.error(f"Error saving learned mappings: {e}")
    
    def get_field_mappings(self, asset_type: str = 'server') -> Dict[str, List[str]]:
        """Get all field mappings for asset type."""
        try:
            # Combine base and learned mappings
            all_mappings = {}
            
            # Add base mappings
            for field, variations in self.base_mappings.items():
                all_mappings[field] = list(variations)
            
            # Add learned mappings
            for field, variations in self.learned_mappings.items():
                if field in all_mappings:
                    # Merge with existing variations
                    all_mappings[field].extend(v for v in variations if v not in all_mappings[field])
                else:
                    all_mappings[field] = list(variations)
            
            return all_mappings
            
        except Exception as e:
            logger.error(f"Error getting field mappings: {e}")
            return self.base_mappings
    
    def learn_field_mapping(self, canonical_field: str, field_variations: List[str], 
                           source: str = "manual") -> Dict[str, Any]:
        """Learn new field mapping variations."""
        try:
            # Normalize variations
            normalized_variations = [v.lower().strip().replace(' ', '_') for v in field_variations]
            
            # Add to learned mappings
            if canonical_field not in self.learned_mappings:
                self.learned_mappings[canonical_field] = []
            
            # Add new variations
            added_count = 0
            for variation in normalized_variations:
                if variation not in self.learned_mappings[canonical_field]:
                    self.learned_mappings[canonical_field].append(variation)
                    added_count += 1
            
            # Save to file
            self._save_learned_mappings()
            
            logger.info(f"Learned {added_count} new variations for '{canonical_field}' from {source}")
            
            return {
                "success": True,
                "canonical_field": canonical_field,
                "variations_added": added_count,
                "total_variations": len(self.learned_mappings[canonical_field]),
                "source": source
            }
            
        except Exception as e:
            logger.error(f"Error learning field mapping: {e}")
            return {
                "success": False,
                "error": str(e),
                "canonical_field": canonical_field
            }
    
    def find_matching_fields(self, available_columns: List[str], required_field: str) -> List[str]:
        """Find matching columns for a required field."""
        try:
            matches = []
            required_lower = required_field.lower().replace(' ', '_')
            
            # Get all mappings
            all_mappings = self.get_field_mappings()
            
            # Check if required field is a canonical field
            field_variations = []
            for canonical, variations in all_mappings.items():
                if canonical.lower().replace(' ', '_') == required_lower:
                    field_variations = variations
                    break
            
            # If not found as canonical, treat as variation
            if not field_variations:
                field_variations = [required_field.lower().replace(' ', '_')]
            
            # Find matches in available columns
            for column in available_columns:
                column_lower = column.lower().replace(' ', '_')
                for variation in field_variations:
                    if variation in column_lower or column_lower in variation:
                        matches.append(column)
                        break
            
            return matches
            
        except Exception as e:
            logger.error(f"Error finding matching fields: {e}")
            return []
    
    def analyze_columns(self, columns: List[str], asset_type: str = "server") -> Dict[str, Any]:
        """Analyze columns and provide mapping insights."""
        try:
            all_mappings = self.get_field_mappings(asset_type)
            
            mapped_fields = {}
            unmapped_columns = []
            
            # Analyze each column
            for column in columns:
                found_mapping = False
                column_lower = column.lower().replace(' ', '_')
                
                # Check against all canonical fields
                for canonical_field, variations in all_mappings.items():
                    for variation in variations:
                        if variation == column_lower or variation in column_lower:
                            mapped_fields[column] = canonical_field
                            found_mapping = True
                            break
                    if found_mapping:
                        break
                
                if not found_mapping:
                    unmapped_columns.append(column)
            
            # Calculate coverage
            mapping_coverage = len(mapped_fields) / len(columns) if columns else 0
            
            return {
                "total_columns": len(columns),
                "mapped_columns": len(mapped_fields),
                "unmapped_columns": unmapped_columns,
                "mapped_fields": mapped_fields,
                "mapping_coverage": mapping_coverage,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing columns: {e}")
            return {
                "total_columns": len(columns),
                "mapped_columns": 0,
                "unmapped_columns": columns,
                "mapped_fields": {},
                "mapping_coverage": 0.0,
                "error": str(e)
            }
    
    def get_mapping_statistics(self) -> Dict[str, Any]:
        """Get statistics about field mappings."""
        try:
            base_fields = len(self.base_mappings)
            learned_fields = len(self.learned_mappings)
            total_variations = sum(len(variations) for variations in self.learned_mappings.values())
            
            return {
                "base_fields": base_fields,
                "learned_fields": learned_fields,
                "total_learned_variations": total_variations,
                "learning_effectiveness": learned_fields / (base_fields + learned_fields) if base_fields + learned_fields > 0 else 0,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting mapping statistics: {e}")
            return {
                "base_fields": 0,
                "learned_fields": 0,
                "total_learned_variations": 0,
                "learning_effectiveness": 0,
                "error": str(e)
            }
    
    def export_mappings(self, export_path: str) -> bool:
        """Export all mappings to file."""
        try:
            all_mappings = self.get_field_mappings()
            
            export_data = {
                "export_timestamp": datetime.utcnow().isoformat(),
                "base_mappings": self.base_mappings,
                "learned_mappings": self.learned_mappings,
                "combined_mappings": all_mappings
            }
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Mappings exported to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting mappings: {e}")
            return False 