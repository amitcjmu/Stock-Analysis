# Railway Deployment Diagnosis & Resolution Plan

## 📋 Executive Summary

After conducting comprehensive testing within the Docker environment, we've identified the root causes of Railway deployment failures and created a clear resolution plan.

### 🎯 Key Findings

**✅ Docker Environment Status: PERFECT**
- All 17 CrewAI agents registered successfully
- Database migrations current (version: `9d6b856ba8a7`)  
- All 35 workflow_states columns present
- CrewAI 0.130.0 installed and functional
- DeepInfra LLM configuration working
- API endpoints responding correctly

**❌ Railway Environment Issues: CRITICAL**
- Database schema constraint errors (UUID vs Integer mismatch)
- Missing CrewAI imports (`DiscoveryFlowService`, `inventory_building_crew`)
- Client context 404 errors
- Potential incomplete database migrations

---

## 🔍 Detailed Analysis

### Docker Environment Test Results

```bash
# Run diagnosis: docker exec migration_backend python scripts/docker_db_diagnosis.py

✅ CrewAI Installation: OK (version 0.130.0)
✅ Discovery Flow Imports: OK (all modules loading)
✅ DeepInfra Config: OK (API key configured)
✅ LLM Configuration: OK (Llama-4-Maverick-17B-128E-Instruct-FP8)
✅ Database Connection: OK (postgres:5432/migration_db)
✅ Table Structure: OK (35 columns in workflow_states)
✅ Migration Version: 9d6b856ba8a7
✅ Agent Registry: 17 agents registered successfully
✅ API Endpoints: All responding correctly
```

### Railway Error Analysis

#### 1. Database Constraint Error
```
psycopg2.errors.DatatypeMismatch: foreign key constraint 
"sixr_analysis_parameters_analysis_id_fkey" cannot be implemented
DETAIL: Key columns "analysis_id" and "id" are of incompatible types: uuid and integer.
```

**Root Cause**: Railway database has outdated schema where `sixr_analyses.id` is still INTEGER instead of UUID.

#### 2. Import Errors
```
cannot import name 'DiscoveryFlowService' from 'app.services.crewai_flows.discovery_flow'
No module named 'app.services.crewai_flows.inventory_building_crew'
```

**Root Cause**: 
- Incorrect import in `dependency_analysis_service.py` (fixed)
- CrewAI package missing from Railway environment

#### 3. Client Context 404s
```
GET /api/v1/clients/11111111-1111-1111-1111-111111111111/engagements → 404
```

**Root Cause**: Database migration issues causing missing client/engagement data.

---

## 🚀 Resolution Plan

### Phase 1: Database Migration Fix (CRITICAL)

#### Step 1: Connect to Railway Database
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and connect
railway login
railway shell

# Or direct connection
railway connect <service-name>
```

#### Step 2: Run Database Migrations
```bash
# Inside Railway shell
cd /app
alembic upgrade head

# Verify migration version
python -c "
from sqlalchemy import create_engine, text
from app.core.config import settings
engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''))
with engine.connect() as conn:
    result = conn.execute(text('SELECT version_num FROM alembic_version;'))
    print(f'Migration version: {result.scalar()}')
"
```

#### Step 3: Verify Schema Integrity
```bash
# Check workflow_states columns
python -c "
from sqlalchemy import create_engine, text
from app.core.config import settings
engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''))
with engine.connect() as conn:
    result = conn.execute(text('''
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'migration' 
        AND table_name = 'workflow_states'
        ORDER BY ordinal_position;
    '''))
    columns = [row[0] for row in result.fetchall()]
    print(f'workflow_states columns: {len(columns)}')
    if len(columns) >= 35:
        print('✅ Schema up to date')
    else:
        print('❌ Schema outdated - needs migration')
"
```

### Phase 2: Package Dependencies

#### Step 1: Verify requirements.txt
Ensure Railway deployment includes all required packages:

```txt
# Core dependencies
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
sqlalchemy[asyncio]>=2.0.23
asyncpg>=0.29.0
alembic>=1.13.1

# CrewAI and AI dependencies  
crewai>=0.130.0
crewai-tools>=0.4.26
openai>=1.3.0
langchain>=0.1.0
langchain-community>=0.0.10

# Data processing
pandas>=2.1.3
numpy>=1.24.3
```

#### Step 2: Check Railway Build Logs
```bash
railway logs --service <backend-service>
```

Look for:
- Package installation failures
- Python module import errors
- Database connection issues during startup

### Phase 3: Environment Configuration

#### Step 1: Verify Railway Environment Variables
```bash
railway variables

