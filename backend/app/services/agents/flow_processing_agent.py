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
    from crewai_tools import BaseTool
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
    """Tool for analyzing current flow state across all flow types"""
    
    name: str = "flow_state_analyzer"
    description: str = "Analyzes the current state of any flow type (Discovery, Assess, Plan, Execute, etc.) to determine progress and completion status"
    
    def __init__(self, db_session: AsyncSession = None, client_account_id: int = None, engagement_id: int = None):
        super().__init__()
        self.db = db_session
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
    
    def _run(self, flow_id: str) -> str:
        """Analyze flow state and return structured analysis"""
        try:
            # This would be called by the agent
            import asyncio
            result = asyncio.run(self._analyze_flow_state(flow_id))
            return f"Flow {flow_id} analysis: Type={result.flow_type}, Phase={result.current_phase}, Progress={result.progress_percentage}%, Status={result.status}"
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
                
                flow_handler = FlowManagementHandler(
                    db=self.db,
                    client_account_id=self.client_account_id,
                    engagement_id=self.engagement_id
                )
                
                flow_status = await flow_handler.get_flow_status(flow_id)
                
                return FlowAnalysisResult(
                    flow_id=flow_id,
                    flow_type=flow_type,
                    current_phase=flow_status.get("current_phase", "unknown"),
                    status=flow_status.get("status", "unknown"),
                    progress_percentage=flow_status.get("progress_percentage", 0),
                    phases_data=flow_status.get("phases", {}),
                    agent_insights=flow_status.get("agent_insights", []),
                    validation_results=flow_status.get("crewai_state_data", {})
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
    """Tool for validating phase completion using actual data validation APIs"""
    
    name: str = "phase_validator"
    description: str = "Validates whether phases are complete by calling validation APIs that check actual data presence and quality"
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__()
        self.base_url = base_url
        self.timeout = 10.0
    
    def _run(self, flow_id: str, phase: str) -> str:
        """Validate phase completion using validation API"""
        try:
            # Use synchronous approach for reliability
            return self._sync_validate_phase(flow_id, phase)
        except Exception as e:
            logger.error(f"Phase validation error for {phase}: {e}")
            return f"Phase {phase} validation ERROR: {str(e)}"
    
    def _sync_validate_phase(self, flow_id: str, phase: str) -> str:
        """Synchronous validation using requests instead of httpx"""
        try:
            import requests
            # Use default client context for agent requests
            headers = {
                "Content-Type": "application/json",
                "X-Client-Account-Id": "dfea7406-1575-4348-a0b2-2770cbe2d9f9",
                "X-Engagement-Id": "ce27e7b1-2ac6-4b74-8dd5-b52d542a1669"
            }
            response = requests.get(
                f"{self.base_url}/api/v1/flow-processing/validate-phase/{flow_id}/{phase}",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "UNKNOWN")
                message = data.get("message", "No details available")
                complete = data.get("complete", False)
                validation_data = data.get("data", {})
                
                # Return detailed validation result
                result = f"Phase {phase} is {status}: {message} (Complete: {complete})"
                if validation_data:
                    result += f" | Data: {validation_data}"
                return result
            else:
                return f"Phase {phase} validation FAILED: API error {response.status_code}"
                
        except Exception as e:
            return f"Phase {phase} validation ERROR: {str(e)}"
    
    async def _async_validate_phase(self, flow_id: str, phase: str) -> str:
        """Async validation using API endpoint"""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/flow-processing/validate-phase/{flow_id}/{phase}",
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "UNKNOWN")
                    message = data.get("message", "No details available")
                    complete = data.get("complete", False)
                    validation_data = data.get("data", {})
                    
                    # Return detailed validation result
                    result = f"Phase {phase} is {status}: {message} (Complete: {complete})"
                    if validation_data:
                        result += f" | Data: {validation_data}"
                    return result
                else:
                    return f"Phase {phase} validation FAILED: API error {response.status_code}"
                    
        except Exception as e:
            return f"Phase {phase} validation ERROR: {str(e)}"

