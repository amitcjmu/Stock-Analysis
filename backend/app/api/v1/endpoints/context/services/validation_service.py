"""
Validation Service

Business logic for context validation.
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client_account import ClientAccount, Engagement
from app.models.rbac import ClientAccess

from ..models.context_schemas import ValidateContextResponse

logger = logging.getLogger(__name__)


class ValidationService:
    """Service for context validation"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def validate_context(
        self,
        client_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> ValidateContextResponse:
        """
        Validate that the provided context is valid.
        
        Checks:
        - Client exists and is active
        - Engagement exists and belongs to client
        - User has access to client (if user_id provided)
        """
        errors = []
        warnings = []
        
        # Validate client
        if client_id:
            client_valid, client_error = await self._validate_client(client_id)
            if not client_valid:
                errors.append(client_error)
        
        # Validate engagement
        if engagement_id:
            if not client_id:
                errors.append("engagement_id provided without client_id")
            else:
                engagement_valid, engagement_error = await self._validate_engagement(
                    engagement_id, client_id
                )
                if not engagement_valid:
                    errors.append(engagement_error)
        
        # Validate user access
        if user_id and client_id:
            has_access, access_error = await self._validate_user_access(user_id, client_id)
            if not has_access:
                warnings.append(access_error)
        
        return ValidateContextResponse(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    async def _validate_client(self, client_id: str) -> tuple[bool, Optional[str]]:
        """Validate client exists and is active"""
        try:
            client_uuid = UUID(client_id)
            
            query = select(ClientAccount).where(
                and_(
                    ClientAccount.id == client_uuid,
                    ClientAccount.is_active is True
                )
            )
            result = await self.db.execute(query)
            client = result.scalar_one_or_none()
            
            if not client:
                return False, f"Client {client_id} not found or inactive"
            
            return True, None
            
        except ValueError:
            return False, f"Invalid client ID format: {client_id}"
        except Exception as e:
            logger.error(f"Error validating client: {e}")
            return False, f"Error validating client: {str(e)}"
    
    async def _validate_engagement(
        self, 
        engagement_id: str, 
        client_id: str
    ) -> tuple[bool, Optional[str]]:
        """Validate engagement exists and belongs to client"""
        try:
            engagement_uuid = UUID(engagement_id)
            client_uuid = UUID(client_id)
            
            query = select(Engagement).where(
                and_(
                    Engagement.id == engagement_uuid,
                    Engagement.client_account_id == client_uuid,
                    Engagement.is_active is True
                )
            )
            result = await self.db.execute(query)
            engagement = result.scalar_one_or_none()
            
            if not engagement:
                return False, f"Engagement {engagement_id} not found or doesn't belong to client"
            
            return True, None
            
        except ValueError:
            return False, f"Invalid engagement ID format: {engagement_id}"
        except Exception as e:
            logger.error(f"Error validating engagement: {e}")
            return False, f"Error validating engagement: {str(e)}"
    
    async def _validate_user_access(
        self, 
        user_id: str, 
        client_id: str
    ) -> tuple[bool, Optional[str]]:
        """Validate user has access to client"""
        try:
            client_uuid = UUID(client_id)
            
            # Check if user has client access
            query = select(ClientAccess).where(
                and_(
                    ClientAccess.user_profile_id == user_id,
                    ClientAccess.client_account_id == client_uuid,
                    ClientAccess.is_active is True
                )
            )
            result = await self.db.execute(query)
            access = result.scalar_one_or_none()
            
            if not access:
                return False, f"User {user_id} does not have access to client {client_id}"
            
            return True, None
            
        except ValueError:
            return False, "Invalid ID format"
        except Exception as e:
            logger.error(f"Error validating user access: {e}")
            return False, f"Error validating user access: {str(e)}"