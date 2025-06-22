# Railway Single Database Migration Plan

## Problem Statement
Currently using dual database setup:
- Main database: Standard PostgreSQL (no pgvector)
- Vector database: PostgreSQL with pgvector extension

This creates complexity in development, testing, and production environments.

## Recommended Solution: Single pgvector Database

### Benefits
1. **Environment Consistency**: Same setup in Docker dev and Railway prod
2. **Simplified Architecture**: One database, one connection pool
3. **Data Integrity**: Proper foreign key relationships
4. **Easier Operations**: Single backup/restore, monitoring, scaling

### Migration Steps

#### 1. Data Export from Current Database
```bash
# Export current data
railway service migrate-ui-orchestrator
pg_dump $DATABASE_URL > current_data_backup.sql

# Or use Railway's backup feature
railway backup create
```

#### 2. Update Environment Variables
```bash
# Point main service to pgvector database
railway variables --set "DATABASE_URL=postgres://postgres:nbxRiVkbnLfyLbO4UWaDe4V~4asYCb4_@switchyard.proxy.rlwy.net:35227/railway"

# Remove the separate vector database URL
railway variables --unset "VECTOR_DATABASE_URL"
```

#### 3. Update Application Code
```python
# Remove dual database configuration
# Use single database for both regular and vector operations

# In database.py - simplify back to single engine
engine = create_async_engine(get_database_url(), ...)
AsyncSessionLocal = async_sessionmaker(engine, ...)

# Remove vector_engine and VectorAsyncSessionLocal
# Use get_db() for all operations
```

#### 4. Import Data to pgvector Database
```bash
# Import existing data to pgvector database
psql $PGVECTOR_DATABASE_URL < current_data_backup.sql
```

#### 5. Create Vector Tables
```sql
-- Create vector tables in the same database
CREATE TABLE asset_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL,  -- Now matches assets.id UUID type
    embedding VECTOR(1536),
    source_text TEXT,
    embedding_model VARCHAR(100) DEFAULT 'text-embedding-3-small',
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
);

-- Create performance indexes
CREATE INDEX idx_asset_embeddings_vector ON asset_embeddings 
USING hnsw (embedding vector_cosine_ops);
```

#### 6. Remove Old Database Service
```bash
# After confirming everything works, remove old database
railway service delete postgres
```

### Docker Development Environment Update

Update `docker-compose.yml`:
```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: migration_db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql

  # Add init script to enable pgvector
  # init.sql:
  # CREATE EXTENSION IF NOT EXISTS vector;
```

### Testing Environment Alignment

All environments will now use:
- PostgreSQL with pgvector extension
- Same database schema
- Same connection patterns
- Same vector operations

### Configuration Changes Required

#### 1. Backend Configuration
```python
# Simplified database.py
def get_database_url() -> str:
    """Single database URL for all operations."""
    return os.getenv("DATABASE_URL")

# Remove vector-specific configurations
# Use single engine and session factory
```

#### 2. Model Updates
```python
# Update asset_embeddings model to use proper foreign key
class AssetEmbedding(Base):
    asset_id = Column(UUID(as_uuid=True), ForeignKey('assets.id'), nullable=False)
    # Now can have proper relationship
    asset = relationship("Asset", back_populates="embeddings")
```

#### 3. Service Layer Simplification
```python
# All services use single database session
async def create_asset_embedding(db: AsyncSession, asset_id: UUID, embedding: List[float]):
    # Single session for both asset lookup and embedding creation
    pass
```

## Migration Timeline

1. **Preparation** (30 minutes)
   - Export current data
   - Test pgvector database setup

2. **Migration** (1 hour)
   - Update environment variables
   - Deploy code changes
   - Import data
   - Test functionality

3. **Cleanup** (15 minutes)
   - Remove old database service
   - Update documentation

## Rollback Plan

If issues occur:
1. Revert environment variables to original DATABASE_URL
2. Keep old database service until migration confirmed
3. Re-deploy previous code version

## Cost Impact

- **Savings**: Remove one database service (~$5-20/month)
- **Performance**: Slightly better (no cross-database queries)
- **Maintenance**: Significantly reduced complexity

## Next Steps

1. Confirm this approach with your team
2. Schedule maintenance window
3. Execute migration steps
4. Update development environment
5. Update documentation and deployment guides 