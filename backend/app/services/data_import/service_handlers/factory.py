"""
Processor factory for multi-category data import execution.
"""

from __future__ import annotations

from typing import Dict, Type

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext

from .app_discovery_processor import ApplicationDiscoveryProcessor
from .base_processor import BaseDataImportProcessor
from .cmdb_export_processor import CMDBExportProcessor
from .infrastructure_processor import InfrastructureProcessor
from .sensitive_data_processor import SensitiveDataProcessor


PROCESSOR_REGISTRY: Dict[str, Type[BaseDataImportProcessor]] = {
    CMDBExportProcessor.category: CMDBExportProcessor,
    ApplicationDiscoveryProcessor.category: ApplicationDiscoveryProcessor,
    InfrastructureProcessor.category: InfrastructureProcessor,
    SensitiveDataProcessor.category: SensitiveDataProcessor,
}


def get_processor_for_category(
    import_category: str,
    db: AsyncSession,
    context: RequestContext,
) -> BaseDataImportProcessor:
    """
    Resolve a processor instance for the given import category.

    Raises:
        KeyError: If no processor is registered for the category.
    """
    category = (import_category or "").lower()
    if category not in PROCESSOR_REGISTRY:
        raise KeyError(f"No processor registered for category '{import_category}'")

    processor_cls = PROCESSOR_REGISTRY[category]
    return processor_cls(db=db, context=context)
