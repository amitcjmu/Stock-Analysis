"""
Agent Wrapper Module

Provides the AgentWrapper class for CrewAI agent compatibility.
"""

import asyncio
import logging
from typing import Any, Dict, List

try:
    from crewai import Agent

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False

    class Agent:
        def __init__(self, **kwargs):
            pass


logger = logging.getLogger(__name__)


class AgentWrapper:
    """
    Wrapper to add execution methods to CrewAI agents without field modification.
    This solves Pydantic v2 compatibility issues where dynamic field assignment is not allowed.
    """

    def __init__(self, agent: Agent, agent_type: str):
        """Initialize the wrapper with the CrewAI agent and its type."""
        self._agent = agent
        self._agent_type = agent_type
        self._context = {}  # Initialize context storage in wrapper
        logger.info(f"✅ Created AgentWrapper for {agent_type}")

    def __getattr__(self, name):
        """Delegate all other attributes to the wrapped agent."""
        return getattr(self._agent, name)

    def get(self, key, default=None):
        """
        Support dict-like .get() calls that CrewAI's Task config processing expects.

        CrewAI's process_config() tries to call values.get("config", {}) on agents.
        This method prevents AttributeError when AgentWrapper is treated as a dict.

        CRITICAL FIX: Resolves 'Agent' object has no attribute 'get' error during Task creation.
        """
        # Return None for all dict-like keys - AgentWrapper is not a dict
        return default

    def __getitem__(self, key):
        """Support dict-like bracket access if needed by CrewAI internals."""
        raise KeyError(f"AgentWrapper doesn't support dictionary access for key: {key}")

    @property
    def context(self):
        """Access to the wrapper's context storage."""
        return self._context

    def execute(self, task: str = None, **kwargs) -> Any:
        """
        Execute a task using this agent in a single-agent crew.
        This provides synchronous execution compatibility.
        """
        try:
            from app.services.crewai_flows.config.crew_factory import (
                create_crew,
                create_task,
            )

            # Create a task for the agent
            # CRITICAL FIX: Pass unwrapped agent to satisfy Pydantic validation
            # CrewAI Task expects BaseAgent instance, not AgentWrapper
            agent_task = create_task(
                description=task or "Execute assigned task",
                agent=self._agent,
                expected_output="Structured analysis and recommendations based on the given task",
            )

            # Create a single-agent crew with explicit configuration
            crew = create_crew(
                agents=[self._agent],
                tasks=[agent_task],
                verbose=False,
                # Factory applies defaults: max_iterations=1, timeout=600s, memory=False (ADR-024)
            )

            # Execute the crew
            result = crew.kickoff()
            return result

        except Exception as e:
            logger.error(f"Agent {self._agent_type} execute method failed: {e}")
            return {"status": "error", "error": str(e), "agent_type": self._agent_type}

    async def execute_async(
        self, inputs: Dict[str, Any] = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Async execution method using agent tools.
        Provides asynchronous execution compatibility.
        """
        task = kwargs.get("task", "Execute agent task")

        # Extract task from inputs if provided
        if inputs and "task" in inputs:
            task = inputs["task"]

        # Run synchronous execute in thread pool
        try:
            result = await asyncio.to_thread(self.execute, task, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Agent {self._agent_type} async execute failed: {e}")
            return {"status": "error", "error": str(e), "agent_type": self._agent_type}

    async def process(self, data: Any) -> Dict[str, Any]:
        """
        Adapter method to make CrewAI agents compatible with executor expectations.
        Converts process() calls to execute_task() calls with structured data.

        This is the critical interface method that executors expect.
        """
        try:
            # Extract field mappings and raw records from input
            if isinstance(data, dict) and "field_mappings" in data:
                field_mappings = data["field_mappings"]
                raw_records = data.get("raw_records", [])

                logger.info(
                    f"🔄 Applying {len(field_mappings)} field mappings to {len(raw_records)} records"
                )

                # Apply field mappings to transform data
                processed_data = self._apply_field_mappings(raw_records, field_mappings)

                return {
                    "status": "success",
                    "processed_data": processed_data,
                    "agent_type": self._agent_type,
                    "field_mappings_applied": len(field_mappings),
                    "records_transformed": len(processed_data),
                    "execution_method": "field_mapping_transformation",
                }
            else:
                # Legacy path - no field mappings provided
                from crewai import Task

                # Create a task description based on data type and agent role
                data_summary = self._create_data_summary(data)
                task_description = (
                    f"Process and analyze the provided data for {self._agent_type} "
                    f"operations.\n\n{data_summary}"
                )

                # Create a task for the agent to process the data
                # CRITICAL FIX: Pass unwrapped agent to satisfy Pydantic validation
                # CrewAI Task expects BaseAgent instance, not AgentWrapper
                # Context is stored in wrapper's _context property and accessed via tools
                task = Task(
                    description=task_description,
                    agent=self._agent,
                    expected_output=(
                        "Structured analysis with processed data, insights, and "
                        "classifications in JSON format"
                    ),
                )

                # Store data in wrapper context for tools to access
                self._context = {"data": data}

                # Execute the task using crew factory
                from app.services.crewai_flows.config.crew_factory import create_crew

                crew = create_crew(agents=[self._agent], tasks=[task], verbose=False)
                result = crew.kickoff()

                # Return structured response
                return {
                    "status": "success",
                    "processed_data": data,
                    "agent_output": str(result),
                    "agent_type": self._agent_type,
                    "insights": getattr(self._agent, "insights", []),
                    "classifications": getattr(self._agent, "classifications", {}),
                    "execution_method": "process_adapter",
                }

        except Exception as e:
            logger.error(f"Agent {self._agent_type} process method failed: {e}")
            # Return fallback response that maintains the expected structure
            return {
                "status": "error",
                "error": str(e),
                "agent_type": self._agent_type,
                "processed_data": (
                    data.get("raw_records", []) if isinstance(data, dict) else data
                ),
                "execution_method": "process_adapter_fallback",
            }

    def _apply_field_mappings(
        self, raw_records: List[Dict[str, Any]], field_mappings: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Apply field mappings to transform raw CSV data to database fields.

        Args:
            raw_records: Raw import records with raw_data field
            field_mappings: Source field -> target field mappings

        Returns:
            Transformed records with correct field names
        """
        from datetime import datetime

        transformed_data = []

        for record in raw_records:
            transformed_record = {}

            # Preserve ID fields
            if "raw_import_record_id" in record:
                transformed_record["raw_import_record_id"] = record[
                    "raw_import_record_id"
                ]
                transformed_record["id"] = record["raw_import_record_id"]

            if "row_number" in record:
                transformed_record["row_number"] = record["row_number"]

            # Apply field mappings to raw_data
            raw_data = record.get("raw_data", {})
            if isinstance(raw_data, dict):
                for source_field, value in raw_data.items():
                    # Use target field name if mapping exists, otherwise keep source
                    target_field = field_mappings.get(source_field, source_field)
                    transformed_record[target_field] = value

            # Add transformation metadata
            transformed_record["cleansing_method"] = "agent_field_mapping"
            transformed_record["cleansed_at"] = datetime.utcnow().isoformat()
            transformed_record["mappings_applied"] = len(field_mappings)

            transformed_data.append(transformed_record)

        logger.debug(
            f"✅ Transformed {len(transformed_data)} records using field mappings"
        )
        return transformed_data

    def _create_data_summary(self, data: Any) -> str:
        """Create a concise summary of the data for task description."""
        try:
            if isinstance(data, list):
                if not data:
                    return "Empty data list provided."

                data_type = type(data[0]).__name__ if data else "unknown"
                sample_keys = []

                if isinstance(data[0], dict):
                    sample_keys = list(data[0].keys())[:5]  # First 5 keys
                    sample_str = f"Sample keys: {sample_keys}"
                    if len(data[0].keys()) > 5:
                        sample_str += f" (and {len(data[0].keys()) - 5} more)"
                else:
                    sample_str = f"Sample value: {str(data[0])[:100]}..."

                return f"Data: {len(data)} {data_type} records. {sample_str}"

            elif isinstance(data, dict):
                keys = list(data.keys())[:5]
                key_str = f"Keys: {keys}"
                if len(data.keys()) > 5:
                    key_str += f" (and {len(data.keys()) - 5} more)"
                return f"Data: Dictionary with {len(data)} items. {key_str}"

            else:
                return f"Data: {type(data).__name__} - {str(data)[:100]}..."

        except Exception as e:
            logger.warning(f"Failed to create data summary: {e}")
            return f"Data provided for processing (summary generation failed: {e})"
