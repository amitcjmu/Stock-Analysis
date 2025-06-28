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
from typing import Dict, List, Any, Optional, ClassVar
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
        name: str = "fallback_tool"
        description: str = "Fallback tool when CrewAI not available"
        
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
        
        def _run(self, *args, **kwargs):
            return "CrewAI not available - using fallback"

# Import LLM configuration
try:
    from app.services.llm_config import get_crewai_llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    def get_crewai_llm():
        return None

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
    """Tool for analyzing current flow state across all flow types using API calls"""
    
    name: str = "flow_state_analyzer"
    description: str = "Analyzes the current state of any flow type (Discovery, Assess, Plan, Execute, etc.) to determine progress and completion status using API validation endpoints"
    
    # API-based tool - no database access needed
    base_url: str = "http://127.0.0.1:8000"  # Use 127.0.0.1 for internal container calls
    timeout: float = 30.0  # Increased timeout for complex validations
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000", **kwargs):
        super().__init__(**kwargs)
        self.base_url = base_url
        self.timeout = 30.0
    
    def _run(self, flow_id: str) -> str:
        """Analyze flow state using API calls and return structured analysis"""
        try:
            # Use API calls to get flow status instead of direct database access
            result = self._get_flow_status_via_api(flow_id)
            return f"Flow {flow_id} analysis: Type={result['flow_type']}, Phase={result['current_phase']}, Progress={result['progress_percentage']}%, Status={result['status']}"
        except Exception as e:
            logger.error(f"Flow state analysis failed for {flow_id}: {e}")
            return f"Error analyzing flow {flow_id}: {str(e)}"
    
    def _get_flow_status_via_api(self, flow_id: str) -> dict:
        """Get flow status using real service calls to provide actionable insights"""
        try:
            # Call the actual flow management service to get real status
            from app.api.v1.discovery_handlers.flow_management import FlowManagementHandler
            from app.core.context import RequestContext
            from app.core.database import AsyncSessionLocal
            import asyncio
            
            # Create context for service calls
            context = RequestContext(
                client_account_id="dfea7406-1575-4348-a0b2-2770cbe2d9f9",
                engagement_id="ce27e7b1-2ac6-4b74-8dd5-b52d542a1669",
                user_id=None,
                session_id=None
            )
            
            # Use a thread to run async call safely
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self._get_real_flow_status(flow_id, context))
                result = future.result(timeout=30)
                return result
                
        except Exception as e:
            logger.error(f"Failed to get real flow status for {flow_id}: {e}")
            # Return error status with actionable guidance
            return {
                "flow_type": "discovery",
                "current_phase": "data_import",
                "status": "error",
                "progress_percentage": 0,
                "phases_data": {},
                "agent_insights": [],
                "validation_results": {},
                "error_message": f"Failed to get flow status: {str(e)}",
                "actionable_guidance": "Please check system logs and retry the flow processing"
            }
    
    async def _get_real_flow_status(self, flow_id: str, context: "RequestContext") -> dict:
        """Get real flow status with detailed analysis"""
        try:
            from app.api.v1.discovery_handlers.flow_management import FlowManagementHandler
            from app.core.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as session:
                handler = FlowManagementHandler(session, context)
                flow_response = await handler.get_flow_status(flow_id)
                
                # Analyze the real status to provide actionable insights
                current_phase = flow_response.get("current_phase", "data_import")
                progress = flow_response.get("progress_percentage", 0)
                phases = flow_response.get("phases", {})
                
                # Determine what specifically failed or needs attention
                actionable_insights = []
                specific_issues = []
                
                if current_phase == "data_import" and progress == 0:
                    # Check if there's actual data
                    raw_data = flow_response.get("raw_data", [])
                    field_mapping = flow_response.get("field_mapping", {})
                    
                    if not raw_data:
                        specific_issues.append("No data has been imported yet")
                        actionable_insights.append("User needs to upload a data file first")
                    elif len(raw_data) < 5:
                        specific_issues.append(f"Only {len(raw_data)} records imported - insufficient for analysis")
                        actionable_insights.append("User should upload a file with more data records")
                    else:
                        specific_issues.append("Data imported but not processed through validation")
                        actionable_insights.append("System should trigger data validation and processing")
                
                # Convert to format expected by agent
                return {
                    "flow_type": "discovery",
                    "current_phase": current_phase,
                    "status": flow_response.get("status", "active"),
                    "progress_percentage": progress,
                    "phases_data": phases,
                    "agent_insights": flow_response.get("agent_insights", []),
                    "validation_results": flow_response.get("validation_results", {}),
                    "raw_data_count": len(flow_response.get("raw_data", [])),
                    "field_mapping_status": "configured" if flow_response.get("field_mapping") else "pending",
                    "specific_issues": specific_issues,
                    "actionable_insights": actionable_insights,
                    "data_import_id": flow_response.get("data_import_id"),
                    "created_at": flow_response.get("created_at"),
                    "updated_at": flow_response.get("updated_at")
                }
        except Exception as e:
            logger.error(f"Real flow status failed for {flow_id}: {e}")
            raise
    
    def _determine_flow_type_via_api(self, flow_id: str) -> str:
        """Determine flow type using API calls instead of database queries"""
        try:
            import requests
            
            # Use default client context for agent requests
            headers = {
                "Content-Type": "application/json",
                "X-Client-Account-Id": "dfea7406-1575-4348-a0b2-2770cbe2d9f9",
                "X-Engagement-Id": "ce27e7b1-2ac6-4b74-8dd5-b52d542a1669"
            }
            
            # Try discovery flows first
            try:
                response = requests.get(
                    f"{self.base_url}/api/v1/discovery/flows",
                    headers=headers,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    flows = response.json()
                    for flow in flows:
                        if flow.get("flow_id") == flow_id or flow.get("id") == flow_id:
                            return "discovery"
            except Exception:
                pass
            
            # For now, default to discovery since that's the primary flow type
            # In the future, this could check other flow type APIs
            return "discovery"
            
        except Exception as e:
            logger.error(f"Failed to determine flow type via API for {flow_id}: {e}")
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
    """Tool for validating phase completion using actual data validation APIs"""
    
    name: str = "phase_validator"
    description: str = "Validates whether phases are complete by calling validation APIs that check actual data presence and quality"
    
    # Define fields for Pydantic compatibility
    base_url: str = "http://127.0.0.1:8000"
    timeout: float = 30.0
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000", **kwargs):
        super().__init__(**kwargs)
        self.base_url = base_url
        self.timeout = 30.0
    
    def _run(self, flow_id: str, phase: str) -> str:
        """Validate phase completion using validation API"""
        try:
            # Use synchronous approach for reliability
            return self._sync_validate_phase(flow_id, phase)
        except Exception as e:
            logger.error(f"Phase validation error for {phase}: {e}")
            return f"Phase {phase} validation ERROR: {str(e)}"
    
    def _sync_validate_phase(self, flow_id: str, phase: str) -> str:
        """Validate phase using real validation services to provide actionable guidance"""
        try:
            # Call the actual phase validation endpoint
            from app.api.v1.endpoints.flow_processing import validate_phase_data
            from app.core.context import RequestContext
            from app.core.database import AsyncSessionLocal
            import asyncio
            
            # Create context for service calls
            context = RequestContext(
                client_account_id="dfea7406-1575-4348-a0b2-2770cbe2d9f9",
                engagement_id="ce27e7b1-2ac6-4b74-8dd5-b52d542a1669",
                user_id=None,
                session_id=None
            )
            
            # Use a thread to run async call safely
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self._validate_phase_real(flow_id, phase, context))
                result = future.result(timeout=30)
                return result
                
        except Exception as e:
            logger.error(f"Phase validation failed for {flow_id}/{phase}: {e}")
            return f"Phase {phase} validation ERROR: {str(e)} - Please check system status and retry"
    
    async def _validate_phase_real(self, flow_id: str, phase: str, context: "RequestContext") -> str:
        """Use real validation service to check phase completion"""
        try:
            from app.api.v1.endpoints.flow_processing import validate_phase_data
            from app.core.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as session:
                # Call the actual validation function
                validation_result = await validate_phase_data(flow_id, phase, session, context)
                
                status = validation_result.get("status", "UNKNOWN")
                message = validation_result.get("message", "No details available")
                complete = validation_result.get("complete", False)
                data = validation_result.get("data", {})
                
                # Provide specific actionable guidance based on phase and validation results
                actionable_guidance = []
                
                if phase == "data_import" and not complete:
                    import_sessions = data.get("import_sessions", 0)
                    raw_records = data.get("raw_records", 0)
                    threshold_met = data.get("threshold_met", False)
                    
                    if import_sessions == 0:
                        actionable_guidance.append("No data files have been uploaded yet")
                        actionable_guidance.append("ACTION: User needs to upload a data file using the Data Import page")
                        actionable_guidance.append("ROUTE: /discovery/data-import")
                    elif raw_records < 5:
                        actionable_guidance.append(f"Only {raw_records} records imported - insufficient for analysis")
                        actionable_guidance.append("ACTION: User needs to upload a larger data file with more records")
                        actionable_guidance.append("ROUTE: /discovery/data-import")
                    else:
                        actionable_guidance.append(f"Data imported ({raw_records} records) but processing incomplete")
                        actionable_guidance.append("ACTION: System should trigger background processing of imported data")
                        actionable_guidance.append("INTERNAL: Re-trigger data import processing workflow")
                
                elif phase == "attribute_mapping" and not complete:
                    approved_mappings = data.get("approved_mappings", 0)
                    high_confidence = data.get("high_confidence_mappings", 0)
                    
                    if approved_mappings == 0:
                        actionable_guidance.append("No field mappings have been configured")
                        actionable_guidance.append("ACTION: User needs to configure field mappings")
                        actionable_guidance.append("ROUTE: /discovery/attribute-mapping")
                    else:
                        actionable_guidance.append(f"Only {approved_mappings} mappings approved - need more for completion")
                        actionable_guidance.append("ACTION: User needs to review and approve more field mappings")
                        actionable_guidance.append("ROUTE: /discovery/attribute-mapping")
                
                # Format comprehensive result with actionable guidance
                result = f"Phase {phase} is {status}: {message} (Complete: {complete})"
                result += f" | Data: {data}"
                if actionable_guidance:
                    result += f" | ACTIONABLE_GUIDANCE: {'; '.join(actionable_guidance)}"
                
                return result
                
        except Exception as e:
            logger.error(f"Real phase validation failed for {flow_id}/{phase}: {e}")
            return f"Phase {phase} validation ERROR: {str(e)} - System unable to validate phase completion"

