"""
Universal Flow Processing Crew

This module implements the CrewAI crew for intelligent flow continuation
and routing across all flow types (Discovery, Assess, Plan, Execute, etc.).
"""

import logging
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from .crewai_imports import (
    CREWAI_AVAILABLE,
    LLM_AVAILABLE,
    Agent,
    Crew,
    Process,
    Task,
    get_crewai_llm,
)
from .models import FlowContinuationResult, RouteDecision
from .tools import (
    FlowStateAnalysisTool,
    FlowValidationTool,
    PhaseValidationTool,
    RouteDecisionTool,
)

logger = logging.getLogger(__name__)


class UniversalFlowProcessingCrew:
    """
    Universal Flow Processing Crew - Proper CrewAI Implementation

    This crew handles flow continuation requests across ALL flow types using
    proper CrewAI patterns with specialized agents, tasks, and tools.
    """

    def __init__(
        self,
        db_session: AsyncSession = None,
        client_account_id: int = None,
        engagement_id: int = None,
    ):
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
        from app.core.env_flags import is_truthy_env

        enable_memory = is_truthy_env("CREWAI_ENABLE_MEMORY", default=False)

        self.flow_analyst = Agent(
            role="Flow State Analyst",
            goal=(
                "Analyze the current state and progress of any migration flow type "
                "to identify what is complete and what should happen next"
            ),
            backstory=(
                "You analyze complex migration projects across Discovery, Assessment, "
                "Planning, Execution, Modernization, FinOps, Observability, and Decommission. "
                "You quickly assess current state, identify completed tasks, and determine "
                "the next actions with awareness of each flow's nuances."
            ),
            tools=[self.flow_analyzer],
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            memory=enable_memory,
            llm=llm,
        )

        # Phase Validation Agent
        self.phase_validator_agent = Agent(
            role="Phase Completion Validator",
            goal=(
                "Validate that phases truly meet required criteria before allowing "
                "progression to the next phase"
            ),
            backstory=(
                "You are a meticulous QA specialist who prevents premature phase "
                "completion by applying rigorous validation criteria grounded in "
                "migration best practices."
            ),
            tools=[self.phase_validator, self.flow_validator],
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            memory=enable_memory,
            llm=llm,
        )

        # Route Decision Agent
        self.route_strategist = Agent(
            role="Flow Navigation Strategist",
            goal=(
                "Route users to the most appropriate next step based on current "
                "state and validation results"
            ),
            backstory=(
                "You guide teams through complex workflows by understanding phase "
                "relationships and user experience, minimizing confusion and "
                "maximizing productivity."
            ),
            tools=[self.route_decider],
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            memory=enable_memory,
            llm=llm,
        )

    def _create_crew(self):
        """Create the CrewAI crew with proper task orchestration"""
        if not CREWAI_AVAILABLE:
            logger.warning("CrewAI not available, using fallback implementation")
            self.crew = None
            return

        from app.core.env_flags import is_truthy_env

        enable_memory = is_truthy_env("CREWAI_ENABLE_MEMORY", default=False)
        self.crew = Crew(
            agents=[
                self.flow_analyst,
                self.phase_validator_agent,
                self.route_strategist,
            ],
            tasks=[],  # Tasks will be created dynamically
            process=Process.sequential,
            verbose=True,
            memory=enable_memory,
        )

    async def process_flow_continuation(
        self, flow_id: str, user_context: Dict[str, Any] = None
    ) -> FlowContinuationResult:
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
            result = self.crew.kickoff(
                {"flow_id": flow_id, "user_context": user_context or {}}
            )

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
                    confidence=0.1,
                ),
                user_guidance={"error": str(e)},
                success=False,
                error_message=str(e),
            )

    def _create_flow_continuation_tasks(
        self, flow_id: str, user_context: Dict[str, Any]
    ) -> List[Task]:
        """Create dynamic tasks for flow continuation analysis"""

        # Task 1: Flow State Analysis (with optional memory context)
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
            expected_output=(
                "Detailed flow state analysis including flow type, current phase, "
                "progress percentage, and available data"
            ),
        )

        # Task 2: Phase Validation (with optional memory context)
        validation_task = Task(
            description=(
                f"Use the flow_validator tool to perform comprehensive validation on flow {flow_id}.\n\n"
                "The flow validator will:\n"
                "1. Check all phases sequentially (data_import, attribute_mapping, "
                "data_cleansing, inventory, dependencies, tech_debt)\n"
                "2. Stop at the FIRST incomplete phase (fail-fast approach)\n"
                "3. Return detailed validation with specific data counts and issues\n"
                "4. Provide guidance distinguishing between USER_ACTION vs SYSTEM_ACTION vs ISSUE\n\n"
                "Then use the phase_validator tool for detailed validation of the incomplete phase.\n\n"
                "Your job is to:\n"
                "- Identify exactly what failed or is incomplete\n"
                "- Determine if this requires user vs system action\n"
                "- Provide specific, actionable guidance\n\n"
                "Do not say 'ensure completion'. Instead:\n"
                "- If they need to upload data → route to data import\n"
                "- If they need to configure mappings → route to attribute mapping\n"
                "- If system processing failed → trigger system actions internally"
            ),
            agent=self.phase_validator_agent,
            expected_output=(
                "Detailed validation with actionable guidance distinguishing user "
                "actions from system actions"
            ),
            context=[analysis_task],
        )

        # Task 3: Route Decision
        routing_task = Task(
            description=(
                "Based on the flow analysis and validation, make a routing decision "
                "that provides actionable user guidance.\n\n"
                "Your routing decision must:\n"
                "1. Parse guidance from validation results\n"
                "2. Distinguish user vs system actions\n"
                "3. Route users to pages where they can act\n"
                "4. Trigger system processes when needed\n"
                "5. Provide clear, specific guidance\n\n"
                "ROUTING LOGIC:\n"
                "- Upload data → /discovery/data-import\n"
                "- Configure mappings → /discovery/attribute-mapping\n"
                "- System processing → enhanced dashboard with processing indicator\n"
                "- Phase complete → advance to next phase\n\n"
                "USER GUIDANCE PRINCIPLES:\n"
                "- No 'ensure completion' phrasing\n"
                "- Provide specific, actionable steps\n"
                "- Route to pages for required action\n"
                "- Explain when background processing is needed\n\n"
                "Provide clear reasoning about the route and set user expectations."
            ),
            agent=self.route_strategist,
            expected_output=(
                "Routing decision with specific user guidance and clear distinction "
                "between user vs system responsibilities"
            ),
            context=[analysis_task, validation_task],
        )

        return [analysis_task, validation_task, routing_task]

    def _parse_crew_result(self, crew_result, flow_id: str) -> FlowContinuationResult:
        """Parse crew execution result into structured response"""
        try:
            # In a real implementation, this would parse the structured crew output
            # For now, we'll create a basic response structure

            result_text = (
                str(crew_result.get("result", ""))
                if isinstance(crew_result, dict)
                else str(crew_result)
            )

            # Extract key information (simplified parsing)
            flow_type = "discovery"  # Default
            current_phase = "data_import"  # Default
            target_page = "/discovery/enhanced-dashboard"  # Default

            # Try to extract actual values from result
            if "Type=" in result_text:
                flow_type = (
                    result_text.split("Type=")[1].split(",")[0]
                    if "," in result_text.split("Type=")[1]
                    else result_text.split("Type=")[1].split(" ")[0]
                )

            if "Phase=" in result_text:
                current_phase = (
                    result_text.split("Phase=")[1].split(",")[0]
                    if "," in result_text.split("Phase=")[1]
                    else result_text.split("Phase=")[1].split(" ")[0]
                )

            if "ROUTE:" in result_text:
                target_page = (
                    result_text.split("ROUTE:")[1].split("|")[0].strip()
                    if "|" in result_text.split("ROUTE:")[1]
                    else result_text.split("ROUTE:")[1].strip()
                )

            routing_decision = RouteDecision(
                target_page=target_page,
                flow_id=flow_id,
                phase=current_phase,
                flow_type=flow_type,
                reasoning="AI crew analysis and routing decision",
                confidence=0.8,
            )

            return FlowContinuationResult(
                flow_id=flow_id,
                flow_type=flow_type,
                current_phase=current_phase,
                routing_decision=routing_decision,
                user_guidance={
                    "message": f"Continue with your {flow_type} flow",
                    "phase": current_phase,
                    "crew_analysis": result_text,
                },
                success=True,
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
                    confidence=0.1,
                ),
                user_guidance={"error": "Failed to process crew result"},
                success=False,
                error_message=str(e),
            )

    async def _fallback_processing(
        self, flow_id: str, user_context: Dict[str, Any]
    ) -> FlowContinuationResult:
        """Fallback processing when CrewAI is not available"""
        logger.info(f"🔄 Using fallback processing for flow {flow_id}")

        try:
            # Use tools directly without crew orchestration
            flow_analysis = self.flow_analyzer._run(flow_id)

            # Extract basic information from analysis
            flow_type = "discovery"
            current_phase = "data_import"
            if "Type=" in flow_analysis:
                flow_type = flow_analysis.split("Type=")[1].split(",")[0]
            if "Phase=" in flow_analysis:
                current_phase = flow_analysis.split("Phase=")[1].split(",")[0]

            routing_decision = RouteDecision(
                target_page="/discovery/enhanced-dashboard",
                flow_id=flow_id,
                phase=current_phase,
                flow_type=flow_type,
                reasoning="Fallback processing - CrewAI not available",
                confidence=0.6,
            )

            return FlowContinuationResult(
                flow_id=flow_id,
                flow_type=flow_type,
                current_phase=current_phase,
                routing_decision=routing_decision,
                user_guidance={
                    "message": f"Continue with your {flow_type} flow",
                    "phase": current_phase,
                    "fallback_mode": True,
                },
                success=True,
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
                    confidence=0.1,
                ),
                user_guidance={"error": str(e)},
                success=False,
                error_message=str(e),
            )
