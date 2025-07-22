"""
Analysis Handler for Agent-UI Communication
Manages agent analysis operations and data processing.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class AnalysisHandler:
    """Handles agent analysis operations and data processing."""
    
    def __init__(self, storage_manager):
        self.storage_manager = storage_manager
    
    async def analyze_with_agents(self, analysis_request: Dict[str, Any]) -> Dict[str, Any]:
        """Process analysis request with agent intelligence."""
        try:
            data_source = analysis_request.get("data_source", "unknown")
            data_content = analysis_request.get("data_content", {})
            analysis_type = analysis_request.get("analysis_type", "general")
            page_context = analysis_request.get("page_context", "discovery")
            
            logger.info(f"Starting agent analysis: {analysis_type} for {data_source}")
            
            # Prepare analysis context
            analysis_context = {
                "data_source": data_source,
                "data_type": data_content.get("type", "unknown"),
                "record_count": len(data_content.get("records", [])),
                "analysis_type": analysis_type,
                "page_context": page_context
            }
            
            # Perform multi-phase analysis
            analysis_result = {
                "analysis_id": f"analysis_{data_source}_{analysis_type}",
                "data_source": data_source,
                "analysis_type": analysis_type,
                "page_context": page_context,
                "insights": [],
                "data_classifications": {},
                "questions": [],
                "confidence_score": 0.0,
                "processing_time": 0,
                "agent_recommendations": []
            }
            
            # Data quality analysis
            quality_analysis = await self._analyze_data_quality_with_agents(analysis_request)
            analysis_result["data_classifications"] = quality_analysis.get("classifications", {})
            analysis_result["insights"].extend(quality_analysis.get("insights", []))
            
            # Data source analysis
            source_analysis = await self._analyze_data_source_with_agents(analysis_request)
            analysis_result["insights"].extend(source_analysis.get("insights", []))
            analysis_result["agent_recommendations"].extend(source_analysis.get("recommendations", []))
            
            # Calculate overall confidence
            insight_confidences = [insight.get("confidence_score", 0.5) for insight in analysis_result["insights"]]
            analysis_result["confidence_score"] = sum(insight_confidences) / len(insight_confidences) if insight_confidences else 0.5
            
            # Store analysis results for learning
            self.storage_manager.store_learning_experience({
                "analysis_type": "agent_analysis",
                "data_source": data_source,
                "analysis_context": analysis_context,
                "confidence_score": analysis_result["confidence_score"],
                "insights_generated": len(analysis_result["insights"]),
                "timestamp": analysis_context.get("timestamp")
            })
            
            logger.info(f"Agent analysis completed: {len(analysis_result['insights'])} insights generated")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in agent analysis: {e}")
            return {
                "analysis_id": "error",
                "error": str(e),
                "insights": [],
                "data_classifications": {},
                "questions": [],
                "confidence_score": 0.0
            }
    
    async def process_with_agents(self, processing_request: Dict[str, Any]) -> Dict[str, Any]:
        """Process data with agent intelligence for cleanup and enhancement."""
        try:
            operation_type = processing_request.get("operation_type", "cleanup")
            data_items = processing_request.get("data_items", [])
            processing_context = processing_request.get("context", {})
            
            logger.info(f"Starting agent processing: {operation_type} for {len(data_items)} items")
            
            processing_result = {
                "operation_type": operation_type,
                "processed_items": [],
                "quality_improvements": [],
                "agent_suggestions": [],
                "processing_summary": {
                    "total_items": len(data_items),
                    "processed_successfully": 0,
                    "quality_improvements_applied": 0,
                    "confidence_score": 0.0
                }
            }
            
            # Process each data item
            for item in data_items:
                processed_item = await self._process_single_item_with_agents(item, operation_type, processing_context)
                processing_result["processed_items"].append(processed_item)
                
                if processed_item.get("quality_improved", False):
                    processing_result["processing_summary"]["quality_improvements_applied"] += 1
                    processing_result["quality_improvements"].append(processed_item.get("improvements", []))
                
                if processed_item.get("processing_successful", False):
                    processing_result["processing_summary"]["processed_successfully"] += 1
            
            # Calculate processing confidence
            item_confidences = [item.get("confidence_score", 0.5) for item in processing_result["processed_items"]]
            processing_result["processing_summary"]["confidence_score"] = sum(item_confidences) / len(item_confidences) if item_confidences else 0.5
            
            logger.info(f"Agent processing completed: {processing_result['processing_summary']['processed_successfully']}/{len(data_items)} items processed")
            return processing_result
            
        except Exception as e:
            logger.error(f"Error in agent processing: {e}")
            return {
                "operation_type": operation_type,
                "error": str(e),
                "processed_items": [],
                "quality_improvements": [],
                "agent_suggestions": []
            }
    
    async def _analyze_data_quality_with_agents(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data quality using agent intelligence."""
        data_content = request.get("data_content", {})
        records = data_content.get("records", [])
        
        quality_analysis = {
            "classifications": {
                "good_data": [],
                "needs_clarification": [],
                "unusable": []
            },
            "insights": []
        }
        
        if not records:
            return quality_analysis
        
        # Analyze sample of records for quality patterns
        sample_size = min(10, len(records))
        sample_records = records[:sample_size]
        
        total_quality_score = 0
        classified_count = 0
        
        for record in sample_records:
            quality_score = self._calculate_basic_quality(record)
            total_quality_score += quality_score
            classified_count += 1
            
            if quality_score >= 0.8:
                quality_analysis["classifications"]["good_data"].append(record)
            elif quality_score >= 0.4:
                quality_analysis["classifications"]["needs_clarification"].append(record)
            else:
                quality_analysis["classifications"]["unusable"].append(record)
        
        # Generate quality insights
        overall_quality = total_quality_score / classified_count if classified_count > 0 else 0.0
        
        quality_analysis["insights"].append({
            "id": f"quality_insight_{request.get('data_source', 'unknown')}",
            "type": "data_quality",
            "title": "Data Quality Assessment",
            "description": f"Overall data quality score: {overall_quality:.1%}. {len(quality_analysis['classifications']['good_data'])} high-quality records, {len(quality_analysis['classifications']['needs_clarification'])} records need clarification.",
            "confidence_score": 0.8,
            "actionable": True,
            "supporting_data": {
                "total_records": len(records),
                "sample_analyzed": sample_size,
                "quality_distribution": {
                    "good": len(quality_analysis["classifications"]["good_data"]),
                    "needs_clarification": len(quality_analysis["classifications"]["needs_clarification"]),
                    "unusable": len(quality_analysis["classifications"]["unusable"])
                }
            }
        })
        
        return quality_analysis
    
    async def _analyze_data_source_with_agents(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data source characteristics using agent intelligence."""
        data_source = request.get("data_source", "unknown")
        data_content = request.get("data_content", {})
        
        source_analysis = {
            "insights": [],
            "recommendations": []
        }
        
        # Analyze data structure and patterns
        records = data_content.get("records", [])
        if records:
            # Field analysis
            field_analysis = self._analyze_field_patterns(records)
            
            source_analysis["insights"].append({
                "id": f"source_insight_{data_source}",
                "type": "data_source",
                "title": "Data Source Analysis",
                "description": f"Analyzed {len(records)} records from {data_source}. Detected {len(field_analysis.get('common_fields', []))} common fields with varying completeness.",
                "confidence_score": 0.7,
                "actionable": True,
                "supporting_data": field_analysis
            })
            
            # Generate recommendations
            if field_analysis.get("incomplete_fields"):
                source_analysis["recommendations"].append({
                    "type": "data_completion",
                    "description": f"Consider data enhancement for incomplete fields: {', '.join(field_analysis['incomplete_fields'][:3])}",
                    "priority": "medium"
                })
        
        return source_analysis
    
    async def _process_single_item_with_agents(self, item: Dict[str, Any], operation_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single data item with agent intelligence."""
        processed_item = {
            "original_item": item,
            "processed_item": item.copy(),
            "processing_successful": True,
            "quality_improved": False,
            "improvements": [],
            "confidence_score": 0.7
        }
        
        # Apply intelligent processing based on operation type
        if operation_type == "cleanup":
            processed_item["processed_item"] = self._standardize_asset_type(processed_item["processed_item"])
            processed_item["processed_item"] = self._normalize_environment(processed_item["processed_item"])
            processed_item["processed_item"] = self._fix_hostname(processed_item["processed_item"])
            processed_item["processed_item"] = self._complete_missing_data(processed_item["processed_item"])
            
            # Check if improvements were made
            if processed_item["processed_item"] != processed_item["original_item"]:
                processed_item["quality_improved"] = True
                processed_item["improvements"] = ["standardization", "normalization", "completion"]
        
        return processed_item
    
    def _calculate_basic_quality(self, asset: Dict[str, Any]) -> float:
        """Calculate basic quality score for an asset."""
        score = 0.0
        total_fields = 0
        
        # Check critical fields
        critical_fields = ["name", "asset_type", "environment"]
        for field in critical_fields:
            total_fields += 1
            if asset.get(field) and str(asset[field]).strip():
                score += 1.0
        
        # Check optional fields
        optional_fields = ["hostname", "ip_address", "department", "location"]
        for field in optional_fields:
            total_fields += 1
            if asset.get(field) and str(asset[field]).strip():
                score += 0.5
        
        return score / total_fields if total_fields > 0 else 0.0
    
    def _standardize_asset_type(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize asset type values."""
        asset_type = asset.get("asset_type", "").lower()
        
        type_mappings = {
            "server": "Server",
            "srv": "Server",
            "database": "Database",
            "db": "Database",
            "application": "Application",
            "app": "Application",
            "network": "Network",
            "storage": "Storage"
        }
        
        standardized_type = type_mappings.get(asset_type, asset.get("asset_type", "Unknown"))
        asset["asset_type"] = standardized_type
        
        return asset
    
    def _normalize_environment(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize environment values."""
        environment = asset.get("environment", "").lower()
        
        env_mappings = {
            "prod": "Production",
            "production": "Production",
            "dev": "Development",
            "development": "Development",
            "test": "Testing",
            "testing": "Testing",
            "stage": "Staging",
            "staging": "Staging"
        }
        
        normalized_env = env_mappings.get(environment, asset.get("environment", "Unknown"))
        asset["environment"] = normalized_env
        
        return asset
    
    def _fix_hostname(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Fix common hostname issues."""
        hostname = asset.get("hostname", "")
        if hostname:
            # Remove common prefixes/suffixes
            hostname = hostname.strip().lower()
            # Add domain if missing for certain patterns
            if "." not in hostname and len(hostname) > 3:
                hostname = f"{hostname}.local"
            asset["hostname"] = hostname
        
        return asset
    
    def _complete_missing_data(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Complete missing data based on patterns."""
        # Infer department from hostname patterns
        hostname = asset.get("hostname", "").lower()
        if not asset.get("department") and hostname:
            if "hr" in hostname:
                asset["department"] = "Human Resources"
            elif "fin" in hostname:
                asset["department"] = "Finance"
            elif "it" in hostname:
                asset["department"] = "IT"
        
        return asset
    
    def _analyze_field_patterns(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze field patterns across records."""
        if not records:
            return {}
        
        all_fields = set()
        field_completeness = {}
        
        for record in records:
            for field in record.keys():
                all_fields.add(field)
                if field not in field_completeness:
                    field_completeness[field] = 0
                if record.get(field) and str(record[field]).strip():
                    field_completeness[field] += 1
        
        total_records = len(records)
        incomplete_fields = []
        
        for field, count in field_completeness.items():
            completeness = count / total_records
            if completeness < 0.8:  # Less than 80% complete
                incomplete_fields.append(field)
        
        return {
            "total_fields": len(all_fields),
            "common_fields": list(all_fields),
            "field_completeness": {k: v/total_records for k, v in field_completeness.items()},
            "incomplete_fields": incomplete_fields
        } 