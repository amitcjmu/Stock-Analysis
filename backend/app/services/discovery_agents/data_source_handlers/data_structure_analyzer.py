"""
Data Structure Analyzer Handler
Analyzes data structure, relationships, and content patterns.
"""

import logging
from typing import Dict, List, Any, Tuple
import re

logger = logging.getLogger(__name__)

class DataStructureAnalyzer:
    """Analyzes data structure and content patterns."""
    
    def __init__(self):
        self.analyzer_id = "data_structure_analyzer"
    
    async def analyze_data_structure(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the structure and patterns in the data."""
        
        if not data:
            return {
                "total_rows": 0,
                "column_analysis": {},
                "data_types": {},
                "patterns": [],
                "relationships": {}
            }
        
        # Basic structure analysis
        total_rows = len(data)
        all_columns = set()
        for row in data:
            all_columns.update(row.keys())
        
        column_analysis = await self._analyze_columns(data, list(all_columns))
        data_types = await self._analyze_data_types(data, list(all_columns))
        patterns = await self._identify_patterns(data)
        relationships = await self._detect_relationship_patterns(data)
        
        return {
            "total_rows": total_rows,
            "total_columns": len(all_columns),
            "column_analysis": column_analysis,
            "data_types": data_types,
            "patterns": patterns,
            "relationships": relationships,
            "structure_summary": await self._generate_structure_summary(
                total_rows, len(all_columns), column_analysis, patterns
            )
        }
    
    async def analyze_content_patterns(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze content patterns within the data."""
        
        if not data:
            return {"patterns": [], "insights": []}
        
        patterns = []
        insights = []
        
        # Sample data for pattern analysis
        sample_size = min(20, len(data))
        sample_data = data[:sample_size]
        
        # Analyze naming conventions
        naming_patterns = await self._analyze_naming_conventions(sample_data)
        if naming_patterns:
            patterns.extend(naming_patterns)
            insights.append(f"Detected {len(naming_patterns)} naming convention patterns")
        
        # Analyze value distributions
        value_patterns = await self._analyze_value_distributions(sample_data)
        patterns.extend(value_patterns)
        
        # Analyze field relationships
        relationship_patterns = await self._analyze_field_relationships(sample_data)
        if relationship_patterns:
            patterns.extend(relationship_patterns)
            insights.append(f"Found {len(relationship_patterns)} field relationship patterns")
        
        return {
            "patterns": patterns,
            "insights": insights,
            "sample_size": sample_size,
            "pattern_confidence": len(patterns) / max(len(sample_data), 1)
        }
    
    async def assess_migration_value(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess the migration value of the data."""
        
        if not data:
            return {
                "migration_value": "low",
                "confidence": 0.0,
                "assessment": "No data to evaluate"
            }
        
        # Criteria for migration value assessment
        value_indicators = {
            "asset_identification": 0,
            "environment_info": 0,
            "dependency_info": 0,
            "business_context": 0,
            "technical_details": 0
        }
        
        # Sample data for assessment
        sample_size = min(10, len(data))
        sample_data = data[:sample_size]
        
        for row in sample_data:
            for column, value in row.items():
                if not value:
                    continue
                
                column_lower = column.lower()
                
                # Asset identification indicators
                if any(keyword in column_lower for keyword in 
                      ['hostname', 'asset_name', 'server_name', 'system_name']):
                    value_indicators["asset_identification"] += 1
                
                # Environment information
                if any(keyword in column_lower for keyword in 
                      ['environment', 'env', 'stage', 'prod', 'dev']):
                    value_indicators["environment_info"] += 1
                
                # Dependency information
                if any(keyword in column_lower for keyword in 
                      ['depends', 'connect', 'service', 'application']):
                    value_indicators["dependency_info"] += 1
                
                # Business context
                if any(keyword in column_lower for keyword in 
                      ['owner', 'department', 'business', 'contact']):
                    value_indicators["business_context"] += 1
                
                # Technical details
                if any(keyword in column_lower for keyword in 
                      ['os', 'ip', 'cpu', 'memory', 'disk', 'version']):
                    value_indicators["technical_details"] += 1
        
        # Calculate overall migration value score
        total_indicators = sum(value_indicators.values())
        max_possible = len(sample_data) * 5  # 5 categories
        value_score = total_indicators / max_possible if max_possible > 0 else 0
        
        # Determine migration value category
        if value_score >= 0.7:
            migration_value = "high"
        elif value_score >= 0.4:
            migration_value = "medium"
        else:
            migration_value = "low"
        
        return {
            "migration_value": migration_value,
            "confidence": min(value_score * 1.2, 1.0),  # Boost confidence slightly
            "value_score": value_score,
            "indicators": value_indicators,
            "assessment": self._generate_migration_assessment(migration_value, value_indicators)
        }
    
    async def _analyze_columns(self, data: List[Dict[str, Any]], 
                              columns: List[str]) -> Dict[str, Any]:
        """Analyze individual columns for patterns and completeness."""
        
        column_analysis = {}
        
        for column in columns:
            values = []
            non_null_count = 0
            
            for row in data:
                if column in row:
                    value = row[column]
                    if value is not None and str(value).strip():
                        values.append(str(value))
                        non_null_count += 1
            
            completeness = non_null_count / len(data) if data else 0
            
            column_analysis[column] = {
                "completeness": completeness,
                "unique_values": len(set(values)) if values else 0,
                "sample_values": values[:5],  # First 5 non-null values
                "data_patterns": await self._identify_column_patterns(values)
            }
        
        return column_analysis
    
    async def _analyze_data_types(self, data: List[Dict[str, Any]], 
                                 columns: List[str]) -> Dict[str, str]:
        """Analyze and infer data types for each column."""
        
        data_types = {}
        
        for column in columns:
            values = []
            for row in data:
                if column in row and row[column] is not None:
                    values.append(str(row[column]).strip())
            
            if not values:
                data_types[column] = "unknown"
                continue
            
            # Sample values for type inference
            sample_values = values[:10]
            inferred_type = self._infer_data_type(sample_values)
            data_types[column] = inferred_type
        
        return data_types
    
    async def _identify_patterns(self, data: List[Dict[str, Any]]) -> List[str]:
        """Identify general patterns in the data."""
        
        patterns = []
        
        if not data:
            return patterns
        
        # Check for consistent row structure
        row_lengths = [len(row) for row in data]
        if len(set(row_lengths)) == 1:
            patterns.append(f"Consistent row structure: {row_lengths[0]} columns per row")
        
        # Check for hierarchical patterns
        hierarchical_fields = 0
        for row in data:
            for key in row.keys():
                if any(separator in key for separator in ['.', '_', '-']):
                    hierarchical_fields += 1
                    break
        
        if hierarchical_fields > len(data) * 0.5:
            patterns.append("Hierarchical field naming detected")
        
        # Check for standardized values
        environment_values = set()
        for row in data:
            for key, value in row.items():
                if "environment" in key.lower() and value:
                    environment_values.add(str(value).lower())
        
        if len(environment_values) <= 5 and len(environment_values) > 1:
            patterns.append(f"Standardized environment values: {', '.join(environment_values)}")
        
        return patterns
    
    async def _detect_relationship_patterns(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect relationships and dependencies between fields."""
        
        relationships = {
            "potential_keys": [],
            "foreign_key_candidates": [],
            "hierarchical_relationships": [],
            "grouping_fields": []
        }
        
        if not data or len(data) < 2:
            return relationships
        
        # Sample data for relationship analysis
        sample_data = data[:20]
        all_columns = set()
        for row in sample_data:
            all_columns.update(row.keys())
        
        # Identify potential primary keys (unique values)
        for column in all_columns:
            values = [str(row.get(column, "")) for row in sample_data if row.get(column)]
            if len(values) == len(set(values)) and len(values) > len(sample_data) * 0.8:
                relationships["potential_keys"].append(column)
        
        # Identify grouping fields (repeated values)
        for column in all_columns:
            values = [str(row.get(column, "")) for row in sample_data if row.get(column)]
            unique_ratio = len(set(values)) / len(values) if values else 0
            if 0.1 < unique_ratio < 0.5:  # Some repetition but not too much
                relationships["grouping_fields"].append(column)
        
        # Check for hierarchical relationships (parent-child patterns)
        for column in all_columns:
            if any(separator in column for separator in ['.', '_']) and 'id' not in column.lower():
                relationships["hierarchical_relationships"].append(column)
        
        return relationships
    
    async def _analyze_naming_conventions(self, data: List[Dict[str, Any]]) -> List[str]:
        """Analyze naming conventions in the data."""
        
        patterns = []
        
        # Check hostname patterns
        hostnames = []
        for row in data:
            for key, value in row.items():
                if "hostname" in key.lower() and value:
                    hostnames.append(str(value))
        
        if hostnames and len(hostnames) >= 3:
            # Check for consistent patterns
            if all(len(h) >= 8 for h in hostnames):
                patterns.append("Hostnames follow enterprise naming convention (8+ characters)")
            
            # Check for environment prefixes
            prefixes = [h[:3].upper() for h in hostnames if len(h) >= 3]
            if len(set(prefixes)) < len(prefixes) * 0.6:
                patterns.append("Environment-based hostname prefixes detected")
        
        return patterns
    
    async def _analyze_value_distributions(self, data: List[Dict[str, Any]]) -> List[str]:
        """Analyze value distributions across fields."""
        
        patterns = []
        
        # Check for standardized values in key fields
        key_fields = ['environment', 'asset_type', 'status', 'category']
        
        for field_pattern in key_fields:
            values = set()
            for row in data:
                for key, value in row.items():
                    if field_pattern in key.lower() and value:
                        values.add(str(value).lower())
            
            if 2 <= len(values) <= 6:
                patterns.append(f"Standardized {field_pattern} values: {len(values)} distinct values")
        
        return patterns
    
    async def _analyze_field_relationships(self, data: List[Dict[str, Any]]) -> List[str]:
        """Analyze relationships between fields."""
        
        patterns = []
        
        # Check for department-hostname relationships
        dept_hostname_pairs = set()
        for row in data:
            dept = None
            hostname = None
            
            for key, value in row.items():
                if "department" in key.lower() and value:
                    dept = str(value)[:3].upper()
                if "hostname" in key.lower() and value:
                    hostname = str(value)[:3].upper()
            
            if dept and hostname:
                dept_hostname_pairs.add((dept, hostname))
        
        if len(dept_hostname_pairs) > 1:
            # Check if hostnames contain department codes
            matching_pairs = sum(1 for dept, hostname in dept_hostname_pairs if dept in hostname)
            if matching_pairs > len(dept_hostname_pairs) * 0.5:
                patterns.append("Hostnames appear to contain department codes")
        
        return patterns
    
    async def _identify_column_patterns(self, values: List[str]) -> List[str]:
        """Identify patterns within a column's values."""
        
        patterns = []
        
        if not values:
            return patterns
        
        # Check for IP address pattern
        ip_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
        if all(ip_pattern.match(value) for value in values):
            patterns.append("IP addresses")
        
        # Check for hostname pattern
        hostname_pattern = re.compile(r'^[a-zA-Z][a-zA-Z0-9\-\.]*$')
        if len(values) >= 3 and all(hostname_pattern.match(value) for value in values):
            patterns.append("Hostnames/server names")
        
        # Check for consistent length
        lengths = [len(value) for value in values]
        if len(set(lengths)) == 1 and lengths[0] > 5:
            patterns.append(f"Fixed length strings ({lengths[0]} characters)")
        
        # Check for enumerated values
        if len(set(values)) <= 10 and len(values) >= 5:
            patterns.append(f"Enumerated values ({len(set(values))} distinct)")
        
        return patterns
    
    def _infer_data_type(self, values: List[str]) -> str:
        """Infer the data type from sample values."""
        
        if not values:
            return "unknown"
        
        # Check for numeric patterns
        try:
            [float(v) for v in values]
            return "numeric"
        except ValueError:
            pass
        
        # Check for IP addresses
        ip_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
        if all(ip_pattern.match(value) for value in values):
            return "ip_address"
        
        # Check for dates
        date_indicators = ['/', '-', ' ']
        if any(indicator in values[0] for indicator in date_indicators):
            if any(word in values[0].lower() for word in ['jan', 'feb', 'mar', 'apr', 'may', 'jun']):
                return "date"
        
        # Check for boolean-like values
        boolean_values = {'true', 'false', 'yes', 'no', '1', '0', 'y', 'n'}
        if all(value.lower() in boolean_values for value in values):
            return "boolean"
        
        # Default to text
        avg_length = sum(len(v) for v in values) / len(values)
        if avg_length > 50:
            return "long_text"
        else:
            return "short_text"
    
    async def _generate_structure_summary(self, total_rows: int, total_columns: int,
                                        column_analysis: Dict[str, Any], 
                                        patterns: List[str]) -> str:
        """Generate a human-readable summary of the data structure."""
        
        summary_parts = []
        summary_parts.append(f"Dataset contains {total_rows} rows with {total_columns} columns")
        
        # Completeness analysis
        if column_analysis:
            completeness_scores = [info['completeness'] for info in column_analysis.values()]
            avg_completeness = sum(completeness_scores) / len(completeness_scores)
            summary_parts.append(f"Average field completeness: {avg_completeness:.1%}")
        
        # Pattern summary
        if patterns:
            summary_parts.append(f"Detected {len(patterns)} structural patterns")
        
        return ". ".join(summary_parts)
    
    def _generate_migration_assessment(self, migration_value: str, 
                                     indicators: Dict[str, int]) -> str:
        """Generate a migration value assessment description."""
        
        descriptions = {
            "high": "Excellent migration value - contains comprehensive asset information",
            "medium": "Good migration value - contains key asset details with some gaps",
            "low": "Limited migration value - missing critical asset information"
        }
        
        base_description = descriptions.get(migration_value, "Unknown migration value")
        
        # Add specific details about strongest indicators
        strong_indicators = [k for k, v in indicators.items() if v > 0]
        if strong_indicators:
            indicator_text = ", ".join(strong_indicators[:3])
            return f"{base_description}. Strong in: {indicator_text}"
        
        return base_description 