# Cloudflare R2 + Upstash Redis Implementation Guide

## Overview
This guide provides step-by-step instructions for adding Cloudflare R2 object storage and Upstash Redis to the AI Force Migration Platform's Railway + Vercel deployment.

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Vercel       │     │     Railway      │     │  Cloudflare R2  │     │  Upstash Redis  │
├─────────────────┤     ├──────────────────┤     ├─────────────────┤     ├─────────────────┤
│ • Next.js UI    │────▶│ • FastAPI        │────▶│ • Raw CSV/JSON  │     │ • Flow state    │
│ • Edge Functions│     │ • PostgreSQL     │     │ • Large imports │     │ • SSE registry  │
│                 │     │ • Background Jobs│     │ • Archived data │     │ • Pattern cache │
└─────────────────┘     └──────────────────┘     └─────────────────┘     └─────────────────┘
```

## Phase 1: Cloudflare R2 Setup (Week 1)

### Step 1: Create Cloudflare R2 Account

1. Sign up for Cloudflare account at https://dash.cloudflare.com
2. Navigate to R2 in the dashboard
3. Create a new R2 bucket:
   ```
   Bucket name: migration-platform-raw-data
   Location: Automatic (or choose closest to Railway region)
   ```

4. Generate API credentials:
   - Go to R2 > Manage R2 API tokens
   - Create token with "Object Read & Write" permissions
   - Save:
     - Account ID
     - Access Key ID
     - Secret Access Key

### Step 2: Add R2 Configuration to Railway

Add these environment variables to Railway:
```bash
# Cloudflare R2 Configuration
R2_ACCOUNT_ID=your-account-id
R2_ACCESS_KEY_ID=your-access-key-id
R2_SECRET_ACCESS_KEY=your-secret-access-key
R2_BUCKET_NAME=migration-platform-raw-data
R2_ENDPOINT=https://{account_id}.r2.cloudflarestorage.com
```

### Step 3: Install Dependencies

```bash
# Add to requirements.txt
boto3==1.28.84
aioboto3==12.0.0
```

### Step 4: Create R2 Storage Service

Create `backend/app/services/storage/r2_storage.py`:

```python
import boto3
import aioboto3
import gzip
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import hashlib
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class R2StorageService:
    """Service for managing object storage in Cloudflare R2"""
    
    def __init__(self):
        self.account_id = settings.R2_ACCOUNT_ID
        self.access_key = settings.R2_ACCESS_KEY_ID
        self.secret_key = settings.R2_SECRET_ACCESS_KEY
        self.bucket_name = settings.R2_BUCKET_NAME
        self.endpoint_url = f"https://{self.account_id}.r2.cloudflarestorage.com"
        
        # Create session for async operations
        self.session = aioboto3.Session(
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key
        )
    
    async def store_raw_import(
        self, 
        import_id: str,
        client_account_id: int,
        data: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store raw import data in R2"""
        
        try:
            # Prepare data
            json_data = json.dumps(data, default=str)
            compressed_data = gzip.compress(json_data.encode())
            
            # Generate storage path
            timestamp = datetime.utcnow().strftime("%Y/%m/%d")
            key = f"imports/{client_account_id}/{timestamp}/{import_id}/raw_data.json.gz"
            
            # Calculate hash for integrity
            data_hash = hashlib.sha256(compressed_data).hexdigest()
            
            # Upload to R2
            async with self.session.client('s3', endpoint_url=self.endpoint_url) as s3:
                await s3.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=compressed_data,
                    ContentType='application/gzip',
                    Metadata={
                        'import_id': import_id,
                        'client_account_id': str(client_account_id),
                        'record_count': str(len(data)),
                        'data_hash': data_hash,
                        'original_size': str(len(json_data)),
                        'compressed_size': str(len(compressed_data)),
                        **(metadata or {})
                    }
                )
            
            logger.info(f"Stored import {import_id} in R2: {key}")
            
            return {
                'storage_location': key,
                'bucket': self.bucket_name,
                'size_bytes': len(compressed_data),
                'original_size_bytes': len(json_data),
                'compression_ratio': round(len(compressed_data) / len(json_data), 2),
                'record_count': len(data),
                'data_hash': data_hash,
                'storage_class': 'STANDARD'
            }
            
        except Exception as e:
            logger.error(f"Failed to store import {import_id} in R2: {str(e)}")
            raise
    
    async def retrieve_raw_import(
        self, 
        storage_location: str,
        sample_size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve raw import data from R2"""
        
        try:
            async with self.session.client('s3', endpoint_url=self.endpoint_url) as s3:
                # Get object
                response = await s3.get_object(
                    Bucket=self.bucket_name,
                    Key=storage_location
                )
                
                # Read and decompress
                compressed_data = await response['Body'].read()
                json_data = gzip.decompress(compressed_data).decode()
                data = json.loads(json_data)
                
                # Return sample if requested
                if sample_size and sample_size < len(data):
                    return data[:sample_size]
                
                return data
                
        except Exception as e:
            logger.error(f"Failed to retrieve from R2: {storage_location} - {str(e)}")
            raise
    
    async def stream_large_import(
        self,
        storage_location: str,
        chunk_size: int = 1000
    ):
        """Stream large import data in chunks"""
        
        try:
            # First get the full data
            data = await self.retrieve_raw_import(storage_location)
            
            # Yield in chunks
            for i in range(0, len(data), chunk_size):
                yield data[i:i + chunk_size]
                
        except Exception as e:
            logger.error(f"Failed to stream from R2: {storage_location} - {str(e)}")
            raise
    
    async def delete_import(self, storage_location: str) -> bool:
        """Delete import data from R2"""
        
        try:
            async with self.session.client('s3', endpoint_url=self.endpoint_url) as s3:
                await s3.delete_object(
                    Bucket=self.bucket_name,
                    Key=storage_location
                )
            
            logger.info(f"Deleted import from R2: {storage_location}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete from R2: {storage_location} - {str(e)}")
            return False
    
    async def get_import_metadata(self, storage_location: str) -> Dict[str, Any]:
        """Get metadata for stored import"""
        
        try:
            async with self.session.client('s3', endpoint_url=self.endpoint_url) as s3:
                response = await s3.head_object(
                    Bucket=self.bucket_name,
                    Key=storage_location
                )
                
                return {
                    'size_bytes': response['ContentLength'],
                    'last_modified': response['LastModified'],
                    'metadata': response.get('Metadata', {}),
                    'content_type': response.get('ContentType'),
                    'etag': response.get('ETag')
                }
                
        except Exception as e:
            logger.error(f"Failed to get metadata from R2: {storage_location} - {str(e)}")
            raise
    
    async def create_presigned_url(
        self,
        storage_location: str,
        expiration: int = 3600
    ) -> str:
        """Create presigned URL for direct download"""
        
        try:
            async with self.session.client('s3', endpoint_url=self.endpoint_url) as s3:
                url = await s3.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': self.bucket_name,
                        'Key': storage_location
                    },
                    ExpiresIn=expiration
                )
                
                return url
                
        except Exception as e:
            logger.error(f"Failed to create presigned URL: {storage_location} - {str(e)}")
            raise


