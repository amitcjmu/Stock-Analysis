### Regression Catalog (Pytest)

#### Discovery
- `tests/backend/flows/test_unified_discovery_flow.py` (markers: discovery, regression, integration)
- `tests/backend/test_api_integration.py` (markers: discovery, regression, integration)
- `tests/test_flow_creation.py` (scripted E2E)
- `tests/test_e2e_validation.py` (scripted E2E)
- `tests/backend/services/test_master_flow_orchestrator.py` (markers: regression, unit)

#### Collection
- `tests/backend/integration/test_collection_flow_mfo.py` (markers: collection, regression, integration)

#### Cross-Flow / Platform
- `tests/backend/test_sixr_analysis.py` (consider: regression)
- `tests/backend/test_agentic_system.py` (consider: regression)
- `tests/backend/test_crewai_system.py` (consider: regression)
- `tests/backend/test_smoke.py` (smoke)

#### Performance
- `tests/backend/performance/test_discovery_performance.py` (performance)
- `tests/backend/performance/test_state_operations.py` (performance)

Ownership: QA curates this list and markers per release.


