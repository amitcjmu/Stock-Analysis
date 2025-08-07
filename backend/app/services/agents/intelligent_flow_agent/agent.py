"""
Intelligent Flow Agent

Single intelligent CrewAI agent for flow processing that can handle all flow processing
tasks using multiple tools and comprehensive knowledge of the platform.
"""

import json
import logging
import re

from app.core.security.cache_encryption import secure_setattr

try:
    from crewai import Agent, Crew, Process, Task

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False

    class Agent:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                secure_setattr(self, key, value)

    class Task:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                secure_setattr(self, key, value)

    class Crew:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                secure_setattr(self, key, value)

        def kickoff(self, inputs=None):
            return {"result": "CrewAI not available - using fallback"}

    class Process:
        sequential = "sequential"


# Import LLM configuration
try:
    from app.services.llm_config import get_crewai_llm

    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

    def get_crewai_llm():
        return None


from .models import FlowIntelligenceResult
from .tools import (
    FlowContextTool,
    FlowStatusTool,
    NavigationDecisionTool,
    PhaseValidationTool,
)

logger = logging.getLogger(__name__)


class IntelligentFlowAgent:
    """Single intelligent CrewAI agent for flow processing"""

    def __init__(self):
        """Initialize the intelligent flow agent"""
        self.agent = None
        self.crew = None
        self.tools = []

        if CREWAI_AVAILABLE:
            self._setup_crewai_agent()
        else:
            logger.warning("CrewAI not available - using fallback implementation")

    def _setup_crewai_agent(self):
        """Setup CrewAI agent with proper tools and configuration"""
        try:
            # Create tools
            self.flow_context_tool = FlowContextTool()
            self.flow_status_tool = FlowStatusTool()
            self.phase_validation_tool = PhaseValidationTool()
            self.navigation_tool = NavigationDecisionTool()

            # Create agent
            self.agent = Agent(
                role="Flow Intelligence Specialist",
                goal="Analyze discovery flow status and provide intelligent routing decisions with actionable user guidance",
                backstory="""You are an expert AI agent specializing in migration discovery flow analysis.
                You understand the complete discovery flow lifecycle and can provide precise guidance on what users need to do next.

                Key Knowledge:
                - When you receive inputs like {flow_id}, {client_account_id}, etc., these are actual values provided by the system
                - The flow_context_analyzer tool expects the actual flow_id value, not the placeholder string
                - If a flow doesn't exist (status="not_found"), users must upload data to create a new flow
                - You distinguish between user actions (things users can do) and system actions (automatic processes)
                - Always use the actual values from inputs, not literal strings like "current_flow_id"
                - Note: Some flows may have phase names (tech_debt, inventory, etc.) as their status due to legacy data

                Tool Usage Examples:
                - flow_context_analyzer: Use with actual flow_id from inputs, e.g., "9a0cb58d-bad8-4fb7-a4b9-ee7e35df281b"
                - flow_status_analyzer: Pass the actual flow_id and context data
                - Never pass placeholder strings like "current_flow_id" to tools""",
                tools=[
                    self.flow_context_tool,
                    self.flow_status_tool,
                    self.phase_validation_tool,
                    self.navigation_tool,
                ],
                verbose=True,
                memory=False,  # Disable memory to prevent APIStatusError
                llm=get_crewai_llm(),
            )

            # Create task
            self.task = Task(
                description="""Analyze the discovery flow and provide intelligent routing guidance.

You will receive these inputs:
- flow_id: The actual UUID of the flow to analyze
- client_account_id: The client's account UUID
- engagement_id: The engagement UUID
- user_id: The user's UUID

IMPORTANT: These are real values, not placeholders. Use them directly in your tool calls.

Analysis Steps:
1. Use flow_context_analyzer with the actual flow_id and other values from inputs
2. Use flow_status_analyzer with the actual flow_id and context_data from step 1
3. Analyze the results to understand the flow's current state
4. Based on the flow status, determine the appropriate next steps
5. If flow exists and needs validation, use phase_validator
6. Make intelligent routing decisions based on your analysis

Key Decision Points:
- If a flow doesn't exist (not_found), guide user to upload data
- If a flow exists but has incomplete phases, guide to complete them
- If a flow has validation errors, provide specific resolution steps
- Always provide actionable, specific guidance

Your response should include:
- routing_decision: The specific page/route for the user
- user_guidance: Clear, actionable instructions
- reasoning: Your analysis of the situation
- next_actions: List of specific steps the user can take""",
                agent=self.agent,
                expected_output="A comprehensive flow analysis with specific routing decision and actionable user guidance",
            )

            # Create crew
            self.crew = Crew(
                agents=[self.agent],
                tasks=[self.task],
                process=Process.sequential,
                memory=False,  # Disable memory to prevent APIStatusError
                verbose=True,
            )

            self.crewai_available = True
            logger.info("✅ CrewAI agent successfully configured")

        except Exception as e:
            logger.error(f"❌ Failed to setup CrewAI agent: {e}")
            self.crewai_available = False

    async def analyze_flow_continuation(
        self,
        flow_id: str,
        client_account_id: str = None,
        engagement_id: str = None,
        user_id: str = None,
    ) -> FlowIntelligenceResult:
        """Analyze flow continuation using intelligent agent"""

        if not self.crewai_available:
            logger.warning("CrewAI not available, using fallback analysis")
            return await self._fallback_analysis(
                flow_id, client_account_id, engagement_id, user_id
            )

        try:
            logger.info(f"🤖 Starting intelligent flow analysis for {flow_id}")

            # Create dynamic task with flow-specific inputs
            inputs = {
                "flow_id": flow_id,
                "client_account_id": client_account_id
                or "11111111-1111-1111-1111-111111111111",
                "engagement_id": engagement_id
                or "22222222-2222-2222-2222-222222222222",
                "user_id": user_id or "33333333-3333-3333-3333-333333333333",
            }

            # Execute crew with specific inputs
            result = self.crew.kickoff(inputs=inputs)

            logger.info(f"✅ CrewAI analysis completed for {flow_id}")

            # Parse and return structured result
            return self._parse_crew_result(result, flow_id)

        except Exception as e:
            logger.error(f"❌ CrewAI flow analysis failed for {flow_id}: {e}")
            # Fallback to direct analysis
            return await self._fallback_analysis(
                flow_id, client_account_id, engagement_id, user_id
            )

    def _parse_crew_result(self, crew_result, flow_id: str) -> FlowIntelligenceResult:
        """Parse crew result into structured response"""
        try:
            # Extract result text
            result_text = str(crew_result)

            # Try to extract JSON from result
            json_match = re.search(r"\{.*\}", result_text, re.DOTALL)

            if json_match:
                try:
                    result_data = json.loads(json_match.group())

                    # Fix next_actions if they're objects instead of strings
                    next_actions = result_data.get("next_actions", [])
                    if next_actions and isinstance(next_actions[0], dict):
                        # Convert objects to strings
                        next_actions = [
                            (
                                action.get("description", str(action))
                                if isinstance(action, dict)
                                else str(action)
                            )
                            for action in next_actions
                        ]

                    return FlowIntelligenceResult(
                        success=True,
                        flow_id=flow_id,
                        flow_type=result_data.get("flow_type", "discovery"),
                        current_phase=result_data.get("current_phase", "data_import"),
                        routing_decision=result_data.get(
                            "routing_decision", "/discovery/overview"
                        ),
                        user_guidance=result_data.get(
                            "user_guidance", "Continue with flow processing"
                        ),
                        reasoning=result_data.get("reasoning", result_text),
                        confidence=float(result_data.get("confidence", 0.8)),
                        next_actions=next_actions,
                        issues_found=result_data.get("issues", []),
                    )
                except json.JSONDecodeError:
                    pass

            # Fallback parsing if no JSON found
            return FlowIntelligenceResult(
                success=True,
                flow_id=flow_id,
                flow_type="discovery",
                current_phase="data_import",
                routing_decision="/discovery/overview",
                user_guidance=(
                    result_text[:200] + "..." if len(result_text) > 200 else result_text
                ),
                reasoning=result_text,
                confidence=0.7,
            )

        except Exception as e:
            logger.error(f"Failed to parse crew result: {e}")
            return FlowIntelligenceResult(
                success=False,
                flow_id=flow_id,
                flow_type="discovery",
                current_phase="data_import",
                routing_decision="/discovery/overview",
                user_guidance="Unable to parse analysis result",
                reasoning=f"Parse error: {str(e)}",
                confidence=0.0,
                issues_found=[str(e)],
            )

    async def _fallback_analysis(
        self,
        flow_id: str,
        client_account_id: str = None,
        engagement_id: str = None,
        user_id: str = None,
    ) -> FlowIntelligenceResult:
        """Fallback analysis when CrewAI is not available"""
        try:
            logger.info(f"🔄 Using fallback analysis for flow {flow_id}")

            # Use direct tools to analyze flow
            context_tool = FlowContextTool()
            status_tool = FlowStatusTool()

            # Get context
            context_data = context_tool._run(
                flow_id=flow_id,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                user_id=user_id,
            )

            # Get flow status
            status_result = status_tool._run(flow_id, context_data)
            status_data = (
                json.loads(status_result)
                if isinstance(status_result, str)
                else status_result
            )

            # Handle non-existent flows
            if (
                status_data.get("status") == "not_found"
                or status_data.get("current_phase") == "not_found"
            ):
                return FlowIntelligenceResult(
                    success=True,
                    flow_id=flow_id,
                    flow_type="discovery",
                    current_phase="not_found",
                    routing_decision="/discovery/data-import",
                    user_guidance="FLOW NOT FOUND: This discovery flow does not exist. Please start a new discovery flow by uploading your CMDB or asset data file.",
                    reasoning="Flow ID not found in database. User needs to initiate a new discovery flow by uploading data.",
                    confidence=1.0,
                    next_actions=[
                        "Go to the Data Import page",
                        "Upload a CSV or Excel file containing your asset/CMDB data",
                        "Wait for the system to process and analyze your data",
                        "Review the generated field mappings",
                    ],
                    issues_found=["Flow does not exist in the system"],
                )

            # Handle flows with no data - check both raw_data_count and field_mapping_count
            raw_data_count = status_data.get("raw_data_count", 0)
            field_mapping_count = status_data.get("field_mapping_count", 0)

            # If we have either raw data or field mappings, the flow has data
            has_data = raw_data_count > 0 or field_mapping_count > 0

            if not has_data:
                return FlowIntelligenceResult(
                    success=True,
                    flow_id=flow_id,
                    flow_type="discovery",
                    current_phase="data_import",
                    routing_decision="/discovery/data-import",
                    user_guidance="NO DATA FOUND: This flow exists but contains no data. Please upload your CMDB or asset data to begin the discovery process.",
                    reasoning="Flow exists but has no raw data or field mappings. Data import phase needs to be completed.",
                    confidence=0.9,
                    next_actions=[
                        "Go to the Data Import page",
                        "Upload a CSV or Excel file with at least 1 record",
                        "Ensure the file contains asset information like names, IDs, owners, etc.",
                        "Wait for processing to complete",
                    ],
                    issues_found=["No raw data in flow", "Data import incomplete"],
                )

            # Handle flows with data but incomplete phases
            current_phase = status_data.get("current_phase", "data_import")
            progress = status_data.get("progress", 0)

            if current_phase == "data_import" and progress < 100:
                return FlowIntelligenceResult(
                    success=True,
                    flow_id=flow_id,
                    flow_type="discovery",
                    current_phase=current_phase,
                    routing_decision="/discovery/data-import",
                    user_guidance="DATA IMPORT IN PROGRESS: Your data is being processed. Please wait for completion or check for any import errors.",
                    reasoning="Data import phase is not yet complete.",
                    confidence=0.8,
                    next_actions=[
                        "Check the data import status",
                        "Wait for processing to complete",
                        "Review any error messages",
                        "Upload additional data if needed",
                    ],
                )

            elif current_phase == "attribute_mapping":
                return FlowIntelligenceResult(
                    success=True,
                    flow_id=flow_id,
                    flow_type="discovery",
                    current_phase=current_phase,
                    routing_decision=f"/discovery/attribute-mapping?flow_id={flow_id}",
                    user_guidance="ATTRIBUTE MAPPING NEEDED: Review and configure how your data fields map to standard asset attributes.",
                    reasoning="Data import complete, attribute mapping phase active.",
                    confidence=0.9,
                    next_actions=[
                        "Review the suggested field mappings",
                        "Correct any incorrect mappings",
                        "Map critical fields like asset names, IDs, owners",
                        "Save the mapping configuration",
                    ],
                )

            # Default case - route to overview
            return FlowIntelligenceResult(
                success=True,
                flow_id=flow_id,
                flow_type="discovery",
                current_phase=current_phase,
                routing_decision="/discovery/overview",
                user_guidance=f"FLOW ANALYSIS: Current phase is {current_phase} ({progress}% complete). Continue with the discovery process.",
                reasoning=f"Flow in {current_phase} phase with {progress}% completion.",
                confidence=0.7,
                next_actions=[
                    "Review the current flow status",
                    "Complete any pending tasks",
                    "Proceed to the next phase when ready",
                ],
            )

        except Exception as e:
            logger.error(f"❌ Fallback analysis failed for {flow_id}: {e}")
            return FlowIntelligenceResult(
                success=False,
                flow_id=flow_id,
                flow_type="discovery",
                current_phase="unknown",
                routing_decision="/discovery/data-import",
                user_guidance="SYSTEM ERROR: Unable to analyze flow. Please start a new discovery flow by uploading data.",
                reasoning=f"Analysis failed due to system error: {str(e)}",
                confidence=0.0,
                next_actions=[
                    "Start a new discovery flow",
                    "Upload your asset data file",
                    "Contact support if the issue persists",
                ],
                issues_found=[f"System error: {str(e)}"],
            )
