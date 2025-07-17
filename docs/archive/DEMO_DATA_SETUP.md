# Demo Data Setup Guide

This guide explains how to set up and use the persistent demo data system in the AI Modernize Migration Platform.

## Overview

The demo data system provides persistent, database-backed mock data that replaces hardcoded frontend mock data. This ensures that demo data remains consistent across development sessions and provides a realistic demonstration environment.

## Features

- **Persistent Mock Data**: Database-stored demo data that survives application restarts
- **Multi-Tenant Support**: Data segregation by client account and engagement
- **pgvector Integration**: Vector embeddings for AI-powered asset similarity and auto-tagging
- **Fallback Logic**: Automatically shows mock data when real data is unavailable
- **Azure Migrate Compliance**: Mock data based on real Azure Migrate metadata standards

## Quick Start

### 1. Database Setup

Ensure PostgreSQL is installed with the pgvector extension:

```bash
# Install PostgreSQL and pgvector
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo -u postgres psql -c "CREATE EXTENSION vector;"

# Create database
sudo -u postgres createdb ai_force_migration
```

### 2. Environment Configuration

Copy the environment template and configure:

```bash
cd backend
cp env.example .env
```

Edit `.env` and set the following key variables:

```env
# Demo data configuration
DEMO_DATA=true

# Database configuration
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/ai_force_migration

# Optional: Vector embeddings (for AI features)
DEEPINFRA_API_KEY=your-api-key-here
EMBEDDING_MODEL=text-embedding-ada-002
```

### 3. Install Dependencies

```bash
# Backend dependencies
cd backend
pip install -r requirements.txt

# Frontend dependencies
cd ../
npm install
```

### 4. Run Database Migrations

```bash
cd backend
python -m alembic upgrade head
```

### 5. Initialize Demo Data

```bash
cd backend
python app/scripts/init_db.py
```

This will populate your database with:
- 1 demo client account (Demo Corporation)
- 2 demo users
- 1 demo engagement
- 20+ predefined tags
- 10 demo CMDB assets
- 1 6R analysis
- 4 migration waves
- Vector embeddings for all assets

### 6. Start the Application

```bash
# Start backend
cd backend
python main.py

# Start frontend (in another terminal)
npm run dev
```

## Demo Data Structure

### Mock Assets

The system creates realistic enterprise infrastructure assets:

- **Servers**: Web servers, database servers, application servers
- **Network Devices**: Switches, firewalls, routers
- **Storage Systems**: SAN, NAS storage devices
- **Legacy Systems**: Legacy ERP and monitoring systems
- **Virtual Infrastructure**: VMware vCenter platforms

### Asset Tags

Automatically assigned tags based on Azure Migrate categories:

- **Technology Tags**: Windows Server, Linux, Database Server, Web Server
- **Business Tags**: Customer Facing, Internal Tools, Security
- **Infrastructure Tags**: Virtual Machine, Physical Server, Network Device
- **Migration Tags**: Cloud Ready, Legacy System, High Availability

### 6R Analysis

Complete migration readiness analysis with:

- Asset distribution across 6R strategies (Rehost, Replatform, etc.)
- Cost analysis and potential savings
- Migration timeline and risk assessment
- Detailed recommendations

### Migration Waves

Phased migration approach:

1. **Wave 1**: Development and non-critical systems
2. **Wave 2**: Database and storage systems
3. **Wave 3**: Customer-facing applications
4. **Wave 4**: Legacy system modernization

## API Endpoints

The demo data is accessible through REST API endpoints:

### Assets
- `GET /api/v1/demo/assets` - List all demo assets
- `GET /api/v1/demo/assets/{id}` - Get specific asset
- `GET /api/v1/demo/assets/summary` - Asset summary statistics

### Analysis
- `GET /api/v1/demo/sixr-analyses` - 6R analysis results
- `GET /api/v1/demo/migration-waves` - Migration wave plans

### AI Features
- `POST /api/v1/demo/assets/{id}/similarity-search` - Find similar assets
- `POST /api/v1/demo/assets/text-search` - Search assets by text
- `POST /api/v1/demo/assets/{id}/auto-tag` - Auto-assign tags

### Engagement Info
- `GET /api/v1/demo/engagement-info` - Client and engagement details

## Frontend Integration

### Using the Demo Data Hook

Replace hardcoded mock data in React components:

