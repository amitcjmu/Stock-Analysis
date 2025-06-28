"""
Flow Processing Agent - Central AI-powered orchestrator for discovery flow continuations.

This agent analyzes flow state, evaluates completion checklists, and intelligently routes
users to the appropriate next step when they click "Continue Flow".
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

try:
    from crewai_tools import BaseTool
except ImportError:
    # Fallback if BaseTool is not available
    class BaseTool:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    COMPLETED = "completed"
    PENDING = "pending"
    BLOCKED = "blocked"
    NOT_STARTED = "not_started"

class PhaseStatus(Enum):
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    BLOCKED = "blocked"

@dataclass
class TaskResult:
    """Result of evaluating a specific task completion"""
    task_id: str
    task_name: str
    status: TaskStatus
    confidence: float
    evidence: List[str] = field(default_factory=list)
    missing_requirements: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    completion_percentage: float = 0.0

@dataclass
class PhaseChecklistResult:
    """Result of evaluating a phase's completion checklist"""
    phase: str
    status: PhaseStatus
    completion_percentage: float
    tasks: List[TaskResult] = field(default_factory=list)
    validation_passed: bool = False
    ready_for_next_phase: bool = False
    blocking_issues: List[str] = field(default_factory=list)
    next_required_actions: List[str] = field(default_factory=list)

@dataclass
class RouteDecision:
    """Decision on where to route the user"""
    target_page: str
    flow_id: str
    phase: str
    specific_task: Optional[str] = None
    context_data: Dict[str, Any] = field(default_factory=dict)
    user_guidance: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FlowContinuationResult:
    """Complete result of flow continuation analysis"""
    flow_id: str
    current_phase: str
    next_action: str
    routing_decision: RouteDecision
    checklist_status: List[PhaseChecklistResult]
    user_guidance: Dict[str, Any]
    success: bool = True
    error_message: Optional[str] = None

