"""
Escalation handlers and actions for core execution logic of crew thinking and collaboration.
"""

import asyncio
from typing import Dict, Any, List, Optional

from .base import logger, STRATEGIC_CREWS_AVAILABLE
from .exceptions import CrewExecutionError, CollaborationError, DelegationError


class EscalationExecutionHandler:
    """
    Handles core execution logic for crew thinking and collaboration processes.
    """

    def __init__(
        self,
        strategic_crews: Dict[str, Any],
        notification_manager: Any,
        metrics_manager: Any,
    ):
        """Initialize with strategic crews and managers."""
        self.strategic_crews = strategic_crews
        self.notification_manager = notification_manager
        self.metrics_manager = metrics_manager

    async def execute_crew_thinking(
        self, escalation_id: str, crew_type: str, context: Dict[str, Any]
    ) -> None:
        """Execute crew thinking process in background with strategic crew integration."""
        try:
            # Phase 1: Crew Initialization
            await self.notification_manager.update_escalation_progress(
                escalation_id,
                10,
                "crew_initialization",
                "Initializing strategic crew for deeper analysis",
            )
            await asyncio.sleep(2)

            # Phase 2: Strategic Crew Execution
            await self.notification_manager.update_escalation_progress(
                escalation_id,
                30,
                "strategic_analysis",
                f"Strategic {crew_type} analyzing {context.get('page', 'data')} with enhanced intelligence",
            )

            # Execute strategic crew if available
            crew_results = await self._execute_strategic_crew_analysis(
                crew_type, context
            )

            # Log crew activity
            self.notification_manager.log_crew_activity(
                escalation_id,
                f"Strategic {crew_type} completed enhanced analysis",
                "strategic_analysis",
                {"crew_results_available": crew_results is not None},
            )

            await asyncio.sleep(3)  # Simulate analysis

            # Phase 3: Pattern Recognition and Learning
            await self.notification_manager.update_escalation_progress(
                escalation_id,
                60,
                "pattern_recognition",
                "Identifying complex patterns and applying learned intelligence",
            )

            # Generate preliminary insights from crew results
            if crew_results:
                preliminary_insights = self.metrics_manager.extract_strategic_insights(
                    crew_type, crew_results, context
                )
            else:
                preliminary_insights = (
                    self.metrics_manager.generate_preliminary_insights(
                        crew_type, context
                    )
                )

            self.notification_manager.add_preliminary_insights(
                escalation_id, preliminary_insights
            )
            await asyncio.sleep(2)

            # Phase 4: Results Generation and Synthesis
            await self.notification_manager.update_escalation_progress(
                escalation_id,
                90,
                "results_generation",
                "Synthesizing strategic insights and recommendations",
            )
            await asyncio.sleep(2)

            # Phase 5: Completion with Strategic Results
            if crew_results:
                results = await self.metrics_manager.generate_strategic_crew_results(
                    crew_type, context, crew_results, preliminary_insights
                )
            else:
                results = await self.metrics_manager.generate_crew_results(
                    crew_type, context, preliminary_insights
                )

            # Complete escalation
            self.notification_manager.complete_escalation(escalation_id, results)

            self.notification_manager.log_crew_activity(
                escalation_id,
                f"Strategic {crew_type} completed comprehensive analysis with actionable insights",
                "completed",
                {
                    "insights_generated": len(preliminary_insights),
                    "strategic_analysis": crew_results is not None,
                },
            )

            logger.info(
                f"✅ Strategic crew thinking completed for escalation {escalation_id}"
            )

        except Exception as e:
            logger.error(f"❌ Error in strategic crew thinking {escalation_id}: {e}")
            await self.notification_manager.handle_escalation_error(
                escalation_id, str(e), {"crew_type": crew_type, "phase": "execution"}
            )
            raise CrewExecutionError(
                f"Crew thinking execution failed: {e}", crew_type, escalation_id
            )

    async def execute_crew_collaboration(
        self,
        escalation_id: str,
        collaboration_strategy: Dict[str, Any],
        context: Dict[str, Any],
    ) -> None:
        """Execute crew collaboration process with strategic crew delegation."""
        try:
            # Phase 1: Collaboration Setup
            await self.notification_manager.update_escalation_progress(
                escalation_id,
                10,
                "collaboration_setup",
                "Setting up strategic crew collaboration",
            )

            primary_crew = collaboration_strategy["primary_crew"]
            additional_crews = collaboration_strategy.get("additional_crews", [])
            pattern = collaboration_strategy["pattern"]

            self.notification_manager.log_crew_activity(
                escalation_id,
                f"Initiating {pattern} with {primary_crew} and {len(additional_crews)} additional crews",
                "collaboration_setup",
            )

            await asyncio.sleep(2)

            # Phase 2: Primary Crew Analysis
            await self.notification_manager.update_escalation_progress(
                escalation_id,
                30,
                "primary_analysis",
                f"Primary crew {primary_crew} conducting strategic analysis",
            )

            primary_results = await self._execute_strategic_crew_analysis(
                primary_crew, context
            )
            await asyncio.sleep(3)

            # Phase 3: Delegation and Parallel Analysis
            await self.notification_manager.update_escalation_progress(
                escalation_id,
                50,
                "delegation_phase",
                "Delegating to additional crews for comprehensive analysis",
            )

            delegation_results = {}
            if pattern == "parallel_delegation" and additional_crews:
                delegation_results = await self._execute_parallel_delegation(
                    additional_crews, context, escalation_id
                )
            elif pattern == "sequential_delegation" and additional_crews:
                delegation_results = await self._execute_sequential_delegation(
                    additional_crews, context, escalation_id
                )
            elif pattern == "hierarchical_delegation":
                delegation_results = await self._execute_hierarchical_delegation(
                    primary_crew, additional_crews, context, escalation_id
                )

            await asyncio.sleep(3)

            # Phase 4: Collaborative Synthesis
            await self.notification_manager.update_escalation_progress(
                escalation_id,
                75,
                "collaborative_synthesis",
                "Synthesizing insights from multiple strategic crews",
            )

            # Generate comprehensive insights from all crew results
            all_crew_results = {"primary": primary_results}
            all_crew_results.update(delegation_results)

            comprehensive_insights = (
                self.metrics_manager.synthesize_multi_crew_insights(
                    all_crew_results, collaboration_strategy, context
                )
            )
            self.notification_manager.add_preliminary_insights(
                escalation_id, comprehensive_insights
            )

            self.notification_manager.log_crew_activity(
                escalation_id,
                f"Synthesized insights from {len(all_crew_results)} crew analyses",
                "collaborative_synthesis",
                {"crews_involved": list(all_crew_results.keys())},
            )

            await asyncio.sleep(2)

            # Phase 5: Final Results and Recommendations
            await self.notification_manager.update_escalation_progress(
                escalation_id,
                95,
                "final_synthesis",
                "Generating final strategic recommendations",
            )

            await asyncio.sleep(2)

            # Generate final collaborative results
            results = await self.metrics_manager.generate_collaborative_results(
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

            # Complete escalation
            self.notification_manager.complete_escalation(escalation_id, results)

            self.notification_manager.log_crew_activity(
                escalation_id,
                f"Strategic crew collaboration completed with {len(comprehensive_insights)} insights",
                "completed",
                {"collaboration_success": True},
            )

            logger.info(
                f"✅ Strategic crew collaboration completed for escalation {escalation_id}"
            )

        except Exception as e:
            logger.error(
                f"❌ Error in strategic crew collaboration {escalation_id}: {e}"
            )
            await self.notification_manager.handle_escalation_error(
                escalation_id,
                str(e),
                {
                    "collaboration_strategy": collaboration_strategy,
                    "phase": "collaboration",
                },
            )
            raise CollaborationError(
                f"Crew collaboration execution failed: {e}",
                collaboration_strategy.get("pattern", "unknown"),
                escalation_id,
            )

    async def _execute_strategic_crew_analysis(
        self, crew_type: str, context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Execute analysis with a specific strategic crew."""
        try:
            if not STRATEGIC_CREWS_AVAILABLE or crew_type not in self.strategic_crews:
                logger.debug(
                    f"Strategic crew {crew_type} not available, using fallback"
                )
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
                self.notification_manager.log_crew_activity(
                    escalation_id,
                    f"Parallel delegation to {crew_type} completed",
                    "parallel_delegation",
                    {"success": result is not None},
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
                self.notification_manager.log_crew_activity(
                    escalation_id,
                    f"Sequential delegation to {crew_type} completed",
                    "sequential_delegation",
                    {"success": result is not None},
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

        try:
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

        except Exception as e:
            logger.error(f"❌ Hierarchical delegation failed: {e}")
            raise DelegationError(
                f"Hierarchical delegation failed: {e}",
                "hierarchical_delegation",
                escalation_id,
            )


# Export for use in other modules
__all__ = ["EscalationExecutionHandler"]
