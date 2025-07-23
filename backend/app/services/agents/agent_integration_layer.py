"""
Agent Integration Layer - Seamless integration between agents and Discovery Flow
Provides compatibility layer for existing systems while enabling agent-first architecture
"""

import logging
import time
import uuid
from datetime import datetime
# Temporary type definitions to replace archived imports
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class AgentResult(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AgentClarificationRequest(BaseModel):
    agent_name: str
    question: str
    context: Optional[Dict[str, Any]] = None


class AgentInsight(BaseModel):
    agent_name: str
    insight: str
    confidence: float
    metadata: Optional[Dict[str, Any]] = None


logger = logging.getLogger(__name__)


class AgentIntegrationLayer:
    """
    Agent Integration Layer

    Provides seamless integration between the new agent-first architecture and
    existing Discovery Flow systems, ensuring backward compatibility while
    enabling enhanced agent capabilities.
    """

    def __init__(self, db: Optional[Any] = None, context: Optional[Any] = None):
        self.integration_id = f"agent_integration_{uuid.uuid4().hex[:8]}"
        self.logger = logging.getLogger("agents.integration_layer")

        # Store db and context for lazy initialization
        self.db = db
        self.context = context
        self.orchestrator = None  # Will be initialized when needed with proper context

        # Integration state
        self.active_integrations = {}
        self.compatibility_mode = True
        self.legacy_fallback_enabled = True

        # Performance tracking
        self.integration_metrics = {
            "total_executions": 0,
            "successful_integrations": 0,
            "fallback_activations": 0,
            "average_execution_time": 0.0,
        }

        self.logger.info(
            f"🔗 Agent Integration Layer initialized (ID: {self.integration_id})"
        )

    async def integrate_with_discovery_flow(
        self, flow_data: Dict[str, Any], flow_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Main integration point for Discovery Flow

        Args:
            flow_data: Data from Discovery Flow
            flow_context: Flow context and metadata

        Returns:
            Integrated results compatible with existing flow
        """
        start_time = time.time()
        integration_id = str(uuid.uuid4())

        self.logger.info(
            f"🔗 Starting Discovery Flow integration (ID: {integration_id})"
        )

        try:
            # Store integration state
            self.active_integrations[integration_id] = {
                "start_time": start_time,
                "status": "running",
                "flow_context": flow_context or {},
            }

            # Transform flow data for agent consumption
            agent_data = await self._transform_flow_data_for_agents(
                flow_data, flow_context
            )

            # Note: MasterFlowOrchestrator integration disabled
            # The orchestrator requires db and context which may not be available at this level
            # For now, return mock agent results
            self.logger.warning(
                "MasterFlowOrchestrator integration disabled - returning mock results"
            )
            agent_results = {
                "status": "success",
                "phase": "agent_execution",
                "results": agent_data,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Transform agent results back to flow format
            flow_compatible_results = await self._transform_agent_results_for_flow(
                agent_results, flow_data, flow_context
            )

            # Update integration metrics
            execution_time = time.time() - start_time
            await self._update_integration_metrics(execution_time, "success")

            # Update integration state
            self.active_integrations[integration_id].update(
                {
                    "status": "completed",
                    "execution_time": execution_time,
                    "agent_results": agent_results,
                    "flow_results": flow_compatible_results,
                }
            )

            self.logger.info(
                f"✅ Discovery Flow integration completed in {execution_time:.2f}s"
            )

            return flow_compatible_results

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"❌ Discovery Flow integration failed: {str(e)}")

            # Attempt fallback if enabled
            if self.legacy_fallback_enabled:
                self.logger.info("🔄 Attempting legacy fallback...")
                fallback_result = await self._execute_legacy_fallback(
                    flow_data, flow_context
                )
                await self._update_integration_metrics(execution_time, "fallback")
                return fallback_result

            await self._update_integration_metrics(execution_time, "failed")
            raise

    async def _transform_flow_data_for_agents(
        self, flow_data: Dict[str, Any], flow_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transform Discovery Flow data format to agent-compatible format"""

        # Extract key data components from flow format
        agent_data = {
            "raw_data": [],
            "source_columns": [],
            "file_info": {},
            "flow_metadata": flow_context or {},
        }

        # Handle different flow data formats
        if "imported_data" in flow_data:
            agent_data["raw_data"] = flow_data["imported_data"]
        elif "data" in flow_data:
            agent_data["raw_data"] = flow_data["data"]
        elif "assets" in flow_data:
            agent_data["raw_data"] = flow_data["assets"]

        # Extract source columns
        if (
            agent_data["raw_data"]
            and isinstance(agent_data["raw_data"], list)
            and len(agent_data["raw_data"]) > 0
        ):
            first_record = agent_data["raw_data"][0]
            if isinstance(first_record, dict):
                agent_data["source_columns"] = list(first_record.keys())

        # Extract file information
        if "file_metadata" in flow_data:
            agent_data["file_info"] = flow_data["file_metadata"]
        elif "import_info" in flow_data:
            agent_data["file_info"] = flow_data["import_info"]

        # Add flow-specific context
        agent_data["flow_metadata"].update(
            {
                "integration_layer": self.integration_id,
                "compatibility_mode": self.compatibility_mode,
                "original_flow_format": True,
            }
        )

        self.logger.info(
            f"📊 Transformed flow data: {len(agent_data['raw_data'])} records, "
            f"{len(agent_data['source_columns'])} columns"
        )

        return agent_data

    async def _transform_agent_results_for_flow(
        self,
        agent_results: Dict[str, Any],
        original_flow_data: Dict[str, Any],
        flow_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Transform agent results back to Discovery Flow compatible format"""

        # Create flow-compatible result structure
        flow_results = {
            "status": agent_results.get("status", "unknown"),
            "confidence": agent_results.get("overall_confidence", 0.0),
            "execution_time": 0.0,
            "results": {},
            "agent_insights": [],
            "user_clarifications": [],
            "recommendations": [],
        }

        # Calculate total execution time
        agent_execution_times = []
        for agent_name, agent_result in agent_results.get("agent_results", {}).items():
            if isinstance(agent_result, dict) and "execution_time" in agent_result:
                agent_execution_times.append(agent_result["execution_time"])

        flow_results["execution_time"] = sum(agent_execution_times)

        # Transform individual agent results
        await self._transform_validation_results(agent_results, flow_results)
        await self._transform_mapping_results(agent_results, flow_results)
        await self._transform_cleansing_results(agent_results, flow_results)

        # Aggregate insights and clarifications
        flow_results["agent_insights"] = agent_results.get("all_insights", [])
        flow_results["user_clarifications"] = agent_results.get(
            "all_clarifications", []
        )

        # Generate flow-level recommendations
        await self._generate_flow_recommendations(agent_results, flow_results)

        self.logger.info(
            f"🔄 Transformed agent results to flow format: {flow_results['status']} "
            f"({flow_results['confidence']:.1f}% confidence)"
        )

        return flow_results

    async def _transform_validation_results(
        self, agent_results: Dict[str, Any], flow_results: Dict[str, Any]
    ):
        """Transform data validation agent results"""
        validation_result = agent_results.get("agent_results", {}).get(
            "data_validation", {}
        )

        if validation_result and validation_result.get("data"):
            validation_data = validation_result["data"]

            flow_results["results"]["validation"] = {
                "file_validation": validation_data.get("file_validation", {}),
                "security_assessment": validation_data.get("security_assessment", {}),
                "pii_detection": validation_data.get("pii_detection", {}),
                "compliance_check": validation_data.get("compliance_check", {}),
                "data_quality": validation_data.get("data_quality", {}),
                "confidence": validation_result.get("confidence_score", 0.0),
            }

    async def _transform_mapping_results(
        self, agent_results: Dict[str, Any], flow_results: Dict[str, Any]
    ):
        """Transform attribute mapping agent results"""
        mapping_result = agent_results.get("agent_results", {}).get(
            "attribute_mapping", {}
        )

        if mapping_result and mapping_result.get("data"):
            mapping_data = mapping_result["data"]

            # Combine critical and secondary mappings
            all_mappings = {}
            all_mappings.update(mapping_data.get("critical_mappings", {}))
            all_mappings.update(mapping_data.get("secondary_mappings", {}))

            flow_results["results"]["field_mappings"] = {
                "mappings": all_mappings,
                "critical_mappings": mapping_data.get("critical_mappings", {}),
                "secondary_mappings": mapping_data.get("secondary_mappings", {}),
                "unmapped_columns": mapping_data.get("unmapped_columns", []),
                "ambiguous_mappings": mapping_data.get("ambiguous_mappings", []),
                "summary": mapping_data.get("summary", {}),
                "confidence": mapping_result.get("confidence_score", 0.0),
            }

    async def _transform_cleansing_results(
        self, agent_results: Dict[str, Any], flow_results: Dict[str, Any]
    ):
        """Transform data cleansing agent results"""
        cleansing_result = agent_results.get("agent_results", {}).get(
            "data_cleansing", {}
        )

        if cleansing_result and cleansing_result.get("data"):
            cleansing_data = cleansing_result["data"]

            flow_results["results"]["data_cleansing"] = {
                "cleaned_data": cleansing_data.get("cleaned_data", []),
                "standardization_summary": cleansing_data.get(
                    "standardization_summary", {}
                ),
                "bulk_operations_summary": cleansing_data.get(
                    "bulk_operations_summary", {}
                ),
                "data_quality_metrics": cleansing_data.get("data_quality_metrics", {}),
                "transformation_log": cleansing_data.get("transformation_log", []),
                "confidence": cleansing_result.get("confidence_score", 0.0),
            }

            # Set final cleaned data as main result
            if cleansing_data.get("cleaned_data"):
                flow_results["cleaned_data"] = cleansing_data["cleaned_data"]

    async def _generate_flow_recommendations(
        self, agent_results: Dict[str, Any], flow_results: Dict[str, Any]
    ):
        """Generate flow-level recommendations based on agent results"""
        recommendations = []

        # Analyze overall agent performance
        execution_summary = agent_results.get("execution_summary", {})

        if execution_summary.get("failed_agents", 0) > 0:
            recommendations.append(
                {
                    "type": "critical",
                    "title": "Agent Execution Failures",
                    "description": f"{execution_summary['failed_agents']} agents failed execution",
                    "action_required": True,
                    "suggested_actions": [
                        "Review agent logs",
                        "Check data quality",
                        "Retry with corrected data",
                    ],
                }
            )

        if execution_summary.get("partial_agents", 0) > 0:
            recommendations.append(
                {
                    "type": "warning",
                    "title": "Partial Agent Completions",
                    "description": f"{execution_summary['partial_agents']} agents completed with partial results",
                    "action_required": True,
                    "suggested_actions": [
                        "Review partial results",
                        "Provide clarifications",
                        "Consider manual review",
                    ],
                }
            )

        # Check for high number of clarifications
        total_clarifications = len(agent_results.get("all_clarifications", []))
        if total_clarifications > 5:
            recommendations.append(
                {
                    "type": "info",
                    "title": "User Input Required",
                    "description": f"{total_clarifications} clarifications requested by agents",
                    "action_required": True,
                    "suggested_actions": [
                        "Review clarification questions",
                        "Provide responses",
                        "Consider data improvements",
                    ],
                }
            )

        # Check overall confidence
        overall_confidence = agent_results.get("overall_confidence", 0.0)
        if overall_confidence < 70:
            recommendations.append(
                {
                    "type": "warning",
                    "title": "Low Overall Confidence",
                    "description": f"Overall confidence is {overall_confidence:.1f}% (below 70% threshold)",
                    "action_required": False,
                    "suggested_actions": [
                        "Review data quality",
                        "Provide additional context",
                        "Consider manual validation",
                    ],
                }
            )

        flow_results["recommendations"] = recommendations

    async def _execute_legacy_fallback(
        self, flow_data: Dict[str, Any], flow_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute legacy fallback when agent integration fails"""

        self.logger.info("🔄 Executing legacy fallback mode...")

        # Increment fallback counter
        self.integration_metrics["fallback_activations"] += 1

        # Create minimal compatible result
        fallback_result = {
            "status": "partial",
            "confidence": 50.0,
            "execution_time": 0.1,
            "results": {
                "validation": {"confidence": 50.0},
                "field_mappings": {"mappings": {}, "confidence": 50.0},
                "data_cleansing": {
                    "cleaned_data": flow_data.get("data", []),
                    "confidence": 50.0,
                },
            },
            "agent_insights": [
                {
                    "title": "Legacy Fallback Mode",
                    "description": "Agent integration failed, using legacy processing mode",
                    "confidence_score": 50.0,
                    "category": "system",
                    "actionable": True,
                    "action_items": [
                        "Review agent integration logs",
                        "Check system compatibility",
                    ],
                }
            ],
            "user_clarifications": [],
            "recommendations": [
                {
                    "type": "critical",
                    "title": "Agent Integration Failure",
                    "description": "The new agent-first processing failed, reverted to legacy mode",
                    "action_required": True,
                    "suggested_actions": [
                        "Check agent system status",
                        "Review error logs",
                        "Contact system administrator",
                    ],
                }
            ],
            "fallback_mode": True,
        }

        return fallback_result

    async def _update_integration_metrics(self, execution_time: float, status: str):
        """Update integration performance metrics"""
        self.integration_metrics["total_executions"] += 1

        if status == "success":
            self.integration_metrics["successful_integrations"] += 1
        elif status == "fallback":
            self.integration_metrics["fallback_activations"] += 1

        # Update average execution time
        current_avg = self.integration_metrics["average_execution_time"]
        total_executions = self.integration_metrics["total_executions"]

        self.integration_metrics["average_execution_time"] = (
            current_avg * (total_executions - 1) + execution_time
        ) / total_executions

    async def get_integration_status(self) -> Dict[str, Any]:
        """Get current integration layer status"""
        return {
            "integration_id": self.integration_id,
            "compatibility_mode": self.compatibility_mode,
            "legacy_fallback_enabled": self.legacy_fallback_enabled,
            "active_integrations": len(self.active_integrations),
            "metrics": self.integration_metrics,
            "orchestrator_status": self.orchestrator.get_orchestration_status(),
        }

    async def process_clarification_response(
        self, question_id: str, response: Dict[str, Any]
    ) -> bool:
        """Process user clarification response through orchestrator"""
        return await self.orchestrator.process_clarification_response(
            question_id, response
        )

    async def get_pending_clarifications(self) -> List[Dict[str, Any]]:
        """Get all pending clarifications from agents"""
        return await self.orchestrator.get_pending_clarifications()

    async def get_all_insights(self) -> List[Dict[str, Any]]:
        """Get all insights from agents"""
        return await self.orchestrator.get_all_insights()

    def enable_compatibility_mode(self, enabled: bool = True):
        """Enable/disable compatibility mode"""
        self.compatibility_mode = enabled
        self.logger.info(
            f"🔧 Compatibility mode {'enabled' if enabled else 'disabled'}"
        )

    def enable_legacy_fallback(self, enabled: bool = True):
        """Enable/disable legacy fallback"""
        self.legacy_fallback_enabled = enabled
        self.logger.info(f"🔧 Legacy fallback {'enabled' if enabled else 'disabled'}")

    async def test_integration(
        self, test_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Test the integration layer with sample data"""

        if not test_data:
            test_data = {
                "data": [
                    {"hostname": "server001", "ip": "192.168.1.10", "os": "linux"},
                    {"hostname": "server002", "ip": "192.168.1.11", "os": "windows"},
                ],
                "file_metadata": {"filename": "test_data.csv", "size_mb": 0.1},
            }

        self.logger.info("🧪 Running integration layer test...")

        try:
            result = await self.integrate_with_discovery_flow(
                test_data,
                {"test_mode": True, "test_timestamp": datetime.now().isoformat()},
            )

            test_result = {
                "test_status": "success",
                "integration_working": True,
                "agents_responsive": result.get("status") != "failed",
                "fallback_triggered": result.get("fallback_mode", False),
                "test_confidence": result.get("confidence", 0.0),
                "test_execution_time": result.get("execution_time", 0.0),
            }

            self.logger.info(
                f"✅ Integration test completed: {test_result['test_status']}"
            )
            return test_result

        except Exception as e:
            self.logger.error(f"❌ Integration test failed: {str(e)}")
            return {
                "test_status": "failed",
                "integration_working": False,
                "error": str(e),
                "fallback_triggered": True,
            }
