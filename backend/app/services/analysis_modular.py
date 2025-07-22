"""
Intelligent Analysis Services - Modular & Robust
Provides memory-enhanced analysis and intelligent placeholders when CrewAI is unavailable.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from .analysis_handlers import CoreAnalysisHandler, IntelligenceEngineHandler, PlaceholderHandler

logger = logging.getLogger(__name__)

class IntelligentAnalysisService:
    """Modular intelligent analysis service with enhanced capabilities."""
    
    def __init__(self, memory=None):
        # Initialize handlers
        self.core_analysis = CoreAnalysisHandler()
        self.intelligence_engine = IntelligenceEngineHandler(memory)
        self.placeholder_handler = PlaceholderHandler()
        
        # Set memory reference
        self.memory = memory
        if memory:
            self.intelligence_engine.set_memory(memory)
        
        logger.info("Intelligent Analysis Service initialized with modular handlers")
    
    def is_available(self) -> bool:
        """Check if the service is properly initialized."""
        return True  # Always available with fallbacks
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of analysis system."""
        return {
            "status": "healthy",
            "service": "analysis",
            "version": "2.0.0",
            "core_analysis": self.core_analysis.is_available(),
            "intelligence_engine": self.intelligence_engine.is_available(),
            "placeholder_handler": self.placeholder_handler.is_available(),
            "memory_available": self.memory is not None,
            "intelligence_summary": self.intelligence_engine.get_intelligence_summary()
        }
    
    def set_memory(self, memory):
        """Set memory component for enhanced analysis."""
        self.memory = memory
        self.intelligence_engine.set_memory(memory)
    
    # Main analysis methods
    def intelligent_placeholder_analysis(self, cmdb_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide intelligent analysis using memory and patterns."""
        try:
            return self.intelligence_engine.intelligent_placeholder_analysis(cmdb_data)
        except Exception as e:
            logger.error(f"Intelligent analysis failed: {e}")
            return self._fallback_basic_analysis(cmdb_data)
    
    def analyze_cmdb_data(self, cmdb_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive CMDB data analysis."""
        try:
            # Detect asset type
            asset_type = self.core_analysis.detect_asset_type(cmdb_data)
            
            # Calculate quality metrics
            quality_score = self.core_analysis.calculate_quality_score(cmdb_data, asset_type)
            data_completeness = 0.0
            sample_data = cmdb_data.get('sample_data', [])
            if sample_data:
                data_completeness = self.core_analysis.calculate_data_completeness(sample_data)
            
            # Identify issues and missing fields
            missing_fields = self.core_analysis.identify_missing_fields(cmdb_data, asset_type)
            issues = self.core_analysis.identify_issues(cmdb_data)
            recommendations = self.core_analysis.generate_basic_recommendations(cmdb_data, asset_type)
            
            # Assess migration readiness
            readiness = self.core_analysis.assess_migration_readiness(cmdb_data, asset_type, quality_score)
            
            # Analyze data patterns
            patterns = self.core_analysis.analyze_data_patterns(sample_data)
            
            return {
                "asset_type": asset_type,
                "quality_score": quality_score,
                "data_completeness": data_completeness,
                "missing_fields": missing_fields,
                "issues": issues,
                "recommendations": recommendations,
                "migration_readiness": readiness,
                "data_patterns": patterns,
                "analysis_mode": "comprehensive",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"CMDB analysis failed: {e}")
            return self._fallback_basic_analysis(cmdb_data)
    
    def placeholder_wave_planning(self, wave_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide intelligent wave planning recommendations."""
        try:
            return self.placeholder_handler.placeholder_wave_planning(wave_data)
        except Exception as e:
            logger.error(f"Wave planning failed: {e}")
            return {
                "total_applications": 0,
                "total_waves": 0,
                "waves": [],
                "total_timeline_weeks": 0,
                "error": str(e),
                "placeholder_mode": True
            }
    
    def placeholder_cmdb_processing(self, processing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide intelligent CMDB processing recommendations."""
        try:
            return self.placeholder_handler.placeholder_cmdb_processing(processing_data)
        except Exception as e:
            logger.error(f"CMDB processing analysis failed: {e}")
            return {
                "processing_recommendations": ["Review and process data"],
                "data_transformations": ["Apply standard transformations"],
                "enrichment_opportunities": ["Add missing context"],
                "quality_improvements": ["Improve data quality"],
                "migration_preparation": ["Prepare for migration"],
                "error": str(e),
                "placeholder_mode": True
            }
    
    def generate_migration_timeline(self, migration_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive migration timeline."""
        try:
            return self.placeholder_handler.generate_migration_timeline(migration_data)
        except Exception as e:
            logger.error(f"Migration timeline generation failed: {e}")
            return {
                "timeline_weeks": 16,
                "phases": [],
                "milestones": [],
                "error": str(e),
                "placeholder_mode": True
            }
    
    # Memory and learning methods
    def learn_from_feedback(self, feedback_data: Dict[str, Any]) -> bool:
        """Learn from user feedback to improve future analysis."""
        try:
            return self.intelligence_engine.learn_from_feedback(feedback_data)
        except Exception as e:
            logger.error(f"Learning from feedback failed: {e}")
            return False
    
    def analyze_historical_patterns(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze historical patterns to improve future analysis."""
        try:
            return self.intelligence_engine.analyze_historical_patterns(historical_data)
        except Exception as e:
            logger.error(f"Historical pattern analysis failed: {e}")
            return {"patterns": [], "insights": [], "error": str(e)}
    
    # Core analysis method exposure for compatibility
    def calculate_quality_score(self, cmdb_data: Dict, asset_type: str) -> int:
        """Calculate data quality score."""
        return self.core_analysis.calculate_quality_score(cmdb_data, asset_type)
    
    def calculate_data_completeness(self, sample_data: List[Dict]) -> float:
        """Calculate data completeness ratio."""
        return self.core_analysis.calculate_data_completeness(sample_data)
    
    def detect_asset_type(self, cmdb_data: Dict[str, Any]) -> str:
        """Detect asset type from CMDB data."""
        return self.core_analysis.detect_asset_type(cmdb_data)
    
    def identify_missing_fields(self, cmdb_data: Dict, asset_type: str) -> List[str]:
        """Identify missing required fields based on asset type."""
        return self.core_analysis.identify_missing_fields(cmdb_data, asset_type)
    
    def identify_issues(self, cmdb_data: Dict) -> List[str]:
        """Identify potential issues in the data."""
        return self.core_analysis.identify_issues(cmdb_data)
    
    def generate_basic_recommendations(self, cmdb_data: Dict, asset_type: str) -> List[str]:
        """Generate basic recommendations for data improvement."""
        return self.core_analysis.generate_basic_recommendations(cmdb_data, asset_type)
    
    def assess_migration_readiness(self, cmdb_data: Dict, asset_type: str, quality_score: int) -> Dict[str, Any]:
        """Assess migration readiness based on data quality and completeness."""
        return self.core_analysis.assess_migration_readiness(cmdb_data, asset_type, quality_score)
    
    def analyze_data_patterns(self, sample_data: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns in the sample data."""
        return self.core_analysis.analyze_data_patterns(sample_data)
    
    # Utility and compatibility methods
    def get_intelligence_summary(self) -> Dict[str, Any]:
        """Get summary of intelligence capabilities and learned patterns."""
        return self.intelligence_engine.get_intelligence_summary()
    
    def has_clear_type_indicators(self, columns: List[str]) -> bool:
        """Check if data has clear type indicators."""
        return self.core_analysis.has_clear_type_indicators(columns)
    
    # Fallback methods
    def _fallback_basic_analysis(self, cmdb_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis when intelligent features fail."""
        try:
            asset_type = self.core_analysis.detect_asset_type(cmdb_data)
            quality_score = self.core_analysis.calculate_quality_score(cmdb_data, asset_type)
            missing_fields = self.core_analysis.identify_missing_fields(cmdb_data, asset_type)
            issues = self.core_analysis.identify_issues(cmdb_data)
            recommendations = self.core_analysis.generate_basic_recommendations(cmdb_data, asset_type)
            readiness = self.core_analysis.assess_migration_readiness(cmdb_data, asset_type, quality_score)
            
            return {
                "asset_type": asset_type,
                "quality_score": quality_score,
                "missing_fields": missing_fields,
                "issues": issues,
                "recommendations": recommendations,
                "migration_readiness": readiness,
                "confidence": 0.7,
                "relevant_experiences": 0,
                "analysis_mode": "basic_fallback",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Fallback analysis failed: {e}")
            return {
                "asset_type": "unknown",
                "quality_score": 50,
                "missing_fields": [],
                "issues": ["Analysis error occurred"],
                "recommendations": ["Review data and try again"],
                "migration_readiness": {
                    "readiness_score": 0.5,
                    "readiness_level": "Unknown",
                    "readiness_message": "Unable to assess"
                },
                "confidence": 0.5,
                "relevant_experiences": 0,
                "analysis_mode": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

# Legacy compatibility classes and functions
class IntelligentAnalyzer:
    """Legacy compatibility class."""
    
    def __init__(self, memory=None):
        self.service = IntelligentAnalysisService(memory)
        self.memory = memory
    
    def intelligent_placeholder_analysis(self, cmdb_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.service.intelligent_placeholder_analysis(cmdb_data)

# Static placeholder functions for backward compatibility
def placeholder_wave_planning(wave_data: Dict[str, Any]) -> Dict[str, Any]:
    """Provide intelligent wave planning recommendations."""
    service = IntelligentAnalysisService()
    return service.placeholder_wave_planning(wave_data)

def placeholder_cmdb_processing(processing_data: Dict[str, Any]) -> Dict[str, Any]:
    """Provide intelligent CMDB processing recommendations."""
    service = IntelligentAnalysisService()
    return service.placeholder_cmdb_processing(processing_data)

def get_analysis_health() -> Dict[str, Any]:
    """Get health status of analysis system."""
    try:
        service = IntelligentAnalysisService()
        return service.get_health_status()
    except Exception as e:
        return {
            "status": "error",
            "service": "analysis",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Export main classes and functions for backward compatibility
__all__ = [
    "IntelligentAnalysisService",
    "IntelligentAnalyzer",
    "placeholder_wave_planning",
    "placeholder_cmdb_processing",
    "get_analysis_health"
] 