# Required variables:
DATABASE_URL=postgresql://...
DEEPINFRA_API_KEY=your_key
CREWAI_ENABLED=true
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app
```

#### Step 2: Test Configuration
```bash
# Inside Railway shell
python scripts/docker_db_diagnosis.py
```

Should show all ✅ results like Docker environment.

### Phase 4: Deployment Verification

#### Step 1: Health Check
```bash
curl https://your-railway-app.railway.app/health
```

Expected response:
```json
{
    "status": "healthy",
    "service": "ai-force-migration-api", 
    "version": "0.2.0",
    "timestamp": "2025-01-27"
}
```

#### Step 2: Agent Status Check
```bash
curl -H "X-Client-Account-Id: 11111111-1111-1111-1111-111111111111" \
     -H "X-Engagement-Id: 22222222-2222-2222-2222-222222222222" \
     https://your-railway-app.railway.app/api/v1/discovery/agents/agent-status
```

Should return agent insights and status data.

---

## 🛠️ Troubleshooting Scripts

### Railway Database Diagnosis Script
```bash
# Upload to Railway and run
railway run python scripts/docker_db_diagnosis.py
```

### Railway Connection Test
```bash
# Compare Railway vs Local database
RAILWAY_DATABASE_URL="postgresql://..." \
railway run python scripts/test_railway_connection.py
```

### Migration Version Check
```bash
railway run python -c "
from sqlalchemy import create_engine, text
from app.core.config import settings
engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''))
with engine.connect() as conn:
    result = conn.execute(text('SELECT version_num FROM alembic_version;'))
    print(f'Current version: {result.scalar()}')
    print('Expected version: 9d6b856ba8a7')
"
```

---

## 🎯 Success Criteria

### Database Migration Success
- [ ] Migration version matches local: `9d6b856ba8a7`
- [ ] workflow_states has 35+ columns
- [ ] All foreign key constraints working
- [ ] No UUID/Integer type mismatches

### CrewAI Integration Success  
- [ ] All 17 agents register successfully
- [ ] No import errors for CrewAI modules
- [ ] DeepInfra LLM configuration working
- [ ] Agent status endpoints responding

### API Functionality Success
- [ ] Health endpoint returns 200
- [ ] Agent status returns insights data
- [ ] Client context resolves correctly
- [ ] No 404 errors on valid endpoints

### Frontend Integration Success
- [ ] Vercel frontend connects to Railway backend
- [ ] CORS configuration allows Vercel domain
- [ ] API calls from frontend succeed
- [ ] Agent monitoring displays correctly

---

## 🚨 Critical Actions Required

### Immediate (Railway Console)
1. **Run Database Migrations**: `alembic upgrade head`
2. **Verify Package Installation**: Check CrewAI in requirements.txt
3. **Restart Railway Service**: After migrations complete

### Verification (Post-Deploy)
1. **Test All Endpoints**: Health, agents, discovery flows
2. **Monitor Logs**: Check for import errors or database issues
3. **Frontend Testing**: Verify Vercel → Railway communication

### Fallback Plan
If Railway issues persist:
1. **Export Railway Database**: Create backup
2. **Fresh Railway Deployment**: Clean deployment with current code
3. **Database Restore**: Import data to new Railway instance

---

## 📊 Environment Comparison

| Component | Docker (Local) | Railway (Production) |
|-----------|----------------|---------------------|
| CrewAI Version | ✅ 0.130.0 | ❌ Missing/Import Errors |
| Migration Version | ✅ 9d6b856ba8a7 | ❌ Outdated Schema |
| Database Schema | ✅ 35 columns | ❌ Missing Columns |
| Agent Registry | ✅ 17 agents | ❌ Import Failures |
| API Endpoints | ✅ All working | ❌ 404/500 errors |
| LLM Configuration | ✅ DeepInfra OK | ❓ Unknown |

**Conclusion**: Railway deployment is significantly behind local Docker environment. Database migrations and package installations are the primary blockers.

---

## 📝 Next Steps

1. **Execute Phase 1** (Database migrations) immediately
2. **Verify Phase 2** (Package dependencies) 
3. **Test Phase 4** (Deployment verification)
4. **Update this document** with Railway-specific results
5. **Create monitoring alerts** for future deployment issues

This diagnosis provides a clear path to resolve Railway deployment issues and achieve parity with the working Docker environment. 