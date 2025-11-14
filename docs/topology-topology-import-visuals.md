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
