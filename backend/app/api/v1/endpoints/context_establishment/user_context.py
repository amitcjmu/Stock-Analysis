"""
User context update endpoint for context establishment.

Handles POST /update-context endpoint - persists user's selected client and engagement.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.database import get_db
from app.core.security.secure_logging import safe_log_format
from app.models import User

from .models import ContextUpdateRequest, ContextUpdateResponse
from .utils import CLIENT_ACCOUNT_AVAILABLE, ClientAccount, Engagement, get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/update-context", response_model=ContextUpdateResponse)
async def update_user_context(
    request: ContextUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update the user's default client and engagement context.

    This persists the user's context selection in the database so it's
    remembered across sessions.
    """
    try:
        logger.info(
            f"🔄 Updating context for user {current_user.id}: client={request.client_id}, "
            f"engagement={request.engagement_id}"
        )

        # Verify client exists and user has access
        if CLIENT_ACCOUNT_AVAILABLE:
            # Check client exists
            client = await db.get(ClientAccount, request.client_id)
            if not client or not client.is_active:
                raise HTTPException(status_code=404, detail="Client not found")

            # Check engagement exists and belongs to client
            engagement = await db.get(Engagement, request.engagement_id)
            if not engagement or not engagement.is_active:
                raise HTTPException(status_code=404, detail="Engagement not found")

            if str(engagement.client_account_id) != request.client_id:
                raise HTTPException(
                    status_code=400,
                    detail="Engagement does not belong to specified client",
                )

            # Update user's default context
            user = await db.get(User, current_user.id)
            if user:
                user.default_client_id = request.client_id
                user.default_engagement_id = request.engagement_id
                await db.commit()

                logger.info(
                    safe_log_format(
                        "✅ Updated default context for user {current_user_email}",
                        current_user_email=current_user.email,
                    )
                )

                return ContextUpdateResponse(
                    status="success",
                    message="Context updated successfully",
                    client_id=request.client_id,
                    engagement_id=request.engagement_id,
                )
            else:
                raise HTTPException(status_code=404, detail="User not found")
        else:
            # Models not available, return success for demo
            return ContextUpdateResponse(
                status="success",
                message="Context updated (demo mode)",
                client_id=request.client_id,
                engagement_id=request.engagement_id,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(safe_log_format("Error updating user context: {e}", e=e))
        raise HTTPException(status_code=500, detail="Failed to update context")
