-- Create Read-Only PostgreSQL User for Grafana
-- Purpose: Security - Grafana should NOT have superuser access
-- Architecture: ADR-031 (lines 561-575)
-- Usage: Run this script in migration_postgres container

-- Create read-only user
-- Generate password with: openssl rand -base64 32
CREATE USER grafana_readonly WITH PASSWORD '<REPLACE_WITH_STRONG_PASSWORD>';

-- CRITICAL: Allow user to bypass Row Level Security (RLS)
-- Without this, RLS policies will filter out all data and dashboards show "No data"
ALTER ROLE grafana_readonly BYPASSRLS;

-- Grant database connection
GRANT CONNECT ON DATABASE migration_db TO grafana_readonly;

-- Grant schema usage
GRANT USAGE ON SCHEMA migration TO grafana_readonly;

-- Grant SELECT on all required tables for dashboards

-- LLM Usage Costs Dashboard
GRANT SELECT ON migration.llm_usage_logs TO grafana_readonly;
GRANT SELECT ON migration.llm_model_pricing TO grafana_readonly;
GRANT SELECT ON migration.llm_usage_summary TO grafana_readonly;

-- MFO Flow Lifecycle Dashboard
GRANT SELECT ON migration.crewai_flow_state_extensions TO grafana_readonly;
GRANT SELECT ON migration.discovery_flows TO grafana_readonly;
GRANT SELECT ON migration.assessment_flows TO grafana_readonly;
GRANT SELECT ON migration.collection_flows TO grafana_readonly;

-- Agent Health Dashboard
GRANT SELECT ON migration.agent_discovered_patterns TO grafana_readonly;
GRANT SELECT ON migration.agent_performance_analytics TO grafana_readonly;

-- Optional: pg_stat_statements (if enabled for performance monitoring)
-- Uncomment if you want to track query performance
-- GRANT SELECT ON pg_stat_statements TO grafana_readonly;

-- Optional: PostgreSQL system views (for infrastructure monitoring)
-- Uncomment if you want to monitor database health
-- GRANT SELECT ON pg_stat_database TO grafana_readonly;
-- GRANT SELECT ON pg_stat_activity TO grafana_readonly;

-- Verify grants (run as postgres superuser)
-- \du grafana_readonly
-- \z migration.*

-- Test connection (from another terminal)
-- psql -U grafana_readonly -d migration_db -h migration_postgres -c "SELECT COUNT(*) FROM migration.llm_usage_logs;"

-- Security Notes:
-- 1. This user has SELECT-only access (no INSERT, UPDATE, DELETE, DROP)
-- 2. Password should be stored in .env.observability (NOT committed to git)
-- 3. Rotate password every 90 days
-- 4. Use strong password: openssl rand -base64 32

-- Deployment Instructions:
-- 1. Copy this file to Azure VM
-- 2. Generate strong password: openssl rand -base64 32
-- 3. Replace <REPLACE_WITH_STRONG_PASSWORD> with generated password
-- 4. Run: docker exec -i migration_postgres psql -U postgres -d migration_db < create-grafana-user.sql
-- 5. Add POSTGRES_GRAFANA_PASSWORD to .env.observability
-- 6. Restart Grafana: docker-compose -f docker-compose.observability.yml restart grafana
