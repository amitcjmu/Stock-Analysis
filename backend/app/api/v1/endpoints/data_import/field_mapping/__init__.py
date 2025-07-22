"""
Field Mapping Module

Modularized field mapping functionality with clear separation of concerns:
- routes/: HTTP route handlers
- services/: Business logic services
- validators/: Data validation logic
- models/: Pydantic schemas and data models
- utils/: Utility functions and helpers
"""

from .routes.approval_routes import router as approval_router
from .routes.mapping_routes import router as mapping_router
from .routes.suggestion_routes import router as suggestion_router
from .routes.validation_routes import router as validation_router
from .services.mapping_service import MappingService
from .services.suggestion_service import SuggestionService
from .services.transformation_service import TransformationService
from .services.validation_service import ValidationService

__all__ = [
    'mapping_router',
    'validation_router', 
    'suggestion_router',
    'approval_router',
    'MappingService',
    'ValidationService',
    'SuggestionService',
    'TransformationService'
]