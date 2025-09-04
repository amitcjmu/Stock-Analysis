"""
Gap Analysis Phase Manager

Handles the orchestration of gap analysis in the collection flow.
This manager analyzes collected data to identify gaps and missing information.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.collection_flow import AutomationTier, CollectionPhase, CollectionStatus
from app.services.ai_analysis import (
    BusinessContextAnalyzer,
    ConfidenceScorer,
    GapAnalysisAgent,
)
from app.services.crewai_flows.handlers.enhanced_error_handler import (
    enhanced_error_handler,
)
from app.services.crewai_flows.utils.retry_utils import retry_with_backoff

logger = logging.getLogger(__name__)


class GapAnalysisManager:
    """
    Manages the gap analysis phase of the collection flow.

    This manager handles:
    - AI-powered gap analysis
    - Gap analysis crew creation and execution
    - SIXR impact assessment
    - Gap categorization and prioritization
    - Determining next phase based on gaps
    - State persistence and updates
    """

    def __init__(self, flow_context, state_manager, audit_service):
        """
        Initialize the gap analysis manager.

        Args:
            flow_context: Flow context containing flow ID, client, and engagement info
            state_manager: State manager for persisting flow state
            audit_service: Audit logging service
        """
        self.flow_context = flow_context
        self.state_manager = state_manager
        self.audit_service = audit_service

        # Initialize AI services with required context
        self.gap_analysis_agent = GapAnalysisAgent(
            client_account_id=flow_context.client_account_id,
            engagement_id=flow_context.engagement_id,
        )
        self.business_analyzer = BusinessContextAnalyzer()
        self.confidence_scorer = ConfidenceScorer()

    async def execute(
        self, flow_state, crewai_service, client_requirements
    ) -> Dict[str, Any]:
        """
        Execute the gap analysis phase.

        Args:
            flow_state: Current collection flow state
            crewai_service: CrewAI service for creating crews
            client_requirements: Client-specific requirements including SIXR requirements

        Returns:
            Dict containing phase execution results
        """
        try:
            logger.info(
                f"🔎 Starting gap analysis for flow {self.flow_context.flow_id}"
            )

            # Update state to indicate phase start
            flow_state.status = CollectionStatus.ANALYZING_GAPS
            flow_state.current_phase = CollectionPhase.GAP_ANALYSIS
            flow_state.updated_at = datetime.utcnow()

            # Get collected data and initial gaps
            collected_data = flow_state.collected_data
            collection_gaps = flow_state.phase_results.get(
                "automated_collection", {}
            ).get("identified_gaps", [])

            # Perform AI gap analysis
            ai_analysis = await self._perform_ai_gap_analysis(
                collected_data,
                collection_gaps,
                client_requirements,
                flow_state.automation_tier,
            )

            # Execute gap analysis crew
            crew_results = await self._execute_gap_analysis_crew(
                crewai_service,
                collected_data,
                ai_analysis,
                client_requirements,
                flow_state.automation_tier,
            )

            # Process and categorize gaps
            processed_gaps = await self._process_gap_results(
                crew_results, ai_analysis, client_requirements
            )

            # Determine next phase
            next_phase = self._determine_next_phase(
                processed_gaps, flow_state.automation_tier
            )

            # Update flow state
            await self._update_flow_state(flow_state, processed_gaps, next_phase)

            # Log phase completion
            await self.audit_service.log_flow_event(
                flow_id=self.flow_context.flow_id,
                event_type="gap_analysis_completed",
                event_data={
                    "gaps_identified": len(processed_gaps["identified_gaps"]),
                    "sixr_impact_score": processed_gaps["sixr_impact"][
                        "overall_impact_score"
                    ],
                    "next_phase": next_phase.value,
                    "gap_categories": list(processed_gaps["gap_categories"].keys()),
                },
            )

            return {
                "phase": "gap_analysis",
                "status": "completed",
                "gaps_identified": len(processed_gaps["identified_gaps"]),
                "sixr_impact_score": processed_gaps["sixr_impact"][
                    "overall_impact_score"
                ],
                "next_phase": next_phase.value,
                "requires_manual_collection": next_phase
                == CollectionPhase.QUESTIONNAIRE_GENERATION,
            }

        except Exception as e:
            logger.error(f"❌ Gap analysis failed: {e}")
            flow_state.add_error("gap_analysis", str(e))
            await enhanced_error_handler.handle_error(e, self.flow_context)
            raise

    async def resume(
        self, flow_state, user_inputs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Resume gap analysis after pause.

        Args:
            flow_state: Current collection flow state
            user_inputs: Optional user inputs for gap prioritization

        Returns:
            Dict containing resume results
        """
        logger.info(f"🔄 Resuming gap analysis for flow {self.flow_context.flow_id}")

        if user_inputs and user_inputs.get("gap_priorities"):
            # Apply user-defined gap priorities
            gap_results = flow_state.gap_analysis_results
            gap_results["user_priorities"] = user_inputs["gap_priorities"]
            flow_state.gap_analysis_results = gap_results
            flow_state.last_user_interaction = datetime.utcnow()

        # Determine next phase based on gaps and user input
        next_phase = flow_state.next_phase
        if user_inputs and user_inputs.get("skip_manual_collection"):
            next_phase = CollectionPhase.DATA_VALIDATION

        # Update progress
        flow_state.progress = 55.0
        flow_state.next_phase = next_phase
        await self.state_manager.save_state(flow_state.to_dict())

        return {
            "phase": "gap_analysis",
            "status": "resumed",
            "next_phase": next_phase.value,
            "can_proceed": True,
        }

    async def _perform_ai_gap_analysis(
        self,
        collected_data: List[Dict],
        existing_gaps: List[Dict],
        client_requirements: Dict[str, Any],
        automation_tier: str,
    ) -> Dict[str, Any]:
        """Perform AI-powered gap analysis"""
        logger.info("🤖 Performing AI gap analysis")

        # Extract SIXR requirements
        sixr_requirements = client_requirements.get("sixr_requirements", {})

        # Perform gap analysis
        gap_analysis_result = await self.gap_analysis_agent.analyze_data_gaps(
            collected_data=collected_data,
            existing_gaps=existing_gaps,
            sixr_requirements=sixr_requirements,
            automation_tier=automation_tier,
        )

        # Analyze business impact
        business_impact = await self.business_analyzer.analyze_gap_business_impact(
            gaps=gap_analysis_result.get("identified_gaps", []),
            business_context=client_requirements.get("business_context", {}),
            sixr_requirements=sixr_requirements,
        )

        gap_analysis_result["business_impact"] = business_impact

        logger.info(
            f"✅ AI gap analysis complete: {len(gap_analysis_result.get('identified_gaps', []))} gaps found"
        )
        return gap_analysis_result

    async def _execute_gap_analysis_crew(
        self,
        crewai_service,
        collected_data,
        ai_analysis,
        client_requirements,
        automation_tier,
    ) -> Dict[str, Any]:
        """Create and execute the gap analysis crew"""
        logger.info("🤖 Creating gap analysis crew")

        # Import crew creation function
        from app.services.crewai_flows.crews.collection.gap_analysis_crew import (
            create_gap_analysis_crew,
        )

        # Extract SIXR requirements
        sixr_requirements = client_requirements.get("sixr_requirements", {})

        # Create crew with context
        crew = create_gap_analysis_crew(
            crewai_service=crewai_service,
            collected_data=collected_data,
            sixr_requirements=sixr_requirements,
            context={
                "automation_tier": automation_tier,
                "existing_gaps": ai_analysis.get("identified_gaps", []),
                "business_impact": ai_analysis.get("business_impact", {}),
                "flow_id": self.flow_context.flow_id,
                "critical_domains": client_requirements.get("critical_domains", []),
            },
        )

        # Execute with retry
        logger.info("🚀 Executing gap analysis crew")
        crew_result = await retry_with_backoff(
            crew.kickoff,
            inputs={"collected_data": collected_data, "ai_analysis": ai_analysis},
        )

        return crew_result

    async def _process_gap_results(
        self,
        crew_results: Dict[str, Any],
        ai_analysis: Dict[str, Any],
        client_requirements: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Process and categorize gap analysis results"""
        logger.info("🔧 Processing gap analysis results")

        # Extract results from crew
        identified_gaps = crew_results.get("data_gaps", [])
        gap_categories = crew_results.get("gap_categories", {})
        sixr_impact = crew_results.get("sixr_impact_analysis", {})
        recommendations = crew_results.get("recommendations", [])

        # Enhance gaps with AI insights
        enhanced_gaps = self._enhance_gaps_with_ai_insights(
            identified_gaps, ai_analysis
        )

        # Prioritize gaps based on SIXR impact
        prioritized_gaps = self._prioritize_gaps(
            enhanced_gaps, sixr_impact, client_requirements
        )

        # Calculate overall gap severity
        overall_severity = self._calculate_overall_severity(prioritized_gaps)

        return {
            "identified_gaps": prioritized_gaps,
            "gap_categories": gap_categories,
            "sixr_impact": sixr_impact,
            "recommendations": recommendations,
            "overall_severity": overall_severity,
            "ai_insights": ai_analysis,
            "crew_output": crew_results,
        }

    async def _update_flow_state(
        self, flow_state, processed_gaps: Dict[str, Any], next_phase: CollectionPhase
    ):
        """Update flow state with gap analysis results"""
        logger.info("💾 Updating flow state with gap analysis results")

        # Store gap analysis results
        flow_state.gap_analysis_results = {
            "identified_gaps": processed_gaps["identified_gaps"],
            "gap_categories": processed_gaps["gap_categories"],
            "sixr_impact": processed_gaps["sixr_impact"],
            "recommendations": processed_gaps["recommendations"],
            "overall_severity": processed_gaps["overall_severity"],
        }

        # Store phase results
        flow_state.phase_results["gap_analysis"] = {
            "gaps_summary": {
                "total_gaps": len(processed_gaps["identified_gaps"]),
                "critical_gaps": len(
                    [
                        g
                        for g in processed_gaps["identified_gaps"]
                        if g.get("severity") == "critical"
                    ]
                ),
                "high_gaps": len(
                    [
                        g
                        for g in processed_gaps["identified_gaps"]
                        if g.get("severity") == "high"
                    ]
                ),
                "medium_gaps": len(
                    [
                        g
                        for g in processed_gaps["identified_gaps"]
                        if g.get("severity") == "medium"
                    ]
                ),
                "low_gaps": len(
                    [
                        g
                        for g in processed_gaps["identified_gaps"]
                        if g.get("severity") == "low"
                    ]
                ),
            },
            "sixr_impact_score": processed_gaps["sixr_impact"].get(
                "overall_impact_score", 0.0
            ),
            "gap_categories": list(processed_gaps["gap_categories"].keys()),
            "recommendations": processed_gaps["recommendations"],
        }

        # Update progress and next phase
        flow_state.progress = 55.0
        flow_state.next_phase = next_phase

        # Persist state
        await self.state_manager.save_state(flow_state.to_dict())

    def _determine_next_phase(
        self, processed_gaps: Dict[str, Any], automation_tier: AutomationTier
    ) -> CollectionPhase:
        """Determine next phase based on gaps and automation tier"""
        identified_gaps = processed_gaps["identified_gaps"]

        # Tier 1: Skip manual collection
        if automation_tier == AutomationTier.TIER_1:
            logger.info("Tier 1 automation - skipping manual collection")
            return CollectionPhase.DATA_VALIDATION

        # No gaps: Skip to validation
        if not identified_gaps:
            logger.info("No gaps identified - proceeding to validation")
            return CollectionPhase.DATA_VALIDATION

        # Critical gaps or low SIXR readiness: Require manual collection
        critical_gaps = [g for g in identified_gaps if g.get("severity") == "critical"]
        sixr_score = processed_gaps["sixr_impact"].get("overall_impact_score", 0.0)

        if critical_gaps or sixr_score > 0.7:
            logger.info(
                f"Critical gaps or high SIXR impact ({sixr_score}) - manual collection required"
            )
            return CollectionPhase.QUESTIONNAIRE_GENERATION

        # Minor gaps: Optional manual collection
        logger.info("Minor gaps identified - manual collection optional")
        return CollectionPhase.QUESTIONNAIRE_GENERATION

    def _enhance_gaps_with_ai_insights(
        self, gaps: List[Dict], ai_analysis: Dict[str, Any]
    ) -> List[Dict]:
        """Enhance gap information with AI insights"""
        ai_gap_map = {
            g["id"]: g for g in ai_analysis.get("identified_gaps", []) if "id" in g
        }

        enhanced_gaps = []
        for gap in gaps:
            enhanced_gap = gap.copy()

            # Add AI insights if available
            gap_id = gap.get("id")
            if gap_id and gap_id in ai_gap_map:
                ai_gap = ai_gap_map[gap_id]
                enhanced_gap["ai_confidence"] = ai_gap.get("confidence", 0.0)
                enhanced_gap["ai_recommendations"] = ai_gap.get("recommendations", [])
                enhanced_gap["business_impact"] = ai_gap.get("business_impact", {})

            enhanced_gaps.append(enhanced_gap)

        return enhanced_gaps

    def _prioritize_gaps(
        self,
        gaps: List[Dict],
        sixr_impact: Dict[str, Any],
        client_requirements: Dict[str, Any],
    ) -> List[Dict]:
        """Prioritize gaps based on SIXR impact and client requirements"""
        # Define priority weights
        severity_weights = {"critical": 1.0, "high": 0.7, "medium": 0.4, "low": 0.1}

        # Calculate priority scores
        for gap in gaps:
            severity = gap.get("severity", "medium")
            sixr_factor = sixr_impact.get("gap_sixr_scores", {}).get(gap.get("id"), 0.5)
            business_impact = gap.get("business_impact", {}).get("score", 0.5)

            # Calculate composite priority score
            priority_score = (
                severity_weights.get(severity, 0.4) * 0.4
                + sixr_factor * 0.4
                + business_impact * 0.2
            )

            gap["priority_score"] = priority_score

        # Sort by priority score (descending)
        prioritized_gaps = sorted(
            gaps, key=lambda g: g.get("priority_score", 0), reverse=True
        )

        return prioritized_gaps

    def _calculate_overall_severity(self, gaps: List[Dict]) -> str:
        """Calculate overall severity based on gap distribution"""
        if not gaps:
            return "none"

        # Count gaps by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for gap in gaps:
            severity = gap.get("severity", "medium")
            if severity in severity_counts:
                severity_counts[severity] += 1

        # Determine overall severity
        if severity_counts["critical"] > 0:
            return "critical"
        elif severity_counts["high"] >= 3:
            return "high"
        elif severity_counts["high"] > 0 or severity_counts["medium"] >= 5:
            return "medium"
        else:
            return "low"
