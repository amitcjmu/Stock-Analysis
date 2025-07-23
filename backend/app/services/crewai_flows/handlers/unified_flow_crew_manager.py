"""
Unified Flow Crew Manager
Handles CrewAI crew creation and management for the Unified Discovery Flow.
Extracted from unified_discovery_flow.py for better modularity.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# CrewAI Flow imports with graceful fallback
CREWAI_FLOW_AVAILABLE = False
try:
    from crewai import Flow
    from crewai.flow.flow import listen, start
    from crewai.flow.persistence import persist

    CREWAI_FLOW_AVAILABLE = True
except ImportError as e:
    logger.warning(f"CrewAI Flow not available: {e}")


class UnifiedFlowCrewManager:
    """
    Manages CrewAI crew creation and execution for the Unified Discovery Flow.
    Handles on-demand crew creation with proper error handling and fallbacks.
    Enhanced with callback handlers for task monitoring.
    """

    def __init__(self, crewai_service, state, callback_handler=None, context=None):
        """Initialize crew manager with service and state references"""
        self.crewai_service = crewai_service
        self.state = state
        self.crew_factories = {}
        self.callback_handler = callback_handler
        self.context = context

        # Initialize callback handler if not provided
        if not self.callback_handler and hasattr(state, "flow_id"):
            from .callback_handler_integration import \
                CallbackHandlerIntegration

            # Extract metadata from state if available
            metadata = getattr(state, "metadata", {})

            self.callback_handler = CallbackHandlerIntegration.create_callback_handler(
                flow_id=getattr(state, "flow_id", "unknown"),
                context=self.context,
                metadata=metadata,
            )
            logger.info("✅ Auto-created callback handler for monitoring")

        # Initialize crew factories for on-demand creation
        self._initialize_crew_factories()

    def _initialize_crew_factories(self):
        """Initialize CrewAI crew factory functions for on-demand creation"""
        try:
            # Import state model for proper type checking
            from app.models.unified_discovery_flow_state import \
                UnifiedDiscoveryFlowState
            # 🚀 PERFORMANCE OPTIMIZATION: Always use optimized crews
            from app.services.crewai_flows.crews.field_mapping_crew_fast import \
                create_fast_field_mapping_crew

            field_mapping_factory = create_fast_field_mapping_crew
            logger.info("✅ Using OPTIMIZED field mapping crew for performance")
            from app.services.crewai_flows.crews.data_cleansing_crew import \
                create_data_cleansing_crew
            from app.services.crewai_flows.crews.data_import_validation_crew import \
                create_data_import_validation_crew
            from app.services.crewai_flows.crews.dependency_analysis_crew import \
                create_dependency_analysis_crew
            from app.services.crewai_flows.crews.inventory_building_crew import \
                create_inventory_building_crew
            from app.services.crewai_flows.crews.technical_debt_crew import \
                create_technical_debt_crew

            # Store factory functions
            self.crew_factories = {
                "data_import_validation": create_data_import_validation_crew,  # NEW: Focused data validation crew
                "data_import": create_data_import_validation_crew,  # Alias for phase executor compatibility
                "attribute_mapping": field_mapping_factory,  # Dynamic based on CREWAI_FAST_MODE setting
                "data_cleansing": create_data_cleansing_crew,
                "inventory": create_inventory_building_crew,  # Fixed: Use inventory to match DB schema
                "dependencies": create_dependency_analysis_crew,  # Fixed: Use dependencies to match DB schema
                "tech_debt": create_technical_debt_crew,  # Fixed: Use tech_debt to match DB schema
            }

            logger.info("✅ CrewAI crew factories initialized successfully")

        except ImportError as e:
            logger.error(f"❌ Failed to import CrewAI crew factories: {e}")
            self.crew_factories = {}
        except Exception as e:
            logger.error(f"❌ Failed to initialize CrewAI crew factories: {e}")
            self.crew_factories = {}

    def create_crew_on_demand(self, crew_type: str, **kwargs) -> Optional[Any]:
        """Create a crew on-demand with proper error handling"""
        try:
            if crew_type not in self.crew_factories:
                raise Exception(f"Crew factory not available for: {crew_type}")

            factory = self.crew_factories[crew_type]

            # Create crew with appropriate parameters
            if crew_type in ["data_import_validation", "data_import"]:
                crew = factory(
                    self.crewai_service,
                    kwargs.get("raw_data", []),
                    kwargs.get("metadata", {}),
                    kwargs.get("shared_memory"),
                    callback_handler=self.callback_handler,
                )
            elif crew_type == "attribute_mapping":
                # 🚀 OPTIMIZED: Use state-based crew creation
                crew = factory(self.crewai_service, self.state)
            elif crew_type == "data_cleansing":
                # 🚀 OPTIMIZED: Use state-based crew creation
                crew = factory(self.crewai_service, self.state)
            elif crew_type == "inventory":
                # Build context info from state for intelligent task management
                context_info = {
                    "client_account_id": getattr(self.state, "client_account_id", None),
                    "engagement_id": getattr(self.state, "engagement_id", None),
                    "flow_id": getattr(self.state, "flow_id", None),
                    "user_id": getattr(self.state, "user_id", None),
                }
                crew = factory(
                    self.crewai_service,
                    kwargs.get("cleaned_data", []),
                    kwargs.get("field_mappings", {}),
                    kwargs.get("shared_memory"),
                    kwargs.get("knowledge_base"),
                    context_info,
                )
            elif crew_type == "dependencies":
                crew = factory(
                    self.crewai_service,
                    kwargs.get("asset_inventory", []),
                    kwargs.get("shared_memory"),
                    kwargs.get("knowledge_base"),
                )
            elif crew_type == "tech_debt":
                crew = factory(
                    self.crewai_service,
                    kwargs.get("asset_inventory", []),
                    kwargs.get("dependencies", {}),
                    kwargs.get("shared_memory"),
                    kwargs.get("knowledge_base"),
                )
            else:
                raise Exception(f"Unknown crew type: {crew_type}")

            logger.info(f"✅ {crew_type} crew created successfully")
            return crew

        except Exception as e:
            logger.error(f"❌ Failed to create {crew_type} crew: {e}")
            self.state.add_error(f"{crew_type}_crew_creation", str(e))
            return None

    def is_crew_available(self, crew_type: str) -> bool:
        """Check if a crew type is available"""
        return crew_type in self.crew_factories and CREWAI_FLOW_AVAILABLE

    def get_available_crews(self) -> list:
        """Get list of available crew types"""
        return list(self.crew_factories.keys()) if CREWAI_FLOW_AVAILABLE else []