class FlowProcessingAgent(BaseTool):
    """
    Universal AI agent for intelligent flow continuation and routing across ALL flow types.
    Supports Discovery, Assess, Plan, Execute, Modernize, FinOps, Observability, and Decommission flows.
    """
    
    name: str = "universal_flow_processing_agent"
    description: str = "Universal intelligent flow analysis and routing for all flow types"
    
    # Universal flow type definitions
    FLOW_TYPES = {
        'discovery': 'Discovery Flow',
        'assess': 'Assessment Flow', 
        'plan': 'Planning Flow',
        'execute': 'Execution Flow',
        'modernize': 'Modernization Flow',
        'finops': 'FinOps Flow',
        'observability': 'Observability Flow',
        'decommission': 'Decommission Flow'
    }
    
    # Universal phase completion checklists for all flow types
    PHASE_CHECKLISTS = {
        # === DISCOVERY FLOW PHASES ===
        "data_import": {
            "required_tasks": {
                "file_upload_completed": "Data file successfully uploaded",
                "format_validation": "File format validated by agents",
                "data_parsing": "Data successfully parsed into records", 
                "initial_analysis": "Basic data analysis completed",
                "agent_insights_generated": "Import validation agents provided insights"
            },
            "validation_criteria": {
                "min_records": 1,
                "agent_confidence": 0.7,
                "validation_status": "passed"
            },
            "target_page": "/discovery/import"
        },
        "attribute_mapping": {
            "required_tasks": {
                "field_analysis_completed": "Source fields analyzed by agents",
                "critical_attributes_identified": "Critical migration attributes identified",
                "mapping_suggestions_generated": "AI-generated field mapping suggestions",
                "user_mapping_review": "User reviewed and approved mappings",
                "confidence_scores_calculated": "Mapping confidence scores generated"
            },
            "validation_criteria": {
                "min_mapped_fields": 5,
                "critical_fields_mapped_percent": 80,
                "avg_confidence_score": 0.6
            },
            "target_page": "/discovery/attribute-mapping"
        },
        "data_cleansing": {
            "required_tasks": {
                "quality_analysis_completed": "Data quality assessment performed",
                "cleansing_rules_applied": "Data cleansing rules executed",
                "validation_performed": "Cleansed data validated",
                "quality_metrics_calculated": "Quality improvement metrics generated",
                "agent_quality_review": "Quality assessment agents completed review"
            },
            "validation_criteria": {
                "quality_improvement_percent": 10,
                "completeness_score": 0.8,
                "consistency_score": 0.7
            },
            "target_page": "/discovery/data-cleansing"
        },
        "inventory": {
            "required_tasks": {
                "asset_classification": "Assets classified by type and category",
                "criticality_assessment": "Business criticality evaluated",
                "dependency_identification": "Basic dependencies identified",
                "migration_readiness": "Migration readiness scored",
                "agent_inventory_review": "Inventory agents completed analysis"
            },
            "validation_criteria": {
                "min_assets_classified_percent": 90,
                "criticality_assigned_percent": 80,
                "migration_scores_calculated": True
            },
            "target_page": "/discovery/inventory"
        },
        "dependencies": {
            "required_tasks": {
                "app_dependencies_mapped": "Application dependencies identified",
                "infrastructure_dependencies": "Infrastructure dependencies mapped",
                "data_dependencies": "Data flow dependencies analyzed",
                "integration_complexity": "Integration complexity assessed",
                "dependency_validation": "Dependencies validated by agents"
            },
            "validation_criteria": {
                "dependency_coverage_percent": 85,
                "complexity_scores_assigned": True,
                "validation_confidence": 0.7
            },
            "target_page": "/discovery/dependencies"
        },
        "tech_debt": {
            "required_tasks": {
                "technical_assessment": "Technical debt assessment completed",
                "modernization_opportunities": "Modernization opportunities identified",
                "risk_analysis": "Technical risks analyzed",
                "recommendation_generation": "Modernization recommendations generated",
                "six_r_preparation": "6R strategy preparation completed"
            },
            "validation_criteria": {
                "debt_scores_calculated": True,
                "recommendations_generated": True,
                "risk_assessment_complete": True
            },
            "target_page": "/discovery/tech-debt"
        },
        
        # === ASSESSMENT FLOW PHASES ===
        "migration_readiness": {
            "required_tasks": {
                "asset_readiness_analysis": "Asset migration readiness assessed",
                "dependency_impact_analysis": "Dependency impact on migration analyzed", 
                "risk_assessment": "Migration risks identified and categorized",
                "effort_estimation": "Migration effort and timeline estimated",
                "strategy_recommendation": "6R migration strategy recommended"
            },
            "validation_criteria": {
                "min_assets_assessed": 90,
                "risk_coverage": 85,
                "strategy_confidence": 0.8
            },
            "target_page": "/assess/migration-readiness"
        },
        "business_impact": {
            "required_tasks": {
                "downtime_analysis": "Downtime requirements analyzed",
                "business_continuity": "Business continuity plan developed",
                "stakeholder_impact": "Stakeholder impact assessment completed",
                "cost_benefit_analysis": "Cost-benefit analysis performed",
                "compliance_review": "Compliance requirements reviewed"
            },
            "validation_criteria": {
                "impact_coverage": 80,
                "cost_analysis_complete": True,
                "compliance_validated": True
            },
            "target_page": "/assess/business-impact"
        },
        "technical_assessment": {
            "required_tasks": {
                "architecture_review": "Current architecture reviewed",
                "performance_baseline": "Performance baseline established",
                "security_assessment": "Security posture assessed",
                "integration_analysis": "Integration points analyzed",
                "modernization_opportunities": "Modernization opportunities identified"
            },
            "validation_criteria": {
                "architecture_documented": True,
                "performance_baselined": True,
                "security_scored": True
            },
            "target_page": "/assess/technical-assessment"
        },
        
        # === PLANNING FLOW PHASES ===
        "wave_planning": {
            "required_tasks": {
                "dependency_sequencing": "Migration sequence based on dependencies",
                "wave_definition": "Migration waves defined and validated",
                "timeline_planning": "Detailed timeline with milestones",
                "resource_planning": "Resource allocation planned",
                "risk_mitigation": "Risk mitigation strategies defined"
            },
            "validation_criteria": {
                "waves_defined": True,
                "timeline_validated": True,
                "resources_allocated": True
            },
            "target_page": "/plan/wave-planning"
        },
        "runbook_creation": {
            "required_tasks": {
                "migration_procedures": "Step-by-step migration procedures documented",
                "rollback_procedures": "Rollback procedures defined",
                "testing_procedures": "Testing and validation procedures created",
                "communication_plan": "Communication plan developed",
                "success_criteria": "Success criteria and KPIs defined"
            },
            "validation_criteria": {
                "procedures_documented": True,
                "rollback_tested": True,
                "success_criteria_defined": True
            },
            "target_page": "/plan/runbook-creation"
        },
        "resource_allocation": {
            "required_tasks": {
                "team_assignment": "Teams assigned to migration waves",
                "skill_gap_analysis": "Skill gaps identified and addressed",
                "training_plan": "Training plan developed",
                "vendor_coordination": "Vendor resources coordinated",
                "budget_allocation": "Budget allocated per wave"
            },
            "validation_criteria": {
                "teams_assigned": True,
                "training_planned": True,
                "budget_approved": True
            },
            "target_page": "/plan/resource-allocation"
        },
        
        # === EXECUTION FLOW PHASES ===
        "pre_migration": {
            "required_tasks": {
                "environment_preparation": "Target environments prepared",
                "data_backup": "Data backup completed and verified",
                "team_readiness": "Teams trained and ready",
                "communication_sent": "Stakeholder communication sent",
                "go_no_go_decision": "Go/No-Go decision made"
            },
            "validation_criteria": {
                "environments_ready": True,
                "backups_verified": True,
                "go_decision_made": True
            },
            "target_page": "/execute/pre-migration"
        },
        "migration_execution": {
            "required_tasks": {
                "migration_started": "Migration process initiated",
                "progress_monitoring": "Migration progress monitored",
                "issue_resolution": "Issues identified and resolved",
                "quality_validation": "Quality checks performed",
                "stakeholder_updates": "Regular stakeholder updates provided"
            },
            "validation_criteria": {
                "migration_in_progress": True,
                "quality_validated": True,
                "issues_tracked": True
            },
            "target_page": "/execute/migration-execution"
        },
        "post_migration": {
            "required_tasks": {
                "functionality_testing": "Functionality testing completed",
                "performance_validation": "Performance validation completed",
                "user_acceptance": "User acceptance testing passed",
                "documentation_updated": "Documentation updated",
                "lessons_learned": "Lessons learned captured"
            },
            "validation_criteria": {
                "testing_passed": True,
                "performance_validated": True,
                "documentation_updated": True
            },
            "target_page": "/execute/post-migration"
        },
        
        # === MODERNIZATION FLOW PHASES ===
        "modernization_assessment": {
            "required_tasks": {
                "technology_review": "Current technology stack reviewed",
                "modernization_options": "Modernization options identified",
                "cost_benefit_analysis": "Cost-benefit analysis for modernization",
                "technology_selection": "Target technologies selected",
                "modernization_roadmap": "Modernization roadmap created"
            },
            "validation_criteria": {
                "options_evaluated": True,
                "technologies_selected": True,
                "roadmap_approved": True
            },
            "target_page": "/modernize/assessment"
        },
        "architecture_design": {
            "required_tasks": {
                "target_architecture": "Target architecture designed",
                "integration_design": "Integration patterns designed",
                "security_design": "Security architecture designed",
                "performance_design": "Performance requirements addressed",
                "scalability_design": "Scalability requirements addressed"
            },
            "validation_criteria": {
                "architecture_approved": True,
                "security_validated": True,
                "performance_requirements_met": True
            },
            "target_page": "/modernize/architecture-design"
        },
        "implementation_planning": {
            "required_tasks": {
                "development_plan": "Development plan created",
                "testing_strategy": "Testing strategy defined",
                "deployment_strategy": "Deployment strategy defined",
                "training_plan": "Team training plan created",
                "change_management": "Change management plan developed"
            },
            "validation_criteria": {
                "plans_approved": True,
                "strategies_defined": True,
                "change_management_ready": True
            },
            "target_page": "/modernize/implementation-planning"
        },
        
        # === FINOPS FLOW PHASES ===
        "cost_analysis": {
            "required_tasks": {
                "current_cost_baseline": "Current cost baseline established",
                "cost_optimization_opportunities": "Cost optimization opportunities identified",
                "rightsizing_recommendations": "Rightsizing recommendations generated",
                "reserved_instance_analysis": "Reserved instance opportunities analyzed",
                "cost_allocation_review": "Cost allocation model reviewed"
            },
            "validation_criteria": {
                "baseline_established": True,
                "opportunities_identified": True,
                "recommendations_generated": True
            },
            "target_page": "/finops/cost-analysis"
        },
        "budget_planning": {
            "required_tasks": {
                "budget_forecast": "Budget forecast created",
                "cost_controls": "Cost control mechanisms implemented",
                "alerting_setup": "Cost alerting setup",
                "governance_policies": "Cost governance policies defined",
                "reporting_dashboard": "Cost reporting dashboard created"
            },
            "validation_criteria": {
                "forecast_approved": True,
                "controls_implemented": True,
                "governance_active": True
            },
            "target_page": "/finops/budget-planning"
        },
        
        # === OBSERVABILITY FLOW PHASES ===
        "monitoring_setup": {
            "required_tasks": {
                "metrics_collection": "Metrics collection configured",
                "log_aggregation": "Log aggregation setup",
                "alerting_rules": "Alerting rules configured",
                "dashboard_creation": "Monitoring dashboards created",
                "baseline_establishment": "Performance baselines established"
            },
            "validation_criteria": {
                "metrics_flowing": True,
                "alerts_configured": True,
                "dashboards_operational": True
            },
            "target_page": "/observability/monitoring-setup"
        },
        "performance_optimization": {
            "required_tasks": {
                "performance_analysis": "Performance bottlenecks analyzed",
                "optimization_recommendations": "Optimization recommendations generated",
                "capacity_planning": "Capacity planning performed",
                "sla_definition": "SLA/SLO definitions created",
                "incident_response": "Incident response procedures defined"
            },
            "validation_criteria": {
                "analysis_complete": True,
                "slas_defined": True,
                "incident_procedures_ready": True
            },
            "target_page": "/observability/performance-optimization"
        },
        
        # === DECOMMISSION FLOW PHASES ===
        "decommission_planning": {
            "required_tasks": {
                "asset_inventory": "Assets to decommission inventoried",
                "dependency_validation": "Dependencies validated for safe removal",
                "data_retention": "Data retention requirements addressed",
                "compliance_review": "Compliance requirements for decommission reviewed",
                "stakeholder_approval": "Stakeholder approval obtained"
            },
            "validation_criteria": {
                "inventory_complete": True,
                "dependencies_cleared": True,
                "approvals_obtained": True
            },
            "target_page": "/decommission/planning"
        },
        "data_migration": {
            "required_tasks": {
                "data_extraction": "Critical data extracted",
                "data_archival": "Data archived per retention policies",
                "data_validation": "Archived data validated",
                "access_revocation": "Access permissions revoked",
                "audit_trail": "Decommission audit trail created"
            },
            "validation_criteria": {
                "data_secured": True,
                "access_revoked": True,
                "audit_complete": True
            },
            "target_page": "/decommission/data-migration"
        },
        "system_shutdown": {
            "required_tasks": {
                "graceful_shutdown": "Systems gracefully shut down",
                "resource_reclamation": "Resources reclaimed",
                "documentation_update": "Documentation updated",
                "cost_validation": "Cost savings validated",
                "completion_notification": "Stakeholders notified of completion"
            },
            "validation_criteria": {
                "shutdown_complete": True,
                "resources_reclaimed": True,
                "savings_validated": True
            },
            "target_page": "/decommission/system-shutdown"
        }
    }
    
    def __init__(self, db_session=None, client_account_id=None, engagement_id=None):
        super().__init__()
        self.db = db_session
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
    
    def _run(self, flow_id: str, user_context: Dict[str, Any] = None) -> str:
        """
        Main entry point for flow continuation processing
        """
        try:
            result = self.process_flow_continuation(flow_id, user_context or {})
            return f"Flow {flow_id} processed successfully. Route: {result.routing_decision.target_page}"
        except Exception as e:
            logger.error(f"Flow Processing Agent failed for {flow_id}: {e}")
            return f"Flow processing failed: {str(e)}"
    
    async def process_flow_continuation(
        self, 
        flow_id: str, 
        user_context: Dict[str, Any]
    ) -> FlowContinuationResult:
        """
        Main processing method for flow continuation requests
        """
        try:
            logger.info(f"🤖 FLOW PROCESSING AGENT: Starting analysis for flow {flow_id}")
            
            # Step 1: Analyze current flow state
            flow_analysis = await self._analyze_flow_state(flow_id)
            
            # Step 2: Evaluate phase completion checklists
            checklist_results = await self._evaluate_all_phase_checklists(flow_analysis)
            
            # Step 3: Determine next action and routing
            routing_decision = await self._determine_optimal_route(flow_analysis, checklist_results)
            
            # Step 4: Generate user guidance
            user_guidance = await self._generate_user_guidance(routing_decision, checklist_results)
            
            logger.info(f"🤖 FLOW PROCESSING AGENT: Analysis complete for {flow_id}")
            logger.info(f"🎯 ROUTING DECISION: {routing_decision.target_page}")
            logger.info(f"📋 NEXT ACTION: {routing_decision.specific_task or 'Continue phase'}")
            
            return FlowContinuationResult(
                flow_id=flow_id,
                current_phase=flow_analysis.get("current_phase", "unknown"),
                next_action=routing_decision.specific_task or "continue_phase",
                routing_decision=routing_decision,
                checklist_status=checklist_results,
                user_guidance=user_guidance,
                success=True
            )
            
        except Exception as e:
            logger.error(f"❌ Flow Processing Agent failed for {flow_id}: {e}")
            return FlowContinuationResult(
                flow_id=flow_id,
                current_phase="error",
                next_action="error_recovery",
                routing_decision=RouteDecision(
                    target_page="/discovery/enhanced-dashboard",
                    flow_id=flow_id,
                    phase="error"
                ),
                checklist_status=[],
                user_guidance={"error": str(e)},
                success=False,
                error_message=str(e)
            )
    
    async def _determine_flow_type(self, flow_id: str) -> str:
        """
        Determine the flow type by looking up the flow in the database
        """
        try:
            if self.db is None:
                logger.warning(f"No database session available, defaulting to discovery flow type for {flow_id}")
                return "discovery"
            
            # Query the database to find the flow type
            # Check different tables where flows might be stored
            
            # First check discovery flows table
            from sqlalchemy import text
            
            # Try discovery flows first
            discovery_query = text("""
                SELECT 'discovery' as flow_type 
                FROM discovery_flows 
                WHERE flow_id = :flow_id OR id = :flow_id
                LIMIT 1
            """)
            
            result = await self.db.execute(discovery_query, {"flow_id": flow_id})
            row = result.fetchone()
            if row:
                return row.flow_type
            
            # Check for other flow types in a generic flows table if it exists
            try:
                generic_query = text("""
                    SELECT flow_type 
                    FROM flows 
                    WHERE id = :flow_id OR flow_id = :flow_id
                    LIMIT 1
                """)
                result = await self.db.execute(generic_query, {"flow_id": flow_id})
                row = result.fetchone()
                if row:
                    return row.flow_type
            except Exception:
                # Flows table might not exist yet
                pass
            
            # Check data imports (which are typically discovery flows)
            import_query = text("""
                SELECT 'discovery' as flow_type 
                FROM data_imports 
                WHERE id = :flow_id
                LIMIT 1
            """)
            
            result = await self.db.execute(import_query, {"flow_id": flow_id})
            row = result.fetchone()
            if row:
                return row.flow_type
            
            # Default to discovery if we can't determine the type
            logger.warning(f"Could not determine flow type for {flow_id}, defaulting to discovery")
            return "discovery"
            
        except Exception as e:
            logger.error(f"❌ Failed to determine flow type for {flow_id}: {e}")
            return "discovery"
    
    async def _analyze_flow_state(self, flow_id: str) -> Dict[str, Any]:
        """
        Analyze the current state of the flow (universal for all flow types)
        """
        try:
            # First determine what type of flow this is
            flow_type = await self._determine_flow_type(flow_id)
            logger.info(f"🔍 FLOW TYPE DETECTION: {flow_id} identified as {flow_type} flow")
            
            # Get flow status based on flow type
            if flow_type == "discovery":
                # Use existing discovery flow handler
                from app.api.v1.discovery_handlers.flow_management import FlowManagementHandler
                
                flow_handler = FlowManagementHandler(
                    db=self.db,
                    client_account_id=self.client_account_id,
                    engagement_id=self.engagement_id
                )
                
                flow_status = await flow_handler.get_flow_status(flow_id)
                flow_status["flow_type"] = flow_type
                
            else:
                # For other flow types, create a generic flow status
                # This will be enhanced as other flow types are implemented
                flow_status = {
                    "flow_id": flow_id,
                    "flow_type": flow_type,
                    "status": "active",  # Assume active for now
                    "current_phase": self._get_default_phase_for_flow_type(flow_type),
                    "progress_percentage": 0,
                    "phases": {},
                    "agent_insights": [],
                    "crewai_state_data": {}
                }
                
                logger.info(f"🔍 NON-DISCOVERY FLOW: {flow_id} ({flow_type}) using generic flow analysis")
            
            logger.info(f"🔍 FLOW ANALYSIS: {flow_id} ({flow_type}) - Status: {flow_status.get('status')}, Phase: {flow_status.get('current_phase')}, Progress: {flow_status.get('progress_percentage')}%")
            
            return flow_status
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze flow state for {flow_id}: {e}")
            return {
                "flow_id": flow_id,
                "flow_type": "unknown",
                "status": "error",
                "current_phase": "unknown",
                "progress_percentage": 0,
                "error": str(e)
            }
    
    def _get_default_phase_for_flow_type(self, flow_type: str) -> str:
        """
        Get the default starting phase for each flow type
        """
        default_phases = {
            "discovery": "data_import",
            "assess": "migration_readiness", 
            "plan": "wave_planning",
            "execute": "pre_migration",
            "modernize": "modernization_assessment",
            "finops": "cost_analysis",
            "observability": "monitoring_setup",
            "decommission": "decommission_planning"
        }
        
        return default_phases.get(flow_type, "data_import")
    
    async def _evaluate_all_phase_checklists(self, flow_analysis: Dict[str, Any]) -> List[PhaseChecklistResult]:
        """
        Evaluate completion checklists for all phases based on flow type
        """
        checklist_results = []
        flow_type = flow_analysis.get("flow_type", "discovery")
        
        # Get phases relevant to this flow type
        relevant_phases = self._get_phases_for_flow_type(flow_type)
        
        logger.info(f"📋 EVALUATING CHECKLISTS: {flow_type} flow has {len(relevant_phases)} phases")
        
        for phase_name in relevant_phases:
            if phase_name in self.PHASE_CHECKLISTS:
                checklist_config = self.PHASE_CHECKLISTS[phase_name]
                phase_result = await self._evaluate_phase_checklist(
                    flow_analysis, 
                    phase_name, 
                    checklist_config
                )
                checklist_results.append(phase_result)
                
                logger.info(f"📋 CHECKLIST: {phase_name} - {phase_result.status.value} ({phase_result.completion_percentage:.1f}%)")
            else:
                logger.warning(f"📋 MISSING CHECKLIST: No checklist defined for phase {phase_name}")
        
        return checklist_results
    
    def _get_phases_for_flow_type(self, flow_type: str) -> List[str]:
        """
        Get the phases that are relevant for each flow type
        """
        flow_phases = {
            "discovery": [
                "data_import", 
                "attribute_mapping", 
                "data_cleansing", 
                "inventory", 
                "dependencies", 
                "tech_debt"
            ],
            "assess": [
                "migration_readiness",
                "business_impact", 
                "technical_assessment"
            ],
            "plan": [
                "wave_planning",
                "runbook_creation",
                "resource_allocation"
            ],
            "execute": [
                "pre_migration",
                "migration_execution",
                "post_migration"
            ],
            "modernize": [
                "modernization_assessment",
                "architecture_design", 
                "implementation_planning"
            ],
            "finops": [
                "cost_analysis",
                "budget_planning"
            ],
            "observability": [
                "monitoring_setup",
                "performance_optimization"
            ],
            "decommission": [
                "decommission_planning",
                "data_migration",
                "system_shutdown"
            ]
        }
        
        return flow_phases.get(flow_type, ["data_import"])
    
    async def _evaluate_phase_checklist(
        self, 
        flow_analysis: Dict[str, Any], 
        phase_name: str, 
        checklist_config: Dict[str, Any]
    ) -> PhaseChecklistResult:
        """
        Evaluate completion checklist for a specific phase
        """
        phase_result = PhaseChecklistResult(
            phase=phase_name,
            status=PhaseStatus.NOT_STARTED,
            completion_percentage=0.0
        )
        
        completed_tasks = 0
        total_tasks = len(checklist_config["required_tasks"])
        
        # Evaluate each required task
        for task_id, task_description in checklist_config["required_tasks"].items():
            task_result = await self._evaluate_task_completion(
                flow_analysis, 
                task_id, 
                task_description, 
                phase_name
            )
            phase_result.tasks.append(task_result)
            
            if task_result.status == TaskStatus.COMPLETED:
                completed_tasks += 1
        
        # Calculate completion percentage
        phase_result.completion_percentage = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        
        # Determine phase status
        if completed_tasks == total_tasks:
            phase_result.status = PhaseStatus.COMPLETED
            phase_result.ready_for_next_phase = True
        elif completed_tasks > 0:
            phase_result.status = PhaseStatus.IN_PROGRESS
        else:
            phase_result.status = PhaseStatus.PENDING
        
        # Check for blocking issues
        pending_tasks = [t for t in phase_result.tasks if t.status != TaskStatus.COMPLETED]
        if pending_tasks:
            phase_result.next_required_actions = [
                f"Complete {task.task_name}" for task in pending_tasks[:3]  # Show top 3
            ]
        
        return phase_result
    
    async def _evaluate_task_completion(
        self, 
        flow_analysis: Dict[str, Any], 
        task_id: str, 
        task_description: str, 
        phase_name: str
    ) -> TaskResult:
        """
        Evaluate if a specific task has been completed using AI analysis
        """
        # Get phase completion status from flow
        phase_completed = flow_analysis.get("phases", {}).get(phase_name, False)
        
        # Analyze agent insights for task-specific evidence
        agent_insights = flow_analysis.get("agent_insights", [])
        task_evidence = self._find_task_evidence(agent_insights, task_id, phase_name)
        
        # Analyze flow state data for task completion indicators
        state_data = flow_analysis.get("crewai_state_data", {}) if isinstance(flow_analysis.get("crewai_state_data"), dict) else {}
        state_evidence = self._analyze_state_data_for_task(state_data, task_id, phase_name)
        
        # Determine completion status using AI logic
        is_completed, confidence = self._ai_determine_task_completion(
            task_id=task_id,
            phase_name=phase_name,
            phase_completed=phase_completed,
            evidence=task_evidence + state_evidence,
            flow_data=flow_analysis
        )
        
        status = TaskStatus.COMPLETED if is_completed else TaskStatus.PENDING
        
        # Generate next steps if not completed
        next_steps = []
        if not is_completed:
            next_steps = self._generate_task_next_steps(task_id, phase_name)
        
        return TaskResult(
            task_id=task_id,
            task_name=task_description,
            status=status,
            confidence=confidence,
            evidence=task_evidence + state_evidence,
            next_steps=next_steps,
            completion_percentage=100.0 if is_completed else 0.0
        )
    
    def _find_task_evidence(self, agent_insights: List[Dict], task_id: str, phase_name: str) -> List[str]:
        """
        Find evidence of task completion in agent insights
        """
        evidence = []
        
        if not agent_insights:
            return evidence
        
        # Task-specific keywords to look for
        task_keywords = {
            "file_upload_completed": ["upload", "file", "imported"],
            "format_validation": ["validation", "format", "valid"],
            "data_parsing": ["parsed", "records", "data"],
            "field_analysis_completed": ["field", "analysis", "mapping"],
            "mapping_suggestions_generated": ["mapping", "suggestions", "generated"],
            "user_mapping_review": ["approved", "review", "user"],
            "quality_analysis_completed": ["quality", "analysis", "assessment"],
            "asset_classification": ["classification", "assets", "categorized"],
            "dependency_identification": ["dependencies", "identified", "mapped"]
        }
        
        keywords = task_keywords.get(task_id, [task_id.split("_")])
        
        for insight in agent_insights:
            if isinstance(insight, dict):
                insight_text = (
                    insight.get("insight", "") + " " + 
                    insight.get("description", "") + " " +
                    insight.get("phase", "")
                ).lower()
                
                # Check if insight is related to this phase and task
                if (insight.get("phase") == phase_name or phase_name in insight_text):
                    for keyword in keywords:
                        if keyword.lower() in insight_text:
                            evidence.append(f"Agent insight: {insight.get('insight', '')[:100]}...")
                            break
        
        return evidence
    
    def _analyze_state_data_for_task(self, state_data: Dict, task_id: str, phase_name: str) -> List[str]:
        """
        Analyze flow state data for task completion indicators
        """
        evidence = []
        
        # Task-specific state data indicators
        task_indicators = {
            "file_upload_completed": ["raw_data", "import_data", "uploaded_file"],
            "format_validation": ["validation_results", "format_valid"],
            "data_parsing": ["parsed_data", "records_processed"],
            "field_analysis_completed": ["field_analysis", "source_fields"],
            "mapping_suggestions_generated": ["field_mappings", "mappings"],
            "user_mapping_review": ["approved_mappings", "user_approved"],
            "quality_analysis_completed": ["quality_metrics", "data_quality"],
            "asset_classification": ["classified_assets", "asset_types"],
            "dependency_identification": ["dependencies", "dependency_map"]
        }
        
        indicators = task_indicators.get(task_id, [])
        
        for indicator in indicators:
            if indicator in state_data and state_data[indicator]:
                evidence.append(f"State data: {indicator} present")
        
        # Check phase-specific data
        phase_data = state_data.get(phase_name, {})
        if isinstance(phase_data, dict) and phase_data:
            evidence.append(f"Phase data: {phase_name} has data")
        
        return evidence
    
    def _ai_determine_task_completion(
        self, 
        task_id: str, 
        phase_name: str, 
        phase_completed: bool, 
        evidence: List[str], 
        flow_data: Dict[str, Any]
    ) -> tuple[bool, float]:
        """
        Use AI logic to determine if a task is completed
        """
        # If the phase is marked as completed, assume most tasks are done
        if phase_completed:
            return True, 0.9
        
        # If we have evidence, it's likely completed
        if len(evidence) >= 2:
            return True, 0.8
        elif len(evidence) == 1:
            return True, 0.6
        
        # Special cases for specific tasks
        if task_id == "user_mapping_review":
            # This requires explicit user action
            user_actions = flow_data.get("user_interactions", [])
            if any("mapping" in str(action).lower() for action in user_actions):
                return True, 0.7
            return False, 0.3
        
        # Default: not completed if no evidence
        return False, 0.2
    
    def _generate_task_next_steps(self, task_id: str, phase_name: str) -> List[str]:
        """
        Generate specific next steps for incomplete tasks
        """
        next_steps_map = {
            "file_upload_completed": ["Upload a data file in CSV or Excel format"],
            "format_validation": ["Ensure file format is supported", "Check data structure"],
            "user_mapping_review": ["Review suggested field mappings", "Approve or modify mappings"],
            "quality_analysis_completed": ["Run data quality assessment", "Review quality metrics"],
            "asset_classification": ["Review asset classifications", "Assign business criticality"],
            "dependency_identification": ["Map application dependencies", "Identify infrastructure dependencies"]
        }
        
        return next_steps_map.get(task_id, [f"Complete {task_id.replace('_', ' ')}"])
    
    async def _determine_optimal_route(
        self, 
        flow_analysis: Dict[str, Any], 
        checklist_results: List[PhaseChecklistResult]
    ) -> RouteDecision:
        """
        Determine the optimal route based on flow analysis and checklist results
        """
        # Find the first incomplete phase
        incomplete_phase = None
        for phase_result in checklist_results:
            if phase_result.status != PhaseStatus.COMPLETED:
                incomplete_phase = phase_result
                break
        
        if not incomplete_phase:
            # All phases complete - route to completion
            return RouteDecision(
                target_page="/discovery/tech-debt",  # Final phase
                flow_id=flow_analysis["flow_id"],
                phase="completed",
                context_data={"all_phases_complete": True},
                user_guidance={"message": "All phases completed! Ready for 6R strategy."}
            )
        
        # Find the next pending task in the incomplete phase
        pending_task = None
        for task in incomplete_phase.tasks:
            if task.status != TaskStatus.COMPLETED:
                pending_task = task
                break
        
        # Get the target page for this phase
        phase_config = self.PHASE_CHECKLISTS.get(incomplete_phase.phase, {})
        target_page = phase_config.get("target_page", f"/discovery/{incomplete_phase.phase}")
        
        # Add flow_id to the page if it's not the import page
        if target_page != "/discovery/import":
            target_page = f"{target_page}/{flow_analysis['flow_id']}"
        
        return RouteDecision(
            target_page=target_page,
            flow_id=flow_analysis["flow_id"],
            phase=incomplete_phase.phase,
            specific_task=pending_task.task_id if pending_task else None,
            context_data={
                "flow_type": flow_analysis.get("flow_type", "discovery"),
                "phase_status": incomplete_phase,
                "pending_task": pending_task,
                "completion_percentage": incomplete_phase.completion_percentage
            },
            user_guidance={
                "phase": incomplete_phase.phase,
                "task": pending_task.task_name if pending_task else "Continue phase",
                "next_steps": pending_task.next_steps if pending_task else []
            }
        )
    
    async def _generate_user_guidance(
        self, 
        routing_decision: RouteDecision, 
        checklist_results: List[PhaseChecklistResult]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive user guidance based on analysis (universal for all flow types)
        """
        current_phase = routing_decision.phase
        flow_id = routing_decision.flow_id
        phase_result = next((p for p in checklist_results if p.phase == current_phase), None)
        
        # Determine flow type from routing decision context
        flow_type = routing_decision.context_data.get("flow_type", "discovery")
        flow_type_display = self.FLOW_TYPES.get(flow_type, "Unknown Flow")
        
        if not phase_result:
            return {
                "message": f"Continue with your {flow_type_display.lower()}",
                "flow_type": flow_type,
                "flow_type_display": flow_type_display
            }
        
        completed_count = sum(1 for task in phase_result.tasks if task.status == TaskStatus.COMPLETED)
        total_count = len(phase_result.tasks)
        
        # Generate flow-type specific phase display name
        phase_display = self._get_phase_display_name(current_phase, flow_type)
        
        guidance = {
            "summary": f"{phase_display} is {phase_result.completion_percentage:.1f}% complete",
            "phase": current_phase,
            "flow_type": flow_type,
            "flow_type_display": flow_type_display,
            "phase_display": phase_display,
            "completion_percentage": phase_result.completion_percentage,
            "completed_tasks": completed_count,
            "total_tasks": total_count,
            "next_steps": phase_result.next_required_actions,
            "detailed_status": {
                "completed_tasks": [
                    {"name": task.task_name, "confidence": task.confidence}
                    for task in phase_result.tasks if task.status == TaskStatus.COMPLETED
                ],
                "pending_tasks": [
                    {"name": task.task_name, "next_steps": task.next_steps}
                    for task in phase_result.tasks if task.status != TaskStatus.COMPLETED
                ]
            }
        }
        
        return guidance
    
    def _get_phase_display_name(self, phase: str, flow_type: str) -> str:
        """
        Get user-friendly display name for phases based on flow type
        """
        phase_display_names = {
            # Discovery phases
            "data_import": "Data Import",
            "attribute_mapping": "Attribute Mapping", 
            "data_cleansing": "Data Cleansing",
            "inventory": "Asset Inventory",
            "dependencies": "Dependency Analysis",
            "tech_debt": "Technical Debt Analysis",
            
            # Assessment phases
            "migration_readiness": "Migration Readiness Assessment",
            "business_impact": "Business Impact Analysis",
            "technical_assessment": "Technical Assessment",
            
            # Planning phases
            "wave_planning": "Migration Wave Planning",
            "runbook_creation": "Runbook Creation",
            "resource_allocation": "Resource Allocation",
            
            # Execution phases
            "pre_migration": "Pre-Migration Preparation",
            "migration_execution": "Migration Execution",
            "post_migration": "Post-Migration Validation",
            
            # Modernization phases
            "modernization_assessment": "Modernization Assessment",
            "architecture_design": "Architecture Design",
            "implementation_planning": "Implementation Planning",
            
            # FinOps phases
            "cost_analysis": "Cost Analysis",
            "budget_planning": "Budget Planning",
            
            # Observability phases
            "monitoring_setup": "Monitoring Setup",
            "performance_optimization": "Performance Optimization",
            
            # Decommission phases
            "decommission_planning": "Decommission Planning",
            "data_migration": "Data Migration & Archival",
            "system_shutdown": "System Shutdown"
        }
        
        return phase_display_names.get(phase, phase.replace('_', ' ').title()) 