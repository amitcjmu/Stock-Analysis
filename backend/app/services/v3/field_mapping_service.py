"""
V3 Field Mapping Service
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.v3.field_mapping import V3FieldMappingRepository
from app.models import ImportFieldMapping
from app.repositories.v3.field_mapping import MappingStatus
from app.core.context import get_current_context
import logging
import uuid

logger = logging.getLogger(__name__)

class V3FieldMappingService:
    """Service for V3 field mapping operations"""
    
    def __init__(self, db: AsyncSession, client_account_id: Optional[str] = None, engagement_id: Optional[str] = None):
        self.db = db
        
        # Get context if not provided
        if not client_account_id or not engagement_id:
            try:
                context = get_current_context()
                client_account_id = client_account_id or str(context.client_account_id)
                engagement_id = engagement_id or str(context.engagement_id)
            except:
                # Default fallback if context not available
                client_account_id = client_account_id or str(uuid.uuid4())
                engagement_id = engagement_id or str(uuid.uuid4())
        
        self.mapping_repo = V3FieldMappingRepository(db, client_account_id, engagement_id)
    
    async def create_ai_suggestions(
        self,
        import_id: str,
        suggestions: List[Dict[str, Any]]
    ) -> List[ImportFieldMapping]:
        """Create AI-suggested field mappings"""
        try:
            # Prepare mapping data
            mappings_data = []
            for suggestion in suggestions:
                mappings_data.append({
                    "data_import_id": import_id,
                    "source_field": suggestion["source_field"],
                    "target_field": suggestion["target_field"],
                    "confidence_score": suggestion.get("confidence", 0.0),
                    "match_type": suggestion.get("match_type", "fuzzy"),
                    "status": MappingStatus.SUGGESTED,
                    "suggested_by": suggestion.get("suggested_by", "ai_agent"),
                    "transformation_rules": suggestion.get("transformation_rules")
                })
            
            # Bulk create mappings
            mappings = await self.mapping_repo.bulk_create_mappings(
                import_id,
                mappings_data
            )
            
            logger.info(f"Created {len(mappings)} AI suggestions for import {import_id}")
            
            return mappings
            
        except Exception as e:
            logger.error(f"Failed to create AI suggestions: {e}")
            raise
    
    async def generate_auto_mappings(
        self,
        import_id: str,
        source_fields: List[str]
    ) -> List[ImportFieldMapping]:
        """Generate automatic field mappings using heuristics"""
        try:
            suggestions = []
            
            for field in source_fields:
                # Use simple field name matching heuristics
                field_lower = field.lower().replace('_', '').replace(' ', '')
                
                # Common field mappings with confidence scores
                if 'name' in field_lower or 'hostname' in field_lower:
                    suggestions.append({
                        "source_field": field,
                        "target_field": "asset_name",
                        "confidence": 0.9,
                        "match_type": "exact"
                    })
                elif 'ip' in field_lower:
                    suggestions.append({
                        "source_field": field,
                        "target_field": "ip_address", 
                        "confidence": 0.95,
                        "match_type": "exact"
                    })
                elif 'os' in field_lower or 'operating' in field_lower:
                    suggestions.append({
                        "source_field": field,
                        "target_field": "operating_system",
                        "confidence": 0.85,
                        "match_type": "fuzzy"
                    })
                elif 'cpu' in field_lower or 'processor' in field_lower:
                    suggestions.append({
                        "source_field": field,
                        "target_field": "cpu_cores",
                        "confidence": 0.8,
                        "match_type": "fuzzy"
                    })
                elif 'memory' in field_lower or 'ram' in field_lower:
                    suggestions.append({
                        "source_field": field,
                        "target_field": "memory_gb",
                        "confidence": 0.8,
                        "match_type": "fuzzy"
                    })
                elif 'storage' in field_lower or 'disk' in field_lower:
                    suggestions.append({
                        "source_field": field,
                        "target_field": "storage_gb",
                        "confidence": 0.8,
                        "match_type": "fuzzy"
                    })
                elif 'environment' in field_lower or 'env' in field_lower:
                    suggestions.append({
                        "source_field": field,
                        "target_field": "environment",
                        "confidence": 0.75,
                        "match_type": "fuzzy"
                    })
                elif 'location' in field_lower or 'datacenter' in field_lower:
                    suggestions.append({
                        "source_field": field,
                        "target_field": "location",
                        "confidence": 0.75,
                        "match_type": "fuzzy"
                    })
            
            # Create the AI suggestions
            return await self.create_ai_suggestions(import_id, suggestions)
            
        except Exception as e:
            logger.error(f"Failed to generate auto mappings: {e}")
            raise
    
    async def get_mappings_for_import(self, import_id: str) -> List[Dict[str, Any]]:
        """Get all mappings for an import"""
        mappings = await self.mapping_repo.get_by_import(import_id)
        
        return [
            {
                "id": str(mapping.id),
                "source_field": mapping.source_field,
                "target_field": mapping.target_field,
                "confidence_score": mapping.confidence_score,
                "match_type": mapping.match_type,
                "status": mapping.status,
                "suggested_by": mapping.suggested_by,
                "transformation_rules": mapping.transformation_rules,
                "approved_by": mapping.approved_by,
                "approved_at": mapping.approved_at.isoformat() if mapping.approved_at else None,
                "created_at": mapping.created_at.isoformat() if mapping.created_at else None,
                "updated_at": mapping.updated_at.isoformat() if mapping.updated_at else None
            }
            for mapping in mappings
        ]
    
    async def get_mapping_by_id(self, mapping_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific mapping by ID"""
        mapping = await self.mapping_repo.get_by_id(mapping_id)
        if not mapping:
            return None
        
        return {
            "id": str(mapping.id),
            "data_import_id": str(mapping.data_import_id),
            "source_field": mapping.source_field,
            "target_field": mapping.target_field,
            "confidence_score": mapping.confidence_score,
            "match_type": mapping.match_type,
            "status": mapping.status,
            "suggested_by": mapping.suggested_by,
            "transformation_rules": mapping.transformation_rules,
            "approved_by": mapping.approved_by,
            "approved_at": mapping.approved_at.isoformat() if mapping.approved_at else None,
            "created_at": mapping.created_at.isoformat() if mapping.created_at else None,
            "updated_at": mapping.updated_at.isoformat() if mapping.updated_at else None
        }
    
    async def approve_mapping(
        self,
        mapping_id: str,
        approved_by: Optional[str] = None
    ) -> bool:
        """Approve a field mapping"""
        try:
            if not approved_by:
                try:
                    context = get_current_context()
                    approved_by = str(context.user_id) if context.user_id else "system"
                except:
                    approved_by = "system"
            
            success = await self.mapping_repo.approve_mapping(mapping_id, approved_by)
            
            if success:
                logger.info(f"Approved mapping {mapping_id} by {approved_by}")
                # Trigger agent learning
                await self._trigger_agent_learning(mapping_id, "approved")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to approve mapping: {e}")
            return False
    
    async def reject_mapping(
        self,
        mapping_id: str,
        rejected_by: Optional[str] = None
    ) -> bool:
        """Reject a field mapping"""
        try:
            if not rejected_by:
                try:
                    context = get_current_context()
                    rejected_by = str(context.user_id) if context.user_id else "system"
                except:
                    rejected_by = "system"
            
            success = await self.mapping_repo.reject_mapping(mapping_id, rejected_by)
            
            if success:
                logger.info(f"Rejected mapping {mapping_id} by {rejected_by}")
                # Trigger agent learning
                await self._trigger_agent_learning(mapping_id, "rejected")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to reject mapping: {e}")
            return False
    
    async def update_mapping(
        self,
        mapping_id: str,
        target_field: str,
        transformation_rules: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update mapping with new target"""
        try:
            success = await self.mapping_repo.update_mapping(
                mapping_id,
                target_field,
                transformation_rules
            )
            
            if success:
                logger.info(f"Updated mapping {mapping_id} to target {target_field}")
                # Trigger agent learning
                await self._trigger_agent_learning(mapping_id, "modified")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update mapping: {e}")
            return False
    
    async def get_mapping_statistics(self, import_id: str) -> Dict[str, Any]:
        """Get mapping statistics for an import"""
        return await self.mapping_repo.get_mapping_statistics(import_id)
    
    async def validate_mappings(
        self,
        import_id: str,
        sample_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Validate field mappings against sample data"""
        try:
            mappings = await self.mapping_repo.get_by_import(import_id)
            
            issues = []
            warnings = []
            
            # Check for duplicate target fields
            target_fields = [m.target_field for m in mappings]
            duplicate_targets = [field for field in set(target_fields) if target_fields.count(field) > 1]
            
            if duplicate_targets:
                issues.append({
                    "type": "DUPLICATE_TARGETS",
                    "severity": "warning",
                    "message": f"Multiple source fields mapped to the same target: {duplicate_targets}",
                    "fields": duplicate_targets
                })
            
            # Validate against sample data if provided
            if sample_data and mappings:
                sample_record = sample_data[0] if sample_data else {}
                
                for mapping in mappings:
                    if mapping.source_field not in sample_record:
                        issues.append({
                            "type": "SOURCE_FIELD_NOT_FOUND",
                            "severity": "error",
                            "message": f"Source field '{mapping.source_field}' not found in sample data",
                            "field": mapping.source_field,
                            "mapping_id": str(mapping.id)
                        })
            
            # Calculate validation score
            total_mappings = len(mappings)
            error_count = len([issue for issue in issues if issue.get("severity") == "error"])
            warning_count = len([issue for issue in issues if issue.get("severity") == "warning"])
            
            validation_score = max(0.0, 1.0 - (error_count * 0.5 + warning_count * 0.2) / max(total_mappings, 1))
            is_valid = error_count == 0
            
            return {
                "is_valid": is_valid,
                "validation_score": validation_score,
                "total_mappings": total_mappings,
                "issues": issues,
                "warnings": warnings,
                "recommendations": self._generate_recommendations(is_valid, warning_count, total_mappings)
            }
            
        except Exception as e:
            logger.error(f"Failed to validate mappings: {e}")
            return {
                "is_valid": False,
                "validation_score": 0.0,
                "total_mappings": 0,
                "issues": [{"type": "VALIDATION_ERROR", "severity": "error", "message": str(e)}],
                "warnings": [],
                "recommendations": ["Fix validation errors before proceeding"]
            }
    
    def _generate_recommendations(self, is_valid: bool, warning_count: int, total_mappings: int) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        if not is_valid:
            recommendations.append("Fix all error-level issues before proceeding")
        if warning_count > 0:
            recommendations.append("Review warning-level issues for optimal mapping")
        if total_mappings < 5:
            recommendations.append("Consider mapping more fields for better data coverage")
        if is_valid and warning_count == 0:
            recommendations.append("Mapping validation passed - ready for data processing")
        
        return recommendations
    
    async def _trigger_agent_learning(
        self,
        mapping_id: str,
        action: str
    ) -> None:
        """Trigger agent learning from user feedback"""
        try:
            # Get the mapping
            mapping = await self.mapping_repo.get_by_id(mapping_id)
            if not mapping:
                return
            
            # Log learning event
            logger.info(
                f"Agent learning: {action} mapping {mapping.source_field} -> {mapping.target_field} "
                f"(confidence: {mapping.confidence_score})"
            )
            
            # TODO: Integrate with actual agent learning system
            # This could send learning events to CrewAI agents or other ML systems
            
        except Exception as e:
            logger.error(f"Failed to trigger agent learning: {e}")