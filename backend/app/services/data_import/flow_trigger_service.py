"""
Flow Trigger Service Module

Handles flow creation and triggering including:
- Discovery flow creation and triggering
- Master flow orchestration integration
- Flow initialization and setup
- Flow configuration management
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.exceptions import FlowError
from app.core.logging import get_logger

logger = get_logger(__name__)


def convert_uuids_to_str(obj: Any) -> Any:
    """
    Recursively convert UUID objects to strings for JSON serialization.
    🔧 CC FIX: Prevents 'Object of type UUID is not JSON serializable' errors
    """
    if isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: convert_uuids_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return type(obj)(convert_uuids_to_str(item) for item in obj)
    return obj


class FlowTriggerService:
    """
    Manages flow creation and triggering operations.
    """

    def __init__(self, db: AsyncSession, client_account_id: str):
        self.db = db
        self.client_account_id = client_account_id

    async def trigger_discovery_flow_atomic(
        self,
        data_import_id: str,
        engagement_id: str,
        user_id: str,
        file_data: List[Dict[str, Any]],
        context: RequestContext,
    ) -> Optional[str]:
        """
        Trigger Discovery Flow through MasterFlowOrchestrator with atomic transaction.

        This method accepts an existing database session to ensure atomicity.
        All operations (import, flow creation, field mapping) happen in single transaction.

        Args:
            data_import_id: ID of the data import
            engagement_id: Engagement ID
            user_id: User ID
            file_data: Raw import data
            context: Request context

        Returns:
            Optional[str]: The flow_id if successful, None otherwise
        """
        try:
            logger.info(
                f"🚀 Creating Discovery Flow atomically for import {data_import_id}"
            )

            # Use existing session for atomicity
            from app.services.master_flow_orchestrator import MasterFlowOrchestrator

            # Initialize Master Flow Orchestrator with existing session
            orchestrator = MasterFlowOrchestrator(self.db, context)

            logger.info("🔍 Creating discovery flow through orchestrator...")
            logger.info(
                f"🔍 Parameters - import_id: {data_import_id}, client: {self.client_account_id}, "
                f"engagement: {engagement_id}, user: {user_id}"
            )
            logger.info(f"🔍 Raw data count: {len(file_data) if file_data else 0}")

            # Create flow through orchestrator (no commit - transaction stays open)
            # 🔧 CC FIX: Convert UUIDs to strings to prevent JSON serialization errors
            configuration = convert_uuids_to_str(
                {
                    "source": "data_import",
                    "import_id": data_import_id,
                    "filename": f"import_{data_import_id}",
                    "import_timestamp": datetime.utcnow().isoformat(),
                }
            )

            initial_state = convert_uuids_to_str(
                {"raw_data": file_data, "data_import_id": data_import_id}
            )

            flow_result = await orchestrator.create_flow(
                flow_type="discovery",
                flow_name=f"Discovery Import {data_import_id}",
                configuration=configuration,
                initial_state=initial_state,
                atomic=True,  # 🔧 CC FIX: Use atomic mode to prevent immediate commit
            )

            # Extract flow_id from result tuple
            if isinstance(flow_result, tuple) and len(flow_result) >= 1:
                master_flow_id = flow_result[0]
                logger.info(f"✅ Master flow created atomically: {master_flow_id}")

                # 🔧 CC FIX: Now create the actual discovery flow that links to this master flow
                # This is the missing piece - we need BOTH master flow AND discovery flow
                try:
                    # Generate unique discovery flow ID for CrewAI
                    import uuid

                    from app.services.discovery_flow_service import DiscoveryFlowService

                    discovery_flow_id = str(uuid.uuid4())

                    # Create discovery flow service
                    discovery_service = DiscoveryFlowService(self.db, context)

                    # Create the discovery flow linked to the master flow
                    # 🔧 CC FIX: Convert UUIDs to strings to prevent JSON serialization errors
                    metadata = convert_uuids_to_str(
                        {
                            "source": "data_import",
                            "import_id": data_import_id,
                            "master_flow_id": master_flow_id,
                            "import_timestamp": datetime.utcnow().isoformat(),
                        }
                    )

                    await discovery_service.create_discovery_flow(
                        flow_id=discovery_flow_id,
                        raw_data=file_data,
                        metadata=metadata,
                        data_import_id=data_import_id,
                        user_id=user_id,
                        master_flow_id=master_flow_id,  # 🔧 CC FIX: Pass existing master flow ID
                    )

                    logger.info(
                        f"✅ Discovery flow created and linked: {discovery_flow_id}"
                    )
                    logger.info(f"   Master Flow ID: {master_flow_id}")
                    logger.info(f"   Discovery Flow ID: {discovery_flow_id}")

                    # Return the master flow ID for foreign key linkage in storage manager
                    # 🔧 CC FIX: Storage manager needs master_flow_id for foreign key constraint
                    return master_flow_id

                except Exception as discovery_error:
                    logger.error(
                        f"❌ Failed to create discovery flow after master flow: {discovery_error}"
                    )
                    # Don't fail the entire import - master flow exists
                    # Return the master flow ID so at least the import can be linked
                    logger.error(
                        "❌ CRITICAL: Master flow created but discovery flow failed - continuing with master flow only"
                    )
                    return master_flow_id

            else:
                logger.error(f"❌ Unexpected flow creation result: {flow_result}")
                return None

        except Exception as e:
            logger.error(f"❌ Atomic discovery flow creation failed: {e}")
            import traceback

            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise FlowError(f"Failed to create discovery flow: {str(e)}")

    async def trigger_discovery_flow(
        self,
        data_import_id: str,
        engagement_id: str,
        user_id: str,
        file_data: List[Dict[str, Any]],
        context: RequestContext,
    ) -> Optional[str]:
        """
        Trigger Discovery Flow through MasterFlowOrchestrator (non-atomic version).

        This method creates a new database session and is used for standalone flow creation.

        Args:
            data_import_id: ID of the data import
            engagement_id: Engagement ID
            user_id: User ID
            file_data: Raw import data
            context: Request context

        Returns:
            Optional[str]: The flow_id if successful, None otherwise
        """
        try:
            logger.info(
                f"🚀 Triggering Discovery Flow via MasterFlowOrchestrator for import {data_import_id}"
            )

            from app.core.database import AsyncSessionLocal
            from app.services.master_flow_orchestrator import MasterFlowOrchestrator

            async with AsyncSessionLocal() as fresh_db:
                # Initialize Master Flow Orchestrator with fresh session
                orchestrator = MasterFlowOrchestrator(fresh_db, context)

                logger.info("🔍 Creating discovery flow through orchestrator...")
                logger.info(
                    f"🔍 Parameters - import_id: {data_import_id}, client: {self.client_account_id}, "
                    f"engagement: {engagement_id}, user: {user_id}"
                )
                logger.info(f"🔍 Raw data count: {len(file_data) if file_data else 0}")

                # Create flow through orchestrator (this will automatically kick off)
                flow_result = await orchestrator.create_flow(
                    flow_type="discovery",
                    flow_name=f"Discovery Import {data_import_id}",
                    configuration={
                        "source": "data_import",
                        "import_id": data_import_id,
                        "filename": f"import_{data_import_id}",
                        "import_timestamp": datetime.utcnow().isoformat(),
                    },
                    initial_state={
                        "raw_data": file_data,
                        "data_import_id": data_import_id,
                    },
                )

                # Extract flow_id from result tuple
                if isinstance(flow_result, tuple) and len(flow_result) >= 1:
                    master_flow_id = flow_result[0]
                    logger.info(
                        f"✅ Discovery flow created via orchestrator: {master_flow_id}"
                    )
                    return master_flow_id
                else:
                    logger.error(f"❌ Unexpected flow creation result: {flow_result}")
                    return None

        except Exception as e:
            logger.error(f"❌ Discovery Flow trigger failed: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            raise FlowError(f"Failed to trigger discovery flow: {str(e)}")

    async def prepare_flow_configuration(
        self,
        data_import_id: str,
        filename: str,
        import_type: str,
        file_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Prepare configuration for flow creation.

        Args:
            data_import_id: ID of the data import
            filename: Name of the imported file
            import_type: Type of import (e.g., 'cmdb', 'applications')
            file_data: Raw import data

        Returns:
            Dict containing flow configuration
        """
        return {
            "source": "data_import",
            "import_id": data_import_id,
            "filename": filename,
            "import_type": import_type,
            "import_timestamp": datetime.utcnow().isoformat(),
            "record_count": len(file_data) if file_data else 0,
            "data_preview": (
                file_data[:5] if file_data else []
            ),  # Include preview of first 5 records
        }

    async def prepare_initial_state(
        self,
        data_import_id: str,
        file_data: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Prepare initial state for flow creation.

        Args:
            data_import_id: ID of the data import
            file_data: Raw import data
            metadata: Additional metadata

        Returns:
            Dict containing initial state data
        """
        initial_state = {
            "raw_data": file_data,
            "data_import_id": data_import_id,
            "initialization_timestamp": datetime.utcnow().isoformat(),
            "state_version": "1.0",
        }

        if metadata:
            initial_state["metadata"] = metadata

        return initial_state

    async def validate_flow_prerequisites(
        self,
        data_import_id: str,
        file_data: List[Dict[str, Any]],
        context: RequestContext,
    ) -> Dict[str, Any]:
        """
        Validate prerequisites for flow creation.

        Args:
            data_import_id: ID of the data import
            file_data: Raw import data
            context: Request context

        Returns:
            Dict containing validation results
        """
        validation_results = {"valid": True, "issues": [], "warnings": []}

        # Check if data exists
        if not file_data:
            validation_results["valid"] = False
            validation_results["issues"].append("No data provided for flow creation")

        # Check context validity
        if not context.client_account_id:
            validation_results["valid"] = False
            validation_results["issues"].append("Missing client account ID")

        if not context.engagement_id:
            validation_results["valid"] = False
            validation_results["issues"].append("Missing engagement ID")

        if not context.user_id:
            validation_results["valid"] = False
            validation_results["issues"].append("Missing user ID")

        # Check data quality
        if file_data and len(file_data) > 10000:
            validation_results["warnings"].append(
                f"Large dataset ({len(file_data)} records) may require additional processing time"
            )

        logger.info(f"✅ Flow prerequisites validation completed: {validation_results}")
        return validation_results
