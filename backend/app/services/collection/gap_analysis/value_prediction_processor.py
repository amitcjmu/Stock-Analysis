"""
Gap Value Prediction Processor

Handles AI-powered prediction of actual VALUES for data gaps.
This is Phase 3 (Agentic Gap Resolution) triggered by manual button click.
"""

import json
import logging
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection_data_gap import CollectionDataGap
from .value_prediction_task_builder import build_single_asset_value_prediction_task
from .context_filter import build_compact_asset_context
from .data_loader import load_assets

logger = logging.getLogger(__name__)


class GapValuePredictionProcessor:
    """Processes gap value predictions using AI agent."""

    def __init__(self, client_account_id: str, engagement_id: str):
        """Initialize processor.

        Args:
            client_account_id: Client account ID
            engagement_id: Engagement ID
        """
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

    async def predict_gap_values(
        self,
        gaps: List[Dict[str, Any]],
        collection_flow_id: UUID,
        db: AsyncSession,
        execute_agent_task_method,
    ) -> Dict[str, Any]:
        """Predict values for existing gaps using AI.

        Args:
            gaps: List of gap dictionaries from frontend
            collection_flow_id: Collection flow UUID
            db: Database session
            execute_agent_task_method: Bound method for executing agent task

        Returns:
            Dict with predictions and summary
        """
        logger.info(
            f"🔮 Starting value prediction for {len(gaps)} gaps "
            f"(flow: {collection_flow_id})"
        )

        # Extract unique asset IDs from gaps
        asset_ids = list(
            set(gap.get("asset_id") for gap in gaps if gap.get("asset_id"))
        )

        # Load assets for context
        assets = await load_assets(
            asset_ids,
            self.client_account_id,
            self.engagement_id,
            db,
        )

        if not assets:
            logger.warning("No assets found for value prediction")
            return {
                "predictions": [],
                "summary": {"total_predictions": 0, "error": "No assets found"},
            }

        # Group gaps by asset
        gaps_by_asset = {}
        for gap in gaps:
            asset_id = gap.get("asset_id")
            if asset_id not in gaps_by_asset:
                gaps_by_asset[asset_id] = []
            gaps_by_asset[asset_id].append(gap)

        # Process each asset's gaps
        all_predictions = []
        high_conf_count = 0
        medium_conf_count = 0
        low_conf_count = 0

        from app.core.redis_config import get_redis_manager

        redis_manager = get_redis_manager()
        redis_client = redis_manager.client if redis_manager.is_available() else None

        # Get tenant safe keys for context filtering
        from .context_filter import DEFAULT_SAFE_KEYS, get_tenant_safe_keys

        if redis_client:
            try:
                tenant_safe_keys = await get_tenant_safe_keys(
                    self.client_account_id, redis_client
                )
            except Exception:
                tenant_safe_keys = DEFAULT_SAFE_KEYS
        else:
            tenant_safe_keys = DEFAULT_SAFE_KEYS

        for asset in assets:
            asset_id_str = str(asset.id)
            asset_gaps = gaps_by_asset.get(asset_id_str, [])

            if not asset_gaps:
                continue

            logger.info(
                f"🔮 Predicting values for {len(asset_gaps)} gaps "
                f"(asset: {asset.name})"
            )

            # Build filtered asset context
            asset_context = build_compact_asset_context(
                asset, tenant_safe_keys, redis_client
            )

            # Build task for agent
            task_description = build_single_asset_value_prediction_task(
                asset_gaps=asset_gaps,
                asset_context=asset_context,
            )

            # Execute agent task
            try:
                task_output = await execute_agent_task_method(
                    agent=None,  # Agent will be provided by service
                    task_description=task_description,
                )

                # Parse predictions from agent output
                predictions = self._parse_prediction_output(task_output, asset_gaps)

                # Count confidence levels
                for pred in predictions:
                    conf = pred.get("prediction_confidence", 0)
                    if conf >= 0.7:
                        high_conf_count += 1
                    elif conf >= 0.4:
                        medium_conf_count += 1
                    else:
                        low_conf_count += 1

                all_predictions.extend(predictions)

                logger.info(f"✅ Predicted {len(predictions)} values for {asset.name}")

            except Exception as e:
                logger.error(
                    f"❌ Value prediction failed for {asset.name}: {e}",
                    exc_info=True,
                )
                # Continue with other assets

        # Persist predictions to database
        persisted_count = await self._persist_predictions(
            all_predictions, collection_flow_id, db
        )

        return {
            "predictions": all_predictions,
            "summary": {
                "total_predictions": len(all_predictions),
                "predictions_persisted": persisted_count,
                "high_confidence_count": high_conf_count,
                "medium_confidence_count": medium_conf_count,
                "low_confidence_count": low_conf_count,
            },
        }

    def _parse_prediction_output(
        self, task_output: Any, input_gaps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Parse agent output into structured predictions.

        Args:
            task_output: Raw output from agent
            input_gaps: Original gaps for validation

        Returns:
            List of prediction dictionaries
        """
        try:
            # Try to parse as JSON
            if isinstance(task_output, str):
                # Remove markdown code blocks if present
                output_str = task_output.strip()
                if output_str.startswith("```"):
                    # Extract JSON from markdown
                    lines = output_str.split("\n")
                    json_lines = []
                    in_json = False
                    for line in lines:
                        if line.startswith("```"):
                            in_json = not in_json
                            continue
                        if in_json:
                            json_lines.append(line)
                    output_str = "\n".join(json_lines)

                result = json.loads(output_str)
            else:
                result = task_output

            predictions = result.get("predictions", [])

            # Validate predictions match input gaps
            if len(predictions) != len(input_gaps):
                logger.warning(
                    f"Prediction count mismatch: {len(predictions)} vs {len(input_gaps)} input gaps"
                )

            return predictions

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse prediction output as JSON: {e}")
            logger.debug(f"Raw output: {task_output}")
            return []
        except Exception as e:
            logger.error(f"Error parsing prediction output: {e}", exc_info=True)
            return []

    async def _persist_predictions(
        self,
        predictions: List[Dict[str, Any]],
        collection_flow_id: UUID,
        db: AsyncSession,
    ) -> int:
        """Persist predictions to database.

        Args:
            predictions: List of prediction dictionaries
            collection_flow_id: Collection flow UUID
            db: Database session

        Returns:
            Number of predictions persisted
        """
        from sqlalchemy import select

        persisted_count = 0

        for pred in predictions:
            try:
                asset_id = UUID(pred.get("asset_id"))
                field_name = pred.get("field_name")

                # Find the gap in database
                stmt = select(CollectionDataGap).where(
                    CollectionDataGap.collection_flow_id == collection_flow_id,
                    CollectionDataGap.asset_id == asset_id,
                    CollectionDataGap.field_name == field_name,
                )
                result = await db.execute(stmt)
                gap = result.scalar_one_or_none()

                if gap:
                    # Update gap with prediction
                    gap.predicted_value = pred.get("predicted_value")
                    gap.prediction_confidence = pred.get("prediction_confidence")
                    gap.prediction_reasoning = pred.get("prediction_reasoning")
                    persisted_count += 1
                else:
                    logger.warning(
                        f"Gap not found for prediction: asset={asset_id}, field={field_name}"
                    )

            except Exception as e:
                logger.error(f"Failed to persist prediction: {e}", exc_info=True)
                continue

        await db.commit()

        logger.info(f"💾 Persisted {persisted_count} value predictions to database")

        return persisted_count
