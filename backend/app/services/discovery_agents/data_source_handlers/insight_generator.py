"""
Insight Generator Handler
Generates intelligent insights from data analysis results.
"""

import logging
from typing import Dict, List, Any

from app.services.models.agent_communication import ConfidenceLevel

logger = logging.getLogger(__name__)

class InsightGenerator:
    """Generates intelligent insights from data analysis."""
    
    def __init__(self):
        self.generator_id = "insight_generator"
        
        # Insight templates and patterns
        self.insight_types = [
            "data_quality", "migration_readiness", "organizational_pattern",
            "risk_assessment", "optimization_opportunity", "compliance_gap"
        ]
    
    async def generate_intelligent_insights(self, data: List[Dict[str, Any]], 
                                          metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate intelligent insights from analyzed data."""
        
        insights = []
        
        if not data:
            return [{
                "type": "data_quality",
                "title": "No Data Available",
                "description": "No data was provided for analysis",
                "confidence": ConfidenceLevel.HIGH.value,
                "actionable": True,  # This is actionable - user should upload data
                "supporting_data": {"row_count": 0}
            }]
        
        # Generate different types of insights
        insights.extend(await self._generate_data_quality_insights(data, metadata))
        insights.extend(await self._generate_migration_insights(data, metadata))
        insights.extend(await self._generate_organizational_insights(data))
        insights.extend(await self._generate_optimization_insights(data))
        
        return insights
    
    async def _generate_data_quality_insights(self, data: List[Dict[str, Any]], 
                                            metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights about data quality."""
        
        insights = []
        total_rows = len(data)
        
        # Analyze field completeness
        all_columns = set()
        for row in data:
            all_columns.update(row.keys())
        
        # Always generate basic dataset insights for any size
        insights.append({
            "type": "data_overview",
            "title": "Dataset Analysis Summary",
            "description": f"Analyzed {total_rows} records with {len(all_columns)} fields. Ready for migration attribute mapping and quality assessment",
            "confidence": ConfidenceLevel.HIGH.value,
            "actionable": False,  # This is informational
            "supporting_data": {
                "total_records": total_rows,
                "total_fields": len(all_columns),
                "analysis_scope": "complete"
            }
        })
        
        # Critical fields analysis (lowered threshold)
        critical_fields_found = 0
        critical_fields = []
        for column in all_columns:
            if any(keyword in column.lower() for keyword in 
                  ['hostname', 'asset_name', 'server', 'ip_address', 'cpu', 'memory', 'ram']):
                critical_fields_found += 1
                critical_fields.append(column)
        
        if critical_fields_found >= 1:  # Lowered from 3 to 1
            insights.append({
                "type": "data_quality",
                "title": "Asset Identification Fields Present",
                "description": f"Found {critical_fields_found} critical fields ({', '.join(critical_fields[:3])}), providing foundation for migration planning",
                "confidence": ConfidenceLevel.HIGH.value,
                "actionable": False,  # This is informational
                "supporting_data": {
                    "critical_fields": critical_fields_found,
                    "identified_fields": critical_fields,
                    "total_columns": len(all_columns),
                    "analysis_confidence": "high"
                }
            })
        
        # Volume analysis (lowered threshold)
        if total_rows >= 50:  # Lowered from 500 to 50
            insights.append({
                "type": "migration_readiness",
                "title": "Migration-Scale Dataset",
                "description": f"Dataset contains {total_rows} assets, suitable for structured migration approach with proper planning",
                "confidence": ConfidenceLevel.MEDIUM.value,
                "actionable": False,  # This is informational
                "supporting_data": {
                    "asset_count": total_rows,
                    "scale_category": "structured_migration" if total_rows < 500 else "enterprise"
                }
            })
        elif total_rows >= 2:  # Add insight for small datasets too
            insights.append({
                "type": "migration_readiness",
                "title": "Sample Migration Dataset",
                "description": f"Dataset contains {total_rows} assets, perfect for testing migration workflows and field mapping validation",
                "confidence": ConfidenceLevel.MEDIUM.value,
                "actionable": False,  # This is informational
                "supporting_data": {
                    "asset_count": total_rows,
                    "scale_category": "sample_testing"
                }
            })
        
        return insights
    
    async def _generate_migration_insights(self, data: List[Dict[str, Any]], 
                                         metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate migration-specific insights."""
        
        insights = []
        
        # Environment distribution analysis
        environments = {}
        for row in data:
            for key, value in row.items():
                if "environment" in key.lower() and value:
                    env = str(value).lower().strip()
                    environments[env] = environments.get(env, 0) + 1
        
        if environments:
            total_envs = sum(environments.values())
            env_insights = []
            
            for env, count in environments.items():
                percentage = (count / total_envs) * 100
                if percentage > 40:
                    env_insights.append(f"{env}: {percentage:.1f}% ({count} assets)")
            
            if env_insights:
                insights.append({
                    "type": "migration_readiness",
                    "title": "Environment Distribution Analysis",
                    "description": f"Identified {len(environments)} distinct environments. Major distributions: {', '.join(env_insights)}",
                    "confidence": ConfidenceLevel.MEDIUM.value,
                    "actionable": False,  # This is informational
                    "supporting_data": {
                        "environments": environments,
                        "total_assets": total_envs
                    }
                })
        
        return insights
    
    async def _generate_organizational_insights(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate organizational pattern insights."""
        
        insights = []
        
        # Department/ownership patterns
        departments = {}
        owners = {}
        
        for row in data:
            for key, value in row.items():
                if "department" in key.lower() and value:
                    dept = str(value).strip()
                    departments[dept] = departments.get(dept, 0) + 1
                
                if "owner" in key.lower() and value:
                    owner = str(value).strip()
                    owners[owner] = owners.get(owner, 0) + 1
        
        if departments and len(departments) > 1:
            largest_dept = max(departments.items(), key=lambda x: x[1])
            total_assets = sum(departments.values())
            
            insights.append({
                "type": "organizational_pattern",
                "title": "Multi-Department Asset Distribution",
                "description": f"Assets span {len(departments)} departments. Largest: {largest_dept[0]} with {largest_dept[1]} assets ({(largest_dept[1]/total_assets)*100:.1f}%)",
                "confidence": ConfidenceLevel.MEDIUM.value,
                "actionable": False,  # This is informational
                "supporting_data": {
                    "departments": departments,
                    "department_count": len(departments)
                }
            })
        
        return insights
    
    async def _generate_optimization_insights(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate optimization opportunity insights."""
        
        insights = []
        
        # Technology stack analysis
        operating_systems = {}
        asset_types = {}
        
        for row in data:
            for key, value in row.items():
                if any(os_keyword in key.lower() for os_keyword in ['os', 'operating', 'system']) and value:
                    os_name = str(value).strip()
                    operating_systems[os_name] = operating_systems.get(os_name, 0) + 1
                
                if "type" in key.lower() and value:
                    asset_type = str(value).strip()
                    asset_types[asset_type] = asset_types.get(asset_type, 0) + 1
        
        # Legacy OS detection
        legacy_indicators = ['2003', '2008', 'xp', 'vista', '7', 'centos 6', 'rhel 6']
        legacy_count = 0
        
        for os_name in operating_systems.keys():
            if any(legacy in os_name.lower() for legacy in legacy_indicators):
                legacy_count += operating_systems[os_name]
        
        if legacy_count > 0:
            total_os_assets = sum(operating_systems.values())
            legacy_percentage = (legacy_count / total_os_assets) * 100
            
            insights.append({
                "type": "optimization_opportunity",
                "title": "Legacy Operating Systems Detected",
                "description": f"Found {legacy_count} assets ({legacy_percentage:.1f}%) running legacy operating systems requiring modernization",
                "confidence": ConfidenceLevel.HIGH.value,
                "actionable": True,  # This is actionable - user should modernize
                "supporting_data": {
                    "legacy_count": legacy_count,
                    "total_assets": total_os_assets,
                    "legacy_percentage": legacy_percentage
                }
            })
        
        return insights
    
    def identify_organizational_patterns(self, data: List[Dict[str, Any]]) -> List[str]:
        """Identify organizational patterns in the data."""
        
        patterns = []
        
        # Check for consistent naming conventions
        hostnames = []
        for row in data:
            for key, value in row.items():
                if "hostname" in key.lower() and value:
                    hostnames.append(str(value))
        
        if hostnames:
            # Check for naming patterns
            if self._has_consistent_naming(hostnames):
                patterns.append("Consistent hostname naming convention detected")
            
            # Check for environment prefixes
            env_prefixes = set()
            for hostname in hostnames:
                if len(hostname) > 3:
                    prefix = hostname[:3].upper()
                    env_prefixes.add(prefix)
            
            if len(env_prefixes) < len(hostnames) * 0.3:  # Reused prefixes
                patterns.append("Environment-based hostname prefixes detected")
        
        return patterns
    
    def _has_consistent_naming(self, hostnames: List[str]) -> bool:
        """Check if hostnames follow consistent naming patterns."""
        if len(hostnames) < 3:
            return False
        
        # Check for consistent length patterns
        lengths = [len(hostname) for hostname in hostnames]
        avg_length = sum(lengths) / len(lengths)
        consistent_length = all(abs(length - avg_length) <= 2 for length in lengths)
        
        # Check for consistent character patterns
        has_numbers = [any(c.isdigit() for c in hostname) for hostname in hostnames]
        consistent_numbers = len(set(has_numbers)) == 1
        
        return consistent_length and consistent_numbers 