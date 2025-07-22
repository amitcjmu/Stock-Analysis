"""
Intelligence Engine Handler
Handles CrewAI-based analysis, pattern recognition, and AI-driven insights.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Check CrewAI availability
CREWAI_AVAILABLE = bool(os.getenv('DEEPINFRA_API_KEY') and os.getenv('CREWAI_ENABLED', 'true').lower() == 'true')

try:
    from app.services.crewai_flows.crews.field_mapping_crew import create_field_mapping_crew
    from app.services.crewai_flows.crews.inventory_building_crew import create_inventory_building_crew
    from app.services.crewai_flows.data_cleansing_crew import create_data_cleansing_crew
    CREWS_AVAILABLE = True
except ImportError:
    CREWS_AVAILABLE = False

class IntelligenceEngineHandler:
    """Handles CrewAI-based intelligent analysis with AI-driven insights."""
    
    def __init__(self, memory=None, llm=None):
        self.memory = memory
        self.llm = llm
        self.crews = {}
        self.service_available = CREWAI_AVAILABLE and CREWS_AVAILABLE
        
        if self.service_available and self.llm:
            self._initialize_crews()
        
        logger.info(f"Intelligence engine handler initialized successfully (CrewAI: {self.service_available})")
    
    def _initialize_crews(self):
        """Initialize CrewAI crews for intelligent analysis."""
        try:
            if CREWS_AVAILABLE and self.llm:
                self.crews['inventory_building'] = create_inventory_building_crew(llm=self.llm)
                self.crews['field_mapping'] = create_field_mapping_crew(llm=self.llm)
                self.crews['data_cleansing'] = create_data_cleansing_crew(llm=self.llm)
                logger.info("CrewAI crews initialized for intelligence analysis")
        except Exception as e:
            logger.error(f"Failed to initialize crews: {e}")
            self.service_available = False
    
    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return self.service_available
    
    def set_memory(self, memory):
        """Set memory component for enhanced analysis."""
        self.memory = memory
    
    def intelligent_placeholder_analysis(self, cmdb_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide AI-driven analysis using CrewAI crews."""
        try:
            if not self.service_available:
                return self._fallback_analysis(cmdb_data)
            
            filename = cmdb_data.get('filename', '')
            structure = cmdb_data.get('structure', {})
            sample_data = cmdb_data.get('sample_data', [])
            
            # Use CrewAI crews for analysis
            analysis_results = {}
            
            # Asset type detection using Inventory Building Crew
            if 'inventory_building' in self.crews:
                try:
                    inventory_result = self.crews['inventory_building'].kickoff({
                        'cmdb_data': cmdb_data,
                        'task': 'asset_classification'
                    })
                    analysis_results['asset_type'] = inventory_result.get('asset_type', 'generic')
                    analysis_results['confidence'] = inventory_result.get('confidence', 0.7)
                except Exception as e:
                    logger.error(f"Inventory crew analysis failed: {e}")
                    analysis_results['asset_type'] = 'generic'
                    analysis_results['confidence'] = 0.5
            
            # Field mapping analysis using Field Mapping Crew
            if 'field_mapping' in self.crews:
                try:
                    mapping_result = self.crews['field_mapping'].kickoff({
                        'data_structure': structure,
                        'task': 'field_analysis'
                    })
                    analysis_results['missing_fields'] = mapping_result.get('missing_fields', [])
                except Exception as e:
                    logger.error(f"Field mapping crew analysis failed: {e}")
                    analysis_results['missing_fields'] = []
            
            # Data quality assessment using Data Cleansing Crew
            if 'data_cleansing' in self.crews:
                try:
                    quality_result = self.crews['data_cleansing'].kickoff({
                        'sample_data': sample_data,
                        'task': 'quality_assessment'
                    })
                    analysis_results['quality_score'] = quality_result.get('quality_score', 0.7)
                    analysis_results['issues'] = quality_result.get('issues', [])
                    analysis_results['recommendations'] = quality_result.get('recommendations', [])
                except Exception as e:
                    logger.error(f"Data cleansing crew analysis failed: {e}")
                    analysis_results['quality_score'] = 0.7
                    analysis_results['issues'] = []
                    analysis_results['recommendations'] = []
            
            # Migration readiness assessment
            quality_score = analysis_results.get('quality_score', 0.7)
            asset_type = analysis_results.get('asset_type', 'generic')
            
            if quality_score >= 0.8:
                readiness = "ready"
            elif quality_score >= 0.6:
                readiness = "needs_review"
            else:
                readiness = "not_ready"
            
            return {
                "asset_type": analysis_results.get('asset_type', 'generic'),
                "confidence": analysis_results.get('confidence', 0.7),
                "quality_score": analysis_results.get('quality_score', 0.7),
                "missing_fields": analysis_results.get('missing_fields', []),
                "issues": analysis_results.get('issues', []),
                "recommendations": analysis_results.get('recommendations', []),
                "migration_readiness": readiness,
                "ai_analysis_recommended": True,
                "intelligence_mode": "crewai_enhanced",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in CrewAI intelligent analysis: {e}")
            return self._fallback_analysis(cmdb_data)
    
    def learn_from_feedback(self, feedback_data: Dict[str, Any]) -> bool:
        """Process feedback for CrewAI learning (placeholder for future crew memory integration)."""
        try:
            if self.memory:
                # Store feedback for future crew learning
                feedback_entry = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'feedback_type': 'user_correction',
                    'data': feedback_data,
                    'source': 'intelligence_engine'
                }
                
                if hasattr(self.memory, 'store_feedback'):
                    self.memory.store_feedback(feedback_entry)
                
                logger.info("Feedback stored for CrewAI learning")
                return True
            
            logger.warning("No memory component available for feedback storage")
            return False
            
        except Exception as e:
            logger.error(f"Error processing feedback: {e}")
            return False
    
    def analyze_historical_patterns(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze historical patterns using CrewAI crews."""
        try:
            if not self.service_available or not historical_data:
                return {
                    "patterns_found": 0,
                    "insights": [],
                    "ai_analysis_recommended": True,
                    "recommendations": ["Use CrewAI crews for pattern analysis"]
                }
            
            # Use crews for historical analysis
            patterns = []
            insights = []
            
            # Aggregate analysis using available crews
            for crew_name, crew in self.crews.items():
                try:
                    result = crew.kickoff({
                        'historical_data': historical_data,
                        'task': 'pattern_analysis'
                    })
                    if result.get('patterns'):
                        patterns.extend(result['patterns'])
                    if result.get('insights'):
                        insights.extend(result['insights'])
                except Exception as e:
                    logger.error(f"Pattern analysis failed for {crew_name}: {e}")
            
            return {
                "patterns_found": len(patterns),
                "patterns": patterns,
                "insights": insights,
                "ai_analysis_recommended": True,
                "analysis_mode": "crewai_historical",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in historical pattern analysis: {e}")
            return {
                "patterns_found": 0,
                "insights": [],
                "ai_analysis_recommended": True,
                "error": str(e)
            }
    
    def get_intelligence_summary(self) -> Dict[str, Any]:
        """Get intelligence system summary."""
        try:
            crew_status = {}
            for crew_name, crew in self.crews.items():
                crew_status[crew_name] = crew is not None
            
            return {
                "service_available": self.service_available,
                "crewai_available": CREWAI_AVAILABLE,
                "crews_available": CREWS_AVAILABLE,
                "active_crews": len(self.crews),
                "crew_status": crew_status,
                "memory_available": self.memory is not None,
                "llm_configured": self.llm is not None,
                "intelligence_mode": "crewai_based",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting intelligence summary: {e}")
            return {
                "service_available": False,
                "error": str(e),
                "ai_analysis_recommended": True
            }
    
    def _fallback_analysis(self, cmdb_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis when CrewAI is not available."""
        logger.warning("Using fallback analysis - CrewAI crews not available")
        
        return {
            "asset_type": "generic",
            "confidence": 0.5,
            "quality_score": 0.6,
            "missing_fields": [],
            "issues": ["CrewAI analysis not available"],
            "recommendations": ["Enable CrewAI for intelligent analysis"],
            "migration_readiness": "needs_review",
            "ai_analysis_recommended": True,
            "intelligence_mode": "fallback",
            "timestamp": datetime.utcnow().isoformat()
        } 