import json
import logging
import os
import uuid
from datetime import datetime
from typing import List, Optional
from uuid import UUID

import markdown
from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import require_api_token, require_role
from db import (
    ApiAccessToken,
    ProjectOnboardingProgress,
    Team,
    get_db,
    get_or_create_project_by_name,
    get_or_create_team_by_name,
    resolve_project_id,
    resolve_team_id,
    project_defaults_from_name,
)

logging.basicConfig(level=logging.INFO)

router = APIRouter(prefix="/onboarding")

logger = logging.getLogger("onboarding")


@router.get("/docs", response_class=Response)
def get_onboarding_docs():
    """Get onboarding documentation."""
    content = """
# Onboarding Documentation

Welcome to the API! This guide will help you get started.

## Getting Started

1. First, you'll need to obtain an API token. Contact your administrator to get one.
2. Use the token in the `Authorization` header for all API requests:
   ```
   Authorization: Bearer your-token-here
   ```

## Available Endpoints

- `/healthz`: Check API health
- `/onboarding/docs`: This documentation
- `/onboarding/user_story/{path}`: Get user story documentation
- `/onboarding/progress`: Track your onboarding progress

## Next Steps

1. Check the API health
2. Read the user stories
3. Start using the API endpoints
"""
    return Response(content=markdown.markdown(content), media_type="text/html")


@router.get("/user_story/{path}", response_class=Response)
def get_onboarding_user_story(path: str):
    """Get user story documentation for a specific path."""
    content = f"""
# User Story: {path}

This is a placeholder for the user story documentation for {path}.

## Overview

[Add overview here]

## Steps

1. [Step 1]
2. [Step 2]
3. [Step 3]

## Expected Outcome

[Add expected outcome here]
"""
    return Response(content=markdown.markdown(content), media_type="text/html")


@router.get("/progress/{project_name}")
async def onboarding_progress(
    project_name: str, path: str = "", db: Session = Depends(get_db)
):
    # Use project_name (string) as project_id in onboarding progress
    logger.info(
        f"Fetching onboarding progress for project_id={project_name}, path={path or 'internal_dev'}"
    )
    progress = (
        db.query(ProjectOnboardingProgress)
        .filter(
            ProjectOnboardingProgress.project_id == project_name,
            ProjectOnboardingProgress.path == (path or "internal_dev"),
        )
        .order_by(ProjectOnboardingProgress.timestamp.desc())
        .all()
    )
    logger.info(
        f"Found {len(progress)} onboarding progress records for project_id={project_name}, path={path or 'internal_dev'}"
    )
    if not progress:
        logger.warning(
            f"No onboarding progress found for project_id={project_name}, path={path or 'internal_dev'}"
        )
        raise HTTPException(status_code=404, detail="Project not found")
    return [
        {
            "id": str(step.id),
            "path": step.path,
            "step": step.step,
            "completed": step.completed,
            "details": step.details,
            "timestamp": step.timestamp,
        }
        for step in progress
    ]


@router.patch("/progress/{step_id}")
async def patch_onboarding_progress(
    step_id: str, request: Request, db: Session = Depends(get_db)
):
    step = (
        db.query(ProjectOnboardingProgress)
        .filter(ProjectOnboardingProgress.id == step_id)
        .first()
    )
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    data = await request.json()
    if "completed" in data:
        step.completed = data["completed"]
    if "details" in data:
        step.details = data["details"]
    if "status" in data:
        step.status = data["status"]
    db.commit()
    db.refresh(step)
    return {
        "id": str(step.id),
        "path": step.path,
        "step": step.step,
        "completed": step.completed,
        "details": step.details,
        "timestamp": step.timestamp,
        "status": getattr(step, "status", None),
    }


# NOTE: This endpoint MUST remain public (no authentication required)!
# Do NOT add Depends(require_api_token) or any authentication dependencies here.
# This allows new users/projects to start onboarding without a token.
@router.post("/init")
async def onboarding_init(request: Request, db: Session = Depends(get_db)):
    import traceback
    data = await request.json()
    project_name = data.get("project_name")
    team_name = data.get("team_name")
    path = data.get("path")
    if not project_name or not path:
        raise HTTPException(status_code=400, detail="Missing project_name or path")
    # Always create or get project/team by name, providing sensible defaults
    default_namespace = f"{project_name}/private"
    namespace_prefix = project_name
    project = get_or_create_project_by_name(
        db,
        project_name,
        default_namespace=default_namespace,
        namespace_prefix=namespace_prefix,
    )
    team = get_or_create_team_by_name(db, team_name) if team_name else None
    onboarding_paths_path = os.path.join(os.path.dirname(__file__), "onboarding_paths.json")
    try:
        with open(onboarding_paths_path, "r") as f:
            onboarding_paths = json.load(f)
        if path not in onboarding_paths:
            raise HTTPException(status_code=400, detail="Invalid onboarding path")
        steps = onboarding_paths[path]
        created_steps = []
        for step in steps:
            # Use project_name (string) as project_id in onboarding progress
            existing = db.query(ProjectOnboardingProgress).filter_by(
                project_id=project_name, path=path, step=step, version=1
            ).first()
            if existing:
                created_steps.append({
                    "id": str(existing.id),
                    "path": path,
                    "step": step,
                    "completed": existing.completed
                })
                continue
            progress = ProjectOnboardingProgress(
                project_id=project_name, path=path, step=step, completed=False
            )
            db.add(progress)
            db.flush()
            created_steps.append({
                "id": str(progress.id),
                "path": path,
                "step": step,
                "completed": False
            })
        db.commit()
        return {
            "project_name": project_name,
            "team_name": team_name,
            "steps": created_steps,
            "team_id": str(team.id) if team else None
        }
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Onboarding init failed: {e}\n{tb}")
        raise HTTPException(status_code=500, detail=f"Onboarding init failed: {e}\n{tb}")
