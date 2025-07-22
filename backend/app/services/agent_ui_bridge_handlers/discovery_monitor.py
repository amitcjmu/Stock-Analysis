"""
Discovery Flow Monitor for Agent-UI Bridge
Monitors the enhanced discovery flow and field mappings for agent insights.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class DiscoveryFlowMonitor:
    """Monitors the enhanced discovery flow for agent communication opportunities."""
    
    def __init__(self, agent_ui_bridge):
        self.agent_ui_bridge = agent_ui_bridge
        self.monitored_endpoints = {
            '/data-import/simple-field-mappings',
            '/data-import/agentic-critical-attributes', 
            '/data-import/agent-clarifications',
            '/data-import/latest-import'
        }
        
    def monitor_field_mappings_request(self, request_data: Dict[str, Any], response_data: Dict[str, Any]) -> None:
        """Monitor field mappings requests for agent insights."""
        try:
            if not response_data.get('success'):
                return
                
            mappings = response_data.get('mappings', [])
            
            # Check for low confidence mappings that need human attention
            low_confidence_mappings = [
                m for m in mappings 
                if m.get('confidence', 0) < 0.75 and m.get('status') == 'pending'
            ]
            
            if low_confidence_mappings:
                # Create agent questions for low confidence mappings
                for mapping in low_confidence_mappings[:2]:  # Limit to 2 questions
                    question_id = self.agent_ui_bridge.add_agent_question(
                        agent_id="field_mapping_specialist",
                        agent_name="Field Mapping Specialist",
                        question_type="field_mapping_verification",
                        page="attribute-mapping",
                        title=f"Verify mapping: {mapping['sourceField']}",
                        question=f"Should '{mapping['sourceField']}' be mapped to '{mapping['targetAttribute']}'?",
                        context={
                            "source_field": mapping['sourceField'],
                            "target_attribute": mapping['targetAttribute'],
                            "confidence": mapping.get('confidence', 0),
                            "ai_reasoning": mapping.get('reasoning', ''),
                            "category": mapping.get('category', 'unknown')
                        },
                        options=[
                            f"Yes, map {mapping['sourceField']} → {mapping['targetAttribute']}",
                            "No, suggest different mapping",
                            "Skip this field",
                            "Need more context"
                        ],
                        confidence="medium",
                        priority="normal"
                    )
                    
                    logger.info(f"Created field mapping question {question_id} for {mapping['sourceField']}")
            
            # Add insight about overall mapping quality
            total_mappings = len(mappings)
            high_confidence = len([m for m in mappings if m.get('confidence', 0) >= 0.85])
            
            if total_mappings > 0:
                confidence_ratio = high_confidence / total_mappings
                
                insight_id = self.agent_ui_bridge.add_agent_insight(
                    agent_id="field_mapping_analyst",
                    agent_name="Field Mapping Analyst", 
                    insight_type="field_mapping_quality",
                    title="Field Mapping Quality Assessment",
                    description=f"Analyzed {total_mappings} field mappings with {high_confidence} high-confidence matches ({confidence_ratio:.1%} accuracy). " +
                               (f"{len(low_confidence_mappings)} mappings need human review." if low_confidence_mappings else "All mappings have high confidence."),
                    confidence="high" if confidence_ratio > 0.8 else "medium",
                    supporting_data={
                        "total_mappings": total_mappings,
                        "high_confidence_count": high_confidence,
                        "confidence_ratio": confidence_ratio,
                        "low_confidence_fields": [m['sourceField'] for m in low_confidence_mappings]
                    },
                    page="attribute-mapping",
                    actionable=len(low_confidence_mappings) > 0
                )
                
                logger.info(f"Added field mapping quality insight {insight_id}")
                
        except Exception as e:
            logger.error(f"Error monitoring field mappings request: {e}")
    
    def monitor_discovery_request(self, endpoint: str, request_data: Dict[str, Any], response_data: Dict[str, Any]) -> None:
        """Main monitoring method for discovery flow requests."""
        try:
            if endpoint not in self.monitored_endpoints:
                return
                
            # Route to specific monitors based on endpoint
            if 'simple-field-mappings' in endpoint:
                self.monitor_field_mappings_request(request_data, response_data)
                
        except Exception as e:
            logger.error(f"Error monitoring discovery request {endpoint}: {e}")


# Global instance for easy import
discovery_flow_monitor = None

def get_discovery_monitor(agent_ui_bridge=None):
    """Get or create the discovery flow monitor."""
    global discovery_flow_monitor
    
    if discovery_flow_monitor is None and agent_ui_bridge:
        discovery_flow_monitor = DiscoveryFlowMonitor(agent_ui_bridge)
        
    return discovery_flow_monitor