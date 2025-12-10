"""
Client CRUD Handler - Write Operations (Create, Update, Delete)
"""

import logging
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.cache_encryption import secure_setattr
from .cascade_delete import cascade_delete_client_data

# bulk_delete_clients is in bulk_operations.py and re-exported via __init__.py
from app.schemas.admin_schemas import (
    AdminSuccessResponse,
    ClientAccountCreate,
    ClientAccountUpdate,
)

# Import models with fallback
try:
    from app.models.client_account import ClientAccount, Engagement

    CLIENT_MODELS_AVAILABLE = True
except ImportError:
    CLIENT_MODELS_AVAILABLE = False
    ClientAccount = None
    Engagement = None

logger = logging.getLogger(__name__)


class ClientCommandOperations:
    """Handler for client write operations (create, update, delete)"""

    @staticmethod
    async def create_client(
        client_data: ClientAccountCreate, db: AsyncSession, admin_user: str
    ) -> AdminSuccessResponse:
        """Create a new client account"""
        try:
            # Import here to avoid circular dependency
            from .queries import ClientQueryOperations

            if not CLIENT_MODELS_AVAILABLE:
                raise HTTPException(
                    status_code=503, detail="Client models not available"
                )

            # Check if client already exists
            existing_query = select(ClientAccount).where(
                ClientAccount.name == client_data.account_name
            )
            result = await db.execute(existing_query)
            existing_client = result.scalar_one_or_none()

            if existing_client:
                raise HTTPException(
                    status_code=400,
                    detail=f"Client account '{client_data.account_name}' already exists",
                )

            # Create new client account
            client = ClientAccount(
                name=client_data.account_name,
                slug=client_data.account_name.lower()
                .replace(" ", "-")
                .replace("&", "and"),
                industry=client_data.industry,
                company_size=client_data.company_size,
                headquarters_location=client_data.headquarters_location,
                primary_contact_name=client_data.primary_contact_name,
                primary_contact_email=client_data.primary_contact_email,
                primary_contact_phone=client_data.primary_contact_phone,
                description=client_data.description,
                subscription_tier=client_data.subscription_tier,
                billing_contact_email=client_data.billing_contact_email,
                settings=client_data.settings or {},
                branding=client_data.branding or {},
                business_objectives={
                    "primary_goals": client_data.business_objectives,
                    "compliance_requirements": client_data.compliance_requirements,
                    "target_cloud_providers": client_data.target_cloud_providers,
                    "business_priorities": client_data.business_priorities,
                },
                it_guidelines=client_data.it_guidelines or {},
                decision_criteria=client_data.decision_criteria or {},
                agent_preferences=client_data.agent_preferences or {},
            )

            db.add(client)
            await db.commit()
            await db.refresh(client)

            # Convert to response format
            response_data = await ClientQueryOperations._convert_client_to_response(
                client, db
            )

            logger.info(
                f"Client account created: {client_data.account_name} by admin {admin_user}"
            )

            return AdminSuccessResponse(
                message=f"Client account '{client_data.account_name}' created successfully",
                data=response_data,
            )

        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating client account: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to create client account: {str(e)}"
            )

    @staticmethod
    async def update_client(  # noqa: C901
        client_id: str,
        update_data: ClientAccountUpdate,
        db: AsyncSession,
        admin_user: str,
    ) -> AdminSuccessResponse:
        """Update client account with enhanced business context support"""
        try:
            # Import here to avoid circular dependency
            from .queries import ClientQueryOperations

            if not CLIENT_MODELS_AVAILABLE:
                raise HTTPException(
                    status_code=503, detail="Client models not available"
                )

            # Debug logging to see what data is being received
            logger.info(
                f"Updating client {client_id} with data: {update_data.dict(exclude_unset=True)}"
            )

            query = select(ClientAccount).where(ClientAccount.id == client_id)
            result = await db.execute(query)
            client = result.scalar_one_or_none()

            if not client:
                raise HTTPException(status_code=404, detail="Client account not found")

            # Convert update data to dict for easier handling
            update_dict = update_data.dict(exclude_unset=True)
            logger.info(f"Update dict: {update_dict}")

            # Field mapping from frontend to database model
            field_mapping = {
                "account_name": "name",  # Frontend sends 'account_name', DB expects 'name'
                "industry": "industry",
                "company_size": "company_size",
                "headquarters_location": "headquarters_location",
                "primary_contact_name": "primary_contact_name",
                "primary_contact_email": "primary_contact_email",
                "primary_contact_phone": "primary_contact_phone",
                "description": "description",
                "subscription_tier": "subscription_tier",
                "billing_contact_email": "billing_contact_email",
                "settings": "settings",
                "branding": "branding",
                "it_guidelines": "it_guidelines",
                "decision_criteria": "decision_criteria",
                "agent_preferences": "agent_preferences",
            }

            # Update basic fields with direct mapping
            for frontend_field, db_field in field_mapping.items():
                if (
                    frontend_field in update_dict
                    and update_dict[frontend_field] is not None
                ):
                    value = update_dict[frontend_field]
                    if hasattr(client, db_field):
                        secure_setattr(client, db_field, value)

            # Handle complex fields that need special processing
            if "business_objectives" in update_dict:
                # Business objectives can be a list or need to be stored in the JSON structure
                current_objectives = client.business_objectives or {}
                if not isinstance(current_objectives, dict):
                    current_objectives = {"primary_goals": []}

                if isinstance(update_dict["business_objectives"], list):
                    current_objectives["primary_goals"] = update_dict[
                        "business_objectives"
                    ]
                else:
                    current_objectives.update(update_dict["business_objectives"])

                client.business_objectives = current_objectives

            if "target_cloud_providers" in update_dict:
                # Store target cloud providers in IT guidelines
                current_it_guidelines = client.it_guidelines or {}
                if not isinstance(current_it_guidelines, dict):
                    current_it_guidelines = {}

                current_it_guidelines["target_cloud_providers"] = update_dict[
                    "target_cloud_providers"
                ]
                client.it_guidelines = current_it_guidelines

            if "business_priorities" in update_dict:
                # Store business priorities in business objectives
                current_objectives = client.business_objectives or {}
                if not isinstance(current_objectives, dict):
                    current_objectives = {}

                current_objectives["business_priorities"] = update_dict[
                    "business_priorities"
                ]
                client.business_objectives = current_objectives

            if "compliance_requirements" in update_dict:
                # Store compliance requirements in business objectives
                current_objectives = client.business_objectives or {}
                if not isinstance(current_objectives, dict):
                    current_objectives = {}

                current_objectives["compliance_requirements"] = update_dict[
                    "compliance_requirements"
                ]
                client.business_objectives = current_objectives

            if "budget_constraints" in update_dict:
                # Store budget constraints in business objectives
                current_objectives = client.business_objectives or {}
                if not isinstance(current_objectives, dict):
                    current_objectives = {}

                current_objectives["budget_constraints"] = update_dict[
                    "budget_constraints"
                ]
                client.business_objectives = current_objectives

            if "timeline_constraints" in update_dict:
                # Store timeline constraints in business objectives
                current_objectives = client.business_objectives or {}
                if not isinstance(current_objectives, dict):
                    current_objectives = {}

                current_objectives["timeline_constraints"] = update_dict[
                    "timeline_constraints"
                ]
                client.business_objectives = current_objectives

            # Update the updated_at timestamp
            client.updated_at = datetime.utcnow()

            await db.commit()
            await db.refresh(client)

            response_data = await ClientQueryOperations._convert_client_to_response(
                client, db
            )

            logger.info(f"Client account updated: {client_id} by admin {admin_user}")

            return AdminSuccessResponse(
                message="Client account updated successfully", data=response_data
            )

        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating client account {client_id}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to update client account: {str(e)}"
            )

    @staticmethod
    async def delete_client(
        client_id: str, db: AsyncSession, admin_user: str
    ) -> AdminSuccessResponse:
        """Delete client account with proper cascade handling for foreign key constraints"""
        try:
            if not CLIENT_MODELS_AVAILABLE:
                raise HTTPException(
                    status_code=503, detail="Client models not available"
                )

            query = select(ClientAccount).where(ClientAccount.id == client_id)
            result = await db.execute(query)
            client = result.scalar_one_or_none()

            if not client:
                raise HTTPException(status_code=404, detail="Client account not found")

            client_name = client.name

            # Handle cascade deletion of related records to avoid foreign key constraints
            try:
                # Perform comprehensive cascade deletion
                await cascade_delete_client_data(db, client_id)

                # Finally delete the client itself
                await db.delete(client)
                await db.commit()

                logger.info(
                    f"Client account deleted with cascade cleanup: {client_name} by admin {admin_user}"
                )

                return AdminSuccessResponse(
                    message=f"Client account '{client_name}' deleted successfully"
                )

            except HTTPException:
                # Re-raise HTTP exceptions
                raise
            except Exception as cascade_error:
                await db.rollback()
                logger.error(
                    f"Error during cascade deletion for client {client_id}: {cascade_error}"
                )

                # If cascade deletion fails, try soft delete instead
                try:
                    client.is_active = False
                    await db.commit()

                    logger.info(
                        f"Client account soft-deleted due to constraints: {client_name} by admin {admin_user}"
                    )

                    return AdminSuccessResponse(
                        message=f"Client account '{client_name}' deactivated (soft delete due to data dependencies)"
                    )

                except Exception as soft_delete_error:
                    await db.rollback()
                    logger.error(
                        f"Error during soft delete for client {client_id}: {soft_delete_error}"
                    )
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to delete client account: Unable to delete due to data dependencies. "
                        "Please contact administrator.",
                    )

        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting client account {client_id}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to delete client account: {str(e)}"
            )