class FlowValidationTool(BaseTool):
    """Tool for fast fail-first flow validation to find the current incomplete phase"""
    
    name: str = "flow_validator"
    description: str = "Performs fast fail-first validation to identify the first incomplete phase that needs attention"
    
    # Define fields for Pydantic compatibility
    base_url: str = "http://127.0.0.1:8000"
    timeout: float = 30.0
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000", **kwargs):
        super().__init__(**kwargs)
        self.base_url = base_url
        self.timeout = 30.0
    
    def _run(self, flow_id: str) -> str:
        """Validate flow and return first incomplete phase"""
        try:
            # Use synchronous approach for reliability
            return self._sync_validate_flow(flow_id)
        except Exception as e:
            logger.error(f"Flow validation error for {flow_id}: {e}")
            return f"Flow {flow_id} validation ERROR: {str(e)}"
    
    def _sync_validate_flow(self, flow_id: str) -> str:
        """Flow validation using real validation services with actionable guidance"""
        try:
            # Call the actual flow validation endpoint
            from app.api.v1.endpoints.flow_processing import validate_flow_phases
            from app.core.context import RequestContext
            from app.core.database import AsyncSessionLocal
            import asyncio
            
            # Create context for service calls
            context = RequestContext(
                client_account_id="dfea7406-1575-4348-a0b2-2770cbe2d9f9",
                engagement_id="ce27e7b1-2ac6-4b74-8dd5-b52d542a1669",
                user_id=None,
                session_id=None
            )
            
            # Use a thread to run async call safely
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self._validate_flow_real(flow_id, context))
                result = future.result(timeout=30)
                return result
                
        except Exception as e:
            logger.error(f"Flow validation failed for {flow_id}: {e}")
            return f"Flow {flow_id} validation ERROR: {str(e)} - Please check system status and retry"
    
    async def _validate_flow_real(self, flow_id: str, context: "RequestContext") -> str:
        """Use real validation service to check flow completion with actionable guidance"""
        try:
            from app.api.v1.endpoints.flow_processing import validate_flow_phases
            from app.core.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as session:
                # Call the actual validation function
                validation_result = await validate_flow_phases(flow_id, session, context)
                
                current_phase = validation_result.get("current_phase", "unknown")
                status = validation_result.get("status", "UNKNOWN")
                next_action = validation_result.get("next_action", "Unknown action required")
                route_to = validation_result.get("route_to", "/discovery/enhanced-dashboard")
                validation_details = validation_result.get("validation_details", {})
                
                # Build actionable guidance based on validation details
                actionable_guidance = []
                
                if current_phase == "data_import" and status == "INCOMPLETE":
                    data = validation_details.get("data", {})
                    import_sessions = data.get("import_sessions", 0)
                    raw_records = data.get("raw_records", 0)
                    
                    if import_sessions == 0:
                        actionable_guidance.append("ISSUE: No data has been uploaded")
                        actionable_guidance.append("USER_ACTION: Upload a data file via Data Import page")
                        actionable_guidance.append("SYSTEM_ACTION: Navigate user to data import")
                    elif raw_records < 5:
                        actionable_guidance.append(f"ISSUE: Insufficient data ({raw_records} records)")
                        actionable_guidance.append("USER_ACTION: Upload a larger data file with more records")
                        actionable_guidance.append("SYSTEM_ACTION: Guide user to upload better data")
                    else:
                        actionable_guidance.append(f"ISSUE: Data uploaded ({raw_records} records) but processing incomplete")
                        actionable_guidance.append("USER_ACTION: No user action required")
                        actionable_guidance.append("SYSTEM_ACTION: Trigger background data processing")
                
                # Format comprehensive result with fail-fast approach
                result = f"Flow {flow_id}: CurrentPhase={current_phase}, Status={status}, NextAction={next_action}, Route={route_to}"
                result += " | FailFast=True (stopped at first incomplete phase)"
                
                if actionable_guidance:
                    result += f" | ACTIONABLE_GUIDANCE: {'; '.join(actionable_guidance)}"
                
                return result
                
        except Exception as e:
            logger.error(f"Real flow validation failed for {flow_id}: {e}")
            return f"Flow {flow_id} validation ERROR: {str(e)} - System unable to validate flow completion"