class FlowValidationTool(BaseTool):
    """Tool for fast fail-first flow validation to find the current incomplete phase"""
    
    name: str = "flow_validator"
    description: str = "Performs fast fail-first validation to identify the first incomplete phase that needs attention"
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__()
        self.base_url = base_url
        self.timeout = 10.0
    
    def _run(self, flow_id: str) -> str:
        """Validate flow and return first incomplete phase"""
        try:
            # Use synchronous approach for reliability
            return self._sync_validate_flow(flow_id)
        except Exception as e:
            logger.error(f"Flow validation error for {flow_id}: {e}")
            return f"Flow {flow_id} validation ERROR: {str(e)}"
    
    def _sync_validate_flow(self, flow_id: str) -> str:
        """Synchronous flow validation using requests"""
        try:
            import requests
            # Use default client context for agent requests
            headers = {
                "Content-Type": "application/json",
                "X-Client-Account-Id": "dfea7406-1575-4348-a0b2-2770cbe2d9f9",
                "X-Engagement-Id": "ce27e7b1-2ac6-4b74-8dd5-b52d542a1669"
            }
            response = requests.get(
                f"{self.base_url}/api/v1/flow-processing/validate-flow/{flow_id}",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                current_phase = data.get("current_phase", "unknown")
                status = data.get("status", "UNKNOWN")
                next_action = data.get("next_action", "Continue with discovery")
                route_to = data.get("route_to", "/discovery/enhanced-dashboard")
                fail_fast = data.get("fail_fast", False)
                
                result = f"Flow {flow_id}: CurrentPhase={current_phase}, Status={status}, NextAction={next_action}, Route={route_to}"
                if fail_fast:
                    result += " | FailFast=True (stopped at first incomplete phase)"
                return result
            else:
                return f"Flow {flow_id} validation FAILED: API error {response.status_code}"
                
        except Exception as e:
            return f"Flow {flow_id} validation ERROR: {str(e)}"
    
    async def _async_validate_flow(self, flow_id: str) -> str:
        """Async flow validation using API endpoint"""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/flow-processing/validate-flow/{flow_id}",
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    current_phase = data.get("current_phase", "unknown")
                    status = data.get("status", "UNKNOWN")
                    next_action = data.get("next_action", "Continue with discovery")
                    route_to = data.get("route_to", "/discovery/enhanced-dashboard")
                    fail_fast = data.get("fail_fast", False)
                    
                    result = f"Flow {flow_id}: CurrentPhase={current_phase}, Status={status}, NextAction={next_action}, Route={route_to}"
                    if fail_fast:
                        result += " | FailFast=True (stopped at first incomplete phase)"
                    return result
                else:
                    return f"Flow {flow_id} validation FAILED: API error {response.status_code}"
                    
        except Exception as e:
            return f"Flow {flow_id} validation ERROR: {str(e)}"

class RouteDecisionTool(BaseTool):
    """Tool for making intelligent routing decisions"""
    
    name: str = "route_decision_maker"
    description: str = "Makes intelligent routing decisions based on flow analysis and phase validation results"
    
    # Route mapping for all flow types
    ROUTE_MAPPING = {
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
    
    def __init__(self, db_session: AsyncSession = None, client_account_id: int = None, engagement_id: int = None):
        self.db = db_session
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        
        # Initialize tools
        self.flow_analyzer = FlowStateAnalysisTool(db_session, client_account_id, engagement_id)
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
            memory=True,
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
            memory=True,
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
            memory=True,
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
            memory=True
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
            description=f"""Use the flow_validator tool to perform fast fail-first validation on flow {flow_id}.
            
            The flow validator will:
            1. Check all phases sequentially (data_import, attribute_mapping, data_cleansing, inventory, dependencies, tech_debt)
            2. Stop at the FIRST incomplete phase (fail-fast approach)
            3. Return the current phase that needs attention
            4. Provide specific validation criteria and data counts
            
            Then use the phase_validator tool to get detailed validation information for the identified phase.
            
            Determine:
            - Which phase is the current bottleneck
            - What specific criteria are not met
            - What data is missing or incomplete
            - Whether the phase can be considered complete
            
            Provide a clear assessment of what needs to be completed before advancing.
            """,
            agent=self.phase_validator_agent,
            expected_output="Detailed validation result with current incomplete phase, specific criteria not met, and required actions",
            context=[analysis_task]
        )
        
        # Task 3: Route Decision
        routing_task = Task(
            description="""Based on the flow analysis and phase validation, make an intelligent routing decision.
            
            Determine:
            1. Where the user should be directed next
            2. What specific page or section they need
            3. What actions they should take
            4. How to provide clear guidance
            5. What context should be passed along
            
            Make the optimal routing decision that will help the user make progress efficiently.
            """,
            agent=self.route_strategist,
            expected_output="Routing decision with target page, reasoning, confidence level, and user guidance",
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