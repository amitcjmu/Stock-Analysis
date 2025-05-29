"""
Testing and Debugging Endpoints.
Provides endpoints for testing and validating discovery functionality.
"""

import logging
from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException

from app.api.v1.discovery.persistence import get_processed_assets
from app.api.v1.discovery.serialization import clean_for_json_serialization

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/test-field-mapping")
async def test_field_mapping():
    """
    Test and validate field mapping logic.
    """
    try:
        # Sample test data for field mapping validation
        test_data = {
            "hostname_variations": ["host", "server_name", "machine_name", "system_name"],
            "asset_type_variations": ["type", "category", "classification", "asset_category"],
            "environment_variations": ["env", "stage", "tier", "deployment_environment"],
            "department_variations": ["dept", "business_unit", "organization", "team"]
        }
        
        # Test mapping results
        mapping_results = {
            "hostname_mapping": _test_field_mapping("hostname", test_data["hostname_variations"]),
            "asset_type_mapping": _test_field_mapping("asset_type", test_data["asset_type_variations"]),
            "environment_mapping": _test_field_mapping("environment", test_data["environment_variations"]),
            "department_mapping": _test_field_mapping("department", test_data["department_variations"])
        }
        
        return {
            "status": "success",
            "test_data": test_data,
            "mapping_results": mapping_results,
            "summary": {
                "total_variations_tested": sum(len(variations) for variations in test_data.values()),
                "successful_mappings": sum(1 for result in mapping_results.values() if result["success"]),
                "field_coverage": f"{len([r for r in mapping_results.values() if r['success']])}/{len(mapping_results)}"
            }
        }
        
    except Exception as e:
        logger.error(f"Field mapping test error: {e}")
        raise HTTPException(status_code=500, detail=f"Field mapping test failed: {str(e)}")

@router.post("/test-asset-classification")
async def test_asset_classification(test_data: Dict[str, Any]):
    """
    Test asset classification algorithms.
    """
    try:
        # Extract test parameters
        sample_assets = test_data.get("assets", [])
        classification_rules = test_data.get("rules", {})
        
        if not sample_assets:
            raise HTTPException(status_code=400, detail="No test assets provided")
        
        # Perform classification testing
        results = []
        
        for asset in sample_assets:
            classification_result = _classify_asset_for_testing(asset, classification_rules)
            results.append({
                "original_asset": asset,
                "classification": classification_result,
                "confidence": _calculate_classification_confidence(asset, classification_result)
            })
        
        # Generate summary statistics
        summary = _generate_classification_summary(results)
        
        return {
            "status": "success",
            "test_results": results,
            "summary": summary,
            "recommendations": _generate_classification_recommendations(results)
        }
        
    except Exception as e:
        logger.error(f"Asset classification test error: {e}")
        raise HTTPException(status_code=500, detail=f"Asset classification test failed: {str(e)}")

@router.get("/test-json-parsing")
async def test_json_parsing_improvements():
    """
    Test JSON parsing and serialization improvements.
    """
    try:
        # Get sample assets for testing
        sample_assets = get_processed_assets()[:5] if get_processed_assets() else []
        
        # Test serialization
        serialization_results = []
        
        for asset in sample_assets:
            try:
                cleaned_asset = clean_for_json_serialization(asset)
                serialization_results.append({
                    "asset_id": asset.get("id", "unknown"),
                    "original_keys": len(asset.keys()) if isinstance(asset, dict) else 0,
                    "cleaned_keys": len(cleaned_asset.keys()) if isinstance(cleaned_asset, dict) else 0,
                    "status": "success",
                    "data_types_processed": _analyze_data_types(asset)
                })
            except Exception as e:
                serialization_results.append({
                    "asset_id": asset.get("id", "unknown"),
                    "status": "failed",
                    "error": str(e)
                })
        
        # Generate test summary
        successful_tests = len([r for r in serialization_results if r["status"] == "success"])
        total_tests = len(serialization_results)
        
        return {
            "status": "success",
            "serialization_tests": serialization_results,
            "summary": {
                "total_assets_tested": total_tests,
                "successful_serializations": successful_tests,
                "success_rate": f"{successful_tests}/{total_tests}" if total_tests > 0 else "0/0",
                "common_data_types": _get_common_data_types(serialization_results)
            }
        }
        
    except Exception as e:
        logger.error(f"JSON parsing test error: {e}")
        raise HTTPException(status_code=500, detail=f"JSON parsing test failed: {str(e)}")