```typescript
import { useDemoAssets, useDemoAssetsSummary } from '@/hooks/useDemoData';

function AssetsDashboard() {
  const { assets, loading, error } = useDemoAssets();
  const { summary } = useDemoAssetsSummary();

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h1>Assets ({summary?.total_assets})</h1>
      {assets.map(asset => (
        <AssetCard key={asset.id} asset={asset} />
      ))}
    </div>
  );
}
```

### Available Hooks

- `useDemoAssets(filters?)` - Fetch assets with optional filtering
- `useDemoAsset(id)` - Fetch single asset
- `useDemoAssetsSummary()` - Get asset statistics
- `useDemoSixRAnalyses()` - Get 6R analysis data
- `useDemoMigrationWaves()` - Get migration wave data
- `useDemoTags(category?)` - Get tag library
- `useDemoEngagement()` - Get engagement information
- `useSimilaritySearch()` - AI-powered similarity search
- `useDemoDashboard()` - Combined dashboard data

## Configuration Options

### Demo Data Behavior

The `DEMO_DATA` environment variable controls the fallback behavior:

- `DEMO_DATA=true`: Show mock data when real data is unavailable
- `DEMO_DATA=false`: Only show real data, hide mock data

### Customizing Mock Data

Edit `backend/app/scripts/init_db.py` to customize the mock data:

```python
MOCK_DATA = {
    "client_accounts": [{
        "name": "Your Company Name",
        "industry": "Your Industry",
        # ... other fields
    }],
    "cmdb_assets": [
        # Add your custom assets here
    ]
}
```

## AI Features Setup

### Vector Embeddings

For AI-powered features, configure a DeepInfra API key:

```env
DEEPINFRA_API_KEY=your-api-key-here
```

Without an API key, the system uses deterministic mock embeddings for development.

### Auto-Tagging

Assets are automatically tagged based on:

- Operating system (Windows/Linux detection)
- Asset type classification
- Technology stack analysis
- Business function categorization
- Migration readiness assessment

### Similarity Search

Find similar assets using:

- Vector similarity based on asset descriptions
- Technology stack matching
- Configuration similarity
- Business context alignment

## Troubleshooting

### Database Issues

1. **pgvector not available**: Install the pgvector extension
2. **Migration failed**: Ensure database permissions are correct
3. **Connection refused**: Check PostgreSQL service status

### Demo Data Issues

1. **No data shown**: Check `DEMO_DATA=true` in environment
2. **Real data not overriding**: Ensure mock data has `is_mock=true`
3. **Inconsistent data**: Re-run the initialization script

### API Issues

1. **CORS errors**: Check `FRONTEND_URL` and `ALLOWED_ORIGINS` settings
2. **404 errors**: Verify demo endpoints are loaded in main.py
3. **500 errors**: Check backend logs for database connection issues

### Frontend Issues

1. **Hook errors**: Verify API base URL configuration
2. **Loading forever**: Check network tab for API failures
3. **Type errors**: Ensure TypeScript interfaces match API responses

## Development Workflow

### Adding New Mock Data

1. Update the `MOCK_DATA` structure in `init_db.py`
2. Run the initialization script to refresh data
3. Update TypeScript interfaces if needed
4. Test with frontend components

### Extending the API

1. Add new endpoints to `demo_data.py`
2. Update the repository layer for new queries
3. Add corresponding hooks in `useDemoData.ts`
4. Update this documentation

### Database Schema Changes

1. Create new Alembic migration for schema changes
2. Update model classes
3. Modify initialization script for new fields
4. Update API responses and TypeScript interfaces

## Production Considerations

### Performance

- Demo data queries use proper indexing
- Vector searches are optimized with HNSW indexes
- Database connection pooling is configured

### Security

- Demo data is clearly marked with `is_mock=true`
- Multi-tenant isolation prevents data leakage
- API endpoints require proper context headers

### Monitoring

- Health check endpoint: `/api/v1/demo/health`
- Logging includes demo data usage tracking
- Database performance metrics available

## Support

For issues or questions about the demo data system:

1. Check this documentation first
2. Review error logs in the backend console
3. Test API endpoints directly with curl/Postman
4. Verify database connectivity and data presence

## Next Steps

After setting up demo data:

1. Explore the AI-powered features (similarity search, auto-tagging)
2. Customize mock data for your specific use case
3. Integrate with real migration discovery tools
4. Set up user authentication and multi-tenancy
5. Configure production deployment 