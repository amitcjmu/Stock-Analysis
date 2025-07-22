"""
Collaboration Monitoring Service
Tracks and analyzes agent collaboration activities within and across crews
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class CollaborationType(Enum):
    """Types of agent collaboration"""
    INTRA_CREW = "intra_crew"           # Collaboration within same crew
    INTER_CREW = "inter_crew"           # Collaboration across different crews
    MEMORY_SHARING = "memory_sharing"   # Shared memory access and updates
    KNOWLEDGE_SHARING = "knowledge_sharing"  # Knowledge base utilization
    PLANNING_COORDINATION = "planning_coordination"  # Joint planning activities

class CollaborationStatus(Enum):
    """Status of collaboration activities"""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

@dataclass
class CollaborationEvent:
    """Individual collaboration event tracking"""
    event_id: str
    timestamp: datetime
    collaboration_type: CollaborationType
    status: CollaborationStatus
    participants: List[str]  # Agent names or IDs
    crews_involved: List[str]  # Crew names
    context: Dict[str, Any]  # Collaboration context
    duration_seconds: Optional[float] = None
    success_metrics: Dict[str, Any] = field(default_factory=dict)
    error_details: Optional[str] = None

@dataclass
class AgentCollaborationMetrics:
    """Metrics for individual agent collaboration"""
    agent_name: str
    crew_name: str
    total_collaborations: int = 0
    successful_collaborations: int = 0
    failed_collaborations: int = 0
    average_collaboration_duration: float = 0.0
    collaboration_types: Dict[str, int] = field(default_factory=dict)
    partners: List[str] = field(default_factory=list)
    effectiveness_score: float = 0.0

@dataclass
class CrewCollaborationMetrics:
    """Metrics for crew-level collaboration"""
    crew_name: str
    internal_collaborations: int = 0
    external_collaborations: int = 0
    memory_sharing_events: int = 0
    knowledge_utilization_events: int = 0
    cross_crew_insights_shared: int = 0
    collaboration_effectiveness: float = 0.0
    top_collaboration_partners: List[str] = field(default_factory=list)

class CollaborationMonitor:
    """
    Monitors and analyzes agent collaboration across the Discovery Flow
    Provides real-time tracking and effectiveness metrics for Task 31
    """
    
    def __init__(self, flow_instance=None):
        self.flow_instance = flow_instance
        self.logger = logger
        
        # Collaboration tracking storage
        self.collaboration_events: List[CollaborationEvent] = []
        self.agent_metrics: Dict[str, AgentCollaborationMetrics] = {}
        self.crew_metrics: Dict[str, CrewCollaborationMetrics] = {}
        
        # Active collaboration tracking
        self.active_collaborations: Dict[str, CollaborationEvent] = {}
        
        # Configuration
        self.monitoring_config = {
            "real_time_tracking": True,
            "effectiveness_calculation": True,
            "cross_crew_analysis": True,
            "memory_access_tracking": True,
            "knowledge_utilization_tracking": True,
            "collaboration_timeout_seconds": 300  # 5 minutes
        }
        
        # Initialize crew names from Discovery Flow
        self.crew_names = [
            "field_mapping", "data_cleansing", "inventory_building",
            "app_server_dependencies", "app_app_dependencies", "technical_debt"
        ]
        
        # Initialize metrics for all crews
        for crew_name in self.crew_names:
            self.crew_metrics[crew_name] = CrewCollaborationMetrics(crew_name=crew_name)
        
        logger.info("✅ Collaboration Monitor initialized for Task 31")
    
    def start_collaboration_event(self, 
                                collaboration_type: CollaborationType,
                                participants: List[str],
                                crews_involved: List[str],
                                context: Dict[str, Any] = None) -> str:
        """Start tracking a collaboration event"""
        
        event_id = self._generate_event_id()
        
        collaboration_event = CollaborationEvent(
            event_id=event_id,
            timestamp=datetime.utcnow(),
            collaboration_type=collaboration_type,
            status=CollaborationStatus.INITIATED,
            participants=participants,
            crews_involved=crews_involved,
            context=context or {}
        )
        
        # Store active collaboration
        self.active_collaborations[event_id] = collaboration_event
        
        # Log collaboration start
        self.logger.info(
            f"🤝 Collaboration started: {collaboration_type.value} - "
            f"Participants: {participants} - Crews: {crews_involved}"
        )
        
        return event_id
    
    def update_collaboration_status(self, 
                                  event_id: str, 
                                  status: CollaborationStatus,
                                  success_metrics: Dict[str, Any] = None,
                                  error_details: str = None):
        """Update collaboration event status"""
        
        if event_id not in self.active_collaborations:
            self.logger.warning(f"Collaboration event not found: {event_id}")
            return
        
        collaboration = self.active_collaborations[event_id]
        collaboration.status = status
        
        if success_metrics:
            collaboration.success_metrics.update(success_metrics)
        
        if error_details:
            collaboration.error_details = error_details
        
        # Calculate duration if completed or failed
        if status in [CollaborationStatus.COMPLETED, CollaborationStatus.FAILED, CollaborationStatus.TIMEOUT]:
            duration = (datetime.utcnow() - collaboration.timestamp).total_seconds()
            collaboration.duration_seconds = duration
            
            # Move to completed events
            self.collaboration_events.append(collaboration)
            del self.active_collaborations[event_id]
            
            # Update metrics
            self._update_collaboration_metrics(collaboration)
        
        self.logger.info(f"🔄 Collaboration updated: {event_id} - Status: {status.value}")
    
    def track_memory_sharing_event(self, 
                                 sharing_agent: str,
                                 receiving_agents: List[str],
                                 memory_category: str,
                                 data_size: int = 0,
                                 success: bool = True):
        """Track memory sharing events between agents"""
        
        event_id = self.start_collaboration_event(
            collaboration_type=CollaborationType.MEMORY_SHARING,
            participants=[sharing_agent] + receiving_agents,
            crews_involved=self._determine_crews_for_agents([sharing_agent] + receiving_agents),
            context={
                "memory_category": memory_category,
                "data_size": data_size,
                "sharing_direction": f"{sharing_agent} -> {receiving_agents}"
            }
        )
        
        # Immediately complete the event
        status = CollaborationStatus.COMPLETED if success else CollaborationStatus.FAILED
        self.update_collaboration_status(
            event_id=event_id,
            status=status,
            success_metrics={
                "memory_shared": success,
                "data_size": data_size,
                "recipients_count": len(receiving_agents)
            }
        )
        
        # Update crew metrics
        for crew_name in self._determine_crews_for_agents([sharing_agent] + receiving_agents):
            if crew_name in self.crew_metrics:
                self.crew_metrics[crew_name].memory_sharing_events += 1
    
    def track_knowledge_utilization_event(self,
                                        agent: str,
                                        knowledge_base: str,
                                        utilization_type: str,
                                        effectiveness_score: float = 0.0):
        """Track knowledge base utilization by agents"""
        
        event_id = self.start_collaboration_event(
            collaboration_type=CollaborationType.KNOWLEDGE_SHARING,
            participants=[agent],
            crews_involved=self._determine_crews_for_agents([agent]),
            context={
                "knowledge_base": knowledge_base,
                "utilization_type": utilization_type,
                "effectiveness_score": effectiveness_score
            }
        )
        
        # Complete immediately
        self.update_collaboration_status(
            event_id=event_id,
            status=CollaborationStatus.COMPLETED,
            success_metrics={
                "knowledge_utilized": True,
                "effectiveness_score": effectiveness_score,
                "knowledge_base": knowledge_base
            }
        )
        
        # Update crew metrics
        crew_name = self._determine_crews_for_agents([agent])[0] if self._determine_crews_for_agents([agent]) else "unknown"
        if crew_name in self.crew_metrics:
            self.crew_metrics[crew_name].knowledge_utilization_events += 1
    
    def track_cross_crew_insight_sharing(self,
                                       source_crew: str,
                                       target_crews: List[str],
                                       insight_category: str,
                                       insight_confidence: float = 0.0):
        """Track insights shared across crews"""
        
        event_id = self.start_collaboration_event(
            collaboration_type=CollaborationType.INTER_CREW,
            participants=[f"{source_crew}_insight_agent"],
            crews_involved=[source_crew] + target_crews,
            context={
                "insight_category": insight_category,
                "insight_confidence": insight_confidence,
                "sharing_direction": f"{source_crew} -> {target_crews}"
            }
        )
        
        # Complete immediately
        self.update_collaboration_status(
            event_id=event_id,
            status=CollaborationStatus.COMPLETED,
            success_metrics={
                "insights_shared": True,
                "target_crews_count": len(target_crews),
                "insight_confidence": insight_confidence
            }
        )
        
        # Update source crew metrics
        if source_crew in self.crew_metrics:
            self.crew_metrics[source_crew].cross_crew_insights_shared += 1
            self.crew_metrics[source_crew].external_collaborations += len(target_crews)
    
    def get_real_time_collaboration_status(self) -> Dict[str, Any]:
        """Get current collaboration status for real-time monitoring"""
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "active_collaborations": len(self.active_collaborations),
            "active_events": [
                {
                    "event_id": event.event_id,
                    "type": event.collaboration_type.value,
                    "participants": event.participants,
                    "crews": event.crews_involved,
                    "duration_seconds": (datetime.utcnow() - event.timestamp).total_seconds(),
                    "status": event.status.value
                }
                for event in self.active_collaborations.values()
            ],
            "recent_completed_events": self._get_recent_completed_events(limit=10),
            "collaboration_summary": self._get_collaboration_summary()
        }
    
    def get_agent_collaboration_analytics(self, agent_name: str = None) -> Dict[str, Any]:
        """Get collaboration analytics for specific agent or all agents"""
        
        if agent_name:
            metrics = self.agent_metrics.get(agent_name)
            if not metrics:
                return {"agent": agent_name, "found": False}
            
            return {
                "agent": agent_name,
                "found": True,
                "metrics": {
                    "total_collaborations": metrics.total_collaborations,
                    "success_rate": metrics.successful_collaborations / max(metrics.total_collaborations, 1),
                    "average_duration": metrics.average_collaboration_duration,
                    "collaboration_types": metrics.collaboration_types,
                    "frequent_partners": metrics.partners[:5],
                    "effectiveness_score": metrics.effectiveness_score
                }
            }
        else:
            # Return analytics for all agents
            return {
                "all_agents": True,
                "total_agents": len(self.agent_metrics),
                "agent_summaries": [
                    {
                        "agent": name,
                        "total_collaborations": metrics.total_collaborations,
                        "success_rate": metrics.successful_collaborations / max(metrics.total_collaborations, 1),
                        "effectiveness_score": metrics.effectiveness_score
                    }
                    for name, metrics in self.agent_metrics.items()
                ]
            }
    
    def get_crew_collaboration_analytics(self, crew_name: str = None) -> Dict[str, Any]:
        """Get collaboration analytics for specific crew or all crews"""
        
        if crew_name:
            metrics = self.crew_metrics.get(crew_name)
            if not metrics:
                return {"crew": crew_name, "found": False}
            
            return {
                "crew": crew_name,
                "found": True,
                "metrics": {
                    "internal_collaborations": metrics.internal_collaborations,
                    "external_collaborations": metrics.external_collaborations,
                    "memory_sharing_events": metrics.memory_sharing_events,
                    "knowledge_utilization_events": metrics.knowledge_utilization_events,
                    "cross_crew_insights_shared": metrics.cross_crew_insights_shared,
                    "collaboration_effectiveness": metrics.collaboration_effectiveness,
                    "top_partners": metrics.top_collaboration_partners
                }
            }
        else:
            # Return analytics for all crews
            return {
                "all_crews": True,
                "total_crews": len(self.crew_metrics),
                "crew_summaries": [
                    {
                        "crew": name,
                        "total_events": metrics.internal_collaborations + metrics.external_collaborations,
                        "memory_sharing": metrics.memory_sharing_events,
                        "knowledge_utilization": metrics.knowledge_utilization_events,
                        "effectiveness": metrics.collaboration_effectiveness
                    }
                    for name, metrics in self.crew_metrics.items()
                ]
            }
    
    def get_collaboration_effectiveness_report(self) -> Dict[str, Any]:
        """Generate comprehensive collaboration effectiveness report"""
        
        total_events = len(self.collaboration_events)
        if total_events == 0:
            return {"report": "no_data", "total_events": 0}
        
        # Calculate overall effectiveness metrics
        successful_events = len([e for e in self.collaboration_events 
                               if e.status == CollaborationStatus.COMPLETED])
        
        failed_events = len([e for e in self.collaboration_events 
                           if e.status == CollaborationStatus.FAILED])
        
        average_duration = sum([e.duration_seconds for e in self.collaboration_events 
                              if e.duration_seconds]) / max(total_events, 1)
        
        # Collaboration type breakdown
        type_breakdown = {}
        for event in self.collaboration_events:
            event_type = event.collaboration_type.value
            if event_type not in type_breakdown:
                type_breakdown[event_type] = {"total": 0, "successful": 0}
            type_breakdown[event_type]["total"] += 1
            if event.status == CollaborationStatus.COMPLETED:
                type_breakdown[event_type]["successful"] += 1
        
        # Cross-crew collaboration analysis
        cross_crew_events = [e for e in self.collaboration_events 
                           if len(e.crews_involved) > 1]
        
        return {
            "report": "generated",
            "timestamp": datetime.utcnow().isoformat(),
            "overall_metrics": {
                "total_events": total_events,
                "successful_events": successful_events,
                "failed_events": failed_events,
                "success_rate": successful_events / total_events,
                "average_duration_seconds": average_duration
            },
            "collaboration_types": type_breakdown,
            "cross_crew_analysis": {
                "total_cross_crew_events": len(cross_crew_events),
                "cross_crew_success_rate": len([e for e in cross_crew_events 
                                              if e.status == CollaborationStatus.COMPLETED]) / max(len(cross_crew_events), 1)
            },
            "top_performing_agents": self._get_top_performing_agents(limit=5),
            "most_collaborative_crews": self._get_most_collaborative_crews(limit=3),
            "recommendations": self._generate_collaboration_recommendations()
        }
    
    # Private helper methods
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        return f"collab_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{len(self.collaboration_events)}"
    
    def _determine_crews_for_agents(self, agents: List[str]) -> List[str]:
        """Determine which crews the agents belong to"""
        # Simplified mapping - in real implementation, this would query agent-crew relationships
        crew_mapping = {
            "Field Mapping Manager": "field_mapping",
            "Schema Analysis Expert": "field_mapping",
            "Attribute Mapping Specialist": "field_mapping",
            "Data Quality Manager": "data_cleansing",
            "Data Validation Expert": "data_cleansing",
            "Data Standardization Specialist": "data_cleansing",
            "Inventory Manager": "inventory_building",
            "Server Classification Expert": "inventory_building",
            "Application Discovery Expert": "inventory_building",
            "Device Classification Expert": "inventory_building",
            "Dependency Manager": "app_server_dependencies",
            "Hosting Relationship Expert": "app_server_dependencies",
            "Migration Impact Analyst": "app_server_dependencies",
            "Integration Manager": "app_app_dependencies",
            "Integration Pattern Expert": "app_app_dependencies",
            "Business Flow Analyst": "app_app_dependencies",
            "Technical Debt Manager": "technical_debt",
            "Legacy Systems Analyst": "technical_debt",
            "Modernization Expert": "technical_debt",
            "Risk Assessment Specialist": "technical_debt"
        }
        
        return list(set([crew_mapping.get(agent, "unknown") for agent in agents]))
    
    def _update_collaboration_metrics(self, collaboration: CollaborationEvent):
        """Update metrics based on completed collaboration event"""
        
        # Update agent metrics
        for participant in collaboration.participants:
            if participant not in self.agent_metrics:
                crew_name = self._determine_crews_for_agents([participant])[0] if self._determine_crews_for_agents([participant]) else "unknown"
                self.agent_metrics[participant] = AgentCollaborationMetrics(
                    agent_name=participant,
                    crew_name=crew_name
                )
            
            agent_metrics = self.agent_metrics[participant]
            agent_metrics.total_collaborations += 1
            
            if collaboration.status == CollaborationStatus.COMPLETED:
                agent_metrics.successful_collaborations += 1
            elif collaboration.status == CollaborationStatus.FAILED:
                agent_metrics.failed_collaborations += 1
            
            # Update collaboration type tracking
            collab_type = collaboration.collaboration_type.value
            if collab_type not in agent_metrics.collaboration_types:
                agent_metrics.collaboration_types[collab_type] = 0
            agent_metrics.collaboration_types[collab_type] += 1
            
            # Update duration
            if collaboration.duration_seconds:
                total_duration = agent_metrics.average_collaboration_duration * (agent_metrics.total_collaborations - 1)
                agent_metrics.average_collaboration_duration = (total_duration + collaboration.duration_seconds) / agent_metrics.total_collaborations
            
            # Update effectiveness score
            agent_metrics.effectiveness_score = agent_metrics.successful_collaborations / max(agent_metrics.total_collaborations, 1)
        
        # Update crew metrics
        for crew_name in collaboration.crews_involved:
            if crew_name in self.crew_metrics:
                crew_metrics = self.crew_metrics[crew_name]
                
                if len(collaboration.crews_involved) == 1:
                    crew_metrics.internal_collaborations += 1
                else:
                    crew_metrics.external_collaborations += 1
                
                # Update effectiveness
                total_events = crew_metrics.internal_collaborations + crew_metrics.external_collaborations
                if collaboration.status == CollaborationStatus.COMPLETED:
                    crew_metrics.collaboration_effectiveness = (crew_metrics.collaboration_effectiveness * (total_events - 1) + 1.0) / total_events
                else:
                    crew_metrics.collaboration_effectiveness = (crew_metrics.collaboration_effectiveness * (total_events - 1) + 0.0) / total_events
    
    def _get_recent_completed_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent completed collaboration events"""
        recent_events = sorted(self.collaboration_events, key=lambda x: x.timestamp, reverse=True)[:limit]
        
        return [
            {
                "event_id": event.event_id,
                "type": event.collaboration_type.value,
                "status": event.status.value,
                "participants": event.participants,
                "crews": event.crews_involved,
                "duration_seconds": event.duration_seconds,
                "timestamp": event.timestamp.isoformat()
            }
            for event in recent_events
        ]
    
    def _get_collaboration_summary(self) -> Dict[str, Any]:
        """Get summary of all collaboration activity"""
        return {
            "total_events": len(self.collaboration_events),
            "active_events": len(self.active_collaborations),
            "success_rate": len([e for e in self.collaboration_events if e.status == CollaborationStatus.COMPLETED]) / max(len(self.collaboration_events), 1),
            "collaboration_types": len(set([e.collaboration_type.value for e in self.collaboration_events])),
            "participating_agents": len(self.agent_metrics),
            "active_crews": len([c for c in self.crew_metrics.values() if c.internal_collaborations + c.external_collaborations > 0])
        }
    
    def _get_top_performing_agents(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top performing agents by effectiveness score"""
        sorted_agents = sorted(self.agent_metrics.values(), key=lambda x: x.effectiveness_score, reverse=True)[:limit]
        
        return [
            {
                "agent": agent.agent_name,
                "crew": agent.crew_name,
                "effectiveness_score": agent.effectiveness_score,
                "total_collaborations": agent.total_collaborations
            }
            for agent in sorted_agents
        ]
    
    def _get_most_collaborative_crews(self, limit: int = 3) -> List[Dict[str, Any]]:
        """Get most collaborative crews"""
        sorted_crews = sorted(self.crew_metrics.values(), 
                            key=lambda x: x.internal_collaborations + x.external_collaborations, 
                            reverse=True)[:limit]
        
        return [
            {
                "crew": crew.crew_name,
                "total_collaborations": crew.internal_collaborations + crew.external_collaborations,
                "effectiveness": crew.collaboration_effectiveness,
                "memory_sharing": crew.memory_sharing_events
            }
            for crew in sorted_crews
        ]
    
    def _generate_collaboration_recommendations(self) -> List[str]:
        """Generate recommendations for improving collaboration"""
        recommendations = []
        
        # Analyze success rates
        if len(self.collaboration_events) > 0:
            success_rate = len([e for e in self.collaboration_events if e.status == CollaborationStatus.COMPLETED]) / len(self.collaboration_events)
            
            if success_rate < 0.8:
                recommendations.append("Consider improving agent coordination mechanisms to increase collaboration success rate")
            
            # Analyze cross-crew collaboration
            cross_crew_events = [e for e in self.collaboration_events if len(e.crews_involved) > 1]
            if len(cross_crew_events) < len(self.collaboration_events) * 0.3:
                recommendations.append("Increase cross-crew collaboration to improve knowledge sharing")
            
            # Analyze memory sharing
            memory_events = [e for e in self.collaboration_events if e.collaboration_type == CollaborationType.MEMORY_SHARING]
            if len(memory_events) < len(self.collaboration_events) * 0.2:
                recommendations.append("Enhance memory sharing mechanisms between agents")
        
        if not recommendations:
            recommendations.append("Collaboration patterns are performing well - continue monitoring")
        
        return recommendations 