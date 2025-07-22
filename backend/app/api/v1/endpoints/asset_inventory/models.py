"""
Pydantic models for Asset Inventory API requests and responses.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class AssetAnalysisRequest(BaseModel):
    asset_ids: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    operation: str = "general_analysis"
    include_patterns: bool = True
    include_quality_assessment: bool = True


class BulkUpdatePlanRequest(BaseModel):
    asset_ids: List[str]
    proposed_updates: Dict[str, Any]
    validation_level: str = "standard"  # standard, strict, minimal
    execution_strategy: Optional[str] = None  # auto, batch, staged


class AssetClassificationRequest(BaseModel):
    asset_ids: List[str]
    use_learned_patterns: bool = True
    confidence_threshold: float = 0.8
    classification_context: Optional[str] = None


class AssetFeedbackRequest(BaseModel):
    operation_type: str
    feedback_text: str
    asset_ids: Optional[List[str]] = None
    corrections: Optional[Dict[str, Any]] = None
    user_context: Optional[str] = None