"""
Enrichment Agents Module - AI agents for automatic asset enrichment.

**ADR COMPLIANCE**:
- ADR-015: All agents use TenantScopedAgentPool for persistent agents
- ADR-024: All agents use TenantMemoryManager for learning (memory=False)
- LLM Tracking: All agents use multi_model_service.generate_response()

**Available Agents** (6 total):
1. ComplianceEnrichmentAgent - Compliance requirements and data classification
2. LicensingEnrichmentAgent - Software licensing information
3. VulnerabilityEnrichmentAgent - Security vulnerabilities (CVE tracking)
4. ResilienceEnrichmentAgent - HA/DR configuration
5. DependencyEnrichmentAgent - Asset relationship mapping
6. ProductMatchingAgent - Vendor product catalog matching

**Usage**:
```python
from app.services.enrichment.agents import (
    ComplianceEnrichmentAgent,
    LicensingEnrichmentAgent,
    VulnerabilityEnrichmentAgent,
    ResilienceEnrichmentAgent,
    DependencyEnrichmentAgent,
    ProductMatchingAgent
)

# Initialize agents
compliance_agent = ComplianceEnrichmentAgent(
    db=db,
    agent_pool=agent_pool,
    memory_manager=memory_manager,
    client_account_id=client_account_id,
    engagement_id=engagement_id
)

# Enrich assets
enriched_count = await compliance_agent.enrich_assets(assets)
```
"""

from app.services.enrichment.agents.compliance_agent import ComplianceEnrichmentAgent
from app.services.enrichment.agents.dependency_agent import DependencyEnrichmentAgent
from app.services.enrichment.agents.licensing_agent import LicensingEnrichmentAgent
from app.services.enrichment.agents.product_matching_agent import (
    ProductMatchingAgent,
)
from app.services.enrichment.agents.resilience_agent import ResilienceEnrichmentAgent
from app.services.enrichment.agents.vulnerability_agent import (
    VulnerabilityEnrichmentAgent,
)

__all__ = [
    "ComplianceEnrichmentAgent",
    "LicensingEnrichmentAgent",
    "VulnerabilityEnrichmentAgent",
    "ResilienceEnrichmentAgent",
    "DependencyEnrichmentAgent",
    "ProductMatchingAgent",
]
