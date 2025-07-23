"""
Unified Assessment Flow - CrewAI Implementation

This module implements the main AssessmentFlow using CrewAI Flow patterns,
following the same architecture as UnifiedDiscoveryFlow with PostgreSQL-only persistence.

The Assessment Flow evaluates applications selected from Discovery inventory and:
1. Captures architecture requirements at engagement level
2. Analyzes technical debt for each application component
3. Determines component-level 6R strategies
4. Generates comprehensive "App on a page" assessments
5. Provides input for Planning Flow wave grouping

Flow Phases:
- INITIALIZATION: Load selected applications and initialize flow state
- ARCHITECTURE_MINIMUMS: Capture/verify engagement architecture standards
- TECH_DEBT_ANALYSIS: Analyze components and technical debt
- COMPONENT_SIXR_STRATEGIES: Determine 6R strategy for each component
- APP_ON_PAGE_GENERATION: Generate comprehensive application assessments
- FINALIZATION: Mark applications ready for planning

Each phase includes pause points for user input and collaboration.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# CrewAI Flow imports with graceful fallback
CREWAI_FLOW_AVAILABLE = False
try:
    from crewai import Flow
    from crewai.flow.flow import listen, start

    CREWAI_FLOW_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ CrewAI Flow imports successful for AssessmentFlow")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"CrewAI Flow not available for AssessmentFlow: {e}")

    # Fallback implementations
    class Flow:
        def __init__(self):
            self.state = None

        def __class_getitem__(cls, item):
            return cls

        def kickoff(self):
            return {}

    def listen(condition):
        def decorator(func):
            return func

        return decorator

    def start():
        def decorator(func):
            return func

        return decorator


# Import models and dependencies
from app.core.context import RequestContext
from app.models.assessment_flow import (AssessmentFlowError,
                                        AssessmentFlowState, AssessmentPhase,
                                        AssessmentStatus, SixRDecision)
from app.services.crewai_flows.flow_state_manager import FlowStateManager
from app.services.crewai_flows.persistence.postgres_store import \
    PostgresFlowStateStore


class FlowContext:
    """Flow context container for Assessment Flow execution."""

    def __init__(
        self,
        flow_id: str,
        client_account_id: str,
        engagement_id: str,
        user_id: Optional[str] = None,
        db_session=None,
    ):
        self.flow_id = flow_id
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.user_id = user_id
        self.db_session = db_session


class UnifiedAssessmentFlow(Flow[AssessmentFlowState]):
    """
    Unified Assessment Flow with PostgreSQL-only persistence.

    This CrewAI Flow orchestrates the assessment of applications from Discovery inventory,
    determining component-level 6R strategies and preparing input for Planning Flow.

    Follows the same patterns as UnifiedDiscoveryFlow:
    - PostgreSQL-only state management
    - Multi-tenant context preservation
    - Pause/resume functionality at each phase
    - True CrewAI agents for intelligence
    - Error handling and recovery
    """

    def __init__(
        self,
        crewai_service,
        context: RequestContext,
        selected_application_ids: List[str],
        **kwargs,
    ):
        """Initialize unified assessment flow with agent-first architecture"""

        # Initialize flow_id early to avoid attribute errors
        self._flow_id = kwargs.get("flow_id") or f"assess_{str(uuid.uuid4())[:8]}"

        # Initialize base flow
        if CREWAI_FLOW_AVAILABLE:
            super().__init__()
        else:
            self.state = None

        logger.info(
            "🚀 Initializing Unified Assessment Flow with Agent-First Architecture"
        )

        # Store context and service
        self.crewai_service = crewai_service
        self.context = context
        self.selected_application_ids = selected_application_ids

        # Create flow context for crews
        self.flow_context = FlowContext(
            flow_id=self._flow_id,
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
            user_id=str(context.user_id) if context.user_id else None,
            db_session=getattr(context, "db_session", None),
        )

        # Initialize state management components
        self._initialize_components()

        logger.info(
            f"✅ Unified Assessment Flow initialized - Flow ID: {self._flow_id}"
        )

    @property
    def flow_id(self):
        """Get the flow ID"""
        return self._flow_id

    def _initialize_components(self):
        """Initialize flow components"""

        # Initialize state manager
        self.state_manager = FlowStateManager(self._flow_id)

        # Initialize PostgreSQL store
        self.postgres_store = PostgresFlowStateStore(
            None, self.context
        )  # We'll pass db session later

        # Import crews (will be implemented in separate task)
        try:
            from app.services.crewai_flows.crews.architecture_standards_crew import \
                ArchitectureStandardsCrew
            from app.services.crewai_flows.crews.component_analysis_crew import \
                ComponentAnalysisCrew
            from app.services.crewai_flows.crews.sixr_strategy_crew import \
                SixRStrategyCrew

            # Initialize crews
            self.architecture_standards_crew = ArchitectureStandardsCrew(
                self.flow_context
            )
            self.component_analysis_crew = ComponentAnalysisCrew(self.flow_context)
            self.sixr_strategy_crew = SixRStrategyCrew(self.flow_context)

            logger.info("✅ Assessment crews initialized successfully")

        except ImportError as e:
            logger.warning(f"Assessment crews not yet available: {e}")
            # Create placeholder crews for now
            self.architecture_standards_crew = None
            self.component_analysis_crew = None
            self.sixr_strategy_crew = None

    # ========================================
    # CREWAI FLOW METHODS (@start and @listen)
    # ========================================

    @start()
    async def initialize_assessment(self):
        """Initialize the assessment flow with selected applications"""
        logger.info(
            f"🎯 Starting Assessment Flow for {len(self.selected_application_ids)} applications"
        )

        try:
            # Create initial flow state
            initial_state = AssessmentFlowState(
                flow_id=self._flow_id,
                client_account_id=str(self.context.client_account_id),
                engagement_id=str(self.context.engagement_id),
                user_id=str(self.context.user_id) if self.context.user_id else None,
                current_phase=AssessmentPhase.INITIALIZATION,
                next_phase=AssessmentPhase.ARCHITECTURE_MINIMUMS,
                status=AssessmentStatus.INITIALIZING,
                progress=10.0,
                selected_application_ids=self.selected_application_ids,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            # Set state for CrewAI Flow management
            if CREWAI_FLOW_AVAILABLE and hasattr(super(), "state"):
                # Copy attributes from initial state to managed state
                for key, value in initial_state.__dict__.items():
                    setattr(self.state, key, value)
            else:
                self.state = initial_state

            # Persist initial state would go here
            # await self.postgres_store.save_flow_state(self.state)

            # Load applications from Discovery inventory
            applications_data = await self._load_selected_applications()

            # Update state with loaded data
            self.state.phase_results["initialization"] = {
                "loaded_applications": len(applications_data),
                "application_data": applications_data,
                "initialization_timestamp": datetime.utcnow().isoformat(),
            }

            # Update status and progress
            self.state.status = AssessmentStatus.PROCESSING
            self.state.progress = 15.0
            self.state.updated_at = datetime.utcnow()

            # await self.postgres_store.save_flow_state(self.state)  # Handled by master orchestrator

            logger.info(
                f"✅ Assessment flow initialized with {len(applications_data)} applications"
            )
            return "initialization_completed"

        except Exception as e:
            logger.error(f"❌ Assessment flow initialization failed: {e}")
            if hasattr(self, "state") and self.state:
                self.state.add_error("initialization", str(e))
                # await self.postgres_store.save_flow_state(self.state)  # Handled by master orchestrator
            raise AssessmentFlowError(f"Initialization failed: {str(e)}")

    @listen(initialize_assessment)
    async def capture_architecture_minimums(self, previous_result):
        """Capture and verify architecture requirements at multiple levels"""
        logger.info("🏗️ Starting architecture minimums capture phase")

        try:
            # Update phase status
            self.state.current_phase = AssessmentPhase.ARCHITECTURE_MINIMUMS
            self.state.progress = 20.0

            # Load existing engagement-level standards (if they exist)
            engagement_standards = await self._load_engagement_standards()

            # Initialize with default standards if none exist
            if not engagement_standards:
                logger.info(
                    "No existing engagement standards found, initializing defaults"
                )
                engagement_standards = await self._initialize_default_standards()

            # Use Architecture Standards Crew if available
            if self.architecture_standards_crew:
                logger.info("Executing Architecture Standards Crew")
                crew_result = await self.architecture_standards_crew.execute(
                    {
                        "engagement_context": {
                            "client_account_id": self.state.client_account_id,
                            "engagement_id": self.state.engagement_id,
                        },
                        "selected_applications": self.state.selected_application_ids,
                        "existing_standards": engagement_standards,
                        "flow_context": self.flow_context,
                    }
                )

                # Update standards with crew results
                engagement_standards = crew_result.get(
                    "engagement_standards", engagement_standards
                )

                # Store crew insights
                self.state.phase_results["architecture_minimums"] = {
                    "standards_count": len(engagement_standards),
                    "crew_confidence": crew_result.get("crew_confidence", 0.8),
                    "recommendations": crew_result.get("recommendations", []),
                    "application_compliance": crew_result.get(
                        "application_compliance", {}
                    ),
                    "exceptions": crew_result.get("exceptions", []),
                }
            else:
                logger.warning(
                    "Architecture Standards Crew not available, using defaults"
                )
                self.state.phase_results["architecture_minimums"] = {
                    "standards_count": len(engagement_standards),
                    "crew_confidence": 0.6,  # Lower confidence without crew analysis
                    "recommendations": [],
                    "note": "Generated using default standards (crew not available)",
                }

            # Update flow state with architecture standards
            self.state.engagement_architecture_standards = engagement_standards

            # Add pause point for user input/review
            self.state.pause_points.append("architecture_minimums")
            self.state.status = AssessmentStatus.PAUSED_FOR_USER_INPUT
            self.state.progress = 25.0
            self.state.last_user_interaction = datetime.utcnow()

            # Persist state
            # await self.postgres_store.save_flow_state(self.state)  # Handled by master orchestrator

            logger.info(
                "✅ Architecture minimums phase completed - paused for user input"
            )
            return "architecture_minimums_captured"

        except Exception as e:
            logger.error(f"❌ Architecture minimums capture failed: {e}")
            self.state.add_error("architecture_minimums", str(e))
            # await self.postgres_store.save_flow_state(self.state)  # Handled by master orchestrator
            raise AssessmentFlowError(f"Architecture capture failed: {str(e)}")

    @listen(capture_architecture_minimums)
    async def analyze_technical_debt(self, previous_result):
        """Analyze tech debt for selected applications and identify components"""
        logger.info("🔍 Starting technical debt analysis phase")

        try:
            # Update phase status
            self.state.current_phase = AssessmentPhase.TECH_DEBT_ANALYSIS
            self.state.progress = 30.0

            # Apply any user input from previous phase
            user_arch_input = self.state.user_inputs.get("architecture_minimums", {})
            if user_arch_input:
                await self._apply_architecture_modifications(user_arch_input)

            # Analyze each selected application
            for app_id in self.state.selected_application_ids:
                logger.info(f"🔍 Analyzing tech debt for application {app_id}")

                # Get application metadata from Discovery results
                app_metadata = await self._get_application_metadata(app_id)

                # Use Component Analysis Crew if available
                if self.component_analysis_crew:
                    crew_result = await self.component_analysis_crew.execute(
                        {
                            "application_id": app_id,
                            "application_metadata": app_metadata,
                            "architecture_standards": self.state.engagement_architecture_standards,
                            "flow_context": self.flow_context,
                        }
                    )

                    # Process crew results
                    components = crew_result.get("components", [])
                    tech_debt_items = crew_result.get("tech_debt_analysis", [])
                    component_scores = crew_result.get("component_scores", {})

                    # Store results in flow state
                    self.state.application_components[app_id] = components
                    self.state.tech_debt_analysis[app_id] = tech_debt_items
                    self.state.component_tech_debt[app_id] = component_scores

                    logger.info(
                        f"✅ Identified {len(components)} components and {len(tech_debt_items)} tech debt items for {app_id}"
                    )

                else:
                    logger.warning(
                        f"Component Analysis Crew not available, using placeholder analysis for {app_id}"
                    )
                    # Placeholder analysis
                    self.state.application_components[app_id] = [
                        {
                            "name": "main_application",
                            "type": "web_frontend",
                            "tech_debt_score": 5.0,
                        }
                    ]
                    self.state.tech_debt_analysis[app_id] = [
                        {
                            "category": "technology",
                            "severity": "medium",
                            "score": 5.0,
                            "description": "Placeholder tech debt analysis",
                        }
                    ]
                    self.state.component_tech_debt[app_id] = {"main_application": 5.0}

            # Update progress and add pause point
            self.state.progress = 50.0
            self.state.pause_points.append("tech_debt_analysis")
            self.state.status = AssessmentStatus.PAUSED_FOR_USER_INPUT
            self.state.last_user_interaction = datetime.utcnow()

            # Store phase results
            total_components = sum(
                len(components)
                for components in self.state.application_components.values()
            )
            total_debt_items = sum(
                len(items) for items in self.state.tech_debt_analysis.values()
            )

            self.state.phase_results["tech_debt_analysis"] = {
                "total_components_identified": total_components,
                "total_tech_debt_items": total_debt_items,
                "applications_analyzed": len(self.state.selected_application_ids),
                "analysis_timestamp": datetime.utcnow().isoformat(),
            }

            # Persist updated state
            # await self.postgres_store.save_flow_state(self.state)  # Handled by master orchestrator

            logger.info("✅ Technical debt analysis completed - paused for user input")
            return "tech_debt_analysis_completed"

        except Exception as e:
            logger.error(f"❌ Technical debt analysis failed: {e}")
            self.state.add_error("tech_debt_analysis", str(e))
            # await self.postgres_store.save_flow_state(self.state)  # Handled by master orchestrator
            raise AssessmentFlowError(f"Tech debt analysis failed: {str(e)}")

    @listen(analyze_technical_debt)
    async def determine_component_sixr_strategies(self, previous_result):
        """Determine 6R treatment for each application component"""
        logger.info("📋 Starting component 6R strategy determination")

        try:
            # Update phase status
            self.state.current_phase = AssessmentPhase.COMPONENT_SIXR_STRATEGIES
            self.state.progress = 60.0

            # Apply any user input from tech debt phase
            user_tech_debt_input = self.state.user_inputs.get("tech_debt_analysis", {})
            if user_tech_debt_input:
                await self._apply_tech_debt_modifications(user_tech_debt_input)

            # Determine 6R strategies for each application
            for app_id in self.state.selected_application_ids:
                logger.info(f"📋 Determining 6R strategies for application {app_id}")

                app_components = self.state.application_components.get(app_id, [])
                tech_debt_analysis = self.state.tech_debt_analysis.get(app_id, [])
                arch_standards = self.state.engagement_architecture_standards

                # Use Six R Strategy Crew if available
                if self.sixr_strategy_crew:
                    crew_result = await self.sixr_strategy_crew.execute(
                        {
                            "application_id": app_id,
                            "components": app_components,
                            "tech_debt_analysis": tech_debt_analysis,
                            "architecture_standards": arch_standards,
                            "flow_context": self.flow_context,
                        }
                    )

                    # Process crew results
                    component_treatments = crew_result.get("component_treatments", [])
                    overall_strategy = crew_result.get("overall_strategy")
                    confidence_score = crew_result.get("confidence_score", 0.0)
                    rationale = crew_result.get("rationale", "")
                    move_group_hints = crew_result.get("move_group_hints", [])

                else:
                    logger.warning(
                        f"Six R Strategy Crew not available, using placeholder strategy for {app_id}"
                    )
                    # Placeholder strategy determination
                    component_treatments = [
                        {
                            "component_name": comp.get("name", "unknown"),
                            "strategy": "replatform",  # Default strategy
                            "confidence": 0.6,
                            "rationale": "Placeholder strategy (crew not available)",
                        }
                        for comp in app_components
                    ]
                    overall_strategy = "replatform"
                    confidence_score = 0.6
                    rationale = (
                        "Default replatform strategy applied due to crew unavailability"
                    )
                    move_group_hints = []

                # Create SixR decision
                app_name = await self._get_application_name(app_id)
                sixr_decision = SixRDecision(
                    application_id=app_id,
                    application_name=app_name,
                    component_treatments=component_treatments,
                    overall_strategy=overall_strategy,
                    confidence_score=confidence_score,
                    rationale=rationale,
                    move_group_hints=move_group_hints,
                    tech_debt_score=self._calculate_overall_tech_debt_score(app_id),
                    architecture_exceptions=self._get_architecture_exceptions(app_id),
                )

                # Validate component compatibility
                compatibility_issues = self.state.validate_component_compatibility(
                    app_id
                )
                if compatibility_issues:
                    sixr_decision.risk_factors.extend(compatibility_issues)

                # Store decision in flow state
                self.state.sixr_decisions[app_id] = sixr_decision

                logger.info(
                    f"✅ 6R strategy determined for {app_id}: {overall_strategy} (confidence: {confidence_score:.2f})"
                )

            # Update progress and add pause point
            self.state.progress = 75.0
            self.state.pause_points.append("component_sixr_strategies")
            self.state.status = AssessmentStatus.PAUSED_FOR_USER_INPUT
            self.state.last_user_interaction = datetime.utcnow()

            # Store phase results
            self.state.phase_results["component_sixr_strategies"] = {
                "applications_assessed": len(self.state.sixr_decisions),
                "overall_confidence": sum(
                    decision.confidence_score
                    for decision in self.state.sixr_decisions.values()
                )
                / len(self.state.sixr_decisions),
                "strategy_distribution": self._get_strategy_distribution(),
                "assessment_timestamp": datetime.utcnow().isoformat(),
            }

            # Persist updated state
            # await self.postgres_store.save_flow_state(self.state)  # Handled by master orchestrator

            logger.info("✅ Component 6R strategies determined - paused for user input")
            return "sixr_strategies_determined"

        except Exception as e:
            logger.error(f"❌ 6R strategy determination failed: {e}")
            self.state.add_error("component_sixr_strategies", str(e))
            # await self.postgres_store.save_flow_state(self.state)  # Handled by master orchestrator
            raise AssessmentFlowError(f"6R strategy determination failed: {str(e)}")

    @listen(determine_component_sixr_strategies)
    async def generate_app_on_page(self, previous_result):
        """Generate comprehensive "App on a page" view"""
        logger.info("📄 Starting app on a page generation")

        try:
            # Update phase status
            self.state.current_phase = AssessmentPhase.APP_ON_PAGE_GENERATION
            self.state.progress = 80.0

            # Apply any user input from 6R strategies phase
            user_sixr_input = self.state.user_inputs.get(
                "component_sixr_strategies", {}
            )
            if user_sixr_input:
                await self._apply_sixr_modifications(user_sixr_input)

            # Generate app on a page for each application
            for app_id in self.state.selected_application_ids:
                logger.info(f"📄 Generating app on a page for application {app_id}")

                decision = self.state.sixr_decisions[app_id]

                # Consolidate all application data
                app_on_page_data = await self._generate_app_on_page_data(
                    app_id, decision
                )

                # Update decision with app on a page data
                decision.app_on_page_data = app_on_page_data

                logger.info(f"✅ App on a page generated for {app_id}")

            # Update progress and add pause point
            self.state.progress = 90.0
            self.state.pause_points.append("app_on_page_generation")
            self.state.status = AssessmentStatus.PAUSED_FOR_USER_INPUT
            self.state.last_user_interaction = datetime.utcnow()

            # Store phase results
            self.state.phase_results["app_on_page_generation"] = {
                "apps_with_pages": len(
                    [
                        d
                        for d in self.state.sixr_decisions.values()
                        if d.app_on_page_data
                    ]
                ),
                "generation_timestamp": datetime.utcnow().isoformat(),
            }

            # Persist updated state
            # await self.postgres_store.save_flow_state(self.state)  # Handled by master orchestrator

            logger.info("✅ App on a page generation completed - paused for user input")
            return "app_on_page_generated"

        except Exception as e:
            logger.error(f"❌ App on a page generation failed: {e}")
            self.state.add_error("app_on_page_generation", str(e))
            # await self.postgres_store.save_flow_state(self.state)  # Handled by master orchestrator
            raise AssessmentFlowError(f"App on a page generation failed: {str(e)}")

    @listen(generate_app_on_page)
    async def finalize_assessment(self, previous_result):
        """Finalize and prepare applications for Planning Flow"""
        logger.info("🎯 Starting assessment finalization")

        try:
            # Update phase status
            self.state.current_phase = AssessmentPhase.FINALIZATION
            self.state.progress = 95.0

            # Apply any user input from app on a page phase
            user_final_input = self.state.user_inputs.get("app_on_page_generation", {})
            if user_final_input:
                await self._apply_final_modifications(user_final_input)

            # Determine which apps are ready for planning
            apps_ready = []
            for app_id, decision in self.state.sixr_decisions.items():
                # Apps are ready if they have confident decisions and no critical issues
                if decision.confidence_score >= 0.7 and not any(
                    "critical" in str(risk).lower() for risk in decision.risk_factors
                ):
                    apps_ready.append(app_id)

            self.state.apps_ready_for_planning = apps_ready

            # Update flow to completed status
            self.state.status = AssessmentStatus.COMPLETED
            self.state.progress = 100.0
            self.state.completed_at = datetime.utcnow()
            self.state.updated_at = datetime.utcnow()

            # Generate assessment summary
            summary = await self._generate_assessment_summary()
            self.state.phase_results["final_summary"] = summary

            # Persist final state
            # await self.postgres_store.save_flow_state(self.state)  # Handled by master orchestrator

            logger.info(
                f"✅ Assessment finalized - {len(apps_ready)} apps ready for planning"
            )
            return "assessment_completed"

        except Exception as e:
            logger.error(f"❌ Assessment finalization failed: {e}")
            self.state.add_error("finalization", str(e))
            # await self.postgres_store.save_flow_state(self.state)  # Handled by master orchestrator
            raise AssessmentFlowError(f"Assessment finalization failed: {str(e)}")

    # ========================================
    # RESUME FUNCTIONALITY
    # ========================================

    async def resume_from_phase(
        self, phase: AssessmentPhase, user_input: Dict[str, Any]
    ) -> AssessmentFlowState:
        """Resume flow from specific phase with user input"""

        try:
            logger.info(f"🔄 Resuming assessment flow from phase: {phase}")

            # Load current flow state - handled by master orchestrator
            # current_state = await self.postgres_store.load_flow_state()
            current_state = self.state  # Use existing state
            if not current_state:
                raise AssessmentFlowError("No flow state found for resume")

            # Update current state reference
            self.state = current_state

            # Save user input for the phase
            self.state.user_inputs[phase.value] = user_input

            # Update current phase and status
            self.state.current_phase = phase
            self.state.status = AssessmentStatus.PROCESSING
            self.state.last_user_interaction = datetime.utcnow()
            self.state.updated_at = datetime.utcnow()

            # Persist the updated state
            # await self.postgres_store.save_flow_state(self.state)  # Handled by master orchestrator

            # Resume from the appropriate phase
            if phase == AssessmentPhase.ARCHITECTURE_MINIMUMS:
                return await self.analyze_technical_debt(
                    "resumed_from_architecture_minimums"
                )
            elif phase == AssessmentPhase.TECH_DEBT_ANALYSIS:
                return await self.determine_component_sixr_strategies(
                    "resumed_from_tech_debt_analysis"
                )
            elif phase == AssessmentPhase.COMPONENT_SIXR_STRATEGIES:
                return await self.generate_app_on_page(
                    "resumed_from_component_sixr_strategies"
                )
            elif phase == AssessmentPhase.APP_ON_PAGE_GENERATION:
                return await self.finalize_assessment(
                    "resumed_from_app_on_page_generation"
                )
            else:
                raise AssessmentFlowError(f"Cannot resume from phase: {phase}")

        except Exception as e:
            logger.error(f"❌ Failed to resume from phase {phase}: {str(e)}")
            raise AssessmentFlowError(f"Resume failed: {str(e)}")

    # ========================================
    # HELPER METHODS
    # ========================================

    async def _load_selected_applications(self) -> List[Dict[str, Any]]:
        """Load applications marked ready for assessment from Discovery inventory"""
        # Placeholder implementation - would load from Discovery Flow results
        applications = []
        for app_id in self.selected_application_ids:
            applications.append(
                {
                    "id": app_id,
                    "name": f"Application {app_id}",
                    "discovery_data": {"placeholder": True},
                }
            )
        return applications

    async def _load_engagement_standards(self) -> List[Dict[str, Any]]:
        """Load existing engagement architecture standards"""
        # Placeholder implementation - would load from database
        return []

    async def _initialize_default_standards(self) -> List[Dict[str, Any]]:
        """Initialize default architecture standards for engagement"""
        # Placeholder implementation - would create default standards
        return [
            {
                "type": "technology_version",
                "name": "Java Version Standard",
                "description": "Minimum Java version requirement",
                "technology_specifications": {
                    "minimum_version": "11",
                    "recommended_version": "17",
                },
            }
        ]

    async def _get_application_metadata(self, app_id: str) -> Dict[str, Any]:
        """Get application metadata from Discovery flow results"""
        # Placeholder implementation
        return {"app_id": app_id, "metadata": {"placeholder": True}}

    async def _get_application_name(self, app_id: str) -> str:
        """Get application name from inventory"""
        return f"Application {app_id}"

    def _calculate_overall_tech_debt_score(self, app_id: str) -> float:
        """Calculate overall technical debt score for application"""
        scores = self.state.component_tech_debt.get(app_id, {})
        if not scores:
            return 0.0
        return sum(scores.values()) / len(scores)

    def _get_architecture_exceptions(self, app_id: str) -> List[Dict[str, Any]]:
        """Get architecture exceptions for application"""
        return []  # Placeholder

    def _get_strategy_distribution(self) -> Dict[str, int]:
        """Get distribution of 6R strategies across applications"""
        distribution = {}
        for decision in self.state.sixr_decisions.values():
            strategy = decision.overall_strategy
            if strategy:
                distribution[strategy] = distribution.get(strategy, 0) + 1
        return distribution

    async def _generate_app_on_page_data(
        self, app_id: str, decision: SixRDecision
    ) -> Dict[str, Any]:
        """Generate comprehensive app on a page data"""
        return {
            "application_summary": {
                "id": app_id,
                "name": decision.application_name,
                "overall_strategy": decision.overall_strategy,
                "confidence": decision.confidence_score,
            },
            "components": decision.component_treatments,
            "tech_debt_summary": {
                "overall_score": decision.tech_debt_score,
                "key_issues": [],
            },
            "migration_readiness": {
                "ready": decision.confidence_score >= 0.7,
                "blockers": [
                    risk
                    for risk in decision.risk_factors
                    if "critical" in str(risk).lower()
                ],
            },
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def _generate_assessment_summary(self) -> Dict[str, Any]:
        """Generate assessment summary"""
        return {
            "total_applications": len(self.state.selected_application_ids),
            "apps_ready_for_planning": len(self.state.apps_ready_for_planning),
            "strategy_distribution": self._get_strategy_distribution(),
            "overall_confidence": (
                sum(d.confidence_score for d in self.state.sixr_decisions.values())
                / len(self.state.sixr_decisions)
                if self.state.sixr_decisions
                else 0.0
            ),
            "completion_time": datetime.utcnow().isoformat(),
        }

    # Placeholder modification methods (would contain actual business logic)
    async def _apply_architecture_modifications(self, user_input: Dict[str, Any]):
        """Apply user modifications to architecture standards"""
        logger.info("Applying user architecture modifications")

    async def _apply_tech_debt_modifications(self, user_input: Dict[str, Any]):
        """Apply user modifications to tech debt analysis"""
        logger.info("Applying user tech debt modifications")

    async def _apply_sixr_modifications(self, user_input: Dict[str, Any]):
        """Apply user modifications to 6R decisions"""
        logger.info("Applying user 6R strategy modifications")

    async def _apply_final_modifications(self, user_input: Dict[str, Any]):
        """Apply final user modifications"""
        logger.info("Applying final user modifications")


# Factory function for creating assessment flows
def create_unified_assessment_flow(
    crewai_service,
    context: RequestContext,
    selected_application_ids: List[str],
    **kwargs,
) -> UnifiedAssessmentFlow:
    """
    Factory function to create a Unified Assessment Flow instance.

    Args:
        crewai_service: The CrewAI service instance
        context: Request context for multi-tenant operations
        selected_application_ids: List of application IDs from Discovery inventory
        **kwargs: Additional flow configuration

    Returns:
        UnifiedAssessmentFlow instance
    """
    return UnifiedAssessmentFlow(
        crewai_service=crewai_service,
        context=context,
        selected_application_ids=selected_application_ids,
        **kwargs,
    )
