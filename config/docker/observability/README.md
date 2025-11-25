# Observability Stack Setup

This directory contains configuration for the observability stack (Grafana, Prometheus, etc.) for the Migration UI Orchestrator.

## Quick Start

### Option 1: Standalone Grafana (Recommended for Development)

Run Grafana in a separate container:

```bash
docker run -d \
  --name grafana \
  --network migration_network \
  -p 9999:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  -e GF_INSTALL_PLUGINS=grafana-clock-panel \
  -v $(pwd)/data/grafana:/var/lib/grafana \
  grafana/grafana:latest
```

**Access**: http://localhost:9999
**Default Credentials**: admin / admin (change on first login)

### PostgreSQL Datasource Configuration

Manual configuration:
1. Navigate to Grafana: http://localhost:9999
2. Login with admin/admin
3. Go to Configuration → Data Sources → Add data source
4. Select PostgreSQL
5. Configure:
   - Name: migration-db
   - Host: postgres:5432 (Docker network) or localhost:5433 (host)
   - Database: migration_db
   - User: postgres
   - Password: postgres
   - SSL Mode: disable
6. Click Save & Test

### Dashboard Installation

1. Navigate to Dashboards → Import
2. Upload /monitoring/grafana/dashboards/intelligent-gap-detection.json
3. Choose datasource: migration-db
4. Click Import

## Accessing Dashboards

Intelligent Gap Detection: http://localhost:9999/d/intelligent-gap-detection/
