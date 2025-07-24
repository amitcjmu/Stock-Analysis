from typing import List

from app.api.v1.dependencies import get_db
from app.services.workflow_state_service import workflow_state_service
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/")
def get_field_mappings(flow_id: str, db: Session = Depends(get_db)):
    workflow_state = workflow_state_service.get_workflow_state(db, flow_id)
    if not workflow_state or "data_import_id" not in workflow_state.state_details:
        raise HTTPException(
            status_code=404, detail="No active data import found for this flow."
        )

    data_import_id = workflow_state.state_details["data_import_id"]
    # ... (rest of the function uses data_import_id)


@router.post("/")
def update_field_mappings(
    flow_id: str, mappings: List[dict], db: Session = Depends(get_db)
):
    workflow_state = workflow_state_service.get_workflow_state(db, flow_id)
    if not workflow_state or "data_import_id" not in workflow_state.state_details:
        raise HTTPException(
            status_code=404, detail="No active data import found for this flow."
        )

    data_import_id = workflow_state.state_details["data_import_id"]
    # ... (rest of the function uses data_import_id)
