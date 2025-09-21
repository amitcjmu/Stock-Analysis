## Database Schema Changes (Migration Schema)

Note: All tables in `migration` schema. Use CHECK constraints over ENUMs. Tenant isolation via `client_account_id`, `engagement_id`.

Vendor Lifecycle (Global Catalog + Tenant Overrides)
```sql
-- Global catalog (shared)
CREATE TABLE migration.vendor_products_catalog (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  vendor_name VARCHAR(255) NOT NULL,
  product_name VARCHAR(255) NOT NULL,
  normalized_key VARCHAR(255) NOT NULL,
  is_global BOOLEAN NOT NULL DEFAULT TRUE,
  UNIQUE (vendor_name, product_name)
);

CREATE TABLE migration.product_versions_catalog (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  catalog_id UUID NOT NULL REFERENCES migration.vendor_products_catalog(id) ON DELETE CASCADE,
  version_label VARCHAR(100) NOT NULL,
  version_semver VARCHAR(100),
  UNIQUE (catalog_id, version_label)
);

-- Tenant overrides/additions
CREATE TABLE migration.tenant_vendor_products (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_account_id UUID NOT NULL REFERENCES migration.client_accounts(id) ON DELETE CASCADE,
  engagement_id UUID NOT NULL REFERENCES migration.engagements(id) ON DELETE CASCADE,
  catalog_id UUID REFERENCES migration.vendor_products_catalog(id) ON DELETE SET NULL,
  custom_vendor_name VARCHAR(255),
  custom_product_name VARCHAR(255),
  normalized_key VARCHAR(255),
  UNIQUE (client_account_id, engagement_id, COALESCE(catalog_id, '00000000-0000-0000-0000-000000000000'::uuid), COALESCE(custom_vendor_name,''), COALESCE(custom_product_name,''))
);

CREATE TABLE migration.tenant_product_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_product_id UUID REFERENCES migration.tenant_vendor_products(id) ON DELETE CASCADE,
  catalog_version_id UUID REFERENCES migration.product_versions_catalog(id) ON DELETE SET NULL,
  version_label VARCHAR(100),
  version_semver VARCHAR(100)
);

CREATE TABLE migration.lifecycle_milestones (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  catalog_version_id UUID REFERENCES migration.product_versions_catalog(id) ON DELETE CASCADE,
  tenant_version_id UUID REFERENCES migration.tenant_product_versions(id) ON DELETE CASCADE,
  milestone_type VARCHAR(50) NOT NULL CHECK (milestone_type IN ('release','end_of_support','end_of_life','extended_support_end')),
  milestone_date DATE NOT NULL,
  source VARCHAR(255),
  provenance JSONB DEFAULT '{}'::jsonb,
  last_checked_at TIMESTAMPTZ
);

CREATE TABLE migration.asset_product_links (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_id UUID NOT NULL REFERENCES migration.assets(id) ON DELETE CASCADE,
  catalog_version_id UUID REFERENCES migration.product_versions_catalog(id) ON DELETE SET NULL,
  tenant_version_id UUID REFERENCES migration.tenant_product_versions(id) ON DELETE SET NULL,
  confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
  matched_by VARCHAR(50),
  UNIQUE (asset_id, COALESCE(catalog_version_id, '00000000-0000-0000-0000-000000000000'::uuid), COALESCE(tenant_version_id, '00000000-0000-0000-0000-000000000000'::uuid))
);
```

Resilience & Compliance
```sql
CREATE TABLE migration.asset_resilience (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_id UUID NOT NULL REFERENCES migration.assets(id) ON DELETE CASCADE,
  rto_minutes INTEGER CHECK (rto_minutes >= 0),
  rpo_minutes INTEGER CHECK (rpo_minutes >= 0),
  sla_json JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE migration.asset_compliance_flags (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_id UUID NOT NULL REFERENCES migration.assets(id) ON DELETE CASCADE,
  compliance_scopes TEXT[] DEFAULT '{}',
  data_classification VARCHAR(50),
  residency VARCHAR(50),
  evidence_refs JSONB DEFAULT '[]'::jsonb
);

CREATE TABLE migration.asset_vulnerabilities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_id UUID NOT NULL REFERENCES migration.assets(id) ON DELETE CASCADE,
  cve_id VARCHAR(50),
  severity VARCHAR(10),
  detected_at TIMESTAMPTZ,
  source VARCHAR(255),
  details JSONB DEFAULT '{}'::jsonb
);
```