# Singleton instance
r2_storage = R2StorageService()
```

### Step 5: Update Data Import Handler

Modify `backend/app/api/v1/endpoints/data_import/handlers/import_storage_handler.py`:

```python
from app.services.storage.r2_storage import r2_storage
from app.services.caching.redis_cache import redis_cache

class EnhancedImportStorageHandler(ImportStorageHandler):
    """Enhanced handler with R2 storage and Redis caching"""
    
    async def store_import_data(
        self,
        discovery_flow_id: str,
        import_metadata: DataImportCreate,
        parsed_data: List[Dict[str, Any]]
    ) -> DataImportResponse:
        """Store import data with R2 offloading"""
        
        async with AsyncSessionLocal() as db:
            try:
                # 1. Create import record in PostgreSQL
                import_record = await self._create_import_record(
                    db, discovery_flow_id, import_metadata
                )
                
                # 2. Store raw data in R2 (async)
                r2_result = await r2_storage.store_raw_import(
                    import_id=str(import_record.id),
                    client_account_id=self.client_account_id,
                    data=parsed_data,
                    metadata={
                        'source_type': import_metadata.source_type,
                        'file_name': import_metadata.file_name,
                        'discovery_flow_id': discovery_flow_id
                    }
                )
                
                # 3. Update import record with R2 location
                import_record.storage_location = r2_result['storage_location']
                import_record.storage_metadata = r2_result
                await db.commit()
                
                # 4. Cache sample data in Redis for quick access
                await redis_cache.cache_import_sample(
                    import_id=str(import_record.id),
                    sample_data=parsed_data[:100],  # First 100 records
                    ttl=3600  # 1 hour
                )
                
                # 5. Store only metadata in PostgreSQL raw_import_records
                # This significantly reduces database size
                sample_records = parsed_data[:10]  # Store only first 10 as sample
                
                for idx, record in enumerate(sample_records):
                    raw_record = RawImportRecord(
                        client_account_id=self.client_account_id,
                        data_import_id=import_record.id,
                        raw_data=record,
                        is_sample=True,
                        record_index=idx
                    )
                    db.add(raw_record)
                
                # 6. Store summary statistics
                import_record.total_records = len(parsed_data)
                import_record.field_summary = self._generate_field_summary(parsed_data)
                
                await db.commit()
                
                logger.info(
                    f"Successfully stored import {import_record.id} with "
                    f"{len(parsed_data)} records in R2"
                )
                
                return self._create_response(import_record)
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Failed to store import: {str(e)}")
                raise
