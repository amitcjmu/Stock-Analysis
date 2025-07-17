# pgvector Integration Guide for AI Modernize Migration Platform

This document outlines the steps to integrate the `pgvector` extension into the AI Modernize Migration Platform, enabling vector-based storage and querying within the existing PostgreSQL database. The integration supports AI-driven features like semantic search for CMDB assets while maintaining multi-tenant data isolation and compatibility with the platform’s FastAPI, SQLAlchemy, and CrewAI architecture.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Install and Enable pgvector](#install-and-enable-pgvector)
3. [Update Database Schema](#update-database-schema)
4. [Generate and Store Embeddings](#generate-and-store-embeddings)
5. [Update SQLAlchemy Models](#update-sqlalchemy-models)
6. [Implement Vector Queries](#implement-vector-queries)
7. [Integrate with Authentication and Authorization](#integrate-with-authentication-and-authorization)
8. [Update Alembic Migrations](#update-alembic-migrations)
9. [Testing Strategy](#testing-strategy)
10. [Deployment Considerations](#deployment-considerations)
11. [Future Entra SSO Integration](#future-entra-sso-integration)

## Prerequisites
- **PostgreSQL**: Version 12 or higher with `pgvector` support (your existing database, as per `TECHNICAL_ARCHITECTURE.md`).
- **SQLAlchemy**: Version 2.0+ with `psycopg` driver for async support.
- **DeepInfra LLM**: Access to generate embeddings (e.g., via API for text embeddings).
- **Python Libraries**: Install required dependencies (`psycopg2`, `sqlalchemy[postgresql_psycopg2]`, `numpy`).
- **Alembic**: Configured for database migrations (as per your use of SQLAlchemy and Alembic).
- **CrewAI**: Version 0.121.0, for AI agent integration.
- **FastAPI**: For API endpoints and middleware.
- **Docker**: For local development and deployment consistency.

## Install and Enable pgvector

1. **Install pgvector on PostgreSQL**:
   - If using a managed PostgreSQL service (e.g., Railway, as mentioned in `TECHNICAL_ARCHITECTURE.md`), check if `pgvector` is pre-installed or can be enabled via configuration.
   - For self-hosted PostgreSQL:
     ```bash
     # On Ubuntu/Debian
     sudo apt-get update
     sudo apt-get install postgresql-contrib postgresql-15-pgvector

     # Or, build from source
     git clone https://github.com/pgvector/pgvector.git
     cd pgvector
     make
     sudo make install
     ```
   - Enable the extension in your database:
     ```sql
     CREATE EXTENSION IF NOT EXISTS vector;
     ```

2. **Verify Installation**:
   - Connect to your PostgreSQL database and run:
     ```sql
     SELECT * FROM pg_extension WHERE extname = 'vector';
     ```
   - Ensure the `vector` extension is listed.

3. **Update Docker Configuration**:
   - Modify your `docker-compose.yml` to ensure the PostgreSQL container includes `pgvector`:
     ```yaml
     services:
       db:
         image: pgvector/pgvector:pg15
         environment:
           POSTGRES_USER: ${POSTGRES_USER}
           POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
           POSTGRES_DB: ${POSTGRES_DB}
         volumes:
           - postgres_data:/var/lib/postgresql/data
         ports:
           - "5432:5432"
     volumes:
       postgres_data:
     ```

## Update Database Schema

Create a new table to store vector embeddings for CMDB assets, ensuring multi-tenant isolation with `client_account_id` and `engagement_id`. This aligns with your `CLIENT_ACCOUNT_DESIGN.md` requirement for data isolation.

```sql
CREATE TABLE cmdb_asset_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cmdb_asset_id UUID NOT NULL REFERENCES cmdb_assets(id) ON DELETE CASCADE,
    client_account_id UUID NOT NULL REFERENCES client_accounts(id) ON DELETE CASCADE,
    engagement_id UUID NOT NULL REFERENCES engagements(id) ON DELETE CASCADE,
    embedding VECTOR(1536), -- Adjust dimension based on DeepInfra LLM (e.g., 1536 for text-embedding-ada-002)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_asset_embedding UNIQUE (cmdb_asset_id, client_account_id, engagement_id)
);

-- Indexes for performance
CREATE INDEX idx_cmdb_asset_embeddings_client ON cmdb_asset_embeddings(client_account_id);
CREATE INDEX idx_cmdb_asset_embeddings_engagement ON cmdb_asset_embeddings(engagement_id);
CREATE INDEX idx_cmdb_asset_embeddings_hnsw ON cmdb_asset_embeddings USING hnsw (embedding vector_cosine_ops);
```

- **Explanation**:
  - `embedding`: Stores the vector representation (e.g., 1536 dimensions for DeepInfra’s LLM embeddings).
  - `client_account_id` and `engagement_id`: Ensure data isolation by linking embeddings to specific client accounts and engagements.
  - `hnsw` index: Uses Hierarchical Navigable Small World (HNSW) for efficient vector similarity searches with cosine distance.

## Generate and Store Embeddings

Use DeepInfra’s LLM to generate embeddings for CMDB asset data (e.g., descriptions, configurations). Integrate this with your CrewAI agents (e.g., `CMDB Analyst Agent` or `Pattern Recognition Agent`).

1. **Install Dependencies**:
   ```bash
   pip install requests numpy
   ```

2. **Embedding Generation Service**:
   Create a service to generate and store embeddings.

   ```python
   # backend/app/services/embedding_service.py
   import requests
   import numpy as np
   from sqlalchemy.orm import Session
   from app.models.cmdb_asset_embedding import CMDBAssetEmbedding
   from app.services.context_service import ContextService

   class EmbeddingService:
       def __init__(self, db: Session, context: dict):
           self.db = db
           self.context = context
           self.deepinfra_api_key = "your-deepinfra-api-key"  # Store in env variable
           self.embedding_model = "text-embedding-ada-002"  # Adjust as per DeepInfra

       async def generate_embedding(self, text: str) -> np.ndarray:
           """Generate embedding using DeepInfra API."""
           headers = {
               "Authorization": f"Bearer {self.deepinfra_api_key}",
               "Content-Type": "application/json"
           }
           payload = {
               "input": text,
               "model": self.embedding_model
           }
           response = requests.post(
               "https://api.deepinfra.com/v1/embeddings",
               json=payload,
               headers=headers
           )
           response.raise_for_status()
           return np.array(response.json()["data"][0]["embedding"])

       async def store_cmdb_asset_embedding(self, cmdb_asset_id: str, text: str):
           """Store embedding for a CMDB asset."""
           embedding = await self.generate_embedding(text)
           embedding_record = CMDBAssetEmbedding(
               cmdb_asset_id=cmdb_asset_id,
               client_account_id=self.context["client_account_id"],
               engagement_id=self.context.get("engagement_id"),
               embedding=embedding.tolist()
           )
           self.db.add(embedding_record)
           self.db.commit()
           return embedding_record

       async def find_similar_assets(self, query_text: str, top_k: int = 5) -> list:
           """Find similar CMDB assets using vector search."""
           query_embedding = await self.generate_embedding(query_text)
           query = (
               self.db.query(CMDBAssetEmbedding)
               .filter(
                   CMDBAssetEmbedding.client_account_id == self.context["client_account_id"],
                   CMDBAssetEmbedding.engagement_id == self.context.get("engagement_id")
               )
               .order_by(CMDBAssetEmbedding.embedding.cosine_distance(query_embedding))
               .limit(top_k)
           )
           return query.all()
   ```

- **Explanation**:
  - `generate_embedding`: Calls DeepInfra’s embedding API to convert text (e.g., CMDB asset description) into a vector.
  - `store_cmdb_asset_embedding`: Stores the embedding in the `cmdb_asset_embeddings` table, respecting the current context.
  - `find_similar_assets`: Performs a vector similarity search using cosine distance, filtered by client and engagement.

## Update SQLAlchemy Models

Define a SQLAlchemy model for the `cmdb_asset_embeddings` table, compatible with `pgvector`.

1. **Install `pgvector` Python Package**:
   ```bash
   pip install pgvector
   ```

2. **Create Model**:
   ```python
   # backend/app/models/cmdb_asset_embedding.py
   from sqlalchemy import Column, UUID, DateTime, ForeignKey
   from sqlalchemy.ext.declarative import declarative_base
   from pgvector.sqlalchemy import Vector
   from sqlalchemy.sql import func
   import uuid

   Base = declarative_base()

   class CMDBAssetEmbedding(Base):
       __tablename__ = 'cmdb_asset_embeddings'
       
       id = Column(UUID, primary_key=True, default=uuid.uuid4)
       cmdb_asset_id = Column(UUID, ForeignKey('cmdb_assets.id'), nullable=False)
       client_account_id = Column(UUID, ForeignKey('client_accounts.id'), nullable=False)
       engagement_id = Column(UUID, ForeignKey('engagements.id'), nullable=False)
       embedding = Column(Vector(1536))  # Adjust dimension based on DeepInfra model
       created_at = Column(DateTime(timezone=True), server_default=func.now())
       updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
   ```

- **Explanation**:
  - `Vector(1536)`: Uses `pgvector`’s `Vector` type to store embeddings (adjust dimension to match DeepInfra’s model output).
  - Foreign keys ensure integration with your multi-tenant schema.

## Implement Vector Queries

Update the `ContextAwareRepository` to support vector queries, ensuring context-aware filtering.

```python
# backend/app/repositories/cmdb_asset_embedding_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.cmdb_asset_embedding import CMDBAssetEmbedding
from app.repositories.base_repository import ContextAwareRepository

class CMDBAssetEmbeddingRepository(ContextAwareRepository):
    """Repository for CMDB asset embeddings with context awareness."""
    
    def __init__(self, db: Session, context: dict):
        super().__init__(db, context)
    
    def create_embedding(self, cmdb_asset_id: str, embedding: list) -> CMDBAssetEmbedding:
        """Create a new embedding record."""
        return self.create_with_context(CMDBAssetEmbedding, 
            cmdb_asset_id=cmdb_asset_id,
            embedding=embedding
        )
    
    def find_similar_assets(self, query_embedding: list, top_k: int = 5) -> list:
        """Find similar CMDB assets using vector search."""
        query = self.db.query(CMDBAssetEmbedding).filter(
            CMDBAssetEmbedding.client_account_id == self.context['client_account_id']
        )
        if self.context.get('engagement_id'):
            query = query.filter(CMDBAssetEmbedding.engagement_id == self.context['engagement_id'])
        
        query = query.order_by(CMDBAssetEmbedding.embedding.cosine_distance(query_embedding)).limit(top_k)
        return query.all()
```

- **Explanation**:
  - Extends `ContextAwareRepository` to apply `client_account_id` and `engagement_id` filters.
  - Uses `cosine_distance` for vector similarity searches, leveraging `pgvector`’s HNSW index.

## Integrate with Authentication and Authorization

Ensure vector queries respect RBAC and context validation, as defined in your authentication/authorization design.

1. **Update Context Middleware**:
   - The existing `ContextMiddleware` (from `CLIENT_ACCOUNT_DESIGN.md`) injects `client_account_id` and `engagement_id` into the request state. Ensure it’s applied to vector-related endpoints.

2. **Add Permission Checks**:
   - Update `AuthorizationMiddleware` to include permissions for vector operations (e.g., `data.vector_search`).
   - Example:
     ```python
     # backend/app/middleware/authorization_middleware.py
     CLIENT_ACCOUNT_PERMISSIONS = {
         'admin': ['account.manage', 'users.manage', 'engagements.create', 'data.full_access', 'data.vector_search'],
         # ... other roles
     }
     ```

3. **API Endpoint for Vector Search**:
   ```python
   # backend/app/api/v1/endpoints/cmdb.py
   from fastapi import APIRouter, Depends, Request
   from app.services.embedding_service import EmbeddingService
   from app.repositories.cmdb_asset_embedding_repository import CMDBAssetEmbeddingRepository

   router = APIRouter(prefix="/cmdb")

   @router.post("/find-similar-assets", dependencies=[Depends(requires_permission('data.vector_search'))])
   async def find_similar_assets(request: Request, query_text: str, top_k: int = 5):
       """Find similar CMDB assets using vector search."""
       context = request.state.context
       db = request.state.db
       embedding_service = EmbeddingService(db, context)
       similar_assets = await embedding_service.find_similar_assets(query_text, top_k)
       return {"similar_assets": [asset.to_dict() for asset in similar_assets]}
   ```

- **Explanation**:
  - The endpoint uses `EmbeddingService` to generate a query embedding and find similar assets.
  - `requires_permission` ensures only authorized users can perform vector searches.
  - Context filtering ensures data isolation.

## Update Alembic Migrations

Use Alembic to create the `cmdb_asset_embeddings` table and indexes.

1. **Generate Migration**:
   ```bash
   alembic revision --autogenerate -m "Add cmdb_asset_embeddings table"
   ```

2. **Edit Migration Script**:
   ```python
   # alembic/versions/002_add_cmdb_asset_embeddings.py
   from alembic import op
   import sqlalchemy as sa
   from pgvector.sqlalchemy import Vector

   def upgrade():
       op.create_table(
           'cmdb_asset_embeddings',
           sa.Column('id', sa.UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
           sa.Column('cmdb_asset_id', sa.UUID, sa.ForeignKey('cmdb_assets.id', ondelete='CASCADE'), nullable=False),
           sa.Column('client_account_id', sa.UUID, sa.ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=False),
           sa.Column('engagement_id', sa.UUID, sa.ForeignKey('engagements.id', ondelete='CASCADE'), nullable=False),
           sa.Column('embedding', Vector(1536)),
           sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
           sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
           sa.UniqueConstraint('cmdb_asset_id', 'client_account_id', 'engagement_id', name='unique_asset_embedding')
       )
       op.create_index('idx_cmdb_asset_embeddings_client', 'cmdb_asset_embeddings', ['client_account_id'])
       op.create_index('idx_cmdb_asset_embeddings_engagement', 'cmdb_asset_embeddings', ['engagement_id'])
       op.create_index('idx_cmdb_asset_embeddings_hnsw', 'cmdb_asset_embeddings', ['embedding'], postgresql_using='hnsw', postgresql_ops={'embedding': 'vector_cosine_ops'})

   def downgrade():
       op.drop_index('idx_cmdb_asset_embeddings_hnsw', 'cmdb_asset_embeddings')
       op.drop_index('idx_cmdb_asset_embeddings_engagement')
       op.drop_index('idx_cmdb_asset_embeddings_client')
       op.drop_table('cmdb_asset_embeddings')
   ```

3. **Apply Migration**:
   ```bash
   alembic upgrade head
   ```

## Testing Strategy

1. **Unit Tests**:
   - Test `EmbeddingService.generate_embedding` with mock DeepInfra API responses.
   - Test `CMDBAssetEmbeddingRepository.create_embedding` and `find_similar_assets` with sample embeddings.
   - Example:
     ```python
     # tests/backend/test_embedding_service.py
     def test_generate_embedding(mocker, db_session):
         mocker.patch('requests.post', return_value=mock_response([0.1, 0.2, ...]))
         service = EmbeddingService(db_session, {"client_account_id": "uuid"})
         embedding = await service.generate_embedding("test text")
         assert len(embedding) == 1536
     ```

2. **Integration Tests**:
   - Test end-to-end vector search with real PostgreSQL and `pgvector`.
   - Verify context filtering ensures no cross-tenant data leakage.
   - Example: Ensure `find_similar_assets` only returns assets for the current `client_account_id`.

3. **Performance Tests**:
   - Test vector search performance with 10,000+ embeddings.
   - Verify HNSW index improves query speed (<200ms for top_k=5).

4. **Security Tests**:
   - Test RBAC enforcement for vector search endpoints.
   - Verify no unauthorized access to embeddings outside the user’s context.

## Deployment Considerations

1. **Docker Configuration**:
   - Ensure the PostgreSQL container uses the `pgvector/pgvector` image.
   - Update `docker-compose.yml` to include `pgvector` dependencies.

2. **Environment Variables**:
   - Store DeepInfra API key securely:
     ```yaml
     services:
       backend:
         environment:
           - DEEPINFRA_API_KEY=${DEEPINFRA_API_KEY}
     ```

3. **Monitoring**:
   - Monitor `pgvector` query performance using PostgreSQL’s `EXPLAIN ANALYZE`.
   - Track embedding generation latency and errors via FastAPI logs.

4. **Scaling**:
   - Optimize HNSW index parameters (e.g., `m`, `ef_construction`) for large datasets.
   - Consider partitioning the `cmdb_asset_embeddings` table by `client_account_id` for scalability.

## Future Entra SSO Integration

The `pgvector` integration is compatible with future Entra SSO integration:
- **User Profile Embeddings**: Store embeddings of user profiles or roles in `pgvector` to enhance RBAC (e.g., recommend similar access patterns).
- **Context Filtering**: Ensure vector queries continue to respect `client_account_id` and `engagement_id` when Entra users are added.
- **Schema Updates**: Use Alembic to add new vector-based tables (e.g., for user profile embeddings) as needed.

## Example Usage in CrewAI

Integrate `pgvector` with a CrewAI agent for CMDB analysis.

```python
# backend/app/services/tools/cmdb_similarity_tool.py
from crewai import Tool
from app.services.embedding_service import EmbeddingService

class CMDBSimilarityTool(Tool):
    name = "CMDB Similarity Search"
    description = "Finds similar CMDB assets using vector search."
    
    def _run(self, query_text: str, top_k: int = 5, **context) -> list:
        db = context["db"]
        embedding_service = EmbeddingService(db, context)
        similar_assets = embedding_service.find_similar_assets(query_text, top_k)
        return [asset.to_dict() for asset in similar_assets]
```

- **Usage in Agent**:
  ```python
  from crewai import Agent
  cmdb_analyst = Agent(
      role="CMDB Analyst",
      goal="Analyze CMDB data and find similar assets",
      tools=[CMDBSimilarityTool()]
  )
  ```

## Conclusion

This guide provides a comprehensive approach to integrating `pgvector` into the AI Modernize Migration Platform, enabling vector-based features like semantic search for CMDB assets while maintaining multi-tenant isolation and RBAC. By leveraging `pgvector` within PostgreSQL, you avoid the complexity of a separate vector database while enhancing AI-driven capabilities. The integration aligns with your existing FastAPI, SQLAlchemy, and CrewAI architecture and supports future Entra SSO integration.