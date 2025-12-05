# pgvector Migrations - NO Schema Prefix (Critical)

**Problem**: Railway deployment failed with `type "public.vector" does not exist` error in migration 145.

**Root Cause**: Migration used explicit schema prefix (`public.vector(1024)`, `public.vector_cosine_ops`) which doesn't work when pgvector extension is not in public schema.

## WRONG Pattern (Causes Railway Failures)

```sql
-- ❌ DON'T do this
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;
embedding public.vector(1024),
USING ivfflat (embedding public.vector_cosine_ops)
```

## CORRECT Pattern (Works on Railway)

```sql
-- ✅ DO this
CREATE EXTENSION IF NOT EXISTS vector;
embedding vector(1024),
USING hnsw (embedding vector_cosine_ops)
```

## Complete Idempotent pgvector Migration

```python
def upgrade() -> None:
    # Ensure pgvector extension (idempotent)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    
    # Create table with vector column
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'help_documents'
            ) THEN
                CREATE TABLE migration.help_documents (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    title VARCHAR(255) NOT NULL,
                    embedding vector(1024),  -- NO public. prefix!
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            END IF;
        END $$;
    """)
    
    # Create vector index (HNSW doesn't need pre-populated data)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND indexname = 'ix_help_documents_embedding'
            ) THEN
                CREATE INDEX ix_help_documents_embedding
                    ON migration.help_documents
                    USING hnsw (embedding vector_cosine_ops);
            END IF;
        END $$;
    """)

def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS migration.ix_help_documents_embedding;")
    op.execute("DROP TABLE IF EXISTS migration.help_documents CASCADE;")
```

## Key Rules

1. **No schema prefix** on vector types: `vector(1024)` not `public.vector(1024)`
2. **No schema prefix** on operators: `vector_cosine_ops` not `public.vector_cosine_ops`
3. **Use HNSW index** instead of ivfflat (doesn't require pre-populated data)
4. **Extension without schema**: `CREATE EXTENSION IF NOT EXISTS vector`

## Reference
- Fixed in commit `7cc7f666a` for migration 145
- File: `backend/alembic/versions/145_create_help_documents_table.py`
