"""
Asset Update Logic for Recommendation Executor - Issue #999

This module contains the logic to update the assets table with 6R recommendations
after the recommendation generation phase completes.
"""

from typing import Any, Dict

from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.repositories.asset_repository import AssetRepository

logger = get_logger(__name__)


class AssetUpdateMixin:
    """Mixin for updating assets with 6R recommendations from assessment flow"""

    async def _update_assets_with_recommendations(
        self,
        parsed_result: Dict[str, Any],
        assessment_flow_id: str,
        master_flow: CrewAIFlowStateExtensions,
    ) -> int:
        """
        Update assets table with 6R recommendations from parsed agent results.

        ISSUE-999: After recommendation phase completes, persist 6R strategies
        to the assets table so they're available for wave planning and migration execution.

        Args:
            parsed_result: Parsed JSON from recommendation agent containing applications array
            assessment_flow_id: UUID of the assessment flow for tracking
            master_flow: Master flow object containing tenant scoping info

        Returns:
            Total number of assets updated across all applications

        Architecture Notes:
            - Uses AssetRepository with proper tenant scoping
            - Updates assets by application_name (canonical name)
            - Handles partial failures gracefully (logs warnings, continues processing)
            - Validates 6R strategy enum values before update
        """
        total_updated = 0

        try:
            # Extract applications array from results
            applications = parsed_result.get("applications", [])

            if not applications:
                logger.warning(
                    f"[ISSUE-999] ⚠️ No applications found in recommendation results "
                    f"for assessment flow {assessment_flow_id}"
                )
                return 0

            logger.info(
                f"[ISSUE-999] 📝 Processing {len(applications)} application "
                f"recommendations for asset updates"
            )

            # Get database session from execution engine (passed via crew_utils)
            if not hasattr(self, "crew_utils") or not hasattr(self.crew_utils, "db"):
                logger.error(
                    "[ISSUE-999] ❌ Database session not available in execution engine"
                )
                return 0

            db = self.crew_utils.db

            # Initialize asset repository with tenant scoping from master flow
            asset_repo = AssetRepository(
                db=db,
                client_account_id=str(master_flow.client_account_id),
                engagement_id=str(master_flow.engagement_id),
            )

            # Process each application recommendation
            for app in applications:
                try:
                    app_name = app.get("application_name")
                    six_r_strategy = app.get("six_r_strategy")
                    confidence_score = app.get("confidence_score", 0.0)

                    # Validate required fields
                    if not app_name:
                        logger.warning(
                            "[ISSUE-999] ⚠️ Skipping application without name"
                        )
                        continue

                    if not six_r_strategy:
                        logger.warning(
                            f"[ISSUE-999] ⚠️ Skipping application '{app_name}' - "
                            f"no 6R strategy provided"
                        )
                        continue

                    # Update assets matching this application name
                    count = await asset_repo.update_six_r_strategy_from_assessment(
                        application_name=app_name,
                        six_r_strategy=six_r_strategy,
                        confidence_score=confidence_score,
                        assessment_flow_id=assessment_flow_id,
                    )

                    total_updated += count

                except ValueError as e:
                    # Invalid enum value - log and continue
                    logger.error(
                        f"[ISSUE-999] ❌ Invalid 6R strategy for application "
                        f"'{app.get('application_name', 'unknown')}': {e}"
                    )
                    continue

                except Exception as e:
                    # Unexpected error - log and continue
                    logger.error(
                        f"[ISSUE-999] ❌ Failed to update assets for application "
                        f"'{app.get('application_name', 'unknown')}': {e}",
                        exc_info=True,
                    )
                    continue

            # Summary logging
            logger.info(
                f"[ISSUE-999] ✅ Asset update complete: {total_updated} assets updated "
                f"across {len(applications)} applications"
            )

            # Commit the transaction
            await db.commit()

            return total_updated

        except Exception as e:
            logger.error(
                f"[ISSUE-999] ❌ Critical error during asset updates: {e}",
                exc_info=True,
            )
            # Rollback on critical error
            if hasattr(self, "crew_utils") and hasattr(self.crew_utils, "db"):
                try:
                    await self.crew_utils.db.rollback()
                except Exception:
                    pass  # Best effort rollback
            return total_updated  # Return partial count if any updates succeeded
