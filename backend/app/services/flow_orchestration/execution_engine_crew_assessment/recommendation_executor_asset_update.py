"""
Asset Update Logic for Recommendation Executor - Issue #999

This module contains the logic to update the assets table with 6R recommendations
after the recommendation generation phase completes.

ISSUE-999 Phase 3: Uses junction table (collection_flow_applications) for reliable
asset lookup instead of unreliable application_name field matching.
"""

from typing import Any, Dict

from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

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

        ISSUE-999 Phase 3: Uses junction table (collection_flow_applications) for reliable
        asset lookup instead of unreliable application_name field matching.

        Args:
            parsed_result: Parsed JSON from recommendation agent containing applications array
            assessment_flow_id: UUID of the assessment flow for tracking
            master_flow: Master flow object containing tenant scoping info

        Returns:
            Total number of assets updated across all applications
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
                f"[ISSUE-999-PHASE3] 📝 Processing {len(applications)} application "
                f"recommendations using junction table lookup"
            )

            # Get database session from execution engine (passed via crew_utils)
            if not hasattr(self, "crew_utils") or not hasattr(self.crew_utils, "db"):
                logger.error(
                    "[ISSUE-999] ❌ Database session not available in execution engine"
                )
                return 0

            db = self.crew_utils.db

            # Import models
            from app.models.canonical_applications.collection_flow_app import (
                CollectionFlowApplication,
            )
            from app.models.asset import Asset
            from sqlalchemy import and_, update
            from sqlalchemy.future import select

            # Process each application recommendation
            for app in applications:
                try:
                    # Extract data from recommendation
                    canonical_app_id = app.get(
                        "application_id"
                    )  # This is canonical_application_id
                    app_name = app.get("application_name")
                    six_r_strategy = app.get("six_r_strategy")
                    confidence_score = app.get("confidence_score", 0.0)

                    # Validate required fields
                    if not canonical_app_id:
                        logger.warning(
                            f"[ISSUE-999-PHASE3] ⚠️ Skipping application without canonical_app_id: {app_name}"
                        )
                        continue

                    if not six_r_strategy:
                        logger.warning(
                            f"[ISSUE-999-PHASE3] ⚠️ Skipping application '{app_name}' - "
                            f"no 6R strategy provided"
                        )
                        continue

                    # Phase 3: Get asset IDs from junction table (RELIABLE!)
                    result = await db.execute(
                        select(CollectionFlowApplication.asset_id).where(
                            CollectionFlowApplication.canonical_application_id
                            == canonical_app_id,
                            CollectionFlowApplication.client_account_id
                            == str(master_flow.client_account_id),
                            CollectionFlowApplication.engagement_id
                            == str(master_flow.engagement_id),
                        )
                    )
                    asset_rows = result.fetchall()
                    asset_ids = [row[0] for row in asset_rows]

                    if not asset_ids:
                        logger.warning(
                            f"[ISSUE-999-PHASE3] ⚠️ No assets found in junction table for "
                            f"canonical app '{app_name}' (ID: {canonical_app_id})"
                        )
                        continue

                    logger.info(
                        f"[ISSUE-999-PHASE3] 🔍 Found {len(asset_ids)} asset(s) for "
                        f"canonical app '{app_name}' via junction table"
                    )

                    # Update assets by asset_id (RELIABLE!)
                    update_stmt = (
                        update(Asset)
                        .where(
                            and_(
                                Asset.id.in_(asset_ids),
                                Asset.client_account_id
                                == str(master_flow.client_account_id),
                                Asset.engagement_id == str(master_flow.engagement_id),
                            )
                        )
                        .values(
                            **{
                                "six_r_strategy": six_r_strategy.lower(),
                                "confidence_score": confidence_score,
                                "assessment_flow_id": assessment_flow_id,
                                # Backfill application_name only if provided
                                **({"application_name": app_name} if app_name else {}),
                            }
                        )
                    )

                    result = await db.execute(update_stmt)
                    count = result.rowcount
                    total_updated += count

                    logger.info(
                        f"[ISSUE-999-PHASE3] ✅ Updated {count} asset(s) for application "
                        f"'{app_name}' with 6R strategy: {six_r_strategy} "
                        f"(confidence: {confidence_score:.2%})"
                    )

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
                f"[ISSUE-999-PHASE3] ✅ Asset update complete: {total_updated} assets updated "
                f"across {len(applications)} applications using junction table"
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