Operations & Licensing
```sql
CREATE TABLE migration.maintenance_windows (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_account_id UUID NOT NULL REFERENCES migration.client_accounts(id) ON DELETE CASCADE,
  engagement_id UUID NOT NULL REFERENCES migration.engagements(id) ON DELETE CASCADE,
  scope_type VARCHAR(20) NOT NULL CHECK (scope_type IN ('tenant','application','asset')),
  application_id UUID,
  asset_id UUID,
  name VARCHAR(255) NOT NULL,
  start_time TIMESTAMPTZ NOT NULL,
  end_time TIMESTAMPTZ NOT NULL,
  recurring BOOLEAN DEFAULT FALSE,
  timezone VARCHAR(50)
);

CREATE TABLE migration.blackout_periods (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_account_id UUID NOT NULL REFERENCES migration.client_accounts(id) ON DELETE CASCADE,
  engagement_id UUID NOT NULL REFERENCES migration.engagements(id) ON DELETE CASCADE,
  scope_type VARCHAR(20) NOT NULL CHECK (scope_type IN ('tenant','application','asset')),
  application_id UUID,
  asset_id UUID,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  reason TEXT
);

CREATE TABLE migration.asset_licenses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_id UUID NOT NULL REFERENCES migration.assets(id) ON DELETE CASCADE,
  license_type VARCHAR(100),
  renewal_date DATE,
  contract_reference VARCHAR(255),
  support_tier VARCHAR(50)
);
```

Governance
```sql
CREATE TABLE migration.approval_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_account_id UUID NOT NULL REFERENCES migration.client_accounts(id) ON DELETE CASCADE,
  engagement_id UUID NOT NULL REFERENCES migration.engagements(id) ON DELETE CASCADE,
  entity_type VARCHAR(30) NOT NULL CHECK (entity_type IN ('strategy','wave','schedule','exception')),
  entity_id UUID,
  status VARCHAR(20) NOT NULL CHECK (status IN ('PENDING','APPROVED','REJECTED')) DEFAULT 'PENDING',
  approver_id UUID,
  notes TEXT,
  requested_at TIMESTAMPTZ DEFAULT now(),
  decided_at TIMESTAMPTZ
);

CREATE TABLE migration.migration_exceptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_account_id UUID NOT NULL REFERENCES migration.client_accounts(id) ON DELETE CASCADE,
  engagement_id UUID NOT NULL REFERENCES migration.engagements(id) ON DELETE CASCADE,
  application_id UUID,
  asset_id UUID,
  exception_type VARCHAR(50),
  rationale TEXT,
  risk_level VARCHAR(10),
  approval_request_id UUID REFERENCES migration.approval_requests(id) ON DELETE SET NULL,
  status VARCHAR(20) NOT NULL CHECK (status IN ('OPEN','CLOSED')) DEFAULT 'OPEN'
);
```

Extensions
```sql
ALTER TABLE migration.asset_dependencies
  ADD COLUMN relationship_nature VARCHAR(50),
  ADD COLUMN direction VARCHAR(10) CHECK (direction IN ('upstream','downstream')),
  ADD COLUMN criticality VARCHAR(10) CHECK (criticality IN ('low','medium','high','critical')),
  ADD COLUMN dataflow_type VARCHAR(20) CHECK (dataflow_type IN ('batch','stream','sync','async'));
```

Indexes
```sql
-- Tenant composite indexes (examples)
CREATE INDEX idx_asset_resilience_asset ON migration.asset_resilience(asset_id);
CREATE INDEX idx_asset_product_links_asset ON migration.asset_product_links(asset_id);
CREATE INDEX idx_lifecycle_milestones_catver ON migration.lifecycle_milestones(catalog_version_id);
CREATE INDEX idx_lifecycle_milestones_tenver ON migration.lifecycle_milestones(tenant_version_id);
```

Materialized Views (Optional)
```sql
-- Simplified view combining global catalog and tenant overrides for read paths
CREATE MATERIALIZED VIEW migration.unified_vendor_products AS
SELECT
    COALESCE(tvp.id, vpc.id)               AS id,
    tvp.client_account_id                  AS client_account_id,
    tvp.engagement_id                      AS engagement_id,
    COALESCE(tvp.custom_vendor_name, vpc.vendor_name)  AS vendor_name,
    COALESCE(tvp.custom_product_name, vpc.product_name) AS product_name,
    (tvp.id IS NOT NULL)                   AS is_tenant_override
FROM migration.vendor_products_catalog vpc
LEFT JOIN migration.tenant_vendor_products tvp
  ON tvp.catalog_id = vpc.id;

-- Refresh policy managed by scheduler; consider CONCURRENT REFRESH
```


