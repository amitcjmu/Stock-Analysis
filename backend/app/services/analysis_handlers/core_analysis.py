"""
Core Analysis Handler
Handles main analysis logic, quality scoring, and data completeness calculations.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class CoreAnalysisHandler:
    """Handles core analysis operations with graceful fallbacks."""
    
    def __init__(self):
        self.service_available = True
        logger.info("Core analysis handler initialized successfully")
    
    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return True
    
    def calculate_quality_score(self, cmdb_data: Dict, asset_type: str) -> int:
        """Calculate data quality score."""
        try:
            score = 50  # Base score
            
            structure = cmdb_data.get('structure', {})
            columns = structure.get('columns', [])
            sample_data = cmdb_data.get('sample_data', [])
            
            # Score based on column count
            if len(columns) >= 5:
                score += 15
            elif len(columns) >= 3:
                score += 10
            
            # Score based on data completeness
            if sample_data:
                completeness = self.calculate_data_completeness(sample_data)
                score += int(completeness * 20)
            
            # Score based on asset type clarity
            if self.has_clear_type_indicators(columns):
                score += 15
            
            return min(100, score)
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 50  # Default score
    
    def calculate_data_completeness(self, sample_data: List[Dict]) -> float:
        """Calculate data completeness ratio."""
        try:
            if not sample_data:
                return 0.0
            
            total_fields = 0
            filled_fields = 0
            
            for row in sample_data:
                for value in row.values():
                    total_fields += 1
                    if value and str(value).strip():
                        filled_fields += 1
            
            return filled_fields / total_fields if total_fields > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating data completeness: {e}")
            return 0.0
    
    def has_clear_type_indicators(self, columns: List[str]) -> bool:
        """Check if data has clear type indicators."""
        try:
            col_lower = [col.lower() for col in columns]
            type_indicators = ['ci_type', 'type', 'asset_type', 'category']
            
            return any(indicator in ' '.join(col_lower) for indicator in type_indicators)
            
        except Exception as e:
            logger.error(f"Error checking type indicators: {e}")
            return False
    
    def detect_asset_type(self, cmdb_data: Dict[str, Any]) -> str:
        """Detect asset type from CMDB data."""
        try:
            structure = cmdb_data.get('structure', {})
            columns = structure.get('columns', [])
            sample_data = cmdb_data.get('sample_data', [])
            
            # Check columns for type indicators
            col_text = ' '.join(columns).lower()
            
            # Server indicators
            server_indicators = ['server', 'host', 'compute', 'vm', 'virtual', 'physical', 'cpu', 'memory', 'ram']
            if any(indicator in col_text for indicator in server_indicators):
                return 'server'
            
            # Application indicators
            app_indicators = ['application', 'app', 'service', 'software', 'system']
            if any(indicator in col_text for indicator in app_indicators):
                return 'application'
            
            # Database indicators
            db_indicators = ['database', 'db', 'sql', 'oracle', 'mysql', 'postgres']
            if any(indicator in col_text for indicator in db_indicators):
                return 'database'
            
            # Network indicators
            network_indicators = ['network', 'switch', 'router', 'firewall', 'load_balancer']
            if any(indicator in col_text for indicator in network_indicators):
                return 'network'
            
            # Storage indicators
            storage_indicators = ['storage', 'disk', 'san', 'nas', 'volume']
            if any(indicator in col_text for indicator in storage_indicators):
                return 'storage'
            
            # Check sample data for type clues
            if sample_data:
                sample_text = ' '.join(str(value).lower() for row in sample_data[:5] for value in row.values() if value)
                
                if any(indicator in sample_text for indicator in server_indicators):
                    return 'server'
                elif any(indicator in sample_text for indicator in app_indicators):
                    return 'application'
                elif any(indicator in sample_text for indicator in db_indicators):
                    return 'database'
            
            # Default to generic if no clear indicators
            return 'generic'
            
        except Exception as e:
            logger.error(f"Error detecting asset type: {e}")
            return 'generic'
    
    def identify_missing_fields(self, cmdb_data: Dict, asset_type: str) -> List[str]:
        """Identify missing required fields based on asset type."""
        try:
            structure = cmdb_data.get('structure', {})
            columns = structure.get('columns', [])
            col_lower = [col.lower() for col in columns]
            
            # Define required fields by asset type
            required_fields = {
                'server': ['name', 'ip_address', 'operating_system', 'environment', 'cpu', 'memory'],
                'application': ['name', 'business_owner', 'environment', 'version', 'criticality'],
                'database': ['name', 'db_type', 'version', 'size', 'environment'],
                'network': ['name', 'ip_address', 'device_type', 'location'],
                'storage': ['name', 'capacity', 'type', 'location'],
                'generic': ['name', 'type', 'environment', 'owner']
            }
            
            asset_required = required_fields.get(asset_type, required_fields['generic'])
            missing_fields = []
            
            for required_field in asset_required:
                # Check if any column matches this required field
                found = False
                for col in col_lower:
                    if (required_field in col or 
                        any(synonym in col for synonym in self._get_field_synonyms(required_field))):
                        found = True
                        break
                
                if not found:
                    missing_fields.append(required_field.replace('_', ' ').title())
            
            return missing_fields
            
        except Exception as e:
            logger.error(f"Error identifying missing fields: {e}")
            return []
    
    def _get_field_synonyms(self, field: str) -> List[str]:
        """Get synonyms for common field names."""
        synonyms = {
            'name': ['hostname', 'ci_name', 'asset_name', 'device_name'],
            'ip_address': ['ip', 'network_address', 'primary_ip'],
            'operating_system': ['os', 'platform', 'os_version'],
            'environment': ['env', 'stage', 'tier'],
            'cpu': ['cores', 'processors', 'vcpu'],
            'memory': ['ram', 'memory_gb', 'ram_gb'],
            'business_owner': ['owner', 'responsible_party', 'app_owner'],
            'criticality': ['priority', 'importance', 'business_criticality'],
            'version': ['release', 'build', 'software_version'],
            'db_type': ['database_type', 'dbms', 'database_engine'],
            'size': ['capacity', 'storage_size', 'disk_size'],
            'device_type': ['type', 'category', 'classification'],
            'location': ['site', 'datacenter', 'facility']
        }
        
        return synonyms.get(field, [])
    
    def identify_issues(self, cmdb_data: Dict) -> List[str]:
        """Identify potential issues in the data."""
        try:
            issues = []
            
            structure = cmdb_data.get('structure', {})
            columns = structure.get('columns', [])
            sample_data = cmdb_data.get('sample_data', [])
            
            # Check for insufficient columns
            if len(columns) < 3:
                issues.append("Insufficient number of data fields")
            
            # Check for missing type indicators
            if not self.has_clear_type_indicators(columns):
                issues.append("No clear asset type indicators found")
            
            # Check data completeness
            if sample_data:
                completeness = self.calculate_data_completeness(sample_data)
                if completeness < 0.5:
                    issues.append("Low data completeness - many empty fields")
                elif completeness < 0.7:
                    issues.append("Moderate data completeness - some empty fields")
            
            # Check for duplicate column names
            if len(columns) != len(set(columns)):
                issues.append("Duplicate column names detected")
            
            # Check for very short column names (likely abbreviated)
            short_columns = [col for col in columns if len(col) <= 2]
            if short_columns:
                issues.append(f"Very short column names detected: {', '.join(short_columns)}")
            
            return issues if issues else ["No significant issues detected"]
            
        except Exception as e:
            logger.error(f"Error identifying issues: {e}")
            return ["Error analyzing data quality"]
    
    def generate_basic_recommendations(self, cmdb_data: Dict, asset_type: str) -> List[str]:
        """Generate basic recommendations for data improvement."""
        try:
            recommendations = []
            
            # Asset type specific recommendations
            if asset_type == "server":
                recommendations.extend([
                    "Collect IP addresses for all servers",
                    "Standardize operating system naming conventions",
                    "Ensure CPU and memory specifications are complete"
                ])
            elif asset_type == "application":
                recommendations.extend([
                    "Identify business owners for all applications",
                    "Establish application criticality ratings",
                    "Document application dependencies"
                ])
            elif asset_type == "database":
                recommendations.extend([
                    "Document database sizes and growth patterns",
                    "Identify database dependencies and consumers",
                    "Ensure backup and recovery procedures are documented"
                ])
            else:
                recommendations.extend([
                    "Standardize asset naming conventions",
                    "Complete missing asset type classifications",
                    "Establish ownership and responsibility"
                ])
            
            # General recommendations
            structure = cmdb_data.get('structure', {})
            columns = structure.get('columns', [])
            
            if len(columns) < 5:
                recommendations.append("Consider adding more descriptive fields")
            
            sample_data = cmdb_data.get('sample_data', [])
            if sample_data:
                completeness = self.calculate_data_completeness(sample_data)
                if completeness < 0.8:
                    recommendations.append("Improve data completeness across all fields")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Complete data analysis and standardization"]
    
    def assess_migration_readiness(self, cmdb_data: Dict, asset_type: str, quality_score: int) -> Dict[str, Any]:
        """Assess migration readiness based on data quality and completeness."""
        try:
            readiness_score = quality_score / 100.0
            
            # Adjust based on asset type complexity
            complexity_adjustments = {
                'server': 0.0,
                'application': 0.1,
                'database': 0.2,
                'network': -0.1,
                'storage': -0.05,
                'generic': -0.2
            }
            
            readiness_score += complexity_adjustments.get(asset_type, 0)
            readiness_score = max(0.0, min(1.0, readiness_score))
            
            # Determine readiness level
            if readiness_score >= 0.8:
                readiness_level = "High"
                readiness_message = "Data is well-structured and ready for migration planning"
            elif readiness_score >= 0.6:
                readiness_level = "Medium"
                readiness_message = "Data is adequate but could benefit from improvement"
            elif readiness_score >= 0.4:
                readiness_level = "Low"
                readiness_message = "Data needs significant improvement before migration"
            else:
                readiness_level = "Very Low"
                readiness_message = "Data requires major cleanup and standardization"
            
            return {
                "readiness_score": readiness_score,
                "readiness_level": readiness_level,
                "readiness_message": readiness_message,
                "asset_type": asset_type,
                "quality_score": quality_score
            }
            
        except Exception as e:
            logger.error(f"Error assessing migration readiness: {e}")
            return {
                "readiness_score": 0.5,
                "readiness_level": "Unknown",
                "readiness_message": "Unable to assess migration readiness",
                "error": str(e)
            }
    
    def analyze_data_patterns(self, sample_data: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns in the sample data."""
        try:
            if not sample_data:
                return {"patterns": [], "insights": []}
            
            patterns = []
            insights = []
            
            # Analyze field value patterns
            field_analysis = {}
            for row in sample_data:
                for field, value in row.items():
                    if field not in field_analysis:
                        field_analysis[field] = {"values": [], "empty_count": 0}
                    
                    if value and str(value).strip():
                        field_analysis[field]["values"].append(str(value))
                    else:
                        field_analysis[field]["empty_count"] += 1
            
            # Generate patterns and insights
            for field, analysis in field_analysis.items():
                values = analysis["values"]
                empty_count = analysis["empty_count"]
                total_count = len(values) + empty_count
                
                if empty_count > total_count * 0.5:
                    patterns.append(f"High percentage of empty values in {field}")
                
                if values:
                    unique_values = set(values)
                    if len(unique_values) == 1:
                        patterns.append(f"All {field} values are identical")
                    elif len(unique_values) / len(values) > 0.9:
                        insights.append(f"{field} has high uniqueness - likely identifier field")
                    elif len(unique_values) < 10:
                        insights.append(f"{field} has limited values - likely categorical field")
            
            return {
                "patterns": patterns,
                "insights": insights,
                "field_count": len(field_analysis),
                "sample_size": len(sample_data)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing data patterns: {e}")
            return {"patterns": [], "insights": [], "error": str(e)} 