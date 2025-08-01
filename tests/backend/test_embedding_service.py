#!/usr/bin/env python3
"""
Test script for the embedding service
"""

import asyncio
import sys

# Add the backend directory to the path
sys.path.append("/app")

from app.services.embedding_service import EmbeddingService


async def test_embedding_service():
    """Test the embedding service functionality."""
    print("🧪 Testing Embedding Service with DeepInfra thenlper/gte-large model")
    print("=" * 60)

    service = EmbeddingService()
    print(f"✅ AI Available: {service.ai_available}")

    if service.ai_available:
        print(f"✅ OpenAI Client: {service.openai_client is not None}")

    print("\n📝 Testing single text embedding...")
    text = "server_name"
    try:
        embedding = await service.embed_text(text)
        print(f"✅ Generated embedding for '{text}':")
        print(f"   - Length: {len(embedding)}")
        print(f"   - First 5 values: {embedding[:5]}")
        print(f"   - Data type: {type(embedding[0])}")
    except Exception as e:
        print(f"❌ Error generating embedding: {e}")

    print("\n📝 Testing batch text embeddings...")
    texts = ["ip_address", "operating_system", "memory_gb"]
    try:
        embeddings = await service.embed_texts(texts)
        print(f"✅ Generated {len(embeddings)} embeddings for batch:")
        for i, text in enumerate(texts):
            print(f"   - {text}: {len(embeddings[i])} dimensions")
    except Exception as e:
        print(f"❌ Error generating batch embeddings: {e}")

    print("\n📝 Testing similarity calculation...")
    try:
        text1_emb = await service.embed_text("server_name")
        text2_emb = await service.embed_text("hostname")
        text3_emb = await service.embed_text("database_port")

        similarity1 = service.calculate_cosine_similarity(text1_emb, text2_emb)
        similarity2 = service.calculate_cosine_similarity(text1_emb, text3_emb)

        print("✅ Similarity calculations:")
        print(f"   - 'server_name' vs 'hostname': {similarity1:.3f}")
        print(f"   - 'server_name' vs 'database_port': {similarity2:.3f}")
        print("   - Expected: hostname should be more similar to server_name")
    except Exception as e:
        print(f"❌ Error calculating similarity: {e}")

    print("\n📝 Testing mock embedding fallback...")
    try:
        # Test mock embedding generation
        mock_embedding = service._generate_mock_embedding("test_field")
        print("✅ Mock embedding generated:")
        print(f"   - Length: {len(mock_embedding)}")
        print(
            f"   - Deterministic: {mock_embedding == service._generate_mock_embedding('test_field')}"
        )
    except Exception as e:
        print(f"❌ Error generating mock embedding: {e}")

    print("\n🎯 Embedding Service Test Complete!")


if __name__ == "__main__":
    asyncio.run(test_embedding_service())
