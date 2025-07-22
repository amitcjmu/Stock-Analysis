"""
Mapping Engine Handler
Handles core field mapping, learning, and matching functionality.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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
            'Memory (GB)': ['memory', 'memory_gb', 'ram', 'ram_gb', 'mem', 'memory_size', 'ram_(gb)', 'ram_gb', 'ram_in_gb', 'memory_in_gb'],
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
            
            # Find matches in available columns with enhanced fuzzy matching
            for column in available_columns:
                column_lower = column.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')
                for variation in field_variations:
                    variation_clean = variation.lower().replace('(', '').replace(')', '').replace('-', '_')
                    # Exact match
                    if variation_clean == column_lower:
                        matches.append(column)
                        break
                    # Contains match
                    elif variation_clean in column_lower or column_lower in variation_clean:
                        matches.append(column)
                        break
                    # Fuzzy match for similar terms (ram <-> memory)
                    elif self._fuzzy_match_fields(column_lower, variation_clean):
                        matches.append(column)
                        break
            
            return matches
            
        except Exception as e:
            logger.error(f"Error finding matching fields: {e}")
            return []
    
    def analyze_columns(self, columns: List[str], asset_type: str = "server", sample_data: Optional[List[List[str]]] = None) -> Dict[str, Any]:
        """Analyze columns and provide mapping insights with optional content analysis."""
        try:
            all_mappings = self.get_field_mappings(asset_type)
            
            mapped_fields = {}
            unmapped_columns = []
            confidence_scores = {}
            
            # Analyze each column
            for i, column in enumerate(columns):
                found_mapping = False
                column_lower = column.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')
                best_match = None
                best_confidence = 0.0
                
                # Check against all canonical fields with enhanced matching
                for canonical_field, variations in all_mappings.items():
                    for variation in variations:
                        variation_clean = variation.lower().replace('(', '').replace(')', '').replace('-', '_')
                        confidence = 0.0
                        
                        # Exact match - highest confidence
                        if variation_clean == column_lower:
                            confidence = 1.0
                        # Contains match - high confidence  
                        elif variation_clean in column_lower or column_lower in variation_clean:
                            confidence = 0.8
                        # Fuzzy match - medium confidence
                        elif self._fuzzy_match_fields(column_lower, variation_clean):
                            confidence = 0.6
                        
                        # Content-based analysis boost if sample data available
                        if sample_data and confidence > 0 and i < len(sample_data[0]):
                            content_boost = self._analyze_content_match(canonical_field, sample_data, i)
                            confidence = min(1.0, confidence + content_boost)
                        
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_match = canonical_field
                            found_mapping = confidence >= 0.5  # Confidence threshold
                
                if found_mapping and best_match:
                    mapped_fields[column] = best_match
                    confidence_scores[column] = best_confidence
                else:
                    unmapped_columns.append(column)
                    confidence_scores[column] = 0.0
            
            # Calculate coverage
            mapping_coverage = len(mapped_fields) / len(columns) if columns else 0
            
            return {
                "total_columns": len(columns),
                "mapped_columns": len(mapped_fields),
                "unmapped_columns": unmapped_columns,
                "mapped_fields": mapped_fields,
                "confidence_scores": confidence_scores,
                "mapping_coverage": mapping_coverage,
                "content_analysis_used": sample_data is not None,
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
    
    def _fuzzy_match_fields(self, field1: str, field2: str) -> bool:
        """Enhanced fuzzy matching for field names with semantic awareness."""
        try:
            # Semantic equivalence mappings
            semantic_groups = {
                frozenset(['ram', 'memory', 'mem']): 'memory',
                frozenset(['cpu', 'cores', 'processors', 'vcpu']): 'cpu',
                frozenset(['disk', 'storage', 'hdd', 'ssd']): 'storage',
                frozenset(['ip', 'address', 'network']): 'ip',
                frozenset(['os', 'operating', 'system', 'platform']): 'os',
                frozenset(['env', 'environment', 'stage', 'tier']): 'environment'
            }
            
            # Extract key terms from both fields
            field1_terms = set(field1.split('_'))
            field2_terms = set(field2.split('_'))
            
            # Check if both fields belong to the same semantic group
            for semantic_set, group_name in semantic_groups.items():
                if (semantic_set & field1_terms) and (semantic_set & field2_terms):
                    return True
            
            # Check for common suffixes/prefixes that indicate same type
            suffixes = ['_gb', '_tb', '_mb', '_id', '_name', '_type', '_count']
            for suffix in suffixes:
                if field1.endswith(suffix) and field2.endswith(suffix):
                    # Same suffix type - check base similarity
                    base1 = field1.replace(suffix, '')
                    base2 = field2.replace(suffix, '')
                    if base1 in base2 or base2 in base1:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error in fuzzy field matching: {e}")
            return False
    
    def _analyze_content_match(self, canonical_field: str, sample_data: List[List[str]], column_index: int) -> float:
        """AI-driven content analysis placeholder - enhanced analysis delegated to CrewAI Field Mapping Crew."""
        try:
            # Deprecated: Hard-coded heuristic content analysis has been removed
            # Content analysis is now handled by CrewAI Field Mapping Crew with semantic understanding
            
            # Simple fallback boost for when AI analysis is not available
            if sample_data and column_index < len(sample_data[0]):
                # Extract sample values for this column
                column_values = [row[column_index] for row in sample_data[:5] if len(row) > column_index]
                
                if column_values:
                    # Basic data quality check - if we have meaningful data, give small boost
                    non_empty_values = [v for v in column_values if str(v).strip() not in ['', 'N/A', 'NULL', 'None']]
                    if len(non_empty_values) > len(column_values) * 0.5:
                        return 0.1  # Small boost for having meaningful data
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error in content analysis: {e}")
            return 0.0

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