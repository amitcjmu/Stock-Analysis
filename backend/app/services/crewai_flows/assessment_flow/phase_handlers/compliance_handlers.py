"""
Compliance validation handlers for Assessment Flow.

ADR-039 Enhancement:
- Validates technology compliance against engagement standards
- Persists compliance validation results to phase_results JSONB
- Provides compliance context for downstream phases
"""

import logging
from datetime import datetime
from typing import Any, Dict

from app.core.seed_data.assessment_standards import validate_technology_compliance
from app.models.assessment_flow import AssessmentPhase

logger = logging.getLogger(__name__)


class ComplianceHandlers:
    """Mixin class for architecture compliance validation."""

    async def handle_architecture_minimums(self, previous_result) -> Dict[str, Any]:
        """
        Phase 2: Capture and validate architecture requirements.
        Allow user to review and modify architecture standards.

        ADR-039 Enhancement:
        - Validate each application's technology stack against engagement standards
        - Persist compliance validation to phase_results["architecture_minimums"]
        - Store compliance_validation for downstream consumption by tech debt and 6R phases
        """
        logger.info("📋 Capturing architecture minimums")

        try:
            self.flow.state.transition_to_phase(AssessmentPhase.ARCHITECTURE_MINIMUMS)
            self.flow.state.update_phase_progress(
                AssessmentPhase.ARCHITECTURE_MINIMUMS.value, 10.0
            )

            # Apply any user modifications to architecture standards
            if previous_result and "user_input" in previous_result:
                await self._apply_architecture_modifications(
                    previous_result["user_input"]
                )

            self.flow.state.update_phase_progress(
                AssessmentPhase.ARCHITECTURE_MINIMUMS.value, 25.0
            )

            # Load engagement standards from database for compliance validation
            engagement_standards = await self._load_engagement_standards_from_db()

            # ADR-039: Validate technology compliance for each application
            app_compliance_results = {}
            total_apps = len(self.flow.state.application_components)
            overall_compliant = True

            for i, app in enumerate(self.flow.state.application_components):
                app_id = app.get("application_id", f"app_{i}")
                app_name = app.get("application_name", f"Application {i}")
                tech_stack = app.get("technology_stack", {})

                # Convert list to dict if needed (e.g., ["Java", "Oracle"] -> {"Java": "unknown", ...})
                if isinstance(tech_stack, list):
                    tech_stack = {t: "unknown" for t in tech_stack}

                # Validate technology compliance
                compliance_result = validate_technology_compliance(
                    technology_stack=tech_stack,
                    engagement_standards=engagement_standards,
                )

                app_compliance_results[app_id] = {
                    "application_name": app_name,
                    **compliance_result,
                }

                if not compliance_result.get("compliant", True):
                    overall_compliant = False

                # Update progress
                progress = 25.0 + (50.0 * (i + 1) / max(total_apps, 1))
                self.flow.state.update_phase_progress(
                    AssessmentPhase.ARCHITECTURE_MINIMUMS.value, progress
                )

            # Validate architecture standards completeness (legacy)
            standards_validation = self._validate_architecture_standards()

            # ADR-039: Build architecture_minimums phase result structure
            architecture_minimums_data = {
                "engagement_standards": engagement_standards,
                "compliance_validation": {
                    "overall_compliant": overall_compliant,
                    "applications": app_compliance_results,
                    "total_applications": total_apps,
                    "compliant_applications": sum(
                        1
                        for r in app_compliance_results.values()
                        if r.get("compliant", True)
                    ),
                    "non_compliant_applications": sum(
                        1
                        for r in app_compliance_results.values()
                        if not r.get("compliant", True)
                    ),
                },
                "standards_validation": standards_validation,
                "validated_at": datetime.utcnow().isoformat(),
            }

            # Store in in-memory state for downstream phases
            if "architecture_minimums" not in self.flow.state.metadata:
                self.flow.state.metadata["architecture_minimums"] = {}
            self.flow.state.metadata["architecture_minimums"] = (
                architecture_minimums_data
            )

            self.flow.state.update_phase_progress(
                AssessmentPhase.ARCHITECTURE_MINIMUMS.value, 90.0
            )

            # ADR-039: Persist to database phase_results JSONB
            await self._persist_phase_results_to_database(
                phase="architecture_minimums",
                phase_data=architecture_minimums_data,
            )

            # Final progress update
            self.flow.state.update_phase_progress(
                AssessmentPhase.ARCHITECTURE_MINIMUMS.value, 100.0
            )

            # Save state
            await self.flow.flow_state_manager.save_state(
                self.flow.flow_id, self.flow.state.to_dict()
            )

            logger.info(
                f"✅ Architecture minimums captured - "
                f"{architecture_minimums_data['compliance_validation']['compliant_applications']}/{total_apps} "
                f"applications compliant"
            )

            return {
                "phase": AssessmentPhase.ARCHITECTURE_MINIMUMS.value,
                "standards_count": len(engagement_standards),
                "validation_results": standards_validation,
                "compliance_summary": {
                    "overall_compliant": overall_compliant,
                    "compliant_count": architecture_minimums_data[
                        "compliance_validation"
                    ]["compliant_applications"],
                    "non_compliant_count": architecture_minimums_data[
                        "compliance_validation"
                    ]["non_compliant_applications"],
                },
                "next_phase": AssessmentPhase.TECH_DEBT_ANALYSIS.value,
                "requires_user_input": False,
            }

        except Exception as e:
            logger.error(f"❌ Architecture minimums capture failed: {str(e)}")
            self.flow.state.last_error = str(e)
            await self.flow.flow_state_manager.save_state(
                self.flow.flow_id, self.flow.state.to_dict()
            )
            raise
