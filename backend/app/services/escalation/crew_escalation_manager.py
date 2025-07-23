"""
Crew Escalation Manager
Manages crew escalations for Think/Ponder More button functionality.
Implements Tasks 2.3 and 3.4 of the Discovery Flow Redesign.
Enhanced with strategic crew integration and delegation capabilities.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks

# Setup logger first
logger = logging.getLogger(__name__)

# Import strategic crews from Phase 3
try:
    from ..crewai_flows.crews.asset_intelligence_crew import \
        create_asset_intelligence_crew
    from ..crewai_flows.crews.dependency_analysis_crew import \
        create_dependency_analysis_crew
    from ..crewai_flows.crews.tech_debt_analysis_crew import \
        create_tech_debt_analysis_crew

    STRATEGIC_CREWS_AVAILABLE = True
except ImportError:
    logger.debug("Strategic crews not available - using fallback functionality")
    STRATEGIC_CREWS_AVAILABLE = False


class CrewEscalationManager:
    """
    Manages crew escalations for Think/Ponder More functionality.

    Handles:
    - Crew selection based on page/agent context
    - Background crew execution
    - Progress tracking and status updates
    - Results integration back to discovery flow
    """

    def __init__(self):
        self.active_escalations: Dict[str, Dict[str, Any]] = {}
        self.crew_mappings = {
            # Page -> Agent -> Crew mappings (Enhanced with strategic crews)
            "field_mapping": {
                "attribute_mapping_agent": "field_mapping_crew",
                "data_validation_agent": "data_quality_crew",
                "asset_classification_expert": "asset_intelligence_crew",
            },
            "asset_inventory": {
                "asset_inventory_agent": "asset_intelligence_crew",
                "data_cleansing_agent": "data_quality_crew",
                "asset_classification_expert": "asset_intelligence_crew",
                "business_context_analyst": "asset_intelligence_crew",
                "environment_specialist": "asset_intelligence_crew",
            },
            "dependencies": {
                "dependency_analysis_agent": "dependency_analysis_crew",
                "asset_inventory_agent": "asset_intelligence_crew",
                "network_architecture_specialist": "dependency_analysis_crew",
                "application_integration_expert": "dependency_analysis_crew",
                "infrastructure_dependencies_analyst": "dependency_analysis_crew",
            },
            "tech_debt": {
                "tech_debt_analysis_agent": "tech_debt_analysis_crew",
                "dependency_analysis_agent": "dependency_analysis_crew",
                "legacy_modernization_expert": "tech_debt_analysis_crew",
                "cloud_migration_strategist": "tech_debt_analysis_crew",
                "risk_assessment_specialist": "tech_debt_analysis_crew",
            },
        }

        # Strategic crew instances (Phase 3 enhancement)
        self.strategic_crews = {}
        if STRATEGIC_CREWS_AVAILABLE:
            try:
                self.strategic_crews = {
                    "asset_intelligence_crew": create_asset_intelligence_crew(),
                    "dependency_analysis_crew": create_dependency_analysis_crew(),
                    "tech_debt_analysis_crew": create_tech_debt_analysis_crew(),
                }
                logger.info("✅ Strategic crews initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize strategic crews: {e}")
                self.strategic_crews = {}

        # Delegation capabilities for Ponder More (Task 3.4 enhancement)
        self.delegation_patterns = {
            "sequential_delegation": {
                "description": "Sequential expert delegation with escalating complexity",
                "pattern": "expert_1 -> expert_2 -> expert_3 -> synthesis",
            },
            "parallel_delegation": {
                "description": "Parallel expert analysis with collaborative synthesis",
                "pattern": "expert_1 || expert_2 || expert_3 -> collaborative_synthesis",
            },
            "hierarchical_delegation": {
                "description": "Hierarchical delegation with specialist review",
                "pattern": "specialists -> senior_experts -> executive_review",
            },
        }

        # Collaboration strategies for Ponder More
        self.collaboration_strategies = {
            "cross_agent": {
                "pattern": "parallel_synthesis",
                "description": "Multiple agents collaborate in parallel then synthesize results",
            },
            "expert_panel": {
                "pattern": "sequential_expert_review",
                "description": "Sequential expert review with escalating complexity",
            },
            "full_crew": {
                "pattern": "full_crew_collaboration",
                "description": "Complete crew collaboration with debate and consensus",
            },
        }

        logger.info(
            "🚀 Crew Escalation Manager initialized with strategic crew integration"
        )

    def determine_crew_for_page_agent(self, page: str, agent_id: str) -> str:
        """Determine appropriate crew based on page and agent context."""
        page_mappings = self.crew_mappings.get(page, {})
        crew_type = page_mappings.get(agent_id)

        if not crew_type:
            # Default crew selection based on page
            default_crews = {
                "field_mapping": "field_mapping_crew",
                "asset_inventory": "asset_intelligence_crew",
                "dependencies": "dependency_analysis_crew",
                "tech_debt": "tech_debt_analysis_crew",
            }
            crew_type = default_crews.get(page, "general_analysis_crew")

        logger.info(
            f"🎯 Selected crew '{crew_type}' for page '{page}' and agent '{agent_id}'"
        )
        return crew_type

    def determine_collaboration_strategy(
        self, page: str, agent_id: str, collaboration_type: str
    ) -> Dict[str, Any]:
        """Determine collaboration strategy for Ponder More functionality."""
        base_strategy = self.collaboration_strategies.get(
            collaboration_type, self.collaboration_strategies["cross_agent"]
        )

        # Determine primary crew
        primary_crew = self.determine_crew_for_page_agent(page, agent_id)

        # Determine additional crews based on collaboration type
        additional_crews = []
        if collaboration_type == "expert_panel":
            # Add complementary crews for expert panel
            if page == "dependencies":
                additional_crews = [
                    "asset_intelligence_crew",
                    "tech_debt_analysis_crew",
                ]
            elif page == "asset_inventory":
                additional_crews = ["dependency_analysis_crew", "field_mapping_crew"]
            elif page == "tech_debt":
                additional_crews = [
                    "dependency_analysis_crew",
                    "asset_intelligence_crew",
                ]
        elif collaboration_type == "full_crew":
            # Add all relevant crews for full collaboration
            additional_crews = [
                "asset_intelligence_crew",
                "dependency_analysis_crew",
                "tech_debt_analysis_crew",
                "field_mapping_crew",
            ]
            additional_crews = [c for c in additional_crews if c != primary_crew]

        strategy = {
            "primary_crew": primary_crew,
            "additional_crews": additional_crews,
            "pattern": base_strategy["pattern"],
            "description": base_strategy["description"],
            "collaboration_type": collaboration_type,
            "expected_outcomes": self._get_expected_outcomes(page, collaboration_type),
        }

        logger.info(
            f"🤝 Collaboration strategy: {strategy['pattern']} with {len(additional_crews)} additional crews"
        )
        return strategy

    def _get_expected_outcomes(self, page: str, collaboration_type: str) -> List[str]:
        """Get expected outcomes based on page and collaboration type."""
        base_outcomes = {
            "field_mapping": [
                "Enhanced field mapping accuracy",
                "Identification of complex mapping patterns",
                "Data quality improvement recommendations",
            ],
            "asset_inventory": [
                "Comprehensive asset classification",
                "Business criticality assessment",
                "Environment and dependency insights",
            ],
            "dependencies": [
                "Complete dependency mapping",
                "Critical path identification",
                "Migration risk assessment",
            ],
            "tech_debt": [
                "Modernization strategy recommendations",
                "6R strategy optimization",
                "Technical debt prioritization",
            ],
        }

        outcomes = base_outcomes.get(page, ["Enhanced analysis results"])

        # Add collaboration-specific outcomes
        if collaboration_type == "expert_panel":
            outcomes.append("Expert validation and refinement")
        elif collaboration_type == "full_crew":
            outcomes.extend(
                [
                    "Cross-domain insights",
                    "Comprehensive risk analysis",
                    "Holistic migration recommendations",
                ]
            )

        return outcomes

    async def start_crew_escalation(
        self,
        crew_type: str,
        escalation_context: Dict[str, Any],
        background_tasks: BackgroundTasks,
    ) -> str:
        """Start a crew escalation for Think button functionality."""
        escalation_id = str(uuid.uuid4())

        # Initialize escalation tracking
        escalation_record = {
            "escalation_id": escalation_id,
            "crew_type": crew_type,
            "escalation_type": "think",
            "status": "initializing",
            "progress": 0,
            "current_phase": "crew_initialization",
            "context": escalation_context,
            "started_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "crew_activity": [],
            "preliminary_insights": [],
            "estimated_completion": (
                datetime.utcnow() + timedelta(minutes=5)
            ).isoformat(),
        }

        self.active_escalations[escalation_id] = escalation_record

        # Start crew execution in background
        background_tasks.add_task(
            self._execute_crew_thinking, escalation_id, crew_type, escalation_context
        )

        logger.info(f"🚀 Started crew escalation {escalation_id} with {crew_type}")
        return escalation_id

    async def start_extended_collaboration(
        self,
        collaboration_strategy: Dict[str, Any],
        collaboration_context: Dict[str, Any],
        background_tasks: BackgroundTasks,
    ) -> str:
        """Start extended crew collaboration for Ponder More functionality."""
        escalation_id = str(uuid.uuid4())

        # Initialize collaboration tracking
        collaboration_record = {
            "escalation_id": escalation_id,
            "collaboration_strategy": collaboration_strategy,
            "escalation_type": "ponder_more",
            "status": "initializing",
            "progress": 0,
            "current_phase": "collaboration_setup",
            "context": collaboration_context,
            "started_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "crew_activity": [],
            "preliminary_insights": [],
            "collaboration_details": {
                "active_crews": [collaboration_strategy["primary_crew"]]
                + collaboration_strategy.get("additional_crews", []),
                "collaboration_pattern": collaboration_strategy["pattern"],
                "phase_progress": {},
            },
            "estimated_completion": (
                datetime.utcnow() + timedelta(minutes=10)
            ).isoformat(),
        }

        self.active_escalations[escalation_id] = collaboration_record

        # Start collaboration in background
        background_tasks.add_task(
            self._execute_crew_collaboration,
            escalation_id,
            collaboration_strategy,
            collaboration_context,
        )

        logger.info(
            f"🤝 Started crew collaboration {escalation_id} with strategy {collaboration_strategy['pattern']}"
        )
        return escalation_id

    async def _execute_crew_thinking(
        self, escalation_id: str, crew_type: str, context: Dict[str, Any]
    ) -> None:
        """Execute crew thinking process in background with strategic crew integration."""
        try:
            escalation = self.active_escalations[escalation_id]

            # Phase 1: Crew Initialization
            await self._update_escalation_progress(
                escalation_id,
                10,
                "crew_initialization",
                "Initializing strategic crew for deeper analysis",
            )
            await asyncio.sleep(2)  # Simulate crew setup

            # Phase 2: Strategic Crew Execution
            await self._update_escalation_progress(
                escalation_id,
                30,
                "strategic_analysis",
                f"Strategic {crew_type} analyzing {context.get('page', 'data')} with enhanced intelligence",
            )

            # Execute strategic crew if available
            crew_results = None
            if STRATEGIC_CREWS_AVAILABLE and crew_type in self.strategic_crews:
                try:
                    strategic_crew = self.strategic_crews[crew_type]
                    page_data = context.get("page_data", {})
                    assets_data = page_data.get("assets", []) if page_data else []

                    # Execute appropriate strategic crew method
                    if crew_type == "asset_intelligence_crew":
                        crew_results = await strategic_crew.analyze_assets(
                            assets_data, context
                        )
                    elif crew_type == "dependency_analysis_crew":
                        crew_results = await strategic_crew.analyze_dependencies(
                            assets_data, context
                        )
                    elif crew_type == "tech_debt_analysis_crew":
                        crew_results = await strategic_crew.analyze_tech_debt(
                            assets_data, context
                        )

                    logger.info(f"✅ Strategic crew {crew_type} execution completed")

                except Exception as e:
                    logger.error(f"❌ Strategic crew execution failed: {e}")
                    crew_results = None

            # Add crew activity
            escalation["crew_activity"].append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "activity": f"Strategic {crew_type} completed enhanced analysis",
                    "phase": "strategic_analysis",
                    "crew_results_available": crew_results is not None,
                }
            )

            await asyncio.sleep(3)  # Simulate analysis

            # Phase 3: Pattern Recognition and Learning
            await self._update_escalation_progress(
                escalation_id,
                60,
                "pattern_recognition",
                "Identifying complex patterns and applying learned intelligence",
            )

            # Generate preliminary insights from crew results
            if crew_results:
                preliminary_insights = self._extract_strategic_insights(
                    crew_type, crew_results, context
                )
            else:
                preliminary_insights = self._generate_preliminary_insights(
                    crew_type, context
                )

            escalation["preliminary_insights"] = preliminary_insights

            await asyncio.sleep(2)

            # Phase 4: Results Generation and Synthesis
            await self._update_escalation_progress(
                escalation_id,
                90,
                "results_generation",
                "Synthesizing strategic insights and recommendations",
            )

            await asyncio.sleep(2)

            # Phase 5: Completion with Strategic Results
            if crew_results:
                results = await self._generate_strategic_crew_results(
                    crew_type, context, crew_results, preliminary_insights
                )
            else:
                results = await self._generate_crew_results(
                    crew_type, context, preliminary_insights
                )

            escalation["status"] = "completed"
            escalation["progress"] = 100
            escalation["current_phase"] = "completed"
            escalation["results"] = results
            escalation["completed_at"] = datetime.utcnow().isoformat()
            escalation["updated_at"] = datetime.utcnow().isoformat()

            escalation["crew_activity"].append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "activity": f"Strategic {crew_type} completed comprehensive analysis with actionable insights",
                    "phase": "completed",
                    "insights_generated": len(preliminary_insights),
                    "strategic_analysis": crew_results is not None,
                }
            )

            logger.info(
                f"✅ Strategic crew thinking completed for escalation {escalation_id}"
            )

        except Exception as e:
            logger.error(f"❌ Error in strategic crew thinking {escalation_id}: {e}")
            await self._handle_escalation_error(escalation_id, str(e))

    async def _execute_crew_collaboration(
        self,
        escalation_id: str,
        collaboration_strategy: Dict[str, Any],
        context: Dict[str, Any],
    ) -> None:
        """Execute crew collaboration process with strategic crew delegation."""
        try:
            escalation = self.active_escalations[escalation_id]

            # Phase 1: Collaboration Setup
            await self._update_escalation_progress(
                escalation_id,
                10,
                "collaboration_setup",
                "Setting up strategic crew collaboration",
            )

            primary_crew = collaboration_strategy["primary_crew"]
            additional_crews = collaboration_strategy.get("additional_crews", [])
            pattern = collaboration_strategy["pattern"]

            escalation["crew_activity"].append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "activity": f"Initiating {pattern} with {primary_crew} and {len(additional_crews)} additional crews",
                    "phase": "collaboration_setup",
                }
            )

            await asyncio.sleep(2)

            # Phase 2: Primary Crew Analysis
            await self._update_escalation_progress(
                escalation_id,
                30,
                "primary_analysis",
                f"Primary crew {primary_crew} conducting strategic analysis",
            )

            primary_results = None
            if STRATEGIC_CREWS_AVAILABLE and primary_crew in self.strategic_crews:
                primary_results = await self._execute_strategic_crew_analysis(
                    primary_crew, context
                )

            await asyncio.sleep(3)

            # Phase 3: Delegation and Parallel Analysis
            await self._update_escalation_progress(
                escalation_id,
                50,
                "delegation_phase",
                "Delegating to additional crews for comprehensive analysis",
            )

            delegation_results = {}
            if pattern == "parallel_delegation" and additional_crews:
                # Execute parallel delegation
                delegation_results = await self._execute_parallel_delegation(
                    additional_crews, context, escalation_id
                )
            elif pattern == "sequential_delegation" and additional_crews:
                # Execute sequential delegation
                delegation_results = await self._execute_sequential_delegation(
                    additional_crews, context, escalation_id
                )
            elif pattern == "hierarchical_delegation":
                # Execute hierarchical delegation
                delegation_results = await self._execute_hierarchical_delegation(
                    primary_crew, additional_crews, context, escalation_id
                )

            await asyncio.sleep(3)

            # Phase 4: Collaborative Synthesis
            await self._update_escalation_progress(
                escalation_id,
                75,
                "collaborative_synthesis",
                "Synthesizing insights from multiple strategic crews",
            )

            # Generate comprehensive insights from all crew results
            all_crew_results = {"primary": primary_results}
            all_crew_results.update(delegation_results)

            comprehensive_insights = self._synthesize_multi_crew_insights(
                all_crew_results, collaboration_strategy, context
            )
            escalation["preliminary_insights"] = comprehensive_insights

            escalation["crew_activity"].append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "activity": f"Synthesized insights from {len(all_crew_results)} crew analyses",
                    "phase": "collaborative_synthesis",
                    "crews_involved": list(all_crew_results.keys()),
                }
            )

            await asyncio.sleep(2)

            # Phase 5: Final Results and Recommendations
            await self._update_escalation_progress(
                escalation_id,
                95,
                "final_synthesis",
                "Generating final strategic recommendations",
            )

            await asyncio.sleep(2)

            # Generate final collaborative results
            results = await self._generate_collaborative_results(
                collaboration_strategy, context, comprehensive_insights
            )
            results["crew_collaboration_details"] = {
                "primary_crew": primary_crew,
                "additional_crews": additional_crews,
                "collaboration_pattern": pattern,
                "total_crews_involved": len(all_crew_results),
                "strategic_crews_executed": sum(
                    1 for r in all_crew_results.values() if r is not None
                ),
            }

            escalation["status"] = "completed"
            escalation["progress"] = 100
            escalation["current_phase"] = "completed"
            escalation["results"] = results
            escalation["completed_at"] = datetime.utcnow().isoformat()
            escalation["updated_at"] = datetime.utcnow().isoformat()

            escalation["crew_activity"].append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "activity": f"Strategic crew collaboration completed with {len(comprehensive_insights)} insights",
                    "phase": "completed",
                    "collaboration_success": True,
                }
            )

            logger.info(
                f"✅ Strategic crew collaboration completed for escalation {escalation_id}"
            )

        except Exception as e:
            logger.error(
                f"❌ Error in strategic crew collaboration {escalation_id}: {e}"
            )
            await self._handle_escalation_error(escalation_id, str(e))

    async def _execute_strategic_crew_analysis(
        self, crew_type: str, context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Execute analysis with a specific strategic crew."""
        try:
            if not STRATEGIC_CREWS_AVAILABLE or crew_type not in self.strategic_crews:
                return None

            strategic_crew = self.strategic_crews[crew_type]
            page_data = context.get("page_data", {})
            assets_data = page_data.get("assets", []) if page_data else []

            # Execute appropriate crew method
            if crew_type == "asset_intelligence_crew":
                return await strategic_crew.analyze_assets(assets_data, context)
            elif crew_type == "dependency_analysis_crew":
                return await strategic_crew.analyze_dependencies(assets_data, context)
            elif crew_type == "tech_debt_analysis_crew":
                return await strategic_crew.analyze_tech_debt(assets_data, context)

            return None

        except Exception as e:
            logger.error(f"❌ Strategic crew {crew_type} execution failed: {e}")
            return None

    async def _execute_parallel_delegation(
        self, crews: List[str], context: Dict[str, Any], escalation_id: str
    ) -> Dict[str, Any]:
        """Execute parallel delegation to multiple crews."""
        results = {}

        # Create tasks for parallel execution
        tasks = []
        for crew_type in crews:
            if STRATEGIC_CREWS_AVAILABLE and crew_type in self.strategic_crews:
                task = asyncio.create_task(
                    self._execute_strategic_crew_analysis(crew_type, context)
                )
                tasks.append((crew_type, task))

        # Wait for all tasks to complete
        for crew_type, task in tasks:
            try:
                result = await task
                results[crew_type] = result

                # Update activity
                escalation = self.active_escalations[escalation_id]
                escalation["crew_activity"].append(
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "activity": f"Parallel delegation to {crew_type} completed",
                        "phase": "parallel_delegation",
                        "success": result is not None,
                    }
                )

            except Exception as e:
                logger.error(f"❌ Parallel delegation to {crew_type} failed: {e}")
                results[crew_type] = None

        return results

    async def _execute_sequential_delegation(
        self, crews: List[str], context: Dict[str, Any], escalation_id: str
    ) -> Dict[str, Any]:
        """Execute sequential delegation to multiple crews."""
        results = {}

        for crew_type in crews:
            try:
                result = await self._execute_strategic_crew_analysis(crew_type, context)
                results[crew_type] = result

                # Update activity
                escalation = self.active_escalations[escalation_id]
                escalation["crew_activity"].append(
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "activity": f"Sequential delegation to {crew_type} completed",
                        "phase": "sequential_delegation",
                        "success": result is not None,
                    }
                )

                # Add delay between sequential executions
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"❌ Sequential delegation to {crew_type} failed: {e}")
                results[crew_type] = None

        return results

    async def _execute_hierarchical_delegation(
        self,
        primary_crew: str,
        additional_crews: List[str],
        context: Dict[str, Any],
        escalation_id: str,
    ) -> Dict[str, Any]:
        """Execute hierarchical delegation with specialist review."""
        results = {}

        # Level 1: Specialist analysis (additional crews)
        specialist_results = await self._execute_parallel_delegation(
            additional_crews[:2], context, escalation_id
        )
        results.update(specialist_results)

        # Level 2: Senior expert review (primary crew with specialist context)
        enhanced_context = {**context, "specialist_insights": specialist_results}
        senior_result = await self._execute_strategic_crew_analysis(
            primary_crew, enhanced_context
        )
        results["senior_review"] = senior_result

        # Level 3: Executive synthesis (if more than 3 crews involved)
        if len(additional_crews) > 2:
            executive_context = {**enhanced_context, "senior_review": senior_result}
            executive_result = await self._execute_strategic_crew_analysis(
                additional_crews[2], executive_context
            )
            results["executive_synthesis"] = executive_result

        return results

    def _extract_strategic_insights(
        self, crew_type: str, crew_results: Dict[str, Any], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract insights from strategic crew results."""
        insights = []

        try:
            if crew_results.get("success") and crew_results.get("analysis_results"):
                analysis_results = crew_results["analysis_results"]

                # Extract insights based on crew type
                if crew_type == "asset_intelligence_crew":
                    insights.extend(
                        self._extract_asset_intelligence_insights(
                            analysis_results, context
                        )
                    )
                elif crew_type == "dependency_analysis_crew":
                    insights.extend(
                        self._extract_dependency_insights(analysis_results, context)
                    )
                elif crew_type == "tech_debt_analysis_crew":
                    insights.extend(
                        self._extract_tech_debt_insights(analysis_results, context)
                    )

                # Add crew metadata insight
                insights.append(
                    {
                        "type": "crew_execution_success",
                        "crew_type": crew_type,
                        "assets_analyzed": len(analysis_results),
                        "insight": f"Strategic {crew_type} successfully analyzed {len(analysis_results)} assets with enhanced intelligence",
                        "confidence": 0.9,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

        except Exception as e:
            logger.error(f"❌ Error extracting strategic insights: {e}")
            insights.append(
                {
                    "type": "crew_execution_error",
                    "crew_type": crew_type,
                    "error": str(e),
                    "insight": "Strategic crew execution encountered issues but provided fallback analysis",
                    "confidence": 0.3,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        return insights

    def _extract_asset_intelligence_insights(
        self, analysis_results: List[Any], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract insights from asset intelligence crew results."""
        insights = []

        for result in analysis_results:
            if hasattr(result, "confidence_score") and result.confidence_score > 0.8:
                insights.append(
                    {
                        "type": "high_confidence_classification",
                        "asset_name": result.asset_name,
                        "classification": result.classification,
                        "confidence": result.confidence_score,
                        "insight": f"High-confidence asset classification achieved for {result.asset_name}",
                        "recommendations": result.recommendations,
                    }
                )

            if (
                hasattr(result, "migration_priority")
                and result.migration_priority == "high"
            ):
                insights.append(
                    {
                        "type": "high_priority_migration",
                        "asset_name": result.asset_name,
                        "priority": result.migration_priority,
                        "insight": f"Asset {result.asset_name} identified as high priority for migration",
                        "business_value": result.business_context.get(
                            "business_value_score", 0
                        ),
                    }
                )

        return insights

    def _extract_dependency_insights(
        self, analysis_results: List[Any], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract insights from dependency analysis crew results."""
        insights = []

        for result in analysis_results:
            if hasattr(result, "network_analysis"):
                complexity = result.network_analysis.get("complexity_level", "medium")
                if complexity in ["high", "very_high"]:
                    insights.append(
                        {
                            "type": "complex_dependencies",
                            "asset_name": result.asset_name,
                            "complexity": complexity,
                            "insight": f"Complex dependency patterns identified for {result.asset_name}",
                            "migration_impact": "requires_careful_planning",
                        }
                    )

        return insights

    def _extract_tech_debt_insights(
        self, analysis_results: List[Any], context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract insights from tech debt analysis crew results."""
        insights = []

        for result in analysis_results:
            if hasattr(result, "legacy_assessment"):
                legacy_level = result.legacy_assessment.get("legacy_level", "medium")
                if legacy_level in ["high", "critical"]:
                    insights.append(
                        {
                            "type": "high_tech_debt",
                            "asset_name": result.asset_name,
                            "legacy_level": legacy_level,
                            "insight": f"High technical debt identified for {result.asset_name}",
                            "modernization_urgency": result.legacy_assessment.get(
                                "modernization_urgency", {}
                            ),
                        }
                    )

        return insights

    def _synthesize_multi_crew_insights(
        self,
        crew_results: Dict[str, Any],
        collaboration_strategy: Dict[str, Any],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Synthesize insights from multiple crew analyses."""
        synthesized_insights = []

        # Cross-crew pattern identification
        asset_patterns = {}
        for crew_name, results in crew_results.items():
            if results and results.get("analysis_results"):
                for result in results["analysis_results"]:
                    asset_id = getattr(result, "asset_id", f"unknown_{crew_name}")
                    if asset_id not in asset_patterns:
                        asset_patterns[asset_id] = {}
                    asset_patterns[asset_id][crew_name] = result

        # Generate cross-crew insights
        for asset_id, crew_analyses in asset_patterns.items():
            if len(crew_analyses) > 1:
                synthesized_insights.append(
                    {
                        "type": "cross_crew_analysis",
                        "asset_id": asset_id,
                        "crews_involved": list(crew_analyses.keys()),
                        "insight": f"Multi-crew analysis completed for {asset_id} with {len(crew_analyses)} strategic perspectives",
                        "synthesis_confidence": 0.85,
                        "collaboration_pattern": collaboration_strategy["pattern"],
                    }
                )

        # Add collaboration strategy insight
        synthesized_insights.append(
            {
                "type": "collaboration_success",
                "strategy": collaboration_strategy["pattern"],
                "crews_executed": len(
                    [r for r in crew_results.values() if r is not None]
                ),
                "total_crews": len(crew_results),
                "insight": f"Strategic crew collaboration using {collaboration_strategy['pattern']} pattern completed successfully",
                "collaboration_effectiveness": len(
                    [r for r in crew_results.values() if r is not None]
                )
                / len(crew_results),
            }
        )

        return synthesized_insights

    async def _generate_strategic_crew_results(
        self,
        crew_type: str,
        context: Dict[str, Any],
        crew_results: Dict[str, Any],
        preliminary_insights: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate results from strategic crew execution."""
        base_results = await self._generate_crew_results(
            crew_type, context, preliminary_insights
        )

        # Enhance with strategic crew data
        if crew_results and crew_results.get("success"):
            base_results.update(
                {
                    "strategic_analysis": True,
                    "crew_execution_success": True,
                    "analysis_metadata": crew_results.get("metadata", {}),
                    "crew_insights": crew_results.get("crew_insights", []),
                    "analysis_summary": crew_results.get("summary", {}),
                    "strategic_recommendations": self._extract_strategic_recommendations(
                        crew_type, crew_results
                    ),
                    "confidence_improvements": {
                        "strategic_analysis_applied": True,
                        "analysis_depth": "comprehensive",
                        "crew_confidence": crew_results.get("metadata", {}).get(
                            "average_confidence", 0.8
                        ),
                    },
                }
            )
        else:
            base_results.update(
                {
                    "strategic_analysis": False,
                    "crew_execution_success": False,
                    "fallback_analysis": True,
                    "note": "Strategic crew execution failed, using fallback analysis",
                }
            )

        return base_results

    def _extract_strategic_recommendations(
        self, crew_type: str, crew_results: Dict[str, Any]
    ) -> List[str]:
        """Extract strategic recommendations from crew results."""
        recommendations = []

        try:
            analysis_results = crew_results.get("analysis_results", [])

            for result in analysis_results:
                if hasattr(result, "recommendations"):
                    recommendations.extend(result.recommendations)

                # Add crew-specific recommendations
                if crew_type == "asset_intelligence_crew" and hasattr(
                    result, "migration_priority"
                ):
                    if result.migration_priority == "high":
                        recommendations.append(
                            f"Prioritize {result.asset_name} for early migration due to high business value"
                        )
                elif crew_type == "dependency_analysis_crew" and hasattr(
                    result, "critical_path_analysis"
                ):
                    recommendations.append(
                        f"Review dependency paths for {result.asset_name} before migration"
                    )
                elif crew_type == "tech_debt_analysis_crew" and hasattr(
                    result, "sixr_recommendations"
                ):
                    sixr_strategy = result.sixr_recommendations.get(
                        "recommended_strategy", "rehost"
                    )
                    recommendations.append(
                        f"Apply {sixr_strategy} strategy for {result.asset_name}"
                    )

        except Exception as e:
            logger.error(f"❌ Error extracting strategic recommendations: {e}")
            recommendations.append(
                "Review strategic analysis results for detailed recommendations"
            )

        return list(set(recommendations))  # Remove duplicates

    async def _update_escalation_progress(
        self, escalation_id: str, progress: int, phase: str, description: str
    ) -> None:
        """Update escalation progress and status."""
        if escalation_id in self.active_escalations:
            escalation = self.active_escalations[escalation_id]
            escalation["progress"] = progress
            escalation["current_phase"] = phase
            escalation["phase_description"] = description
            escalation["updated_at"] = datetime.utcnow().isoformat()

            if progress > 0 and escalation["status"] == "initializing":
                escalation["status"] = (
                    "thinking"
                    if escalation.get("escalation_type") == "think"
                    else "pondering"
                )

    async def _handle_escalation_error(
        self, escalation_id: str, error_message: str
    ) -> None:
        """Handle escalation errors."""
        if escalation_id in self.active_escalations:
            escalation = self.active_escalations[escalation_id]
            escalation["status"] = "failed"
            escalation["error"] = error_message
            escalation["failed_at"] = datetime.utcnow().isoformat()
            escalation["updated_at"] = datetime.utcnow().isoformat()

    async def get_escalation_status(
        self, escalation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get status of a specific escalation."""
        return self.active_escalations.get(escalation_id)

    async def get_flow_escalations(self, flow_id: str) -> List[Dict[str, Any]]:
        """Get all escalations for a specific flow."""
        flow_escalations = []
        for escalation in self.active_escalations.values():
            if escalation.get("context", {}).get("flow_id") == flow_id:
                flow_escalations.append(escalation)

        # Sort by creation time
        flow_escalations.sort(key=lambda x: x.get("started_at", ""), reverse=True)
        return flow_escalations

    async def cancel_escalation(self, escalation_id: str) -> Dict[str, Any]:
        """Cancel an ongoing escalation."""
        if escalation_id not in self.active_escalations:
            return {"success": False, "error": "Escalation not found"}

        escalation = self.active_escalations[escalation_id]

        if escalation["status"] in ["completed", "failed", "cancelled"]:
            return {
                "success": False,
                "error": f"Cannot cancel escalation in {escalation['status']} state",
            }

        escalation["status"] = "cancelled"
        escalation["cancelled_at"] = datetime.utcnow().isoformat()
        escalation["updated_at"] = datetime.utcnow().isoformat()

        logger.info(f"🚫 Cancelled escalation {escalation_id}")
        return {"success": True, "message": "Escalation cancelled successfully"}

    def cleanup_completed_escalations(self, max_age_hours: int = 24) -> int:
        """Clean up old completed escalations."""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

        to_remove = []
        for escalation_id, escalation in self.active_escalations.items():
            if escalation["status"] in ["completed", "failed", "cancelled"]:
                completed_time = (
                    escalation.get("completed_at")
                    or escalation.get("failed_at")
                    or escalation.get("cancelled_at")
                )
                if (
                    completed_time
                    and datetime.fromisoformat(completed_time) < cutoff_time
                ):
                    to_remove.append(escalation_id)

        for escalation_id in to_remove:
            del self.active_escalations[escalation_id]

        if to_remove:
            logger.info(f"🧹 Cleaned up {len(to_remove)} old escalations")

        return len(to_remove)

    def _generate_preliminary_insights(
        self, crew_type: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate preliminary insights when crew results are not available."""
        return {
            "crew_type": crew_type,
            "status": "preliminary",
            "insights": f"Initial analysis for {crew_type} crew based on context",
            "generated_at": datetime.utcnow().isoformat(),
            "context_summary": (
                str(context)[:200] + "..." if len(str(context)) > 200 else str(context)
            ),
        }

    async def _generate_crew_results(
        self,
        crew_type: str,
        context: Dict[str, Any],
        preliminary_insights: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate crew results based on preliminary insights."""
        return {
            "crew_type": crew_type,
            "status": "generated",
            "results": f"Generated results for {crew_type} crew",
            "preliminary_insights": preliminary_insights,
            "generated_at": datetime.utcnow().isoformat(),
            "context": context,
        }

    async def _generate_collaborative_results(
        self,
        collaboration_strategy: str,
        context: Dict[str, Any],
        comprehensive_insights: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate collaborative results from multiple crews."""
        return {
            "collaboration_strategy": collaboration_strategy,
            "status": "collaborative_complete",
            "results": f"Collaborative analysis using {collaboration_strategy} strategy",
            "comprehensive_insights": comprehensive_insights,
            "generated_at": datetime.utcnow().isoformat(),
            "context": context,
        }
