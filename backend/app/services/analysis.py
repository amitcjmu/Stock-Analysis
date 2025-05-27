"""
Intelligent Analysis Services for CMDB data.
Provides memory-enhanced analysis and intelligent placeholders when CrewAI is unavailable.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class IntelligentAnalyzer:
    """Memory-enhanced analysis when CrewAI is unavailable."""
    
    def __init__(self, memory):
        self.memory = memory
    
    def intelligent_placeholder_analysis(self, cmdb_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide intelligent analysis using memory and patterns."""
        
        filename = cmdb_data.get('filename', '')
        structure = cmdb_data.get('structure', {})
        sample_data = cmdb_data.get('sample_data', [])
        
        # Get relevant past experiences
        relevant_experiences = self.memory.get_relevant_experiences(filename)
        
        # Apply learned patterns
        asset_type = self._detect_asset_type_from_memory(cmdb_data, relevant_experiences)
        
        # Use memory-enhanced field validation
        missing_fields = self._identify_missing_fields_from_memory(
            cmdb_data, asset_type, relevant_experiences
        )
        
        # Calculate confidence based on memory
        confidence = self._calculate_memory_based_confidence(
            cmdb_data, relevant_experiences
        )
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(cmdb_data, asset_type)
        
        # Generate issues and recommendations
        issues = self._identify_issues_from_memory(cmdb_data, relevant_experiences)
        recommendations = self._generate_memory_based_recommendations(cmdb_data, asset_type)
        
        # Assess migration readiness
        migration_readiness = self._assess_migration_readiness(cmdb_data, quality_score)
        
        # Record this analysis
        self.memory.add_experience("placeholder_analysis", {
            "filename": filename,
            "asset_type_detected": asset_type,
            "confidence_level": confidence,
            "quality_score": quality_score,
            "experiences_used": len(relevant_experiences)
        })
        
        return {
            "asset_type_detected": asset_type,
            "confidence_level": confidence,
            "data_quality_score": quality_score,
            "issues": issues,
            "recommendations": recommendations,
            "missing_fields_relevant": missing_fields,
            "migration_readiness": migration_readiness,
            "fallback_mode": True,
            "memory_context": {
                "experiences_used": len(relevant_experiences),
                "patterns_applied": self._count_patterns_applied(relevant_experiences),
                "analysis_type": "memory_enhanced_placeholder"
            },
            "learning_notes": f"Applied {len(relevant_experiences)} past experiences for enhanced analysis"
        }
    
    def _detect_asset_type_from_memory(self, cmdb_data: Dict, experiences: List[Dict]) -> str:
        """Detect asset type using memory and learned patterns."""
        
        structure = cmdb_data.get('structure', {})
        columns = structure.get('columns', [])
        sample_data = cmdb_data.get('sample_data', [])
        
        # Check for explicit type indicators
        type_indicators = self._find_type_indicators(columns, sample_data)
        if type_indicators:
            return type_indicators
        
        # Apply learned patterns from memory
        for exp in experiences:
            if exp.get('type') == 'successful_analysis':
                exp_result = exp.get('result', {})
                if exp_result.get('asset_type_detected'):
                    # Check if current data matches patterns from this experience
                    if self._matches_experience_pattern(cmdb_data, exp):
                        return exp_result['asset_type_detected']
        
        # Fallback to field-based detection
        return self._detect_by_field_patterns(columns, sample_data)
    
    def _find_type_indicators(self, columns: List[str], sample_data: List[Dict]) -> Optional[str]:
        """Find explicit type indicators in the data."""
        
        # Check column names for type indicators
        type_columns = ['ci_type', 'type', 'asset_type', 'category', 'class']
        
        for col in columns:
            col_lower = col.lower().replace('_', '').replace(' ', '')
            for type_col in type_columns:
                if type_col.replace('_', '') in col_lower:
                    # Found a type column, check its values
                    return self._analyze_type_column_values(col, sample_data)
        
        return None
    
    def _analyze_type_column_values(self, type_column: str, sample_data: List[Dict]) -> str:
        """Analyze values in a type column to determine asset type."""
        
        if not sample_data:
            return "mixed"
        
        type_counts = {"application": 0, "server": 0, "database": 0, "other": 0}
        
        for row in sample_data:
            value = str(row.get(type_column, '')).lower()
            
            if any(term in value for term in ['app', 'application', 'service']):
                type_counts["application"] += 1
            elif any(term in value for term in ['server', 'host', 'vm', 'virtual']):
                type_counts["server"] += 1
            elif any(term in value for term in ['db', 'database', 'sql', 'oracle', 'mysql']):
                type_counts["database"] += 1
            else:
                type_counts["other"] += 1
        
        # Return the most common type
        max_type = max(type_counts, key=type_counts.get)
        if max_type == "other" or type_counts[max_type] < len(sample_data) * 0.6:
            return "mixed"
        
        return max_type
    
    def _detect_by_field_patterns(self, columns: List[str], sample_data: List[Dict]) -> str:
        """Detect asset type by analyzing field patterns."""
        
        col_lower = [col.lower() for col in columns]
        
        # Server indicators
        server_fields = ['cpu', 'memory', 'ram', 'ip_address', 'hostname', 'os', 'cores']
        server_score = sum(1 for field in server_fields if any(field in col for col in col_lower))
        
        # Application indicators
        app_fields = ['version', 'environment', 'business_owner', 'dependencies']
        app_score = sum(1 for field in app_fields if any(field in col for col in col_lower))
        
        # Database indicators
        db_fields = ['port', 'instance', 'schema', 'connection', 'db_name']
        db_score = sum(1 for field in db_fields if any(field in col for col in col_lower))
        
        # Determine primary type
        if server_score >= app_score and server_score >= db_score:
            return "server"
        elif app_score >= db_score:
            return "application"
        elif db_score > 0:
            return "database"
        else:
            return "mixed"
    
    def _matches_experience_pattern(self, cmdb_data: Dict, experience: Dict) -> bool:
        """Check if current data matches patterns from a past experience."""
        
        current_columns = set(col.lower() for col in cmdb_data.get('structure', {}).get('columns', []))
        
        # Try to extract column info from experience
        exp_data = experience.get('data_structure', {})
        if exp_data and 'columns' in exp_data:
            exp_columns = set(col.lower() for col in exp_data['columns'])
            
            # Calculate column overlap
            overlap = len(current_columns.intersection(exp_columns))
            total = len(current_columns.union(exp_columns))
            
            if total > 0 and overlap / total > 0.6:  # 60% similarity
                return True
        
        return False
    
    def _identify_missing_fields_from_memory(self, cmdb_data: Dict, asset_type: str, experiences: List[Dict]) -> List[str]:
        """Identify missing fields using memory and asset type context."""
        
        columns = cmdb_data.get('structure', {}).get('columns', [])
        col_lower = [col.lower() for col in columns]
        
        # Define required fields by asset type
        required_fields = {
            "application": ["name", "version", "environment"],
            "server": ["hostname", "ip_address", "os", "cpu", "memory"],
            "database": ["db_name", "version", "host", "port"],
            "mixed": ["name"]
        }
        
        # Get base required fields
        base_required = required_fields.get(asset_type, required_fields["mixed"])
        
        # Check for learned patterns from memory
        learned_fields = set()
        for exp in experiences:
            if exp.get('type') == 'user_feedback':
                corrections = exp.get('corrections', {})
                if 'missing_fields_feedback' in corrections:
                    # Extract field names from feedback
                    feedback = corrections['missing_fields_feedback'].lower()
                    for field in base_required:
                        if field in feedback:
                            learned_fields.add(field)
        
        # Combine base and learned requirements
        all_required = set(base_required) | learned_fields
        
        # Find missing fields
        missing = []
        for field in all_required:
            if not any(field in col for col in col_lower):
                missing.append(field.replace('_', ' ').title())
        
        return missing
    
    def _calculate_memory_based_confidence(self, cmdb_data: Dict, experiences: List[Dict]) -> float:
        """Calculate confidence based on memory and past experiences."""
        
        base_confidence = 0.6  # Base confidence for memory-enhanced analysis
        
        # Boost confidence based on relevant experiences
        if experiences:
            experience_boost = min(0.2, len(experiences) * 0.02)  # Up to 0.2 boost
            base_confidence += experience_boost
        
        # Check for clear type indicators
        structure = cmdb_data.get('structure', {})
        columns = structure.get('columns', [])
        
        if self._has_clear_type_indicators(columns):
            base_confidence += 0.15
        
        # Check data completeness
        sample_data = cmdb_data.get('sample_data', [])
        if sample_data:
            completeness = self._calculate_data_completeness(sample_data)
            base_confidence += completeness * 0.1
        
        return min(0.95, base_confidence)  # Cap at 95% for placeholder analysis
    
    def _has_clear_type_indicators(self, columns: List[str]) -> bool:
        """Check if data has clear type indicators."""
        col_lower = [col.lower() for col in columns]
        type_indicators = ['ci_type', 'type', 'asset_type', 'category']
        
        return any(indicator in ' '.join(col_lower) for indicator in type_indicators)
    
    def _calculate_data_completeness(self, sample_data: List[Dict]) -> float:
        """Calculate data completeness ratio."""
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
    
    def _calculate_quality_score(self, cmdb_data: Dict, asset_type: str) -> int:
        """Calculate data quality score."""
        
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
            completeness = self._calculate_data_completeness(sample_data)
            score += int(completeness * 20)
        
        # Score based on asset type clarity
        if self._has_clear_type_indicators(columns):
            score += 15
        
        return min(100, score)
    
    def _identify_issues_from_memory(self, cmdb_data: Dict, experiences: List[Dict]) -> List[str]:
        """Identify issues using memory and past experiences."""
        
        issues = []
        
        # Check for common issues from past experiences
        for exp in experiences:
            if exp.get('type') == 'user_feedback':
                analysis_issues = exp.get('corrections', {}).get('analysis_issues', '')
                if analysis_issues:
                    # Extract common issue patterns
                    if 'naming' in analysis_issues.lower():
                        issues.append("Inconsistent naming convention detected")
                    if 'missing' in analysis_issues.lower():
                        issues.append("Missing critical fields identified")
        
        # Check current data for issues
        structure = cmdb_data.get('structure', {})
        columns = structure.get('columns', [])
        
        if len(columns) < 3:
            issues.append("Insufficient number of data fields")
        
        if not self._has_clear_type_indicators(columns):
            issues.append("No clear asset type indicators found")
        
        return issues or ["No significant issues detected"]
    
    def _generate_memory_based_recommendations(self, cmdb_data: Dict, asset_type: str) -> List[str]:
        """Generate recommendations based on memory and asset type."""
        
        recommendations = []
        
        # Asset type specific recommendations
        if asset_type == "server":
            recommendations.extend([
                "Collect IP addresses for all servers",
                "Document OS versions for compatibility assessment",
                "Gather hardware specifications for sizing"
            ])
        elif asset_type == "application":
            recommendations.extend([
                "Document application dependencies",
                "Identify business owners and criticality",
                "Map applications to hosting servers"
            ])
        elif asset_type == "database":
            recommendations.extend([
                "Document database connections and ports",
                "Identify host server relationships",
                "Gather backup and replication details"
            ])
        else:
            recommendations.extend([
                "Standardize asset type classification",
                "Improve data consistency across records",
                "Add missing critical fields for migration planning"
            ])
        
        return recommendations
    
    def _assess_migration_readiness(self, cmdb_data: Dict, quality_score: int) -> str:
        """Assess migration readiness based on data quality."""
        
        if quality_score >= 80:
            return "ready"
        elif quality_score >= 60:
            return "needs_work"
        else:
            return "insufficient_data"
    
    def _count_patterns_applied(self, experiences: List[Dict]) -> int:
        """Count how many patterns were applied from experiences."""
        
        pattern_count = 0
        for exp in experiences:
            if exp.get('type') in ['successful_analysis', 'learned_patterns']:
                pattern_count += 1
        
        return pattern_count


