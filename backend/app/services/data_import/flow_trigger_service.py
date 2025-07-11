"""
Flow Trigger Service Module

Handles flow creation and triggering including:
- Discovery flow creation and triggering
- Master flow orchestration integration
- Flow initialization and setup
- Flow configuration management
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.context import RequestContext
from app.core.exceptions import FlowError

logger = get_logger(__name__)


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
        context: RequestContext
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
            logger.info(f"🚀 Creating Discovery Flow atomically for import {data_import_id}")
            
            # Use existing session for atomicity
            from app.services.master_flow_orchestrator import MasterFlowOrchestrator
            
            # Initialize Master Flow Orchestrator with existing session
            orchestrator = MasterFlowOrchestrator(self.db, context)
            
            logger.info(f"🔍 Creating discovery flow through orchestrator...")
            logger.info(f"🔍 Parameters - import_id: {data_import_id}, client: {self.client_account_id}, engagement: {engagement_id}, user: {user_id}")
            logger.info(f"🔍 Raw data count: {len(file_data) if file_data else 0}")
            
            # Create flow through orchestrator (no commit - transaction stays open)
            flow_result = await orchestrator.create_flow(
                flow_type="discovery",
                flow_name=f"Discovery Import {data_import_id}",
                configuration={
                    "source": "data_import",
                    "import_id": data_import_id,
                    "filename": f"import_{data_import_id}",
                    "import_timestamp": datetime.utcnow().isoformat()
                },
                initial_state={
                    "raw_data": file_data,
                    "data_import_id": data_import_id
                }
            )
            
            # Extract flow_id from result tuple
            if isinstance(flow_result, tuple) and len(flow_result) >= 1:
                master_flow_id = flow_result[0]
                logger.info(f"✅ Discovery flow created atomically: {master_flow_id}")
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
        context: RequestContext
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
            logger.info(f"🚀 Triggering Discovery Flow via MasterFlowOrchestrator for import {data_import_id}")
            
            from app.services.master_flow_orchestrator import MasterFlowOrchestrator
            from app.core.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as fresh_db:
                # Initialize Master Flow Orchestrator with fresh session
                orchestrator = MasterFlowOrchestrator(fresh_db, context)
                
                logger.info(f"🔍 Creating discovery flow through orchestrator...")
                logger.info(f"🔍 Parameters - import_id: {data_import_id}, client: {self.client_account_id}, engagement: {engagement_id}, user: {user_id}")
                logger.info(f"🔍 Raw data count: {len(file_data) if file_data else 0}")
                
                # Create flow through orchestrator (this will automatically kick off)
                flow_result = await orchestrator.create_flow(
                    flow_type="discovery",
                    flow_name=f"Discovery Import {data_import_id}",
                    configuration={
                        "source": "data_import",
                        "import_id": data_import_id,
                        "filename": f"import_{data_import_id}",
                        "import_timestamp": datetime.utcnow().isoformat()
                    },
                    initial_state={
                        "raw_data": file_data,
                        "data_import_id": data_import_id
                    }
                )
                
                # Extract flow_id from result tuple
                if isinstance(flow_result, tuple) and len(flow_result) >= 1:
                    master_flow_id = flow_result[0]
                    logger.info(f"✅ Discovery flow created via orchestrator: {master_flow_id}")
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
        file_data: List[Dict[str, Any]]
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
            "data_preview": file_data[:5] if file_data else []  # Include preview of first 5 records
        }
    
    async def prepare_initial_state(
        self,
        data_import_id: str,
        file_data: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
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
            "state_version": "1.0"
        }
        
        if metadata:
            initial_state["metadata"] = metadata
            
        return initial_state
    
    async def validate_flow_prerequisites(
        self,
        data_import_id: str,
        file_data: List[Dict[str, Any]],
        context: RequestContext
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
        validation_results = {
            "valid": True,
            "issues": [],
            "warnings": []
        }
        
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
            validation_results["warnings"].append(f"Large dataset ({len(file_data)} records) may require additional processing time")
        
        logger.info(f"✅ Flow prerequisites validation completed: {validation_results}")
        return validation_results