@router.get("/ai-parsing-analytics")
async def get_ai_parsing_analytics():
    """
    Get analytics on AI parsing performance and accuracy.
    """
    try:
        # Get processed assets for analysis
        all_assets = get_processed_assets()
        
        if not all_assets:
            return {
                "status": "success",
                "message": "No assets available for analysis",
                "analytics": {
                    "total_assets": 0,
                    "parsing_accuracy": 0,
                    "field_completeness": {},
                    "data_quality_score": 0
                }
            }
        
        # Analyze parsing performance
        analytics = {
            "total_assets": len(all_assets),
            "parsing_accuracy": _calculate_parsing_accuracy(all_assets),
            "field_completeness": _analyze_field_completeness(all_assets),
            "data_quality_score": _calculate_data_quality_score(all_assets),
            "asset_type_distribution": _analyze_asset_type_distribution(all_assets),
            "parsing_errors": _identify_parsing_errors(all_assets),
            "improvement_suggestions": _generate_improvement_suggestions(all_assets)
        }
        
        return {
            "status": "success",
            "analytics": analytics,
            "summary": {
                "overall_health": "Good" if analytics["data_quality_score"] > 80 else "Needs Improvement",
                "key_insights": _generate_key_insights(analytics)
            }
        }
        
    except Exception as e:
        logger.error(f"AI parsing analytics error: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics generation failed: {str(e)}")

# Helper functions
def _test_field_mapping(field_name: str, variations: List[str]) -> Dict[str, Any]:
    """Test field mapping for a specific field."""
    try:
        # Simulate field mapping test
        successful_mappings = []
        failed_mappings = []
        
        for variation in variations:
            # Simple test - in real implementation this would test actual mapping logic
            if variation.lower() in field_name.lower() or field_name.lower() in variation.lower():
                successful_mappings.append(variation)
            else:
                failed_mappings.append(variation)
        
        return {
            "success": len(successful_mappings) > 0,
            "successful_mappings": successful_mappings,
            "failed_mappings": failed_mappings,
            "accuracy": len(successful_mappings) / len(variations) if variations else 0
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "accuracy": 0
        }

def _classify_asset_for_testing(asset: Dict[str, Any], rules: Dict[str, Any]) -> Dict[str, Any]:
    """Classify an asset for testing purposes."""
    asset_type = asset.get("asset_type", "").lower()
    hostname = asset.get("hostname", "").lower()
    
    # Simple classification logic
    if "server" in asset_type or "host" in hostname:
        return {"type": "Server", "category": "Infrastructure"}
    elif "app" in asset_type or "application" in asset_type:
        return {"type": "Application", "category": "Software"}
    elif "db" in asset_type or "database" in asset_type:
        return {"type": "Database", "category": "Data"}
    else:
        return {"type": "Unknown", "category": "Other"}

def _calculate_classification_confidence(asset: Dict[str, Any], classification: Dict[str, Any]) -> float:
    """Calculate confidence score for classification."""
    # Simple confidence calculation based on available data
    confidence = 0.5  # Base confidence
    
    if asset.get("asset_type"):
        confidence += 0.2
    if asset.get("hostname"):
        confidence += 0.1
    if asset.get("application_name"):
        confidence += 0.1
    if asset.get("department"):
        confidence += 0.1
    
    return min(confidence, 1.0)

