# Railway pgvector Service Deployment Guide

## Overview
Railway offers official pgvector templates that provide PostgreSQL with the vector extension pre-installed. This is the proper solution for production deployments requiring vector embeddings.

## Deployment Steps

### 1. Deploy pgvector Template
1. Go to [Railway pgvector template](https://railway.com/deploy/3jJFCA)
2. Click "Deploy Now"
3. Connect your GitHub account if prompted
4. Select your project: `AIForce-assess`
5. Deploy the service

### 2. Alternative: Use PostgreSQL 17 with pgvector
For the latest PostgreSQL version:
1. Go to [Railway pgvector-pg17 template](https://railway.com/deploy/qcuy_M)
2. Follow same deployment steps

### 3. Configure Environment Variables
After deployment, configure your backend to use the new pgvector database:

```bash
# In Railway dashboard, update backend environment variables:
DATABASE_URL=postgresql://postgres:NEW_PASSWORD@NEW_HOST:NEW_PORT/railway
```

### 4. Enable pgvector Extension
Connect to the new database and enable the extension:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 5. Test Vector Functionality
Verify the setup works:

```sql
-- Create test table
CREATE TABLE test_vectors (
    id SERIAL PRIMARY KEY,
    embedding VECTOR(3)
);

-- Insert test data
INSERT INTO test_vectors (embedding) VALUES 
('[1,2,3]'), 
('[4,5,6]');

-- Test vector similarity search
SELECT * FROM test_vectors 
ORDER BY embedding <-> '[3,1,2]' 
LIMIT 5;
```

## Migration Strategy

### Option A: Replace Current Database
1. Deploy new pgvector service
2. Export data from current database
3. Import data to new pgvector database
4. Update DATABASE_URL in backend
5. Remove old database service

### Option B: Dual Database Setup
1. Keep current database for non-vector data
2. Use pgvector database specifically for embeddings
3. Configure backend to use both databases

## Database Schema Updates

After deploying pgvector service, update your models:

```python
# In asset_embeddings.py
from sqlalchemy import Column, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector

class AssetEmbedding(Base):
    __tablename__ = "asset_embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), nullable=False)
    embedding = Column(Vector(1536))  # OpenAI embedding dimension
    created_at = Column(DateTime, default=datetime.utcnow)
```

## Connection Configuration

```python
# In database configuration
VECTOR_DATABASE_URL = os.getenv("VECTOR_DATABASE_URL")
MAIN_DATABASE_URL = os.getenv("DATABASE_URL")

# Create separate engines if using dual setup
vector_engine = create_async_engine(VECTOR_DATABASE_URL)
main_engine = create_async_engine(MAIN_DATABASE_URL)
```

## Benefits of Railway pgvector Template

1. **Pre-configured**: pgvector extension already installed
2. **Production-ready**: Optimized PostgreSQL configuration
3. **Managed**: Automatic backups and updates
4. **Scalable**: Can handle millions of vectors with proper indexing
5. **Cost-effective**: Only pay for what you use

## Performance Optimization

```sql
-- Create HNSW index for fast similarity search
CREATE INDEX ON asset_embeddings 
USING hnsw (embedding vector_cosine_ops);

-- For exact search, create IVFFlat index
CREATE INDEX ON asset_embeddings 
USING ivfflat (embedding vector_l2_ops) 
WITH (lists = 100);
```

## Next Steps

1. Deploy the pgvector template
2. Update your backend configuration
3. Run database migrations
4. Test vector functionality
5. Update application code to use vector search

This approach provides a robust, scalable foundation for AI-powered features in your migration platform. 