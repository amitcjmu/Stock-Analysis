"""
Intelligence Engine Handler
Handles memory-enhanced analysis, pattern recognition, and experience-based insights.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class IntelligenceEngineHandler:
    """Handles intelligent analysis with memory and pattern recognition."""
    
    def __init__(self, memory=None):
        self.memory = memory
        self.service_available = True
        logger.info("Intelligence engine handler initialized successfully")
    
    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return True
    
    def set_memory(self, memory):
        """Set memory component for enhanced analysis."""
        self.memory = memory
    
    def intelligent_placeholder_analysis(self, cmdb_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide intelligent analysis using memory and patterns."""
        try:
            filename = cmdb_data.get('filename', '')
            structure = cmdb_data.get('structure', {})
            sample_data = cmdb_data.get('sample_data', [])
            
            # Get relevant past experiences
            relevant_experiences = self._get_relevant_experiences(filename)
            
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
            from .core_analysis import CoreAnalysisHandler
            core_handler = CoreAnalysisHandler()
            quality_score = core_handler.calculate_quality_score(cmdb_data, asset_type)
            
            # Generate issues and recommendations
            issues = self._identify_issues_from_memory(cmdb_data, relevant_experiences)
            recommendations = self._generate_memory_based_recommendations(cmdb_data, asset_type)
            
            # Assess migration readiness
            readiness = core_handler.assess_migration_readiness(cmdb_data, asset_type, quality_score)
            
            return {
                "asset_type": asset_type,
                "confidence": confidence,
                "quality_score": quality_score,
                "missing_fields": missing_fields,
                "issues": issues,
                "recommendations": recommendations,
                "migration_readiness": readiness,
                "relevant_experiences": len(relevant_experiences),
                "intelligence_mode": "memory_enhanced",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in intelligent analysis: {e}")
            return self._fallback_analysis(cmdb_data)
    
    def _get_relevant_experiences(self, filename: str) -> List[Dict]:
        """Get relevant past experiences from memory."""
        try:
            if self.memory and hasattr(self.memory, 'get_relevant_experiences'):
                return self.memory.get_relevant_experiences(filename)
            else:
                # Simulate relevant experiences based on filename patterns
                return self._simulate_experiences(filename)
        except Exception as e:
            logger.error(f"Error getting relevant experiences: {e}")
            return []
    
    def _simulate_experiences(self, filename: str) -> List[Dict]:
        """Simulate relevant experiences when memory is not available."""
        experiences = []
        filename_lower = filename.lower()
        
        # Simulate based on filename patterns
        if any(pattern in filename_lower for pattern in ['server', 'host', 'compute']):
            experiences.append({
                'type': 'pattern_match',
                'asset_type': 'server',
                'confidence': 0.8,
                'patterns': ['server-like filename']
            })
        elif any(pattern in filename_lower for pattern in ['app', 'application', 'service']):
            experiences.append({
                'type': 'pattern_match',
                'asset_type': 'application',
                'confidence': 0.8,
                'patterns': ['application-like filename']
            })
        elif any(pattern in filename_lower for pattern in ['db', 'database', 'sql']):
            experiences.append({
                'type': 'pattern_match',
                'asset_type': 'database',
                'confidence': 0.8,
                'patterns': ['database-like filename']
            })
        
        return experiences
    
    def _detect_asset_type_from_memory(self, cmdb_data: Dict, experiences: List[Dict]) -> str:
        """Detect asset type using memory and past experiences."""
        try:
            # Check experiences for asset type patterns
            type_confidence = {}
            
            for exp in experiences:
                if exp.get('type') == 'pattern_match':
                    asset_type = exp.get('asset_type', 'generic')
                    confidence = exp.get('confidence', 0.5)
                    
                    if asset_type not in type_confidence:
                        type_confidence[asset_type] = 0
                    type_confidence[asset_type] += confidence
            
            # Use memory-based detection if available
            if type_confidence:
                best_type = max(type_confidence.items(), key=lambda x: x[1])
                if best_type[1] > 0.6:
                    return best_type[0]
            
            # Fallback to core analysis
            from .core_analysis import CoreAnalysisHandler
            core_handler = CoreAnalysisHandler()
            return core_handler.detect_asset_type(cmdb_data)
            
        except Exception as e:
            logger.error(f"Error detecting asset type from memory: {e}")
            return 'generic'
    
    def _identify_missing_fields_from_memory(self, cmdb_data: Dict, asset_type: str, 
                                           experiences: List[Dict]) -> List[str]:
        """Identify missing fields using memory and past experiences."""
        try:
            # Start with core analysis
            from .core_analysis import CoreAnalysisHandler
            core_handler = CoreAnalysisHandler()
            missing_fields = core_handler.identify_missing_fields(cmdb_data, asset_type)
            
            # Enhance with memory insights
            for exp in experiences:
                if exp.get('type') == 'user_feedback':
                    feedback_fields = exp.get('missing_fields', [])
                    for field in feedback_fields:
                        if field not in missing_fields:
                            missing_fields.append(field)
            
            return missing_fields
            
        except Exception as e:
            logger.error(f"Error identifying missing fields from memory: {e}")
            return []
    
    def _calculate_memory_based_confidence(self, cmdb_data: Dict, 
                                         experiences: List[Dict]) -> float:
        """Calculate confidence based on memory and past experiences."""
        try:
            base_confidence = 0.5
            
            # Boost confidence based on relevant experiences
            if experiences:
                experience_boost = min(0.3, len(experiences) * 0.1)
                base_confidence += experience_boost
            
            # Check for clear type indicators
            structure = cmdb_data.get('structure', {})
            columns = structure.get('columns', [])
            
            from .core_analysis import CoreAnalysisHandler
            core_handler = CoreAnalysisHandler()
            if core_handler.has_clear_type_indicators(columns):
                base_confidence += 0.15
            
            # Check data completeness
            sample_data = cmdb_data.get('sample_data', [])
            if sample_data:
                completeness = core_handler.calculate_data_completeness(sample_data)
                base_confidence += completeness * 0.1
            
            return min(0.95, base_confidence)  # Cap at 95% for placeholder analysis
            
        except Exception as e:
            logger.error(f"Error calculating memory-based confidence: {e}")
            return 0.5
    
    def _identify_issues_from_memory(self, cmdb_data: Dict, experiences: List[Dict]) -> List[str]:
        """Identify issues using memory and past experiences."""
        try:
            # Start with core analysis
            from .core_analysis import CoreAnalysisHandler
            core_handler = CoreAnalysisHandler()
            issues = core_handler.identify_issues(cmdb_data)
            
            # Add memory-based issues
            for exp in experiences:
                if exp.get('type') == 'user_feedback':
                    analysis_issues = exp.get('corrections', {}).get('analysis_issues', '')
                    if analysis_issues:
                        # Extract common issue patterns
                        if 'naming' in analysis_issues.lower():
                            if "Inconsistent naming convention detected" not in issues:
                                issues.append("Inconsistent naming convention detected")
                        if 'missing' in analysis_issues.lower():
                            if "Missing critical fields identified" not in issues:
                                issues.append("Missing critical fields identified")
            
            return issues
            
        except Exception as e:
            logger.error(f"Error identifying issues from memory: {e}")
            return ["Error analyzing data quality"]
    
    def _generate_memory_based_recommendations(self, cmdb_data: Dict, asset_type: str) -> List[str]:
        """Generate recommendations based on memory and asset type."""
        try:
            # Start with core recommendations
            from .core_analysis import CoreAnalysisHandler
            core_handler = CoreAnalysisHandler()
            recommendations = core_handler.generate_basic_recommendations(cmdb_data, asset_type)
            
            # Add memory-enhanced recommendations
            structure = cmdb_data.get('structure', {})
            columns = structure.get('columns', [])
            
            # Intelligent recommendations based on patterns
            if len(columns) > 10:
                recommendations.append("Consider consolidating similar fields to reduce complexity")
            
            if any('id' in col.lower() for col in columns):
                recommendations.append("Ensure identifier fields are properly documented and unique")
            
            if asset_type == "application":
                recommendations.append("Map application dependencies for migration planning")
                recommendations.append("Identify application owners and stakeholders")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating memory-based recommendations: {e}")
            return ["Complete data analysis and standardization"]
    
    def learn_from_feedback(self, feedback_data: Dict[str, Any]) -> bool:
        """Learn from user feedback to improve future analysis."""
        try:
            if self.memory and hasattr(self.memory, 'store_experience'):
                experience = {
                    'type': 'user_feedback',
                    'timestamp': datetime.utcnow().isoformat(),
                    'feedback': feedback_data,
                    'corrections': feedback_data.get('corrections', {}),
                    'asset_type': feedback_data.get('asset_type'),
                    'filename': feedback_data.get('filename', '')
                }
                
                self.memory.store_experience(experience)
                logger.info(f"Stored learning experience for {feedback_data.get('filename', 'unknown')}")
                return True
            else:
                logger.info(f"Memory not available - would store: {feedback_data.get('filename', 'unknown')}")
                return False
                
        except Exception as e:
            logger.error(f"Error learning from feedback: {e}")
            return False
    
    def analyze_historical_patterns(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze historical patterns to improve future analysis."""
        try:
            if not historical_data:
                return {"patterns": [], "insights": []}
            
            patterns = {}
            asset_type_frequency = {}
            
            # Analyze historical data patterns
            for data in historical_data:
                asset_type = data.get('asset_type', 'unknown')
                
                # Count asset type frequency
                if asset_type not in asset_type_frequency:
                    asset_type_frequency[asset_type] = 0
                asset_type_frequency[asset_type] += 1
                
                # Analyze field patterns
                fields = data.get('fields', [])
                for field in fields:
                    if field not in patterns:
                        patterns[field] = {'count': 0, 'asset_types': set()}
                    patterns[field]['count'] += 1
                    patterns[field]['asset_types'].add(asset_type)
            
            # Generate insights
            insights = []
            
            # Most common asset type
            if asset_type_frequency:
                most_common = max(asset_type_frequency.items(), key=lambda x: x[1])
                insights.append(f"Most common asset type: {most_common[0]} ({most_common[1]} occurrences)")
            
            # Most common fields
            common_fields = sorted(patterns.items(), key=lambda x: x[1]['count'], reverse=True)[:5]
            if common_fields:
                field_names = [field[0] for field in common_fields]
                insights.append(f"Most common fields: {', '.join(field_names)}")
            
            return {
                "patterns": patterns,
                "asset_type_frequency": asset_type_frequency,
                "insights": insights,
                "historical_count": len(historical_data)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing historical patterns: {e}")
            return {"patterns": [], "insights": [], "error": str(e)}
    
    def get_intelligence_summary(self) -> Dict[str, Any]:
        """Get summary of intelligence capabilities and learned patterns."""
        try:
            summary = {
                "intelligence_available": True,
                "memory_available": self.memory is not None,
                "learning_enabled": self.memory is not None,
                "pattern_recognition": True,
                "experience_based_analysis": True
            }
            
            if self.memory and hasattr(self.memory, 'get_statistics'):
                memory_stats = self.memory.get_statistics()
                summary.update(memory_stats)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting intelligence summary: {e}")
            return {
                "intelligence_available": True,
                "memory_available": False,
                "error": str(e)
            }
    
    def _fallback_analysis(self, cmdb_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis when intelligence features fail."""
        try:
            from .core_analysis import CoreAnalysisHandler
            core_handler = CoreAnalysisHandler()
            
            asset_type = core_handler.detect_asset_type(cmdb_data)
            quality_score = core_handler.calculate_quality_score(cmdb_data, asset_type)
            missing_fields = core_handler.identify_missing_fields(cmdb_data, asset_type)
            issues = core_handler.identify_issues(cmdb_data)
            recommendations = core_handler.generate_basic_recommendations(cmdb_data, asset_type)
            readiness = core_handler.assess_migration_readiness(cmdb_data, asset_type, quality_score)
            
            return {
                "asset_type": asset_type,
                "confidence": 0.7,
                "quality_score": quality_score,
                "missing_fields": missing_fields,
                "issues": issues,
                "recommendations": recommendations,
                "migration_readiness": readiness,
                "relevant_experiences": 0,
                "intelligence_mode": "fallback",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in fallback analysis: {e}")
            return {
                "asset_type": "unknown",
                "confidence": 0.5,
                "quality_score": 50,
                "missing_fields": [],
                "issues": ["Analysis error occurred"],
                "recommendations": ["Review data and try again"],
                "migration_readiness": {
                    "readiness_score": 0.5,
                    "readiness_level": "Unknown",
                    "readiness_message": "Unable to assess"
                },
                "relevant_experiences": 0,
                "intelligence_mode": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            } 