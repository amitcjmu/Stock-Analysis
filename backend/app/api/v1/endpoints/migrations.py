"""
Migration project API endpoints.
Handles CRUD operations for migration projects and related functionality.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

try:
    from sqlalchemy import delete, select, update
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import selectinload

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

    # Create dummy classes for type hints
    class AsyncSession:
        pass

    def select(*args, **kwargs):
        return None

    def update(*args, **kwargs):
        return None

    def delete(*args, **kwargs):
        return None

    def selectinload(*args, **kwargs):
        return None


from app.core.database import get_db
from app.models.migration import Migration, MigrationPhase, MigrationStatus
from app.schemas.migration import (
    MigrationCreate,
    MigrationListResponse,
    MigrationResponse,
    MigrationUpdate,
)
from app.websocket.manager import ConnectionManager

router = APIRouter()

# WebSocket manager for real-time updates
manager = ConnectionManager()


@router.get("/", response_model=List[MigrationListResponse])
async def list_migrations(
    skip: int = 0,
    limit: int = 100,
    status: Optional[MigrationStatus] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all migration projects with optional filtering."""
    query = select(Migration)

    if status:
        query = query.where(Migration.status == status)

    query = query.offset(skip).limit(limit).order_by(Migration.created_at.desc())

    result = await db.execute(query)
    migrations = result.scalars().all()

    return [
        MigrationListResponse(
            id=migration.id,
            name=migration.name,
            status=migration.status,
            current_phase=migration.current_phase,
            progress_percentage=migration.progress_percentage,
            total_assets=migration.total_assets,
            migrated_assets=migration.migrated_assets,
            created_at=migration.created_at,
            target_completion_date=migration.target_completion_date,
        )
        for migration in migrations
    ]


@router.post("/", response_model=MigrationResponse, status_code=status.HTTP_201_CREATED)
async def create_migration(
    migration_data: MigrationCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new migration project."""

    # Create migration instance
    migration = Migration(
        name=migration_data.name,
        description=migration_data.description,
        source_environment=migration_data.source_environment,
        target_environment=migration_data.target_environment,
        migration_strategy=migration_data.migration_strategy,
        start_date=migration_data.start_date,
        target_completion_date=migration_data.target_completion_date,
        settings=migration_data.settings or {},
    )

    db.add(migration)
    await db.commit()
    await db.refresh(migration)

    # Send real-time update
    await manager.send_migration_update(
        migration.id,
        {
            "action": "created",
            "migration": {
                "id": migration.id,
                "name": migration.name,
                "status": migration.status.value,
            },
        },
    )

    return MigrationResponse.from_orm(migration)


@router.get("/{migration_id}", response_model=MigrationResponse)
async def get_migration(migration_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific migration project by ID."""
    query = (
        select(Migration)
        .where(Migration.id == migration_id)
        .options(selectinload(Migration.assets), selectinload(Migration.assessments))
    )

    result = await db.execute(query)
    migration = result.scalar_one_or_none()

    if not migration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Migration with ID {migration_id} not found",
        )

    return MigrationResponse.from_orm(migration)


@router.put("/{migration_id}", response_model=MigrationResponse)
async def update_migration(
    migration_id: int,
    migration_data: MigrationUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a migration project."""
    query = select(Migration).where(Migration.id == migration_id)
    result = await db.execute(query)
    migration = result.scalar_one_or_none()

    if not migration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Migration with ID {migration_id} not found",
        )

    # Update fields
    update_data = migration_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(migration, field, value)

    await db.commit()
    await db.refresh(migration)

    # Send real-time update
    await manager.send_migration_update(
        migration.id,
        {
            "action": "updated",
            "migration": {
                "id": migration.id,
                "name": migration.name,
                "status": migration.status.value,
                "updated_fields": list(update_data.keys()),
            },
        },
    )

    return MigrationResponse.from_orm(migration)


@router.delete("/{migration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_migration(migration_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a migration project."""
    query = select(Migration).where(Migration.id == migration_id)
    result = await db.execute(query)
    migration = result.scalar_one_or_none()

    if not migration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Migration with ID {migration_id} not found",
        )

    await db.delete(migration)
    await db.commit()

    # Send real-time update
    await manager.send_migration_update(
        migration_id, {"action": "deleted", "migration_id": migration_id}
    )


@router.post("/{migration_id}/start")
async def start_migration(migration_id: int, db: AsyncSession = Depends(get_db)):
    """Start a migration project."""
    query = select(Migration).where(Migration.id == migration_id)
    result = await db.execute(query)
    migration = result.scalar_one_or_none()

    if not migration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Migration with ID {migration_id} not found",
        )

    if migration.status != MigrationStatus.PLANNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Migration must be in planning status to start. Current status: {migration.status}",
        )

    migration.status = MigrationStatus.IN_PROGRESS
    await db.commit()

    # Send real-time update
    await manager.send_migration_update(
        migration.id,
        {
            "action": "started",
            "migration": {
                "id": migration.id,
                "name": migration.name,
                "status": migration.status.value,
            },
        },
    )

    return {"message": "Migration started successfully", "migration_id": migration_id}


