"""
Flow Execution Engine Discovery Crew
Discovery-specific CrewAI execution methods and phase handlers.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import select

from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

# UnifiedFlowCrewManager import moved to discovery_phase_handlers.py
from .asset_creation_tools import AssetCreationToolsExecutor
from .discovery_phase_handlers import DiscoveryPhaseHandlers
from .field_mapping_logic import FieldMappingLogic

logger = get_logger(__name__)


class DictStateAdapter:
    """Adapter to make a dict work as a state object for UnifiedFlowCrewManager."""

    def __init__(self, data: Dict[str, Any]):
        """Initialize adapter with dict data as attributes."""
        self._errors: List[Dict[str, str]] = []
        # Prevent overwriting internal attributes
        for k, v in data.items():
            if k.startswith("_"):
                continue
            setattr(self, k, v)

    def add_error(self, key: str, message: str):
        """Add an error to the state."""
        self._errors.append({"key": key, "message": message})


class ExecutionEngineDiscoveryCrews:
    """Discovery flow CrewAI execution handlers."""

    def __init__(self, crew_utils, context=None, db_session=None):
        self.crew_utils = crew_utils
        self.field_mapping_logic = FieldMappingLogic()
        self.phase_handlers = DiscoveryPhaseHandlers(context)
        self.context = context
        self.service_registry = None
        self.db_session = db_session

    def set_service_registry(self, service_registry):
        """Set the ServiceRegistry for this discovery crews instance."""
        self.service_registry = service_registry

    async def execute_discovery_phase(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_config,
        phase_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Main entry point for discovery phase execution.

        Routes to appropriate phase method based on phase name.
        """
        phase_name = phase_config.name
        logger.info(f"🎯 Executing discovery phase: {phase_name}")

        # Define phase-to-method mapping
        phase_methods = {
            "asset_creation": self._execute_discovery_asset_inventory,  # Asset creation is part of inventory (ADR-022)
            "asset_inventory": self._execute_discovery_asset_inventory,
            # Add other phases as needed
        }

        # Map phase to execution method
        execution_method = phase_methods.get(phase_name)

        if execution_method:
            logger.info(
                f"📍 Mapped phase '{phase_name}' to method: {execution_method.__name__}"
            )
            return await execution_method(
                None, phase_input
            )  # agent_pool not used in persistent agent pattern
        else:
            # Use generic phase handler for unmapped phases
            logger.warning(f"⚠️ Phase '{phase_name}' not mapped, using generic handler")
            return await self._execute_discovery_generic_phase(None, phase_input)

    async def _get_approved_field_mappings(self, phase_input: Dict[str, Any]) -> Dict:
        """Get approved field mappings from database with correct model and filters"""
        try:
            # CORRECTED: Use correct import path
            from app.models.data_import.mapping import ImportFieldMapping

            data_import_id = phase_input.get("data_import_id")
            if not data_import_id:
                logger.warning("No data_import_id in phase_input")
                return {}

            # CORRECTED: Use provided session, not open new one
            session = self.db_session if hasattr(self, "db_session") else self.db

            # CORRECTED: Use status='approved' and add multi-tenant scoping
            result = await session.execute(
                select(ImportFieldMapping).where(
                    ImportFieldMapping.data_import_id == data_import_id,
                    ImportFieldMapping.status == "approved",  # CORRECTED field
                    ImportFieldMapping.client_account_id
                    == self.context.client_account_id,
                    ImportFieldMapping.engagement_id == self.context.engagement_id,
                )
            )
            mappings = result.scalars().all()

            # Convert to dict, exclude UNMAPPED targets
            # CRITICAL FIX: Reverse mapping - we need target -> source to look up CSV fields
            field_mappings = {
                m.target_field: m.source_field
                for m in mappings
                if m.target_field and m.target_field != "UNMAPPED"
            }

            logger.info(f"📋 Retrieved {len(field_mappings)} approved field mappings")
            return field_mappings

        except Exception as e:
            logger.warning(f"⚠️ Could not retrieve field mappings: {e}")
            return {}

    async def _get_discovery_flow_id(self, master_flow_id: str) -> Optional[str]:
        """Get internal discovery flow ID from master flow ID"""
        if not master_flow_id:
            return None

        try:
            from app.models.discovery_flow import DiscoveryFlow

            session = self.db_session if hasattr(self, "db_session") else self.db
            result = await session.execute(
                select(DiscoveryFlow.id).where(
                    DiscoveryFlow.master_flow_id == master_flow_id
                )
            )
            discovery_flow = result.scalar_one_or_none()
            return str(discovery_flow) if discovery_flow else None
        except Exception as e:
            logger.warning(f"Could not get discovery_flow_id: {e}")
            return None

    async def _normalize_assets_for_creation(
        self,
        raw_data: List[Dict],
        field_mappings: Dict,
        master_flow_id: str,
        discovery_flow_id: str,
    ) -> List[Dict]:
        """Normalize raw data for asset creation with proper linking"""
        normalized = []

        # Get raw_import_records if we need to link them
        raw_import_records_map = {}
        if hasattr(self, "db_session"):
            try:
                from app.models.raw_import_record import RawImportRecord

                result = await self.db_session.execute(
                    select(RawImportRecord)
                    .where(RawImportRecord.master_flow_id == master_flow_id)
                    .order_by(RawImportRecord.row_number)
                )
                raw_records = result.scalars().all()
                # Map by row number for correlation
                raw_import_records_map = {r.row_number - 1: r.id for r in raw_records}
                logger.info(
                    f"📋 Found {len(raw_import_records_map)} raw_import_records to link"
                )
            except Exception as e:
                logger.warning(f"Could not load raw_import_records for linking: {e}")

        # Process each record
        for idx, record in enumerate(raw_data):
            # Helper functions extracted from database_operations.py
            def get_mapped_value(record, field, mappings):
                """Get value using field mapping or direct field"""
                if field in mappings:
                    source_field = mappings[field]
                    return record.get(source_field)
                return record.get(field)

            def determine_asset_type(record, mappings):
                """Determine asset type from record - respect mapped value"""
                asset_type = get_mapped_value(record, "asset_type", mappings)
                if asset_type:
                    # Map common variations to standard types
                    type_lower = asset_type.lower()
                    if "application" in type_lower or "app" in type_lower:
                        return "application"
                    elif "server" in type_lower:
                        return "server"
                    elif "database" in type_lower or "db" in type_lower:
                        return "database"
                    elif "device" in type_lower or "network" in type_lower:
                        return "device"
                    else:
                        return type_lower

                # Only use fallback if no asset_type mapping exists
                return "device"  # Default

            # Get mapped values - CRITICAL FIX: Use "name" not "asset_name"
            asset_name = get_mapped_value(record, "name", field_mappings)
            hostname = get_mapped_value(record, "hostname", field_mappings)
            ip_address = get_mapped_value(record, "ip_address", field_mappings)

            # CRITICAL FIX: Don't generate names - use actual mapped value or skip
            if not asset_name:
                # Log warning but still try to use hostname/ip as fallback
                logger.warning(
                    f"No name found for record {idx+1}, using fallback: {hostname or ip_address or 'unnamed'}"
                )
                asset_name = hostname or ip_address or f"unnamed_asset_{idx+1}"

            # Build asset data with explicit flow IDs and raw_import_record linking
            asset_data = {
                "name": asset_name,
                "asset_type": determine_asset_type(record, field_mappings),
                "hostname": hostname,
                "ip_address": ip_address,
                "operating_system": get_mapped_value(
                    record, "operating_system", field_mappings
                ),
                "environment": get_mapped_value(record, "environment", field_mappings)
                or "production",
                "status": get_mapped_value(record, "status", field_mappings),
                "location": get_mapped_value(record, "location", field_mappings),
                # Explicit flow IDs
                "master_flow_id": master_flow_id,
                "discovery_flow_id": discovery_flow_id,
                "flow_id": discovery_flow_id,  # Some code expects flow_id
                # Link to raw_import_record if available
                "raw_import_records_id": raw_import_records_map.get(idx),
                # Unmapped fields to custom_attributes
                "custom_attributes": {
                    k: v
                    for k, v in record.items()
                    if k not in field_mappings.values()  # Check against source fields
                },
                "raw_data": record,
            }

            normalized.append(asset_data)

        logger.info(f"✅ Normalized {len(normalized)}/{len(raw_data)} records")
        if normalized:
            # Log sample without sensitive data
            sample = {k: type(v).__name__ for k, v in normalized[0].items()}
            logger.debug(f"📊 Sample asset structure: {sample}")

        return normalized

    async def execute_discovery_phase_with_persistent_agents(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_config,
        phase_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute discovery flow phase using persistent agents (ADR-015)"""

        # ADR-015: Use ONLY persistent agents - no fallback to service pattern
        logger.info(f"🔄 Executing phase '{phase_config.name}' with persistent agents")

        # Add flow context to phase_input for proper persistence
        phase_input["flow_id"] = master_flow.id
        phase_input["client_account_id"] = master_flow.client_account_id
        phase_input["engagement_id"] = master_flow.engagement_id

        # Get data_import_id from flow_metadata if available
        if hasattr(master_flow, "flow_metadata") and master_flow.flow_metadata:
            # flow_metadata is a JSONB column, accessed directly
            if isinstance(master_flow.flow_metadata, dict):
                phase_input["data_import_id"] = master_flow.flow_metadata.get(
                    "data_import_id"
                )

        # Retrieve flow data from persistence to ensure raw_data is available
        logger.info(
            f"🔍 Flow persistence data exists: {master_flow.flow_persistence_data is not None}"
        )

        if master_flow.flow_persistence_data:
            logger.info(
                f"🔍 Flow persistence keys: {list(master_flow.flow_persistence_data.keys())}"
            )

            # Always ensure raw_data is transferred from flow persistence
            # Check both direct raw_data and nested structures
            raw_data = None

            if "raw_data" in master_flow.flow_persistence_data:
                raw_data = master_flow.flow_persistence_data["raw_data"]
                logger.info("✅ Found raw_data in flow_persistence_data")
            elif "initial_state" in master_flow.flow_persistence_data:
                # Check if raw_data is nested in initial_state
                initial_state = master_flow.flow_persistence_data["initial_state"]
                if isinstance(initial_state, dict) and "raw_data" in initial_state:
                    raw_data = initial_state["raw_data"]
                    logger.info(
                        "✅ Found raw_data in flow_persistence_data.initial_state"
                    )

            if raw_data is not None:
                # Always set raw_data in phase_input, even if it already exists (ensure latest data)
                phase_input["raw_data"] = raw_data

                # Safely get the count of records
                try:
                    record_count = len(raw_data) if raw_data is not None else 0
                except (TypeError, AttributeError):
                    # Handle cases where raw_data is not a sized iterable
                    record_count = 1 if raw_data is not None else 0

                logger.info(
                    f"📊 Retrieved {record_count} records from flow persistence for phase execution"
                )
            else:
                logger.warning("⚠️ No raw_data found in flow_persistence_data structure")
        else:
            logger.warning("⚠️ No flow_persistence_data available on master_flow")

        try:
            # Initialize persistent agent pool
            agent_pool = await self._initialize_discovery_agent_pool(master_flow)

        except ValueError as e:
            if "object has no field" in str(e):
                logger.error(
                    f"❌ Pydantic field validation error in agent creation: {e}"
                )
                logger.error(
                    "🔧 Hint: This is likely a CrewAI/Pydantic v2 compatibility issue"
                )
                logger.error("🔧 Check AgentWrapper implementation in agent_config.py")
                return self.crew_utils.build_error_response(
                    phase_config.name,
                    f"Agent creation failed due to Pydantic v2 compatibility: {str(e)}",
                    master_flow,
                )
            else:
                logger.error(
                    f"❌ ValueError in discovery phase '{phase_config.name}': {e}"
                )
                return self.crew_utils.build_error_response(
                    phase_config.name, str(e), master_flow
                )
        except Exception as e:
            logger.error(f"❌ Discovery phase '{phase_config.name}' failed: {e}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            import traceback

            logger.error(f"❌ Full traceback:\n{traceback.format_exc()}")
            return self.crew_utils.build_error_response(
                phase_config.name, str(e), master_flow
            )

        try:
            # Map and execute phase
            mapped_phase = self._map_discovery_phase_name(phase_config.name)
            logger.info(
                f"🗺️ Mapped phase '{phase_config.name}' to '{mapped_phase}' for agent execution"
            )

            # Execute the specific phase
            result = await self._execute_discovery_mapped_phase(
                mapped_phase, agent_pool, phase_input
            )

            logger.info(
                f"✅ Discovery phase '{mapped_phase}' completed using persistent agents"
            )

            return {
                "phase": phase_config.name,
                "status": "completed",
                "crew_results": result,
                "method": "persistent_agent_execution",
                "agents_used": result.get("agents", [result.get("agent")]),
            }

        except Exception as e:
            logger.error(f"❌ Discovery phase failed: {e}")
            return self.crew_utils.build_error_response(phase_config.name, str(e))

    async def _initialize_discovery_agent_pool(
        self, master_flow: CrewAIFlowStateExtensions
    ) -> Dict[str, Any]:
        """Initialize persistent agent pool for the tenant with ServiceRegistry support"""
        try:
            # Import here to avoid circular dependencies
            from app.services.persistent_agents.tenant_scoped_agent_pool import (
                TenantScopedAgentPool,
            )

            agent_pool = await TenantScopedAgentPool.initialize_tenant_pool(
                client_id=master_flow.client_account_id,
                engagement_id=master_flow.engagement_id,
            )

            logger.info(
                f"🏊 Initialized agent pool for tenant {master_flow.client_account_id}"
            )
            return agent_pool

        except Exception as e:
            logger.error(f"❌ Failed to initialize agent pool: {e}")
            raise

    def _map_discovery_phase_name(self, phase_name: str) -> str:
        """Map flow phase names to discovery service methods"""
        phase_mapping = {
            "data_import": "data_import_validation",
            "field_mapping": "field_mapping",
            "data_cleansing": "data_cleansing",
            "asset_creation": "asset_creation",
            "asset_inventory": "asset_inventory",
            "analysis": "analysis",
        }
        return phase_mapping.get(phase_name, phase_name)

    async def _execute_discovery_mapped_phase(
        self, mapped_phase: str, agent_pool: Dict[str, Any], phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute mapped discovery phase"""
        phase_methods = {
            "data_import_validation": self.phase_handlers.execute_data_import_validation,
            "field_mapping": self._execute_discovery_field_mapping,
            "data_cleansing": self.phase_handlers.execute_data_cleansing,
            "asset_creation": self._execute_discovery_asset_inventory,  # Asset creation is part of inventory (ADR-022)
            "asset_inventory": self._execute_discovery_asset_inventory,
            "analysis": self.phase_handlers.execute_analysis,
        }

        method = phase_methods.get(mapped_phase, self._execute_discovery_generic_phase)
        return await method(agent_pool, phase_input)

    async def _execute_discovery_field_mapping(
        self, agent_pool: Dict[str, Any], phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute field mapping phase - delegated to specialized handler"""
        return await self.field_mapping_logic.execute_discovery_field_mapping(
            agent_pool, phase_input, self.db_session
        )

    # REMOVED: _execute_discovery_asset_creation placeholder
    # Asset creation is now part of asset_inventory phase per ADR-022
    # The asset_inventory phase handles both creation and inventory

    async def _execute_discovery_asset_inventory(
        self, agent_pool: Dict[str, Any], phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute asset inventory phase using persistent agent"""
        logger.info("📦 Executing discovery asset inventory using persistent agent")

        data_import_id = phase_input.get("data_import_id")
        if not data_import_id:
            raise ValueError("No data_import_id provided")

        # CORRECT IMPORTS
        from sqlalchemy import func
        from app.models.data_import.core import RawImportRecord  # CORRECT PATH

        # Query for cleansed data WITH TENANT SCOPING using self.db_session
        result = await self.db_session.execute(  # USE db_session
            select(RawImportRecord).where(
                RawImportRecord.data_import_id == data_import_id,
                RawImportRecord.cleansed_data.isnot(None),
                RawImportRecord.client_account_id
                == self.context.client_account_id,  # TENANT
                RawImportRecord.engagement_id == self.context.engagement_id,  # TENANT
            )
        )
        records = result.scalars().all()

        cleansed_count = len(records)

        # Count raw records for comparison
        raw_result = await self.db_session.execute(
            select(func.count(RawImportRecord.id)).where(
                RawImportRecord.data_import_id == data_import_id,
                RawImportRecord.client_account_id == self.context.client_account_id,
                RawImportRecord.engagement_id == self.context.engagement_id,
            )
        )
        raw_count = raw_result.scalar()

        logger.info(
            f"📊 Using cleansed rows: {cleansed_count}; raw fallback: 0 (blocked)"
        )

        # NO FALLBACK - fail if no cleansed data
        if cleansed_count == 0:
            return {
                "status": "error",
                "error_code": "CLEANSING_REQUIRED",
                "message": "No cleansed data available. Run data cleansing first.",
                "counts": {"raw": raw_count, "cleansed": 0},
            }

        # Extract cleansed data
        cleansed_data = [r.cleansed_data for r in records]

        # Get field mappings
        field_mappings = await self._get_approved_field_mappings(phase_input)
        logger.info(f"📋 Retrieved {len(field_mappings)} approved field mappings")

        # Get flow IDs
        master_flow_id = phase_input.get("master_flow_id") or phase_input.get("flow_id")
        discovery_flow_id = await self._get_discovery_flow_id(master_flow_id)

        # Normalize using cleansed data
        normalized_assets = await self._normalize_assets_for_creation(
            cleansed_data,  # USE CLEANSED DATA
            field_mappings,
            master_flow_id,
            discovery_flow_id,
        )

        logger.info(f"✅ Normalized {len(normalized_assets)}/{cleansed_count} records")

        # Get persistent agent for asset creation (use same pattern as cleansing)
        # Build context from self.context (ExecutionEngineDiscoveryCrews has it)
        request_context = self.context  # Already a RequestContext

        from app.services.persistent_agents.tenant_scoped_agent_pool import (
            TenantScopedAgentPool,
        )

        inventory_agent = await TenantScopedAgentPool.get_agent(
            context=request_context,
            agent_type="asset_inventory",
            service_registry=self.service_registry,  # Pass existing service_registry
        )

        logger.info("🔧 Retrieved agent: asset_inventory")
        logger.info("Agent tools: ['asset_creator','bulk_asset_creator']")

        # Continue with asset creation using the inventory agent
        try:
            # Use the persistent agent to create assets from normalized data
            # Prepare task description for the agent
            task_description = "Create database asset records from cleaned CMDB data"

            # Execute asset creation with the persistent agent
            # AssetCreationToolsExecutor already imported at module level

            result = await AssetCreationToolsExecutor.execute_asset_creation_with_tools(
                inventory_agent, {"raw_data": normalized_assets}, task_description
            )

            # Extract actual counts from result
            assets_created = 0
            assets_failed = 0

            if isinstance(result, dict):
                assets_created = result.get("assets_created", 0)
                # Calculate failed count: total normalized - created
                total_normalized = len(normalized_assets)
                assets_failed = max(0, total_normalized - assets_created)

            # 5. Log asset creation results as specified
            logger.info(
                f"🔨 Asset creation result: created={assets_created}, failed={assets_failed}"
            )

            # Maintain backward compatibility with asset_inventory field
            asset_inventory = (
                result.get(
                    "asset_inventory",
                    {"total_assets": assets_created, "classification_complete": True},
                )
                if isinstance(result, dict)
                else {"total_assets": 0, "classification_complete": False}
            )

            return {
                "phase": "asset_inventory",
                "status": "completed",
                "crew_results": result,
                "asset_inventory": asset_inventory,  # Backward compatibility
                "agent": "asset_inventory_agent",
                "method": "persistent_agent_execution",
                "assets_created": assets_created,  # Return actual counts
                "assets_failed": assets_failed,
            }
        except Exception as e:
            logger.error(f"Asset inventory failed: {str(e)}")
            return {
                "phase": "asset_inventory",
                "status": "error",
                "error": str(e),
                "asset_inventory": {
                    "total_assets": 0,
                    "classification_complete": False,
                },
                "agent": "asset_inventory_agent",
                "assets_created": 0,
                "assets_failed": 0,
            }

    async def _execute_discovery_generic_phase(
        self, agent_pool: Dict[str, Any], phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute generic discovery phase"""
        logger.info("⚡ Executing generic discovery phase")

        # Generic phase execution
        return {
            "phase": "generic",
            "status": "completed",
            "result": "Generic phase execution completed",
            "agent": "generic_agent",
        }
