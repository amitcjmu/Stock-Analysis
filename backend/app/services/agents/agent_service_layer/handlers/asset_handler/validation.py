"""
Asset validation operations for data quality and consistency checking.
"""

import logging
from typing import Any, Dict

from sqlalchemy import and_, select

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.models.asset import Asset

logger = logging.getLogger(__name__)


class AssetValidation:
    """Handles asset validation operations."""

    def __init__(self, context: RequestContext):
        self.context = context

    async def validate_asset_data(self, asset_id: str) -> Dict[str, Any]:
        """Validate asset data quality"""
        async with AsyncSessionLocal() as db:
            try:
                # Get asset
                asset_query = select(Asset).where(
                    and_(
                        Asset.id == asset_id,
                        Asset.client_account_id == self.context.client_account_id,
                    )
                )
                result = await db.execute(asset_query)
                asset = result.scalar_one_or_none()

                if not asset:
                    return {
                        "status": "error",
                        "error": "Asset not found",
                        "is_valid": False,
                    }

                # Validate asset data
                validation_results = {
                    "required_fields": self._validate_required_fields(asset),
                    "data_quality": self._validate_data_quality(asset),
                    "consistency": self._validate_data_consistency(asset),
                }

                # Calculate overall validity
                field_validity = validation_results["required_fields"]["is_valid"]
                quality_validity = validation_results["data_quality"]["score"] >= 0.7
                consistency_validity = validation_results["consistency"][
                    "is_consistent"
                ]

                overall_valid = (
                    field_validity and quality_validity and consistency_validity
                )

                # Generate recommendations
                recommendations = []
                if not field_validity:
                    recommendations.extend(
                        validation_results["required_fields"]["recommendations"]
                    )
                if not quality_validity:
                    recommendations.extend(
                        validation_results["data_quality"]["recommendations"]
                    )
                if not consistency_validity:
                    recommendations.extend(
                        validation_results["consistency"]["recommendations"]
                    )

                return {
                    "status": "success",
                    "asset_id": asset_id,
                    "asset_name": asset.name,
                    "is_valid": overall_valid,
                    "validation_results": validation_results,
                    "recommendations": recommendations,
                    "validation_score": self._calculate_validation_score(
                        validation_results
                    ),
                }

            except Exception as e:
                logger.error(f"Database error in validate_asset_data: {e}")
                raise

    def _validate_required_fields(self, asset: Asset) -> Dict[str, Any]:
        """Validate required fields for an asset"""
        required_fields = ["name", "asset_type"]
        missing_fields = []

        for field in required_fields:
            if not getattr(asset, field, None):
                missing_fields.append(field)

        return {
            "is_valid": len(missing_fields) == 0,
            "missing_fields": missing_fields,
            "recommendations": [
                f"Provide value for {field}" for field in missing_fields
            ],
        }

    def _validate_data_quality(self, asset: Asset) -> Dict[str, Any]:
        """Validate data quality for an asset"""
        quality_score = getattr(asset, "quality_score", 0.0)
        confidence_score = getattr(asset, "confidence_score", 0.0)

        recommendations = []
        if quality_score < 0.7:
            recommendations.append(
                "Improve data quality through validation and cleansing"
            )
        if confidence_score < 0.7:
            recommendations.append(
                "Increase confidence through additional data verification"
            )

        return {
            "score": max(quality_score, confidence_score),
            "quality_score": quality_score,
            "confidence_score": confidence_score,
            "recommendations": recommendations,
        }

    def _validate_data_consistency(self, asset: Asset) -> Dict[str, Any]:
        """Validate data consistency for an asset"""
        # Simple consistency checks
        is_consistent = True
        issues = []

        # Check name consistency
        if asset.name and len(asset.name.strip()) == 0:
            is_consistent = False
            issues.append("Asset name is empty or whitespace only")

        # Check type consistency
        if not asset.asset_type:
            is_consistent = False
            issues.append("Asset type is not specified")

        return {
            "is_consistent": is_consistent,
            "consistency_issues": issues,
            "recommendations": ["Fix " + issue.lower() for issue in issues],
        }

    def _calculate_validation_score(self, validation_results: Dict[str, Any]) -> float:
        """Calculate overall validation score"""
        field_score = 1.0 if validation_results["required_fields"]["is_valid"] else 0.0
        quality_score = validation_results["data_quality"]["score"]
        consistency_score = (
            1.0 if validation_results["consistency"]["is_consistent"] else 0.0
        )

        return round((field_score + quality_score + consistency_score) / 3, 2)
