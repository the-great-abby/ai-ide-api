import json
import os
import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from db import (
    Project,
    ProjectOnboardingProgress,
    Team,
    get_db,
    get_or_create_project_by_name,
    get_or_create_team_by_name,
)

public_router = APIRouter()


@public_router.post("/onboarding-init")
async def onboarding_init(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    project_name = data.get("project_name")
    team_name = data.get("team_name")
    description = data.get("description", None)
    path = data.get("path")
    if not project_name or not path:
        raise HTTPException(status_code=400, detail="Missing project_name or path")
    # Validate path
    onboarding_paths_path = os.path.join(
        os.path.dirname(__file__), "onboarding_paths.json"
    )
    with open(onboarding_paths_path, "r") as f:
        onboarding_paths = json.load(f)
    if path not in onboarding_paths:
        raise HTTPException(status_code=400, detail="Invalid onboarding path")
    # Get or create team
    team = None
    if team_name:
        team = get_or_create_team_by_name(db, team_name, description=description)
    # Get or create project
    default_namespace = f"{project_name}/private"
    namespace_prefix = project_name
    project = get_or_create_project_by_name(
        db,
        project_name,
        description=description,
        default_namespace=default_namespace,
        namespace_prefix=namespace_prefix,
    )
    # Create onboarding progress steps
    steps = onboarding_paths[path]
    created_steps = []
    for step in steps:
        progress = ProjectOnboardingProgress(
            project_id=project.id, path=path, step=step, completed=False
        )
        db.add(progress)
        db.flush()
        created_steps.append(
            {"id": str(progress.id), "path": path, "step": step, "completed": False}
        )
    db.commit()
    return JSONResponse(
        status_code=200,
        content={
            "project_id": str(project.id),
            "team_id": str(team.id) if team else None,
            "steps": created_steps,
        },
    )
