"""
Handler Registry

Registry for custom phase handlers and flow lifecycle hooks.
Provides a centralized system for registering and executing custom business logic.
"""

import inspect
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional

from app.core.context import RequestContext

logger = logging.getLogger(__name__)


class HandlerType(Enum):
    """Types of handlers"""
    PRE_PHASE = "pre_phase"          # Run before phase execution
    POST_PHASE = "post_phase"        # Run after phase execution
    COMPLETION = "completion"        # Run on phase completion
    ERROR = "error"                  # Run on phase error
    INITIALIZATION = "initialization"  # Run on flow initialization
    FINALIZATION = "finalization"    # Run on flow finalization
    ASSET_CREATION = "asset_creation"  # Run when creating assets
    CUSTOM = "custom"                # Custom handler type


@dataclass
class HandlerResult:
    """Result of handler execution"""
    success: bool
    data: Dict[str, Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        self.data = self.data or {}
        self.metadata = self.metadata or {}


# Type alias for handler functions
HandlerFunc = Callable[..., Awaitable[HandlerResult]]


class HandlerRegistry:
    """
    Registry for custom phase handlers.
    Handlers can be registered globally or for specific flow types and phases.
    """
    
    def __init__(self):
        # Global handlers
        self._global_handlers: Dict[str, HandlerFunc] = {}
        
        # Flow-type specific handlers
        self._flow_handlers: Dict[str, Dict[str, HandlerFunc]] = {}
        
        # Phase-specific handlers
        self._phase_handlers: Dict[str, Dict[str, Dict[str, HandlerFunc]]] = {}
        
        # Handler metadata
        self._handler_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Built-in handlers
        self._register_builtin_handlers()
        
        logger.info("✅ Handler Registry initialized")
    
    def register_handler(
        self,
        name: str,
        handler: HandlerFunc,
        handler_type: HandlerType = HandlerType.CUSTOM,
        flow_type: Optional[str] = None,
        phase: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a handler function
        
        Args:
            name: Unique name for the handler
            handler: Async function that performs the action
            handler_type: Type of handler
            flow_type: Optional flow type to restrict handler to
            phase: Optional phase to restrict handler to (requires flow_type)
            description: Optional description of what the handler does
            metadata: Optional metadata about the handler
            
        Raises:
            ValueError: If handler is invalid or name already exists
        """
        # Validate the handler function
        if not callable(handler):
            raise ValueError("Handler must be callable")
        
        if not inspect.iscoroutinefunction(handler):
            raise ValueError("Handler must be async function")
        
        # Store metadata
        self._handler_metadata[name] = {
            "type": handler_type,
            "description": description or "",
            "metadata": metadata or {}
        }
        
        # Register based on scope
        if flow_type and phase:
            # Phase-specific handler
            if flow_type not in self._phase_handlers:
                self._phase_handlers[flow_type] = {}
            if phase not in self._phase_handlers[flow_type]:
                self._phase_handlers[flow_type][phase] = {}
            
            if name in self._phase_handlers[flow_type][phase]:
                raise ValueError(f"Phase handler '{name}' already exists for {flow_type}.{phase}")
            
            self._phase_handlers[flow_type][phase][name] = handler
            logger.info(f"✅ Registered phase handler: {name} for {flow_type}.{phase}")
            
        elif flow_type:
            # Flow-type specific handler
            if flow_type not in self._flow_handlers:
                self._flow_handlers[flow_type] = {}
            
            if name in self._flow_handlers[flow_type]:
                raise ValueError(f"Flow handler '{name}' already exists for {flow_type}")
            
            self._flow_handlers[flow_type][name] = handler
            logger.info(f"✅ Registered flow handler: {name} for {flow_type}")
            
        else:
            # Global handler
            if name in self._global_handlers:
                raise ValueError(f"Global handler '{name}' already exists")
            
            self._global_handlers[name] = handler
            logger.info(f"✅ Registered global handler: {name}")
    
    def get_handler(
        self,
        name: str,
        flow_type: Optional[str] = None,
        phase: Optional[str] = None
    ) -> Optional[HandlerFunc]:
        """
        Get a handler by name
        
        Args:
            name: Handler name
            flow_type: Optional flow type for scoped lookup
            phase: Optional phase for scoped lookup
            
        Returns:
            Handler function if found, None otherwise
        """
        # Check phase-specific first (most specific)
        if flow_type and phase:
            phase_handlers = self._phase_handlers.get(flow_type, {}).get(phase, {})
            if name in phase_handlers:
                return phase_handlers[name]
        
        # Check flow-type specific
        if flow_type:
            flow_handlers = self._flow_handlers.get(flow_type, {})
            if name in flow_handlers:
                return flow_handlers[name]
        
        # Check global handlers
        return self._global_handlers.get(name)
    
    async def execute_handler(
        self,
        name: str,
        flow_type: Optional[str] = None,
        phase: Optional[str] = None,
        **kwargs
    ) -> HandlerResult:
        """
        Execute a handler by name
        
        Args:
            name: Handler name
            flow_type: Optional flow type for scoped lookup
            phase: Optional phase for scoped lookup
            **kwargs: Arguments to pass to the handler
            
        Returns:
            Handler execution result
        """
        handler = self.get_handler(name, flow_type, phase)
        
        if not handler:
            logger.warning(f"Handler '{name}' not found")
            return HandlerResult(
                success=False,
                error=f"Handler '{name}' not found"
            )
        
        try:
            result = await handler(**kwargs)
            
            if not isinstance(result, HandlerResult):
                # Wrap non-HandlerResult returns
                return HandlerResult(success=True, data={"result": result})
            
            return result
            
        except Exception as e:
            logger.error(f"Handler '{name}' failed: {e}")
            return HandlerResult(
                success=False,
                error=f"Handler execution failed: {str(e)}"
            )
    
    def list_handlers(
        self,
        flow_type: Optional[str] = None,
        phase: Optional[str] = None,
        handler_type: Optional[HandlerType] = None
    ) -> List[Dict[str, Any]]:
        """
        List available handlers
        
        Args:
            flow_type: Optional flow type filter
            phase: Optional phase filter
            handler_type: Optional handler type filter
            
        Returns:
            List of handler information
        """
        handlers = []
        
        # Helper to add handler info
        def add_handler_info(name: str, scope: str):
            info = {
                "name": name,
                "scope": scope,
                **self._handler_metadata.get(name, {})
            }
            
            if handler_type is None or info.get("type") == handler_type:
                handlers.append(info)
        
        # Add global handlers
        for name in self._global_handlers:
            add_handler_info(name, "global")
        
        # Add flow-type handlers if specified
        if flow_type:
            for name in self._flow_handlers.get(flow_type, {}):
                add_handler_info(name, f"flow:{flow_type}")
            
            # Add phase handlers if specified
            if phase:
                for name in self._phase_handlers.get(flow_type, {}).get(phase, {}):
                    add_handler_info(name, f"phase:{flow_type}.{phase}")
        
        return handlers
    
    def _register_builtin_handlers(self):
        """Register built-in handlers"""
        
        # Store raw data handler
        async def store_raw_data(
            flow_id: str,
            flow_type: str,
            configuration: Dict[str, Any],
            initial_state: Dict[str, Any],
            context: RequestContext,
            **kwargs
        ) -> HandlerResult:
            """Store raw imported data"""
            try:
                # In real implementation, store data in database
                # For now, just return success
                return HandlerResult(
                    success=True,
                    data={
                        "stored_records": 0,
                        "storage_location": "postgres"
                    },
                    metadata={"timestamp": "2024-01-01T00:00:00Z"}
                )
            except Exception as e:
                return HandlerResult(
                    success=False,
                    error=f"Failed to store raw data: {str(e)}"
                )
        
        self.register_handler(
            "store_raw_data",
            store_raw_data,
            handler_type=HandlerType.POST_PHASE,
            description="Stores raw imported data to database"
        )
        
        # Apply mappings handler
        async def apply_mappings(
            flow_id: str,
            phase_name: str,
            crew_result: Dict[str, Any],
            context: RequestContext,
            **kwargs
        ) -> HandlerResult:
            """Apply field mappings to data"""
            try:
                # In real implementation, apply mappings
                return HandlerResult(
                    success=True,
                    data={
                        "mapped_fields": 0,
                        "mapping_errors": []
                    }
                )
            except Exception as e:
                return HandlerResult(
                    success=False,
                    error=f"Failed to apply mappings: {str(e)}"
                )
        
        self.register_handler(
            "apply_mappings",
            apply_mappings,
            handler_type=HandlerType.COMPLETION,
            description="Applies field mappings to imported data"
        )
        
        # Fetch application data handler
        async def fetch_application_data(
            flow_id: str,
            phase_name: str,
            phase_input: Dict[str, Any],
            context: RequestContext,
            **kwargs
        ) -> HandlerResult:
            """Fetch application data for assessment"""
            try:
                app_ids = phase_input.get("application_ids", [])
                
                # In real implementation, fetch from database
                return HandlerResult(
                    success=True,
                    data={
                        "applications": [],
                        "total_count": len(app_ids)
                    }
                )
            except Exception as e:
                return HandlerResult(
                    success=False,
                    error=f"Failed to fetch application data: {str(e)}"
                )
        
        self.register_handler(
            "fetch_application_data",
            fetch_application_data,
            handler_type=HandlerType.PRE_PHASE,
            description="Fetches application data for assessment"
        )
        
        # Create asset handler
        async def create_asset_handler(
            asset_type: str,
            asset_data: Dict[str, Any],
            flow_id: str,
            context: RequestContext,
            **kwargs
        ) -> HandlerResult:
            """Create an asset in the database"""
            try:
                # In real implementation, create asset in database
                asset_id = f"{asset_type}_123"
                
                return HandlerResult(
                    success=True,
                    data={
                        "asset_id": asset_id,
                        "asset_type": asset_type,
                        "created": True
                    }
                )
            except Exception as e:
                return HandlerResult(
                    success=False,
                    error=f"Failed to create asset: {str(e)}"
                )
        
        self.register_handler(
            "create_asset",
            create_asset_handler,
            handler_type=HandlerType.ASSET_CREATION,
            description="Creates assets in the database"
        )
        
        # Error notification handler
        async def error_notification_handler(
            error: Exception,
            flow_id: str,
            phase: str,
            context: RequestContext,
            **kwargs
        ) -> HandlerResult:
            """Send error notifications"""
            try:
                # In real implementation, send notifications
                logger.error(f"Flow {flow_id} error in phase {phase}: {error}")
                
                return HandlerResult(
                    success=True,
                    data={
                        "notification_sent": True,
                        "channels": ["log", "email"]
                    }
                )
            except Exception as e:
                return HandlerResult(
                    success=False,
                    error=f"Failed to send error notification: {str(e)}"
                )
        
        self.register_handler(
            "error_notification",
            error_notification_handler,
            handler_type=HandlerType.ERROR,
            description="Sends error notifications"
        )
        
        # Checkpoint creation handler
        async def create_checkpoint_handler(
            flow_id: str,
            phase: str,
            state: Dict[str, Any],
            context: RequestContext,
            **kwargs
        ) -> HandlerResult:
            """Create a flow checkpoint"""
            try:
                # In real implementation, save checkpoint
                checkpoint_id = f"checkpoint_{flow_id}_{phase}"
                
                return HandlerResult(
                    success=True,
                    data={
                        "checkpoint_id": checkpoint_id,
                        "phase": phase,
                        "timestamp": "2024-01-01T00:00:00Z"
                    }
                )
            except Exception as e:
                return HandlerResult(
                    success=False,
                    error=f"Failed to create checkpoint: {str(e)}"
                )
        
        self.register_handler(
            "create_checkpoint",
            create_checkpoint_handler,
            handler_type=HandlerType.COMPLETION,
            description="Creates flow state checkpoints"
        )
        
        logger.info("✅ Registered 6 built-in handlers")


# Global handler registry instance
handler_registry = HandlerRegistry()