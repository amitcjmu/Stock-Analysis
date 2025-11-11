"""Compliance standards templates."""

from app.services.gap_detection.standards.templates.hipaa import get_hipaa_standards
from app.services.gap_detection.standards.templates.pci_dss import (
    get_pci_dss_standards,
)
from app.services.gap_detection.standards.templates.soc2 import get_soc2_standards
from app.services.gap_detection.standards.templates.standards_loader import (
    StandardsTemplateLoader,
)

__all__ = [
    "get_pci_dss_standards",
    "get_hipaa_standards",
    "get_soc2_standards",
    "StandardsTemplateLoader",
]
