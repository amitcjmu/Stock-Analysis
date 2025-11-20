"""
Collection Flow Lifecycle Service

This service handles Collection Flow lifecycle operations including:
- Flow creation with Master Flow Orchestrator (MFO) integration
- Flow status updates and synchronization with MFO
- Flow lifecycle coordination between repository and orchestrator layers

Per architectural pattern: Services handle orchestration, repositories handle data.
"""

import logging
import uuid
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.collection_flow import CollectionFlow
from app.repositories.collection_flow_repository import CollectionFlowRepository
from app.services.master_flow_orchestrator import MasterFlowOrchestrator

logger = logging.getLogger(__name__)


class CollectionFlowLifecycleService:
    """
    Service for Collection Flow lifecycle operations.

    Coordinates between repository (data persistence) and orchestrator (workflow management).
    Follows the MFO two-table pattern: master_flow_id for orchestration, flow_id for data.
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize the Collection Flow Lifecycle Service.

        Args:
            db: Database session
            context: Request context with tenant information
        """
        self.db = db
        self.context = context
        self.repository = CollectionFlowRepository(
            db=db,
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
        )
        self.orchestrator = MasterFlowOrchestrator(db, context)

    async def create_flow_with_orchestration(
        self,
        flow_name: str,
        automation_tier: str,
        flow_metadata: Optional[Dict[str, Any]] = None,
        collection_config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> CollectionFlow:
        """
        Create a new collection flow with Master Flow Orchestrator (MFO) integration.

        This method follows the architectural pattern:
        1. Repository creates child flow data (child flow ID)
        2. Service coordinates with MFO (master flow ID)
        3. Service links the two tables together

        Per MFO two-table pattern (CLAUDE.md):
        - Child flow ID: User-facing identifier (collection_flows.flow_id)
        - Master flow ID: Internal MFO routing (crewai_flow_state_extensions.flow_id)
        - Service layer resolves between the two IDs

        Args:
            flow_name: Name of the collection flow
            automation_tier: Automation tier (tier_1, tier_2, tier_3, tier_4)
            flow_metadata: Optional flow metadata
            collection_config: Optional collection configuration
            **kwargs: Additional parameters (flow_id, user_id, etc.)

        Returns:
            Created CollectionFlow instance with master_flow_id linkage

        Raises:
            Exception: If flow creation or MFO registration fails
        """
        try:
            # Generate child flow_id if not provided
            flow_id = kwargs.get("flow_id") or str(uuid.uuid4())

            # Step 1: Prepare master flow configuration for MFO
            master_flow_config = {
                "flow_name": flow_name,
                "automation_tier": automation_tier,
                "metadata": flow_metadata or {},
                "collection_config": collection_config or {},
            }

            # Step 2: Prepare master flow initial state
            initial_state = {
                "current_phase": "initialization",
                "progress_percentage": 0.0,
                "collection_config": collection_config or {},
                "flow_metadata": flow_metadata or {},
            }

            # Step 3: Register flow with Master Flow Orchestrator (ADR-006 pattern)
            # This creates the master flow record (MFO routing)
            master_flow_id, master_flow_data = await self.orchestrator.create_flow(
                flow_type="collection",
                flow_name=flow_name,
                configuration=master_flow_config,
                initial_state=initial_state,
                atomic=True,  # Prevents internal commits
            )

            # Step 4: Flush to make master flow ID available for FK relationship
            await self.db.flush()

            logger.info(
                f"✅ Master flow created for collection: "
                f"master_flow_id={master_flow_id}, child_flow_id={flow_id}"
            )

            # Step 5: Create child collection flow with repository
            # Repository ONLY handles data persistence, NO orchestration
            collection_flow = await self.repository.create_with_master_flow(
                flow_id=flow_id,
                flow_name=flow_name,
                automation_tier=automation_tier,
                master_flow_id=master_flow_id,
                flow_metadata=flow_metadata,
                collection_config=collection_config,
                **kwargs,
            )

            # Transaction will be automatically committed by get_db() context manager
            logger.info(
                f"✅ Collection flow created with MFO integration: "
                f"flow_id={flow_id}, master_flow_id={master_flow_id}"
            )

            return collection_flow

        except Exception as e:
            logger.error(
                f"Failed to create collection flow with orchestration: {str(e)}"
            )
            await self.db.rollback()
            raise

    async def get_flow(self, flow_id: str) -> Optional[CollectionFlow]:
        """
        Get collection flow by child flow ID.

        Args:
            flow_id: Child flow ID (user-facing identifier)

        Returns:
            CollectionFlow instance or None
        """
        return await self.repository.get_by_flow_id(flow_id)

    async def update_flow_status(
        self,
        flow_id: str,
        status: str,
        current_phase: Optional[str] = None,
        progress_percentage: Optional[float] = None,
    ) -> Optional[CollectionFlow]:
        """
        Update collection flow status.

        Delegates to repository for data persistence.

        Args:
            flow_id: Child flow ID
            status: New status
            current_phase: Optional phase update
            progress_percentage: Optional progress update

        Returns:
            Updated CollectionFlow instance or None
        """
        return await self.repository.update_status(
            flow_id=flow_id,
            status=status,
            current_phase=current_phase,
            progress_percentage=progress_percentage,
        )
