"""Field mapping route modules."""

from .approval_routes import router as approval_router
from .mapping_routes import router as mapping_router
from .suggestion_routes import router as suggestion_router
from .validation_routes import router as validation_router

__all__ = [
    'mapping_router',
    'validation_router',
    'suggestion_routes', 
    'approval_router'
]