@router.post("/{migration_id}/pause")
async def pause_migration(migration_id: int, db: AsyncSession = Depends(get_db)):
    """Pause a migration project."""
    query = select(Migration).where(Migration.id == migration_id)
    result = await db.execute(query)
    migration = result.scalar_one_or_none()

    if not migration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Migration with ID {migration_id} not found",
        )

    if migration.status != MigrationStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Can only pause migrations in progress. Current status: {migration.status}",
        )

    migration.status = MigrationStatus.PAUSED
    await db.commit()

    # Send real-time update
    await manager.send_migration_update(
        migration.id,
        {
            "action": "paused",
            "migration": {
                "id": migration.id,
                "name": migration.name,
                "status": migration.status.value,
            },
        },
    )

    return {"message": "Migration paused successfully", "migration_id": migration_id}


@router.post("/{migration_id}/ai-assessment")
async def generate_ai_assessment(migration_id: int, db: AsyncSession = Depends(get_db)):
    """
    Trigger AI-powered assessment for a migration project using CrewAI.
    """
    # This endpoint is temporarily disabled pending service refactoring
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="AI assessment service is currently under maintenance. Please try again later.",
    )
    # query = select(Migration).where(Migration.id == migration_id).options(
    #     selectinload(Migration.assets)
    # )
    # result = await db.execute(query)
    # migration = result.scalar_one_or_none()

    # if not migration:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail=f"Migration with ID {migration_id} not found"
    #     )

    # if not migration.assets:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Migration has no assets to assess."
    #     )

    # # Construct asset data for CrewAI service
    # asset_data = [
    #     {
    #         "id": asset.id,
    #         "name": asset.name,
    #         "asset_type": asset.asset_type,
    #         "technology_stack": asset.technology_stack
    #     }
    #     for asset in migration.assets
    # ]

    # # Asynchronously run the CrewAI assessment flow
    # try:
    #     assessment_results = await crewai_service.run_assessment_flow(
    #         migration_id=migration_id,
    #         asset_data=asset_data
    #     )

    #     # Update the migration project with assessment results (simplified)
    #     # A more robust implementation would update individual assessments
    #     migration.status = MigrationStatus.ASSESSED
    #     await db.commit()

    #     await manager.send_migration_update(
    #         migration.id,
    #         {
    #             "action": "assessment_completed",
    #             "migration_id": migration_id,
    #             "status": "success",
    #             "results_summary": f"Assessed {len(assessment_results)} assets."
    #         }
    #     )

    #     return {
    #         "message": "AI assessment completed successfully.",
    #         "migration_id": migration_id,
    #         "assessment_results": assessment_results
    #     }
    # except Exception as e:
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail=f"An error occurred during AI assessment: {str(e)}"
    #     )


@router.get("/{migration_id}/progress")
async def get_migration_progress(migration_id: int, db: AsyncSession = Depends(get_db)):
    """Get detailed progress information for a migration."""
    query = (
        select(Migration)
        .where(Migration.id == migration_id)
        .options(selectinload(Migration.assets), selectinload(Migration.assessments))
    )
    result = await db.execute(query)
    migration = result.scalar_one_or_none()

    if not migration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Migration with ID {migration_id} not found",
        )

    # Calculate detailed progress metrics
    total_assets = len(migration.assets)
    migrated_assets = sum(
        1 for asset in migration.assets if asset.status.value == "migrated"
    )
    assessed_assets = sum(
        1
        for asset in migration.assets
        if asset.status.value in ["assessed", "planned", "migrating", "migrated"]
    )

    progress_data = {
        "migration_id": migration_id,
        "overall_progress": migration.progress_percentage,
        "phase_progress": {
            "discovery": (
                100 if migration.current_phase != MigrationPhase.DISCOVERY else 50
            ),
            "assess": (
                100
                if migration.current_phase
                not in [MigrationPhase.DISCOVERY, MigrationPhase.ASSESS]
                else (assessed_assets / total_assets * 100 if total_assets > 0 else 0)
            ),
            "plan": (
                100
                if migration.current_phase
                not in [
                    MigrationPhase.DISCOVERY,
                    MigrationPhase.ASSESS,
                    MigrationPhase.PLAN,
                ]
                else 0
            ),
            "execute": migrated_assets / total_assets * 100 if total_assets > 0 else 0,
        },
        "asset_counts": {
            "total": total_assets,
            "discovered": total_assets,
            "assessed": assessed_assets,
            "migrated": migrated_assets,
        },
        "current_phase": migration.current_phase.value,
        "status": migration.status.value,
    }

    return progress_data
