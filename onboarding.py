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
import secrets

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
    # Map onboarding path names to markdown files
    path_map = {
        "internal_dev": "ONBOARDING_INTERNAL.md",
        "external_project": "ONBOARDING_EXTERNAL.md",
        "memory_onboarding": "FIRST_MEMORY_ONBOARDING.md",
        "test_path": "ONBOARDING.md",
    }
    filename = path_map.get(path)
    if not filename or not os.path.exists(filename):
        return Response(
            f"<h1>Not Found</h1><p>No onboarding documentation found for path: {path}</p>",
            status_code=404,
            media_type="text/html",
        )
    with open(filename, "r", encoding="utf-8") as f:
        md_content = f.read()
    html_content = markdown.markdown(md_content, extensions=["fenced_code", "tables"])
    return Response(html_content, media_type="text/html")


@router.get("/progress/{project_name}")
async def onboarding_progress(
    project_name: str, path: str = "", db: Session = Depends(get_db)
):
    logger.info(
        f"Fetching onboarding progress for project_id={project_name}, path={path or 'internal_dev'}"
    )
    # Load onboarding_paths to get doc_links
    onboarding_paths_path = os.path.join(
        os.path.dirname(__file__), "onboarding_paths.json"
    )
    with open(onboarding_paths_path, "r") as f:
        onboarding_paths = json.load(f)
    path_entry = None
    if isinstance(onboarding_paths, dict) and "paths" in onboarding_paths:
        for entry in onboarding_paths["paths"]:
            if entry.get("name") == (path or "internal_dev"):
                path_entry = entry
                break
    doc_links = {}
    if path_entry and "steps" in path_entry:
        for step in path_entry["steps"]:
            instruction = (
                step["instruction"]
                if isinstance(step, dict) and "instruction" in step
                else step
            )
            doc_link = step.get("doc_link") if isinstance(step, dict) else None
            doc_links[instruction] = doc_link
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
    steps_out = [
        {
            "id": str(step.id),
            "path": step.path,
            "instruction": step.step,
            "doc_link": doc_links.get(step.step),
            "completed": step.completed,
            "details": step.details,
            "timestamp": step.timestamp,
            "status": getattr(step, "status", "not_started"),
        }
        for step in progress
    ]
    # If all steps are completed, add a congratulatory message
    all_completed = all(s.get("status") == "completed" for s in steps_out)
    response = {"steps": steps_out}
    if all_completed and steps_out:
        response[
            "congratulations"
        ] = "Congratulations! All onboarding steps are complete. Welcome aboard!"
    return response


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
    allowed_statuses = [
        "not_started",
        "in_progress",
        "completed",
        "skipped",
        "needs_help",
    ]
    if "completed" in data:
        step.completed = data["completed"]
        if data["completed"]:
            step.status = "completed"
    if "details" in data:
        step.details = data["details"]
    if "status" in data:
        if data["status"] not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {data['status']}. Allowed: {allowed_statuses}",
            )
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
        "status": getattr(step, "status", "not_started"),
    }


