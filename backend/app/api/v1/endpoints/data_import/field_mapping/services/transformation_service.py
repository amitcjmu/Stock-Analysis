"""
Field mapping transformation service.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext

logger = logging.getLogger(__name__)


class TransformationService:
    """Service for field mapping transformations."""
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
    
    async def apply_transformation(
        self, 
        value: Any, 
        transformation_rule: str
    ) -> Any:
        """Apply transformation rule to a value."""
        if not transformation_rule:
            return value
        
        try:
            # Basic transformation rules
            rule = transformation_rule.lower().strip()
            
            if rule == "upper()":
                return str(value).upper() if value is not None else value
            elif rule == "lower()":
                return str(value).lower() if value is not None else value
            elif rule == "strip()":
                return str(value).strip() if value is not None else value
            elif rule.startswith("replace("):
                # Extract replace parameters
                # This is simplified - production would need proper parsing
                return str(value) if value is not None else value
            elif rule == "int()":
                return int(float(value)) if value is not None else value
            elif rule == "float()":
                return float(value) if value is not None else value
            else:
                logger.warning(f"Unknown transformation rule: {transformation_rule}")
                return value
                
        except Exception as e:
            logger.error(f"Error applying transformation {transformation_rule}: {e}")
            return value
    
    async def validate_transformation_rule(self, rule: str) -> Dict[str, Any]:
        """Validate if a transformation rule is safe and correct."""
        if not rule:
            return {"valid": True, "message": "No transformation rule"}
        
        # Basic validation
        safe_patterns = ["upper()", "lower()", "strip()", "int()", "float()"]
        
        if rule.lower() in safe_patterns:
            return {"valid": True, "message": "Valid transformation rule"}
        
        return {"valid": False, "message": f"Unsupported transformation rule: {rule}"}
    
    async def suggest_transformation(
        self, 
        source_values: List[Any], 
        target_field_type: str
    ) -> Optional[str]:
        """Suggest a transformation rule based on data analysis."""
        if not source_values:
            return None
        
        # Analyze source data
        sample_values = [v for v in source_values[:10] if v is not None]
        if not sample_values:
            return None
        
        # Basic suggestions based on target type
        if target_field_type == "integer":
            if all(isinstance(v, str) and v.isdigit() for v in sample_values):
                return "int()"
        elif target_field_type == "number":
            if all(isinstance(v, str) for v in sample_values):
                try:
                    [float(v) for v in sample_values]
                    return "float()"
                except ValueError:
                    pass
        elif target_field_type == "string":
            if any(isinstance(v, str) and v != v.strip() for v in sample_values):
                return "strip()"
        
        return None