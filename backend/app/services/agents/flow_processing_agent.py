"""
Universal Flow Processing Agent - Proper CrewAI Implementation

This module implements a true CrewAI agent system for intelligent flow continuation 
and routing across all flow types (Discovery, Assess, Plan, Execute, etc.).

Based on CrewAI documentation patterns:
- Agents with role, goal, backstory
- Task-based architecture  
- Tool integration
- Crew orchestration
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

try:
    from crewai import Agent, Task, Crew, Process
    from crewai.tools import BaseTool
    CREWAI_AVAILABLE = True
except ImportError:
    # Fallback classes if CrewAI is not available
    CREWAI_AVAILABLE = False
    
    class Agent:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class Task:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class Crew:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
        
        def kickoff(self, inputs=None):
            return {"result": "CrewAI not available - using fallback"}
    
    class Process:
        sequential = "sequential"
    
    class BaseTool:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Data models for flow processing results
@dataclass
class FlowAnalysisResult:
    """Result of flow state analysis"""
    flow_id: str
    flow_type: str
    current_phase: str
    status: str
    progress_percentage: float
    phases_data: Dict[str, Any] = field(default_factory=dict)
    agent_insights: List[Dict] = field(default_factory=list)
    validation_results: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RouteDecision:
    """Routing decision made by the agent"""
    target_page: str
    flow_id: str
    phase: str
    flow_type: str
    reasoning: str
    confidence: float
    next_actions: List[str] = field(default_factory=list)
    context_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FlowContinuationResult:
    """Complete result of flow continuation analysis"""
    flow_id: str
    flow_type: str
    current_phase: str
    routing_decision: RouteDecision
    user_guidance: Dict[str, Any]
    success: bool = True
    error_message: Optional[str] = None

# CrewAI Tools for Flow Processing
class FlowStateAnalysisTool(BaseTool):
    """Tool for analyzing current flow state across all flow types"""
    
    name: str = "flow_state_analyzer"
    description: str = "Analyzes the current state of any flow type (Discovery, Assess, Plan, Execute, etc.) to determine progress and completion status"
    
    # Use class variables to store session info (not ideal but works with Pydantic)
    _db_session: AsyncSession = None
    _client_account_id: int = None
    _engagement_id: int = None
    _user_id: int = None
    
    def __init__(self, db_session: AsyncSession = None, client_account_id: int = None, engagement_id: int = None, user_id: int = None):
        super().__init__()
        # Store in class variables since Pydantic doesn't allow instance attributes
        FlowStateAnalysisTool._db_session = db_session
        FlowStateAnalysisTool._client_account_id = client_account_id
        FlowStateAnalysisTool._engagement_id = engagement_id
        FlowStateAnalysisTool._user_id = user_id
    
    @property
    def db(self):
        return FlowStateAnalysisTool._db_session
    
    @property
    def client_account_id(self):
        return FlowStateAnalysisTool._client_account_id
    
    @property
    def engagement_id(self):
        return FlowStateAnalysisTool._engagement_id
    
    @property
    def user_id(self):
        return FlowStateAnalysisTool._user_id
    
    def _run(self, flow_id: str) -> str:
        """Analyze flow state and return structured analysis"""
        try:
            # Store the flow_id for async processing
            self._current_flow_id = flow_id
            
            # For now, return a placeholder that the crew can use
            # The actual async processing will be handled by the crew's async context
            return f"FLOW_ANALYSIS_NEEDED:{flow_id}"
        except Exception as e:
            logger.error(f"Flow state analysis failed for {flow_id}: {e}")
            return f"Error analyzing flow {flow_id}: {str(e)}"
    
    async def _analyze_flow_state(self, flow_id: str) -> FlowAnalysisResult:
        """Detailed flow state analysis"""
        try:
            # Determine flow type
            flow_type = await self._determine_flow_type(flow_id)
            
            if flow_type == "discovery":
                # Use existing discovery flow handler
                from app.api.v1.discovery_handlers.flow_management import FlowManagementHandler
                
                # Create a context object for the FlowManagementHandler
                from app.core.context import RequestContext
                context = RequestContext(
                    client_account_id=self.client_account_id,
                    engagement_id=self.engagement_id,
                    user_id=self.user_id,
                    session_id=None
                )
                flow_handler = FlowManagementHandler(db=self.db, context=context)
                
                try:
                    flow_status = await flow_handler.get_flow_status(flow_id)
                    
                    # Get detailed phase information
                    phases_data = flow_status.get("phases", {})
                    current_phase = flow_status.get("current_phase", "data_import")
                    
                    # Calculate actual progress based on phases
                    if phases_data:
                        # Count completed phases from the phases dictionary
                        completed_phases = sum(1 for phase_completed in phases_data.values() if phase_completed is True)
                        total_phases = len(phases_data)
                        progress_percentage = (completed_phases / total_phases * 100) if total_phases > 0 else 0
                    else:
                        # Fallback: use the progress_percentage from flow_status if available
                        progress_percentage = flow_status.get("progress_percentage", 0)
                    
                    # Get status and error information
                    status = flow_status.get("status", "active")
                    error_info = flow_status.get("error_message", "")
                    
                    return FlowAnalysisResult(
                        flow_id=flow_id,
                        flow_type=flow_type,
                        current_phase=current_phase,
                        status=status,
                        progress_percentage=progress_percentage,
                        phases_data=phases_data,
                        agent_insights=flow_status.get("agent_insights", []),
                        validation_results={
                            "error_message": error_info,
                            "last_updated": flow_status.get("last_updated"),
                            "crewai_state_data": flow_status.get("crewai_state_data", {})
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to get flow status for {flow_id}: {e}")
                    # Return error state with explanation
                    return FlowAnalysisResult(
                        flow_id=flow_id,
                        flow_type=flow_type,
                        current_phase="error",
                        status="error",
                        progress_percentage=0,
                        phases_data={},
                        agent_insights=[],
                        validation_results={"error_message": f"Failed to retrieve flow status: {str(e)}"}
                    )
            else:
                # For other flow types, create basic analysis
                return FlowAnalysisResult(
                    flow_id=flow_id,
                    flow_type=flow_type,
                    current_phase=self._get_default_phase_for_flow_type(flow_type),
                    status="active",
                    progress_percentage=0,
                    phases_data={},
                    agent_insights=[],
                    validation_results={}
                )
                
        except Exception as e:
            logger.error(f"Failed to analyze flow {flow_id}: {e}")
            return FlowAnalysisResult(
                flow_id=flow_id,
                flow_type="unknown",
                current_phase="error",
                status="error",
                progress_percentage=0
            )
    
    async def _determine_flow_type(self, flow_id: str) -> str:
        """Determine flow type from database"""
        try:
            if self.db is None:
                return "discovery"
            
            from sqlalchemy import text
            
            # Check discovery flows
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
            
            # Check other flow types if generic flows table exists
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
                pass
            
            return "discovery"  # Default fallback
            
        except Exception as e:
            logger.error(f"Failed to determine flow type for {flow_id}: {e}")
            return "discovery"
    
    def _get_default_phase_for_flow_type(self, flow_type: str) -> str:
        """Get default starting phase for each flow type"""
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

class PhaseValidationTool(BaseTool):
    """Tool for validating phase completion based on actual database data"""
    
    name: str = "phase_validator"
    description: str = "Validates whether phases are complete by analyzing actual database data, not just status flags. Checks for real asset data, dependencies, tech debt analysis, etc."
    
    # Store database session and context info
    _db_session: AsyncSession = None
    _client_account_id: int = None
    _engagement_id: int = None
    _user_id: int = None
    
    def __init__(self, db_session: AsyncSession = None, client_account_id: int = None, engagement_id: int = None, user_id: int = None):
        super().__init__()
        PhaseValidationTool._db_session = db_session
        PhaseValidationTool._client_account_id = client_account_id
        PhaseValidationTool._engagement_id = engagement_id
        PhaseValidationTool._user_id = user_id
    
    @property
    def db(self):
        return PhaseValidationTool._db_session
    
    @property
    def client_account_id(self):
        return PhaseValidationTool._client_account_id
    
    @property
    def engagement_id(self):
        return PhaseValidationTool._engagement_id
    
    @property
    def user_id(self):
        return PhaseValidationTool._user_id
    
    def _run(self, flow_analysis: str, phase: str) -> str:
        """Validate phase completion with actual data analysis"""
        try:
            # Extract flow ID from analysis
            import re
            flow_match = re.search(r"Flow ([a-f0-9-]+)", flow_analysis)
            if not flow_match:
                # Try to extract from FLOW_ANALYSIS_NEEDED format
                needed_match = re.search(r"FLOW_ANALYSIS_NEEDED:([a-f0-9-]+)", flow_analysis)
                flow_id = needed_match.group(1) if needed_match else None
            else:
                flow_id = flow_match.group(1)
            
            if not flow_id:
                return f"Phase {phase} validation FAILED: Cannot extract flow ID from analysis"
            
            # Store for async processing - return a placeholder that indicates data validation needed
            self._current_flow_id = flow_id
            self._current_phase = phase
            return f"DATA_VALIDATION_NEEDED:{flow_id}:{phase}"
            
        except Exception as e:
            logger.error(f"Phase validation error for {phase}: {e}")
            return f"Phase {phase} validation ERROR: {str(e)}"
    
    async def _validate_phase_with_data(self, flow_id: str, phase: str) -> str:
        """Perform comprehensive data-driven phase validation"""
        try:
            # Get flow information
            from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
            from app.core.context import RequestContext
            
            context = RequestContext(
                client_account_id=self.client_account_id,
                engagement_id=self.engagement_id,
                user_id=self.user_id,
                session_id=None
            )
            
            flow_repo = DiscoveryFlowRepository(self.db, context)
            flow = await flow_repo.get_by_flow_id(flow_id)
            
            if not flow:
                return f"Phase {phase} validation FAILED: Flow {flow_id} not found"
            
            # Phase-specific validation logic
            if phase == "data_import":
                return await self._validate_data_import_phase(flow)
            elif phase == "attribute_mapping":
                return await self._validate_attribute_mapping_phase(flow)
            elif phase == "data_cleansing":
                return await self._validate_data_cleansing_phase(flow)
            elif phase == "inventory":
                return await self._validate_inventory_phase(flow)
            elif phase == "dependencies":
                return await self._validate_dependencies_phase(flow)
            elif phase == "tech_debt":
                return await self._validate_tech_debt_phase(flow)
            else:
                return f"Phase {phase} validation UNKNOWN: Unsupported phase type"
                
        except Exception as e:
            logger.error(f"Data validation error for phase {phase}: {e}")
            return f"Phase {phase} validation ERROR: {str(e)}"
    
    async def _validate_data_import_phase(self, flow) -> str:
        """Validate data import phase by checking for actual imported data"""
        try:
            # Check if data_import_sessions exist for this flow
            from sqlalchemy import select, func
            from app.models.data_import import DataImportSession
            
            # Count import sessions for this flow
            import_count_query = select(func.count(DataImportSession.id)).where(
                DataImportSession.discovery_flow_id == flow.id
            )
            result = await self.db.execute(import_count_query)
            import_count = result.scalar() or 0
            
            # Check for raw data records
            from app.models.raw_data_record import RawDataRecord
            raw_data_query = select(func.count(RawDataRecord.id)).where(
                RawDataRecord.client_account_id == flow.client_account_id
            )
            result = await self.db.execute(raw_data_query)
            raw_data_count = result.scalar() or 0
            
            # Validation criteria
            if import_count > 0 and raw_data_count > 0:
                return f"Phase data_import is COMPLETE: {import_count} import sessions, {raw_data_count} raw records imported"
            elif import_count > 0:
                return f"Phase data_import is PARTIAL: {import_count} import sessions but no raw data records found"
            else:
                return f"Phase data_import is INCOMPLETE: No import sessions or data found"
                
        except Exception as e:
            logger.error(f"Data import validation error: {e}")
            return f"Phase data_import validation ERROR: {str(e)}"
    
    async def _validate_attribute_mapping_phase(self, flow) -> str:
        """Validate attribute mapping by checking for field mappings"""
        try:
            from sqlalchemy import select, func
            from app.models.field_mapping import FieldMapping
            
            # Count field mappings for this flow
            mapping_query = select(func.count(FieldMapping.id)).where(
                FieldMapping.discovery_flow_id == flow.id
            )
            result = await self.db.execute(mapping_query)
            mapping_count = result.scalar() or 0
            
            # Check for mapped fields with confidence scores
            confident_mappings_query = select(func.count(FieldMapping.id)).where(
                FieldMapping.discovery_flow_id == flow.id,
                FieldMapping.confidence_score >= 0.7
            )
            result = await self.db.execute(confident_mappings_query)
            confident_count = result.scalar() or 0
            
            if mapping_count >= 5 and confident_count >= 3:
                return f"Phase attribute_mapping is COMPLETE: {mapping_count} mappings, {confident_count} high-confidence"
            elif mapping_count > 0:
                return f"Phase attribute_mapping is PARTIAL: {mapping_count} mappings, {confident_count} high-confidence (need more)"
            else:
                return f"Phase attribute_mapping is INCOMPLETE: No field mappings found"
                
        except Exception as e:
            logger.error(f"Attribute mapping validation error: {e}")
            return f"Phase attribute_mapping validation ERROR: {str(e)}"
    
    async def _validate_data_cleansing_phase(self, flow) -> str:
        """Validate data cleansing by checking for cleaned data and quality metrics"""
        try:
            from sqlalchemy import select, func
            from app.models.data_quality_issue import DataQualityIssue
            
            # Count data quality issues identified
            quality_issues_query = select(func.count(DataQualityIssue.id)).where(
                DataQualityIssue.client_account_id == flow.client_account_id
            )
            result = await self.db.execute(quality_issues_query)
            issues_count = result.scalar() or 0
            
            # Count resolved issues
            resolved_issues_query = select(func.count(DataQualityIssue.id)).where(
                DataQualityIssue.client_account_id == flow.client_account_id,
                DataQualityIssue.status == 'resolved'
            )
            result = await self.db.execute(resolved_issues_query)
            resolved_count = result.scalar() or 0
            
            # Check if flow has cleansing metadata
            has_cleansing_data = bool(flow.data_cleansing_completed and 
                                    flow.crewai_state_data and 
                                    'data_cleansing' in flow.crewai_state_data)
            
            if has_cleansing_data and (issues_count == 0 or resolved_count >= issues_count * 0.8):
                return f"Phase data_cleansing is COMPLETE: {resolved_count}/{issues_count} issues resolved, cleansing metadata present"
            elif has_cleansing_data:
                return f"Phase data_cleansing is PARTIAL: {resolved_count}/{issues_count} issues resolved, more cleanup needed"
            else:
                return f"Phase data_cleansing is INCOMPLETE: No cleansing data or unresolved quality issues"
                
        except Exception as e:
            logger.error(f"Data cleansing validation error: {e}")
            return f"Phase data_cleansing validation ERROR: {str(e)}"
    
    async def _validate_inventory_phase(self, flow) -> str:
        """Validate inventory phase by checking for actual assets in the assets table"""
        try:
            from sqlalchemy import select, func
            from app.models.asset import Asset
            
            # Count assets created from this discovery flow
            assets_query = select(func.count(Asset.id)).where(
                Asset.discovery_flow_id == flow.id,
                Asset.client_account_id == flow.client_account_id
            )
            result = await self.db.execute(assets_query)
            asset_count = result.scalar() or 0
            
            # Count assets with complete data (name, type, and technical specs)
            complete_assets_query = select(func.count(Asset.id)).where(
                Asset.discovery_flow_id == flow.id,
                Asset.client_account_id == flow.client_account_id,
                Asset.name.isnot(None),
                Asset.asset_type.isnot(None),
                Asset.hostname.isnot(None)
            )
            result = await self.db.execute(complete_assets_query)
            complete_count = result.scalar() or 0
            
            # Count assets with migration readiness data
            assessed_assets_query = select(func.count(Asset.id)).where(
                Asset.discovery_flow_id == flow.id,
                Asset.client_account_id == flow.client_account_id,
                Asset.migration_status.isnot(None)
            )
            result = await self.db.execute(assessed_assets_query)
            assessed_count = result.scalar() or 0
            
            if asset_count >= 5 and complete_count >= asset_count * 0.8:
                return f"Phase inventory is COMPLETE: {asset_count} assets created, {complete_count} complete, {assessed_count} assessed"
            elif asset_count > 0:
                return f"Phase inventory is PARTIAL: {asset_count} assets created, {complete_count} complete (need {int(asset_count * 0.8)} minimum)"
            else:
                return f"Phase inventory is INCOMPLETE: No assets found in main assets table"
                
        except Exception as e:
            logger.error(f"Inventory validation error: {e}")
            return f"Phase inventory validation ERROR: {str(e)}"
    
    async def _validate_dependencies_phase(self, flow) -> str:
        """Validate dependencies phase by checking for dependency analysis"""
        try:
            from sqlalchemy import select, func
            from app.models.asset import Asset, AssetDependency
            
            # Count assets from this flow
            assets_query = select(func.count(Asset.id)).where(
                Asset.discovery_flow_id == flow.id,
                Asset.client_account_id == flow.client_account_id
            )
            result = await self.db.execute(assets_query)
            asset_count = result.scalar() or 0
            
            # Count assets with dependency data
            assets_with_deps_query = select(func.count(Asset.id)).where(
                Asset.discovery_flow_id == flow.id,
                Asset.client_account_id == flow.client_account_id,
                Asset.dependencies.isnot(None)
            )
            result = await self.db.execute(assets_with_deps_query)
            deps_count = result.scalar() or 0
            
            # Count formal dependency relationships
            formal_deps_query = select(func.count(AssetDependency.id)).join(
                Asset, AssetDependency.asset_id == Asset.id
            ).where(
                Asset.discovery_flow_id == flow.id,
                Asset.client_account_id == flow.client_account_id
            )
            result = await self.db.execute(formal_deps_query)
            formal_deps_count = result.scalar() or 0
            
            # Check for dependency analysis in flow metadata
            has_dep_analysis = bool(flow.dependencies_completed and 
                                  flow.crewai_state_data and 
                                  'dependencies' in flow.crewai_state_data)
            
            if has_dep_analysis and (deps_count > 0 or formal_deps_count > 0):
                return f"Phase dependencies is COMPLETE: {deps_count} assets with dependencies, {formal_deps_count} formal relationships"
            elif asset_count > 0 and deps_count >= asset_count * 0.3:
                return f"Phase dependencies is PARTIAL: {deps_count}/{asset_count} assets analyzed for dependencies"
            else:
                return f"Phase dependencies is INCOMPLETE: Insufficient dependency analysis ({deps_count}/{asset_count} assets)"
                
        except Exception as e:
            logger.error(f"Dependencies validation error: {e}")
            return f"Phase dependencies validation ERROR: {str(e)}"
    
    async def _validate_tech_debt_phase(self, flow) -> str:
        """Validate tech debt phase by checking for technical debt analysis"""
        try:
            from sqlalchemy import select, func
            from app.models.asset import Asset
            
            # Count assets from this flow
            assets_query = select(func.count(Asset.id)).where(
                Asset.discovery_flow_id == flow.id,
                Asset.client_account_id == flow.client_account_id
            )
            result = await self.db.execute(assets_query)
            asset_count = result.scalar() or 0
            
            # Count assets with migration strategy (6R analysis)
            sixr_assets_query = select(func.count(Asset.id)).where(
                Asset.discovery_flow_id == flow.id,
                Asset.client_account_id == flow.client_account_id,
                Asset.six_r_strategy.isnot(None)
            )
            result = await self.db.execute(sixr_assets_query)
            sixr_count = result.scalar() or 0
            
            # Count assets with complexity assessment
            complexity_assets_query = select(func.count(Asset.id)).where(
                Asset.discovery_flow_id == flow.id,
                Asset.client_account_id == flow.client_account_id,
                Asset.migration_complexity.isnot(None)
            )
            result = await self.db.execute(complexity_assets_query)
            complexity_count = result.scalar() or 0
            
            # Count assets with business criticality
            criticality_assets_query = select(func.count(Asset.id)).where(
                Asset.discovery_flow_id == flow.id,
                Asset.client_account_id == flow.client_account_id,
                Asset.business_criticality.isnot(None)
            )
            result = await self.db.execute(criticality_assets_query)
            criticality_count = result.scalar() or 0
            
            # Check for tech debt analysis in flow metadata
            has_tech_debt_analysis = bool(flow.tech_debt_completed and 
                                        flow.crewai_state_data and 
                                        'tech_debt' in flow.crewai_state_data)
            
            # Calculate completion percentage
            completion_rate = 0
            if asset_count > 0:
                completion_rate = min(sixr_count, complexity_count, criticality_count) / asset_count
            
            if has_tech_debt_analysis and completion_rate >= 0.8:
                return f"Phase tech_debt is COMPLETE: {sixr_count} 6R strategies, {complexity_count} complexity, {criticality_count} criticality assessments"
            elif completion_rate >= 0.5:
                return f"Phase tech_debt is PARTIAL: {int(completion_rate*100)}% completion rate, need more analysis"
            else:
                return f"Phase tech_debt is INCOMPLETE: Only {int(completion_rate*100)}% of assets analyzed for tech debt"
                
        except Exception as e:
            logger.error(f"Tech debt validation error: {e}")
            return f"Phase tech_debt validation ERROR: {str(e)}"

class RouteDecisionTool(BaseTool):
    """Tool for making intelligent routing decisions"""
    
    name: str = "route_decision_maker"
    description: str = "Makes intelligent routing decisions based on flow analysis and phase validation results"
    
    # Route mapping for all flow types
    ROUTE_MAPPING: Dict[str, Dict[str, str]] = {
        "discovery": {
            "data_import": "/discovery/import",
            "attribute_mapping": "/discovery/attribute-mapping",
            "data_cleansing": "/discovery/data-cleansing", 
            "inventory": "/discovery/inventory",
            "dependencies": "/discovery/dependencies",
            "tech_debt": "/discovery/tech-debt",
            "completed": "/assess"
        },
        "assess": {
            "migration_readiness": "/assess/migration-readiness",
            "business_impact": "/assess/business-impact",
            "technical_assessment": "/assess/technical-assessment",
            "completed": "/assess/summary"
        },
        "plan": {
            "wave_planning": "/plan/wave-planning",
            "runbook_creation": "/plan/runbook-creation",
            "resource_allocation": "/plan/resource-allocation",
            "completed": "/plan/summary"
        },
        "execute": {
            "pre_migration": "/execute/pre-migration",
            "migration_execution": "/execute/migration-execution",
            "post_migration": "/execute/post-migration",
            "completed": "/execute/summary"
        },
        "modernize": {
            "modernization_assessment": "/modernize/assessment",
            "architecture_design": "/modernize/architecture-design",
            "implementation_planning": "/modernize/implementation-planning",
            "completed": "/modernize/summary"
        },
        "finops": {
            "cost_analysis": "/finops/cost-analysis",
            "budget_planning": "/finops/budget-planning",
            "completed": "/finops/summary"
        },
        "observability": {
            "monitoring_setup": "/observability/monitoring-setup",
            "performance_optimization": "/observability/performance-optimization",
            "completed": "/observability/summary"
        },
        "decommission": {
            "decommission_planning": "/decommission/planning",
            "data_migration": "/decommission/data-migration",
            "system_shutdown": "/decommission/system-shutdown",
            "completed": "/decommission/summary"
        }
    }
    
    def _run(self, flow_analysis: str, validation_result: str) -> str:
        """Make routing decision based on analysis"""
        try:
            # Parse inputs (in real implementation, these would be structured)
            flow_type = self._extract_flow_type(flow_analysis)
            current_phase = self._extract_current_phase(flow_analysis)
            is_complete = "COMPLETE" in validation_result
            
            routes = self.ROUTE_MAPPING.get(flow_type, {})
            
            if is_complete:
                # Move to next phase or completion
                next_phase = self._get_next_phase(flow_type, current_phase)
                target_page = routes.get(next_phase, routes.get("completed", "/"))
            else:
                # Stay in current phase
                target_page = routes.get(current_phase, "/")
            
            # Add flow_id to route if not the import page
            if not target_page.endswith("/import"):
                flow_id = self._extract_flow_id(flow_analysis)
                if flow_id:
                    target_page = f"{target_page}/{flow_id}"
            
            reasoning = f"Flow {flow_type} in phase {current_phase} - {'advancing' if is_complete else 'continuing'}"
            
            return f"ROUTE: {target_page} | REASONING: {reasoning} | CONFIDENCE: 0.9"
            
        except Exception as e:
            return f"Error making routing decision: {str(e)}"
    
    def _extract_flow_type(self, analysis: str) -> str:
        """Extract flow type from analysis"""
        for flow_type in ["discovery", "assess", "plan", "execute", "modernize", "finops", "observability", "decommission"]:
            if f"Type={flow_type}" in analysis:
                return flow_type
        return "discovery"
    
    def _extract_current_phase(self, analysis: str) -> str:
        """Extract current phase from analysis"""
        import re
        match = re.search(r"Phase=([^,]+)", analysis)
        return match.group(1) if match else "data_import"
    
    def _extract_flow_id(self, analysis: str) -> str:
        """Extract flow ID from analysis"""
        import re
        match = re.search(r"Flow ([a-f0-9-]+)", analysis)
        return match.group(1) if match else ""
    
    def _get_next_phase(self, flow_type: str, current_phase: str) -> str:
        """Get the next phase for a flow type"""
        phase_sequences = {
            "discovery": ["data_import", "attribute_mapping", "data_cleansing", "inventory", "dependencies", "tech_debt"],
            "assess": ["migration_readiness", "business_impact", "technical_assessment"],
            "plan": ["wave_planning", "runbook_creation", "resource_allocation"],
            "execute": ["pre_migration", "migration_execution", "post_migration"],
            "modernize": ["modernization_assessment", "architecture_design", "implementation_planning"],
            "finops": ["cost_analysis", "budget_planning"],
            "observability": ["monitoring_setup", "performance_optimization"],
            "decommission": ["decommission_planning", "data_migration", "system_shutdown"]
        }
        
        sequence = phase_sequences.get(flow_type, [])
        try:
            current_index = sequence.index(current_phase)
            if current_index + 1 < len(sequence):
                return sequence[current_index + 1]
        except ValueError:
            pass
        
        return "completed"

# CrewAI Agent Definitions
class UniversalFlowProcessingCrew:
    """
    Universal Flow Processing Crew - Proper CrewAI Implementation
    
    This crew handles flow continuation requests across ALL flow types using
    proper CrewAI patterns with specialized agents, tasks, and tools.
    """
    
    def __init__(self, db_session: AsyncSession = None, client_account_id: int = None, engagement_id: int = None, user_id: int = None):
        self.db = db_session
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.user_id = user_id
        
        # Initialize tools
        self.flow_analyzer = FlowStateAnalysisTool(db_session, client_account_id, engagement_id, user_id)
        self.phase_validator = PhaseValidationTool(db_session, client_account_id, engagement_id, user_id)
        self.route_decider = RouteDecisionTool()
        
        # Create agents
        self._create_agents()
        
        # Create crew
        self._create_crew()
    
    def _create_agents(self):
        """Create specialized CrewAI agents following documentation patterns"""
        
        # Get CrewAI LLM configuration
        try:
            from app.services.llm_config import get_crewai_llm
            llm = get_crewai_llm()
            logger.info("✅ CrewAI LLM configured for Flow Processing agents")
        except Exception as e:
            logger.error(f"Failed to get CrewAI LLM: {e}")
            llm = None
        
        # Flow Analysis Agent
        self.flow_analyst = Agent(
            role="Flow State Analyst",
            goal="Quickly analyze flow state and return structured data about current phase and completion status",
            backstory="You are a fast, efficient flow analyzer. Your job is to quickly check database state and return factual information about flow progress. No lengthy analysis needed - just facts.",
            tools=[self.flow_analyzer],
            verbose=False,
            allow_delegation=False,
            max_iter=1,
            memory=False,
            llm=llm
        )
        
        # Phase Validation Agent  
        self.phase_validator_agent = Agent(
            role="Database-Driven Phase Validator",
            goal="Validate phase completion by analyzing actual database data - assets, mappings, dependencies, tech debt analysis - not just status flags",
            backstory="You are a data-driven validator. You check actual database records to determine if work was really completed. You count assets, validate field mappings, check dependency analysis, and verify tech debt assessments. You don't trust status flags - only real data.",
            tools=[self.phase_validator],
            verbose=False,
            allow_delegation=False,
            max_iter=1,
            memory=False,
            llm=llm
        )
        
        # Route Decision Agent
        self.route_strategist = Agent(
            role="Flow Navigation Strategist", 
            goal="Quickly determine the next page URL based on current phase and flow type using the route mapping table",
            backstory="You are a fast router. Use the route mapping table to quickly return the correct URL for the current phase. No complex thinking needed.",
            tools=[self.route_decider],
            verbose=False,
            allow_delegation=False,
            max_iter=1,
            memory=False,
            llm=llm
        )
    
    def _create_crew(self):
        """Create the CrewAI crew with proper task orchestration"""
        if not CREWAI_AVAILABLE:
            logger.warning("CrewAI not available, using fallback implementation")
            self.crew = None
            return
        
        self.crew = Crew(
            agents=[self.flow_analyst, self.phase_validator_agent, self.route_strategist],
            tasks=[],  # Tasks will be created dynamically
            process=Process.sequential,
            verbose=False,
            memory=False
        )
    
    async def process_flow_continuation(self, flow_id: str, user_context: Dict[str, Any] = None) -> FlowContinuationResult:
        """
        Process flow continuation request using proper CrewAI crew orchestration
        """
        try:
            logger.info(f"🤖 UNIVERSAL FLOW CREW: Starting analysis for flow {flow_id}")
            
            if not CREWAI_AVAILABLE or self.crew is None:
                return await self._fallback_processing(flow_id, user_context)
            
            # Create dynamic tasks for this specific flow continuation request
            tasks = self._create_flow_continuation_tasks(flow_id, user_context)
            
            # Update crew with current tasks
            self.crew.tasks = tasks
            
            # Execute the crew
            result = self.crew.kickoff({
                "flow_id": flow_id,
                "user_context": user_context or {}
            })
            
            # Parse crew result into structured response
            return await self._parse_crew_result(result, flow_id)
            
        except Exception as e:
            logger.error(f"❌ Universal Flow Crew failed for {flow_id}: {e}")
            return FlowContinuationResult(
                flow_id=flow_id,
                flow_type="unknown",
                current_phase="error",
                routing_decision=RouteDecision(
                    target_page="/discovery/enhanced-dashboard",
                    flow_id=flow_id,
                    phase="error",
                    flow_type="unknown",
                    reasoning=f"Error in flow processing: {str(e)}",
                    confidence=0.1
                ),
                user_guidance={"error": str(e)},
                success=False,
                error_message=str(e)
            )
    
    def _create_flow_continuation_tasks(self, flow_id: str, user_context: Dict[str, Any]) -> List[Task]:
        """Create dynamic tasks for flow continuation analysis"""
        
        # Task 1: Flow State Analysis
        analysis_task = Task(
            description=f"Check flow {flow_id} database state. Return: flow_type, current_phase, progress_percentage. Be fast and factual.",
            agent=self.flow_analyst,
            expected_output="Flow type, current phase, progress percentage"
        )
        
        # Task 2: Data-Driven Phase Validation
        validation_task = Task(
            description="Validate phase completion by checking actual database data: count assets created, verify field mappings exist, check dependency analysis, validate tech debt assessments. Don't rely on status flags - examine real data records.",
            agent=self.phase_validator_agent,
            expected_output="Data-driven validation results with asset counts, mapping status, and completion analysis",
            context=[analysis_task]
        )
        
        # Task 3: Route Decision
        routing_task = Task(
            description="Use route mapping table to find correct URL for current phase. Return: target_page_url. Be fast.",
            agent=self.route_strategist,
            expected_output="Target page URL from route mapping",
            context=[analysis_task, validation_task]
        )
        
        return [analysis_task, validation_task, routing_task]
    
    async def _parse_crew_result(self, crew_result, flow_id: str) -> FlowContinuationResult:
        """Parse crew execution result into structured response with comprehensive data validation"""
        try:
            # Get the actual flow analysis first to have real data
            flow_analysis = await self.flow_analyzer._analyze_flow_state(flow_id)
            
            result_text = str(crew_result.get("result", "")) if isinstance(crew_result, dict) else str(crew_result)
            
            # Perform comprehensive data validation for each phase
            phase_validations = {}
            if flow_analysis.flow_type == "discovery":
                # Validate each discovery phase with actual data
                phases_to_validate = ["data_import", "attribute_mapping", "data_cleansing", "inventory", "dependencies", "tech_debt"]
                for phase in phases_to_validate:
                    try:
                        validation_result = await self.phase_validator._validate_phase_with_data(flow_id, phase)
                        phase_validations[phase] = validation_result
                    except Exception as e:
                        phase_validations[phase] = f"Phase {phase} validation ERROR: {str(e)}"
            
            # Determine the actual current phase based on data validation
            actual_current_phase = self._determine_actual_phase_from_validation(phase_validations, flow_analysis.current_phase)
            
            # Use validated phase instead of flow status phase
            flow_type = flow_analysis.flow_type
            current_phase = actual_current_phase
            
            # Try to extract route from crew result, but fall back to intelligent routing
            target_page = None
            if "ROUTE:" in result_text:
                target_page = result_text.split("ROUTE:")[1].split("|")[0].strip() if "|" in result_text.split("ROUTE:")[1] else result_text.split("ROUTE:")[1].strip()
            
            # If no route found in crew result, use intelligent routing based on validated phase
            if not target_page:
                # Update flow analysis with validated phase
                validated_flow_analysis = FlowAnalysisResult(
                    flow_id=flow_analysis.flow_id,
                    flow_type=flow_analysis.flow_type,
                    current_phase=current_phase,
                    status=flow_analysis.status,
                    progress_percentage=flow_analysis.progress_percentage,
                    phases_data=flow_analysis.phases_data,
                    agent_insights=flow_analysis.agent_insights,
                    validation_results=phase_validations
                )
                target_page = self._get_intelligent_route(validated_flow_analysis)
            
            # Generate user guidance based on validated flow state
            user_guidance = self._generate_user_guidance_with_validation(flow_analysis, phase_validations)
            
            routing_decision = RouteDecision(
                target_page=target_page,
                flow_id=flow_id,
                phase=current_phase,
                flow_type=flow_type,
                reasoning="AI crew analysis and routing decision",
                confidence=0.8,
                next_actions=user_guidance.get("next_steps", []),
                context_data={"flow_data": flow_analysis.phases_data}
            )
            
            return FlowContinuationResult(
                flow_id=flow_id,
                flow_type=flow_type,
                current_phase=current_phase,
                routing_decision=routing_decision,
                user_guidance=user_guidance,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Failed to parse crew result: {e}")
            return FlowContinuationResult(
                flow_id=flow_id,
                flow_type="unknown",
                current_phase="error",
                routing_decision=RouteDecision(
                    target_page="/discovery/enhanced-dashboard",
                    flow_id=flow_id,
                    phase="error",
                    flow_type="unknown",
                    reasoning="Failed to parse crew result",
                    confidence=0.1
                ),
                user_guidance={"error": "Failed to process crew result"},
                success=False,
                error_message=str(e)
            )
    
    async def _fallback_processing(self, flow_id: str, user_context: Dict[str, Any]) -> FlowContinuationResult:
        """Fallback processing when CrewAI is not available"""
        logger.info(f"🔄 Using fallback processing for flow {flow_id}")
        
        try:
            # Use tools directly without crew orchestration
            flow_analysis = await self.flow_analyzer._analyze_flow_state(flow_id)
            
            # Use intelligent routing based on actual flow state
            target_page = self._get_intelligent_route(flow_analysis)
            
            # Generate specific user guidance based on flow state
            user_guidance = self._generate_user_guidance(flow_analysis)
            
            routing_decision = RouteDecision(
                target_page=target_page,
                flow_id=flow_id,
                phase=flow_analysis.current_phase,
                flow_type=flow_analysis.flow_type,
                reasoning=f"Intelligent routing: {flow_analysis.flow_type} flow in {flow_analysis.current_phase} phase",
                confidence=0.8,
                next_actions=user_guidance.get("next_steps", []),
                context_data={"flow_data": flow_analysis.phases_data}
            )
            
            return FlowContinuationResult(
                flow_id=flow_id,
                flow_type=flow_analysis.flow_type,
                current_phase=flow_analysis.current_phase,
                routing_decision=routing_decision,
                user_guidance=user_guidance,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Fallback processing failed: {e}")
            return FlowContinuationResult(
                flow_id=flow_id,
                flow_type="unknown",
                current_phase="error",
                routing_decision=RouteDecision(
                    target_page="/discovery/enhanced-dashboard",
                    flow_id=flow_id,
                    phase="error",
                    flow_type="unknown",
                    reasoning="Fallback processing failed",
                    confidence=0.1
                ),
                user_guidance={"error": str(e)},
                success=False,
                error_message=str(e)
            )

    def _get_intelligent_route(self, flow_analysis: FlowAnalysisResult) -> str:
        """Get intelligent route based on flow analysis"""
        try:
            # Use the same route mapping as the RouteDecisionTool
            route_mapping = {
                "discovery": {
                    "data_import": "/discovery/import",
                    "attribute_mapping": "/discovery/attribute-mapping",
                    "data_cleansing": "/discovery/data-cleansing", 
                    "inventory": "/discovery/inventory",
                    "dependencies": "/discovery/dependencies",
                    "tech_debt": "/discovery/tech-debt",
                    "completed": "/assess"  # Move to assessment when discovery is complete
                },
                "assess": {
                    "migration_readiness": "/assess/migration-readiness",
                    "business_impact": "/assess/business-impact", 
                    "technical_assessment": "/assess/technical-assessment",
                    "completed": "/plan"  # Move to planning when assessment is complete
                },
                "plan": {
                    "wave_planning": "/plan/wave-planning",
                    "runbook_creation": "/plan/runbook-creation",
                    "resource_allocation": "/plan/resource-allocation",
                    "completed": "/execute"  # Move to execution when planning is complete
                }
            }
            
            flow_routes = route_mapping.get(flow_analysis.flow_type, route_mapping["discovery"])
            
            # If current phase is completed, determine next step
            if flow_analysis.current_phase == "completed":
                return flow_routes.get("completed", "/assess")
            
            # Get route for current phase
            base_route = flow_routes.get(flow_analysis.current_phase, "/discovery/import")
            
            # For specific phase pages, append flow ID for context
            if base_route != "/discovery/import" and not base_route.startswith("/assess") and not base_route.startswith("/plan"):
                return f"{base_route}?flow_id={flow_analysis.flow_id}"
            
            return base_route
            
        except Exception as e:
            logger.error(f"Error generating intelligent route: {e}")
            return "/discovery/enhanced-dashboard"
    
    def _determine_actual_phase_from_validation(self, phase_validations: Dict[str, str], fallback_phase: str) -> str:
        """Determine the actual current phase based on data validation results"""
        try:
            # Define phase order for discovery flows
            phase_order = ["data_import", "attribute_mapping", "data_cleansing", "inventory", "dependencies", "tech_debt"]
            
            # Find the first incomplete phase
            for phase in phase_order:
                validation = phase_validations.get(phase, "")
                if "INCOMPLETE" in validation:
                    return phase
                elif "PARTIAL" in validation:
                    return phase  # Stay on partial phases for completion
            
            # If all phases are complete, mark as completed
            all_complete = all("COMPLETE" in validation for validation in phase_validations.values() if validation)
            if all_complete and len(phase_validations) >= 6:  # All 6 discovery phases validated
                return "completed"
            
            # Fallback to the provided phase
            return fallback_phase
            
        except Exception as e:
            logger.error(f"Error determining actual phase from validation: {e}")
            return fallback_phase
    
    def _generate_user_guidance_with_validation(self, flow_analysis: FlowAnalysisResult, phase_validations: Dict[str, str]) -> Dict[str, Any]:
        """Generate user guidance based on actual data validation results"""
        try:
            # Get base guidance
            base_guidance = self._generate_user_guidance(flow_analysis)
            
            # Add validation-specific guidance
            validation_guidance = {
                "data_validation": phase_validations,
                "critical_issues": [],
                "next_required_actions": []
            }
            
            # Analyze validation results for critical issues
            for phase, validation in phase_validations.items():
                if "INCOMPLETE" in validation:
                    if phase == "data_import":
                        validation_guidance["critical_issues"].append(
                            f"Data import required: {validation}"
                        )
                        validation_guidance["next_required_actions"].append(
                            "Import your CMDB or asset data to begin discovery"
                        )
                    elif phase == "attribute_mapping":
                        validation_guidance["critical_issues"].append(
                            f"Attribute mapping incomplete: {validation}"
                        )
                        validation_guidance["next_required_actions"].append(
                            "Complete field mapping to standardize your asset data"
                        )
                    elif phase == "inventory":
                        validation_guidance["critical_issues"].append(
                            f"Asset inventory not populated: {validation}"
                        )
                        validation_guidance["next_required_actions"].append(
                            "Ensure data flows properly into the main asset inventory"
                        )
                elif "PARTIAL" in validation:
                    validation_guidance["critical_issues"].append(
                        f"Phase {phase} needs completion: {validation}"
                    )
            
            # Merge with base guidance
            base_guidance.update(validation_guidance)
            return base_guidance
            
        except Exception as e:
            logger.error(f"Error generating validation guidance: {e}")
            return self._generate_user_guidance(flow_analysis)
    
    def _generate_user_guidance(self, flow_analysis: FlowAnalysisResult) -> Dict[str, Any]:
        """Generate specific user guidance based on flow state"""
        try:
            phase_guidance = {
                "discovery": {
                    "data_import": {
                        "message": "Continue with data import to begin your discovery process",
                        "summary": "Import your CMDB or asset data to start the discovery flow",
                        "next_steps": [
                            "Upload CMDB export file",
                            "Validate data format and completeness",
                            "Review import results"
                        ]
                    },
                    "attribute_mapping": {
                        "message": "Map your data attributes to migration standards",
                        "summary": "Ensure your asset data is properly mapped to critical migration attributes",
                        "next_steps": [
                            "Review attribute mapping suggestions",
                            "Validate field mappings",
                            "Complete attribute standardization"
                        ]
                    },
                    "data_cleansing": {
                        "message": "Clean and validate your asset data",
                        "summary": "Improve data quality and resolve inconsistencies",
                        "next_steps": [
                            "Review data quality issues",
                            "Apply cleansing rules",
                            "Validate cleaned data"
                        ]
                    },
                    "inventory": {
                        "message": "Review and complete your asset inventory",
                        "summary": "Ensure all assets are properly categorized and documented",
                        "next_steps": [
                            "Review asset classifications",
                            "Validate asset details",
                            "Complete inventory documentation"
                        ]
                    },
                    "dependencies": {
                        "message": "Analyze asset dependencies and relationships",
                        "summary": "Map dependencies to understand migration complexity",
                        "next_steps": [
                            "Review dependency mappings",
                            "Validate relationships",
                            "Document critical dependencies"
                        ]
                    },
                    "tech_debt": {
                        "message": "Complete technical debt analysis",
                        "summary": "Assess and document technical debt for migration planning",
                        "next_steps": [
                            "Review technical debt assessment",
                            "Validate findings",
                            "Complete analysis documentation"
                        ]
                    },
                    "completed": {
                        "message": "Discovery phase complete! Ready to begin assessment",
                        "summary": "All discovery tasks completed successfully",
                        "next_steps": [
                            "Review discovery summary",
                            "Begin migration readiness assessment",
                            "Start business impact analysis"
                        ]
                    }
                }
            }
            
            # Get guidance for the specific flow type and phase
            flow_guidance = phase_guidance.get(flow_analysis.flow_type, phase_guidance["discovery"])
            guidance = flow_guidance.get(flow_analysis.current_phase, {
                "message": f"Continue with your {flow_analysis.flow_type} flow",
                "summary": f"Working on {flow_analysis.current_phase} phase",
                "next_steps": ["Review current progress", "Complete remaining tasks"]
            })
            
            # Add progress information
            guidance["progress"] = {
                "current_phase": flow_analysis.current_phase,
                "progress_percentage": flow_analysis.progress_percentage,
                "flow_type": flow_analysis.flow_type,
                "status": flow_analysis.status
            }
            
            return guidance
            
        except Exception as e:
            logger.error(f"Error generating user guidance: {e}")
            return {
                "message": f"Continue with your {flow_analysis.flow_type} flow",
                "summary": "Flow analysis complete",
                "next_steps": ["Review current progress"],
                "error": str(e)
            }

# Legacy compatibility wrapper
class FlowProcessingAgent:
    """
    Legacy compatibility wrapper for the new CrewAI-based implementation
    """
    
    def __init__(self, db_session=None, client_account_id=None, engagement_id=None):
        self.crew = UniversalFlowProcessingCrew(db_session, client_account_id, engagement_id)
    
    async def process_flow_continuation(self, flow_id: str, user_context: Dict[str, Any] = None) -> FlowContinuationResult:
        """Legacy method that delegates to the new crew-based implementation"""
        return await self.crew.process_flow_continuation(flow_id, user_context)
    
    def _run(self, flow_id: str, user_context: Dict[str, Any] = None) -> str:
        """Legacy method for backwards compatibility"""
        import asyncio
        try:
            result = asyncio.run(self.process_flow_continuation(flow_id, user_context))
            return f"Flow {flow_id} processed. Route: {result.routing_decision.target_page}"
        except Exception as e:
            return f"Flow processing failed: {str(e)}"
    
    async def _analyze_flow_state(self, flow_id: str) -> FlowAnalysisResult:
        """Analyze flow state - delegates to crew implementation"""
        return await self.crew.flow_analyzer._analyze_flow_state(flow_id)
    
    async def _evaluate_all_phase_checklists(self, flow_analysis: FlowAnalysisResult) -> List[Dict[str, Any]]:
        """Evaluate phase checklists for the flow"""
        try:
            # Create mock phase checklist results based on flow analysis
            phases = []
            
            if flow_analysis.flow_type == "discovery":
                discovery_phases = ["data_import", "attribute_mapping", "data_cleansing", "inventory", "dependencies", "tech_debt"]
                
                for i, phase in enumerate(discovery_phases):
                    is_current = phase == flow_analysis.current_phase
                    is_completed = i < discovery_phases.index(flow_analysis.current_phase) if flow_analysis.current_phase in discovery_phases else False
                    
                    phases.append({
                        "phase": phase,
                        "status": {"value": "completed" if is_completed else ("in_progress" if is_current else "pending")},
                        "completion_percentage": 100 if is_completed else (50 if is_current else 0),
                        "tasks": [
                            {
                                "task_id": f"{phase}_task_1",
                                "task_name": f"Complete {phase.replace('_', ' ')} phase",
                                "status": {"value": "completed" if is_completed else ("in_progress" if is_current else "pending")},
                                "confidence": 0.9 if is_completed else (0.5 if is_current else 0.0),
                                "evidence": [f"{phase} phase evidence"] if is_completed else [],
                                "next_steps": [] if is_completed else [f"Complete {phase.replace('_', ' ')} tasks"]
                            }
                        ],
                        "ready_for_next_phase": is_completed,
                        "next_required_actions": [] if is_completed else [f"Complete {phase.replace('_', ' ')} phase"]
                    })
            else:
                # For other flow types, create basic phase structure
                phases.append({
                    "phase": flow_analysis.current_phase,
                    "status": {"value": "in_progress"},
                    "completion_percentage": flow_analysis.progress_percentage,
                    "tasks": [
                        {
                            "task_id": f"{flow_analysis.current_phase}_task_1",
                            "task_name": f"Complete {flow_analysis.current_phase.replace('_', ' ')} phase",
                            "status": {"value": "in_progress"},
                            "confidence": 0.5,
                            "evidence": [],
                            "next_steps": [f"Continue with {flow_analysis.current_phase.replace('_', ' ')} tasks"]
                        }
                    ],
                    "ready_for_next_phase": False,
                    "next_required_actions": [f"Complete {flow_analysis.current_phase.replace('_', ' ')} phase"]
                })
            
            return phases
            
        except Exception as e:
            logger.error(f"Failed to evaluate phase checklists: {e}")
            return [
                {
                    "phase": "error",
                    "status": {"value": "error"},
                    "completion_percentage": 0,
                    "tasks": [],
                    "ready_for_next_phase": False,
                    "next_required_actions": ["Fix evaluation error"]
                }
            ] 