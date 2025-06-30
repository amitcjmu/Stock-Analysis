"""
Crew Management System for AI Force Migration Platform

This package provides:
- BaseDiscoveryCrew: Abstract base class for all crews
- FieldMappingCrew: Intelligent field mapping with semantic understanding  
- DataCleansingCrew: Data quality assurance and standardization
- AssetInventoryCrew: Asset classification and inventory management
- CrewFactory: Dynamic crew creation and management
- TaskTemplates: Reusable task patterns for common operations

Usage:
    from app.services.crews.factory import CrewFactory
    
    # Create a crew
    crew = CrewFactory.create_crew("field_mapping")
    
    # Execute crew with inputs
    result = crew.execute({
        "raw_data": [...],
        "target_fields": [...]
    })
    
    # Or use factory shorthand
    result = CrewFactory.execute_crew("field_mapping", inputs)
"""

from .base_crew import BaseDiscoveryCrew
from .factory import CrewFactory, crew_factory
from .task_templates import TaskTemplates

# Crew implementations
from .field_mapping_crew import FieldMappingCrew
from .data_cleansing_crew import DataCleansingCrew  
from .asset_inventory_crew import AssetInventoryCrew

__all__ = [
    "BaseDiscoveryCrew",
    "CrewFactory", 
    "crew_factory",
    "TaskTemplates",
    "FieldMappingCrew",
    "DataCleansingCrew", 
    "AssetInventoryCrew"
]