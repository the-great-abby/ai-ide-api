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


@router.get("/progress/{project_id}")
async def onboarding_progress(
    project_id: str, path: str = "", db: Session = Depends(get_db)
):
    try:
        project_uuid = UUID(project_id)
    except Exception:
        logger.error(f"Invalid project_id format: {project_id}")
        raise HTTPException(status_code=400, detail="Invalid project_id format")
    logger.info(
        f"Fetching onboarding progress for project_id={project_uuid}, path={path or 'internal_dev'}"
    )
    progress = (
        db.query(ProjectOnboardingProgress)
        .filter(
            ProjectOnboardingProgress.project_id == project_uuid,
            ProjectOnboardingProgress.path == (path or "internal_dev"),
        )
        .order_by(ProjectOnboardingProgress.timestamp.desc())
        .all()
    )
    logger.info(
        f"Found {len(progress)} onboarding progress records for project_id={project_uuid}, path={path or 'internal_dev'}"
    )
    if not progress:
        logger.warning(
            f"No onboarding progress found for project_id={project_uuid}, path={path or 'internal_dev'}"
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
    db.commit()
    db.refresh(step)
    return {
        "id": step.id,
        "path": step.path,
        "step": step.step,
        "completed": step.completed,
        "details": step.details,
        "timestamp": step.timestamp,
    }


@router.post("/init")
async def onboarding_init(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    project_name = data.get("project_name")
    team_name = data.get("team_name")
    path = data.get("path")
    if not project_name or not path:
        raise HTTPException(status_code=400, detail="Missing project_name or path")
    # Get or create team
    team = None
    if team_name:
        team = get_or_create_team_by_name(db, team_name)
    # Get or create project
    default_namespace = f"{project_name}/private"
    namespace_prefix = project_name
    project = get_or_create_project_by_name(
        db,
        project_name,
        default_namespace=default_namespace,
        namespace_prefix=namespace_prefix,
    )
    return {"project_id": str(project.id), "team_id": str(team.id) if team else None}
