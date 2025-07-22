"""
Confidence Scoring Manager - Framework for agent confidence tracking and escalation
"""

import logging
import statistics
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

class ConfidenceManager:
    """
    Confidence Scoring Manager
    
    Manages confidence scoring across all discovery agents, handles aggregation,
    and determines escalation triggers based on confidence thresholds.
    """
    
    def __init__(self):
        self.confidence_history = {}
        self.escalation_thresholds = {
            'low': 60.0,      # Below 60% triggers crew escalation
            'medium': 75.0,   # Below 75% flags for review
            'high': 90.0      # Above 90% is high confidence
        }
        
        # Weight factors for different agents
        self.agent_weights = {
            'data_validation': 0.15,      # 15% weight
            'attribute_mapping': 0.25,    # 25% weight (critical for migration)
            'data_cleansing': 0.20,       # 20% weight
            'asset_inventory': 0.15,      # 15% weight
            'dependency_analysis': 0.15,  # 15% weight
            'tech_debt_analysis': 0.10    # 10% weight
        }
        
        logger.info("🎯 Confidence Manager initialized with escalation thresholds")
    
    def calculate_agent_confidence(self, agent_id: str, factors: Dict[str, Any]) -> float:
        """Calculate confidence score for an individual agent"""
        base_confidence = factors.get('base_confidence', 50.0)
        
        # Apply factor-based adjustments
        adjustments = []
        
        # Data quality factor
        data_quality = factors.get('data_quality_score', 75.0)
        adjustments.append(('data_quality', (data_quality - 75.0) * 0.3))
        
        # Pattern matching accuracy
        pattern_accuracy = factors.get('pattern_accuracy', 70.0)
        adjustments.append(('pattern_accuracy', (pattern_accuracy - 70.0) * 0.2))
        
        # Completeness factor
        completeness = factors.get('completeness_percentage', 80.0)
        adjustments.append(('completeness', (completeness - 80.0) * 0.25))
        
        # Validation success rate
        validation_rate = factors.get('validation_success_rate', 85.0)
        adjustments.append(('validation', (validation_rate - 85.0) * 0.15))
        
        # Apply adjustments
        final_confidence = base_confidence
        for factor_name, adjustment in adjustments:
            final_confidence += adjustment
        
        # Clamp to 0-100 range
        final_confidence = max(0.0, min(100.0, final_confidence))
        
        # Store in history
        if agent_id not in self.confidence_history:
            self.confidence_history[agent_id] = []
        
        self.confidence_history[agent_id].append({
            'timestamp': datetime.utcnow().isoformat(),
            'confidence': final_confidence,
            'factors': factors,
            'adjustments': adjustments
        })
        
        logger.debug(f"🎯 {agent_id} confidence: {final_confidence:.1f}% (base: {base_confidence:.1f}%)")
        return final_confidence
    
    def aggregate_flow_confidence(self, agent_confidences: Dict[str, float]) -> Dict[str, Any]:
        """Aggregate confidence scores across all agents in the flow"""
        if not agent_confidences:
            return {
                'overall_confidence': 50.0,
                'confidence_level': 'medium',
                'escalation_recommended': True,
                'agent_breakdown': {}
            }
        
        # Calculate weighted average
        weighted_sum = 0.0
        total_weight = 0.0
        
        for agent_id, confidence in agent_confidences.items():
            weight = self.agent_weights.get(agent_id, 0.1)  # Default 10% weight
            weighted_sum += confidence * weight
            total_weight += weight
        
        overall_confidence = weighted_sum / total_weight if total_weight > 0 else 50.0
        
        # Determine confidence level
        if overall_confidence >= self.escalation_thresholds['high']:
            confidence_level = 'high'
        elif overall_confidence >= self.escalation_thresholds['medium']:
            confidence_level = 'medium'
        else:
            confidence_level = 'low'
        
        # Check escalation recommendation
        escalation_recommended = overall_confidence < self.escalation_thresholds['low']
        
        # Identify low-confidence agents
        low_confidence_agents = [
            agent_id for agent_id, confidence in agent_confidences.items()
            if confidence < self.escalation_thresholds['low']
        ]
        
        return {
            'overall_confidence': overall_confidence,
            'confidence_level': confidence_level,
            'escalation_recommended': escalation_recommended,
            'low_confidence_agents': low_confidence_agents,
            'agent_breakdown': {
                agent_id: {
                    'confidence': confidence,
                    'weight': self.agent_weights.get(agent_id, 0.1),
                    'contribution': confidence * self.agent_weights.get(agent_id, 0.1)
                }
                for agent_id, confidence in agent_confidences.items()
            },
            'confidence_statistics': {
                'min': min(agent_confidences.values()),
                'max': max(agent_confidences.values()),
                'avg': statistics.mean(agent_confidences.values()),
                'std_dev': statistics.stdev(agent_confidences.values()) if len(agent_confidences) > 1 else 0.0
            }
        }
    
    def determine_escalation_triggers(self, agent_confidences: Dict[str, float], 
                                    flow_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Determine which agents/phases should trigger crew escalation"""
        escalation_triggers = {
            'should_escalate': False,
            'escalation_reasons': [],
            'recommended_crews': [],
            'escalation_priority': 'low'
        }
        
        # Check individual agent thresholds
        for agent_id, confidence in agent_confidences.items():
            if confidence < self.escalation_thresholds['low']:
                escalation_triggers['should_escalate'] = True
                escalation_triggers['escalation_reasons'].append(
                    f"{agent_id} confidence ({confidence:.1f}%) below threshold ({self.escalation_thresholds['low']:.1f}%)"
                )
                
                # Map agent to crew recommendations
                crew_mapping = {
                    'data_validation': 'data_quality_crew',
                    'attribute_mapping': 'field_mapping_crew',
                    'data_cleansing': 'data_cleansing_crew',
                    'asset_inventory': 'asset_intelligence_crew',
                    'dependency_analysis': 'dependency_analysis_crew',
                    'tech_debt_analysis': 'tech_debt_analysis_crew'
                }
                
                recommended_crew = crew_mapping.get(agent_id, f"{agent_id}_crew")
                if recommended_crew not in escalation_triggers['recommended_crews']:
                    escalation_triggers['recommended_crews'].append(recommended_crew)
        
        # Determine escalation priority
        overall_confidence = self.aggregate_flow_confidence(agent_confidences)['overall_confidence']
        
        if overall_confidence < 40.0:
            escalation_triggers['escalation_priority'] = 'critical'
        elif overall_confidence < 60.0:
            escalation_triggers['escalation_priority'] = 'high'
        elif overall_confidence < 75.0:
            escalation_triggers['escalation_priority'] = 'medium'
        else:
            escalation_triggers['escalation_priority'] = 'low'
        
        # Context-based escalation triggers
        if flow_context:
            # High-value assets trigger lower thresholds
            if flow_context.get('high_value_assets', 0) > 10:
                if overall_confidence < 80.0:
                    escalation_triggers['should_escalate'] = True
                    escalation_triggers['escalation_reasons'].append(
                        "High-value assets detected - elevated confidence threshold required"
                    )
            
            # Complex environment triggers
            if flow_context.get('environment_complexity', 'low') == 'high':
                if overall_confidence < 70.0:
                    escalation_triggers['should_escalate'] = True
                    escalation_triggers['escalation_reasons'].append(
                        "Complex environment detected - crew collaboration recommended"
                    )
        
        return escalation_triggers
    
    def get_confidence_recommendations(self, agent_confidences: Dict[str, float]) -> List[Dict[str, Any]]:
        """Get recommendations for improving confidence scores"""
        recommendations = []
        
        for agent_id, confidence in agent_confidences.items():
            if confidence < self.escalation_thresholds['medium']:
                if agent_id == 'data_validation':
                    recommendations.append({
                        'agent': agent_id,
                        'issue': 'Low data validation confidence',
                        'recommendations': [
                            'Review data quality and completeness',
                            'Check for missing or invalid data patterns',
                            'Consider additional data validation rules'
                        ],
                        'priority': 'high' if confidence < 50 else 'medium'
                    })
                
                elif agent_id == 'attribute_mapping':
                    recommendations.append({
                        'agent': agent_id,
                        'issue': 'Low field mapping confidence',
                        'recommendations': [
                            'Review field mapping accuracy',
                            'Provide additional mapping examples',
                            'Consider manual field mapping for critical attributes'
                        ],
                        'priority': 'critical' if confidence < 50 else 'high'
                    })
                
                elif agent_id == 'data_cleansing':
                    recommendations.append({
                        'agent': agent_id,
                        'issue': 'Low data cleansing confidence',
                        'recommendations': [
                            'Review data standardization results',
                            'Check cleansing rule effectiveness',
                            'Consider additional data transformation steps'
                        ],
                        'priority': 'medium'
                    })
                
                # Add recommendations for other agents...
        
        return recommendations
    
    def track_confidence_improvement(self, agent_id: str, before_confidence: float, 
                                   after_confidence: float, intervention: str) -> Dict[str, Any]:
        """Track confidence improvements after interventions"""
        improvement = after_confidence - before_confidence
        
        improvement_record = {
            'agent_id': agent_id,
            'before_confidence': before_confidence,
            'after_confidence': after_confidence,
            'improvement': improvement,
            'intervention': intervention,
            'timestamp': datetime.utcnow().isoformat(),
            'effectiveness': 'high' if improvement > 10 else 'medium' if improvement > 5 else 'low'
        }
        
        # Store improvement history
        if not hasattr(self, 'improvement_history'):
            self.improvement_history = []
        
        self.improvement_history.append(improvement_record)
        
        logger.info(f"📈 {agent_id} confidence improved by {improvement:.1f}% after {intervention}")
        return improvement_record
    
    def get_confidence_summary(self, flow_id: str) -> Dict[str, Any]:
        """Get comprehensive confidence summary for a flow"""
        return {
            'flow_id': flow_id,
            'confidence_history': self.confidence_history,
            'escalation_thresholds': self.escalation_thresholds,
            'agent_weights': self.agent_weights,
            'improvement_history': getattr(self, 'improvement_history', []),
            'summary_generated_at': datetime.utcnow().isoformat()
        }
    
    async def get_page_confidence_scores(self, page: str) -> Dict[str, Any]:
        """Get confidence scores for agents relevant to a specific page"""
        # Map pages to relevant agents
        page_agent_mapping = {
            'dependencies': ['dependency_analysis', 'asset_inventory'],
            'attribute-mapping': ['attribute_mapping', 'data_validation'],
            'data-cleansing': ['data_cleansing', 'attribute_mapping'],
            'inventory': ['asset_inventory', 'data_validation'],
            'tech-debt': ['tech_debt_analysis', 'asset_inventory']
        }
        
        relevant_agents = page_agent_mapping.get(page, ['data_validation', 'attribute_mapping'])
        
        # Get current confidence scores for relevant agents
        agent_confidences = {}
        for agent_id in relevant_agents:
            # For demo purposes, simulate confidence scores
            # In real implementation, this would fetch from agent execution results
            if agent_id == 'dependency_analysis':
                agent_confidences[agent_id] = 75.0 if page == 'dependencies' else 65.0
            elif agent_id == 'asset_inventory':
                agent_confidences[agent_id] = 82.0
            elif agent_id == 'attribute_mapping':
                agent_confidences[agent_id] = 88.0
            elif agent_id == 'data_validation':
                agent_confidences[agent_id] = 91.0
            elif agent_id == 'data_cleansing':
                agent_confidences[agent_id] = 79.0
            elif agent_id == 'tech_debt_analysis':
                agent_confidences[agent_id] = 73.0
            else:
                agent_confidences[agent_id] = 70.0
        
        # Calculate overall confidence for the page
        overall_confidence = self.aggregate_flow_confidence(agent_confidences)
        
        # Determine what needs attention
        needs_attention = []
        for agent_id, confidence in agent_confidences.items():
            if confidence < self.escalation_thresholds['medium']:
                needs_attention.append({
                    'agent': agent_id,
                    'confidence': confidence,
                    'reason': f'Confidence below medium threshold ({self.escalation_thresholds["medium"]}%)'
                })
        
        return {
            'page': page,
            'relevant_agents': relevant_agents,
            'agent_confidences': agent_confidences,
            'overall': overall_confidence['overall_confidence'],
            'confidence_level': overall_confidence['confidence_level'],
            'needs_attention': needs_attention,
            'escalation_recommended': overall_confidence['escalation_recommended'],
            'page_specific_insights': self._get_page_specific_insights(page, agent_confidences)
        }
    
    def _get_page_specific_insights(self, page: str, agent_confidences: Dict[str, float]) -> List[Dict[str, Any]]:
        """Get page-specific confidence insights"""
        insights = []
        
        if page == 'dependencies':
            dep_confidence = agent_confidences.get('dependency_analysis', 0)
            if dep_confidence < 80:
                insights.append({
                    'type': 'warning',
                    'message': 'Dependency analysis confidence is below optimal level',
                    'recommendation': 'Consider manual review of critical dependencies'
                })
            
            asset_confidence = agent_confidences.get('asset_inventory', 0)
            if asset_confidence > 85:
                insights.append({
                    'type': 'success',
                    'message': 'Asset inventory has high confidence',
                    'recommendation': 'Dependency mappings should be reliable'
                })
        
        elif page == 'attribute-mapping':
            mapping_confidence = agent_confidences.get('attribute_mapping', 0)
            if mapping_confidence > 85:
                insights.append({
                    'type': 'success',
                    'message': 'Field mappings have high confidence',
                    'recommendation': 'Proceed with data cleansing phase'
                })
            elif mapping_confidence < 70:
                insights.append({
                    'type': 'error',
                    'message': 'Field mapping confidence is low',
                    'recommendation': 'Review and correct field mappings before proceeding'
                })
        
        return insights 