class RouteDecisionTool(BaseTool):
    """Tool for making intelligent routing decisions"""
    
    name: str = "route_decision_maker"
    description: str = "Makes intelligent routing decisions based on flow analysis and phase validation results"
    
    # Route mapping for all flow types - ClassVar to avoid Pydantic field annotation requirement
    ROUTE_MAPPING: ClassVar[Dict[str, Dict[str, str]]] = {
        "discovery": {
            "data_import": "/discovery/import",
            "attribute_mapping": "/discovery/attribute-mapping",
            "data_cleansing": "/discovery/data-cleansing", 
            "inventory": "/discovery/inventory",
            "dependencies": "/discovery/dependencies",
            "tech_debt": "/discovery/tech-debt",
            "completed": "/discovery/tech-debt"
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
        """Make intelligent routing decision based on actionable guidance"""
        try:
            # Parse inputs to extract actionable guidance
            flow_type = self._extract_flow_type(flow_analysis)
            current_phase = self._extract_current_phase(flow_analysis)
            flow_id = self._extract_flow_id(flow_analysis)
            
            # Extract actionable guidance from validation results
            actionable_guidance = self._extract_actionable_guidance(validation_result)
            
            # Determine if this requires user action or system action
            user_actions = [g for g in actionable_guidance if "USER_ACTION:" in g]
            system_actions = [g for g in actionable_guidance if "SYSTEM_ACTION:" in g]
            issues = [g for g in actionable_guidance if "ISSUE:" in g]
            
            # Make intelligent routing decision
            if user_actions:
                # User action required - route to appropriate page
                target_page = self._determine_user_action_route(current_phase, user_actions, flow_id)
                reasoning = f"User action required: {'; '.join(user_actions)}"
                confidence = 0.9
            elif system_actions:
                # System action required - trigger internal processing
                target_page = self._determine_system_action_route(current_phase, system_actions, flow_id)
                reasoning = f"System action required: {'; '.join(system_actions)}"
                confidence = 0.8
            else:
                # Default routing based on phase completion
                is_complete = "COMPLETE" in validation_result
                routes = self.ROUTE_MAPPING.get(flow_type, {})
                
                if is_complete:
                    next_phase = self._get_next_phase(flow_type, current_phase)
                    target_page = routes.get(next_phase, routes.get("completed", "/"))
                    reasoning = f"Phase {current_phase} complete - advancing to {next_phase}"
                else:
                    target_page = routes.get(current_phase, "/")
                    reasoning = f"Phase {current_phase} incomplete - staying in current phase"
                
                confidence = 0.7
            
            # Include specific issues in reasoning
            if issues:
                reasoning += f" | Issues: {'; '.join(issues)}"
            
            return f"ROUTE: {target_page} | REASONING: {reasoning} | CONFIDENCE: {confidence}"
            
        except Exception as e:
            return f"Error making routing decision: {str(e)}"
    
    def _extract_actionable_guidance(self, validation_result: str) -> List[str]:
        """Extract actionable guidance from validation result"""
        if "ACTIONABLE_GUIDANCE:" in validation_result:
            guidance_part = validation_result.split("ACTIONABLE_GUIDANCE:")[1]
            return [g.strip() for g in guidance_part.split(";") if g.strip()]
        return []
    
    def _determine_user_action_route(self, current_phase: str, user_actions: List[str], flow_id: str) -> str:
        """Determine route based on required user actions"""
        # Check if user needs to upload data
        if any("upload" in action.lower() for action in user_actions):
            return "/discovery/data-import"
        
        # Check if user needs to configure mappings
        if any("mapping" in action.lower() for action in user_actions):
            return f"/discovery/attribute-mapping?flow_id={flow_id}"
        
        # Check if user needs to review something
        if any("review" in action.lower() for action in user_actions):
            return f"/discovery/{current_phase.replace('_', '-')}?flow_id={flow_id}"
        
        # Default to current phase page
        return f"/discovery/{current_phase.replace('_', '-')}?flow_id={flow_id}"
    
    def _determine_system_action_route(self, current_phase: str, system_actions: List[str], flow_id: str) -> str:
        """Determine route for system actions (usually stay on current page while processing)"""
        # For system actions, usually stay on enhanced dashboard to show processing
        if any("trigger" in action.lower() or "process" in action.lower() for action in system_actions):
            return f"/discovery/enhanced-dashboard?flow_id={flow_id}&action=processing"
        
        # For navigation actions, go to the specified page
        if any("navigate" in action.lower() for action in system_actions):
            return f"/discovery/{current_phase.replace('_', '-')}?flow_id={flow_id}"
        
        # Default to enhanced dashboard
        return f"/discovery/enhanced-dashboard?flow_id={flow_id}"
    
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
    
    def __init__(self, db_session: AsyncSession = None, client_account_id: int = None, engagement_id: int = None):
        # Store parameters for backward compatibility, but tools use APIs instead of direct DB access
        self.db = db_session
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        
        # Initialize API-based tools (no database dependencies)
        self.flow_analyzer = FlowStateAnalysisTool()
        self.phase_validator = PhaseValidationTool()
        self.flow_validator = FlowValidationTool()
        self.route_decider = RouteDecisionTool()
        
        # Create agents
        self._create_agents()
        
        # Create crew
        self._create_crew()
    
    def _create_agents(self):
        """Create specialized CrewAI agents following documentation patterns"""
        
        # Get LLM for agents
        llm = get_crewai_llm() if LLM_AVAILABLE else None
        
        # Flow Analysis Agent
        self.flow_analyst = Agent(
            role="Flow State Analyst",
            goal="Analyze the current state and progress of any migration flow type to understand what has been completed and what needs to be done next",
            backstory="""You are an expert migration flow analyst with deep knowledge of all migration phases across Discovery, Assessment, Planning, Execution, Modernization, FinOps, Observability, and Decommission workflows. 
            
            You have years of experience analyzing complex migration projects and can quickly assess the current state of any flow, identify completed tasks, and determine what needs attention. You understand the nuances of different flow types and their unique requirements.
            
            Your analytical skills help teams understand exactly where they are in their migration journey and what the next logical steps should be.""",
            tools=[self.flow_analyzer],
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            memory=False,  # DISABLE MEMORY - Prevents APIStatusError
            llm=llm
        )
        
        # Phase Validation Agent  
        self.phase_validator_agent = Agent(
            role="Phase Completion Validator",
            goal="Validate whether migration phases are truly complete and meet all required criteria before allowing progression to the next phase",
            backstory="""You are a meticulous quality assurance specialist for migration projects. Your role is critical - you ensure that no phase is marked complete unless it truly meets all the necessary criteria.
            
            You have extensive experience with migration best practices and understand that rushing through phases or marking them complete prematurely can lead to serious issues downstream. You carefully examine evidence of completion and apply rigorous validation criteria.
            
            Teams rely on your thorough validation to ensure their migration foundation is solid before moving forward. You prevent costly mistakes by catching incomplete work early.""",
            tools=[self.phase_validator, self.flow_validator],
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            memory=False,  # DISABLE MEMORY - Prevents APIStatusError
            llm=llm
        )
        
        # Route Decision Agent
        self.route_strategist = Agent(
            role="Flow Navigation Strategist", 
            goal="Make intelligent routing decisions to guide users to the exact right place in their migration flow based on current state and validation results",
            backstory="""You are a strategic navigation expert who specializes in guiding teams through complex migration workflows. You understand the intricate relationships between different phases and know exactly where to direct teams based on their current situation.
            
            Your deep knowledge of user experience and workflow optimization helps you make routing decisions that minimize confusion and maximize productivity. You consider not just what needs to be done, but the most efficient and logical way to guide users there.
            
            Teams trust your routing decisions because you always consider the bigger picture and ensure they're directed to the most appropriate next step in their migration journey.""",
            tools=[self.route_decider],
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            memory=False,  # DISABLE MEMORY - Prevents APIStatusError
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
            verbose=True,
            memory=False  # DISABLE MEMORY - Prevents APIStatusError
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
            return self._parse_crew_result(result, flow_id)
            
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
            description=f"""Analyze the current state of flow {flow_id}. 
            
            Determine:
            1. What type of flow this is (Discovery, Assess, Plan, Execute, etc.)
            2. What phase the flow is currently in
            3. What progress has been made
            4. What data and insights are available
            5. What the current status indicates
            
            Provide a comprehensive analysis of where this flow stands and what has been accomplished so far.
            
            Flow ID: {flow_id}
            User Context: {user_context}
            """,
            agent=self.flow_analyst,
            expected_output="Detailed flow state analysis including flow type, current phase, progress percentage, and available data"
        )
        
        # Task 2: Phase Validation
        validation_task = Task(
            description=f"""Use the flow_validator tool to perform comprehensive validation on flow {flow_id}.
            
            The flow validator will:
            1. Check all phases sequentially (data_import, attribute_mapping, data_cleansing, inventory, dependencies, tech_debt)
            2. Stop at the FIRST incomplete phase (fail-fast approach)
            3. Return detailed validation with specific data counts and issues
            4. Provide ACTIONABLE GUIDANCE distinguishing between:
               - USER_ACTION: What the user needs to do (upload data, configure mappings, etc.)
               - SYSTEM_ACTION: What the system needs to do internally (trigger processing, etc.)
               - ISSUE: Specific problems identified
            
            Then use the phase_validator tool to get detailed validation for the identified incomplete phase.
            
            Your job is to:
            - Identify exactly what failed or is incomplete
            - Determine if this requires user action or system action
            - Provide specific, actionable guidance about what needs to be done
            - Distinguish between things the user can control vs. system-level issues
            
            DO NOT tell users to "ensure something is completed" - instead identify:
            - If they need to upload data → route them to data import
            - If they need to configure mappings → route them to attribute mapping  
            - If system processing failed → trigger system actions internally
            """,
            agent=self.phase_validator_agent,
            expected_output="Detailed validation with specific actionable guidance distinguishing user actions from system actions",
            context=[analysis_task]
        )
        
        # Task 3: Route Decision
        routing_task = Task(
            description="""Based on the flow analysis and phase validation, make an intelligent routing decision that provides ACTIONABLE USER GUIDANCE.
            
            Your routing decision must:
            1. Parse the actionable guidance from validation results
            2. Distinguish between user actions and system actions
            3. Route users to pages where they can actually take action
            4. Trigger system processes when needed (not user responsibility)
            5. Provide clear, specific guidance about what the user should do
            
            ROUTING LOGIC:
            - If user needs to upload data → route to /discovery/data-import
            - If user needs to configure mappings → route to /discovery/attribute-mapping
            - If system needs to process data → stay on enhanced dashboard with processing indicator
            - If phase is truly complete → advance to next phase
            
            USER GUIDANCE PRINCIPLES:
            - Never tell users to "ensure completion" of something they can't control
            - Always provide specific, actionable steps
            - Route them to pages where they can actually take the required action
            - For system issues, explain that background processing is needed
            
            Provide clear reasoning about why this route was chosen and what the user should expect.
            """,
            agent=self.route_strategist,
            expected_output="Routing decision with specific user guidance and clear distinction between user vs system responsibilities",
            context=[analysis_task, validation_task]
        )
        
        return [analysis_task, validation_task, routing_task]
    
    def _parse_crew_result(self, crew_result, flow_id: str) -> FlowContinuationResult:
        """Parse crew execution result into structured response"""
        try:
            # In a real implementation, this would parse the structured crew output
            # For now, we'll create a basic response structure
            
            result_text = str(crew_result.get("result", "")) if isinstance(crew_result, dict) else str(crew_result)
            
            # Extract key information (simplified parsing)
            flow_type = "discovery"  # Default
            current_phase = "data_import"  # Default
            target_page = "/discovery/enhanced-dashboard"  # Default
            
            # Try to extract actual values from result
            if "Type=" in result_text:
                flow_type = result_text.split("Type=")[1].split(",")[0] if "," in result_text.split("Type=")[1] else result_text.split("Type=")[1].split(" ")[0]
            
            if "Phase=" in result_text:
                current_phase = result_text.split("Phase=")[1].split(",")[0] if "," in result_text.split("Phase=")[1] else result_text.split("Phase=")[1].split(" ")[0]
            
            if "ROUTE:" in result_text:
                target_page = result_text.split("ROUTE:")[1].split("|")[0].strip() if "|" in result_text.split("ROUTE:")[1] else result_text.split("ROUTE:")[1].strip()
            
            routing_decision = RouteDecision(
                target_page=target_page,
                flow_id=flow_id,
                phase=current_phase,
                flow_type=flow_type,
                reasoning="AI crew analysis and routing decision",
                confidence=0.8
            )
            
            return FlowContinuationResult(
                flow_id=flow_id,
                flow_type=flow_type,
                current_phase=current_phase,
                routing_decision=routing_decision,
                user_guidance={
                    "message": f"Continue with your {flow_type} flow",
                    "phase": current_phase,
                    "crew_analysis": result_text
                },
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
            
            routing_decision = RouteDecision(
                target_page=f"/discovery/enhanced-dashboard",
                flow_id=flow_id,
                phase=flow_analysis.current_phase,
                flow_type=flow_analysis.flow_type,
                reasoning="Fallback processing - CrewAI not available",
                confidence=0.6
            )
            
            return FlowContinuationResult(
                flow_id=flow_id,
                flow_type=flow_analysis.flow_type,
                current_phase=flow_analysis.current_phase,
                routing_decision=routing_decision,
                user_guidance={
                    "message": f"Continue with your {flow_analysis.flow_type} flow",
                    "phase": flow_analysis.current_phase,
                    "fallback_mode": True
                },
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