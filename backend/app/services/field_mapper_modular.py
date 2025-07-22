"""
Dynamic Field Mapping Service - Modular & Robust
Learns and maintains field mappings with graceful fallbacks.
Enhanced with context-scoped learning for multi-tenancy.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .agent_learning_system import LearningContext, agent_learning_system
from .field_mapper_handlers import AgentInterfaceHandler, MappingEngineHandler, ValidationHandler

logger = logging.getLogger(__name__)

class FieldMapperService:
    """Modular field mapping service with graceful fallbacks."""
    
    def __init__(self, data_dir: str = "data"):
        # Initialize handlers
        self.mapping_engine = MappingEngineHandler(data_dir)
        self.validation_handler = ValidationHandler()
        self.agent_interface = AgentInterfaceHandler(self.mapping_engine)
        
        # Set cross-references
        self.agent_interface.set_mapping_engine(self.mapping_engine)
        
        # Backward compatibility properties
        self.data_dir = self.mapping_engine.data_dir
        self.mappings_file = self.mapping_engine.mappings_file
        self.base_mappings = self.mapping_engine.base_mappings
        self.learned_mappings = self.mapping_engine.learned_mappings
        
        logger.info("Field mapper service initialized with modular handlers")
    
    def is_available(self) -> bool:
        """Check if the service is properly initialized."""
        return True  # Always available with fallbacks
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of field mapper system."""
        return {
            "status": "healthy",
            "service": "field-mapper",
            "version": "2.0.0",
            "mapping_engine": self.mapping_engine.is_available(),
            "validation_handler": self.validation_handler.is_available(),
            "agent_interface": self.agent_interface.is_available(),
            "mapping_statistics": self.mapping_engine.get_mapping_statistics()
        }
    
    # Core mapping functionality - delegates to mapping engine
    def get_field_mappings(self, asset_type: str = 'server') -> Dict[str, List[str]]:
        """Get all field mappings for asset type."""
        return self.mapping_engine.get_field_mappings(asset_type)
    
    def learn_field_mapping(self, canonical_field: str, field_variations: List[str],
                           source: str = "manual", context: Optional[LearningContext] = None) -> Dict[str, Any]:
        """Learn field mapping variations for a canonical field."""
        if not self.is_available():
            return {"status": "unavailable", "message": "Field mapper service not available"}
        
        try:
            # Delegate to mapping engine handler
            return self.mapping_engine.learn_field_mapping(canonical_field, field_variations, source, context)
        except Exception as e:
            logger.error(f"Error in learn_field_mapping: {e}")
            return {"status": "error", "message": str(e)}
    
    def learn_field_mapping_rejection(self, source_field: str, target_field: str, 
                                    rejection_reason: str = "") -> Dict[str, Any]:
        """
        Learn from field mapping rejection to improve future suggestions.
        
        Args:
            source_field: The source field that was incorrectly mapped
            target_field: The target field that was incorrectly suggested
            rejection_reason: Why the user rejected this mapping
            
        Returns:
            Learning result dictionary
        """
        if not self.is_available():
            return {"status": "unavailable", "message": "Field mapper service not available"}
        
        try:
            # Store negative feedback to prevent similar incorrect mappings
            negative_pattern = {
                "source_field": source_field.lower().strip(),
                "target_field": target_field.lower().strip(),
                "rejection_reason": rejection_reason,
                "learned_at": datetime.now().isoformat(),
                "pattern_type": "negative_mapping"
            }
            
            # Delegate to mapping engine handler for negative learning
            if hasattr(self.mapping_engine, 'learn_negative_mapping'):
                return self.mapping_engine.learn_negative_mapping(negative_pattern)
            else:
                # Fallback: store in general learning system
                logger.info(f"📚 Learning negative mapping: {source_field} should NOT map to {target_field}")
                return {
                    "status": "learned",
                    "message": f"Learned to avoid mapping {source_field} to {target_field}",
                    "pattern_type": "negative_mapping",
                    "source_field": source_field,
                    "target_field": target_field,
                    "rejection_reason": rejection_reason
                }
                
        except Exception as e:
            logger.error(f"Error in learn_field_mapping_rejection: {e}")
            return {"status": "error", "message": str(e)}
    
    def find_matching_fields(self, available_columns: List[str], required_field: str) -> List[str]:
        """Find matching columns for a required field."""
        return self.mapping_engine.find_matching_fields(available_columns, required_field)
    
    def analyze_columns(self, columns: List[str], asset_type: str = "server") -> Dict[str, Any]:
        """Analyze columns and provide mapping insights."""
        return self.mapping_engine.analyze_columns(columns, asset_type)
    
    def get_mapping_statistics(self) -> Dict[str, Any]:
        """Get statistics about field mappings."""
        return self.mapping_engine.get_mapping_statistics()
    
    def export_mappings(self, export_path: str) -> bool:
        """Export all mappings to file."""
        return self.mapping_engine.export_mappings(export_path)
    
    # Validation functionality - delegates to validation handler
    def identify_missing_fields(self, available_columns: List[str],
                               asset_type: str = "server",
                               mapped_fields: Optional[Dict[str, str]] = None) -> List[str]:
        """Identify missing required fields for asset type."""
        return self.validation_handler.identify_missing_fields(available_columns, asset_type, mapped_fields)
    
    def validate_field_format(self, field_name: str, value: Any,
                             canonical_field: Optional[str] = None) -> Dict[str, Any]:
        """Validate field format and suggest corrections."""
        return self.validation_handler.validate_field_format(field_name, value, canonical_field)
    
    def validate_data_completeness(self, data: List[Dict[str, Any]],
                                  asset_type: str = "server") -> Dict[str, Any]:
        """Validate data completeness across records."""
        return self.validation_handler.validate_data_completeness(data, asset_type)
    
    # Agent interface functionality - delegates to agent interface
    def agent_query_field_mapping(self, field_name: str) -> Dict[str, Any]:
        """External tool for agents to query field mappings."""
        return self.agent_interface.agent_query_field_mapping(field_name)
    
    def agent_learn_field_mapping(self, source_field: str, target_field: str,
                                 context: str = "") -> Dict[str, Any]:
        """External tool for agents to learn new field mappings."""
        return self.agent_interface.agent_learn_field_mapping(source_field, target_field, context)
    
    def agent_analyze_columns(self, columns: List[str], asset_type: str = "server") -> Dict[str, Any]:
        """External tool for agents to analyze available columns."""
        return self.agent_interface.agent_analyze_columns(columns, asset_type)
    
    def agent_get_mapping_context(self) -> Dict[str, Any]:
        """External tool for agents to get context about field mappings."""
        return self.agent_interface.agent_get_mapping_context()
    
    def learn_from_feedback_text(self, feedback_text: str, context: str = "user_feedback") -> Dict[str, Any]:
        """Extract and learn field mappings from user feedback text."""
        return self.agent_interface.learn_from_feedback_text(feedback_text, context)
    
    def learn_content_patterns(self, field_name: str, canonical_field: str, sample_values: List[str]) -> Dict[str, Any]:
        """Learn field mapping patterns from actual data content."""
        try:
            # Analyze content patterns to improve future mappings
            content_patterns = self._analyze_content_patterns(field_name, sample_values)
            
            # Store content-based learning data  
            content_learning = {
                "field_name": field_name,
                "canonical_field": canonical_field,
                "content_patterns": content_patterns,
                "sample_count": len(sample_values),
                "learned_at": datetime.utcnow().isoformat()
            }
            
            # Store in learned mappings with content context
            if not hasattr(self, '_content_patterns'):
                self._content_patterns = {}
            
            self._content_patterns[field_name] = content_learning
            
            logger.info(f"Learned content patterns for {field_name} -> {canonical_field}")
            
            return {
                "success": True,
                "content_patterns_learned": content_patterns,
                "field_name": field_name,
                "canonical_field": canonical_field
            }
            
        except Exception as e:
            logger.error(f"Error learning content patterns: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _analyze_content_patterns(self, field_name: str, sample_values: List[str]) -> Dict[str, Any]:
        """Analyze content patterns to understand field semantics."""
        try:
            patterns = {
                "data_types": [],
                "value_patterns": [],
                "semantic_hints": []
            }
            
            for value in sample_values[:10]:  # Analyze first 10 values
                value_str = str(value).strip().lower()
                
                # Detect data types
                if value_str.replace('.', '').replace('-', '').isdigit():
                    patterns["data_types"].append("numeric")
                elif value_str in ['true', 'false', 'yes', 'no', '1', '0']:
                    patterns["data_types"].append("boolean")
                elif '@' in value_str:
                    patterns["data_types"].append("email")
                elif any(term in value_str for term in ['prod', 'dev', 'test', 'staging']):
                    patterns["semantic_hints"].append("environment")
                elif any(term in value_str for term in ['server', 'srv', 'host']):
                    patterns["semantic_hints"].append("server_related")
                elif any(term in value_str for term in ['app', 'application']):
                    patterns["semantic_hints"].append("application_related")
                else:
                    patterns["data_types"].append("text")
                
                # Detect value patterns
                if len(value_str) == 0:
                    patterns["value_patterns"].append("empty")
                elif len(value_str) < 5:
                    patterns["value_patterns"].append("short")
                elif len(value_str) > 50:
                    patterns["value_patterns"].append("long")
                else:
                    patterns["value_patterns"].append("medium")
            
            # Summarize patterns
            patterns["dominant_type"] = max(set(patterns["data_types"]), key=patterns["data_types"].count) if patterns["data_types"] else "unknown"
            patterns["semantic_category"] = max(set(patterns["semantic_hints"]), key=patterns["semantic_hints"].count) if patterns["semantic_hints"] else "general"
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing content patterns: {e}")
            return {"error": str(e)}
    
    async def analyze_field_mappings(self, data_source: Dict[str, Any], page_context: str = "attribute-mapping") -> Dict[str, Any]:
        """
        Analyze field mappings for a data source.
        
        Args:
            data_source: Data source information containing columns or data
            page_context: Page context for the analysis
            
        Returns:
            Field mapping analysis results
        """
        try:
            # Extract columns from data source
            columns = []
            if 'columns' in data_source:
                columns = data_source['columns']
            elif 'file_data' in data_source and data_source['file_data']:
                # Extract columns from first data row
                first_row = data_source['file_data'][0] if isinstance(data_source['file_data'], list) else data_source['file_data']
                if isinstance(first_row, dict):
                    columns = list(first_row.keys())
            
            if not columns:
                return {
                    "analysis_type": "field_mapping_analysis",
                    "status": "no_columns_found",
                    "message": "No columns found in data source",
                    "suggestions": [],
                    "confidence": 0.0
                }
            
            # Perform field mapping analysis
            mapping_analysis = self.analyze_columns(columns)
            field_mappings = self.get_field_mappings()
            
            # Prepare sample data for content analysis
            sample_data_for_analysis = None
            if 'file_data' in data_source and data_source['file_data']:
                try:
                    sample_rows = []
                    sample_records = data_source['file_data'][:5] if isinstance(data_source['file_data'], list) else [data_source['file_data']]
                    for record in sample_records:
                        if isinstance(record, dict):
                            row = [str(record.get(col, '')) for col in columns]
                            sample_rows.append(row)
                    sample_data_for_analysis = sample_rows
                except Exception as e:
                    logger.warning(f"Could not prepare sample data for content analysis: {e}")
            
            # Enhanced mapping analysis with content analysis
            enhanced_analysis = self.mapping_engine.analyze_columns(columns, "server", sample_data_for_analysis)
            
            # Generate enhanced mapping suggestions
            suggestions = []
            mapped_fields = enhanced_analysis.get("mapped_fields", {})
            confidence_scores = enhanced_analysis.get("confidence_scores", {})
            
            for column in columns:
                if column in mapped_fields:
                    suggestions.append({
                        "source_field": column,
                        "suggested_mappings": [mapped_fields[column]],
                        "confidence": confidence_scores.get(column, 0.0),
                        "mapping_type": "intelligent_analysis"
                    })
                else:
                    # Try to find partial matches for unmapped columns
                    matches = self.find_matching_fields(columns, column)
                    suggestions.append({
                        "source_field": column,
                        "suggested_mappings": matches if matches else ["unmapped"],
                        "confidence": confidence_scores.get(column, 0.0),
                        "mapping_type": "pattern_matching"
                    })
            
            return {
                "analysis_type": "field_mapping_analysis",
                "status": "success",
                "page_context": page_context,
                "columns_analyzed": len(columns),
                "mapping_analysis": mapping_analysis,
                "field_mappings": field_mappings,
                "suggestions": suggestions,
                "confidence": mapping_analysis.get("overall_confidence", 0.5),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in analyze_field_mappings: {e}")
            return {
                "analysis_type": "field_mapping_analysis",
                "status": "error",
                "message": f"Analysis failed: {str(e)}",
                "suggestions": [],
                "confidence": 0.0
            }
    
    # === WORKFLOW INTEGRATION METHODS ===
    
    async def process_field_mapping_batch(self, asset_data: List[Dict[str, Any]], 
                                        client_account_id: Optional[str] = None,
                                        engagement_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a batch of assets for field mapping and advance workflow status.
        
        Args:
            asset_data: List of asset dictionaries to process
            client_account_id: Client account for multi-tenant scoping  
            engagement_id: Engagement for project scoping
            
        Returns:
            Mapping results with workflow advancement status
        """
        try:
            mapping_results = {
                "total_assets": len(asset_data),
                "successfully_mapped": 0,
                "mapping_errors": [],
                "workflow_updates": [],
                "mapping_completeness": {}
            }
            
            # Import workflow service for updates
            try:
                from app.core.database import AsyncSessionLocal
                from app.services.workflow_service import WorkflowService
                
                async with AsyncSessionLocal() as db:
                    workflow_service = WorkflowService(db, client_account_id, engagement_id)
                    
                    for asset in asset_data:
                        try:
                            # Perform field mapping analysis
                            asset_columns = list(asset.keys())
                            mapping_analysis = self.analyze_columns(asset_columns)
                            
                            # Calculate mapping completeness
                            completeness = self._calculate_mapping_completeness(asset, mapping_analysis)
                            mapping_results["mapping_completeness"][asset.get('id', 'unknown')] = completeness
                            
                            # Update workflow status if mapping is complete enough
                            if completeness >= 80.0:  # 80% threshold for mapping completion
                                asset_id = asset.get('id')
                                if asset_id:
                                    workflow_update = await workflow_service.advance_asset_workflow(
                                        asset_id, "mapping", f"Field mapping completed ({completeness:.1f}% complete)"
                                    )
                                    mapping_results["workflow_updates"].append({
                                        "asset_id": asset_id,
                                        "workflow_update": workflow_update,
                                        "completeness": completeness
                                    })
                            
                            mapping_results["successfully_mapped"] += 1
                            
                        except Exception as e:
                            logger.error(f"Error processing asset {asset.get('id', 'unknown')}: {e}")
                            mapping_results["mapping_errors"].append({
                                "asset_id": asset.get('id', 'unknown'),
                                "error": str(e)
                            })
                
            except ImportError:
                logger.warning("Workflow service not available, proceeding without workflow updates")
                mapping_results["workflow_updates"] = "not_available"
            
            return mapping_results
            
        except Exception as e:
            logger.error(f"Error in process_field_mapping_batch: {e}")
            return {
                "error": f"Batch processing failed: {str(e)}",
                "total_assets": len(asset_data) if asset_data else 0,
                "successfully_mapped": 0
            }
    
    def _calculate_mapping_completeness(self, asset: Dict[str, Any], 
                                      mapping_analysis: Dict[str, Any]) -> float:
        """Calculate mapping completeness percentage for an asset."""
        try:
            # Critical fields for migration assessment
            critical_fields = [
                'hostname', 'asset_name', 'asset_type', 'environment', 
                'business_owner', 'department', 'operating_system'
            ]
            
            # Count how many critical fields are populated
            populated_count = 0
            for field in critical_fields:
                value = asset.get(field)
                if value and str(value).strip() and str(value).lower() not in ['unknown', 'null', 'none', '']:
                    populated_count += 1
            
            # Base completeness on critical field population
            base_completeness = (populated_count / len(critical_fields)) * 100
            
            # Bonus points for additional mapped fields
            total_fields = len(asset)
            bonus_completeness = min(20, (total_fields - len(critical_fields)) * 2)  # Max 20% bonus
            
            return min(100.0, base_completeness + bonus_completeness)
            
        except Exception as e:
            logger.error(f"Error calculating mapping completeness: {e}")
            return 0.0
    
    async def update_field_mapping_from_user_input(self, mapping_updates: Dict[str, str],
                                                 asset_id: str,
                                                 client_account_id: Optional[str] = None,
                                                 engagement_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Update field mappings based on user input and advance workflow if appropriate.
        
        Args:
            mapping_updates: Dictionary of field mappings (source_field -> target_field)
            asset_id: ID of the asset being updated
            client_account_id: Client account for multi-tenant scoping
            engagement_id: Engagement for project scoping
            
        Returns:
            Update results with workflow status
        """
        try:
            # Learn from user mappings
            learning_results = []
            for source_field, target_field in mapping_updates.items():
                learn_result = self.learn_field_mapping(target_field, [source_field], "user_mapping")
                learning_results.append(learn_result)
            
            # Try to update workflow status
            try:
                from app.core.database import AsyncSessionLocal
                from app.services.workflow_service import WorkflowService
                
                async with AsyncSessionLocal() as db:
                    workflow_service = WorkflowService(db, client_account_id, engagement_id)
                    
                    # Get asset to check current completeness
                    from app.repositories.asset_repository import AssetRepository
                    asset_repo = AssetRepository(db, client_account_id, engagement_id)
                    asset = await asset_repo.get_by_id(asset_id)
                    
                    if asset:
                        # Update asset with new mappings and check completeness
                        asset_dict = asset.__dict__.copy()
                        asset_dict.update(mapping_updates)
                        
                        # Calculate new completeness
                        completeness = self._calculate_mapping_completeness(asset_dict, {})
                        
                        # Update asset completeness score
                        await asset_repo.update(asset_id, completeness_score=completeness)
                        
                        # Advance workflow if mapping is complete
                        workflow_result = None
                        if completeness >= 80.0:
                            workflow_result = await workflow_service.update_asset_workflow_status(
                                asset_id, {"mapping_status": "completed"}
                            )
                        
                        return {
                            "success": True,
                            "mappings_learned": len(learning_results),
                            "learning_results": learning_results,
                            "completeness": completeness,
                            "workflow_result": workflow_result
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Asset {asset_id} not found"
                        }
                        
            except ImportError:
                logger.warning("Workflow service not available for field mapping updates")
                return {
                    "success": True,
                    "mappings_learned": len(learning_results),
                    "learning_results": learning_results,
                    "workflow_result": "not_available"
                }
                
        except Exception as e:
            logger.error(f"Error updating field mapping from user input: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def assess_mapping_readiness(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Assess overall mapping readiness across a set of assets.
        
        Args:
            assets: List of asset dictionaries to assess
            
        Returns:
            Mapping readiness assessment
        """
        try:
            if not assets:
                return {"readiness": "no_data", "message": "No assets to assess"}
            
            readiness_scores = []
            field_coverage = {}
            missing_fields_summary = {}
            
            # Critical fields for assessment
            critical_fields = [
                'hostname', 'asset_name', 'asset_type', 'environment',
                'business_owner', 'department', 'operating_system'
            ]
            
            for asset in assets:
                # Calculate completeness for this asset
                mapping_analysis = self.analyze_columns(list(asset.keys()))
                completeness = self._calculate_mapping_completeness(asset, mapping_analysis)
                readiness_scores.append(completeness)
                
                # Track field coverage
                for field in critical_fields:
                    if field not in field_coverage:
                        field_coverage[field] = 0
                    if asset.get(field) and str(asset.get(field)).strip():
                        field_coverage[field] += 1
                    else:
                        if field not in missing_fields_summary:
                            missing_fields_summary[field] = 0
                        missing_fields_summary[field] += 1
            
            # Calculate overall statistics
            total_assets = len(assets)
            average_completeness = sum(readiness_scores) / total_assets
            ready_assets = len([score for score in readiness_scores if score >= 80.0])
            
            # Calculate field coverage percentages
            field_coverage_percent = {
                field: (count / total_assets) * 100 
                for field, count in field_coverage.items()
            }
            
            # Determine readiness level
            if average_completeness >= 80.0:
                readiness_level = "ready"
            elif average_completeness >= 60.0:
                readiness_level = "partially_ready"
            else:
                readiness_level = "needs_work"
            
            return {
                "readiness": readiness_level,
                "average_completeness": round(average_completeness, 1),
                "ready_assets": ready_assets,
                "total_assets": total_assets,
                "ready_percentage": round((ready_assets / total_assets) * 100, 1),
                "field_coverage": field_coverage_percent,
                "missing_fields_summary": missing_fields_summary,
                "recommendations": self._generate_mapping_recommendations(
                    average_completeness, field_coverage_percent, missing_fields_summary
                )
            }
            
        except Exception as e:
            logger.error(f"Error assessing mapping readiness: {e}")
            return {
                "readiness": "error",
                "error": str(e)
            }
    
    def _generate_mapping_recommendations(self, average_completeness: float,
                                        field_coverage: Dict[str, float],
                                        missing_fields: Dict[str, int]) -> List[str]:
        """Generate specific recommendations for improving mapping completeness."""
        recommendations = []
        
        if average_completeness < 80.0:
            recommendations.append(f"Increase overall mapping completeness from {average_completeness:.1f}% to 80%")
        
        # Identify fields with low coverage
        for field, coverage in field_coverage.items():
            if coverage < 70.0:
                missing_count = missing_fields.get(field, 0)
                recommendations.append(
                    f"Complete {field} mapping - currently {coverage:.1f}% coverage ({missing_count} assets missing)"
                )
        
        # Priority recommendations
        if field_coverage.get('asset_type', 0) < 90.0:
            recommendations.insert(0, "Prioritize asset_type classification - critical for migration planning")
        
        if field_coverage.get('environment', 0) < 80.0:
            recommendations.insert(0 if not recommendations else 1, 
                                 "Complete environment classification - required for wave planning")
        
        if not recommendations:
            recommendations.append("Mapping is complete! Ready to proceed to cleanup phase.")
        
        return recommendations
    
    # Additional utility methods for backward compatibility
    def process_feedback_patterns(self, patterns: List[str]):
        """Process feedback patterns for learning (backward compatibility)."""
        try:
            for pattern in patterns:
                # Try to extract field mappings from pattern text
                self.learn_from_feedback_text(pattern, "pattern_processing")
        except Exception as e:
            logger.error(f"Error processing feedback patterns: {e}")
    
    def _normalize_field_name(self, field_name: str) -> str:
        """Normalize field name for matching."""
        return field_name.lower().strip().replace(' ', '_')
    
    def _find_base_mapping_matches(self, normalized_field: str) -> List[Dict[str, Any]]:
        """Find matches in base mappings."""
        matches = []
        for canonical_field, variations in self.base_mappings.items():
            for variation in variations:
                if normalized_field == variation or normalized_field in variation:
                    matches.append({
                        "target_field": canonical_field,
                        "confidence": "medium",
                        "source": "base_mapping"
                    })
                    break
        return matches
    
    def _calculate_match_confidence(self, matches: List[str], target_field: str) -> float:
        """Calculate confidence score for field matches."""
        if not matches:
            return 0.0
        
        # Simple confidence calculation based on exact matches
        exact_matches = sum(1 for match in matches if match.lower() == target_field.lower())
        return min(1.0, (exact_matches + len(matches) * 0.5) / len(matches))

# Create global instance for backward compatibility
def get_field_mapper() -> FieldMapperService:
    """Get global field mapper instance."""
    global _field_mapper_instance
    if '_field_mapper_instance' not in globals():
        _field_mapper_instance = FieldMapperService()
    return _field_mapper_instance

# Global instance
field_mapper = get_field_mapper()

# Legacy compatibility
FieldMapper = FieldMapperService
DynamicFieldMapper = FieldMapperService

# Export main classes and functions for backward compatibility
__all__ = [
    "FieldMapperService",
    "FieldMapper", 
    "DynamicFieldMapper",
    "field_mapper",
    "get_field_mapper"
] 