# NOTE: This endpoint MUST remain public (no authentication required)!
# Do NOT add Depends(require_api_token) or any authentication dependencies here.
# This allows new users/projects to start onboarding without a token.
@router.post("/init")
async def onboarding_init(request: Request, db: Session = Depends(get_db)):
    import traceback

    try:
        body = await request.body()
        if not body:
            data = {}
        else:
            data = await request.json()
    except Exception:
        data = {}

    project_name = data.get("project_name")
    team_name = data.get("team_name")
    # Accept 'journey' as preferred, fallback to 'path' for backward compatibility
    journey = data.get("journey") or data.get("path")
    pirate_mode = data.get("pirate_mode", False)
    # Strictly require non-empty project_name and journey
    if (
        not isinstance(project_name, str)
        or not project_name.strip()
        or not isinstance(journey, str)
        or not journey.strip()
    ):
        raise HTTPException(
            status_code=400,
            detail="Missing project_name or journey (must be non-empty strings)",
        )
    project_name = project_name.strip()
    journey = journey.strip()
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
    onboarding_paths_path = os.path.join(
        os.path.dirname(__file__), "onboarding_paths.json"
    )
    try:
        with open(onboarding_paths_path, "r") as f:
            onboarding_paths = json.load(f)
        # Support new structure: onboarding_paths['paths'] is a list of dicts with 'name' and 'steps'
        path_entry = None
        valid_journeys = []
        if isinstance(onboarding_paths, dict) and "paths" in onboarding_paths:
            for entry in onboarding_paths["paths"]:
                valid_journeys.append(entry.get("name"))
                if entry.get("name") == journey:
                    path_entry = entry
                    break
        if not path_entry or "steps" not in path_entry:
            raise HTTPException(status_code=400, detail=f"Invalid onboarding journey. Valid options are: {', '.join(valid_journeys)}.")
        buddy = path_entry.get("buddy")
        # Define buddy intros (can be moved to a config file if needed)
        buddy_intros = {
            "Patch McDebug": "Arrr, I be Patch McDebug, yer relentless bug-hunter! Let's get ye shipshape.",
            "Captain Abby": "Welcome aboard! Captain Abby here to chart your course to greatness.",
            "Doc Testwell": "Ahoy! Doc Testwell at your service—let's keep things healthy and well-tested.",
            "Dave the Database Deckhand": "Dave here! I'll help you wrangle the data seas.",
            "Maple Cartwright": "Maple Cartwright, navigator extraordinaire—let's find your way.",
            "Bosun Riggs": "Bosun Riggs reporting! Automation and efficiency be my game.",
        }
        pirate_buddy_intros = {
            "Patch McDebug": "Arrr matey! Patch McDebug at yer service. Let's hunt bugs and plunder technical debt! 🏴‍☠️",
            "Captain Abby": "Avast! Captain Abby here to chart a course through these code-infested waters.",
            "Doc Testwell": "Shiver me test cases! Doc Testwell's the name, and healthy code's me game.",
            "Dave the Database Deckhand": "Hoist the data sails! Dave'll keep yer tables afloat.",
            "Maple Cartwright": "Maple Cartwright, navigator of the digital seas—let's find yer way to glory!",
            "Bosun Riggs": "Bosun Riggs, at yer command! Automation be the wind in our sails.",
        }
        buddy_intro = None
        if buddy:
            if pirate_mode:
                buddy_intro = pirate_buddy_intros.get(
                    buddy, f"Arrr! {buddy} be yer guide on this voyage."
                )
            else:
                buddy_intro = buddy_intros.get(
                    buddy, f"Welcome! {buddy} will guide you on this path."
                )
        steps = path_entry["steps"]
        created_steps = []
        for step in steps:
            instruction = (
                step["instruction"]
                if isinstance(step, dict) and "instruction" in step
                else step
            )
            doc_link = step.get("doc_link") if isinstance(step, dict) else None
            # Use project_name (string) as project_id in onboarding progress
            existing = (
                db.query(ProjectOnboardingProgress)
                .filter_by(
                    project_id=project_name, path=journey, step=instruction, version=1
                )
                .first()
            )
            if existing:
                created_steps.append(
                    {
                        "id": str(existing.id),
                        "path": journey,
                        "instruction": instruction,
                        "doc_link": doc_link,
                        "completed": existing.completed,
                        "status": getattr(existing, "status", "not_started"),
                    }
                )
                continue
            progress = ProjectOnboardingProgress(
                project_id=project_name,
                path=journey,
                step=instruction,
                completed=False,
                status="not_started",
            )
            db.add(progress)
            db.flush()
            created_steps.append(
                {
                    "id": str(progress.id),
                    "path": journey,
                    "instruction": instruction,
                    "doc_link": doc_link,
                    "completed": False,
                    "status": "not_started",
                }
            )
        db.commit()
        # Patch: Always create a token and return project_id for test_path
        response = {
            "project_name": project_name,
            "team_name": team_name,
            "buddy": buddy,
            "buddy_intro": buddy_intro,
            "steps": created_steps,
            "team_id": str(team.id) if team else None,
        }
        if journey == "test_path":
            # Label project as test-run and always create a token
            from db import ApiAccessToken
            new_token = secrets.token_urlsafe(32)
            db_token = ApiAccessToken(
                token=new_token,
                description="test-run token",
                active=True,
                role="admin",
                project_id=project.id,
            )
            db.add(db_token)
            db.commit()
            response["project_id"] = str(project.id)
            response["token"] = new_token
            response["project_label"] = "test-run"
        else:
            # For other paths, include project_id if available/desired
            response["project_id"] = str(project.id)
        return response
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Onboarding init failed: {e}\n{tb}")
        raise HTTPException(
            status_code=500, detail=f"Onboarding init failed: {e}\n{tb}"
        )