def _generate_classification_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate summary for classification results."""
    if not results:
        return {}
    
    type_counts = {}
    total_confidence = 0
    
    for result in results:
        classification_type = result["classification"]["type"]
        type_counts[classification_type] = type_counts.get(classification_type, 0) + 1
        total_confidence += result["confidence"]
    
    return {
        "total_assets": len(results),
        "average_confidence": total_confidence / len(results),
        "type_distribution": type_counts,
        "high_confidence_assets": len([r for r in results if r["confidence"] > 0.8])
    }

def _generate_classification_recommendations(results: List[Dict[str, Any]]) -> List[str]:
    """Generate recommendations for improving classification."""
    recommendations = []
    
    low_confidence_count = len([r for r in results if r["confidence"] < 0.6])
    if low_confidence_count > 0:
        recommendations.append(f"Review {low_confidence_count} assets with low confidence scores")
    
    unknown_count = len([r for r in results if r["classification"]["type"] == "Unknown"])
    if unknown_count > 0:
        recommendations.append(f"Improve classification rules for {unknown_count} unclassified assets")
    
    return recommendations

def _analyze_data_types(asset: Dict[str, Any]) -> Dict[str, int]:
    """Analyze data types in an asset."""
    type_counts = {}
    
    for value in asset.values():
        data_type = type(value).__name__
        type_counts[data_type] = type_counts.get(data_type, 0) + 1
    
    return type_counts

def _get_common_data_types(results: List[Dict[str, Any]]) -> Dict[str, int]:
    """Get common data types across all results."""
    type_counts = {}
    
    for result in results:
        if result["status"] == "success" and "data_types_processed" in result:
            for data_type, count in result["data_types_processed"].items():
                type_counts[data_type] = type_counts.get(data_type, 0) + count
    
    return type_counts

def _calculate_parsing_accuracy(assets: List[Dict[str, Any]]) -> float:
    """Calculate overall parsing accuracy."""
    if not assets:
        return 0.0
    
    # Simple accuracy calculation based on completeness
    total_fields = 0
    populated_fields = 0
    
    for asset in assets:
        for value in asset.values():
            total_fields += 1
            if value is not None and value != "" and value != "Unknown":
                populated_fields += 1
    
    return (populated_fields / total_fields * 100) if total_fields > 0 else 0

def _analyze_field_completeness(assets: List[Dict[str, Any]]) -> Dict[str, float]:
    """Analyze completeness of each field across all assets."""
    if not assets:
        return {}
    
    field_completeness = {}
    total_assets = len(assets)
    
    # Get all unique fields
    all_fields = set()
    for asset in assets:
        all_fields.update(asset.keys())
    
    # Calculate completeness for each field
    for field in all_fields:
        populated_count = 0
        for asset in assets:
            value = asset.get(field)
            if value is not None and value != "" and value != "Unknown":
                populated_count += 1
        
        field_completeness[field] = (populated_count / total_assets * 100) if total_assets > 0 else 0
    
    return field_completeness

def _calculate_data_quality_score(assets: List[Dict[str, Any]]) -> float:
    """Calculate overall data quality score."""
    if not assets:
        return 0.0
    
    # Combine various quality metrics
    parsing_accuracy = _calculate_parsing_accuracy(assets)
    field_completeness = _analyze_field_completeness(assets)
    
    # Average completeness of important fields
    important_fields = ["hostname", "asset_type", "environment", "department"]
    important_completeness = []
    
    for field in important_fields:
        if field in field_completeness:
            important_completeness.append(field_completeness[field])
    
    avg_important_completeness = sum(important_completeness) / len(important_completeness) if important_completeness else 0
    
    # Weighted score
    quality_score = (parsing_accuracy * 0.4) + (avg_important_completeness * 0.6)
    
    return round(quality_score, 2)

def _analyze_asset_type_distribution(assets: List[Dict[str, Any]]) -> Dict[str, int]:
    """Analyze distribution of asset types."""
    type_distribution = {}
    
    for asset in assets:
        asset_type = asset.get("asset_type", "Unknown")
        type_distribution[asset_type] = type_distribution.get(asset_type, 0) + 1
    
    return type_distribution

def _identify_parsing_errors(assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Identify potential parsing errors."""
    errors = []
    
    for asset in assets:
        asset_id = asset.get("id", "unknown")
        
        # Check for missing critical fields
        if not asset.get("hostname"):
            errors.append({
                "asset_id": asset_id,
                "error_type": "missing_hostname",
                "severity": "high"
            })
        
        # Check for invalid asset types
        asset_type = asset.get("asset_type", "").lower()
        if asset_type in ["unknown", "", None]:
            errors.append({
                "asset_id": asset_id,
                "error_type": "unknown_asset_type",
                "severity": "medium"
            })
    
    return errors

def _generate_improvement_suggestions(assets: List[Dict[str, Any]]) -> List[str]:
    """Generate suggestions for improving parsing."""
    suggestions = []
    
    field_completeness = _analyze_field_completeness(assets)
    
    # Suggest improvements for low completeness fields
    for field, completeness in field_completeness.items():
        if completeness < 50:
            suggestions.append(f"Improve data collection for '{field}' field ({completeness:.1f}% complete)")
    
    # Check for consistency issues
    asset_types = set(asset.get("asset_type", "") for asset in assets)
    if len(asset_types) > 20:  # Too many asset types might indicate inconsistency
        suggestions.append("Standardize asset type classifications - too many unique types detected")
    
    return suggestions

def _generate_key_insights(analytics: Dict[str, Any]) -> List[str]:
    """Generate key insights from analytics."""
    insights = []
    
    total_assets = analytics.get("total_assets", 0)
    quality_score = analytics.get("data_quality_score", 0)
    
    insights.append(f"Analyzed {total_assets} assets with {quality_score}% data quality score")
    
    # Field completeness insights
    field_completeness = analytics.get("field_completeness", {})
    if field_completeness:
        best_field = max(field_completeness.items(), key=lambda x: x[1])
        worst_field = min(field_completeness.items(), key=lambda x: x[1])
        
        insights.append(f"Best populated field: {best_field[0]} ({best_field[1]:.1f}%)")
        insights.append(f"Needs attention: {worst_field[0]} ({worst_field[1]:.1f}%)")
    
    return insights 