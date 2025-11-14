
# Design Context

**Design guidelines:** see Issue [#1009](https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/issues/1009) for the full architecture and reference materials that informed the visuals below. The sections that follow summarize how Tranche 1 generalized the discovery flow so CMDB and non-CMDB topology inputs reuse the same phases.

### Flow-Phase Responsibilities & Agent Touchpoints

| Discovery Phase (ADR-027) | Processor Responsibilities | Agent / LLM Interactions | Outputs we must persist |
| --- | --- | --- | --- |
| `data_import` | Store raw topology rows, capture metadata (`import_category`, `processing_config`). | None (file ingestion only). | `raw_import_records`, `DataImport.flow_execution_data`. |
| `data_validation` | Normalize schema per source (AppDynamics, Datadog), check required keys, deduplicate hosts/components. | Call validation agents via the agent pool (e.g., `topology_schema_agent`) to inspect samples and produce warnings/errors. All calls must go through the LLM tracking wrapper with `import_id`, `flow_id`, `category`. | Phase result with `validation.valid`, warnings/errors saved to `flow_state.phase_results`. |
| `attribute_mapping` | Surface discovered columns/components to the UI for mapping (e.g., tier name → CMDB attribute). | Optional field-mapping agent assistance (existing persistent agent). | `import_field_mappings`, `flow_state.raw_data` updates. |
| `data_cleansing` | Apply agent-guided fixes (e.g., normalize service names, environment tags, hostnames). | Use cleansing agents from the pool when automatic corrections are needed; log every prompt/response. | Cleaned rows (either `raw_import_records.cleansed_data` or processor-specific staging tables). |
| `asset_creation` | Persist components/dependencies: create/update `Asset`, `ApplicationComponent`, `AssetDependency` entries, record counts. | Optional enrichment agents (e.g., to infer missing relationships) but still via pool + LLM tracking. | Database writes plus phase summary metrics (components matched, edges created). |

### Processor Contract (Issue #1009 §§2–3)

1. **Base class expectations**
   - `validate_data(import_id, raw_records, processing_config)` **must** return `{"valid": bool, "validation_errors": [...], "warnings": [...]}` so the orchestrator can update the `data_validation` phase consistently.
   - `enrich_assets(import_id, validated_records, processing_config)` **must** return counts (`assets_enriched`, `dependencies_created`, etc.) so we can surface progress in `asset_creation`.
   - Both methods should write any intermediate artifacts (normalized rows, inferred relationships) back to persistence (`flow_execution_data`, dedicated tables) so downstream phases or retries don’t need the original file.
2. **Application Discovery processor example**
   - Validation step can call the schema-validation agent to confirm tier/service fields, and attach explanations to `warnings`.
   - Enrichment step should resolve each service to a CMDB application + host asset (using the alias map), then insert or update the `Asset`/`AssetDependency` tables while noting mismatches for the UI.

### Agent Pool & LLM Tracking (Issue #1009 §§5–6)

- **Agent pool access**: processors must obtain agents via the shared pool classmethod (e.g., `AgentPool.get_agent("topology_validator", context)`) rather than instantiating clients directly. This enforces tenant-aware configuration and resource quotas.
- **Automatic tracking**: every LLM/agent call must go through the centralized wrapper that logs prompt, completion, cost, and metadata (`import_id`, `flow_id`, `import_category`). This keeps the audit trail intact and allows cost attribution per import.
- **Documentation / TODOs**
  - Add processor-specific notes indicating which agent profile they use (validation vs. cleansing vs. enrichment) so future contributors know where to extend.
  - Capture any new tracking fields we need (e.g., `component_id`, `dependency_type`) so the LLM logs can be correlated with stored graph data.

> **Next inputs needed:**  
> - Agent profile names + prompts we plan to register (validation vs. enrichment).  
> - Any additional metadata that should be included in LLM tracking (e.g., source system, export timestamp).

### Asset & Dependency Persistence Strategy

- **Reuse the existing `Asset` table** for application components. Each distinct tier/service discovered from AppDynamics/Datadog becomes (or updates) an `Asset` row with `asset_type = "component"` and appropriate metadata (language, environment, agent type, export timestamp). This keeps querying uniform across infrastructure + components.
- **Dependencies stay in `AssetDependency`**. For each source → target relationship we insert/update an `AssetDependency` row keyed strictly by the canonical `asset_id` values (UUID) from the `Asset` table—never by names. Metrics (`latency_ms`, `call_count`, `error_rate`, `dependency_type`) live alongside those IDs, and any extra attributes can go into the JSONB payload. During import we must resolve both ends to real assets (creating component assets first if needed) before inserting the dependency edge.
- **Matching flow**:
  1. Resolve application → parent Asset (existing CMDB entry).
  2. Resolve component → Asset (create if missing, `asset_type="component"`).
  3. Resolve host → Asset (existing server entry) and link via `asset.host_asset_id` (custom attribute) or a join table if needed.
  4. Create/update `AssetDependency` records (component ↔ component, component ↔ database, etc.).
- **Repository usage**: processors should call the existing asset/dependency repositories (or helper methods we expose) so the same transaction/tenant scoping rules apply. For example, use `AssetRepository.find_or_create_by(name, asset_type)` and `AssetDependencyRepository.upsert_edge(...)`.
- **Unmatched items**: when a component can’t be tied to a known application or host, log it in the phase results and optionally create a “pending” component asset flagged for manual review (e.g., `status="unmatched"`). This preserves traceability without blocking ingestion.

## Discovery flow adjustments for non-CMDB imports

### a) Application discovery uploads on the CMDB import page
- Add a second option on the Discovery / CMDB Import UI labelled “Application Discovery Data (AppDynamics / Datadog dependency scans)”.
- Submissions still post to `/api/v1/data-import/upload`, but set `import_category=app_discovery` so ApplicationDiscoveryProcessor handles the records while the same master/child flow orchestration runs (`data_import → … → asset_creation`).
- Make it clear to users that this path ingests service-to-service dependencies (application portfolio + dependency scan results) but otherwise shares the CMDB discovery flow.

### b) Attribute mapping UX after validation
- After `data_validation`, auto-route users to `/discovery/attribute-mapping/:flow_id`.
- Restrict the target-field dropdowns to dependency-relevant fields only:
  - `assets`: application name, hostname/FQDN, environment, owner, criticality.
  - `asset_dependency`: downstream component, dependency_type, latency, call_count, error_rate, port, protocol.
- Persist selections in `import_field_mappings` so cleansing and asset creation phases reuse the same mappings for AppDynamics/Datadog columns.

---

# Application & Dependency Export References

Ram Ayyalaraju noted that AppDynamics and Datadog provide topology, dependency, and component exports beyond basic metrics. Below are the key datasets and examples derived from synthetic exports he generated.

🧩 **1. Application–Server Dependencies (Topology Mapping)**

Both AppDynamics and Datadog APM produce service/flow maps showing:

- How applications/services call each other.
- Which backends (databases, queues, APIs) they reach.
- Which infrastructure nodes host each tier.

| Field | Description |
| --- | --- |
| Application Name | Logical app in AppDynamics or Datadog |
| Tier/Service Name | Microservice or application component |
| Node/Host Name | Server or container the service runs on |
| Dependency Type | HTTP, JDBC, MQ, gRPC, custom |
| Downstream Component | Service or backend being called |
| Average Latency | Average response time between tiers |
| Call Count | Number of calls in the sample period |
| Error Rate | Percentage of failed calls |
| Link Direction | source → target relationship |

**Example: AppDynamics Flow Map CSV**

| application_name | tier_name | node_name | called_component | dependency_type | call_count | avg_response_time_ms | error_rate_percent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RetailApp | CheckoutService | checkout-01 | InventoryService | HTTP | 15890 | 230 | 1.2 |
| RetailApp | CheckoutService | checkout-01 | PaymentsDB | JDBC | 4250 | 87 | 0.3 |
| RetailApp | InventoryService | inventory-02 | OracleDB | JDBC | 3090 | 95 | 0.1 |
| RetailApp | FrontendService | frontend-03 | CheckoutService | HTTP | 12200 | 180 | 0.5 |

🧱 **2. Application Components and Services Details**

| Field | Description |
| --- | --- |
| Application ID / Name | The monitored app |
| Tier Name | Logical grouping (e.g., Web Tier, API Tier) |
| Node Name | Physical or virtual node |
| Agent Type | Java, .NET, Node.js, etc. |
| Business Transaction | Named transaction path being monitored |
| Entry Point | Servlet, API, message queue, etc. |
| Health Status | Normal / Warning / Critical |
| Associated Services | List of dependent services or tiers |

**Example: Datadog Service Catalog / AppDynamics Tier List**

| application_name | service_name | component_type | language | host | environment | status | dependencies |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RetailApp | FrontendService | Web | JavaScript | frontend-03 | production | Healthy | CheckoutService |
| RetailApp | CheckoutService | API | Java | checkout-01 | production | Warning | InventoryService, PaymentsDB |
| RetailApp | InventoryService | Backend | Java | inventory-02 | production | Healthy | OracleDB |
| RetailApp | PaymentsDB | Database | PostgreSQL | payments-db | production | Healthy | - |

🗺️ **3. Export Endpoints**

- **AppDynamics**: Application Model REST API (tiers), Business Transactions API, Backend Dependencies API.
- **Datadog**: Service Catalog API, Service Map API, Topology API.

**Combined Topology JSON example**

```json
{
  "application": "RetailApp",
  "services": [
    {"name": "FrontendService", "type": "web", "language": "javascript", "dependencies": ["CheckoutService"]},
    {"name": "CheckoutService", "type": "api", "language": "java", "dependencies": ["InventoryService", "PaymentsDB"]},
    {"name": "InventoryService", "type": "backend", "language": "java", "dependencies": ["OracleDB"]},
    {"name": "PaymentsDB", "type": "database", "language": "postgresql", "dependencies": []}
  ]
}
```

# Topology Import Data Flow

Ram Ayyalaraju - You can create synthetic versions of the app monitoring tools from copilot. Here's what I had generated.

you’re absolutely right to look for topology, dependency, and component mapping data.

Let’s go a level deeper, because AppDynamics and Datadog absolutely can export application-to-server mappings, component relationships, and service topology data — it’s just that those are separate datasets (not part of basic metric exports).

🧩 1. Application–Server Dependencies (Topology Mapping)

What It Contains

Both AppDynamics and Datadog APM build a service map or flow map, showing how:

Applications and services call each other.

Backends (databases, message queues, APIs) are connected.

Infrastructure nodes (VMs, containers, hosts) support those applications.

The exported data here includes:

| Field | Description |
| --- | --- |
| Application Name | Logical app in AppDynamics or Datadog |
| Tier/Service Name | Microservice or application component |
| Node/Host Name | Server or container the service runs on |
| Dependency Type | HTTP, JDBC, MQ, gRPC, custom |
| Downstream Component | Service or backend being called |
| Average Latency | Average response time between tiers |
| Call Count | Number of calls in the sample period |
| Error Rate | Percentage of failed calls |
| Link Direction | source → target relationship |

**Example: App-to-Server Mapping Export (AppDynamics Flow Map CSV)**

| application_name | tier_name | node_name | called_component | dependency_type | call_count | avg_response_time_ms | error_rate_percent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RetailApp | CheckoutService | checkout-01 | InventoryService | HTTP | 15890 | 230 | 1.2 |
| RetailApp | CheckoutService | checkout-01 | PaymentsDB | JDBC | 4250 | 87 | 0.3 |
| RetailApp | InventoryService | inventory-02 | OracleDB | JDBC | 3090 | 95 | 0.1 |
| RetailApp | FrontendService | frontend-03 | CheckoutService | HTTP | 12200 | 180 | 0.5 |

This gives you a complete topology snapshot — essentially a “flattened” representation of the AppDynamics flow map.

🧱 2. Application Components and Services Details

What It Contains

These exports describe logical components, tiers, and business transactions (BTs).

They’re key to understanding what makes up an application.

| Field | Description |
| --- | --- |
| Application ID / Name | The monitored app |
| Tier Name | Logical grouping (e.g., Web Tier, API Tier) |
| Node Name | Physical or virtual node |
| Agent Type | Java, .NET, Node.js, etc. |
| Business Transaction | Named transaction path being monitored |
| Entry Point | Servlet, API, message queue, etc. |
| Health Status | Normal / Warning / Critical |
| Associated Services | List of dependent services or tiers |

**Example: Component Definition Export (Datadog Service Catalog / AppDynamics Tier List)**

| application_name | service_name | component_type | language | host | environment | status | dependencies |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RetailApp | FrontendService | Web | JavaScript | frontend-03 | production | Healthy | CheckoutService |
| RetailApp | CheckoutService | API | Java | checkout-01 | production | Warning | InventoryService, PaymentsDB |
| RetailApp | InventoryService | Backend | Java | inventory-02 | production | Healthy | OracleDB |
| RetailApp | PaymentsDB | Database | PostgreSQL | payments-db | production | Healthy | - |

This corresponds to the AppDynamics “Tiers & Nodes” view or Datadog Service Catalog export.

🗺️ 3. How These Are Exported

In AppDynamics

Flow Maps → Exported via Application Model REST API (/controller/rest/applications/{id}/tiers)

Business Transactions → /controller/rest/applications/{id}/business-transactions

Backend Dependencies → /controller/rest/applications/{id}/backends

You can combine these to reconstruct a complete topology graph.

In Datadog

Service Catalog API → Lists services, owners, runtimes, dependencies

Service Map API → Returns relationships between services

Topology API → Used to visualize or export node–edge relationships

📄 Combined Example (Service Topology JSON Export)

{

  "application": "RetailApp",

  "services": [

    {

      "name": "FrontendService",

      "type": "web",

      "language": "javascript",

      "dependencies": ["CheckoutService"]

    },

    {

      "name": "CheckoutService",

      "type": "api",

      "language": "java",

      "dependencies": ["InventoryService", "PaymentsDB"]

    },

    {

      "name": "InventoryService",

      "type": "backend",

      "language": "java",

      "dependencies": ["OracleDB"]

    },

    {

      "name": "PaymentsDB",

      "type": "database",

      "language": "postgresql",

      "dependencies": []

    }

  ]

}

This JSON model reflects what both AppDynamics and Datadog can produce — a graph of services, components, and their dependencies.

# Topology Import Data Flow

```
+------------------+        +----------------------------+        +------------------------------+
|  Source Export   |        |   Topology Import Upload   |        |  DataImport Storage/ChildFlow |
| (Datadog / AppD) |        | (existing /upload endpoint)|        |  (DataImportChildFlowService) |
+------------------+        +----------------------------+        +------------------------------+
        |                               |                                    |
        | 1. CSV/JSON payload           |                                    |
        +------------------------------>| 2. Store raw file rows             |
                                        |    → raw_import_records.raw_data   |
                                        | 3. Create DataImport record        |
                                        | 4. Kick off discovery flow         |
                                        |    (master_flow_id)                |
                                        +----------------------------------->| 5. Persist flow metadata          |
                                                                             |    (full raw_data, sample, config)|
                                                                             | 6. BackgroundExecutionService     |
                                                                             +--------------------+--------------+
                                                                                                  |
                                                                                                  v
                                                                                 +------------------------------+
                                                                                 |  Topology Processor (new)    |
                                                                                 |  e.g. DatadogTopologyProcessor|
                                                                                 +------------------------------+
                                                                                                  |
                                                                                  7a. Validation: normalize IDs |
                                                                                  7b. Enrichment: match assets  |
                                                                                  |    - asset lookup by hostname|
                                                                                  |    - create/update Asset     |
                                                                                  |      and AssetDependency rows|
                                                                                                  |
                                                                                                  v
+----------------------------+         +---------------------------------------------+
| Existing Asset Inventory   |<--------| Persisted Graph                            |
| (Asset, AssetDependency)   | 8. edges reference asset_id/source/target            |
+----------------------------+         +---------------------------------------------+
                                             |
                                   +---------------------------+
                                   | UI / Reports / APIs       |
                                   |  - unmatched components   |
                                   |  - dependency map         |
                                   |  - merge suggestions      |
                                   +---------------------------+
```

## Component-to-Application Linkage

```
                ┌────────────────────────────┐
                │ Raw topology rows (import) │
                └────────────┬───────────────┘
                             │
                             ▼
┌───────────────────────────────────────────────────────┐
│ Datadog/AppDynamics topology processor                │
│  (validate, normalize identifiers, classify)          │
│                                                       │
│ 1. Resolve tier/service → application component       │
│    • Normalize service name, env, runtime             │
│    • Check for existing ApplicationComponent records  │
│    • If none, create component entry that references  │
│      the parent application and hosting asset         │
│                                                       │
│ 2. Link component ↔ asset                             │
│    • Match hostname / k8s node / VM ID to Asset       │
│    • Store relationship (e.g., component.host_asset_id)│
│                                                       │
│ 3. Record dependencies between components             │
│    • Create edges (component → component, component → DB)│
│      via ApplicationDependency or repurposed          │
│      AssetDependency with a “component” flag)         │
└───────────────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│ Graph storage (new tables or reuse existing relationships)│
│  • ApplicationComponent (service/tier metadata)           │
│  • ComponentDependency (edges, latency metrics)           │
│  • Link to Asset / Database assets                        │
└──────────────────────────────────────────────────────────┘
                             │
                             ▼
                   UI & analytics layers
                   (component list, dependency maps,
                    alerts for unmatched components)
```

Each import row includes the source application identifier (e.g., `application_name` or service catalog tag). During processing we:

1. Look up or create the parent application in the CMDB.
2. Create/update the application component with pointers to both the application and the hosting asset.
3. Store dependency edges so the GUI can render the complete application topology.
