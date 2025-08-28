# AI Embeddings and VectorUtils Restoration

## Critical Issue Discovered
Consolidation incorrectly stubbed out AI functionality, breaking production features.

## VectorUtils Fix (backend/app/utils/vector_utils.py)
```python
# WRONG - Stubbed implementation
class VectorUtils:
    """Stub implementation of VectorUtils - pattern storage disabled"""
    async def store_pattern_embedding(self, *args, **kwargs) -> str:
        return str(uuid.uuid4())  # Returns fake ID!

# CORRECT - Full implementation
from app.models.agent_discovered_patterns import AgentDiscoveredPatterns
from app.services.embedding_service import EmbeddingService

class VectorUtils:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        logger.info("VectorUtils initialized with AgentDiscoveredPatterns model")

    # Full pgvector operations with 1536-dimensional embeddings
    # Handles dimension mismatch: 1024→1536 with padding
```

## DeepInfra Embeddings Fix (backend/app/services/embedding_service.py)
```python
# WRONG - Mock embeddings despite API key
if EMBEDDING_LLM_AVAILABLE and settings.DEEPINFRA_API_KEY:
    # Still used mock because get_embedding_llm() didn't exist!

# CORRECT - Direct API calls
import httpx

class EmbeddingService:
    def __init__(self):
        self.api_key = settings.DEEPINFRA_API_KEY
        self.base_url = "https://api.deepinfra.com/v1/openai"
        self.model = "thenlper/gte-large"  # 1024 dimensions

    async def embed_text(self, text: str) -> List[float]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "input": text}
            )
```

## Missing Function Fix (backend/app/services/llm_config.py)
```python
def get_embedding_llm():
    """Added this missing function that EmbeddingService expected"""
    return {
        "api_key": os.getenv("DEEPINFRA_API_KEY"),
        "model": DEEPINFRA_EMBEDDINGS_MODEL,
        "base_url": "https://api.deepinfra.com/v1/openai",
    }
```

## Verification Commands
```bash
# Test embedding service
docker exec migration_backend python -c "from app.services.embedding_service import embedding_service; print('AI Available:', embedding_service.ai_available)"

# Test VectorUtils
docker exec migration_backend python -c "from app.utils.vector_utils import vector_utils; print('Has embedding service:', hasattr(vector_utils, 'embedding_service'))"
```

## Key Lessons
1. **ALWAYS verify AI features aren't mocked** when DEEPINFRA_API_KEY is set
2. **Check for stubbed implementations** - consolidation may incorrectly simplify
3. **Dimension handling**: thenlper/gte-large = 1024, pgvector configured = 1536
4. **Direct API calls work better** than trying to use CrewAI's LLM class for embeddings
