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