class PlaceholderAnalyzer:
    """Static placeholder analysis methods for various migration tasks."""
    
    @staticmethod
    def placeholder_6r_analysis(asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide intelligent 6R strategy analysis placeholder."""
        
        asset_type = asset_data.get('asset_type', 'unknown')
        business_criticality = asset_data.get('business_criticality', 'medium')
        
        # Intelligent strategy recommendation based on asset characteristics
        if asset_type.lower() == 'application':
            if business_criticality.lower() in ['high', 'critical']:
                strategy = "replatform"
                rationale = "High-criticality application benefits from cloud-native services"
            else:
                strategy = "rehost"
                rationale = "Standard application suitable for lift-and-shift migration"
        elif asset_type.lower() == 'server':
            strategy = "rehost"
            rationale = "Infrastructure component suitable for direct migration"
        else:
            strategy = "rehost"
            rationale = "Default strategy for unknown asset types"
        
        return {
            "recommended_strategy": strategy,
            "rationale": rationale,
            "alternative_strategies": ["rehost", "replatform", "refactor"],
            "risk_level": "medium",
            "complexity": "medium",
            "migration_priority": 5,
            "considerations": [
                f"Asset type: {asset_type}",
                f"Business criticality: {business_criticality}",
                "Detailed assessment recommended for final strategy"
            ],
            "placeholder_mode": True
        }
    
    @staticmethod
    def placeholder_risk_assessment(migration_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide intelligent risk assessment placeholder."""
        
        total_assets = migration_data.get('total_assets', 0)
        timeline_days = migration_data.get('timeline_days', 90)
        
        # Calculate risk based on scale and timeline
        if total_assets > 500 or timeline_days < 60:
            risk_level = "high"
        elif total_assets > 100 or timeline_days < 90:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "overall_risk_level": risk_level,
            "risk_categories": {
                "technical": risk_level,
                "business": "medium",
                "security": "medium",
                "timeline": "medium" if timeline_days < 90 else "low"
            },
            "key_risks": [
                "Dependency mapping complexity",
                "Data migration challenges",
                "Business continuity during migration"
            ],
            "mitigation_strategies": [
                "Comprehensive dependency analysis",
                "Phased migration approach",
                "Robust testing and rollback procedures"
            ],
            "placeholder_mode": True
        }
    
    @staticmethod
    def placeholder_wave_plan(assets_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Provide intelligent wave planning placeholder."""
        
        total_assets = len(assets_data)
        
        # Simple wave distribution
        if total_assets <= 50:
            wave_count = 2
        elif total_assets <= 200:
            wave_count = 3
        else:
            wave_count = 4
        
        assets_per_wave = total_assets // wave_count
        
        waves = []
        for i in range(wave_count):
            wave = {
                "wave_number": i + 1,
                "asset_count": assets_per_wave,
                "timeline_weeks": 2 + i,
                "focus": f"Wave {i + 1} migration batch",
                "risk_level": "medium"
            }
            waves.append(wave)
        
        return {
            "total_waves": wave_count,
            "waves": waves,
            "total_timeline_weeks": wave_count * 2 + 2,
            "sequencing_rationale": "Balanced distribution based on asset count",
            "success_criteria": [
                "Zero business disruption",
                "All assets successfully migrated",
                "Performance validation completed"
            ],
            "placeholder_mode": True
        }
    
    @staticmethod
    def placeholder_cmdb_processing(processing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide intelligent CMDB processing recommendations."""
        
        filename = processing_data.get('filename', 'unknown')
        record_count = len(processing_data.get('processed_data', []))
        
        return {
            "processing_recommendations": [
                "Standardize naming conventions across all records",
                "Validate and normalize IP address formats",
                "Enrich data with missing business context",
                "Establish clear asset relationships"
            ],
            "data_transformations": [
                "Convert text fields to standardized formats",
                "Normalize environment classifications",
                "Validate technical specifications"
            ],
            "enrichment_opportunities": [
                "Add business criticality ratings",
                "Map asset dependencies",
                "Include compliance requirements"
            ],
            "quality_improvements": [
                f"Process {record_count} records for consistency",
                "Implement data validation rules",
                "Add missing mandatory fields"
            ],
            "migration_preparation": [
                "Group assets by migration complexity",
                "Identify quick wins for early waves",
                "Flag high-risk assets for detailed analysis"
            ],
            "placeholder_mode": True
        } 