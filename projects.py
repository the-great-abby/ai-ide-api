import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import require_api_token, require_role
from db import (
    ApiAccessToken,
    Project,
    get_db,
    resolve_project_id,
    resolve_team_id,
    project_defaults_from_name,
)
from utils.serialization import serialize_uuids

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    has_llm_access: bool = False


class ProjectOut(ProjectCreate):
    id: str
    created_at: datetime
    active: bool


@router.post("", response_model=ProjectOut)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    token: ApiAccessToken = Depends(require_role(["admin"])),
):
    """Create a new project."""
    db_project = Project(
        id=str(uuid.uuid4()),
        name=project.name,
        description=project.description,
        has_llm_access=project.has_llm_access,
        active=True,
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return serialize_uuids(db_project.__dict__.copy())


@router.get("", response_model=List[ProjectOut])
def list_projects(
    db: Session = Depends(get_db), token: ApiAccessToken = Depends(require_api_token)
):
    """List all projects."""
    projects = db.query(Project).filter(Project.active == True).all()
    return [serialize_uuids(obj.__dict__.copy()) for obj in projects]


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    token: ApiAccessToken = Depends(require_api_token),
):
    """Get a specific project by UUID or name."""
    try:
        uuid.UUID(project_id)
        resolved_id = resolve_project_id(db, project_id)
    except Exception:
        resolved_id = resolve_project_id(
            db, project_id, **project_defaults_from_name(project_id)
        )
    project = (
        db.query(Project)
        .filter(Project.id == resolved_id, Project.active == True)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return serialize_uuids(project.__dict__.copy())


@router.put("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: str,
    project: ProjectCreate,
    db: Session = Depends(get_db),
    token: ApiAccessToken = Depends(require_role(["admin"])),
):
    """Update a project by UUID or name."""
    try:
        uuid.UUID(project_id)
        resolved_id = resolve_project_id(db, project_id)
    except Exception:
        resolved_id = resolve_project_id(
            db, project_id, **project_defaults_from_name(project_id)
        )
    db_project = (
        db.query(Project)
        .filter(Project.id == resolved_id, Project.active == True)
        .first()
    )
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    db_project.name = project.name
    db_project.description = project.description
    db_project.has_llm_access = project.has_llm_access
    db.commit()
    db.refresh(db_project)
    return serialize_uuids(db_project.__dict__.copy())


@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    token: ApiAccessToken = Depends(require_role(["admin"])),
):
    """Soft delete a project by UUID or name."""
    try:
        uuid.UUID(project_id)
        resolved_id = resolve_project_id(db, project_id)
    except Exception:
        resolved_id = resolve_project_id(
            db, project_id, **project_defaults_from_name(project_id)
        )
    db_project = (
        db.query(Project)
        .filter(Project.id == resolved_id, Project.active == True)
        .first()
    )
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    db_project.active = False
    db.commit()
    return {"status": "success"}
