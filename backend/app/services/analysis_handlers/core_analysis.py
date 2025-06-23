"""
Core Analysis Handler
Handles CrewAI-based core analysis operations with AI-driven intelligence.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
import os

logger = logging.getLogger(__name__)

# Check CrewAI availability
CREWAI_AVAILABLE = bool(os.getenv('DEEPINFRA_API_KEY') and os.getenv('CREWAI_ENABLED', 'true').lower() == 'true')

try:
    from app.services.crewai_flows.crews.inventory_building_crew import create_inventory_building_crew
    from app.services.crewai_flows.data_cleansing_crew import create_data_cleansing_crew
    from app.services.crewai_flows.crews.field_mapping_crew import create_field_mapping_crew
    CREWS_AVAILABLE = True
except ImportError:
    CREWS_AVAILABLE = False

class CoreAnalysisHandler:
    """Handles CrewAI-based core analysis operations."""
    
    def __init__(self, llm=None):
        self.llm = llm
        self.crews = {}
        self.service_available = CREWAI_AVAILABLE and CREWS_AVAILABLE
        
        if self.service_available and self.llm:
            self._initialize_crews()
        
        logger.info(f"Core analysis handler initialized (CrewAI: {self.service_available})")
    
    def _initialize_crews(self):
        """Initialize CrewAI crews for core analysis."""
        try:
            if CREWS_AVAILABLE and self.llm:
                self.crews['inventory_building'] = create_inventory_building_crew(llm=self.llm)
                self.crews['data_cleansing'] = create_data_cleansing_crew(llm=self.llm)
                self.crews['field_mapping'] = create_field_mapping_crew(llm=self.llm)
                logger.info("CrewAI crews initialized for core analysis")
        except Exception as e:
            logger.error(f"Failed to initialize crews: {e}")
            self.service_available = False
    
    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return self.service_available
    
    def calculate_quality_score(self, cmdb_data: Dict, asset_type: str) -> int:
        """Calculate data quality score using CrewAI crews."""
        try:
            if not self.service_available:
                return self._fallback_quality_score(cmdb_data)
            
            # Use Data Cleansing Crew for quality assessment
            if 'data_cleansing' in self.crews:
                try:
                    crew_result = self.crews['data_cleansing'].kickoff({
                        'cmdb_data': cmdb_data,
                        'asset_type': asset_type,
                        'task': 'quality_scoring'
                    })
                    
                    if crew_result and isinstance(crew_result, dict):
                        return int(crew_result.get('quality_score', 70))
                except Exception as e:
                    logger.error(f"Data Cleansing Crew quality scoring failed: {e}")
            
            return self._fallback_quality_score(cmdb_data)
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 50  # Default score
    
    def _fallback_quality_score(self, cmdb_data: Dict) -> int:
        """Fallback quality scoring when CrewAI is not available."""
        structure = cmdb_data.get('structure', {})
        columns = structure.get('columns', [])
        sample_data = cmdb_data.get('sample_data', [])
        
        # Basic scoring - recommend AI analysis
        base_score = 60 if len(columns) >= 3 else 40
        if sample_data and len(sample_data) > 0:
            base_score += 10
        
        return min(100, base_score)
    
    def calculate_data_completeness(self, sample_data: List[Dict]) -> float:
        """Calculate data completeness using AI analysis."""
        try:
            if not self.service_available:
                return self._fallback_data_completeness(sample_data)
            
            # Use Data Cleansing Crew for completeness analysis
            if 'data_cleansing' in self.crews:
                try:
                    crew_result = self.crews['data_cleansing'].kickoff({
                        'sample_data': sample_data,
                        'task': 'completeness_analysis'
                    })
                    
                    if crew_result and isinstance(crew_result, dict):
                        return float(crew_result.get('completeness_ratio', 0.7))
                except Exception as e:
                    logger.error(f"Data Cleansing Crew completeness analysis failed: {e}")
            
            return self._fallback_data_completeness(sample_data)
            
        except Exception as e:
            logger.error(f"Error calculating data completeness: {e}")
            return 0.0
    
    def _fallback_data_completeness(self, sample_data: List[Dict]) -> float:
        """Fallback completeness calculation when CrewAI is not available."""
        if not sample_data:
            return 0.0
        
        # Basic completeness check
        total_fields = sum(len(row) for row in sample_data)
        filled_fields = sum(1 for row in sample_data for value in row.values() if value and str(value).strip())
        
        return filled_fields / total_fields if total_fields > 0 else 0.0
    
    def has_clear_type_indicators(self, columns: List[str]) -> bool:
        """Check if data has clear type indicators using AI analysis."""
        try:
            if not self.service_available:
                return self._fallback_type_indicators(columns)
            
            # Use Field Mapping Crew for type indicator analysis
            if 'field_mapping' in self.crews:
                try:
                    crew_result = self.crews['field_mapping'].kickoff({
                        'columns': columns,
                        'task': 'type_indicator_analysis'
                    })
                    
                    if crew_result and isinstance(crew_result, dict):
                        return crew_result.get('has_type_indicators', False)
                except Exception as e:
                    logger.error(f"Field Mapping Crew type indicator analysis failed: {e}")
            
            return self._fallback_type_indicators(columns)
            
        except Exception as e:
            logger.error(f"Error checking type indicators: {e}")
            return False
    
    def _fallback_type_indicators(self, columns: List[str]) -> bool:
        """Fallback type indicator check when CrewAI is not available."""
        col_lower = [col.lower() for col in columns]
        type_indicators = ['ci_type', 'type', 'asset_type', 'category']
        return any(indicator in ' '.join(col_lower) for indicator in type_indicators)
    
    def detect_asset_type(self, cmdb_data: Dict[str, Any]) -> str:
        """Detect asset type using CrewAI crews."""
        try:
            if not self.service_available:
                return self._fallback_asset_type(cmdb_data)
            
            # Use Inventory Building Crew for asset type detection
            if 'inventory_building' in self.crews:
                try:
                    crew_result = self.crews['inventory_building'].kickoff({
                        'cmdb_data': cmdb_data,
                        'task': 'asset_type_detection'
                    })
                    
                    if crew_result and isinstance(crew_result, dict):
                        return crew_result.get('asset_type', 'generic')
                except Exception as e:
                    logger.error(f"Inventory Building Crew asset type detection failed: {e}")
            
            return self._fallback_asset_type(cmdb_data)
            
        except Exception as e:
            logger.error(f"Error detecting asset type: {e}")
            return 'generic'
    
    def _fallback_asset_type(self, cmdb_data: Dict[str, Any]) -> str:
        """Fallback asset type detection when CrewAI is not available."""
        structure = cmdb_data.get('structure', {})
        columns = structure.get('columns', [])
        col_text = ' '.join(columns).lower()
        
        # Basic type detection - recommend AI analysis
        if any(indicator in col_text for indicator in ['server', 'host', 'compute']):
            return 'server'
        elif any(indicator in col_text for indicator in ['application', 'app', 'service']):
            return 'application'
        elif any(indicator in col_text for indicator in ['database', 'db', 'sql']):
            return 'database'
        else:
            return 'generic'
    
    def identify_missing_fields(self, cmdb_data: Dict, asset_type: str) -> List[str]:
        """Identify missing fields using CrewAI crews."""
        try:
            if not self.service_available:
                return self._fallback_missing_fields(cmdb_data, asset_type)
            
            # Use Field Mapping Crew for missing field analysis
            if 'field_mapping' in self.crews:
                try:
                    crew_result = self.crews['field_mapping'].kickoff({
                        'cmdb_data': cmdb_data,
                        'asset_type': asset_type,
                        'task': 'missing_field_analysis'
                    })
                    
                    if crew_result and isinstance(crew_result, dict):
                        return crew_result.get('missing_fields', [])
                except Exception as e:
                    logger.error(f"Field Mapping Crew missing field analysis failed: {e}")
            
            return self._fallback_missing_fields(cmdb_data, asset_type)
            
        except Exception as e:
            logger.error(f"Error identifying missing fields: {e}")
            return []
    
    def _fallback_missing_fields(self, cmdb_data: Dict, asset_type: str) -> List[str]:
        """Fallback missing field identification when CrewAI is not available."""
        # Return basic recommendations for AI analysis
        return [
            "Use Field Mapping Crew for comprehensive field analysis",
            "Enable CrewAI for intelligent field mapping",
            "AI analysis recommended for missing field detection"
        ]
    
    def identify_issues(self, cmdb_data: Dict) -> List[str]:
        """Identify issues using CrewAI crews."""
        try:
            if not self.service_available:
                return self._fallback_issues(cmdb_data)
            
            # Use Data Cleansing Crew for issue identification
            if 'data_cleansing' in self.crews:
                try:
                    crew_result = self.crews['data_cleansing'].kickoff({
                        'cmdb_data': cmdb_data,
                        'task': 'issue_identification'
                    })
                    
                    if crew_result and isinstance(crew_result, dict):
                        return crew_result.get('issues', [])
                except Exception as e:
                    logger.error(f"Data Cleansing Crew issue identification failed: {e}")
            
            return self._fallback_issues(cmdb_data)
            
        except Exception as e:
            logger.error(f"Error identifying issues: {e}")
            return []
    
    def _fallback_issues(self, cmdb_data: Dict) -> List[str]:
        """Fallback issue identification when CrewAI is not available."""
        return [
            "Use Data Cleansing Crew for comprehensive issue analysis",
            "Enable CrewAI for intelligent data quality assessment",
            "AI analysis recommended for issue identification"
        ]
    
    def generate_basic_recommendations(self, cmdb_data: Dict, asset_type: str) -> List[str]:
        """Generate recommendations using CrewAI crews."""
        try:
            if not self.service_available:
                return self._fallback_recommendations(cmdb_data, asset_type)
            
            # Use Data Cleansing Crew for recommendations
            if 'data_cleansing' in self.crews:
                try:
                    crew_result = self.crews['data_cleansing'].kickoff({
                        'cmdb_data': cmdb_data,
                        'asset_type': asset_type,
                        'task': 'recommendation_generation'
                    })
                    
                    if crew_result and isinstance(crew_result, dict):
                        return crew_result.get('recommendations', [])
                except Exception as e:
                    logger.error(f"Data Cleansing Crew recommendation generation failed: {e}")
            
            return self._fallback_recommendations(cmdb_data, asset_type)
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def _fallback_recommendations(self, cmdb_data: Dict, asset_type: str) -> List[str]:
        """Fallback recommendations when CrewAI is not available."""
        return [
            "Use Data Cleansing Crew for intelligent recommendations",
            "Enable Field Mapping Crew for field analysis",
            "Use Inventory Building Crew for asset classification",
            "AI analysis recommended for comprehensive insights"
        ]
    
    def assess_migration_readiness(self, cmdb_data: Dict, asset_type: str, quality_score: int) -> Dict[str, Any]:
        """Assess migration readiness using CrewAI crews."""
        try:
            if not self.service_available:
                return self._fallback_migration_readiness(quality_score)
            
            # Use Data Cleansing Crew for readiness assessment
            if 'data_cleansing' in self.crews:
                try:
                    crew_result = self.crews['data_cleansing'].kickoff({
                        'cmdb_data': cmdb_data,
                        'asset_type': asset_type,
                        'quality_score': quality_score,
                        'task': 'migration_readiness_assessment'
                    })
                    
                    if crew_result and isinstance(crew_result, dict):
                        return crew_result
                except Exception as e:
                    logger.error(f"Data Cleansing Crew readiness assessment failed: {e}")
            
            return self._fallback_migration_readiness(quality_score)
            
        except Exception as e:
            logger.error(f"Error assessing migration readiness: {e}")
            return self._fallback_migration_readiness(quality_score)
    
    def _fallback_migration_readiness(self, quality_score: int) -> Dict[str, Any]:
        """Fallback migration readiness when CrewAI is not available."""
        readiness_score = quality_score / 100.0
        
        if readiness_score >= 0.8:
            status = "ready"
            message = "Data appears ready for migration"
        elif readiness_score >= 0.6:
            status = "needs_review"
            message = "Data needs review before migration"
        else:
            status = "not_ready"
            message = "Data requires significant improvement"
        
        return {
            "status": status,
            "score": readiness_score,
            "message": message,
            "ai_analysis_recommended": True,
            "recommended_crew": "Data Cleansing Crew"
        }
    
    def analyze_data_patterns(self, sample_data: List[Dict]) -> Dict[str, Any]:
        """Analyze data patterns using CrewAI crews."""
        try:
            if not self.service_available:
                return self._fallback_data_patterns(sample_data)
            
            # Use Data Cleansing Crew for pattern analysis
            if 'data_cleansing' in self.crews:
                try:
                    crew_result = self.crews['data_cleansing'].kickoff({
                        'sample_data': sample_data,
                        'task': 'pattern_analysis'
                    })
                    
                    if crew_result and isinstance(crew_result, dict):
                        return crew_result
                except Exception as e:
                    logger.error(f"Data Cleansing Crew pattern analysis failed: {e}")
            
            return self._fallback_data_patterns(sample_data)
            
        except Exception as e:
            logger.error(f"Error analyzing data patterns: {e}")
            return self._fallback_data_patterns(sample_data)
    
    def _fallback_data_patterns(self, sample_data: List[Dict]) -> Dict[str, Any]:
        """Fallback data pattern analysis when CrewAI is not available."""
        return {
            "patterns_found": 0,
            "data_types": {},
            "value_distributions": {},
            "ai_analysis_recommended": True,
            "recommended_crew": "Data Cleansing Crew",
            "message": "Enable CrewAI for comprehensive pattern analysis"
        } 