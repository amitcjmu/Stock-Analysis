"""
Chat Interface Endpoints.
Handles AI chat interactions with context awareness.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.discovery.persistence import get_processed_assets
from app.core.context import get_user_id
from app.core.database import get_db
from app.services.crewai_flow_service import CrewAIFlowService
from app.services.multi_model_service import multi_model_service

logger = logging.getLogger(__name__)

router = APIRouter()


# This is a placeholder for a proper dependency injection factory
# In a real app, this would be more robust.
def get_crewai_flow_service(db: AsyncSession = Depends(get_db)) -> CrewAIFlowService:
    # This is a simplified way to get the service.
    # In a real application, you might use a more sophisticated service locator
    # or ensure a single instance is created and reused.
    return CrewAIFlowService(db=db)


@router.post("/chat-test")
async def chat_test(
    request: Dict[str, Any],
    user_id: str = Depends(get_user_id),
    crewai_service: CrewAIFlowService = Depends(get_crewai_flow_service),
):
    """
    Test chat interface with context-aware responses about the asset inventory.
    """
    try:
        user_message = request.get("message", "")

        if not user_message:
            raise HTTPException(status_code=400, detail="Message is required")

        # Get current asset context
        all_assets = get_processed_assets()
        context = _build_asset_context(all_assets)

        # Enhanced system prompt with real asset context

        try:
            # Use multi-model service for proper chat with Gemma-3-4b
            response = await multi_model_service.generate_response(
                prompt=user_message,
                task_type="chat",  # Specify task type for model selection
                system_message="You are a helpful AI assistant for the AI Modernize migration platform.",
            )

            # Store message and response
            await save_chat_message(user_id, user_message, "user")
            await save_chat_message(
                user_id, response.get("content", "No response"), "assistant"
            )

            # Return response for POST endpoint
            return response

        except Exception as e:
            logger.error(f"Chat processing error: {e}")
            # Fallback response with context awareness
            fallback_response = _generate_fallback_response(user_message, context)

            return {
                "status": "success",
                "chat_response": fallback_response,
                "model_used": "fallback",
                "timestamp": None,
                "context_used": context,
                "multi_model_service_available": False,
                "error": str(e),
            }

    except Exception as e:
        logger.error(f"Chat test error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    user_id: str = Depends(get_user_id),
    crewai_service: CrewAIFlowService = Depends(get_crewai_flow_service),
):
    # This is a placeholder - in production, you'd fetch this from a database
    return [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there! How can I help you today?"},
    ]


# Helper functions
def _build_asset_context(assets: list) -> str:
    """Build context string from current assets."""
    if not assets:
        return "Currently, your asset inventory shows a completely blank slate – **0 total assets discovered**. You'll need to import CMDB data or discover assets before you can proceed with migration analysis."

    # Count different asset types
    applications = sum(
        1 for asset in assets if "application" in asset.get("asset_type", "").lower()
    )
    servers = sum(
        1 for asset in assets if "server" in asset.get("asset_type", "").lower()
    )
    databases = sum(
        1 for asset in assets if "database" in asset.get("asset_type", "").lower()
    )

    # Count by environment
    environments = {}
    departments = {}

    for asset in assets:
        env = asset.get("environment", "Unknown")
        dept = asset.get("department", "Unknown")
        environments[env] = environments.get(env, 0) + 1
        departments[dept] = departments.get(dept, 0) + 1

    context_parts = [
        f"- **Total Assets**: {len(assets)}",
        f"- **Applications**: {applications}",
        f"- **Servers**: {servers}",
        f"- **Databases**: {databases}",
        f"- **Environments**: {', '.join([f'{env} ({count})' for env, count in environments.items()])}",
        f"- **Departments**: {', '.join([f'{dept} ({count})' for dept, count in departments.items()])}",
    ]

    return "\n".join(context_parts)


def _generate_fallback_response(user_message: str, context: str) -> str:
    """Generate a fallback response based on user message and context."""
    message_lower = user_message.lower()

    # Check if asking about current state/inventory
    if any(
        keyword in message_lower
        for keyword in ["how many", "current", "inventory", "assets", "what do we have"]
    ):
        if "0 total assets" in context:
            return "Currently, your asset inventory shows a completely blank slate – **0 total assets discovered**. To get started with migration planning, you'll need to:\n\n1. **Import CMDB data** using the Discovery tab\n2. **Upload asset inventories** (CSV, Excel, JSON formats supported)\n3. **Run automated discovery** tools to scan your infrastructure\n\nOnce you have asset data, I can help you analyze migration strategies, assess 6R recommendations, and plan your cloud journey!"
        else:
            return f"Based on your current asset inventory:\n\n{context}\n\nYour migration planning can now proceed! I can help you with:\n- **6R Strategy Analysis** for your applications\n- **Migration complexity assessment**\n- **Cloud readiness evaluation**\n- **Dependency mapping and risk analysis**\n\nWhat specific aspect of your migration would you like to explore?"

    # Migration strategy questions
    elif any(
        keyword in message_lower for keyword in ["migrate", "cloud", "6r", "strategy"]
    ):
        if "0 total assets" in context:
            return "To provide migration strategy recommendations, I need asset data first. Please import your CMDB data or asset inventory through the Discovery tab, then I can analyze the best migration approaches (Rehost, Refactor, Rearchitect, etc.) for each application."
        else:
            return f"Great question about migration strategy! With your current inventory of assets, I can help you:\n\n{context}\n\n**Recommended Next Steps:**\n1. Use the **6R Analysis** tab to get AI-powered migration recommendations\n2. Start with **high-business-value, low-complexity** applications\n3. Consider **Rehost** for quick wins, **Refactor** for optimization\n\nWould you like me to guide you through the 6R analysis process?"

    # Technical questions
    elif any(
        keyword in message_lower
        for keyword in ["technical", "complexity", "dependencies"]
    ):
        return "Technical complexity analysis considers factors like:\n- **Technology stack age and supportability**\n- **Application dependencies and integration points**\n- **Data architecture and storage requirements**\n- **Security and compliance constraints**\n\nI can help you assess these factors once you have asset data loaded. The platform uses AI agents to automatically evaluate technical complexity and provide detailed recommendations."

    # General help
    else:
        return f"I'm here to help with your cloud migration planning! Here's what I can assist with:\n\n**Current Status:**\n{context}\n\n**My Capabilities:**\n- 📊 **Asset Analysis**: Review your inventory and identify migration candidates\n- 🎯 **6R Strategy**: Recommend optimal migration approaches (Rehost, Refactor, etc.)\n- 🔍 **Complexity Assessment**: Evaluate technical challenges and dependencies\n- 📈 **Migration Planning**: Help prioritize applications and plan phases\n\nWhat specific area would you like to explore?"


async def get_chat_history(user_id: str, limit: int = 10) -> List[Dict[str, str]]:
    """Retrieve chat history for a user."""
    # This is a placeholder - in production, you'd fetch this from a database
    return [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there! How can I help you today?"},
    ]


async def save_chat_message(user_id: str, message: str, role: str):
    """Save a chat message."""
    # This is a placeholder - in production, you'd save this to a database
    logger.info(f"Saving message for user {user_id}: ({role}) {message}")
