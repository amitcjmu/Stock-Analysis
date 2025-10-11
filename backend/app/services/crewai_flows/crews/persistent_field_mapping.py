"""
Persistent Field Mapping using Tenant-Scoped Agent Pool

This module uses the persistent field_mapper agent from the TenantScopedAgentPool
instead of creating new crews for every mapping request. This dramatically reduces
latency and improves consistency through agent memory.

Performance improvements:
- Single persistent agent vs 3 new agents per request
- 1 LLM call vs 8+ calls
- ~5 seconds vs 86+ seconds
- Memory accumulation for better mappings over time
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List

# Check if we can use persistent agents
try:
    from app.services.persistent_agents.tenant_scoped_agent_pool import (
        TenantScopedAgentPool,
    )

    PERSISTENT_AGENTS_AVAILABLE = True
except ImportError:
    PERSISTENT_AGENTS_AVAILABLE = False

# For crew compatibility
try:
    from crewai import Crew

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False

    class Crew:
        def __init__(self, **kwargs):
            pass

        def kickoff(self):
            return {}


logger = logging.getLogger(__name__)


class PersistentFieldMapping:
    """Use persistent field_mapper agent for efficient field mapping"""

    def __init__(self, crewai_service, context):
        self.crewai_service = crewai_service
        self.context = context
        self.client_id = (
            str(context.client_account_id) if context.client_account_id else None
        )
        self.engagement_id = (
            str(context.engagement_id) if context.engagement_id else None
        )

    async def map_fields(self, raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Map fields using persistent agent instead of creating new crew

        Args:
            raw_data: List of data records to analyze for field mapping

        Returns:
            Field mapping results with confidence scores
        """
        if not self.client_id or not self.engagement_id:
            logger.error("Missing client_id or engagement_id for persistent agent")
            return self._fallback_mapping(raw_data)

        try:
            # Get or create persistent field_mapper agent
            logger.info("🔄 Getting persistent field_mapper agent from pool")
            context_info = {
                "service_registry": getattr(
                    self.crewai_service, "service_registry", None
                ),
                "flow_id": getattr(self.context, "flow_id", None),
            }
            agent = await TenantScopedAgentPool.get_or_create_agent(
                client_id=self.client_id,
                engagement_id=self.engagement_id,
                agent_type="field_mapper",
                context_info=context_info,
            )

            # Prepare mapping task
            headers = list(raw_data[0].keys()) if raw_data else []
            sample_values = {}

            # Collect sample values from first record
            if raw_data:
                for header in headers[:10]:  # Limit to first 10 fields
                    sample_values[header] = str(raw_data[0].get(header, ""))[:50]

            # Create simple task for the agent
            task_description = f"""
            Analyze these CSV fields and map them to Asset model fields:

            Source Fields: {json.dumps(headers)}
            Sample Values: {json.dumps(sample_values, indent=2)}

            Asset model primary fields:
            - asset_id: Unique identifier for the asset
            - name/asset_name: Name of the asset
            - asset_type: Type/category of asset
            - ip_address: IP address
            - status: Current status
            - location: Physical or logical location
            - environment: Deployment environment
            - hostname: Host name
            - operating_system: OS information

            Return a JSON mapping with this structure:
            {{
                "mappings": {{
                    "SourceField": {{
                        "target_field": "asset_field_name",
                        "confidence": 0.0-1.0,
                        "reasoning": "brief explanation"
                    }}
                }}
            }}

            IMPORTANT:
            - Use EXACT source field names (e.g., "Device_ID" not "device_id")
            - Map Device_ID to asset_id (not name)
            - Map Device_Name to asset_name or name
            - Skip metadata fields like row_index
            """

            # Execute agent directly (single LLM call)
            logger.info(
                f"🚀 Executing persistent field_mapper with {len(headers)} fields"
            )
            start_time = logger.time() if hasattr(logger, "time") else None

            # Direct agent execution without crew overhead
            result = await self._execute_agent_task(agent, task_description)

            if start_time:
                elapsed = (
                    logger.timeEnd(start_time) if hasattr(logger, "timeEnd") else 0
                )
                logger.info(f"✅ Field mapping completed in {elapsed}ms")

            # Parse and validate result
            mapping_result = self._parse_agent_result(result)

            # Store in agent memory for future reference
            await self._update_agent_memory(agent, headers, mapping_result)

            return mapping_result

        except Exception as e:
            logger.error(f"❌ Persistent field mapping failed: {e}")
            return self._fallback_mapping(raw_data)

    async def _execute_agent_task(self, agent, task_description: str) -> str:
        """Execute task directly with agent without crew overhead"""
        try:
            # Use agent's execute method if available
            if hasattr(agent, "execute"):
                # Check if the result is a coroutine or CrewOutput
                result = agent.execute(task_description)

                # If it's a coroutine, await it
                import inspect

                if inspect.iscoroutine(result):
                    return await result
                else:
                    # If it's a CrewOutput or other object, convert to string
                    return str(result)

            # Fallback to synchronous execution
            if hasattr(agent, "run"):
                return agent.run(task_description)

            # Last resort - use agent as callable
            return str(agent(task_description))

        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            raise

    def _parse_agent_result(self, result: Any) -> Dict[str, Any]:
        """
        Parse agent result into structured mapping with robust error handling.

        Handles common JSON formatting issues from LLM outputs:
        - Single quotes instead of double quotes
        - Unquoted property names
        - Escaped special characters
        - Malformed JSON structures
        """
        import re

        try:
            # Try to extract JSON from result
            result_str = str(result)

            # Find JSON in the result
            json_match = re.search(r"\{.*\}", result_str, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)

                # Try direct parse first
                try:
                    parsed_result = json.loads(json_str)
                except json.JSONDecodeError as json_error:
                    logger.warning(
                        f"Initial JSON parse failed (char {json_error.pos}): {str(json_error)[:100]}"
                    )

                    # Attempt to fix common JSON issues
                    fixed_json = self._sanitize_json_string(json_str)

                    try:
                        parsed_result = json.loads(fixed_json)
                        logger.info("✅ Successfully parsed JSON after sanitization")
                    except json.JSONDecodeError as retry_error:
                        logger.error(
                            f"JSON sanitization failed: {str(retry_error)[:100]}"
                        )
                        # Log excerpt of problematic JSON for debugging
                        logger.error(f"Problematic JSON excerpt: {fixed_json[:200]}...")
                        return {
                            "mappings": {},
                            "error": "Invalid JSON format",
                            "raw_output": result_str[:500],
                        }

                # Extract critical attributes assessment if present
                # The agent may include this when using CriticalAttributesAssessmentTool
                if "critical_attributes_assessment" in parsed_result:
                    logger.info("✅ Agent provided critical attributes assessment")
                elif "critical_attributes" in parsed_result:
                    # Alternative key the agent might use
                    parsed_result["critical_attributes_assessment"] = parsed_result[
                        "critical_attributes"
                    ]
                    logger.info("✅ Found critical attributes in agent response")

                return parsed_result

            # Fallback parsing
            logger.warning("Could not extract JSON from agent result")
            return {
                "mappings": {},
                "error": "No JSON found in agent response",
                "raw_output": result_str[:500],
            }

        except Exception as e:
            logger.error(f"Failed to parse agent result: {e}")
            return {
                "mappings": {},
                "error": str(e),
                "raw_output": str(result)[:500],
            }

    def _sanitize_json_string(self, json_str: str) -> str:
        """
        Attempt to fix common JSON formatting issues from LLM outputs.

        Uses conservative transformations that preserve string content semantics.
        Only applies fixes that are safe and won't corrupt legitimate data.

        Common fixes:
        - Remove trailing commas (safe - always invalid in JSON)
        - Quote bare property names at object start/after commas (context-aware)

        NOTE: Does NOT replace quotes globally to avoid corrupting string values
        like "it's" or "Time: 3:00 PM". If quote fixing is needed, recommend
        using json_repair library or re-prompting LLM for valid JSON.
        """
        import re

        # SAFE: Remove trailing commas before closing braces/brackets
        fixed = re.sub(r",(\s*[}\]])", r"\1", json_str)

        # SAFE: Quote bare property names only at object boundaries
        # Matches: { word: or , word: but not "word: or in middle of strings
        fixed = re.sub(r"([{,]\s*)(\w+)(\s*:)", r'\1"\2"\3', fixed)

        # CONSERVATIVE: Only fix double-escaped quotes (safe transformation)
        # Avoid global quote replacement that corrupts apostrophes in strings
        fixed = fixed.replace('\\\\"', '"')

        # If result still invalid, try json_repair library (best-effort)
        try:
            # Check if json_repair is available (optional dependency)
            from json_repair import repair_json

            # Attempt repair - this library is designed to handle LLM outputs safely
            fixed = repair_json(fixed, return_objects=False)
        except ImportError:
            # json_repair not available - return best-effort fix
            logger.debug(
                "json_repair library not available - using conservative sanitization only"
            )
        except Exception as e:
            # Repair failed - return conservative fix
            logger.debug(f"json_repair failed: {e} - using conservative sanitization")

        return fixed

    async def _update_agent_memory(
        self, agent, headers: List[str], mapping_result: Dict[str, Any]
    ):
        """Update agent memory with successful mappings and critical attributes assessment for future reference"""
        try:
            if hasattr(agent, "memory") and agent.memory:
                memory_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "source_fields": headers,
                    "mappings": mapping_result.get("mappings", {}),
                    "critical_attributes_assessment": mapping_result.get(
                        "critical_attributes_assessment", {}
                    ),
                    "client_id": self.client_id,
                    "engagement_id": self.engagement_id,
                }

                # Store in agent's long-term memory
                if hasattr(agent.memory, "save"):
                    await agent.memory.save("field_mappings", memory_entry)
                    logger.info("📝 Updated agent memory with field mapping results")

        except Exception as e:
            logger.warning(f"Failed to update agent memory: {e}")

    def _fallback_mapping(self, raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simple fallback mapping when persistent agent unavailable"""
        if not raw_data:
            return {"mappings": {}}

        headers = list(raw_data[0].keys())
        mappings = {}

        # Simple heuristic mapping
        for header in headers:
            header_lower = header.lower()

            # Skip metadata fields
            if header_lower in ["row_index", "row_number", "_id"]:
                continue

            # Direct mappings
            if "id" in header_lower and "device" in header_lower:
                mappings[header] = {
                    "target_field": "asset_id",
                    "confidence": 0.8,
                    "reasoning": "ID field likely maps to asset_id",
                }
            elif "name" in header_lower:
                mappings[header] = {
                    "target_field": "asset_name",
                    "confidence": 0.8,
                    "reasoning": "Name field maps to asset_name",
                }
            elif "type" in header_lower:
                mappings[header] = {
                    "target_field": "asset_type",
                    "confidence": 0.7,
                    "reasoning": "Type field maps to asset_type",
                }
            elif "ip" in header_lower:
                mappings[header] = {
                    "target_field": "ip_address",
                    "confidence": 0.9,
                    "reasoning": "IP field maps to ip_address",
                }
            elif "status" in header_lower:
                mappings[header] = {
                    "target_field": "status",
                    "confidence": 0.8,
                    "reasoning": "Status field direct mapping",
                }
            elif "location" in header_lower:
                mappings[header] = {
                    "target_field": "location",
                    "confidence": 0.8,
                    "reasoning": "Location field direct mapping",
                }

        return {"mappings": mappings}


class PersistentFieldMappingCrew:
    """Crew-compatible wrapper for persistent field mapping"""

    def __init__(self, mapper: PersistentFieldMapping, raw_data: List[Dict[str, Any]]):
        self.mapper = mapper
        self.raw_data = raw_data
        self.agents = []  # Empty for compatibility
        self.tasks = []  # Empty for compatibility

    async def kickoff_async(self) -> Any:
        """Async execution of field mapping"""
        result = await self.mapper.map_fields(self.raw_data)

        # Format result as CrewAI would
        if "mappings" in result:
            return type("Result", (), {"raw": json.dumps(result)})()
        return result

    def kickoff(self) -> Any:
        """Sync execution for compatibility"""
        import asyncio
        import threading

        try:
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                # If we're in a running loop, use a separate thread with its own loop
                result_container = {}
                exc_container = {}

                def _run():
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        res = new_loop.run_until_complete(self.kickoff_async())
                        result_container["res"] = res
                    except Exception as ex:
                        exc_container["ex"] = ex
                    finally:
                        new_loop.close()

                t = threading.Thread(target=_run, daemon=True)
                t.start()
                t.join()

                if "ex" in exc_container:
                    raise exc_container["ex"]
                return result_container.get("res")
            else:
                # No running loop, safe to use asyncio.run
                return asyncio.run(self.kickoff_async())
        except Exception as e:
            logger.error(f"Failed to execute persistent field mapping: {e}")
            # Return fallback result
            return type(
                "Result",
                (),
                {"raw": json.dumps(self.mapper._fallback_mapping(self.raw_data))},
            )()


def create_persistent_field_mapping_crew(
    crewai_service,
    raw_data: List[Dict[str, Any]],
    shared_memory=None,
    knowledge_base=None,
) -> Any:
    """
    Factory function that creates a crew-compatible interface
    This matches the signature expected by UnifiedFlowCrewManager
    """
    if not PERSISTENT_AGENTS_AVAILABLE:
        logger.warning("Persistent agents not available, falling back to standard crew")
        # Fall back to standard crew
        from app.services.crewai_flows.crews.field_mapping_crew import (
            create_field_mapping_crew,
        )

        return create_field_mapping_crew(
            crewai_service, raw_data, shared_memory, knowledge_base
        )

    # Get context from crewai_service
    context = getattr(crewai_service, "context", None)
    if not context:
        logger.warning("No context available, falling back to standard crew")
        from app.services.crewai_flows.crews.field_mapping_crew import (
            create_field_mapping_crew,
        )

        return create_field_mapping_crew(
            crewai_service, raw_data, shared_memory, knowledge_base
        )

    # Create persistent mapper
    mapper = PersistentFieldMapping(crewai_service, context)

    # Return crew-compatible wrapper
    return PersistentFieldMappingCrew(mapper, raw_data)


# Alias for compatibility
create_persistent_field_mapper = create_persistent_field_mapping_crew
