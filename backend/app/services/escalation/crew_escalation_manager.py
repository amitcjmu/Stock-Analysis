"""
Crew Escalation Manager
Manages crew escalations for Think/Ponder More button functionality.
Implements Task 2.3 of the Discovery Flow Redesign.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)

class CrewEscalationManager:
    """
    Manages crew escalations for Think/Ponder More functionality.
    
    Handles:
    - Crew selection based on page/agent context
    - Background crew execution
    - Progress tracking and status updates
    - Results integration back to discovery flow
    """
    
    def __init__(self):
        self.active_escalations: Dict[str, Dict[str, Any]] = {}
        self.crew_mappings = {
            # Page -> Agent -> Crew mappings
            "field_mapping": {
                "attribute_mapping_agent": "field_mapping_crew",
                "data_validation_agent": "data_quality_crew"
            },
            "asset_inventory": {
                "asset_inventory_agent": "asset_intelligence_crew",
                "data_cleansing_agent": "data_quality_crew"
            },
            "dependencies": {
                "dependency_analysis_agent": "dependency_analysis_crew",
                "asset_inventory_agent": "asset_intelligence_crew"
            },
            "tech_debt": {
                "tech_debt_analysis_agent": "tech_debt_analysis_crew",
                "dependency_analysis_agent": "dependency_analysis_crew"
            }
        }
        
        # Collaboration strategies for Ponder More
        self.collaboration_strategies = {
            "cross_agent": {
                "pattern": "parallel_synthesis",
                "description": "Multiple agents collaborate in parallel then synthesize results"
            },
            "expert_panel": {
                "pattern": "sequential_expert_review",
                "description": "Sequential expert review with escalating complexity"
            },
            "full_crew": {
                "pattern": "full_crew_collaboration",
                "description": "Complete crew collaboration with debate and consensus"
            }
        }
        
        logger.info("🚀 Crew Escalation Manager initialized")
    
    def determine_crew_for_page_agent(self, page: str, agent_id: str) -> str:
        """Determine appropriate crew based on page and agent context."""
        page_mappings = self.crew_mappings.get(page, {})
        crew_type = page_mappings.get(agent_id)
        
        if not crew_type:
            # Default crew selection based on page
            default_crews = {
                "field_mapping": "field_mapping_crew",
                "asset_inventory": "asset_intelligence_crew", 
                "dependencies": "dependency_analysis_crew",
                "tech_debt": "tech_debt_analysis_crew"
            }
            crew_type = default_crews.get(page, "general_analysis_crew")
        
        logger.info(f"🎯 Selected crew '{crew_type}' for page '{page}' and agent '{agent_id}'")
        return crew_type
    
    def determine_collaboration_strategy(self, page: str, agent_id: str, 
                                       collaboration_type: str) -> Dict[str, Any]:
        """Determine collaboration strategy for Ponder More functionality."""
        base_strategy = self.collaboration_strategies.get(
            collaboration_type, 
            self.collaboration_strategies["cross_agent"]
        )
        
        # Determine primary crew
        primary_crew = self.determine_crew_for_page_agent(page, agent_id)
        
        # Determine additional crews based on collaboration type
        additional_crews = []
        if collaboration_type == "expert_panel":
            # Add complementary crews for expert panel
            if page == "dependencies":
                additional_crews = ["asset_intelligence_crew", "tech_debt_analysis_crew"]
            elif page == "asset_inventory":
                additional_crews = ["dependency_analysis_crew", "field_mapping_crew"]
            elif page == "tech_debt":
                additional_crews = ["dependency_analysis_crew", "asset_intelligence_crew"]
        elif collaboration_type == "full_crew":
            # Add all relevant crews for full collaboration
            additional_crews = ["asset_intelligence_crew", "dependency_analysis_crew", 
                              "tech_debt_analysis_crew", "field_mapping_crew"]
            additional_crews = [c for c in additional_crews if c != primary_crew]
        
        strategy = {
            "primary_crew": primary_crew,
            "additional_crews": additional_crews,
            "pattern": base_strategy["pattern"],
            "description": base_strategy["description"],
            "collaboration_type": collaboration_type,
            "expected_outcomes": self._get_expected_outcomes(page, collaboration_type)
        }
        
        logger.info(f"🤝 Collaboration strategy: {strategy['pattern']} with {len(additional_crews)} additional crews")
        return strategy
    
    def _get_expected_outcomes(self, page: str, collaboration_type: str) -> List[str]:
        """Get expected outcomes based on page and collaboration type."""
        base_outcomes = {
            "field_mapping": [
                "Enhanced field mapping accuracy",
                "Identification of complex mapping patterns",
                "Data quality improvement recommendations"
            ],
            "asset_inventory": [
                "Comprehensive asset classification",
                "Business criticality assessment", 
                "Environment and dependency insights"
            ],
            "dependencies": [
                "Complete dependency mapping",
                "Critical path identification",
                "Migration risk assessment"
            ],
            "tech_debt": [
                "Modernization strategy recommendations",
                "6R strategy optimization",
                "Technical debt prioritization"
            ]
        }
        
        outcomes = base_outcomes.get(page, ["Enhanced analysis results"])
        
        # Add collaboration-specific outcomes
        if collaboration_type == "expert_panel":
            outcomes.append("Expert validation and refinement")
        elif collaboration_type == "full_crew":
            outcomes.extend([
                "Cross-domain insights",
                "Comprehensive risk analysis",
                "Holistic migration recommendations"
            ])
        
        return outcomes
    
    async def start_crew_escalation(self, crew_type: str, escalation_context: Dict[str, Any],
                                  background_tasks: BackgroundTasks) -> str:
        """Start a crew escalation for Think button functionality."""
        escalation_id = str(uuid.uuid4())
        
        # Initialize escalation tracking
        escalation_record = {
            "escalation_id": escalation_id,
            "crew_type": crew_type,
            "escalation_type": "think",
            "status": "initializing",
            "progress": 0,
            "current_phase": "crew_initialization",
            "context": escalation_context,
            "started_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "crew_activity": [],
            "preliminary_insights": [],
            "estimated_completion": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
        }
        
        self.active_escalations[escalation_id] = escalation_record
        
        # Start crew execution in background
        background_tasks.add_task(
            self._execute_crew_thinking,
            escalation_id,
            crew_type,
            escalation_context
        )
        
        logger.info(f"🚀 Started crew escalation {escalation_id} with {crew_type}")
        return escalation_id
    
    async def start_extended_collaboration(self, collaboration_strategy: Dict[str, Any],
                                         collaboration_context: Dict[str, Any],
                                         background_tasks: BackgroundTasks) -> str:
        """Start extended crew collaboration for Ponder More functionality."""
        escalation_id = str(uuid.uuid4())
        
        # Initialize collaboration tracking
        collaboration_record = {
            "escalation_id": escalation_id,
            "collaboration_strategy": collaboration_strategy,
            "escalation_type": "ponder_more",
            "status": "initializing",
            "progress": 0,
            "current_phase": "collaboration_setup",
            "context": collaboration_context,
            "started_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "crew_activity": [],
            "preliminary_insights": [],
            "collaboration_details": {
                "active_crews": [collaboration_strategy["primary_crew"]] + collaboration_strategy.get("additional_crews", []),
                "collaboration_pattern": collaboration_strategy["pattern"],
                "phase_progress": {}
            },
            "estimated_completion": (datetime.utcnow() + timedelta(minutes=10)).isoformat()
        }
        
        self.active_escalations[escalation_id] = collaboration_record
        
        # Start collaboration in background
        background_tasks.add_task(
            self._execute_crew_collaboration,
            escalation_id,
            collaboration_strategy,
            collaboration_context
        )
        
        logger.info(f"🤝 Started crew collaboration {escalation_id} with strategy {collaboration_strategy['pattern']}")
        return escalation_id
    
    async def _execute_crew_thinking(self, escalation_id: str, crew_type: str, 
                                   context: Dict[str, Any]) -> None:
        """Execute crew thinking process in background."""
        try:
            escalation = self.active_escalations[escalation_id]
            
            # Phase 1: Crew Initialization
            await self._update_escalation_progress(escalation_id, 10, "crew_initialization", 
                                                 "Initializing crew for deeper analysis")
            await asyncio.sleep(2)  # Simulate crew setup
            
            # Phase 2: Data Analysis
            await self._update_escalation_progress(escalation_id, 30, "data_analysis",
                                                 f"Crew analyzing {context.get('page', 'data')} with enhanced intelligence")
            
            # Add crew activity
            escalation["crew_activity"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "activity": f"{crew_type} initiated deeper analysis",
                "phase": "data_analysis"
            })
            
            await asyncio.sleep(3)  # Simulate analysis
            
            # Phase 3: Pattern Recognition
            await self._update_escalation_progress(escalation_id, 60, "pattern_recognition",
                                                 "Identifying complex patterns and relationships")
            
            # Generate preliminary insights
            preliminary_insights = self._generate_preliminary_insights(crew_type, context)
            escalation["preliminary_insights"] = preliminary_insights
            
            await asyncio.sleep(2)
            
            # Phase 4: Results Generation
            await self._update_escalation_progress(escalation_id, 90, "results_generation",
                                                 "Generating enhanced insights and recommendations")
            
            await asyncio.sleep(2)
            
            # Phase 5: Completion
            results = await self._generate_crew_results(crew_type, context, preliminary_insights)
            
            escalation["status"] = "completed"
            escalation["progress"] = 100
            escalation["current_phase"] = "completed"
            escalation["results"] = results
            escalation["completed_at"] = datetime.utcnow().isoformat()
            escalation["updated_at"] = datetime.utcnow().isoformat()
            
            escalation["crew_activity"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "activity": f"{crew_type} completed enhanced analysis",
                "phase": "completed"
            })
            
            logger.info(f"✅ Crew thinking completed for escalation {escalation_id}")
            
        except Exception as e:
            logger.error(f"❌ Error in crew thinking {escalation_id}: {e}")
            await self._handle_escalation_error(escalation_id, str(e))
    
    async def _execute_crew_collaboration(self, escalation_id: str, 
                                        collaboration_strategy: Dict[str, Any],
                                        context: Dict[str, Any]) -> None:
        """Execute crew collaboration process in background."""
        try:
            escalation = self.active_escalations[escalation_id]
            primary_crew = collaboration_strategy["primary_crew"]
            additional_crews = collaboration_strategy.get("additional_crews", [])
            
            # Phase 1: Collaboration Setup
            await self._update_escalation_progress(escalation_id, 5, "collaboration_setup",
                                                 "Setting up multi-crew collaboration")
            await asyncio.sleep(1)
            
            # Phase 2: Primary Crew Analysis
            await self._update_escalation_progress(escalation_id, 20, "primary_analysis",
                                                 f"{primary_crew} conducting primary analysis")
            
            escalation["crew_activity"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "activity": f"{primary_crew} started primary analysis",
                "phase": "primary_analysis"
            })
            
            await asyncio.sleep(3)
            
            # Phase 3: Additional Crew Collaboration
            if additional_crews:
                for i, crew in enumerate(additional_crews):
                    progress = 20 + (40 * (i + 1) / len(additional_crews))
                    await self._update_escalation_progress(escalation_id, int(progress), "crew_collaboration",
                                                         f"{crew} contributing specialized insights")
                    
                    escalation["crew_activity"].append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "activity": f"{crew} added specialized analysis",
                        "phase": "crew_collaboration"
                    })
                    
                    await asyncio.sleep(2)
            
            # Phase 4: Synthesis and Consensus
            await self._update_escalation_progress(escalation_id, 80, "synthesis",
                                                 "Synthesizing insights from all crews")
            
            # Generate comprehensive insights
            comprehensive_insights = self._generate_collaborative_insights(
                collaboration_strategy, context, escalation["crew_activity"]
            )
            escalation["preliminary_insights"] = comprehensive_insights
            
            await asyncio.sleep(3)
            
            # Phase 5: Final Results
            await self._update_escalation_progress(escalation_id, 95, "final_results",
                                                 "Generating comprehensive recommendations")
            
            results = await self._generate_collaborative_results(
                collaboration_strategy, context, comprehensive_insights
            )
            
            escalation["status"] = "completed"
            escalation["progress"] = 100
            escalation["current_phase"] = "completed"
            escalation["results"] = results
            escalation["completed_at"] = datetime.utcnow().isoformat()
            escalation["updated_at"] = datetime.utcnow().isoformat()
            
            escalation["crew_activity"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "activity": "Multi-crew collaboration completed successfully",
                "phase": "completed"
            })
            
            logger.info(f"✅ Crew collaboration completed for escalation {escalation_id}")
            
        except Exception as e:
            logger.error(f"❌ Error in crew collaboration {escalation_id}: {e}")
            await self._handle_escalation_error(escalation_id, str(e))
    
    def _generate_preliminary_insights(self, crew_type: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate preliminary insights during crew thinking."""
        page = context.get("page", "unknown")
        
        base_insights = {
            "asset_intelligence_crew": [
                {"insight": "Identified high-value assets requiring special migration attention", "confidence": 0.85},
                {"insight": "Detected complex business dependencies not visible in initial analysis", "confidence": 0.78}
            ],
            "dependency_analysis_crew": [
                {"insight": "Discovered hidden network dependencies affecting migration sequence", "confidence": 0.82},
                {"insight": "Identified critical path bottlenecks that could delay migration", "confidence": 0.89}
            ],
            "tech_debt_analysis_crew": [
                {"insight": "Found modernization opportunities that could reduce migration complexity", "confidence": 0.87},
                {"insight": "Identified legacy components requiring refactoring before migration", "confidence": 0.83}
            ],
            "field_mapping_crew": [
                {"insight": "Detected data quality issues requiring pre-migration cleansing", "confidence": 0.81},
                {"insight": "Found complex field relationships not captured in initial mapping", "confidence": 0.86}
            ]
        }
        
        return base_insights.get(crew_type, [
            {"insight": f"Enhanced analysis of {page} data reveals additional complexity", "confidence": 0.80}
        ])
    
    def _generate_collaborative_insights(self, collaboration_strategy: Dict[str, Any],
                                       context: Dict[str, Any], 
                                       crew_activity: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate insights from multi-crew collaboration."""
        page = context.get("page", "unknown")
        pattern = collaboration_strategy["pattern"]
        
        collaborative_insights = [
            {
                "insight": f"Multi-crew analysis reveals {page} complexity requires coordinated approach",
                "confidence": 0.92,
                "source": "collaborative_synthesis"
            },
            {
                "insight": f"Cross-domain dependencies identified through {pattern} collaboration",
                "confidence": 0.88,
                "source": "cross_crew_analysis"
            },
            {
                "insight": "Holistic view reveals migration risks not visible to individual crews",
                "confidence": 0.85,
                "source": "comprehensive_review"
            }
        ]
        
        return collaborative_insights
    
    async def _generate_crew_results(self, crew_type: str, context: Dict[str, Any],
                                   preliminary_insights: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate final results from crew thinking."""
        return {
            "crew_type": crew_type,
            "analysis_type": "enhanced_thinking",
            "insights_generated": len(preliminary_insights),
            "recommendations": [
                f"Enhanced {crew_type} analysis recommends detailed review of flagged items",
                f"Consider additional validation for high-confidence insights",
                f"Implement recommended changes before proceeding with migration"
            ],
            "confidence_improvements": {
                "average_confidence_increase": 0.15,
                "high_confidence_items": len([i for i in preliminary_insights if i.get("confidence", 0) > 0.85]),
                "areas_needing_attention": [i["insight"] for i in preliminary_insights if i.get("confidence", 0) < 0.80]
            },
            "next_steps": [
                "Review and validate crew recommendations",
                "Implement suggested improvements",
                "Consider additional crew collaboration if needed"
            ]
        }
    
    async def _generate_collaborative_results(self, collaboration_strategy: Dict[str, Any],
                                            context: Dict[str, Any],
                                            comprehensive_insights: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate final results from crew collaboration."""
        return {
            "collaboration_strategy": collaboration_strategy["pattern"],
            "crews_involved": [collaboration_strategy["primary_crew"]] + collaboration_strategy.get("additional_crews", []),
            "analysis_type": "collaborative_pondering",
            "insights_generated": len(comprehensive_insights),
            "recommendations": [
                "Multi-crew collaboration reveals complex interdependencies requiring coordinated migration approach",
                "Implement cross-domain validation before proceeding",
                "Consider phased migration approach based on collaborative insights"
            ],
            "collaborative_benefits": {
                "cross_domain_insights": len([i for i in comprehensive_insights if i.get("source") == "cross_crew_analysis"]),
                "consensus_confidence": 0.90,
                "holistic_recommendations": True
            },
            "strategic_outcomes": collaboration_strategy.get("expected_outcomes", []),
            "next_steps": [
                "Validate collaborative recommendations with stakeholders",
                "Implement coordinated migration strategy",
                "Monitor cross-domain dependencies during execution"
            ]
        }
    
    async def _update_escalation_progress(self, escalation_id: str, progress: int, 
                                        phase: str, description: str) -> None:
        """Update escalation progress and status."""
        if escalation_id in self.active_escalations:
            escalation = self.active_escalations[escalation_id]
            escalation["progress"] = progress
            escalation["current_phase"] = phase
            escalation["phase_description"] = description
            escalation["updated_at"] = datetime.utcnow().isoformat()
            
            if progress > 0 and escalation["status"] == "initializing":
                escalation["status"] = "thinking" if escalation.get("escalation_type") == "think" else "pondering"
    
    async def _handle_escalation_error(self, escalation_id: str, error_message: str) -> None:
        """Handle escalation errors."""
        if escalation_id in self.active_escalations:
            escalation = self.active_escalations[escalation_id]
            escalation["status"] = "failed"
            escalation["error"] = error_message
            escalation["failed_at"] = datetime.utcnow().isoformat()
            escalation["updated_at"] = datetime.utcnow().isoformat()
    
    async def get_escalation_status(self, escalation_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific escalation."""
        return self.active_escalations.get(escalation_id)
    
    async def get_flow_escalations(self, flow_id: str) -> List[Dict[str, Any]]:
        """Get all escalations for a specific flow."""
        flow_escalations = []
        for escalation in self.active_escalations.values():
            if escalation.get("context", {}).get("flow_id") == flow_id:
                flow_escalations.append(escalation)
        
        # Sort by creation time
        flow_escalations.sort(key=lambda x: x.get("started_at", ""), reverse=True)
        return flow_escalations
    
    async def cancel_escalation(self, escalation_id: str) -> Dict[str, Any]:
        """Cancel an ongoing escalation."""
        if escalation_id not in self.active_escalations:
            return {"success": False, "error": "Escalation not found"}
        
        escalation = self.active_escalations[escalation_id]
        
        if escalation["status"] in ["completed", "failed", "cancelled"]:
            return {"success": False, "error": f"Cannot cancel escalation in {escalation['status']} state"}
        
        escalation["status"] = "cancelled"
        escalation["cancelled_at"] = datetime.utcnow().isoformat()
        escalation["updated_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"🚫 Cancelled escalation {escalation_id}")
        return {"success": True, "message": "Escalation cancelled successfully"}
    
    def cleanup_completed_escalations(self, max_age_hours: int = 24) -> int:
        """Clean up old completed escalations."""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        to_remove = []
        for escalation_id, escalation in self.active_escalations.items():
            if escalation["status"] in ["completed", "failed", "cancelled"]:
                completed_time = escalation.get("completed_at") or escalation.get("failed_at") or escalation.get("cancelled_at")
                if completed_time and datetime.fromisoformat(completed_time) < cutoff_time:
                    to_remove.append(escalation_id)
        
        for escalation_id in to_remove:
            del self.active_escalations[escalation_id]
        
        if to_remove:
            logger.info(f"🧹 Cleaned up {len(to_remove)} old escalations")
        
        return len(to_remove) 