```

## Phase 2: Upstash Redis Setup (Week 1)

### Step 1: Create Upstash Account

1. Sign up at https://upstash.com
2. Create a new Redis database:
   - Name: `migration-platform-cache`
   - Region: Choose closest to Railway
   - Type: Regional (not Global)
   - Enable TLS: Yes

3. Copy credentials:
   - UPSTASH_REDIS_REST_URL
   - UPSTASH_REDIS_REST_TOKEN

### Step 2: Add Redis Configuration to Railway

```bash
# Upstash Redis Configuration
UPSTASH_REDIS_URL=https://your-endpoint.upstash.io
UPSTASH_REDIS_TOKEN=your-token
REDIS_ENABLED=true
REDIS_DEFAULT_TTL=3600
```

### Step 3: Install Dependencies

```bash
# Add to requirements.txt
upstash-redis==1.5.0
redis==5.0.1
```

### Step 4: Create Redis Cache Service

Create `backend/app/services/caching/redis_cache.py`:

```python
from typing import Any, Dict, Optional, List, Union
import json
from datetime import datetime, timedelta
from upstash_redis import Redis
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RedisCache:
    """Service for managing Redis cache with Upstash"""
    
    def __init__(self):
        self.enabled = settings.REDIS_ENABLED
        if self.enabled:
            self.client = Redis(
                url=settings.UPSTASH_REDIS_URL,
                token=settings.UPSTASH_REDIS_TOKEN
            )
            self.default_ttl = settings.REDIS_DEFAULT_TTL
        else:
            logger.warning("Redis cache is disabled")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None
            
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {str(e)}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with optional TTL"""
        if not self.enabled:
            return False
            
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value, default=str)
            await self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.enabled:
            return False
            
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {str(e)}")
            return False
    
    # Flow State Caching
    async def cache_flow_state(
        self,
        flow_id: str,
        state: Dict[str, Any],
        ttl: int = 3600
    ) -> bool:
        """Cache flow state for quick access"""
        key = f"flow:state:{flow_id}"
        return await self.set(key, state, ttl)
    
    async def get_flow_state(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Get flow state from cache"""
        key = f"flow:state:{flow_id}"
        return await self.get(key)
    
    # Import Sample Caching
    async def cache_import_sample(
        self,
        import_id: str,
        sample_data: List[Dict[str, Any]],
        ttl: int = 3600
    ) -> bool:
        """Cache import sample for agent analysis"""
        key = f"import:sample:{import_id}"
        return await self.set(key, sample_data, ttl)
    
    async def get_import_sample(
        self,
        import_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Get import sample from cache"""
        key = f"import:sample:{import_id}"
        return await self.get(key)
    
    # Pattern Learning Cache
    async def cache_mapping_pattern(
        self,
        pattern_key: str,
        pattern: Dict[str, Any],
        ttl: int = 86400  # 24 hours
    ) -> bool:
        """Cache field mapping pattern"""
        key = f"pattern:mapping:{pattern_key}"
        return await self.set(key, pattern, ttl)
    
    async def get_mapping_pattern(
        self,
        pattern_key: str
    ) -> Optional[Dict[str, Any]]:
        """Get mapping pattern from cache"""
        key = f"pattern:mapping:{pattern_key}"
        return await self.get(key)
    
    # SSE Connection Registry
    async def register_sse_connection(
        self,
        flow_id: str,
        connection_id: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """Register SSE connection for cross-instance updates"""
        key = f"sse:connections:{flow_id}"
        
        try:
            # Get existing connections
            connections = await self.get(key) or {}
            
            # Add new connection
            connections[connection_id] = {
                **metadata,
                'registered_at': datetime.utcnow().isoformat()
            }
            
            # Store with 1 hour TTL (connections should refresh)
            return await self.set(key, connections, 3600)
            
        except Exception as e:
            logger.error(f"Failed to register SSE connection: {str(e)}")
            return False
    
    async def unregister_sse_connection(
        self,
        flow_id: str,
        connection_id: str
    ) -> bool:
        """Unregister SSE connection"""
        key = f"sse:connections:{flow_id}"
        
        try:
            connections = await self.get(key) or {}
            if connection_id in connections:
                del connections[connection_id]
                return await self.set(key, connections, 3600)
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister SSE connection: {str(e)}")
            return False
    
    async def get_sse_connections(
        self,
        flow_id: str
    ) -> Dict[str, Dict[str, Any]]:
        """Get all SSE connections for a flow"""
        key = f"sse:connections:{flow_id}"
        return await self.get(key) or {}
    
    # Distributed Locking
    async def acquire_lock(
        self,
        resource: str,
        ttl: int = 30
    ) -> Optional[str]:
        """Acquire distributed lock"""
        if not self.enabled:
            return "local-lock"  # Fallback for local development
            
        key = f"lock:{resource}"
        lock_id = f"{datetime.utcnow().timestamp()}"
        
        try:
            # SET NX (set if not exists)
            result = await self.client.set(
                key, 
                lock_id, 
                nx=True,  # Only set if not exists
                ex=ttl    # Expire after TTL
            )
            
            if result:
                return lock_id
            return None
            
        except Exception as e:
            logger.error(f"Failed to acquire lock for {resource}: {str(e)}")
            return None
    
    async def release_lock(
        self,
        resource: str,
        lock_id: str
    ) -> bool:
        """Release distributed lock"""
        if not self.enabled:
            return True
            
        key = f"lock:{resource}"
        
        try:
            # Only delete if we own the lock
            current_lock = await self.get(key)
            if current_lock == lock_id:
                return await self.delete(key)
            return False
            
        except Exception as e:
            logger.error(f"Failed to release lock for {resource}: {str(e)}")
            return False
    
    # Event Broadcasting
    async def publish_event(
        self,
        channel: str,
        event: Dict[str, Any]
    ) -> bool:
        """Publish event for cross-instance communication"""
        if not self.enabled:
            return False
            
        try:
            await self.client.publish(
                channel,
                json.dumps(event, default=str)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to publish event to {channel}: {str(e)}")
            return False
    
    # Performance Metrics
    async def increment_metric(
        self,
        metric_name: str,
        value: int = 1
    ) -> bool:
        """Increment a metric counter"""
        if not self.enabled:
            return False
            
        key = f"metric:{metric_name}:{datetime.utcnow().strftime('%Y%m%d')}"
        
        try:
            await self.client.incrby(key, value)
            # Expire after 7 days
            await self.client.expire(key, 604800)
            return True
        except Exception as e:
            logger.error(f"Failed to increment metric {metric_name}: {str(e)}")
            return False


# Singleton instance
redis_cache = RedisCache()
```

### Step 5: Update Flow State Manager

Modify `backend/app/services/crewai_flows/flow_state_manager.py`:

```python
from app.services.caching.redis_cache import redis_cache

class EnhancedStateManager(StateManager):
    """State manager with Redis caching"""
    
    async def get_state(self) -> Dict[str, Any]:
        """Get state with cache-through pattern"""
        
        # Try cache first
        cached_state = await redis_cache.get_flow_state(self.flow_id)
        if cached_state:
            logger.debug(f"State cache hit for flow {self.flow_id}")
            return cached_state
        
        # Fall back to database
        state = await super().get_state()
        
        # Cache for next time
        await redis_cache.cache_flow_state(self.flow_id, state)
        
        return state
    
    async def update_state(self, updates: Dict[str, Any]):
        """Update state with cache invalidation"""
        
        # Update database
        await super().update_state(updates)
        
        # Invalidate cache
        await redis_cache.delete(f"flow:state:{self.flow_id}")
        
        # Publish update event for SSE
        await redis_cache.publish_event(
            f"flow:updates:{self.flow_id}",
            {
                "type": "state_update",
                "flow_id": self.flow_id,
                "updates": updates,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
```

## Phase 3: Update Agent Tools (Week 2)

### Step 1: Enhanced Schema Analyzer Tool

Update `backend/app/services/tools/schema_analyzer_tool.py`:

```python
from app.services.storage.r2_storage import r2_storage
from app.services.caching.redis_cache import redis_cache

class EnhancedSchemaAnalyzerTool(SchemaAnalyzerTool):
    """Schema analyzer with R2 streaming and Redis caching"""
    
    async def analyze_schema(self, import_id: str) -> Dict[str, Any]:
        """Analyze schema with optimized data access"""
        
        # Check cache first
        cached_analysis = await redis_cache.get(f"schema:analysis:{import_id}")
        if cached_analysis:
            logger.info(f"Using cached schema analysis for {import_id}")
            return cached_analysis
        
        # Get import metadata from PostgreSQL
        import_record = await self._get_import_record(import_id)
        
        if not import_record.storage_location:
            # Fallback to PostgreSQL if no R2 storage
            return await super().analyze_schema(import_id)
        
        # Analyze based on data size
        if import_record.total_records < 10000:
            # Small dataset - load fully
            data = await r2_storage.retrieve_raw_import(
                import_record.storage_location
            )
            analysis = await self._analyze_data(data)
        else:
            # Large dataset - stream and sample
            analysis = await self._analyze_streaming(
                import_record.storage_location,
                import_record.total_records
            )
        
        # Cache results
        await redis_cache.set(
            f"schema:analysis:{import_id}",
            analysis,
            ttl=3600  # 1 hour
        )
        
        return analysis
    
    async def _analyze_streaming(
        self,
        storage_location: str,
        total_records: int
    ) -> Dict[str, Any]:
        """Analyze schema using streaming for large datasets"""
        
        schema_info = {}
        sample_size = min(5000, total_records)
        records_analyzed = 0
        
        async for chunk in r2_storage.stream_large_import(
            storage_location,
            chunk_size=1000
        ):
            for record in chunk:
                self._update_schema_info(schema_info, record)
                records_analyzed += 1
                
                if records_analyzed >= sample_size:
                    break
            
            if records_analyzed >= sample_size:
                break
        
        return {
            "field_info": schema_info,
            "records_analyzed": records_analyzed,
            "total_records": total_records,
            "analysis_type": "streaming_sample"
        }
```

### Step 2: Pattern Learning Integration

Update `backend/app/services/crews/agents/attribute_mapping_agent.py`:

```python
class EnhancedAttributeMappingAgent(AttributeMappingAgent):
    """Attribute mapping with Redis pattern caching"""
    
    async def map_attributes(
        self,
        source_data: Dict,
        target_schema: Dict
    ) -> Dict[str, Any]:
        """Map attributes with pattern caching"""
        
        # Generate pattern key
        pattern_key = self._generate_pattern_key(source_data, target_schema)
        
        # Check cache
        cached_pattern = await redis_cache.get_mapping_pattern(pattern_key)
        if cached_pattern:
            logger.info(f"Using cached mapping pattern: {pattern_key}")
            return cached_pattern
        
        # Perform mapping
        mapping_result = await super().map_attributes(source_data, target_schema)
        
        # Cache successful high-confidence mappings
        if self._is_high_confidence_mapping(mapping_result):
            await redis_cache.cache_mapping_pattern(
                pattern_key,
                mapping_result,
                ttl=86400  # 24 hours
            )
        
        return mapping_result
```

## Phase 4: Migration Strategy (Week 2-3)

### Step 1: Database Migration

Create new migration `backend/alembic/versions/xxx_add_r2_storage_fields.py`:

```python
"""Add R2 storage fields to imports

Revision ID: xxx
Create Date: 2024-xx-xx
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Add storage fields to data_imports
    op.add_column(
        'data_imports',
        sa.Column('storage_location', sa.String(500), nullable=True)
    )
    op.add_column(
        'data_imports',
        sa.Column('storage_metadata', postgresql.JSONB, nullable=True)
    )
    op.add_column(
        'data_imports',
        sa.Column('storage_provider', sa.String(50), default='r2')
    )
    
    # Add sample flag to raw_import_records
    op.add_column(
        'raw_import_records',
        sa.Column('is_sample', sa.Boolean(), default=False)
    )
    op.add_column(
        'raw_import_records',
        sa.Column('record_index', sa.Integer(), nullable=True)
    )
    
    # Create index for sample records
    op.create_index(
        'idx_raw_import_sample',
        'raw_import_records',
        ['data_import_id', 'is_sample']
    )

def downgrade():
    op.drop_index('idx_raw_import_sample', 'raw_import_records')
    op.drop_column('raw_import_records', 'record_index')
    op.drop_column('raw_import_records', 'is_sample')
    op.drop_column('data_imports', 'storage_provider')
    op.drop_column('data_imports', 'storage_metadata')
    op.drop_column('data_imports', 'storage_location')
```

### Step 2: Data Migration Script

Create `backend/scripts/migrate_to_r2.py`:

```python
"""
Script to migrate existing raw data to R2 storage
Run with: python -m scripts.migrate_to_r2
"""

import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models import DataImport, RawImportRecord
from app.services.storage.r2_storage import r2_storage
from app.core.logging import get_logger

logger = get_logger(__name__)


async def migrate_import_to_r2(import_id: str):
    """Migrate a single import to R2"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Get import record
            import_record = await db.get(DataImport, import_id)
            if not import_record:
                logger.error(f"Import {import_id} not found")
                return False
            
            # Skip if already migrated
            if import_record.storage_location:
                logger.info(f"Import {import_id} already migrated")
                return True
            
            # Get all raw records
            result = await db.execute(
                select(RawImportRecord)
                .where(RawImportRecord.data_import_id == import_id)
                .order_by(RawImportRecord.created_at)
            )
            raw_records = result.scalars().all()
            
            if not raw_records:
                logger.warning(f"No raw records for import {import_id}")
                return False
            
            # Extract raw data
            raw_data = [record.raw_data for record in raw_records]
            
            # Store in R2
            r2_result = await r2_storage.store_raw_import(
                import_id=str(import_id),
                client_account_id=import_record.client_account_id,
                data=raw_data,
                metadata={
                    'migration_date': datetime.utcnow().isoformat(),
                    'original_record_count': len(raw_records)
                }
            )
            
            # Update import record
            import_record.storage_location = r2_result['storage_location']
            import_record.storage_metadata = r2_result
            
            # Mark existing records as samples (keep first 10)
            for idx, record in enumerate(raw_records):
                if idx < 10:
                    record.is_sample = True
                    record.record_index = idx
                else:
                    # Delete non-sample records to save space
                    await db.delete(record)
            
            await db.commit()
            
            logger.info(
                f"Successfully migrated import {import_id} "
                f"({len(raw_records)} records) to R2"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate import {import_id}: {str(e)}")
            await db.rollback()
            return False


async def migrate_all_imports(batch_size: int = 10):
    """Migrate all imports to R2 in batches"""
    
    async with AsyncSessionLocal() as db:
        # Get all imports without R2 storage
        result = await db.execute(
            select(DataImport)
            .where(DataImport.storage_location.is_(None))
            .order_by(DataImport.created_at.desc())
        )
        imports = result.scalars().all()
        
        logger.info(f"Found {len(imports)} imports to migrate")
        
        # Process in batches
        for i in range(0, len(imports), batch_size):
            batch = imports[i:i + batch_size]
            
            # Migrate batch concurrently
            tasks = [
                migrate_import_to_r2(str(imp.id))
                for imp in batch
            ]
            
            results = await asyncio.gather(*tasks)
            
            success_count = sum(1 for r in results if r)
            logger.info(
                f"Batch {i//batch_size + 1}: "
                f"{success_count}/{len(batch)} successful"
            )
            
            # Small delay between batches
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(migrate_all_imports())
```

## Phase 5: Monitoring and Optimization (Week 3)

### Step 1: Add Performance Monitoring

Create `backend/app/services/monitoring/storage_metrics.py`:

```python
from app.services.caching.redis_cache import redis_cache
from app.core.logging import get_logger

logger = get_logger(__name__)


class StorageMetrics:
    """Monitor storage performance and usage"""
    
    @staticmethod
    async def track_r2_operation(
        operation: str,
        size_bytes: int,
        duration_ms: float,
        success: bool
    ):
        """Track R2 operation metrics"""
        
        # Increment counters
        metric_base = f"r2:{operation}"
        
        if success:
            await redis_cache.increment_metric(f"{metric_base}:success")
        else:
            await redis_cache.increment_metric(f"{metric_base}:failure")
        
        # Track size
        await redis_cache.increment_metric(
            f"{metric_base}:bytes",
            size_bytes
        )
        
        # Log for analysis
        logger.info(
            f"R2 {operation}: {size_bytes} bytes in {duration_ms}ms "
            f"({'success' if success else 'failure'})"
        )
    
    @staticmethod
    async def track_cache_operation(
        operation: str,
        cache_hit: bool,
        key: str
    ):
        """Track cache hit/miss rates"""
        
        metric = f"cache:{operation}:{'hit' if cache_hit else 'miss'}"
        await redis_cache.increment_metric(metric)
        
        if not cache_hit:
            logger.debug(f"Cache miss for {operation}: {key}")
```

### Step 2: Add Health Checks

Update `backend/app/api/v1/endpoints/health.py`:

```python
@router.get("/health/storage")
async def storage_health():
    """Check storage services health"""
    
    health_status = {
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check R2
    try:
        # Try to get bucket metadata
        test_key = "health-check/test.txt"
        await r2_storage.store_raw_import(
            "health-check",
            0,
            [{"test": "data"}]
        )
        await r2_storage.delete_import(test_key)
        
        health_status["services"]["r2"] = {
            "status": "healthy",
            "endpoint": r2_storage.endpoint_url
        }
    except Exception as e:
        health_status["services"]["r2"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check Redis
    try:
        await redis_cache.set("health:check", "ok", ttl=10)
        value = await redis_cache.get("health:check")
        
        health_status["services"]["redis"] = {
            "status": "healthy" if value == "ok" else "degraded"
        }
    except Exception as e:
        health_status["services"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Overall status
    all_healthy = all(
        s["status"] == "healthy"
        for s in health_status["services"].values()
    )
    
    health_status["overall"] = "healthy" if all_healthy else "degraded"
    
    return health_status
```

## Production Deployment Checklist

### Pre-Deployment
- [ ] Create Cloudflare R2 bucket and get credentials
- [ ] Create Upstash Redis database and get credentials
- [ ] Add all environment variables to Railway
- [ ] Test R2 connectivity from Railway region
- [ ] Verify Redis latency is acceptable

### Deployment Steps
1. Deploy database migration first
2. Deploy backend with new storage services
3. Run migration script for existing data
4. Monitor metrics and performance
5. Gradually increase usage

### Post-Deployment Monitoring
- [ ] Monitor R2 bandwidth usage
- [ ] Track Redis memory usage
- [ ] Check cache hit rates
- [ ] Verify backup strategies
- [ ] Set up alerts for failures

## Cost Optimization Tips

### Cloudflare R2
- Use lifecycle rules to move old data to infrequent access
- Compress all data before storage
- Clean up orphaned objects regularly

### Upstash Redis
- Use appropriate TTLs for all cached data
- Monitor memory usage and adjust cache strategies
- Use Redis only for hot data

### PostgreSQL
- After migration, vacuum tables to reclaim space
- Update table statistics for query optimization
- Consider partitioning for remaining data

## Security Considerations

### R2 Security
- Never expose bucket directly
- Use presigned URLs with short expiration
- Encrypt sensitive data before storage
- Regularly rotate access keys

### Redis Security
- Always use TLS connections
- Don't store sensitive data unencrypted
- Set appropriate TTLs to limit exposure
- Monitor for unusual access patterns

## Rollback Plan

If issues arise:

1. **Disable R2 Storage**:
   ```bash
   # Set in Railway
   R2_ENABLED=false
   ```

2. **Disable Redis Cache**:
   ```bash
   # Set in Railway
   REDIS_ENABLED=false
   ```

3. **Revert Code**:
   - Deploy previous version
   - Data remains in PostgreSQL

4. **Data Recovery**:
   - All data is still in PostgreSQL
   - R2 data can be retrieved if needed

This implementation provides a robust, scalable solution for handling large data imports while maintaining compatibility with your existing Railway + Vercel deployment.