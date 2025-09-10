"""
Collection Data Population Service Module

This module provides the CollectionDataPopulationService for ensuring proper
data population for collection flows. The service has been modularized into
smaller components while maintaining 100% backward compatibility.

Module Structure:
- core.py: Main service class and orchestration logic
- handlers.py: Data processing and population handlers  
- validators.py: Validation and verification methods

For backward compatibility, the main service class can be imported directly:
    from app.services.collection_data_population import CollectionDataPopulationService

The modular components can also be imported individually if needed:
    from app.services.collection_data_population.core import CollectionDataPopulationService
    from app.services.collection_data_population.handlers import CollectionDataHandlers
    from app.services.collection_data_population.validators import CollectionDataValidators
"""

# Import the main service class for backward compatibility
from .core import CollectionDataPopulationService

# Also make the modular components available
from .handlers import CollectionDataHandlers
from .validators import CollectionDataValidators
from .extractors import CollectionDataExtractors

# Export the main class for external usage
__all__ = [
    "CollectionDataPopulationService",
    "CollectionDataHandlers", 
    "CollectionDataValidators",
    "CollectionDataExtractors",
]