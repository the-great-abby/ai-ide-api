import json
import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import require_api_token, require_role
from db import UseCase, get_db

router = APIRouter(prefix="/use-cases", tags=["use-cases"])


class ExampleWorkflowItem(BaseModel):
    endpoint: str
    method: str
    payload: Optional[dict] = None


class UseCaseModel(BaseModel):
    title: str
    description: str
    example_workflow: List[ExampleWorkflowItem]
    tags: Optional[List[str]] = []
    categories: Optional[List[str]] = []
    submitted_by: Optional[str] = None
    source: Optional[str] = None


class UseCaseOut(UseCaseModel):
    id: str
    status: str
    timestamp: str


def str_to_list(s: str) -> List[str]:
    """Convert comma-separated string to list, omitting empty elements."""
    if not s:
        return []
    return [x.strip() for x in s.split(",") if x.strip()]


def list_to_str(l: List[str]) -> str:
    """Convert list to comma-separated string."""
    return ",".join(l)


def ensure_file(path: str, default):
    """Ensure a file exists with default content if missing."""
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(default, f)


def save_json(path: str, data):
    """Save data as JSON to a file."""
    with open(path, "w") as f:
        json.dump(data, f)


@router.get("", response_model=List[UseCaseOut])
def list_use_cases(db: Session = Depends(get_db)):
    """List all approved use cases."""
    use_cases = (
        db.query(UseCase)
        .filter(UseCase.status == "approved")
        .order_by(UseCase.timestamp.desc())
        .all()
    )
    result = []
    for uc in use_cases:
        data = uc.__dict__.copy()
        data.pop("_sa_instance_state", None)
        data["tags"] = str_to_list(data.get("tags", ""))
        data["categories"] = str_to_list(data.get("categories", ""))
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        result.append(data)
    return result


@router.post("", response_model=UseCaseOut)
def submit_use_case(use_case: UseCaseModel, db: Session = Depends(get_db)):
    """Submit a new use case for approval."""
    db_uc = UseCase(
        id=str(uuid.uuid4()),
        title=use_case.title,
        description=use_case.description,
        example_workflow=[ew.dict() for ew in use_case.example_workflow],
        tags=list_to_str(use_case.tags),
        categories=list_to_str(use_case.categories),
        submitted_by=use_case.submitted_by,
        status="pending",
        source=use_case.source,
    )
    db.add(db_uc)
    db.commit()
    db.refresh(db_uc)
    data = db_uc.__dict__.copy()
    data.pop("_sa_instance_state", None)
    data["tags"] = str_to_list(data.get("tags", ""))
    data["categories"] = str_to_list(data.get("categories", ""))
    if isinstance(data.get("timestamp"), datetime):
        data["timestamp"] = data["timestamp"].isoformat()
    return data


@router.get("/pending", response_model=List[UseCaseOut])
def list_pending_use_cases(db: Session = Depends(get_db)):
    """List all pending use cases."""
    use_cases = (
        db.query(UseCase)
        .filter(UseCase.status == "pending")
        .order_by(UseCase.timestamp.desc())
        .all()
    )
    result = []
    for uc in use_cases:
        data = uc.__dict__.copy()
        data.pop("_sa_instance_state", None)
        data["tags"] = str_to_list(data.get("tags", ""))
        data["categories"] = str_to_list(data.get("categories", ""))
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        result.append(data)
    return result


@router.post("/{use_case_id}/approve", response_model=UseCaseOut)
def approve_use_case(
    use_case_id: str,
    db: Session = Depends(get_db),
    auth=Depends(require_role(["admin", "moderator"])),
):
    """Approve a pending use case."""
    uc = db.query(UseCase).filter(UseCase.id == use_case_id).first()
    if not uc:
        raise HTTPException(status_code=404, detail="Use-case not found.")
    if uc.status == "approved":
        raise HTTPException(status_code=400, detail="Use-case already approved.")
    uc.status = "approved"
    db.commit()
    db.refresh(uc)
    data = uc.__dict__.copy()
    data.pop("_sa_instance_state", None)
    data["tags"] = str_to_list(data.get("tags", ""))
    data["categories"] = str_to_list(data.get("categories", ""))
    if isinstance(data.get("timestamp"), datetime):
        data["timestamp"] = data["timestamp"].isoformat()
    return data


@router.post("/{use_case_id}/reject", response_model=UseCaseOut)
def reject_use_case(
    use_case_id: str,
    db: Session = Depends(get_db),
    auth=Depends(require_role(["admin", "moderator"])),
):
    """Reject a pending use case."""
    uc = db.query(UseCase).filter(UseCase.id == use_case_id).first()
    if not uc:
        raise HTTPException(status_code=404, detail="Use-case not found.")
    if uc.status == "rejected":
        raise HTTPException(status_code=400, detail="Use-case already rejected.")
    uc.status = "rejected"
    db.commit()
    db.refresh(uc)
    data = uc.__dict__.copy()
    data.pop("_sa_instance_state", None)
    data["tags"] = str_to_list(data.get("tags", ""))
    data["categories"] = str_to_list(data.get("categories", ""))
    if isinstance(data.get("timestamp"), datetime):
        data["timestamp"] = data["timestamp"].isoformat()
    return data
