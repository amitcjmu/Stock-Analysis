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
        
        # Enhanced base field mappings with comprehensive variations
        self.base_mappings = {
            'Asset Name': ['name', 'asset_name', 'hostname', 'ci_name', 'server_name', 'host_name', 'computer_name', 'machine_name'],
            'Asset Type': ['type', 'asset_type', 'ci_type', 'classification', 'category', 'device_type', 'workload_type', 'workload type'],
            'Environment': ['environment', 'env', 'stage', 'tier', 'deployment_stage'],
            'Operating System': ['os', 'operating_system', 'platform', 'os_version', 'operating_system_version', 'os_type', 'os type'],
            'CPU Cores': ['cpu', 'cores', 'cpu_cores', 'processors', 'vcpu', 'cpu_count', 'processor_count', 'cpu cores'],
            'Memory (GB)': ['memory', 'memory_gb', 'ram', 'ram_gb', 'mem', 'memory_size', 'ram_size', 'ram (gb)'],
            'Storage (GB)': ['storage', 'storage_gb', 'disk', 'disk_gb', 'storage_size', 'disk_size', 'disk size (gb)'],
            'IP Address': ['ip_address', 'ip', 'network_address', 'primary_ip', 'mgmt_ip'],
            'MAC Address': ['mac_address', 'mac', 'physical_address', 'ethernet_address'],
            'Business Owner': ['business_owner', 'owner', 'application_owner', 'responsible_party', 'business_contact'],
            'Criticality': ['criticality', 'business_criticality', 'priority', 'importance', 'dr_tier', 'tier'],
            'Application Service': ['application', 'service', 'business_service', 'app_name', 'service_name'],
            'Version': ['version', 'release', 'build', 'software_version', 'app_version'],
            'Dependencies': ['related_ci', 'depends_on', 'relationships', 'dependencies', 'application_mapped'],
            'Location': ['location', 'site', 'datacenter', 'dc', 'facility'],
            'Vendor': ['vendor', 'manufacturer', 'make', 'brand'],
            'Model': ['model', 'device_model', 'hardware_model', 'product_model']
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

    def analyze_data_patterns(self, columns: List[str], sample_data: List[List[Any]], asset_type: str = "server") -> Dict[str, Any]:
        """
        Analyze data patterns to suggest field mappings based on content analysis.
        This goes beyond column name matching to examine actual data patterns.
        """
        try:
            suggestions = {}
            confidence_scores = {}
            
            for i, column in enumerate(columns):
                # Extract sample values for this column
                sample_values = []
                for row in sample_data:
                    if i < len(row) and row[i] is not None:
                        sample_values.append(str(row[i]).strip())
                
                if not sample_values:
                    continue
                
                # Analyze column patterns
                pattern_analysis = self._analyze_column_content(column, sample_values)
                
                if pattern_analysis["suggested_field"]:
                    suggestions[column] = pattern_analysis["suggested_field"]
                    confidence_scores[column] = pattern_analysis["confidence"]
            
            return {
                "column_analysis": suggestions,
                "confidence_scores": confidence_scores,
                "total_columns_analyzed": len(columns),
                "mappings_found": len(suggestions),
                "asset_type": asset_type
            }
            
        except Exception as e:
            logger.error(f"Data pattern analysis failed: {e}")
            return {
                "error": str(e),
                "column_analysis": {},
                "confidence_scores": {}
            }
    
    def _analyze_column_content(self, column_name: str, sample_values: List[str]) -> Dict[str, Any]:
        """
        Analyze column content to determine the most likely field mapping.
        Uses both column name and data content patterns.
        """
        column_lower = column_name.lower().strip()
        suggestions = []
        
        # First check exact matches in base mappings
        for canonical_field, variations in self.base_mappings.items():
            for variation in variations:
                if variation.lower() == column_lower:
                    return {
                        "suggested_field": canonical_field,
                        "confidence": 0.95,
                        "reason": f"Exact match with known variation: {variation}"
                    }
        
        # Check learned mappings
        for canonical_field, variations in self.learned_mappings.items():
            for variation in variations:
                if variation.lower() == column_lower:
                    return {
                        "suggested_field": canonical_field,
                        "confidence": 0.90,
                        "reason": f"Exact match with learned variation: {variation}"
                    }
        
        # Analyze data content patterns
        content_analysis = self._analyze_data_content_patterns(sample_values)
        
        # Pattern-based suggestions
        if content_analysis["pattern_type"] == "ip_address":
            suggestions.append(("IP Address", 0.85, "IP address pattern detected"))
        elif content_analysis["pattern_type"] == "mac_address":
            suggestions.append(("MAC Address", 0.85, "MAC address pattern detected"))
        elif content_analysis["pattern_type"] == "numeric_memory":
            suggestions.append(("Memory (GB)", 0.80, "Numeric memory values detected"))
        elif content_analysis["pattern_type"] == "numeric_cpu":
            suggestions.append(("CPU Cores", 0.80, "Numeric CPU values detected"))
        elif content_analysis["pattern_type"] == "hostname":
            suggestions.append(("Asset Name", 0.75, "Hostname pattern detected"))
        elif content_analysis["pattern_type"] == "workload_type":
            suggestions.append(("Asset Type", 0.85, "Workload type pattern detected"))
        elif content_analysis["pattern_type"] == "operating_system":
            suggestions.append(("Operating System", 0.85, "OS pattern detected"))
        elif content_analysis["pattern_type"] == "environment":
            suggestions.append(("Environment", 0.80, "Environment values detected"))
        elif content_analysis["pattern_type"] == "asset_type":
            suggestions.append(("Asset Type", 0.80, "Asset type values detected"))
        elif content_analysis["pattern_type"] == "criticality":
            suggestions.append(("Criticality", 0.75, "Criticality values detected"))
        
        # Fuzzy matching on column names
        fuzzy_suggestions = self._fuzzy_match_column_name(column_lower)
        suggestions.extend(fuzzy_suggestions)
        
        # Return best suggestion
        if suggestions:
            best_suggestion = max(suggestions, key=lambda x: x[1])
            return {
                "suggested_field": best_suggestion[0],
                "confidence": best_suggestion[1],
                "reason": best_suggestion[2]
            }
        
        return {
            "suggested_field": None,
            "confidence": 0.0,
            "reason": "No pattern match found"
        }
    
    def _analyze_data_content_patterns(self, sample_values: List[str]) -> Dict[str, Any]:
        """Analyze actual data content to identify patterns."""
        import re
        
        if not sample_values:
            return {"pattern_type": None, "confidence": 0.0}
        
        # Remove empty values
        values = [v for v in sample_values if v and v.strip()]
        if not values:
            return {"pattern_type": None, "confidence": 0.0}
        
        # IP Address pattern
        ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
        ip_matches = sum(1 for v in values if ip_pattern.match(v))
        if ip_matches / len(values) > 0.7:
            return {"pattern_type": "ip_address", "confidence": 0.9}
        
        # MAC Address pattern
        mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
        mac_matches = sum(1 for v in values if mac_pattern.match(v))
        if mac_matches / len(values) > 0.7:
            return {"pattern_type": "mac_address", "confidence": 0.9}
        
        # Numeric patterns
        numeric_values = []
        for v in values:
            try:
                numeric_values.append(float(v))
            except ValueError:
                continue
        
        if len(numeric_values) / len(values) > 0.8:
            # Check if values look like memory (typically 4, 8, 16, 32, 64, 128, etc.)
            if all(0 < n <= 1024 for n in numeric_values):
                memory_indicators = sum(1 for n in numeric_values if n in [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024])
                if memory_indicators / len(numeric_values) > 0.5:
                    return {"pattern_type": "numeric_memory", "confidence": 0.8}
                
                # Check if values look like CPU cores (typically 1, 2, 4, 8, 16, 32)
                cpu_indicators = sum(1 for n in numeric_values if n in [1, 2, 4, 8, 12, 16, 24, 32, 48, 64])
                if cpu_indicators / len(numeric_values) > 0.5:
                    return {"pattern_type": "numeric_cpu", "confidence": 0.8}
        
        # Hostname pattern
        hostname_pattern = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*$')
        hostname_matches = sum(1 for v in values if hostname_pattern.match(v) and len(v) > 2)
        if hostname_matches / len(values) > 0.7:
            return {"pattern_type": "hostname", "confidence": 0.7}
        
        # Workload/Asset Type pattern (specific server types)
        workload_keywords = ['db server', 'web server', 'app server', 'application server', 'database server', 'file server', 'mail server']
        workload_matches = sum(1 for v in values if any(keyword in v.lower() for keyword in workload_keywords))
        if workload_matches / len(values) > 0.5:
            return {"pattern_type": "workload_type", "confidence": 0.85}
        
        # Operating System pattern (specific OS names)
        os_keywords = ['windows', 'linux', 'ubuntu', 'centos', 'rhel', 'aix', 'solaris', 'macos', 'unix', 'server 2016', 'server 2019']
        os_matches = sum(1 for v in values if any(keyword in v.lower() for keyword in os_keywords))
        if os_matches / len(values) > 0.5:
            return {"pattern_type": "operating_system", "confidence": 0.8}
        
        # Environment pattern
        env_keywords = ['production', 'prod', 'development', 'dev', 'test', 'staging', 'qa', 'uat']
        env_matches = sum(1 for v in values if v.lower() in env_keywords)
        if env_matches / len(values) > 0.5:
            return {"pattern_type": "environment", "confidence": 0.85}
        
        # General Asset Type pattern (broader categories)
        asset_keywords = ['server', 'application', 'database', 'network', 'storage', 'vm', 'virtual']
        asset_matches = sum(1 for v in values if any(keyword in v.lower() for keyword in asset_keywords))
        if asset_matches / len(values) > 0.5:
            return {"pattern_type": "asset_type", "confidence": 0.8}
        
        # Criticality pattern
        crit_keywords = ['critical', 'high', 'medium', 'low', 'tier', '1', '2', '3', '4']
        crit_matches = sum(1 for v in values if v.lower() in crit_keywords or v in ['1', '2', '3', '4'])
        if crit_matches / len(values) > 0.5:
            return {"pattern_type": "criticality", "confidence": 0.75}
        
        return {"pattern_type": None, "confidence": 0.0}
    
    def _fuzzy_match_column_name(self, column_lower: str) -> List[tuple]:
        """Fuzzy match column names against known field variations."""
        suggestions = []
        
        # Split column name into words
        column_words = set(column_lower.replace('_', ' ').replace('-', ' ').split())
        
        for canonical_field, variations in self.base_mappings.items():
            max_score = 0
            best_reason = ""
            
            for variation in variations:
                variation_words = set(variation.replace('_', ' ').replace('-', ' ').split())
                
                # Calculate word overlap
                overlap = column_words.intersection(variation_words)
                if overlap:
                    score = len(overlap) / max(len(column_words), len(variation_words))
                    if score > max_score:
                        max_score = score
                        best_reason = f"Word overlap with '{variation}': {', '.join(overlap)}"
            
            # Also check if column name contains key words from canonical field
            canonical_words = set(canonical_field.lower().replace('(', '').replace(')', '').split())
            overlap = column_words.intersection(canonical_words)
            if overlap:
                score = len(overlap) / len(canonical_words)
                if score > max_score:
                    max_score = score
                    best_reason = f"Contains key words from '{canonical_field}': {', '.join(overlap)}"
            
            if max_score > 0.3:  # Minimum threshold for fuzzy matching
                suggestions.append((canonical_field, max_score * 0.7, best_reason))  # Reduce confidence for fuzzy matches
        
        return suggestions


# Global instance
field_mapper = DynamicFieldMapper() 