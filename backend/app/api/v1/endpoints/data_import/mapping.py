from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_db
from app.services.workflow_state_service import workflow_state_service

router = APIRouter()


@router.get("/")
def get_field_mappings(flow_id: str, db: Session = Depends(get_db)):
    workflow_state = workflow_state_service.get_workflow_state(db, flow_id)
    if not workflow_state or "data_import_id" not in workflow_state.state_details:
        raise HTTPException(
            status_code=404, detail="No active data import found for this flow."
        )

    data_import_id = workflow_state.state_details["data_import_id"]  # noqa: F841
    # TODO: Implement field mapping retrieval using data_import_id
    return {
        "message": "Field mappings retrieval not yet implemented",
        "data_import_id": data_import_id,
    }


@router.post("/")
def update_field_mappings(
    flow_id: str, mappings: List[dict], db: Session = Depends(get_db)
):
    workflow_state = workflow_state_service.get_workflow_state(db, flow_id)
    if not workflow_state or "data_import_id" not in workflow_state.state_details:
        raise HTTPException(
            status_code=404, detail="No active data import found for this flow."
        )

    data_import_id = workflow_state.state_details["data_import_id"]  # noqa: F841
    # TODO: Implement field mapping update using data_import_id
    return {
        "message": "Field mappings update not yet implemented",
        "data_import_id": data_import_id,
        "mappings_count": len(mappings),
    }
