import datetime
import json
import logging
import secrets
import uuid
from typing import Dict, List, Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import require_api_token, require_role
from db import ApiAccessToken, ApiErrorLog, Project, get_db

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


class TokenGenerateRequest(BaseModel):
    """Request model for generating an API token."""

    description: str = ""
    created_by: Optional[str] = None
    role: str = "user"
    project_id: Optional[int] = None
    allowed_namespaces: Optional[List[str]] = None
    namespace_permissions: Optional[
        Dict[str, str]
    ] = None  # namespace -> permission_type mapping

    class Config:
        extra = "allow"  # Allow extra fields in the request


@router.post("/generate-token")
async def generate_token(
    request: TokenGenerateRequest,
    authorization: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Generate a new API token with optional project and namespace scoping."""
    logger.debug(f"Received token generation request: {request.dict()}")
    logger.debug(f"Authorization header: {authorization}")
    try:
        # Check if this is the first token being generated
        existing_tokens = (
            db.query(ApiAccessToken).filter(ApiAccessToken.active == 1).count()
        )
        logger.debug(f"Existing tokens count: {existing_tokens}")

        token_obj = None
        # If tokens exist, require admin Authorization header
        if existing_tokens > 0:
            if not authorization or not authorization.startswith("Bearer "):
                logger.warning(
                    "Attempted to generate token without admin token when tokens exist"
                )
                raise HTTPException(
                    status_code=401,
                    detail="Admin token required for generating additional tokens",
                )
            # Validate token and role
            token_obj = require_api_token(authorization, db)
            if token_obj.role != "admin":
                raise HTTPException(status_code=403, detail="Insufficient role")

        # For initial token generation, force admin role
        if existing_tokens == 0:
            request.role = "admin"
            logger.info("Forcing admin role for initial token generation")

        new_token = secrets.token_urlsafe(32)
        logger.debug(f"Generated new token: {new_token}")

        # Validate namespace permissions if provided
        if request.namespace_permissions:
            logger.debug(
                f"Validating namespace permissions: {request.namespace_permissions}"
            )
            for namespace, perm_type in request.namespace_permissions.items():
                if perm_type not in ["read", "write"]:
                    logger.error(
                        f"Invalid permission type '{perm_type}' for namespace '{namespace}'"
                    )
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid permission type '{perm_type}' for namespace '{namespace}'. Must be 'read' or 'write'.",
                    )

        # Check if project exists and has LLM access if requested
        has_llm_access = 0
        if request.project_id:
            logger.debug(f"Checking project existence: {request.project_id}")
            project = (
                db.query(Project)
                .filter(Project.id == request.project_id, Project.active == 1)
                .first()
            )
            if not project:
                logger.error(f"Project not found: {request.project_id}")
                raise HTTPException(
                    status_code=404, detail=f"Project {request.project_id} not found"
                )
            has_llm_access = 1 if project.has_llm_access else 0
            logger.debug(f"Project LLM access: {has_llm_access}")

        db_token = ApiAccessToken(
            token=new_token,
            description=request.description,
            created_by=request.created_by,
            active=1,
            role=request.role,
            project_id=request.project_id,
            allowed_namespaces=request.allowed_namespaces,
            namespace_permissions=json.dumps(request.namespace_permissions)
            if request.namespace_permissions
            else None,
            has_llm_access=has_llm_access,
        )
        db.add(db_token)
        db.commit()
        logger.info(
            f"Successfully created new token with description: {request.description}"
        )

        return {
            "token": new_token,
            "description": request.description,
            "role": request.role,
            "project_id": request.project_id,
            "allowed_namespaces": request.allowed_namespaces,
            "namespace_permissions": request.namespace_permissions,
            "has_llm_access": has_llm_access,
        }
    except Exception as e:
        logger.error(f"Error generating token: {str(e)}", exc_info=True)
        raise


@router.get("/errors/{error_id}")
def get_error_log(
    error_id: str,
    db: Session = Depends(get_db),
):
    """Get error log by ID (public, limited info)."""
    try:
        uuid_obj = uuid.UUID(error_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Error not found")
    log = db.query(ApiErrorLog).filter(ApiErrorLog.id == error_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Error not found")
    # Only return limited info for public access
    return {
        "id": log.id,
        "timestamp": log.timestamp,
        "path": log.path,
        "method": log.method,
        "status_code": log.status_code,
        "message": log.message,
        # 'stack_trace' and 'user_id' are intentionally omitted for public endpoint
    }


def create_access_token(
    data: dict, secret: str = "testsecret", expires_delta: int = 3600
) -> str:
    """Create a dummy JWT access token for testing purposes."""
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_delta)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret, algorithm="HS256")


# Add a custom exception handler for validation errors
def add_validation_error_logging(app):
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        logger.error(
            f"Validation error for request {request.url}: {exc.errors()} | Body: {await request.body()}"
        )
        return JSONResponse(
            status_code=422,
            content={
                "detail": exc.errors(),
                "body": (await request.body()).decode("utf-8"),
            },
        )
