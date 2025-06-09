import datetime
import json
import logging
import secrets
import uuid
from typing import Dict, List, Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import require_api_token, require_role
from db import ApiAccessToken, ApiErrorLog, Project, get_db, resolve_project_id, project_defaults_from_name
from utils.serialization import serialize_uuids

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


class TokenGenerateRequest(BaseModel):
    """Request model for generating an API token."""

    description: str = ""
    created_by: Optional[str] = None
    role: str = "user"
    project_id: Optional[str] = None
    allowed_namespaces: Optional[List[str]] = None
    namespace_permissions: Optional[
        Dict[str, str]
    ] = None  # namespace -> permission_type mapping

    class Config:
        extra = "allow"  # Allow extra fields in the request


@router.post("/generate-token")
async def generate_token(
    request: TokenGenerateRequest,
    authorization: Optional[str] = Header(None, convert_underscores=False),
    db: Session = Depends(get_db),
):
    print(f"[PRINT-DEBUG] /admin/generate-token endpoint called. request={request.dict()}, Authorization={authorization}")
    """Generate a new API token with optional project and namespace scoping.

    Bootstrapping logic:
    - If no tokens exist:
        - Allow creation of a non-admin token with no Authorization required.
        - To create the first admin token, require a valid (non-admin) token in Authorization header.
    - If tokens exist:
        - Require admin token in Authorization header for all token creation.
    """
    logger.debug(f"Received token generation request: {request.dict()}")
    logger.debug(f"Authorization header: {authorization}")
    print(f"[DEBUG] generate_token: Authorization={authorization}, request.role={request.role}")
    try:
        # Check if any admin tokens exist
        existing_admin_tokens = (
            db.query(ApiAccessToken).filter(ApiAccessToken.active == True, ApiAccessToken.role == "admin").count()
        )
        logger.debug(f"Existing admin tokens count: {existing_admin_tokens}")
        existing_tokens = (
            db.query(ApiAccessToken).filter(ApiAccessToken.active == True).count()
        )
        logger.debug(f"Existing tokens count: {existing_tokens}")

        token_obj = None
        if existing_admin_tokens == 0:
            print(f"[PRINT-DEBUG] Bootstrapping: request.role={request.role}, Authorization={authorization}")
            logger.warning(f"[DEBUG] Bootstrapping: request.role={request.role}, Authorization={authorization}")
            # Bootstrapping: allow unauthenticated creation of first non-admin token
            if request.role == "admin":
                print(f"[PRINT-DEBUG] Attempting to create first admin token. Authorization={authorization}")
                # To create the first admin token, require a valid (non-admin) token
                if not authorization or not authorization.startswith("Bearer "):
                    print(f"[PRINT-DEBUG] No valid Authorization header for first admin token: {authorization}")
                    logger.warning(
                        f"[DEBUG] Attempted to create first admin token without valid Authorization header: {authorization}"
                    )
                    raise HTTPException(
                        status_code=401,
                        detail="A valid non-admin API token is required to generate the first admin token.",
                    )
                token_obj = require_api_token(authorization, db)
                print(f"[PRINT-DEBUG] First admin token creation: token_obj.role={getattr(token_obj, 'role', None)}, token_obj={token_obj}")
                logger.warning(f"[DEBUG] First admin token creation: token_obj.role={getattr(token_obj, 'role', None)}, token_obj={token_obj}")
                if token_obj.role == "admin":
                    print(f"[PRINT-DEBUG] Attempted to use admin token to create first admin token: token_obj={token_obj}")
                    logger.warning(f"[DEBUG] Attempted to use admin token to create first admin token: token_obj={token_obj}")
                    raise HTTPException(status_code=403, detail="Cannot use admin token to create the first admin token.")
                print(f"[PRINT-DEBUG] Passed non-admin token check for first admin token creation.")
            # else: allow creation of first non-admin token with no auth
        else:
            print(f"[PRINT-DEBUG] Admin tokens exist: request.role={request.role}, Authorization={authorization}")
            logger.warning(f"[DEBUG] Admin tokens exist: request.role={request.role}, Authorization={authorization}")
            # If any admin tokens exist, require admin Authorization header for all token creation
            if not authorization or not authorization.startswith("Bearer "):
                print(f"[PRINT-DEBUG] No valid Authorization header for additional token creation: {authorization}")
                logger.warning(
                    f"[DEBUG] Attempted to generate token without valid Authorization header: {authorization}"
                )
                raise HTTPException(
                    status_code=401,
                    detail="A valid admin API token is required to generate additional tokens.",
                )
            token_obj = require_api_token(authorization, db)
            print(f"[PRINT-DEBUG] Additional token creation: token_obj.role={getattr(token_obj, 'role', None)}, token_obj={token_obj}")
            logger.warning(f"[DEBUG] Additional token creation: token_obj.role={getattr(token_obj, 'role', None)}, token_obj={token_obj}")
            if token_obj.role != "admin":
                print(f"[PRINT-DEBUG] Insufficient role for additional token creation: token_obj={token_obj}")
                logger.warning(f"[DEBUG] Insufficient role for additional token creation: token_obj={token_obj}")
                raise HTTPException(status_code=403, detail="Insufficient role")

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
            # Always resolve project_id to UUID before DB operations
            try:
                uuid.UUID(request.project_id)
                resolved_project_id = resolve_project_id(db, request.project_id)
            except Exception:
                resolved_project_id = resolve_project_id(db, request.project_id, **project_defaults_from_name(request.project_id))
            logger.debug(f"Checking project existence: {resolved_project_id}")
            project = (
                db.query(Project)
                .filter(Project.id == resolved_project_id, Project.active == True)
                .first()
            )
            if not project:
                logger.error(f"Project not found: {resolved_project_id}")
                raise HTTPException(
                    status_code=404, detail=f"Project {resolved_project_id} not found"
                )
            has_llm_access = 1 if project.has_llm_access else 0
            logger.debug(f"Project LLM access: {has_llm_access}")

        db_token = ApiAccessToken(
            token=new_token,
            description=request.description,
            created_by=request.created_by,
            active=True,
            role=request.role,
            project_id=resolved_project_id if request.project_id else None,
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
    token: dict = Depends(require_api_token),
):
    """Get error log by ID (token required)."""
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
