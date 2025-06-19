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
from db import (
    ApiAccessToken,
    ApiErrorLog,
    Project,
    get_db,
    resolve_project_id,
    project_defaults_from_name,
)
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
    user: Optional[str] = None  # Add user field for user-specific tokens
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
    print(
        f"[PRINT-DEBUG] /admin/generate-token endpoint called. request={request.dict()}, Authorization={authorization}"
    )
    logger.debug(f"[generate_token] DB session id: {id(db)}")
    logger.debug(
        f"[generate_token] DB in transaction: {getattr(db, 'in_transaction', lambda: None)()}"
    )
    logger.debug(f"[generate_token] Existing tokens: {db.query(ApiAccessToken).all()}")
    """Generate a new API token with optional project and namespace scoping.

    Bootstrapping logic:
    - If no admin tokens exist for the specific project:
        - Allow creation of a non-admin token with no Authorization required.
        - To create the first admin token for the project, require a valid (non-admin) token in Authorization header.
    - If admin tokens exist for the project:
        - Require admin token in Authorization header for all token creation for that project.
    """
    logger.debug(f"Received token generation request: {request.dict()}")
    logger.debug(f"Authorization header: {authorization}")
    print(
        f"[DEBUG] generate_token: Authorization={authorization}, request.role={request.role}"
    )
    try:
        # Always define effective_project_id before use
        effective_project_id = request.project_id or (
            getattr(token_obj, "project_id", None) if "token_obj" in locals() else None
        )
        # Patch: Allow token creation with no project_id ONLY if no projects exist (onboarding/init bootstrapping)
        project_count = db.query(Project).count()
        if not effective_project_id:
            if project_count == 0:
                # Allow token creation for first project (onboarding/init)
                resolved_project_id = None
                project_name = None
            else:
                raise HTTPException(
                    status_code=400,
                    detail="project_id must be provided or present in the admin token.",
                )
        else:
            # Patch: Fetch project name for response
            project = (
                db.query(Project).filter(Project.id == effective_project_id).first()
                if effective_project_id
                else None
            )
            project_name = project.name if project else None
            # Always resolve project_id to UUID before DB operations
            try:
                uuid.UUID(effective_project_id)
                resolved_project_id = resolve_project_id(db, effective_project_id)
            except Exception:
                resolved_project_id = resolve_project_id(
                    db,
                    effective_project_id,
                    **project_defaults_from_name(effective_project_id),
                )

        # Check if any admin tokens exist for THIS PROJECT AND USER (not just project)
        existing_admin_tokens_for_project_and_user = 0
        if resolved_project_id and getattr(request, "user", None):
            existing_admin_tokens_for_project_and_user = (
                db.query(ApiAccessToken)
                .filter(
                    ApiAccessToken.active == True,
                    ApiAccessToken.role == "admin",
                    ApiAccessToken.project_id == resolved_project_id,
                    ApiAccessToken.user == getattr(request, "user", None),
                )
                .count()
            )
        logger.debug(
            f"Existing admin tokens for project {resolved_project_id} and user {getattr(request, 'user', None)}: {existing_admin_tokens_for_project_and_user}"
        )

        # Get user from request
        user = getattr(request, "user", None)

        # Check for existing token for this specific (project, user, role) combination
        existing_token_obj = None
        if resolved_project_id and user:
            existing_token_obj = (
                db.query(ApiAccessToken)
                .filter_by(
                    project_id=resolved_project_id,
                    user=user,
                    role=request.role,
                    active=True,
                )
                .first()
            )

        # If token already exists for this user/project/role, return it
        if existing_token_obj:
            return {
                "token": existing_token_obj.token,
                "description": existing_token_obj.description,
                "role": existing_token_obj.role,
                "project_id": existing_token_obj.project_id,
                "project_name": project_name,
                "allowed_namespaces": existing_token_obj.allowed_namespaces,
                "namespace_permissions": json.loads(
                    existing_token_obj.namespace_permissions
                )
                if existing_token_obj.namespace_permissions
                else None,
                "has_llm_access": existing_token_obj.has_llm_access,
            }

        token_obj = None
        if existing_admin_tokens_for_project_and_user == 0:
            print(
                f"[PRINT-DEBUG] Bootstrapping for project {resolved_project_id} and user {user}: request.role={request.role}, Authorization={authorization}"
            )
            logger.warning(
                f"[DEBUG] Bootstrapping for project {resolved_project_id} and user {user}: request.role={request.role}, Authorization={authorization}"
            )
            logger.debug(
                f"[generate_token] All tokens before admin creation: {db.query(ApiAccessToken).all()}"
            )
            # Bootstrapping: allow unauthenticated creation of first non-admin token for this project/user
            if request.role == "admin":
                print(
                    f"[PRINT-DEBUG] Attempting to create first admin token for project {resolved_project_id} and user {user}. Authorization={authorization}"
                )
                # To create the first admin token for this project/user, require a valid token (user or admin)
                if not authorization or not authorization.startswith("Bearer "):
                    print(
                        f"[PRINT-DEBUG] No valid Authorization header for first admin token: {authorization}"
                    )
                    logger.warning(
                        f"[DEBUG] Attempted to create first admin token without valid Authorization header: {authorization}"
                    )
                    raise HTTPException(
                        status_code=401,
                        detail="A valid API token is required to generate the first admin token for this project and user.",
                    )
                token_obj = require_api_token(authorization, db)
                logger.debug(
                    f"[generate_token] require_api_token returned: {token_obj}"
                )
                print(
                    f"[PRINT-DEBUG] First admin token creation: token_obj.role={getattr(token_obj, 'role', None)}, token_obj={token_obj}"
                )
                logger.warning(
                    f"[DEBUG] First admin token creation: token_obj.role={getattr(token_obj, 'role', None)}, token_obj={token_obj}"
                )
                # Allow both user and admin tokens to create the first admin token
                if token_obj.role not in ["user", "admin"]:
                    print(
                        f"[PRINT-DEBUG] Invalid role for first admin token creation: token_obj={token_obj}"
                    )
                    logger.warning(
                        f"[DEBUG] Invalid role for first admin token creation: token_obj={token_obj}"
                    )
                    raise HTTPException(
                        status_code=403,
                        detail="Invalid role for creating the first admin token.",
                    )
                print(
                    f"[PRINT-DEBUG] Passed token check for first admin token creation."
                )
            # else: allow creation of first non-admin token with no auth
        else:
            print(
                f"[PRINT-DEBUG] Admin tokens exist for project {resolved_project_id} and user {user}: request.role={request.role}, Authorization={authorization}"
            )
            logger.warning(
                f"[DEBUG] Admin tokens exist for project {resolved_project_id} and user {user}: request.role={request.role}, Authorization={authorization}"
            )
            # If admin tokens exist for this project/user, require admin Authorization header for all token creation
            if not authorization or not authorization.startswith("Bearer "):
                print(
                    f"[PRINT-DEBUG] No valid Authorization header for additional token creation: {authorization}"
                )
                logger.warning(
                    f"[DEBUG] Attempted to generate token without valid Authorization header: {authorization}"
                )
                raise HTTPException(
                    status_code=401,
                    detail="A valid admin API token is required to generate additional tokens for this project and user.",
                )
            token_obj = require_api_token(authorization, db)
            print(
                f"[PRINT-DEBUG] Additional token creation: token_obj.role={getattr(token_obj, 'role', None)}, token_obj={token_obj}"
            )
            logger.warning(
                f"[DEBUG] Additional token creation: token_obj.role={getattr(token_obj, 'role', None)}, token_obj={token_obj}"
            )
            if token_obj.role != "admin":
                print(
                    f"[PRINT-DEBUG] Insufficient role for additional token creation: token_obj={token_obj}"
                )
                logger.warning(
                    f"[DEBUG] Insufficient role for additional token creation: token_obj={token_obj}"
                )
                raise HTTPException(status_code=403, detail="Insufficient role")

        # Check if project exists and has LLM access if requested
        has_llm_access = 0
        if effective_project_id:
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

        db_token = ApiAccessToken(
            token=new_token,
            description=request.description,
            created_by=request.created_by,
            active=True,
            role=request.role,
            project_id=resolved_project_id if effective_project_id else None,
            allowed_namespaces=request.allowed_namespaces,
            namespace_permissions=json.dumps(request.namespace_permissions)
            if request.namespace_permissions
            else None,
            has_llm_access=has_llm_access,
            user=user,  # Store user field
        )
        db.add(db_token)
        db.commit()
        logger.info(
            f"Successfully created new token with description: {request.description}"
        )
        logger.debug(
            f"[generate_token] Token committed. All tokens now: {db.query(ApiAccessToken).all()}"
        )

        return {
            "token": new_token,
            "description": request.description,
            "role": request.role,
            "project_id": effective_project_id,
            "project_name": project_name,
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
