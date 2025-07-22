"""
Quality Assessment Handler
Handles quality scoring and assessment operations.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

class QualityAssessmentHandler:
    """Handler for data quality assessment operations."""
    
    def __init__(self, quality_thresholds: Dict[str, float]):
        self.quality_thresholds = quality_thresholds
    
    def is_available(self) -> bool:
        """Check if the handler is available."""
        return True
    
    def assess_cleanup_readiness(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess readiness for data cleanup phase."""
        if not assets:
            return {
                "overall_readiness": 0.0,
                "ready_for_cleanup": False,
                "total_assets": 0,
                "quality_summary": "No assets to assess"
            }
        
        total_assets = len(assets)
        quality_scores = [self.calculate_data_quality(asset) for asset in assets[:100]]
        average_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Count assets by quality level
        excellent = len([q for q in quality_scores if q >= self.quality_thresholds["excellent"]])
        good = len([q for q in quality_scores if q >= self.quality_thresholds["good"]])
        acceptable = len([q for q in quality_scores if q >= self.quality_thresholds["acceptable"]])
        
        readiness_score = average_quality / 100.0
        ready_for_cleanup = readiness_score >= 0.6  # 60% threshold
        
        return {
            "overall_readiness": readiness_score,
            "ready_for_cleanup": ready_for_cleanup,
            "total_assets": total_assets,
            "assets_analyzed": len(quality_scores),
            "average_quality": average_quality,
            "quality_distribution": {
                "excellent": excellent,
                "good": good,
                "acceptable": acceptable,
                "needs_work": len(quality_scores) - acceptable
            },
            "quality_summary": f"Average quality: {average_quality:.1f}% across {len(quality_scores)} assets"
        }
    
    def calculate_data_quality(self, asset: Dict[str, Any]) -> float:
        """Calculate data quality score for a single asset."""
        score = 0.0
        max_score = 100.0
        
        # Essential fields (40 points)
        essential_fields = ['asset_name', 'hostname', 'asset_type', 'environment']
        for field in essential_fields:
            if asset.get(field) and str(asset[field]).strip():
                score += 10.0
        
        # Important fields (30 points)
        important_fields = ['operating_system', 'ip_address', 'business_criticality']
        for field in important_fields:
            if asset.get(field) and str(asset[field]).strip():
                score += 10.0
        
        # Optional fields (30 points)
        optional_fields = ['department', 'owner', 'cost_center', 'location']
        for field in optional_fields:
            if asset.get(field) and str(asset[field]).strip():
                score += 7.5
        
        return min(score, max_score) 