# Railway pgvector Extension Request

## Support Request Template

**Subject**: Request for pgvector Extension on PostgreSQL Database

**Message**:
```
Hello Railway Support Team,

I need the pgvector extension enabled on my PostgreSQL database for my AI Force Migration Platform application.

Project Details:
- Project ID: 63f53835-4113-410f-b764-885dbf70d755
- Service: migrate-ui-orchestrator  
- Database: PostgreSQL 16.8
- Extension Needed: pgvector (vector similarity search)

Use Case:
Our application requires vector embeddings for AI-powered asset analysis and similarity matching. The pgvector extension is essential for:
- Storing and querying high-dimensional embeddings (1536 dimensions)
- Performing similarity searches on asset data
- AI-powered recommendations and clustering

Technical Requirements:
- CREATE EXTENSION vector;
- Support for VECTOR(1536) data type
- Vector similarity functions (cosine distance, etc.)

This is a production application and the vector extension is critical for core functionality.

Please let me know if you need any additional information or if there are alternative solutions you recommend.

Thank you!
```

## Alternative Solutions

### Option 2: Use Railway's Database Templates
Check if Railway offers PostgreSQL templates with pgvector pre-installed:
1. Go to Railway Dashboard
2. Create new Database service
3. Look for "PostgreSQL with Extensions" or "AI/ML" templates

### Option 3: Self-Hosted PostgreSQL with pgvector
Deploy your own PostgreSQL container with pgvector:
1. Create new service with custom Dockerfile
2. Use postgres:16 base image + pgvector installation
3. Configure as separate database service

### Option 4: External Vector Database
Consider using:
- Supabase (PostgreSQL + pgvector)
- Pinecone (managed vector database)
- Weaviate (vector database)
- Qdrant (vector database)

## Immediate Workaround

While waiting for pgvector, temporarily modify the model to use TEXT/JSON for embeddings:

```python
# In asset_embeddings model
embedding = Column(Text)  # Store as JSON string temporarily
```

This allows the application to start while we get proper vector support. 